/* Provenance Graph: validated lineage for one run cell.
 * manifest → run (→ audited) → cell → episodes → artifacts, plus
 * verdict, plan, and report nodes joined by recorded identifiers.
 * Every edge label states its check; invalid edges and missing nodes
 * stay visible. Node and edge tables below list the same graph.
 */
import { getState, getRun, rootPath, esc, fmtInt } from '../data.js';
import { sliceCells, matchCellKey } from '../viz/stats.js';
import { buildLineage, cellKeyOf } from '../viz/lineageModel.js';
import { attachTip } from '../viz/tooltip.js';
import { link } from '../app.js';
import { pageHead, emptyState, kvList } from '../components.js';

const LAYERS = ['Manifest', 'Run', 'Cell', 'Episodes', 'Artifacts', 'Verdicts', 'Plans & reports'];
const KIND_COLORS = {
  manifest: '#a78bfa', run: '#39d0d8', audited: '#2aa8af', cell: '#6ea8fe',
  episode: '#a6b0c2', artifacts: '#69748a', verdict: '#e5a83b', plan: '#a78bfa', report: '#8b94a7',
};

async function fetchOk(path) {
  try {
    const res = await fetch(rootPath(path), { cache: 'no-store' });
    return res.ok;
  } catch { return false; }
}

export async function pageLineage(el, { query }) {
  const s = getState();
  const runId = query.run || 'eval-20261028-chimera';
  const run = getRun(runId);
  if (!run) {
    el.innerHTML = pageHead('Provenance Graph', [['Provenance Graph']]) + emptyState(
      'Run evidence missing', `Run file for <code>${esc(runId)}</code> did not load.`);
    return;
  }
  let sliced;
  try {
    sliced = sliceCells(run.data.cells || [], run.data.episodes || []);
  } catch (err) {
    el.innerHTML = pageHead('Provenance Graph', [['Provenance Graph']])
      + `<div class="banner warn"><strong>Cannot map episodes to cells:</strong> ${esc(err.message)}. Refusing to render rather than misattributing trials.</div>`;
    return;
  }
  const options = sliced.map(({ cell }) => ({ key: cellKeyOf(cell), label: `${cell.scenario_id} · ${cell.input_id} · ${JSON.stringify(cell.fault_params || {})}` }));
  const hit = sliced.find(({ cell }) => matchCellKey(cell, query.cell || ''));
  const cellKey = hit ? cellKeyOf(hit.cell) : options[0].key;
  const q = (query.q || '').trim().toLowerCase();
  const selected = query.node || '';

  const manifest = s.manifests.get(run.manifestFile) || null;
  const plans = s.plans.filter((p) => p.runId === runId && p.data).map((p) => ({ kind: p.kind, data: p.data }));
  const reports = [...s.reports.values()].filter((r) => r.text).map((r) => ({ id: r.id, title: r.title, text: r.text }));
  const auditedData = s.audited.get(runId) || null;
  const { episodes } = sliced.find(({ cell }) => cellKeyOf(cell) === cellKey);
  const presence = {};
  await Promise.all(episodes.flatMap((ep) => {
    if (!ep.trace_artifact) return [];
    const i = ep.trace_artifact.lastIndexOf('/');
    const base = ep.trace_artifact.slice(i + 1).split('.')[0];
    const dir = ep.trace_artifact.slice(0, i + 1);
    return [ep.trace_artifact, `${dir}${base}.snapshot.json`, `${dir}${base}.actions.json`]
      .map(async (p) => { presence[p] = await fetchOk(p); });
  }));
  const { nodes, edges, issues } = buildLineage({
    manifest, manifestPath: run.manifestFile, run, auditedData, plans, reports, cellKey, presence,
  });

  // Layered layout: columns per layer, nodes stacked and centered.
  const NW = 138, NH = 50, colW = 168, padL = 86, padT = 34, rowH = 64;
  const byLayer = LAYERS.map((_, li) => nodes.filter((n) => n.layer === li));
  const H = padT + Math.max(...byLayer.map((l) => l.length)) * rowH + 16;
  const W = padL * 2 + (LAYERS.length - 1) * colW;
  const pos = new Map();
  byLayer.forEach((list, li) => {
    const x0 = padL + li * colW;
    const yStart = padT + (Math.max(...byLayer.map((l) => l.length)) - list.length) * rowH / 2;
    list.forEach((n, i) => pos.set(n.id, { x: x0, y: yStart + i * rowH }));
  });
  const neighbors = new Map(nodes.map((n) => [n.id, new Set([n.id])]));
  for (const e of edges) {
    if (neighbors.has(e.from)) neighbors.get(e.from).add(e.to);
    if (neighbors.has(e.to)) neighbors.get(e.to).add(e.from);
  }
  const matchQ = (n) => !q || `${n.label} ${n.sub || ''} ${n.kind}`.toLowerCase().includes(q);
  const dimmed = (id) => (selected && !(neighbors.get(selected) || new Set()).has(id)) || !matchQ(nodes.find((n) => n.id === id));

  const hrefOf = (h) => (h ? link(h.route, h.params || [], h.query || {}) : '');
  let svg = `<svg class="chart" viewBox="0 0 ${W} ${H}" role="group" aria-label="Provenance graph for cell ${esc(cellKey)}">`;
  svg += LAYERS.map((t, i) => `<text x="${padL + i * colW}" y="16" text-anchor="middle" font-size="12" font-weight="700" fill="#e8ecf3">${esc(t)}</text>`).join('');
  for (const e of edges) {
    const a = pos.get(e.from), b = pos.get(e.to);
    if (!a || !b) continue;
    const x0 = a.x + NW / 2, x1 = b.x - NW / 2, mx = (x0 + x1) / 2;
    const y0 = a.y + NH / 2, y1 = b.y + NH / 2;
    const d = `M${x0},${y0} C${mx},${y0} ${mx},${y1} ${x1},${y1}`;
    const tip = `${e.from} → ${e.to}: ${e.label}`;
    svg += `<g class="lineage-edge${dimmed(e.from) || dimmed(e.to) ? ' dimmed' : ''}">`
      + `<path d="${d}" fill="none" stroke="${e.valid ? '#3b4763' : '#e5606e'}" stroke-width="${e.valid ? 1.6 : 2.4}"${e.valid ? '' : ' stroke-dasharray="5 3"'}>`
      + `<title>${esc(tip)}</title></path></g>`;
  }
  for (const n of nodes) {
    const p = pos.get(n.id);
    const col = KIND_COLORS[n.kind] || '#a6b0c2';
    const tip = `${n.label} — ${n.sub || n.kind}${n.missing ? ' (missing)' : ''}`;
    const label = n.label.length > 20 ? `${n.label.slice(0, 19)}…` : n.label;
    const sub = (n.sub || '').length > 24 ? `${(n.sub || '').slice(0, 23)}…` : (n.sub || '');
    svg += `<g class="lineage-node${dimmed(n.id) ? ' dimmed' : ''}${selected === n.id ? ' sel' : ''}" data-node="${esc(n.id)}" tabindex="0" role="button" aria-label="${esc(tip)}" data-tip="${esc(tip)} — select for details">`
      + `<circle class="halo" cx="${p.x}" cy="${p.y + NH / 2}" r="30" fill="transparent"/>`
      + `<rect x="${p.x - NW / 2}" y="${p.y}" width="${NW}" height="${NH}" rx="8" fill="#101623" stroke="${n.missing ? '#e5606e' : col}" stroke-width="${selected === n.id ? 2.6 : 1.6}"${n.missing ? ' stroke-dasharray="5 3"' : ''}/>`
      + `<circle cx="${p.x - NW / 2 + 13}" cy="${p.y + 14}" r="4" fill="${col}"/>`
      + `<text x="${p.x - NW / 2 + 22}" y="${p.y + 18}" font-size="10.5" font-weight="700" fill="#e8ecf3">${esc(label)}</text>`
      + `<text x="${p.x - NW / 2 + 10}" y="${p.y + 35}" font-size="9.5" fill="#a6b0c2">${esc(sub)}</text>`
      + `<title>${esc(tip)}</title></g>`;
  }
  svg += '</svg>';

  const sel = selected && nodes.find((n) => n.id === selected);
  const detail = !sel
    ? '<p style="color:var(--ink-3)">Select a node to inspect its identifiers and open the underlying record. Search dims non-matching nodes.</p>'
    : `<h3 style="font-size:13px;margin:0 0 6px">${esc(sel.label)}</h3>`
      + `<p style="color:var(--ink-2);margin-top:0">${esc(LAYERS[sel.layer])} · ${esc(sel.kind)}${sel.missing ? ' · <strong>missing</strong>' : ''}<br>${esc(sel.sub || '')}</p>`
      + kvList((sel.meta || []).map(([k, v]) => [k, `<code>${esc(v)}</code>`]))
      + (hrefOf(sel.href) ? `<p><a class="btn" href="${hrefOf(sel.href)}">Open record →</a></p>` : '<p style="color:var(--ink-3)">No console view for this node; identifiers above are the evidence.</p>');

  const nodeRows = nodes.map((n) => (
    `<tr><td>${esc(LAYERS[n.layer])}</td><td>${esc(n.kind)}</td><td><strong>${esc(n.label)}</strong></td>`
    + `<td style="font-size:12px">${esc(n.sub || '')}</td><td>${n.missing ? 'missing' : 'present'}</td>`
    + `<td>${hrefOf(n.href) ? `<a href="${hrefOf(n.href)}">open →</a>` : '—'}</td></tr>`)).join('');
  const edgeRows = edges.map((e) => (
    `<tr><td class="mono" style="font-size:11.5px">${esc(e.from)}</td><td class="mono" style="font-size:11.5px">${esc(e.to)}</td>`
    + `<td style="font-size:12px">${esc(e.label)}</td><td>${e.valid ? '✓ valid' : '✗ INVALID'}</td></tr>`)).join('');
  const banners = issues.map((i) => `<div class="banner ${i.severity === 'error' ? 'bad' : 'info'}">${esc(i.text)}</div>`).join('');

  el.innerHTML = pageHead('Provenance Graph', [['Provenance Graph']]) + banners
    + `<div class="card"><div class="filters">
        <div class="field"><label for="l-run">Run</label><select id="l-run">${['eval-20261028-chimera', 'eval-20261028-baseline-a', 'dev-20261028-chimera', 'dev-20261028-baseline-a'].map((r) => `<option value="${r}"${r === runId ? ' selected' : ''}>${r}</option>`).join('')}</select></div>
        <div class="field" style="min-width:280px"><label for="l-cell">Cell</label><select id="l-cell">${options.map((o) => `<option value="${esc(o.key)}"${o.key === cellKey ? ' selected' : ''}>${esc(o.label)}</option>`).join('')}</select></div>
        <div class="field"><label for="l-q">Search nodes</label><input type="search" id="l-q" value="${esc(query.q || '')}" placeholder="trial id, plan, report…"></div>
      </div>
      <p style="color:var(--ink-2)"><strong>${fmtInt(nodes.length)} nodes · ${fmtInt(edges.length)} edges.</strong> Every edge states its identifier check; red dashed edges failed validation and red dashed nodes are missing. Artifact presence was checked against this checkout just now.</p>
      <div class="table-wrap" tabindex="0" aria-label="Provenance graph, scrollable">${svg}</div></div>`
    + `<div class="card" id="lineage-detail"><h2>Node detail</h2>${detail}</div>`
    + `<div class="card"><h2>Nodes (table alternative)</h2><div class="table-wrap"><table class="data"><thead><tr><th>Layer</th><th>Kind</th><th>Node</th><th>Detail</th><th>Status</th><th></th></tr></thead><tbody>${nodeRows}</tbody></table></div></div>`
    + `<div class="card"><h2>Edges (table alternative)</h2><div class="table-wrap"><table class="data"><thead><tr><th>From</th><th>To</th><th>Relationship check</th><th>Valid</th></tr></thead><tbody>${edgeRows}</tbody></table></div></div>`;

  const nav = (patch) => {
    window.location.hash = link('lineage', [], {
      run: el.querySelector('#l-run').value, cell: el.querySelector('#l-cell').value,
      q: el.querySelector('#l-q').value, node: selected, ...patch,
    });
  };
  el.querySelector('#l-run').addEventListener('change', () => nav({ cell: '', node: '' }));
  el.querySelector('#l-cell').addEventListener('change', () => nav({ node: '' }));
  el.querySelector('#l-q').addEventListener('change', () => nav({}));
  el.querySelectorAll('.lineage-node').forEach((g) => {
    const fire = () => nav({ node: g.dataset.node === selected ? '' : g.dataset.node });
    g.addEventListener('click', (e) => { e.preventDefault(); fire(); });
    g.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fire(); }
      else if (e.key === 'Escape') nav({ node: '' });
    });
    attachTip(g, g.dataset.tip);
  });
}
