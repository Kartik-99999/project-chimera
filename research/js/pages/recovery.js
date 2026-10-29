/* Recovery Studio: honest bounded-failure inspection.
 * The repository has no recovery engine and no simulator. This
 * workspace inspects what bounded failure looks like in the evidence
 * and labels every forward-looking item PROPOSED. No fake controls.
 */
import { measuredEpisodes, mVal, esc, fmtMs, fmtInt } from '../data.js';
import { link } from '../app.js';
import { pageHead, pill } from '../components.js';
import { barCell } from '../charts.js';

function pct(sorted, q) {
  if (!sorted.length) return null;
  const i = Math.min(sorted.length - 1, Math.ceil((q / 100) * sorted.length) - 1);
  return sorted[Math.max(0, i)];
}

export async function pageRecovery(el, { query }) {
  const split = query.split === 'development' ? 'development' : 'evaluation';
  const eps = measuredEpisodes().filter((e) => e.split === split
    && (e.scenario_id === 'S-DIS' || e.scenario_id === 'S-SLOWDIS'));
  const groups = ['chimera', 'baseline-a'].map((b) => {
    const g = eps.filter((e) => e.baseline === b);
    const durs = g.map((e) => e.duration_ms).filter((d) => d != null).sort((a, c) => a - c);
    const retries = g.map((e) => { const m = mVal(e.retries); return m.ok ? m.value : null; }).filter((v) => v != null);
    const correctTerminal = g.filter((e) => e.agent_terminal_status === 'failed').length;
    const unexpectedSuccess = g.filter((e) => e.outcome === 'succeeded').length;
    return { b, n: g.length, p50: pct(durs, 50), p95: pct(durs, 95),
      maxRetry: retries.length ? Math.max(...retries) : null,
      correctTerminal, unexpectedSuccess };
  });
  const maxD = Math.max(0, ...groups.map((g) => g.p95 || 0));
  const rows = groups.map((g) => (
    `<tr><td>${g.b === 'chimera' ? 'Chimera' : 'A — replay'}</td><td class="num">${g.n}</td>`
    + `<td class="num">${g.correctTerminal}/${g.n} reported failed</td>`
    + `<td class="num">${barCell(g.p50, maxD, fmtMs(g.p50))}</td>`
    + `<td class="num">${barCell(g.p95, maxD, fmtMs(g.p95))}</td>`
    + `<td class="num">${g.maxRetry == null ? '—' : g.maxRetry}</td>`
    + `<td>${g.unexpectedSuccess === 0 ? pill('ok', 'none unexpected') : pill('bad', `${g.unexpectedSuccess} unexpected`)}</td></tr>`
  )).join('');

  const examples = eps.filter((e) => e.outcome !== 'succeeded').slice(0, 6).map((e) => (
    `<div class="finding"><span class="marker" aria-hidden="true">◆</span><span><code>${esc(e.trial_id)}</code> (${esc(e.scenario_id)}/${esc(e.input_id)}, ${esc(e.baseline)}) — reported <code>${esc(e.agent_terminal_status)}</code> in ${fmtMs(e.duration_ms)}`
    + `${e.error ? ` · <code>${esc(e.error.length > 80 ? `${e.error.slice(0, 77).replace(/\s+\S*$/, '')}…` : e.error)}</code>` : ''} <a href="${link('evidence', [e.runId, e.trial_id])}">Inspect →</a></span></div>`
  )).join('');

  el.innerHTML = pageHead('Recovery Studio', [['Recovery Studio']])
    + `<div class="banner warn"><strong>No recovery engine exists in this repository.</strong> Nothing here runs simulations or recovery attempts. This workspace inspects the bounded-failure evidence that a future recovery study would start from, and labels every forward item <strong>PROPOSED</strong>.</div>`
    + `<div class="card"><div class="filters"><div class="field"><label for="r-split">Split</label><select id="r-split">
        <option value="evaluation"${split === 'evaluation' ? ' selected' : ''}>evaluation (held out)</option>
        <option value="development"${split === 'development' ? ' selected' : ''}>development</option>
      </select></div></div>
      <h2>Bounded failure on persistent faults (S-DIS + S-SLOWDIS)</h2>
      <div class="table-wrap"><table class="data"><thead><tr><th>Baseline</th><th class="num">Episodes</th><th class="num">Terminal correctness</th><th class="num">Duration p50</th><th class="num">Duration p95</th><th class="num">Max retries</th><th>Unexpected success</th></tr></thead><tbody>${rows}</tbody></table></div>
      <p style="color:var(--ink-3);font-size:12.5px">“Terminal correctness” counts episodes whose agent-reported terminal is <code>failed</code> — the only correct report when success is impossible. Percentiles recomputed from episode durations.</p></div>`
    + `<div class="card"><h2>Failure episodes to study</h2>${examples || '<p style="color:var(--ink-3)">None recorded.</p>'}
      <p><a href="${link('failures', [], { split })}">All failures on this split →</a></p></div>`
    + `<div class="card"><h2>Proposed experiments ${pill('dim', 'not implemented')}</h2>
      <div class="finding"><span class="marker" aria-hidden="true">○</span><span><strong>Designated recoverable set.</strong> Define which failures count as recoverable before measuring any recovery rate. Blocked on: an owner ruling + a recovery implementation. ${pill('dim', 'PROPOSED')}</span></div>
      <div class="finding"><span class="marker" aria-hidden="true">○</span><span><strong>Reset-and-retry protocol.</strong> The demo app exposes an in-page Reset; a recovery study could measure re-attempt success after reset. Blocked on: agent support for reset + a recovery baseline. ${pill('dim', 'PROPOSED')}</span></div>
      <div class="finding"><span class="marker" aria-hidden="true">○</span><span><strong>Recovery attribution vs Baseline A.</strong> Any future recovery rate needs the same replay comparison the success rate uses. Blocked on: the two items above. ${pill('dim', 'PROPOSED')}</span></div>
      <p style="color:var(--ink-3)">Tracked in <code>docs/evaluation.md</code> §10 and the project backlog — not started.</p></div>`;

  el.querySelector('#r-split').addEventListener('change', (e) => {
    window.location.hash = link('recovery', [], { split: e.target.value });
  });
}
