/* Shared presentational components. Pure render helpers + small widgets. */
import { esc, mVal, fmtInt, baselineLabel } from './data.js';

export function pageHead(title, crumb = [], actions = '') {
  const trail = crumb.map((c, i) => {
    const last = i === crumb.length - 1;
    return last ? `<span aria-current="page">${esc(c[0])}</span>`
      : `<a href="${c[1]}">${esc(c[0])}</a>`;
  }).join(' <span aria-hidden="true">›</span> ');
  return `<div class="crumb">${trail}</div>
    <div class="page-head"><div><h1>${esc(title)}</h1></div><div class="btn-row">${actions}</div></div>`;
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

export function statCard({ value, label, sub = '', href = '' }) {
  const inner = `<div class="stat-value">${value}</div><div class="stat-label">${esc(label)}</div>`
    + (sub ? `<div class="stat-sub">${sub}</div>` : '');
  return href ? `<a class="card tight stat" href="${href}">${inner}</a>`
    : `<div class="card tight stat">${inner}</div>`;
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
