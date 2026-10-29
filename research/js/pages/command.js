/* Command Center: status, KPIs, constellation, findings, runs. */
import { getState, getRun, measuredEpisodes, isFalseSuccess, isHarnessError,
  wilsonUpper, auditStatus, esc, fmtInt, fmtMs, fmtPct, baselineLabel, SCENARIOS } from '../data.js';
import { link } from '../app.js';
import { pageHead, pill, statCard, outcomePill, baselineTag, emptyState, kvList } from '../components.js';
import { constellation } from '../charts.js';

function successBy(split, scenario, baseline) {
  const eps = measuredEpisodes().filter((e) => e.split === split && e.scenario_id === scenario && e.baseline === baseline);
  const k = eps.filter((e) => e.outcome === 'succeeded').length;
  return { k, n: eps.length };
}

function findings() {
  const out = [];
  for (const split of ['development', 'evaluation']) {
    const c = successBy(split, 'S-SLOW', 'chimera');
    const r = successBy(split, 'S-SLOW', 'baseline-a');
    if (c.n > 0 && r.n > 0 && c.k === c.n && r.k === 0) {
      out.push({ text: `<strong>S-SLOW separates the baselines on ${split}:</strong> Chimera ${c.k}/${c.n}, replay ${r.k}/${r.n}. Waiting clears every transient-slow cell; fixed replay clears none.`, href: link('observatory', [], { split, scenario: 'S-SLOW' }) });
    }
  }
  for (const split of ['development', 'evaluation']) {
    let k = 0, n = 0, he = 0;
    for (const sc of ['S-DIS', 'S-SLOWDIS']) {
      for (const b of ['chimera', 'baseline-a']) {
        const s = successBy(split, sc, b);
        k += s.k; n += s.n;
      }
      he += measuredEpisodes().filter((e) => e.split === split && e.scenario_id === sc && isHarnessError(e)).length;
    }
    if (n > 0 && k === 0 && he === 0) {
      out.push({ text: `<strong>Persistent faults fail boundedly on ${split}:</strong> 0/${n} succeeded and 0 harness errors across S-DIS/S-SLOWDIS — the expected bounded outcome, not a crash.`, href: link('failures', [], { split }) });
    }
  }
  const fs = measuredEpisodes().filter(isFalseSuccess).length;
  const n = measuredEpisodes().length;
  if (n > 0 && fs === 0) {
    const b = wilsonUpper(0, n);
    out.push({ text: `<strong>No false successes in ${fmtInt(n)} measured episodes</strong> (pooled 95% Wilson upper bound ${(b * 100).toFixed(1)}%). Per-cell bounds are wider — see the Observatory.`, href: link('observatory', [], {}) });
  }
  return out;
}

function constellationModel() {
  const s = getState();
  const runs = [...s.runs.values()];
  const audits = [];
  for (const r of runs) {
    const a = auditStatus(r.runId);
    const tag = `${r.split === 'development' ? 'dev' : 'eval'}·${r.baseline === 'chimera' ? 'chimera' : 'replay'}`;
    audits.push({
      runId: r.runId, state: a.state === 'audited' ? 'audited' : 'pending',
      label: a.state === 'audited' ? `✓ ${tag}` : `… ${tag}`,
      blurb: a.state === 'audited'
        ? `${a.auditedCells}/${a.cells} cells, ${a.agreed}/${a.episodes} agreed`
        : `${a.auditedCells}/${a.cells} cells adjudicated — provisional`,
    });
  }
  return { runs, episodes: s.episodes, auditNodes: audits };
}

export async function pageCommand(el) {
  const s = getState();
  if (![...s.runs.values()].some((r) => r.data)) {
    el.innerHTML = pageHead('Command Center', [['Command Center']]) + emptyState(
      'No run evidence loaded',
      'None of the four expected run files could be fetched. Serve the repository root (<code>python -m http.server</code>) and reload.',
    );
    return;
  }
  const eps = measuredEpisodes();
  const succ = eps.filter((e) => e.outcome === 'succeeded').length;
  const fs = eps.filter(isFalseSuccess).length;
  const he = eps.filter(isHarnessError).length;
  const bound = wilsonUpper(fs, eps.length);
  const evalAud = ['eval-20261028-chimera', 'eval-20261028-baseline-a'].map(auditStatus);
  const evalAudited = evalAud.every((a) => a.state === 'audited');
  const banner = evalAudited
    ? `<div class="banner info"><strong>Evaluation audited.</strong> Held-out figures carry human-reviewed agreement — see the ${`<a href="${link('audit')}">audit workspace</a>`} for coverage and rates.</div>`
    : `<div class="banner warn"><strong>Evaluation provisional.</strong> Held-out runs are complete but no eval audit sample is adjudicated. Figures below are measurements with denominators, not vetted claims. ${`<a href="${link('audit')}">Review audit status →</a>`}</div>`;

  const kpis = [
    statCard({ value: fmtInt(eps.length), label: 'Measured episodes', sub: 'warm-ups excluded', href: link('atlas') }),
    statCard({ value: `${fmtInt(succ)}<span style="color:var(--ink-3);font-size:16px">/${fmtInt(eps.length)}</span>`, label: 'Succeeded (pooled)', sub: `${fmtPct(succ, eps.length)} — splits differ, drill down`, href: link('observatory') }),
    statCard({ value: `${fs}<span style="color:var(--ink-3);font-size:16px">/${eps.length}</span>`, label: 'False successes', sub: bound == null ? 'no denominator' : `95% Wilson ≤ ${(bound * 100).toFixed(1)}%`, href: link('atlas', [], { outcome: 'false-success' }) }),
    statCard({ value: String(he), label: 'Harness errors', sub: he === 0 ? 'clean execution' : 'needs triage', href: link('atlas', [], { outcome: 'harness-error' }) }),
  ].join('');

  const finds = findings();
  const findsHtml = finds.length ? finds.map((f) => (
    `<div class="finding"><span class="marker" aria-hidden="true">◆</span><span>${f.text} <a href="${f.href}">Investigate →</a></span></div>`)).join('')
    : '<p style="color:var(--ink-3)">No summary findings derive from the loaded runs yet.</p>';

  const pending = [];
  for (const runId of ['eval-20261028-chimera', 'eval-20261028-baseline-a']) {
    const a = auditStatus(runId);
    if (a.state !== 'audited') {
      pending.push(`<div class="finding"><span class="marker" aria-hidden="true">○</span><span><code>${esc(runId)}</code> — ${a.auditedCells}/${a.cells} cells adjudicated. <a href="${link('audit')}">Open audit workspace →</a></span></div>`);
    }
  }

  const runRows = [...s.runs.values()].filter((r) => r.data).map((r) => {
    const a = auditStatus(r.runId);
    const c = (r.data.cells || []).length, n = (r.data.episodes || []).filter((e) => !String(e.trial_id).startsWith('warmup:')).length;
    const audit = a.state === 'audited' ? pill('ok', `audited ${a.agreed}/${a.episodes}`) : pill('warn', 'provisional');
    return `<tr><td class="mono"><a href="${link('atlas', [], { run: r.runId })}">${esc(r.runId)}</a></td>`
      + `<td>${esc(r.split)}</td><td>${baselineTag(r.baseline)}</td>`
      + `<td class="num">${c}</td><td class="num">${n}</td><td>${audit}</td></tr>`;
  }).join('');

  const cons = constellation({ compact: true });
  el.innerHTML = pageHead('Command Center', [['Command Center']])
    + banner
    + `<div class="grid kpi" role="list">${kpis}</div>`
    + `<div class="grid two-wide"><div class="card"><h2>Evidence constellation</h2>${cons.render(constellationModel())}`
    + `<p style="margin-top:8px"><a href="${link('map')}">Open fullscreen map →</a></p></div>`
    + `<div class="card"><h2>Notable findings</h2>${findsHtml}</div></div>`
    + (pending.length ? `<div class="card"><h2>Pending audit work</h2>${pending.join('')}</div>` : '')
    + `<div class="card"><h2>Runs</h2><div class="table-wrap"><table class="data"><thead><tr><th>Run</th><th>Split</th><th>Baseline</th><th class="num">Cells</th><th class="num">Episodes</th><th>Audit</th></tr></thead><tbody>${runRows}</tbody></table></div></div>`;
  cons.bind(el);
}
