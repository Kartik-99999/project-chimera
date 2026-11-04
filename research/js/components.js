/* Shared presentational components. Pure render helpers + small widgets. */
import { esc, mVal, fmtInt, baselineLabel } from './data.js';

export function pageHead(title, crumb = [], actions = '', opts = null) {
  const trail = crumb.map((c, i) => {
    const last = i === crumb.length - 1;
    return last ? `<span aria-current="page">${esc(c[0])}</span>`
      : `<a href="${c[1]}">${esc(c[0])}</a>`;
  }).join(' <span aria-hidden="true">›</span> ');
  // Hero variant: the same h1/crumb inside the organic pastel field.
  // opts = { kicker, lede, meta } — all values are caller-trusted HTML.
  if (opts && (opts.kicker || opts.lede || opts.meta)) {
    return `<div class="hero"><div class="crumb">${trail}</div>`
      + (opts.kicker ? `<span class="kicker">${opts.kicker}</span>` : '')
      + `<div class="page-head"><div><h1>${esc(title)}</h1></div><div class="btn-row">${actions}</div></div>`
      + (opts.lede ? `<p class="lede">${opts.lede}</p>` : '')
      + (opts.meta ? `<div class="meta">${opts.meta}</div>` : '')
      + `</div>`;
  }
  return `<div class="crumb">${trail}</div>
    <div class="page-head"><div><h1>${esc(title)}</h1></div><div class="btn-row">${actions}</div></div>`;
}

/* Card-top art banner: pastel contour wash, procedural inline SVG. */
const ART_PATHS = [
  '<path d="M-10 70 C 120 40, 200 84, 330 52 S 520 30, 620 58"/><path d="M-10 80 C 140 52, 230 92, 360 62 S 530 44, 620 68" opacity=".6"/><circle cx="492" cy="24" r="14" opacity=".55"/><circle cx="120" cy="20" r="7" opacity=".5"/>',
  '<path d="M-10 60 C 150 20, 260 78, 420 40 S 560 30, 620 52"/><circle cx="90" cy="26" r="9"/><circle cx="500" cy="60" r="6"/>',
  '<path d="M-10 50 C 160 80, 300 24, 460 58 S 570 50, 620 40"/><circle cx="200" cy="30" r="7"/><circle cx="430" cy="62" r="10"/>',
  '<path d="M-10 64 C 170 30, 280 74, 440 44 S 570 36, 620 56"/><circle cx="150" cy="58" r="8"/>',
  '<path d="M-10 44 C 150 70, 300 30, 470 60 S 570 52, 620 46"/><circle cx="330" cy="26" r="8"/>',
];
const ART_HUES = ['peach', 'sky', 'mint', 'lilac', 'rose'];
export function art(i = 0) {
  const n = ((i % ART_HUES.length) + ART_HUES.length) % ART_HUES.length;
  return `<div class="art ${ART_HUES[n]}" aria-hidden="true"><svg viewBox="0 0 600 88" preserveAspectRatio="none"><g fill="none" stroke="#ffffff" stroke-width="1.6" opacity=".85">${ART_PATHS[n]}</g></svg></div>`;
}

/* Wireframe globes for navy immersive panels (decorative). */
export function globes() {
  return `<svg class="globe" viewBox="0 0 200 200" aria-hidden="true"><g fill="none" stroke="#8fb4ff" stroke-width="1"><circle cx="100" cy="100" r="90"/><circle cx="100" cy="100" r="66"/><circle cx="100" cy="100" r="42"/><ellipse cx="100" cy="100" rx="90" ry="34"/><ellipse cx="100" cy="100" rx="90" ry="66"/><line x1="10" y1="100" x2="190" y2="100"/><line x1="100" y1="10" x2="100" y2="190"/></g></svg>`
    + `<svg class="globe two" viewBox="0 0 200 200" aria-hidden="true"><g fill="none" stroke="#ffc9a3" stroke-width="1"><circle cx="100" cy="100" r="90"/><ellipse cx="100" cy="100" rx="90" ry="36"/><line x1="100" y1="10" x2="100" y2="190"/></g></svg>`;
}

export function secHead(title, sub = '', side = '') {
  return `<div class="sec-head"><h2>${esc(title)}</h2>${sub ? `<p>${sub}</p>` : ''}${side ? `<span class="side">${side}</span>` : ''}</div>`;
}

export function pill(kind, text) {
  return `<span class="pill ${kind}"><span class="dot" aria-hidden="true"></span>${esc(text)}</span>`;
}

export function outcomePill(outcome, harnessError = false) {
  if (harnessError) return pill('bad', 'harness error');
  if (outcome === 'succeeded') return pill('ok', 'succeeded');
  if (outcome === 'failed') return pill('bad', 'failed');
  if (outcome === 'cancelled') return pill('warn', 'cancelled');
  return pill('dim', outcome || 'unknown');
}

export function auditPill(state) {
  if (state === 'audited') return pill('ok', 'audited');
  if (state === 'partial') return pill('warn', 'partially audited');
  return pill('warn', 'provisional');
}

export function statCard({ value, label, sub = '', href = '', cls = '' }) {
  const inner = `<div class="stat-value">${value}</div><div class="stat-label">${esc(label)}</div>`
    + (sub ? `<div class="stat-sub">${sub}</div>` : '');
  const klass = cls ? `card tight stat ${cls}` : 'card tight stat';
  return href ? `<a class="${klass}" href="${href}">${inner}</a>`
    : `<div class="${klass}">${inner}</div>`;
}

export function emptyState(title, body, action = '') {
  return `<div class="card empty"><h3>${esc(title)}</h3><p>${body}</p>${action}</div>`;
}

export function kvList(rows) {
  return `<dl class="kv">${rows.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${v}</dd>`).join('')}</dl>`;
}

export function metricCell(metric) {
  const m = mVal(metric);
  if (!m.ok) return `<span class="pill dim" title="${esc(m.reason)}">null</span>`;
  const v = m.value;
  if (v != null && typeof v === 'object') {
    if (v.mean_per_trial != null) return `<span class="num">${Number(v.mean_per_trial).toFixed(1)}</span>`;
    if (v.total != null) return `<span class="num">${fmtInt(v.total)}</span>`;
    return `<span class="mono">${esc(JSON.stringify(v))}</span>`;
  }
  return `<span class="num">${esc(String(v))}</span>`;
}

/** Sortable, paginated table. Columns: [{key,label,num,render}]. */
export function dataTable({ id, columns, rows, sortKey, sortDir = 1, page = 1, perPage = 15, onSort, rowHref }) {
  const sorted = [...rows].sort((a, b) => {
    const col = columns.find((c) => c.key === sortKey) || columns[0];
    const va = col.value ? col.value(a) : a[col.key];
    const vb = col.value ? col.value(b) : b[col.key];
    const an = va == null, bn = vb == null;
    if (an && bn) return 0;
    if (an) return 1;
    if (bn) return -1;
    return (va < vb ? -1 : va > vb ? 1 : 0) * sortDir;
  });
  const pages = Math.max(1, Math.ceil(sorted.length / perPage));
  const p = Math.min(Math.max(1, page), pages);
  const slice = sorted.slice((p - 1) * perPage, p * perPage);
  const th = columns.map((c) => {
    const arrow = c.key === sortKey ? (sortDir === 1 ? ' ▲' : ' ▼') : '';
    return `<th class="${c.num ? 'num' : ''} sortable" data-sort="${esc(c.key)}" tabindex="0" role="button" aria-label="Sort by ${esc(c.label)}">${esc(c.label)}${arrow}</th>`;
  }).join('');
  const td = slice.map((r) => {
    const href = rowHref ? rowHref(r) : null;
    return `<tr${href ? ` class="rowlink" data-href="${href}" tabindex="0"` : ''}>${
      columns.map((c) => `<td class="${c.num ? 'num' : ''}">${c.render(r)}</td>`).join('')}</tr>`;
  }).join('');
  return `<div class="table-wrap"><table class="data" id="${esc(id)}" aria-label="${esc(id)}">
    <thead><tr>${th}</tr></thead><tbody>${td || `<tr><td colspan="${columns.length}">No rows.</td></tr>`}</tbody></table>
    <div class="table-foot"><span>${fmtInt(sorted.length)} row(s) · page ${p} of ${pages}</span>
    <span class="btn-row"><button class="btn" data-page="prev" ${p <= 1 ? 'disabled' : ''}>← Prev</button>
    <button class="btn" data-page="next" ${p >= pages ? 'disabled' : ''}>Next →</button></span></div></div>`;
}

export function bindTable(root, { onSort, onPage, onRow }) {
  root.querySelectorAll('th.sortable').forEach((th) => {
    const fire = () => onSort && onSort(th.dataset.sort);
    th.addEventListener('click', fire);
    th.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fire(); } });
  });
  root.querySelectorAll('button[data-page]').forEach((b) => {
    b.addEventListener('click', () => onPage && onPage(b.dataset.page === 'next' ? 1 : -1));
  });
  if (onRow) {
    root.querySelectorAll('tr.rowlink').forEach((tr) => {
      const go = () => onRow(tr.dataset.href);
      tr.addEventListener('click', go);
      tr.addEventListener('keydown', (e) => { if (e.key === 'Enter') go(); });
    });
  }
}

export function jsonView(obj, summary = 'View JSON') {
  return `<details class="disclosure"><summary>${esc(summary)}</summary><div class="body"><pre class="code">${esc(JSON.stringify(obj, null, 2))}</pre></div></details>`;
}

/** Minimal markdown renderer: headings, rules, bold, code, lists, tables. */
export function md(src) {
  const lines = String(src || '').split('\n');
  let html = '', inList = false, inCode = false, table = [];
  const inline = (t) => esc(t)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  const flushTable = () => {
    if (!table.length) return;
    const rows = table.filter((r) => !/^\|[\s:-]+\|/.test(r))
      .map((r) => r.split('|').slice(1, -1).map((c) => c.trim()));
    if (rows.length) {
      html += '<table><thead><tr>' + rows[0].map((c) => `<th>${inline(c)}</th>`).join('') + '</tr></thead><tbody>'
        + rows.slice(1).map((r) => `<tr>${r.map((c) => `<td>${inline(c)}</td>`).join('')}</tr>`).join('') + '</tbody></table>';
    }
    table = [];
  };
  const closeList = () => { if (inList) { html += '</ul>'; inList = false; } };
  for (const line of lines) {
    if (/^```/.test(line)) {
      closeList(); flushTable();
      html += inCode ? '</code></pre>' : '<pre class="code"><code>';
      inCode = !inCode;
      continue;
    }
    if (inCode) { html += `${esc(line)}\n`; continue; }
    if (/^\|.*\|$/.test(line.trim())) { closeList(); table.push(line.trim()); continue; }
    flushTable();
    const h = line.match(/^(#{1,3})\s+(.*)/);
    if (h) { closeList(); const lvl = h[1].length; html += `<h${lvl}>${inline(h[2])}</h${lvl}>`; continue; }
    if (/^---+$/.test(line.trim())) { closeList(); html += '<hr>'; continue; }
    if (/^>\s?/.test(line)) { closeList(); html += `<blockquote>${inline(line.replace(/^>\s?/, ''))}</blockquote>`; continue; }
    const li = line.match(/^[-*]\s+(.*)/);
    if (li) { if (!inList) { html += '<ul>'; inList = true; } html += `<li>${inline(li[1])}</li>`; continue; }
    closeList();
    if (line.trim()) html += `<p>${inline(line.trim())}</p>`;
  }
  closeList(); flushTable();
  if (inCode) html += '</code></pre>';
  return `<div class="doc">${html}</div>`;
}

export function epLink(runId, trialId, label) {
  return `<a href="#/evidence/${encodeURIComponent(runId)}/${encodeURIComponent(trialId)}" class="mono">${esc(label || trialId)}</a>`;
}

export function baselineTag(b) {
  return b === 'chimera' ? pill('info', baselineLabel(b)) : pill('violet', baselineLabel(b));
}
