/* Evidence River data model (DOM-free; unit-tested).
 * Aggregates measured episodes into scenario → baseline → outcome
 * → cell-audit flows. Each measured episode contributes exactly one
 * unit to each transition; warm-ups are excluded upstream.
 */
import { sliceCells } from './stats.js';
import { isWarmup, isHarnessError } from '../data.js';

export const OUTCOME_ORDER = ['succeeded', 'failed', 'cancelled', 'inconclusive'];

export function outcomeNode(ep) {
  if (isHarnessError(ep)) return 'failed · harness error';
  return OUTCOME_ORDER.includes(ep.outcome) ? ep.outcome : `other (${ep.outcome})`;
}

export function outcomeFilter(node) {
  if (node === 'failed · harness error') return 'harness-error';
  return OUTCOME_ORDER.includes(node) ? node : '';
}

/* Map `${runId}::${trial_id}` → 'cell audited' | 'cell pending'.
 * Throws (fail closed) when episodes cannot be mapped positionally. */
export function buildAuditMap(runs) {
  const auditOf = new Map();
  for (const run of runs) {
    for (const { cell, episodes } of sliceCells(run.data.cells || [], run.data.episodes || [])) {
      const state = cell.verifier_audit ? 'cell audited' : 'cell pending';
      for (const e of episodes) auditOf.set(`${run.runId}::${e.trial_id}`, state);
    }
  }
  return auditOf;
}

/* Aggregate flows. `runs` = [{ runId, baseline, data:{episodes} }].
 * Returns { episodes, flows }; each flow has {fromCol,from,toCol,to,
 * value,filter}. Throws on cell-mapping failure. */
export function aggregateFlows(runs) {
  const auditOf = buildAuditMap(runs);
  const episodes = [];
  for (const run of runs) {
    for (const e of run.data.episodes || []) {
      if (isWarmup(e)) continue;
      episodes.push({ ...e, runId: run.runId, baseline: run.baseline });
    }
  }
  const agg = (keyFn) => {
    const m = new Map();
    for (const e of episodes) {
      const k = keyFn(e);
      m.set(k, (m.get(k) || 0) + 1);
    }
    return m;
  };
  const flows = [];
  const push = (fromCol, from, toCol, to, value, filter) => {
    if (value > 0) flows.push({ fromCol, from, toCol, to, value, filter });
  };
  for (const [key, v] of agg((e) => `${e.scenario_id}||${e.baseline}`)) {
    const [sc, b] = key.split('||');
    push(0, sc, 1, b, v, { scenario: sc, baseline: b });
  }
  for (const [key, v] of agg((e) => `${e.baseline}||${outcomeNode(e)}`)) {
    const [b, o] = key.split('||');
    push(1, b, 2, o, v, { baseline: b, outcome: outcomeFilter(o) });
  }
  for (const [key, v] of agg((e) => `${outcomeNode(e)}||${auditOf.get(`${e.runId}::${e.trial_id}`) || 'cell pending'}`)) {
    const [o, a] = key.split('||');
    push(2, o, 3, a, v, { outcome: outcomeFilter(o) });
  }
  return { episodes, flows };
}
