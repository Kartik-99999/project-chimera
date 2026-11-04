/* Research Archive: reports, manifests, run files, plans. */
import { getState, esc, shortHash, fmtInt } from '../data.js';
import { link } from '../app.js';
import { pageHead, md, jsonView, pill, art, globes, secHead } from '../components.js';

function verdictOf(text) {
  const m = String(text || '').match(/\*\*Verdict:\s*([A-Z]+)\*\*/);
  return m ? m[1] : null;
}

export async function pageArchive(el, { query }) {
  const s = getState();
  const reports = [...s.reports.values()];
  const activeId = query.doc || (reports[0] && reports[0].id) || '';
  const active = s.reports.get(activeId);

  const cards = reports.map((r, ri) => {
    const v = verdictOf(r.text);
    const sel = r.id === activeId;
    return `<div class="card tight${sel ? ' sel' : ''}"${sel ? ' aria-current="true"' : ''}>${art(ri + 1)}
      <div style="font-weight:650"><a href="${link('archive', [], { doc: r.id })}">${esc(r.title)}</a></div>
      <div class="stat-sub"><code>${esc(r.file)}</code> · ${fmtInt((r.text || '').replace(/\n$/, '').split('\n').length)} lines</div>
      <div style="margin-top:6px">${v === 'AUDITED' ? pill('ok', 'AUDITED') : v === 'PROVISIONAL' ? pill('warn', 'PROVISIONAL') : pill('dim', 'no verdict line')}</div>
    </div>`;
  }).join('');

  const runRows = [...s.runs.values()].map((r) => {
    if (!r.data) return `<tr><td class="mono">${esc(r.runId)}</td><td colspan="5"><span class="pill bad">file missing</span></td></tr>`;
    const d = r.data;
    return `<tr><td class="mono" style="font-size:12px"><a href="${link('atlas', [], { run: r.runId })}">${esc(r.runId)}</a></td><td>${esc(r.split)}</td><td>${esc(r.baseline)}</td>`
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

  let totSampled = 0, totVerdicts = 0;
  for (const p of s.plans) {
    if (!p.data) continue;
    for (const c of Object.values(p.data.cells || {})) {
      totSampled += (c.sampled || []).length;
      totVerdicts += Object.keys(c.verdicts || {}).length;
    }
  }
  const manGlass = [...s.manifests.values()].filter(Boolean).map((m) => (
    `<span class="glass"><span class="dot" style="background:#8fb4ff"></span>${esc(m.manifest_id)} · ${esc((m.manifest_sha256 || '').slice(0, 12))}…</span>`)).join('');
  const navy = `<div class="navy">${globes()}<h2>Plans &amp; manifests</h2>`
    + `<p class="sub">${s.plans.length} audit plans (${totSampled} sampled, ${totVerdicts} verdicts) and ${s.manifests.size} manifests pin every figure on this console.</p>`
    + `<p>${manGlass}<span class="glass"><span class="dot" style="background:#fbbf24"></span>${totSampled} sampled · ${totVerdicts} verdicts</span></p></div>`;
  const dlCard = `<div class="card" id="archive-pdf"><div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap">`
    + `<svg viewBox="0 0 40 40" width="44" height="44" aria-hidden="true" style="flex:none"><rect x="8" y="3" width="24" height="34" rx="3" fill="#fff" stroke="#0e7490" stroke-width="2"/><path d="M14 3v8h8" fill="none" stroke="#0e7490" stroke-width="2"/><path d="M20 17v10M15.5 22.5L20 27l4.5-4.5M15 31.5h10" fill="none" stroke="#C0563B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`
    + `<div style="flex:1;min-width:220px"><div style="font-weight:650;font-size:15px">Complete archive (PDF)</div>`
    + `<div class="stat-sub" id="archive-pdf-meta">Every report, run, episode, plan and manifest in one document.</div></div>`
    + `<a class="btn primary" href="/research/assets/research-archive.pdf" download="chimera-research-archive.pdf"><svg viewBox="0 0 20 20" width="16" height="16" aria-hidden="true"><path d="M10 3v10M6 9.5L10 13.5 14 9.5M4 16.5h12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>Download PDF</a>`
    + `</div></div>`;
  el.innerHTML = pageHead('Research Archive', [['Research Archive']], '', {
    kicker: 'Route #/archive',
    lede: 'Reports, run files, audit plans, manifests — the paper trail behind every figure. Select a report to read it in the document viewer, or download the whole archive as one PDF.',
    meta: `<span class="pill"><span class="dot"></span>${reports.length} reports</span><span class="pill"><span class="dot"></span>${[...s.runs.values()].filter((r) => r.data).length} run files</span><span class="pill"><span class="dot"></span>${s.plans.length} plans</span>`,
  })
    + dlCard
    + secHead('Reports', 'Rendered from the markdown sources, tables intact.')
    + `<div class="grid g3">${cards || '<div class="card">No reports loaded.</div>'}</div>`
    + (active ? `<div class="card slim" id="doc-viewer"><details class="disclosure"${query.doc ? ' open' : ''}><summary>Read: ${esc(active.title)} <span style="color:var(--ink-3);font-weight:400">· <code>${esc(active.file)}</code> · full text, ${fmtInt((active.text || '').split('\n').length)} lines</span></summary><div class="body">${md(active.text)}</div></details></div>` : '')
    + secHead('Run files', `${[...s.runs.values()].filter((r) => r.data).length} files · every measured episode accounted`)
    + `<div class="card slim"><div class="table-wrap"><table class="data"><thead><tr><th>Run</th><th>Split</th><th>Baseline</th><th class="num">Cells</th><th class="num">Episodes</th><th>Window</th></tr></thead><tbody>${runRows}</tbody></table></div>
      <p style="color:var(--ink-3);font-size:12.5px">Episode evidence (traces, snapshots, action logs) lives beside each run file under <code>artifacts/</code> and is fetched on demand by the Evidence Inspector — never duplicated here.</p></div>`
    + navy
    + `<div class="card slim"><h2>Audit plans</h2><div class="table-wrap"><table class="data"><thead><tr><th>Plan</th><th>Run</th><th>Kind</th><th class="num">Sampled</th><th class="num">Verdicts</th></tr></thead><tbody>${planRows || '<tr><td colspan="5">None loaded.</td></tr>'}</tbody></table></div></div>`
    + secHead('Manifests', 'Content hashes pin every run.')
    + `<div class="grid g2">${manBlocks}</div>`;

  const viewer = el.querySelector('#doc-viewer');
  if (viewer && query.doc) viewer.scrollIntoView({ block: 'start' });
  const pdfMeta = el.querySelector('#archive-pdf-meta');
  if (pdfMeta) {
    fetch('/research/assets/research-archive.meta.json', { cache: 'no-store' })
      .then((res) => (res.ok ? res.json() : null))
      .then((meta) => {
        if (!meta) return;
        const c = meta.counts || {};
        const mb = meta.pdf_bytes ? (meta.pdf_bytes / 1048576).toFixed(1) : '?';
        pdfMeta.textContent = `${c.reports || '?'} reports · ${c.episodes || '?'} episodes · `
          + `${c.plans || '?'} plans · ${meta.pdf_pages || '?'} pages · ${mb} MB · generated ${meta.generated_at_utc || '?'} UTC`;
      })
      .catch(() => {});
  }
}
