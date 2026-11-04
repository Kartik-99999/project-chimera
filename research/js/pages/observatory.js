/* Evaluation Observatory: condition performance, baselines, uncertainty. */
import { getState, getRun, measuredEpisodes, isFalseSuccess, wilsonUpper,
  esc, fmtMs, fmtPct, SCENARIOS, baselineLabel } from '../data.js';
import { link } from '../app.js';
import { pageHead, pill, emptyState, art, globes, secHead } from '../components.js';
import { groupedBars, barCell, dotPlot } from '../charts.js';
import { sliceCells, wilson } from '../viz/stats.js';
import { attachTip } from '../viz/tooltip.js';

function pct(sorted, q) {
  if (!sorted.length) return null;
  const i = Math.min(sorted.length - 1, Math.ceil((q / 100) * sorted.length) - 1);
  return sorted[Math.max(0, i)];
}

function expectedOf(split, scenario) {
  const s = getState();
  const run = [...s.runs.values()].find((r) => r.split === split && r.data);
  if (!run) return null;
  const man = s.manifests.get(run.manifestFile);
  const sc = man && (man.scenarios || []).find((x) => x.id === scenario);
  return sc ? sc.expected_outcome : null;
}

export async function pageObservatory(el, { query }) {
  const s = getState();
  if (![...s.runs.values()].some((r) => r.data)) {
    el.innerHTML = pageHead('Evaluation Observatory', [['Evaluation Observatory']]) + emptyState(
      'No run evidence loaded', 'Serve the repository root and reload.');
    return;
  }
  const split = query.split === 'development' ? 'development' : 'evaluation';
  const scenarioFilter = SCENARIOS.includes(query.scenario) ? query.scenario : '';
  const scenarios = scenarioFilter ? [scenarioFilter] : SCENARIOS;

  const agg = {};
  for (const sc of scenarios) {
    agg[sc] = {};
    for (const b of ['chimera', 'baseline-a']) {
      const eps = measuredEpisodes().filter((e) => e.split === split && e.scenario_id === sc && e.baseline === b);
      const k = eps.filter((e) => e.outcome === 'succeeded').length;
      const fs = eps.filter(isFalseSuccess).length;
      const durs = eps.map((e) => e.duration_ms).filter((d) => d != null).sort((a, b2) => a - b2);
      agg[sc][b] = { k, n: eps.length, fs, p50: pct(durs, 50), p95: pct(durs, 95) };
    }
  }

  const successChart = groupedBars({
    id: `success by scenario, ${split} split`,
    categories: scenarios.map((sc) => `${sc} (${expectedOf(split, sc) || '?'})`),
    series: [
      { label: 'Chimera', color: '#0e7490', values: scenarios.map((sc) => agg[sc].chimera.k), denoms: scenarios.map((sc) => agg[sc].chimera.n) },
      { label: 'A — replay', color: '#6d28d9', values: scenarios.map((sc) => agg[sc]['baseline-a'].k), denoms: scenarios.map((sc) => agg[sc]['baseline-a'].n) },
    ],
  });
  const fsChart = groupedBars({
    id: `false successes with Wilson bounds, ${split} split`,
    categories: scenarios,
    series: [
      { label: 'Chimera', color: '#0e7490', values: scenarios.map((sc) => agg[sc].chimera.fs), denoms: scenarios.map((sc) => agg[sc].chimera.n) },
      { label: 'A — replay', color: '#6d28d9', values: scenarios.map((sc) => agg[sc]['baseline-a'].fs), denoms: scenarios.map((sc) => agg[sc]['baseline-a'].n) },
    ],
    whiskers: [
      scenarios.map((sc) => { const a = agg[sc].chimera; const w = wilsonUpper(a.fs, a.n); return w == null ? null : w * a.n; }),
      scenarios.map((sc) => { const a = agg[sc]['baseline-a']; const w = wilsonUpper(a.fs, a.n); return w == null ? null : w * a.n; }),
    ],
  });

  const maxLat = Math.max(0, ...scenarios.flatMap((sc) => [agg[sc].chimera.p95 || 0, agg[sc]['baseline-a'].p95 || 0]));
  const latRows = scenarios.map((sc) => {
    const c = agg[sc].chimera, r = agg[sc]['baseline-a'];
    return `<tr><td><a href="${link('atlas', [], { scenario: sc })}">${sc}</a></td>`
      + `<td class="num">${barCell(c.p50, maxLat, fmtMs(c.p50))}</td><td class="num">${barCell(c.p95, maxLat, fmtMs(c.p95))}</td>`
      + `<td class="num">${barCell(r.p50, maxLat, fmtMs(r.p50))}</td><td class="num">${barCell(r.p95, maxLat, fmtMs(r.p95))}</td></tr>`;
  }).join('');

  const drillRows = scenarios.map((sc) => {
    const c = agg[sc].chimera, r = agg[sc]['baseline-a'];
    const wb = (a) => { const w = wilsonUpper(a.fs, a.n); return w == null ? '—' : `≤${(w * 100).toFixed(1)}%`; };
    return `<tr><td>${sc}</td>`
      + `<td class="num">${c.k}/${c.n} (${fmtPct(c.k, c.n)})</td><td class="num">${r.k}/${r.n} (${fmtPct(r.k, r.n)})</td>`
      + `<td class="num">${c.fs}/${c.n} ${wb(c)}</td><td class="num">${r.fs}/${r.n} ${wb(r)}</td>`
      + `<td><a href="${link('atlas', [], { scenario: sc })}">episodes →</a></td></tr>`;
  }).join('');

  // Signal vs Uncertainty rows: per-cell when one scenario is selected
  // (fault-aware via positional slicing), per-scenario pooled otherwise.
  const perCell = scenarioFilter !== '';
  const signalRows = [];
  for (const b of ['chimera', 'baseline-a']) {
    const runId = `${split === 'development' ? 'dev' : 'eval'}-20261028-${b}`;
    const run = getRun(runId);
    if (!run) continue;
    if (perCell) {
      let sliced = [];
      try { sliced = sliceCells(run.data.cells || [], run.data.episodes || []); } catch { sliced = []; }
      for (const { cell, episodes } of sliced) {
        if (cell.scenario_id !== scenarioFilter) continue;
        const kk = episodes.filter((e) => e.outcome === 'succeeded').length;
        const nn = episodes.length;
        const iv = wilson(kk, nn);
        const f = cell.fault_params || {};
        const flabel = Object.keys(f).sort().map((k2) => `${k2}=${f[k2]}`).join(' ');
        signalRows.push({
          label: `${cell.scenario_id} / ${cell.input_id}`, sub: `${b === 'chimera' ? 'Chimera' : 'A — replay'}${flabel ? ` · ${flabel}` : ''}`,
          k: kk, n: nn, color: b === 'chimera' ? '#0e7490' : '#6d28d9',
          href: link('atlas', [], { run: runId, scenario: cell.scenario_id, search: cell.input_id }),
          tip: `${cell.scenario_id}/${cell.input_id} (${b}): ${kk}/${nn} = ${(100 * kk / nn).toFixed(1)}%, 95% Wilson [${(iv.lo * 100).toFixed(1)}%, ${(iv.hi * 100).toFixed(1)}%]`,
        });
      }
    } else {
      for (const sc of scenarios) {
        const a = agg[sc][b];
        const iv = wilson(a.k, a.n);
        signalRows.push({
          label: `${sc} (pooled)`, sub: `${b === 'chimera' ? 'Chimera' : 'A — replay'} · all inputs/variants`,
          k: a.k, n: a.n, color: b === 'chimera' ? '#0e7490' : '#6d28d9',
          href: link('observatory', [], { split, scenario: sc }),
          tip: `${sc} pooled (${b}): ${a.k}/${a.n} = ${(100 * a.k / a.n).toFixed(1)}%, 95% Wilson [${(iv.lo * 100).toFixed(1)}%, ${(iv.hi * 100).toFixed(1)}%]`,
        });
      }
    }
  }
  // Pooled side-by-side for the current scope + overlap fact (descriptive only).
  const poolCards = ['chimera', 'baseline-a'].map((b) => {
    let k = 0, n = 0;
    for (const sc of scenarios) { k += agg[sc][b].k; n += agg[sc][b].n; }
    const iv = wilson(k, n);
    return { b, k, n, iv };
  });
  const [pc, pr] = poolCards;
  const overlap = pc.iv && pr.iv ? !(pc.iv.hi < pr.iv.lo || pr.iv.hi < pc.iv.lo) : null;

  const splitN = scenarios.reduce((a, sc) => a + agg[sc].chimera.n + agg[sc]['baseline-a'].n, 0);
  const navy = `<div class="navy">${globes()}<h2>Signal vs uncertainty</h2>`
    + `<p class="sub">${perCell ? `Per-cell dots with 95% Wilson whiskers for ${esc(scenarioFilter)} — ${signalRows.length} rows below, every one linked to its episodes.` : 'Pooled scenario rows with 95% Wilson whiskers. Select a scenario above for the per-cell view.'} Soft signal bands, same intervals.</p>`
    + `<p>${poolCards.map((p) => `<span class="glass"><span class="dot" style="background:${p.b === 'chimera' ? '#5eead4' : '#c4b5fd'}"></span>${p.b === 'chimera' ? 'Chimera' : 'replay'} pooled · ${p.k}/${p.n}</span>`).join('')}</p></div>`;
  el.innerHTML = pageHead('Evaluation Observatory', [['Evaluation Observatory']], '', {
    kicker: `Route #/observatory · split = ${split}`,
    lede: `Condition performance, baselines, and uncertainty — ${splitN} ${split} episodes. Rounded luminous bars and whiskers; every estimate still prints its denominator.`,
    meta: `${split === 'evaluation' ? pill('warn', 'Eval provisional') : pill('info', 'Development split · audited')} ${pill('dim', `split: ${split} · n = ${splitN}`)}`,
  })
    + (split === 'evaluation'
      ? `<div class="banner warn"><strong>Provisional.</strong> Held-out figures below are measurements with denominators — no eval audit sample is adjudicated, so treat every rate as unvetted. ${`<a href="${link('audit')}">Audit status →</a>`}</div>`
      : `<div class="banner info"><strong>Development split, audited.</strong> The dev sample reached 100% agreement — but dev is the debugging split, not the held-out claim. ${`<a href="${link('audit')}">Audit status →</a>`}</div>`)
    + `<div class="card"><div class="filters">
        <div class="field"><label for="ob-split">Split</label><select id="ob-split">
          <option value="evaluation"${split === 'evaluation' ? ' selected' : ''}>evaluation (held out)</option>
          <option value="development"${split === 'development' ? ' selected' : ''}>development</option>
        </select></div>
        <div class="field"><label for="ob-scenario">Scenario</label><select id="ob-scenario">
          <option value="">All scenarios</option>${SCENARIOS.map((x) => `<option${scenarioFilter === x ? ' selected' : ''}>${x}</option>`).join('')}
        </select></div>
      </div></div>`
    + secHead('Success streams by scenario', 'Rounded luminous bars — exact k/n at every crest.')
    + `<div class="card">${art(1)}<h2>Success by scenario <span style="color:var(--ink-3);font-weight:400">— pooled across inputs and fault variants; labels show k/n</span></h2>${successChart}
      <p style="color:var(--ink-3);font-size:12.5px">Parenthesised words are the manifest's expected outcomes. Pooling hides variant-level differences — see Failure Cartography for the per-input map.</p></div>`
    + secHead('False successes with Wilson bounds', 'Zero-count blooms — dots at 0 with 95% upper-bound halos.')
    + `<div class="card"><h2>False successes with 95% Wilson upper bounds</h2>${fsChart}
      <p style="color:var(--ink-3);font-size:12.5px">Whiskers are upper bounds on the pooled rate, not confidence in zero. Per-cell bounds (n=5) are far wider — e.g. 0/5 → ≤43.4%.</p></div>`
    + navy
    + `<div class="card" id="signal-card"><h2>Signal vs uncertainty — success estimates with 95% Wilson intervals</h2>
      <p style="color:var(--ink-2)">${perCell ? 'One row per cell (fault-aware): dots are observed k/n, whiskers are 95% Wilson intervals. Click a row for its episodes.' : 'One row per scenario (pooled across inputs and variants). Select a scenario above for the per-cell view.'} Hover or focus any row for exact bounds.</p>
      ${dotPlot({ rows: signalRows, id: 'success estimates with Wilson intervals' })}
      <div class="pool-duo" role="group" aria-label="Pooled side-by-side comparison">${poolCards.map((p) => (
        `<div class="pool-cell"><span class="pool-name"><span class="sw" style="background:${p.b === 'chimera' ? '#0e7490' : '#6d28d9'}"></span>${p.b === 'chimera' ? 'Chimera' : 'A — replay'} — pooled scope</span>`
        + `<span class="pool-rate"><strong>${p.k}/${p.n}</strong> = ${(100 * p.k / p.n).toFixed(1)}%</span>`
        + `<span class="pool-iv">95% Wilson [${(p.iv.lo * 100).toFixed(1)}%, ${(p.iv.hi * 100).toFixed(1)}%]</span></div>`)).join('')}</div>
      <p style="color:var(--ink-3);font-size:12.5px">Descriptive only: these intervals describe the observed sample. ${
        overlap == null ? 'Overlap could not be determined.' : overlap
          ? 'The pooled intervals overlap — which by itself is not a significance test and supports no claim either way.'
          : 'The pooled intervals do not overlap — which by itself is not a significance test and supports no generalization claim.'}</p></div>`
    + secHead('Latency, honestly scaled', 'p50 / p95 per scenario · ms · same-machine comparison only')
    + `<div class="card"><h2>Latency distribution (recomputed from episode durations)</h2>
      <div class="table-wrap"><table class="data"><thead><tr><th>Scenario</th><th class="num">Chimera p50</th><th class="num">Chimera p95</th><th class="num">Replay p50</th><th class="num">Replay p95</th></tr></thead><tbody>${latRows}</tbody></table></div>
      <p style="color:var(--ink-3);font-size:12.5px">Nearest-rank percentiles over measured episode durations. Same-machine comparison only; absolute values include browser start-up.</p></div>`
    + `<div class="card"><h2>Numbers behind the charts</h2>
      <div class="table-wrap"><table class="data"><thead><tr><th>Scenario</th><th class="num">Chimera success</th><th class="num">Replay success</th><th class="num">Chimera false-succ.</th><th class="num">Replay false-succ.</th><th></th></tr></thead><tbody>${drillRows}</tbody></table></div></div>`;

  el.querySelectorAll('#signal-card a[data-tip]').forEach((a) => attachTip(a, a.dataset.tip));
  el.querySelector('#ob-split').addEventListener('change', (e) => {
    window.location.hash = link('observatory', [], { split: e.target.value, scenario: scenarioFilter });
  });
  el.querySelector('#ob-scenario').addEventListener('change', (e) => {
    window.location.hash = link('observatory', [], { split, scenario: e.target.value });
  });
}
