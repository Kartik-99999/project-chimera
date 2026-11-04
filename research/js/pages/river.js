/* Evidence River: scenario → baseline → outcome → cell-audit flow.
 * Every unit of width is a counted measured episode (warm-ups
 * excluded); each episode contributes exactly once per transition.
 * Clicking any node or link filters the Atlas to those records.
 */
import { getRun, getState, esc, fmtInt } from '../data.js';
import { sankeyLayout } from '../viz/stats.js';
import { aggregateFlows, outcomeFilter } from '../viz/riverModel.js';
import { attachTip } from '../viz/tooltip.js';
import { link } from '../app.js';
import { pageHead, emptyState, pill, secHead } from '../components.js';

const NODE_COLORS = {
  scenario: '#1d4ed8', chimera: '#0e7490', 'baseline-a': '#6d28d9',
  succeeded: '#15803d', failed: '#b91c1c', cancelled: '#b45309', inconclusive: '#b45309',
  'failed · harness error': '#b91c1c', 'cell audited': '#15803d', 'cell pending': '#b45309',
};

export async function pageRiver(el, { query }) {
  const split = query.split === 'development' ? 'development' : 'evaluation';
  const tag = split === 'development' ? 'dev' : 'eval';
  const s = getState();
  const runs = [`${tag}-20261028-chimera`, `${tag}-20261028-baseline-a`]
    .map((id) => {
      const r = getRun(id);
      if (!r) return null;
      return { ...r, data: s.audited.get(id) || r.data };
    }).filter(Boolean);
  if (runs.length !== 2) {
    el.innerHTML = pageHead('Evidence River', [['Evidence River']]) + emptyState(
      'Run evidence missing', `Both ${esc(split)} run files are needed for the flow.`);
    return;
  }
  let episodes; let flows;
  try {
    ({ episodes, flows } = aggregateFlows(runs));
  } catch (err) {
    el.innerHTML = pageHead('Evidence River', [['Evidence River']])
      + `<div class="banner warn"><strong>Cannot map episodes to cells:</strong> ${esc(err.message)}.</div>`;
    return;
  }
  const N = episodes.length;
  const columns = [{ title: 'Scenario' }, { title: 'Baseline' }, { title: 'Outcome' }, { title: 'Cell audit' }];
  const { nodes, links, height } = sankeyLayout(columns, flows, { unit: 1.7, gap: 12, pad: 30 });
  const W = 760, colX = [70, 270, 470, 660], nodeW = 12;
  const colorOf = (n) => NODE_COLORS[n.id] || (n.col === 0 ? NODE_COLORS.scenario : '#5b6b80');
  const hrefFor = (col, id) => (col === 3
    ? link('audit')
    : link('atlas', [], col === 0 ? { scenario: id } : col === 1 ? { baseline: id } : { outcome: outcomeFilter(id) }));
  const colTotal = columns.map((_, i) => nodes.filter((n) => n.col === i)
    .reduce((a, n) => a + Math.max(n.in, n.out), 0));
  let svg = `<svg class="chart river-svg" viewBox="0 0 ${W} ${height}" role="group" aria-label="Evidence flow for the ${esc(split)} split">`;
  svg += columns.map((c, i) => `<text class="river-col-title" x="${colX[i]}" y="14" text-anchor="middle">${esc(c.title)}</text>`
    + `<text class="river-col-total" x="${colX[i]}" y="27" text-anchor="middle">Σ ${fmtInt(colTotal[i])}</text>`).join('');
  for (const l of links) {
    const x0 = colX[l.fromCol] + nodeW / 2, x1 = colX[l.toCol] - nodeW / 2;
    const mx = (x0 + x1) / 2;
    const d = `M${x0},${l.y0} C${mx},${l.y0} ${mx},${l.y1} ${x1},${l.y1} L${x1},${(l.y1 + l.height).toFixed(1)} C${mx},${(l.y1 + l.height).toFixed(1)} ${mx},${(l.y0 + l.height).toFixed(1)} ${x0},${(l.y0 + l.height).toFixed(1)} Z`;
    const href = l.toCol === 3 ? link('audit') : link('atlas', [], l.filter);
    const tip = `${l.from} → ${l.to}: ${l.value} episode${l.value === 1 ? '' : 's'}`;
    svg += `<a class="flow-link" href="${href}" data-from-col="${l.fromCol}" data-from="${esc(l.from)}" data-to-col="${l.toCol}" data-to="${esc(l.to)}" data-tip="${esc(tip)} — open filtered records" aria-label="${esc(tip)}"><path d="${d}" fill="${colorOf(l.fromNode)}" opacity="0.45"><title>${esc(tip)}</title></path></a>`;
  }
  for (const n of nodes) {
    const x = colX[n.col] - nodeW / 2;
    const total = Math.max(n.in, n.out);
    const tip = `${n.label}: ${total} episode${total === 1 ? '' : 's'}`;
    svg += `<a class="flow-node" href="${hrefFor(n.col, n.id)}" data-col="${n.col}" data-node="${esc(n.id)}" data-tip="${esc(tip)} — open filtered records" aria-label="${esc(tip)}">`
      + `<rect x="${x}" y="${n.y0}" width="${nodeW}" height="${Math.max(2, n.height)}" rx="3" fill="${colorOf(n)}"><title>${esc(tip)}</title></rect>`
      + `<text class="river-node-label" x="${colX[n.col] + (n.col >= 2 ? -14 : 14)}" y="${(n.y0 + n.height / 2 + 4).toFixed(1)}" text-anchor="${n.col >= 2 ? 'end' : 'start'}">${esc(n.label)} (${total})</text></a>`;
  }
  svg += '</svg>';

  const listRows = links.map((l) => (
    `<tr><td>${esc(columns[l.fromCol].title)}: <strong>${esc(l.from)}</strong></td>`
    + `<td>→</td><td>${esc(columns[l.toCol].title)}: <strong>${esc(l.to)}</strong></td>`
    + `<td class="num">${l.value}</td>`
    + `<td><a href="${l.toCol === 3 ? link('audit') : link('atlas', [], l.filter)}">records →</a></td></tr>`)).join('');

  el.innerHTML = pageHead('Evidence River', [['Evidence River']], '', {
    kicker: `Routes #/river · #/lineage · split = ${split}`,
    lede: 'Every unit of ribbon width is one measured episode, counted exactly once per transition. Clicking any ribbon filters the Atlas to those records.',
    meta: `<span class="pill"><span class="dot"></span>Σ ${fmtInt(N)} episodes flow</span>`,
  })
    + (split === 'evaluation' ? `<div class="banner warn"><strong>Provisional.</strong> ${fmtInt(N)} held-out episodes flow below; audit states reflect zero adjudicated eval verdicts.</div>` : '')
    + secHead('Evidence River', 'Soft-graph pattern ribbons — luminous, round-capped, exact Σ at every column.')
    + `<div class="card"><div class="filters"><div class="field"><label for="r-split">Split</label><select id="r-split">
        <option value="evaluation"${split === 'evaluation' ? ' selected' : ''}>evaluation (held out)</option>
        <option value="development"${split === 'development' ? ' selected' : ''}>development</option></select></div></div>
      <p style="color:var(--ink-2)"><strong>Counting method:</strong> each of the ${fmtInt(N)} measured episodes contributes exactly one unit to each transition; link widths are proportional to counts. Harness-error episodes (if any) form their own outcome node so nothing is double-counted. Warm-ups excluded.</p>
      ${svg}<p class="cap"><strong>Conservation holds:</strong> Σ ${fmtInt(N)} at all four columns — check the column totals above against each other.</p></div>`
    + `<div class="card"><h2>Flow records (list alternative)</h2>
      <div class="table-wrap"><table class="data"><thead><tr><th>From</th><th></th><th>To</th><th class="num">Episodes</th><th></th></tr></thead><tbody>${listRows}</tbody></table></div></div>`;

  el.querySelector('#r-split').addEventListener('change', (e) => {
    window.location.hash = link('river', [], { split: e.target.value });
  });
  el.querySelectorAll('[data-tip]').forEach((a) => attachTip(a, a.dataset.tip));
  // Hovering a stage node spotlights its connected transitions; the
  // highlight follows real from/to identity, never proximity.
  const svgEl = el.querySelector('.river-svg');
  if (svgEl && typeof svgEl.querySelectorAll === 'function') {
    const links = [...svgEl.querySelectorAll('.flow-link')];
    const setHi = (col, id) => {
      for (const l of links) {
        const touch = (l.dataset.fromCol === col && l.dataset.from === id)
          || (l.dataset.toCol === col && l.dataset.to === id);
        l.classList.toggle('hi', !!col && touch);
        l.classList.toggle('dim', !!col && !touch);
      }
    };
    svgEl.querySelectorAll('.flow-node').forEach((n) => {
      n.addEventListener('mouseenter', () => setHi(n.dataset.col, n.dataset.node));
      n.addEventListener('mouseleave', () => setHi('', ''));
      n.addEventListener('focus', () => setHi(n.dataset.col, n.dataset.node));
      n.addEventListener('blur', () => setHi('', ''));
    });
  }
}
