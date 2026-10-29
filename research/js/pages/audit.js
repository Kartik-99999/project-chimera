/* Audit & Reproducibility: samples, verdicts, manifests, rerun facts. */
import { getState, auditStatus, esc, shortHash } from '../data.js';
import { link } from '../app.js';
import { pageHead, pill, auditPill, kvList, jsonView, epLink } from '../components.js';

function planSummary(p) {
  if (!p.data) return { cells: 0, sampled: 0, verdicts: 0, agreed: 0, disagreed: 0, unauditable: 0 };
  let cells = 0, sampled = 0, verdicts = 0, agreed = 0, disagreed = 0, unauditable = 0;
  for (const cell of Object.values(p.data.cells || {})) {
    cells += 1;
    sampled += (cell.sampled || []).length;
    const byTrial = new Map((cell.sampled || []).map((b) => [b.trial_id, b]));
    for (const [trialId, v] of Object.entries(cell.verdicts || {})) {
      verdicts += 1;
      if (v && v.verdict === 'unauditable') { unauditable += 1; continue; }
      const bundle = byTrial.get(trialId);
      if (v && v.checks && bundle && bundle.verifier_checks) {
        const keys = Object.keys(v.checks);
        const same = keys.length === Object.keys(bundle.verifier_checks).length
          && keys.every((k) => v.checks[k] === bundle.verifier_checks[k]);
        if (same) agreed += 1; else disagreed += 1;
      }
    }
  }
  return { cells, sampled, verdicts, agreed, disagreed, unauditable };
}

export async function pageAudit(el) {
  const s = getState();
  const runs = [...s.runs.values()].filter((r) => r.data);
  const runCards = runs.map((r) => {
    const a = auditStatus(r.runId);
    return `<div class="card tight"><h3 class="mono" style="font-size:13px">${esc(r.runId)}</h3>
      <p>${auditPill(a.state)}</p>
      <p style="color:var(--ink-2);font-size:13px">${a.auditedCells}/${a.cells} cells adjudicated`
      + (a.episodes ? ` · ${a.agreed}/${a.episodes} agreed` : ' · no verdicts recorded') + `</p></div>`;
  }).join('');

  const planRows = s.plans.map((p) => {
    const sum = planSummary(p);
    const status = sum.verdicts === 0 ? pill('warn', 'awaiting review')
      : sum.verdicts < sum.sampled ? pill('warn', 'in progress')
      : pill('ok', 'verdicts complete');
    const agree = sum.verdicts ? ` · agree ${sum.agreed} / disagree ${sum.disagreed} / unauditable ${sum.unauditable}` : '';
    return `<tr><td class="mono" style="font-size:12px">${esc(p.file.split('/').pop())}</td>`
      + `<td class="mono" style="font-size:12px">${esc(p.runId.replace('20261028-', ''))}</td>`
      + `<td>${p.kind === 'mini' ? pill('violet', 'mini sample') : pill('dim', 'full sample')}</td>`
      + `<td class="num">${sum.sampled}</td><td class="num">${sum.verdicts}</td>`
      + `<td>${status}<span style="color:var(--ink-3);font-size:12px">${agree}</span></td></tr>`;
  }).join('');

  let reviewQueue = '';
  for (const p of s.plans) {
    if (!p.data || p.kind !== 'mini') continue;
    const items = [];
    for (const [cellKey, cell] of Object.entries(p.data.cells || {})) {
      for (const b of cell.sampled || []) {
        const done = cell.verdicts && cell.verdicts[b.trial_id];
        items.push(`<div class="finding"><span class="marker" aria-hidden="true">${done ? '◆' : '○'}</span>`
          + `<span>${epLink(p.runId, b.trial_id)} <code style="font-size:11.5px">${esc(cellKey)}</code><br>`
          + `<span style="color:var(--ink-3)">expected ${esc(JSON.stringify(b.expected_stored_name))} · agent said ${esc(b.agent_terminal_status)} · ${done ? 'verdict recorded' : 'awaiting review'}</span></span></div>`);
      }
    }
    if (items.length) reviewQueue += `<h3 class="mono" style="font-size:12.5px">${esc(p.file)}</h3>${items.join('')}`;
  }

  const manifests = [...s.manifests.entries()].map(([path, m]) => {
    if (!m) return '';
    const scRows = (m.scenarios || []).map((sc) => (
      `<tr><td class="mono">${esc(sc.id)}</td><td class="num">${(sc.inputs || []).length}</td>`
      + `<td class="mono" style="font-size:12px">${esc((sc.fault_variants || []).map((f) => `slow=${f.slow_ms},dis=${f.disabled}`).join(' · '))}</td>`
      + `<td>${esc(sc.expected_outcome)}</td></tr>`)).join('');
    return `<div class="card"><h2><code>${esc(m.manifest_id)}</code> <span style="color:var(--ink-3);font-weight:400">(${esc(m.split)} split)</span></h2>`
      + kvList([
        ['File', `<code>${esc(path)}</code>`],
        ['Benchmark', `<code>${esc(m.benchmark_id)} v${esc(m.benchmark_version)}</code>`],
        ['Content hash', `<code>${esc(m.manifest_sha256 || (() => { const r = runs.find((x) => x.manifestFile === path); return r && r.data ? r.data.manifest_sha256 : ''; })())}</code>`],
        ['Trials / cell', String((m.config || {}).trials_per_cell ?? '?')],
        ['Warm-ups / run', String((m.config || {}).warmup_episodes ?? '?')],
      ])
      + `<div class="table-wrap" style="margin-top:10px"><table class="data"><thead><tr><th>Scenario</th><th class="num">Inputs</th><th>Fault variants</th><th>Expected</th></tr></thead><tbody>${scRows}</tbody></table></div></div>`;
  }).join('');

  const envs = runs.map((r) => {
    const e = (r.data && r.data.environment) || {};
    return `<div class="card tight"><h3 class="mono" style="font-size:12.5px">${esc(r.runId)}</h3>`
      + kvList([
        ['Agent', `<code>${esc(r.data.agent_version || '?')}</code>`],
        ['Playwright / Chromium', `<code>${esc(e.playwright_version || '?')}</code> / <code>${esc(e.browser_build || '?')}</code>`],
        ['Python / platform', `<code>${esc(e.python_version || '?')}</code> / <code>${esc(e.platform || '?')}</code>`],
        ['demo_app', `<code>${shortHash(e.demo_app_sha256)}</code>`],
        ['Started', esc(r.data.started_at || '?')],
      ]) + `</div>`;
  }).join('');

  el.innerHTML = pageHead('Audit & Reproducibility', [['Audit & Reproducibility']])
    + `<div class="banner warn"><strong>Human review is the gate.</strong> Nothing here adjudicates: dev verdicts below were recorded by a human; eval verdicts are still zero because adjudication was deferred. An empty verdict map is pending work, not agreement.</div>`
    + `<h2>Audit status by run</h2><div class="grid two" style="grid-template-columns:repeat(auto-fit,minmax(250px,1fr))">${runCards || '<div class="card">No runs loaded.</div>'}</div>`
    + `<div class="card"><h2>Audit plans &amp; verdict counts</h2>`
    + (s.plans.length ? `<div class="table-wrap"><table class="data"><thead><tr><th>Plan file</th><th>Run</th><th>Kind</th><th class="num">Sampled</th><th class="num">Verdicts</th><th>Status</th></tr></thead><tbody>${planRows}</tbody></table></div>`
      : '<p style="color:var(--ink-3)">No audit plans loaded.</p>') + `</div>`
    + (reviewQueue ? `<div class="card"><h2>Deferred review queue (mini sample)</h2><p style="color:var(--ink-2)">Adjudicate in the <a href="${link('review')}">mini-review queue</a> (blinded protocol, decisions export to <code>decisions.json</code>) — this console never writes verdict files itself. The plan-verdict CLI remains available for the apply_audit path:</p><pre class="code">.venv/bin/python tools/audit_review.py artifacts/eval-20261028/run-chimera.audit-plan-mini.json artifacts/eval-20261028/run-baseline-a.audit-plan-mini.json</pre>${reviewQueue}</div>` : '')
    + `<h2>Manifests</h2>${manifests || '<div class="card">No manifests loaded.</div>'}`
    + `<h2>Execution environments</h2><div class="grid two">${envs}</div>`;
}
