/* Failure Topography data model (DOM-free; unit-tested).
 * Groups measured episodes into fault "soundings": one sounding per
 * (scenario, baseline, slow_ms, disabled) combination, pooled over
 * input variants. Cell→episode mapping is positional (sliceCells)
 * and fails closed.
 */
import { sliceCells } from './stats.js';
import { isWarmup } from '../data.js';

export function soundingKey(cell, baseline) {
  const f = cell.fault_params || {};
  return `${cell.scenario_id}||${baseline}||${Number(f.slow_ms ?? 0)}||${f.disabled === true}`;
}

/* Returns { soundings, levels }: soundings pool episodes over inputs;
 * levels is the sorted unique slow_ms axis. Throws on bad mapping. */
export function groupSoundings(runs) {
  const groups = new Map();
  for (const run of runs) {
    for (const { cell, episodes } of sliceCells(run.data.cells || [], run.data.episodes || [])) {
      const f = cell.fault_params || {};
      const slow = Number(f.slow_ms ?? 0);
      const disabled = f.disabled === true;
      const key = `${cell.scenario_id}||${run.baseline}||${slow}||${disabled}`;
      if (!groups.has(key)) {
        groups.set(key, {
          scenario: cell.scenario_id, baseline: run.baseline, slow, disabled,
          k: 0, n: 0, inputs: new Set(), unverified: false,
        });
      }
      const g = groups.get(key);
      g.inputs.add(cell.input_id);
      for (const e of episodes) {
        if (isWarmup(e)) continue;
        g.n += 1;
        if (e.outcome === 'succeeded') g.k += 1;
        if (!e.verification || e.verification.status !== 'verified') g.unverified = true;
      }
    }
  }
  const soundings = [...groups.values()].map((g) => ({ ...g, inputs: [...g.inputs].sort() }));
  soundings.sort((a, b) => a.scenario.localeCompare(b.scenario) || a.baseline.localeCompare(b.baseline)
    || a.slow - b.slow || Number(a.disabled) - Number(b.disabled));
  const levels = [...new Set(soundings.map((s) => s.slow))].sort((a, b) => a - b);
  return { soundings, levels };
}
