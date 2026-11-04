/* Hand-rolled SVG charts + constellation navigator. No dependencies.
 * Every chart labels denominators; uncertainty whiskers use the same
 * 95% Wilson definition as the evaluation (see data.js).
 */
import { esc, wilsonUpper, fmtPct } from './data.js';
import { wilson } from './viz/stats.js';

const C = { chimera: '#0e7490', replay: '#6d28d9', grid: '#e3e3de', text: '#5b6b80' };

function svgOpen(w, h, label) {
  return `<svg class="chart" viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(label)}">`;
}

/** Grouped vertical bars. values/denoms aligned [series][category]. */
export function groupedBars({ categories, series, height = 260, unit = '', whiskers = null, id = '' }) {
  const W = 680, H = height, padL = 44, padB = 56, padT = 14;
  const plotW = W - padL - 16, plotH = H - padT - padB;
  let rawMax = 0;
  series.forEach((s, si) => s.values.forEach((v, ci) => {
    rawMax = Math.max(rawMax, v || 0, whiskers && whiskers[si] ? (whiskers[si][ci] || 0) : 0);
  }));
  // Nice-number axis: round the top up to a 1/2/2.5/5 step.
  const niceStep = (x) => {
    if (x <= 0) return 1;
    const mag = 10 ** Math.floor(Math.log10(x));
    for (const m of [1, 2, 2.5, 5, 10]) if (m * mag >= x) return m * mag;
    return 10 * mag;
  };
  const step = niceStep(rawMax / 4);
  const maxV = Math.max(step * 4, rawMax * 1.05);
  const y = (v) => padT + plotH - (plotH * v) / maxV;
  const gw = plotW / categories.length;
  const bw = Math.min(44, (gw - 18) / series.length);
  let s = svgOpen(W, H, id || 'grouped bar chart');
  for (let v = 0; v <= maxV + 1e-9; v += step) {
    const label = step >= 1 ? String(Math.round(v)) : String(Math.round(v * 100) / 100);
    s += `<line class="gridline" x1="${padL}" y1="${y(v)}" x2="${W - 16}" y2="${y(v)}"/>`
      + `<text x="${padL - 6}" y="${y(v) + 4}" text-anchor="end" font-size="10">${label}${v === 0 ? '' : unit}</text>`;
  }
  s += `<line class="axis" x1="${padL}" y1="${padT}" x2="${padL}" y2="${padT + plotH}"/>`;
  categories.forEach((cat, ci) => {
    const cx = padL + gw * ci + gw / 2;
    series.forEach((ser, si) => {
      const v = ser.values[ci] || 0;
      const x = cx + (si - (series.length - 1) / 2) * (bw + 4) - bw / 2;
      const denom = ser.denoms ? ser.denoms[ci] : null;
      const title = denom != null ? `${ser.label} · ${cat}: ${v}/${denom}` : `${ser.label} · ${cat}: ${v}${unit}`;
      s += `<rect class="bar" x="${x.toFixed(1)}" y="${y(v).toFixed(1)}" width="${bw}" height="${Math.max(0, (padT + plotH - y(v))).toFixed(1)}" fill="${ser.color}"><title>${esc(title)}</title></rect>`;
      s += `<text x="${(x + bw / 2).toFixed(1)}" y="${(y(v) - 5).toFixed(1)}" text-anchor="middle" font-size="10" fill="#1b2431">${denom != null ? `${v}/${denom}` : `${v}${unit}`}</text>`;
      if (whiskers && whiskers[si] && whiskers[si][ci] != null) {
        const wv = whiskers[si][ci];
        const mx = x + bw / 2;
        s += `<line x1="${mx.toFixed(1)}" y1="${y(v).toFixed(1)}" x2="${mx.toFixed(1)}" y2="${y(wv).toFixed(1)}" stroke="#1b2431" stroke-width="1.4"/>`
          + `<line x1="${(mx - 5).toFixed(1)}" y1="${y(wv).toFixed(1)}" x2="${(mx + 5).toFixed(1)}" y2="${y(wv).toFixed(1)}" stroke="#1b2431" stroke-width="1.4"><title>95% Wilson upper: ${(wv * 100).toFixed(1)}%</title></line>`;
      }
    });
    const words = String(cat).split(' ');
    s += `<text x="${cx.toFixed(1)}" y="${padT + plotH + 16}" text-anchor="middle" font-size="11">${esc(words[0])}</text>`;
    if (words.length > 1) s += `<text x="${cx.toFixed(1)}" y="${padT + plotH + 29}" text-anchor="middle" font-size="10" fill="#8a94a6">${esc(words.slice(1).join(' '))}</text>`;
  });
  s += '</svg>';
  s += `<div class="chart-legend">${series.map((x) => `<span><span class="swatch" style="background:${x.color}"></span>${esc(x.label)}</span>`).join('')}</div>`;
  return s;
}

/** Success-rate heatmap. cells: [{row, col, k, n, href}]. */
export function heatmap({ rows, cols, cells, id = '' }) {
  const cw = 92, rh = 40, padL = 96, padT = 30;
  const W = padL + cols.length * cw + 8, H = padT + rows.length * rh + 8;
  const byKey = new Map(cells.map((c) => [`${c.row}||${c.col}`, c]));
  let s = svgOpen(W, H, id || 'success rate heatmap');
  cols.forEach((c, i) => {
    s += `<text x="${padL + i * cw + cw / 2}" y="18" text-anchor="middle" font-size="11">${esc(c)}</text>`;
  });
  rows.forEach((r, j) => {
    s += `<text x="${padL - 8}" y="${padT + j * rh + rh / 2 + 4}" text-anchor="end" font-size="11">${esc(r)}</text>`;
    cols.forEach((c, i) => {
      const cell = byKey.get(`${r}||${c}`);
      const x = padL + i * cw + 2, y = padT + j * rh + 2, w = cw - 4, h = rh - 4;
      if (!cell || cell.n == null || cell.n <= 0) {
        s += `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="18" fill="#f4f4f1"><title>${esc(r)} · ${esc(c)}: no data</title></rect>`;
        s += `<text x="${x + w / 2}" y="${y + h / 2 + 4}" text-anchor="middle" font-size="11" fill="#8a94a6">—</text>`;
        return;
      }
      const rate = cell.k / cell.n;
      // Tilefield: rounded pastel tiles with dark ink; the single
      // diverging tile carries its expected-outcome tag (✓/✗ + words).
      const fill = rate >= 1 ? '#d9f0e3' : rate <= 0 ? '#f6dfe0' : '#fdf0d3';
      const tcol = rate >= 1 ? '#15803d' : rate <= 0 ? '#b91c1c' : '#b45309';
      const label = `${r} ${c}: ${cell.k}/${cell.n} (${fmtPct(cell.k, cell.n)})`;
      let tag = '';
      if (cell.exp === 'succeeded' || cell.exp === 'failed') {
        const ok = (cell.exp === 'succeeded' && rate >= 1) || (cell.exp === 'failed' && rate <= 0);
        tag = `<text x="${x + w / 2}" y="${y + h - 6}" text-anchor="middle" font-size="9.5" fill="#3f4750">${ok ? '✓ as expected' : `✗ expected ${cell.exp}`}</text>`;
      }
      s += `<a href="${cell.href || '#'}" class="heatmap-cell" aria-label="${esc(label)}"><rect x="${x}" y="${y}" width="${w}" height="${h}" rx="18" fill="${fill}"><title>${esc(label)}</title></rect>`
        + `<text x="${x + w / 2}" y="${y + h / 2 + (tag ? -2 : 4)}" text-anchor="middle" font-size="11" fill="${tcol}" font-weight="700">${cell.k}/${cell.n}</text>${tag}</a>`;
    });
  });
  return `${s}</svg>`;
}

/** Dot-and-whisker interval plot. rows: [{label, sub, k, n, color, href, tip}].
 * Estimates are k/n dots; whiskers are 95% Wilson intervals. Rows with
 * no denominator render as explicit "no data" text, never at zero.
 */
export function dotPlot({ rows, id = '' }) {
  const W = 680, rowH = 26, padL = 250, padR = 64, padT = 26;
  const H = padT + rows.length * rowH + 10;
  const x0 = padL, x1 = W - padR;
  const x = (v) => x0 + (x1 - x0) * v;
  let s = svgOpen(W, H, id || 'dot and whisker interval plot');
  for (const g of [0, 0.25, 0.5, 0.75, 1]) {
    s += `<line class="gridline" x1="${x(g)}" y1="${padT - 8}" x2="${x(g)}" y2="${H - 6}"/>`
      + `<text x="${x(g)}" y="${padT - 12}" text-anchor="middle" font-size="10">${Math.round(g * 100)}%</text>`;
  }
  rows.forEach((r, i) => {
    const y = padT + i * rowH + rowH / 2;
    s += `<text x="${padL - 8}" y="${y - 1}" text-anchor="end" font-size="11" fill="#1b2431">${esc(r.label)}</text>`;
    if (r.sub) s += `<text x="${padL - 8}" y="${y + 11}" text-anchor="end" font-size="10" style="fill:var(--ink-3)">${esc(r.sub)}</text>`;
    if (r.n == null || r.n <= 0) {
      s += `<text x="${x0 + 4}" y="${y + 4}" font-size="11" style="fill:var(--ink-3)">no denominator — unmeasurable</text>`;
      return;
    }
    const est = r.k / r.n;
    const iv = wilson(r.k, r.n) || { lo: 0, hi: 1 };
    const inner = `<line x1="${x(iv.lo).toFixed(1)}" y1="${y}" x2="${x(iv.hi).toFixed(1)}" y2="${y}" stroke="${r.color}" stroke-width="2"/>`
      + `<line x1="${x(iv.lo).toFixed(1)}" y1="${y - 5}" x2="${x(iv.lo).toFixed(1)}" y2="${y + 5}" stroke="${r.color}" stroke-width="2"/>`
      + `<line x1="${x(iv.hi).toFixed(1)}" y1="${y - 5}" x2="${x(iv.hi).toFixed(1)}" y2="${y + 5}" stroke="${r.color}" stroke-width="2"/>`
      + `<circle cx="${x(est).toFixed(1)}" cy="${y}" r="5" fill="${r.color}"><title>${esc(r.tip || `${r.label}: ${r.k}/${r.n}`)}</title></circle>`
      + `<text x="${x1 + 8}" y="${y + 4}" font-size="10" fill="#5b6b80">n=${r.n}</text>`;
    const band = `<rect class="signal-band" x="${x0}" y="${(y - rowH / 2 + 2).toFixed(1)}" width="${(x1 - x0).toFixed(1)}" height="${rowH - 4}" rx="4"/>`;
    s += r.href ? `<a class="signal-row" href="${r.href}" data-tip="${esc(r.tip || '')}" aria-label="${esc(r.tip || r.label)}">${band}${inner}</a>` : inner;
  });
  return `${s}</svg>`;
}

/** Fault transect: discrete soundings at tested slow_ms levels.
 * rows: [{scenario, baseline}]; levels: sorted slow_ms values;
 * soundings: [{scenario, baseline, slow, disabled, k, n, unverified,
 * href, tip}]. Markers encode observed k/n only; no lines connect
 * soundings, so no failure boundary is implied between levels.
 */
export function faultTransect({ rows, levels, soundings, id = '' }) {
  const W = 760, padL = 168, padR = 64, padT = 30, rowH = 46, padB = 66;
  const H = padT + rows.length * rowH + padB;
  const maxLevel = Math.max(...levels, 0);
  const x = (slow) => padL + (maxLevel > 0 ? (slow / maxLevel) * (W - padL - padR) : 0);
  const byRow = new Map();
  for (const s of soundings) {
    const k = `${s.scenario}||${s.baseline}`;
    if (!byRow.has(k)) byRow.set(k, []);
    byRow.get(k).push(s);
  }
  const perLevel = new Map();
  for (const m of soundings) perLevel.set(m.slow, (perLevel.get(m.slow) || 0) + (m.n || 0));
  let s = svgOpen(W, H, id || 'fault transect soundings');
  for (const lv of levels) {
    s += `<line class="gridline" x1="${x(lv).toFixed(1)}" y1="${padT - 10}" x2="${x(lv).toFixed(1)}" y2="${H - padB + 8}"/>`
      + `<text x="${x(lv).toFixed(1)}" y="${padT - 14}" text-anchor="middle" font-size="10">${lv === maxLevel ? `${lv} ms` : lv}</text>`
      + `<text x="${x(lv).toFixed(1)}" y="${H - padB + 24}" text-anchor="middle" font-size="9.5" fill="#5f6b82">n=${perLevel.get(lv) || 0}</text>`;
  }
  const baseColor = (b) => (b === 'chimera' ? C.chimera : C.replay);
  rows.forEach((r, i) => {
    const y = padT + i * rowH + rowH / 2;
    s += `<line x1="${padL}" y1="${padT + (i + 1) * rowH}" x2="${W - padR}" y2="${padT + (i + 1) * rowH}" stroke="#e3e3de" stroke-width="1"/>`
      + `<circle cx="${padL - 12}" cy="${y - 7}" r="4" fill="${baseColor(r.baseline)}"/>`
      + `<text x="${padL - 20}" y="${y - 3}" text-anchor="end" font-size="11" fill="#1b2431">${esc(r.scenario)}</text>`
      + `<text x="${padL - 20}" y="${y + 10}" text-anchor="end" font-size="10" style="fill:var(--ink-3)">${esc(r.baseline)}</text>`;
    const list = byRow.get(`${r.scenario}||${r.baseline}`) || [];
    if (!list.length) {
      s += `<text x="${padL + 4}" y="${y + 4}" font-size="11" style="fill:var(--ink-3)">— untested</text>`;
      return;
    }
    for (const m of list) {
      const cx = x(m.slow);
      const all = m.k === m.n && m.n > 0, none = m.k === 0;
      const col = all ? '#15803d' : none ? '#b91c1c' : '#b45309';
      let mark;
      if (m.disabled) {
        const sq = 15, x0 = (cx - sq / 2).toFixed(1), y0 = (y - sq / 2).toFixed(1);
        mark = all
          ? `<rect x="${x0}" y="${y0}" width="${sq}" height="${sq}" rx="2" fill="#ffffff" stroke="${col}" stroke-width="3"/>`
          : none
            ? `<rect x="${x0}" y="${y0}" width="${sq}" height="${sq}" rx="2" fill="${col}"/>`
            : `<rect x="${x0}" y="${y0}" width="${sq}" height="${sq}" rx="2" fill="#ffffff" stroke="${col}" stroke-width="2"/>`
              + `<rect x="${x0}" y="${y0}" width="${(sq / 2).toFixed(1)}" height="${sq}" fill="${col}"/>`;
      } else {
        mark = all
          ? `<circle cx="${cx.toFixed(1)}" cy="${y}" r="8" fill="#ffffff" stroke="${col}" stroke-width="3"/>`
          : none
            ? `<circle cx="${cx.toFixed(1)}" cy="${y}" r="8" fill="${col}"/>`
            : `<circle cx="${cx.toFixed(1)}" cy="${y}" r="8" fill="#ffffff" stroke="${col}" stroke-width="2"/>`
              + `<path d="M ${cx.toFixed(1)} ${y - 8} A 8 8 0 0 0 ${cx.toFixed(1)} ${y + 8} Z" fill="${col}"/>`;
      }
      const ring = m.unverified
        ? `<circle cx="${cx.toFixed(1)}" cy="${y}" r="13" fill="none" stroke="#b45309" stroke-width="1.5" stroke-dasharray="3 2"/>` : '';
      const tip = m.tip || `${m.scenario} · ${m.baseline} · slow=${m.slow}${m.disabled ? ' +disabled' : ''}: ${m.k}/${m.n}`;
      const inner = `${mark}${ring}<title>${esc(tip)}</title>`
        + `<text x="${(cx + 17).toFixed(1)}" y="${y + 4}" font-size="10" fill="#5b6b80">${m.k}/${m.n}</text>`;
      s += `<a href="${m.href || '#'}" class="sounding" data-tip="${esc(tip)} — open records" aria-label="${esc(tip)}">${inner}</a>`;
    }
  });
  const ly = H - 22;
  s += `<g font-size="10" fill="#5b6b80">`
    + `<circle cx="${padL}" cy="${ly}" r="6" fill="#ffffff" stroke="#15803d" stroke-width="2.5"/><text x="${padL + 10}" y="${ly + 4}">all succeeded</text>`
    + `<circle cx="${padL + 118}" cy="${ly}" r="6" fill="#b91c1c"/><text x="${padL + 128}" y="${ly + 4}">none</text>`
    + `<circle cx="${padL + 190}" cy="${ly}" r="6" fill="#ffffff" stroke="#b45309" stroke-width="2"/><path d="M ${padL + 190} ${ly - 6} A 6 6 0 0 0 ${padL + 190} ${ly + 6} Z" fill="#b45309"/><text x="${padL + 200}" y="${ly + 4}">split</text>`
    + `<rect x="${padL + 252}" y="${ly - 6}" width="12" height="12" rx="2" fill="#ffffff" stroke="#5b6b80" stroke-width="2"/><text x="${padL + 268}" y="${ly + 4}">disabled</text>`
    + `<circle cx="${padL + 348}" cy="${ly}" r="8" fill="none" stroke="#b45309" stroke-width="1.5" stroke-dasharray="3 2"/><text x="${padL + 360}" y="${ly + 4}">unverified present</text></g>`;
  return `${s}</svg>`;
}

/** Oscilloscope strip: logic-analyzer lanes with per-lane coordinates.
 * lanes: [{id, title, coord, marks: [{x, xLabel, kind, title}]}].
 * pxPerStep zooms horizontally; the caller wraps in a scroll region.
 * Every mark carries its exact title; color never stands alone.
 * Returns {svg, width}: the svg carries a fixed pixel width so zoom
 * scrolls instead of rescaling.
 */
export function scopeStrip({ lanes, pxPerStep = 48, id = '' }) {
  const KINDS = {
    ok: { fill: '#15803d', label: 'ok / satisfied' }, fail: { fill: '#b91c1c', label: 'failure' },
    verify: { fill: '#6d28d9', label: 'verification event' }, run: { fill: '#1d4ed8', label: 'run boundary' },
    info: { fill: '#5b6b80', label: 'informational' }, policy: { fill: '#b45309', label: 'policy flag' },
    disagree: { fill: '#b91c1c', label: 'human disagrees' }, unau: { fill: 'none', label: 'unauditable', dash: true },
    missing: { fill: 'none', label: 'missing', dash: true },
  };
  // padL fits the longest lane coordinate ('step index (no recorded
  // sequence numbers)') so left labels never clip at the svg edge.
  const padL = 220, padR = 18, padT = 10, laneH = 58, padB = 30;
  const span = Math.max(1, ...lanes.flatMap((l) => l.marks.map((m) => m.x)));
  const plotW = padL + span * pxPerStep + padR;
  // The legend row sits below the lanes; on narrow spans it is wider than
  // the plot, so grow W to fit it instead of clipping the last label.
  const legendKinds = [...new Set(lanes.flatMap((l) => l.marks.map((m) => m.kind)))];
  const W = Math.max(plotW, padL + legendKinds.length * 150 + padR);
  const H = padT + lanes.length * laneH + padB;
  const x = (v) => padL + (v - 0.5) * pxPerStep;
  let s = `<svg class="chart" style="width:${W}px;max-width:none" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(id || 'episode oscilloscope')}">`;
  const present = new Set();
  lanes.forEach((lane, li) => {
    const y0 = padT + li * laneH, y = y0 + laneH / 2;
    if (li % 2 === 1) s += `<rect x="${padL}" y="${y0}" width="${W - padL - padR}" height="${laneH}" fill="rgba(148,170,210,0.035)"/>`;
    const nMarks = lane.marks.length;
    s += `<text x="${padL - 10}" y="${y - 4}" text-anchor="end" font-size="11" fill="#1b2431">${esc(lane.title)} <tspan fill="#5f6b82">(${nMarks})</tspan></text>`
      + `<text x="${padL - 10}" y="${y + 10}" text-anchor="end" font-size="9.5" style="fill:var(--ink-3)">${esc(lane.coord)}</text>`
      + `<line x1="${padL}" y1="${y + 20}" x2="${W - padR}" y2="${y + 20}" stroke="#e3e3de" stroke-width="1"/>`;
    const laneMax = Math.max(1, ...lane.marks.map((m) => m.x));
    for (let t = 1; t <= laneMax; t += 1) {
      const mark = lane.marks.find((m) => m.x === t);
      const lab = lane.id === 'verdicts' && mark ? mark.xLabel : String(t);
      s += `<line x1="${x(t).toFixed(1)}" y1="${y + 12}" x2="${x(t).toFixed(1)}" y2="${y + 16}" stroke="#d9d9d4" stroke-width="1"/>`
        + `<text x="${x(t).toFixed(1)}" y="${y + 16}" text-anchor="middle" font-size="9" fill="#8a94a6">${esc(lab.length > 14 ? lab.slice(0, 13) + '…' : lab)}</text>`;
    }
    if (!lane.marks.length) {
      s += `<text x="${padL + 6}" y="${y + 4}" font-size="11" style="fill:var(--ink-3)">no marks recorded</text>`;
      return;
    }
    lane.marks.forEach((m, mi) => {
      const k = KINDS[m.kind] || KINDS.info;
      present.add(m.kind);
      const fill = k.fill === 'none' ? '#ffffff' : k.fill;
      const stroke = k.fill === 'none' ? '#8a94a6' : k.fill;
      s += `<g class="scope-event" data-lane="${esc(lane.id)}" data-idx="${mi}" tabindex="0" role="button" aria-label="${esc(m.title)}" data-tip="${esc(m.title)}">`
        + `<circle cx="${x(m.x).toFixed(1)}" cy="${y - 4}" r="7" fill="${fill}" stroke="${stroke}" stroke-width="2"${k.dash ? ' stroke-dasharray="3 2"' : ''}/>`
        + `<title>${esc(m.title)}</title></g>`;
    });
  });
  const items = [...present].map((k) => KINDS[k] || KINDS.info);
  s += `<g font-size="10" fill="#5b6b80">` + items.map((k, i) => {
    const lx = padL + i * 150;
    return `<circle cx="${lx}" cy="${H - 12}" r="5" fill="${k.fill === 'none' ? '#ffffff' : k.fill}" stroke="${k.fill === 'none' ? '#8a94a6' : k.fill}" stroke-width="2"${k.dash ? ' stroke-dasharray="3 2"' : ''}/>`
      + `<text x="${lx + 9}" y="${H - 8}">${esc(k.label)}</text>`;
  }).join('') + `</g>`;
  return { svg: `${s}</svg>`, width: W };
}

/** Inline proportional bar + exact label (for latency tables). */
export function barCell(value, max, label) {
  if (value == null || max == null || max <= 0) return '<span>—</span>';
  const pct = Math.max(2, Math.min(100, (100 * value) / max));
  return `<span style="display:inline-flex;align-items:center;gap:8px"><span style="display:inline-block;width:90px;height:8px;background:#e6dcc4;border-radius:4px;overflow:hidden"><span style="display:block;height:100%;width:${pct.toFixed(0)}%;background:var(--cyan)"></span></span><span class="num">${esc(label)}</span></span>`;
}

/* Constellation: deterministic orbital map over real entities.
 * Nodes: 1 hub + 4 runs + 4 scenarios + audit states. Edges encode
 * membership. Clicking selects (details panel) and offers navigation.
 */
export function constellation({ compact = false } = {}) {
  return { render, bind, filter };
  function render(model) {
    const W = compact ? 640 : 760, H = compact ? 372 : 430;
    const cx = W / 2, cy = H / 2;
    const R = compact ? 118 : 138;
    const nodes = [];
    const hub = { id: 'hub', label: 'Chimera evidence', kind: 'hub', x: cx, y: cy, r: 22, href: '#/command', blurb: 'All indexed runs, reports, and audit plans.' };
    nodes.push(hub);
    const runs = model.runs.filter((r) => r.data);
    runs.forEach((r, i) => {
      const a = (-90 + (360 / Math.max(1, runs.length)) * i) * (Math.PI / 180);
      nodes.push({
        id: `run:${r.runId}`, label: r.runId.replace('20261028-', ''), kind: 'run',
        x: cx + R * Math.cos(a), y: cy + R * Math.sin(a),
        r: 13 + Math.min(9, Math.sqrt((r.data.episodes || []).length) / 1.6),
        href: `#/atlas?run=${encodeURIComponent(r.runId)}`,
        blurb: `${(r.data.cells || []).length} cells · ${(r.data.episodes || []).length} episodes · ${r.baseline} · ${r.split}`,
        runId: r.runId,
      });
    });
    const scenarios = ['S-NORM', 'S-SLOW', 'S-DIS', 'S-SLOWDIS'];
    const scRx = R * (compact ? 1.72 : 1.9), scRy = R * (compact ? 1.04 : 1.0);
    scenarios.forEach((sc, i) => {
      const a = (-90 + (360 / scenarios.length) * (i + 0.5)) * (Math.PI / 180);
      const eps = model.episodes.filter((e) => e.scenario_id === sc && !String(e.trial_id).startsWith('warmup:')).length;
      nodes.push({
        id: `sc:${sc}`, label: sc, kind: 'scenario',
        x: cx + scRx * Math.cos(a),
        y: cy + scRy * Math.sin(a),
        r: 11, href: `#/observatory?scenario=${sc}`,
        blurb: `${eps} measured episodes across all runs.`,
      });
    });
    const audits = model.auditNodes || [];
    const ax = compact ? 64 : 70, ay0 = compact ? 104 : 120, ayStep = compact ? 60 : 62;
    audits.forEach((an, i) => {
      nodes.push({
        id: `audit:${an.runId}`, label: an.label, kind: an.state === 'audited' ? 'audit-ok' : 'audit-pending',
        x: ax, y: ay0 + i * ayStep,
        r: 10, href: '#/audit',
        blurb: an.blurb,
      });
    });
    const byId = new Map(nodes.map((n) => [n.id, n]));
    const links = [];
    for (const n of nodes) {
      if (n.kind === 'run') links.push(['hub', n.id]);
      if (n.kind === 'scenario') {
        for (const r of runs) {
          if ((r.data.cells || []).some((c) => c.scenario_id === n.label)) links.push([`run:${r.runId}`, n.id]);
        }
      }
      if (n.kind.startsWith('audit')) {
        const [runId] = n.id.split(':').slice(1);
        if (byId.has(`run:${runId}`)) links.push([`run:${runId}`, n.id]);
      }
    }
    const kindColor = { hub: '#0e7490', run: '#1d4ed8', scenario: '#6d28d9', 'audit-ok': '#15803d', 'audit-pending': '#b45309' };
    const kindTag = { hub: 'index', run: 'run', scenario: 'scenario', 'audit-ok': 'audit · reviewed', 'audit-pending': 'audit · pending' };
    let s = `<svg viewBox="0 0 ${W} ${H}" role="group" aria-label="Evidence constellation graph">`;
    // Orbital structure: run circle, scenario ellipse, cluster captions.
    s += `<circle class="const-orbit" cx="${cx}" cy="${cy}" r="${R}"/>`;
    s += `<ellipse class="const-orbit dashed" cx="${cx}" cy="${cy}" rx="${scRx.toFixed(0)}" ry="${scRy.toFixed(0)}"/>`;
    s += `<text class="const-cluster" x="${cx}" y="22" text-anchor="middle">runs</text>`;
    s += `<text class="const-cluster" x="${(W - 58).toFixed(0)}" y="22" text-anchor="middle">scenarios</text>`;
    if (audits.length) s += `<text class="const-cluster" x="${ax}" y="${ay0 - 30}" text-anchor="middle">audits</text>`;
    // Gentle curved links: control point pushed perpendicular for readability.
    s += links.map(([a, b]) => {
      const na = byId.get(a), nb = byId.get(b);
      const mx = (na.x + nb.x) / 2, my = (na.y + nb.y) / 2;
      const dx = nb.x - na.x, dy = nb.y - na.y;
      const len = Math.hypot(dx, dy) || 1;
      const bow = Math.min(26, len * 0.09);
      const qx = mx - (dy / len) * bow, qy = my + (dx / len) * bow;
      return `<path class="const-link" data-link="${a} ${b}" d="M${na.x.toFixed(0)},${na.y.toFixed(0)} Q${qx.toFixed(0)},${qy.toFixed(0)} ${nb.x.toFixed(0)},${nb.y.toFixed(0)}"/>`;
    }).join('');
    // Radial-outward labels: side labels for east/west nodes, above/below
    // otherwise, so captions leave the node away from the hub. Scenarios
    // always sit above/below to clear the audit column.
    const labelPos = (n) => {
      const dx = n.x - cx, dy = n.y - cy;
      if (n.kind === 'audit-ok' || n.kind === 'audit-pending') {
        return { x: n.x + n.r + 7, y: n.y + 4, anchor: 'start', strong: false };
      }
      if (n.kind === 'scenario' || Math.abs(dx) <= Math.abs(dy) * 1.4) {
        const above = dy <= 0;
        return { x: n.x, y: above ? n.y - n.r - 8 : n.y + n.r + 15, anchor: 'middle', strong: n.kind === 'scenario' };
      }
      const east = dx > 0;
      return { x: east ? n.x + n.r + 8 : n.x - n.r - 8, y: n.y + 4, anchor: east ? 'start' : 'end', strong: n.kind === 'run' };
    };
    for (const n of nodes) {
      const col = kindColor[n.kind] || '#5b6b80';
      const lp = labelPos(n);
      s += `<g class="const-node" data-node="${esc(n.id)}" data-kind="${esc(kindTag[n.kind] || n.kind)}" data-href="${esc(n.href)}" data-blurb="${esc(n.blurb)}" tabindex="0" role="button" aria-label="${esc(n.label)}. ${esc(n.blurb)}">`
        + `<circle class="halo" cx="${n.x.toFixed(0)}" cy="${n.y.toFixed(0)}" r="${n.r + 9}"/>`
        + (n.kind === 'hub' ? `<circle cx="${n.x.toFixed(0)}" cy="${n.y.toFixed(0)}" r="${n.r + 6}" fill="none" stroke="${col}" stroke-width="1" opacity="0.45"/>` : '')
        + `<circle class="ring core" cx="${n.x.toFixed(0)}" cy="${n.y.toFixed(0)}" r="${n.r}" stroke="${col}" stroke-width="2"/>`
        + `<text class="const-label${lp.strong ? ' strong' : ''}" x="${lp.x.toFixed(0)}" y="${lp.y.toFixed(0)}" text-anchor="${lp.anchor}">${esc(n.label)}</text>`
        + `<title>${esc(n.label)} — ${esc(n.blurb)}</title></g>`;
    }
    s += '</svg>';
    const list = `<ul class="node-list" aria-label="Constellation nodes as a list">${nodes.filter((n) => n.id !== 'hub').map((n) => (
      `<li><a href="${n.href}">${esc(n.label)}</a> <span style="color:var(--ink-3)">— ${esc(kindTag[n.kind] || n.kind)} · ${esc(n.blurb)}</span></li>`)).join('')}</ul>`;
    return `<div class="constellation-wrap" data-constellation>${s}`
      + `<div class="const-panel" data-panel aria-live="polite"><span style="color:var(--ink-3)">Select a node to inspect it, then open its workspace.</span></div>${list}</div>`;
  }

  function bind(root) {
    const wrap = root.querySelector('[data-constellation]');
    if (!wrap) return;
    const panel = wrap.querySelector('[data-panel]');
    const neighbors = new Map();
    wrap.querySelectorAll('.const-link').forEach((l) => {
      const [a, b] = (l.dataset.link || '').split(' ');
      if (!a || !b) return;
      if (!neighbors.has(a)) neighbors.set(a, new Set([a]));
      if (!neighbors.has(b)) neighbors.set(b, new Set([b]));
      neighbors.get(a).add(b);
      neighbors.get(b).add(a);
    });
    const select = (g) => {
      wrap.querySelectorAll('.const-node').forEach((n) => n.classList.remove('selected'));
      g.classList.add('selected');
      const id = g.dataset.node;
      const label = (g.querySelector('title').textContent || '').split(' — ')[0];
      const near = neighbors.get(id) || new Set([id]);
      wrap.querySelectorAll('.const-link').forEach((l) => {
        const touch = (l.dataset.link || '').split(' ').includes(id);
        l.classList.toggle('active', touch);
        l.classList.toggle('dim', !touch);
      });
      wrap.querySelectorAll('.const-node').forEach((n) => {
        n.classList.toggle('dim', !near.has(n.dataset.node));
      });
      panel.innerHTML = `<span class="const-kind">${esc(g.dataset.kind || '')}</span><strong>${esc(label)}</strong> <span style="color:var(--ink-3)">${esc(g.dataset.blurb || '')}</span> <a class="btn" style="margin-left:auto" href="${esc(g.dataset.href || '#/command')}">Open →</a>`;
    };
    wrap.querySelectorAll('.const-node').forEach((g) => {
      g.addEventListener('click', () => select(g));
      g.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); select(g); } });
      g.addEventListener('dblclick', () => { window.location.hash = g.dataset.href || '#/command'; });
    });
  }

  // Dim nodes that fail the text/kind filter; links dim when either end dims.
  function filter(root, { q = '', kind = '' } = {}) {
    const wrap = root.querySelector('[data-constellation]');
    if (!wrap) return { shown: 0, total: 0 };
    const needle = q.trim().toLowerCase();
    let shown = 0, total = 0;
    const visible = new Map();
    wrap.querySelectorAll('.const-node').forEach((g) => {
      total += 1;
      const id = g.dataset.node || '';
      const text = `${(g.querySelector('title').textContent || '')} ${id}`.toLowerCase();
      const kindOk = !kind || (kind === 'audit'
        ? id.startsWith('audit:')
        : (kind === 'run' ? id.startsWith('run:') : (kind === 'scenario' ? id.startsWith('sc:') : true)));
      const ok = (!needle || text.includes(needle)) && kindOk;
      visible.set(id, ok);
      g.classList.toggle('dim', !ok);
      if (ok) shown += 1;
    });
    wrap.querySelectorAll('.const-link').forEach((l) => {
      const [a, b] = (l.dataset.link || '').split(' ');
      const ok = visible.get(a) !== false && visible.get(b) !== false;
      l.classList.toggle('dim', !ok);
      if (!ok) l.classList.remove('active');
    });
    const count = root.querySelector('[data-map-count]');
    if (count) count.textContent = needle || kind ? `${shown} of ${total} nodes match` : `${total} nodes`;
    return { shown, total };
  }
}
