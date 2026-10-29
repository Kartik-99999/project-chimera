/* Research Archive: reports, manifests, run files, plans. */
import { getState, esc, shortHash, fmtInt } from '../data.js';
import { link } from '../app.js';
import { pageHead, md, jsonView, pill } from '../components.js';

function verdictOf(text) {
  const m = String(text || '').match(/\*\*Verdict:\s*([A-Z]+)\*\*/);
  return m ? m[1] : null;
}

export async function pageArchive(el, { query }) {
  const s = getState();
  const reports = [...s.reports.values()];
  const activeId = query.doc || (reports[0] && reports[0].id) || '';
  const active = s.reports.get(activeId);

  const cards = reports.map((r) => {
    const v = verdictOf(r.text);
    const sel = r.id === activeId;
    return `<div class="card tight" style="${sel ? 'border-color:var(--cyan)' : ''}">
      <div style="font-weight:650"><a href="${link('archive', [], { doc: r.id })}">${esc(r.title)}</a></div>
      <div class="stat-sub"><code>${esc(r.file)}</code> · ${fmtInt((r.text || '').replace(/\n$/, '').split('\n').length)} lines</div>
      <div style="margin-top:6px">${v === 'AUDITED' ? pill('ok', 'AUDITED') : v === 'PROVISIONAL' ? pill('warn', 'PROVISIONAL') : pill('dim', 'no verdict line')}</div>
    </div>`;
  }).join('');

  const runRows = [...s.runs.values()].map((r) => {
    if (!r.data) return `<tr><td class="mono">${esc(r.runId)}</td><td colspan="5"><span class="pill bad">file missing</span></td></tr>`;
    const d = r.data;
    return `<tr><td class="mono" style="font-size:12px">${esc(r.runId)}</td><td>${esc(r.split)}</td><td>${esc(r.baseline)}</td>`
      + `<td class="num">${(d.cells || []).length}</td><td class="num">${(d.episodes || []).length}</td>`
      + `<td class="mono" style="font-size:11.5px">${esc(d.started_at || '?')} → ${esc(d.completed_at || '?')}</td></tr>`;
  }).join('');

  const planRows = s.plans.map((p) => {
    if (!p.data) return `<tr><td class="mono">${esc(p.file)}</td><td colspan="4"><span class="pill bad">file missing</span></td></tr>`;
    const cells = Object.values(p.data.cells || {});
    const sampled = cells.reduce((n, c) => n + (c.sampled || []).length, 0);
    const verdicts = cells.reduce((n, c) => n + Object.keys(c.verdicts || {}).length, 0);
    return `<tr><td class="mono" style="font-size:12px">${esc(p.file.split('/').pop())}</td>`
      + `<td class="mono" style="font-size:12px">${esc(p.runId)}</td><td>${p.kind}</td>`
      + `<td class="num">${sampled}</td><td class="num">${verdicts}</td></tr>`;
  }).join('');

  const manBlocks = [...s.manifests.entries()].map(([path, m]) => (
    `<div class="card tight"><h3 class="mono" style="font-size:12.5px">${esc(path)}</h3>`
    + (m ? `<p style="color:var(--ink-2);font-size:13px">${esc(m.manifest_id)} · ${esc(m.split)} · ${(m.scenarios || []).length} scenarios</p>${jsonView(m, 'Manifest JSON')}`
      : '<p><span class="pill bad">file missing</span></p>') + `</div>`
  )).join('');

  el.innerHTML = pageHead('Research Archive', [['Research Archive']])
    + `<h2>Reports</h2><div class="grid two" style="grid-template-columns:repeat(auto-fit,minmax(260px,1fr))">${cards || '<div class="card">No reports loaded.</div>'}</div>`
    + (active ? `<div class="card" id="doc-viewer"><h2>${esc(active.title)}</h2><p style="color:var(--ink-3)"><code>${esc(active.file)}</code></p>${md(active.text)}</div>` : '')
    + `<h2>Run files</h2><div class="card"><div class="table-wrap"><table class="data"><thead><tr><th>Run</th><th>Split</th><th>Baseline</th><th class="num">Cells</th><th class="num">Episodes</th><th>Window</th></tr></thead><tbody>${runRows}</tbody></table></div>
      <p style="color:var(--ink-3);font-size:12.5px">Episode evidence (traces, snapshots, action logs) lives beside each run file under <code>artifacts/</code> and is fetched on demand by the Evidence Inspector — never duplicated here.</p></div>`
    + `<h2>Audit plans</h2><div class="card"><div class="table-wrap"><table class="data"><thead><tr><th>Plan</th><th>Run</th><th>Kind</th><th class="num">Sampled</th><th class="num">Verdicts</th></tr></thead><tbody>${planRows || '<tr><td colspan="5">None loaded.</td></tr>'}</tbody></table></div></div>`
    + `<h2>Manifests</h2><div class="grid two">${manBlocks}</div>`;

  const viewer = el.querySelector('#doc-viewer');
  if (viewer && query.doc) viewer.scrollIntoView({ block: 'start' });
}
