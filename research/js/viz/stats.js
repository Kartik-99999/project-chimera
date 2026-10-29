/* Chimera viz math kit — pure functions, no DOM, no fetch.
 * Importable from both the browser app and Node unit tests
 * (research/js/viz/stats.test.mjs). All denominators explicit;
 * invalid inputs yield null, never zero.
 */

/** Two-sided 95% Wilson score interval. Reference (§4.3): 0/5 → upper 43.4%. */
export function wilson(k, n, z = 1.96) {
  if (!Number.isInteger(k) || !Number.isInteger(n) || n <= 0 || k < 0 || k > n) return null;
  const denom = 1 + (z * z) / n;
  const center = (k / n + (z * z) / (2 * n)) / denom;
  const spread = (z * Math.sqrt(((k / n) * (1 - k / n)) / n + (z * z) / (4 * n * n))) / denom;
  return { lo: Math.max(0, center - spread), hi: Math.min(1, center + spread) };
}

export function wilsonUpper(k, n, z = 1.96) {
  const w = wilson(k, n, z);
  return w ? w.hi : null;
}

/** Nearest-rank percentile over a numeric array (unsorted ok). */
export function percentile(values, q) {
  const xs = values.filter((v) => typeof v === 'number' && Number.isFinite(v)).sort((a, b) => a - b);
  if (!xs.length) return null;
  const i = Math.min(xs.length - 1, Math.ceil((q / 100) * xs.length) - 1);
  return xs[Math.max(0, i)];
}

/**
 * Positional episode→cell mapping, mirroring the audit's documented rule
 * (benchmarks/audit.py::_cell_episodes): episodes persist grouped by cell
 * in manifest order and each cell owns its recorded `trials` episodes.
 * Throws on any inconsistency instead of misattributing episodes.
 * Returns [{cell, episodes[]}].
 */
export function sliceCells(cells, episodes) {
  const measured = episodes.filter((e) => !String(e.trial_id || '').startsWith('warmup:'));
  const out = [];
  let cursor = 0;
  for (const cell of cells) {
    const owned = measured.slice(cursor, cursor + cell.trials);
    for (const ep of owned) {
      if (ep.scenario_id !== cell.scenario_id || ep.input_id !== cell.input_id || ep.baseline !== cell.baseline) {
        throw new Error(`episode ${ep.trial_id} does not belong to cell ${cell.scenario_id}/${cell.input_id}; run order inconsistent`);
      }
    }
    out.push({ cell, episodes: owned });
    cursor += cell.trials;
  }
  if (cursor !== measured.length) {
    throw new Error(`cell trial counts sum to ${cursor} but run holds ${measured.length} measured episodes`);
  }
  return out;
}

/**
 * Sankey-style column layout from flows. Each flow: {from, to, value, filter}.
 * Nodes are assigned per column in first-seen order; link widths scale to
 * counts with a fixed unit height per episode. Returns {nodes, links} with
 * absolute y-offsets — pure geometry, no DOM.
 */
export function sankeyLayout(columns, flows, { unit = 3, gap = 14, pad = 8 } = {}) {
  const nodeMap = new Map();
  const get = (col, id, label) => {
    const k = `${col}::${id}`;
    if (!nodeMap.has(k)) nodeMap.set(k, { id, col, label: label || id, in: 0, out: 0, y0: 0, height: 0 });
    return nodeMap.get(k);
  };
  const links = [];
  for (const f of flows) {
    if (!(f.value > 0)) continue;
    const a = get(f.fromCol, f.from, f.fromLabel);
    const b = get(f.toCol, f.to, f.toLabel);
    a.out += f.value;
    b.in += f.value;
    links.push({ ...f, fromNode: a, toNode: b });
  }
  const cols = columns.map(() => []);
  for (const n of nodeMap.values()) cols[n.col].push(n);
  let height = 0;
  for (const col of cols) {
    let y = pad;
    for (const n of col) {
      n.y0 = y;
      n.height = Math.max(2, Math.max(n.in, n.out) * unit);
      y += n.height + gap;
    }
    height = Math.max(height, y - gap + pad);
  }
  const usedOut = new Map();
  const usedIn = new Map();
  for (const l of links) {
    const ka = `${l.fromCol}::${l.from}`;
    const kb = `${l.toCol}::${l.to}`;
    l.height = Math.max(1, l.value * unit);
    l.y0 = l.fromNode.y0 + (usedOut.get(ka) || 0);
    l.y1 = l.toNode.y0 + (usedIn.get(kb) || 0);
    usedOut.set(ka, (usedOut.get(ka) || 0) + l.height);
    usedIn.set(kb, (usedIn.get(kb) || 0) + l.height);
  }
  return { nodes: [...nodeMap.values()], links, height };
}

/** Nice-number axis step (1/2/2.5/5 × 10^k) covering [0, max]. */
export function niceStep(max, ticks = 4) {
  if (!(max > 0)) return 1;
  const mag = 10 ** Math.floor(Math.log10(max / ticks));
  for (const m of [1, 2, 2.5, 5, 10]) if (m * mag * ticks >= max) return m * mag;
  return 10 * mag;
}

/**
 * Structural cell-key match. Keys are `scenario|input|faultJSON`, but
 * JSON text varies in spacing and key order across producers (JS vs
 * Python), so the fault part is parsed and compared canonically.
 * Never throws; malformed keys simply do not match.
 */
export function matchCellKey(cell, key) {
  if (!cell || typeof key !== 'string') return false;
  const i = key.indexOf('|');
  const j = key.indexOf('|', i + 1);
  if (i < 0 || j < 0) return false;
  if (cell.scenario_id !== key.slice(0, i) || cell.input_id !== key.slice(i + 1, j)) return false;
  let fp;
  try {
    fp = JSON.parse(key.slice(j + 1));
  } catch {
    return false;
  }
  const norm = (o) => {
    if (!o || typeof o !== 'object' || Array.isArray(o)) return JSON.stringify(o ?? {});
    return JSON.stringify(Object.keys(o).sort().map((k) => [k, o[k]]));
  };
  return norm(cell.fault_params) === norm(fp);
}
