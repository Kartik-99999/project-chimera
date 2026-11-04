/* Sigil engine: pure layout + field math for the Chimera particle
 * experience (DOM-free; unit-tested). All geometry lives in world
 * units: origin at center, sigil ring radius 1. Screen mapping is
 * the renderer's job, so resize never invalidates particle state.
 *
 * The Convergence Sigil (original): an instrument ring with gauge
 * ticks, an evidence hexagon with bright vertex nodes, three spiral
 * streams merging into a small intense core — many pieces of
 * evidence converging into one.
 *
 * The scroll morph is a staged transit, not a crossfade: each layer
 * owns a progress window (dust and ring release first, the core
 * travels last) and follows a quadratic bezier from its sigil seat
 * to its constellation target, so the ring peels into streams, the
 * three arms diverge on their own trajectories, and the hexagon
 * exhales before releasing.
 */
const TWO_PI = Math.PI * 2;

export function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a |= 0; a += 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t ^= t + Math.imul(t ^ (t >>> 7), 61 | t);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export const clamp01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
export const smootherstep = (t) => {
  const x = clamp01(t);
  return x * x * x * (x * (x * 6 - 15) + 10);
};
export const easeOutCubic = (t) => 1 - (1 - clamp01(t)) ** 3;

/* Distribute `count` particles over weighted layers deterministically. */
function apportion(count, weights) {
  const total = weights.reduce((n, [, w]) => n + w, 0);
  const out = [];
  let used = 0;
  weights.forEach(([name, w], i) => {
    const n = i === weights.length - 1 ? count - used : Math.floor((count * w) / total);
    used += n;
    out.push([name, n]);
  });
  return out;
}

/* Morph windows per layer: [start, end] of scroll progress over which
 * the layer travels. Jittered per particle; the core arrives last. */
const MORPH_WINDOWS = {
  dust: [0.00, 0.45], ring: [0.02, 0.55], tick: [0.02, 0.55],
  stream: [0.15, 0.70], hex: [0.30, 0.85], vertex: [0.30, 0.85],
  core: [0.45, 1.00],
};

/* Sigil formation targets. Each particle carries its sigil seat
 * (sx,sy), dispersed origin (dx,dy, shell r≤3.6), intro stagger
 * (delay), morph window (m0,m1), and optional transit extras. */
export function sigilLayout(count, seed = 1337) {
  const rand = mulberry32(seed);
  const pts = [];
  const push = (x, y, layer, size, tint, extra) => {
    const da = rand() * TWO_PI;
    const dr = 2.2 + rand() * 1.4;
    const [w0, w1] = MORPH_WINDOWS[layer];
    const m0 = Math.max(0, w0 + (rand() - 0.5) * 0.06);
    const m1 = Math.min(1, Math.max(m0 + 0.2, w1 + (rand() - 0.5) * 0.06));
    pts.push({
      sx: x, sy: y, layer, size, tint,
      phase: rand() * TWO_PI,
      delay: rand(),
      dx: Math.cos(da) * dr,
      dy: Math.sin(da) * dr,
      m0, m1,
      ...extra,
    });
  };
  // NOTE: array order doubles as constellation assignment order
  // (contiguous member blocks), so early-window layers come first
  // and nodes materialize in evidence-pipeline order.
  for (const [layer, n] of apportion(count, [
    ['dust', 0.05], ['ring', 0.18], ['tick', 0.06], ['hex', 0.18],
    ['vertex', 0.02], ['stream', 0.38], ['core', 0.08],
  ])) {
    for (let i = 0; i < n; i++) {
      if (layer === 'dust') {
        const a = rand() * TWO_PI;
        const r = 0.4 + 1.25 * Math.sqrt(rand());
        push(Math.cos(a) * r, Math.sin(a) * r, layer, 0.3 + rand() * 0.4, 2);
      } else if (layer === 'ring') {
        const a = rand() * TWO_PI;
        const r = 1.0 + (rand() - 0.5) * 0.012;
        push(Math.cos(a) * r, Math.sin(a) * r, layer, 0.5 + rand() * 0.9, rand() < 0.7 ? 0 : 1);
      } else if (layer === 'tick') {
        const tick = (rand() * 60) | 0;
        const a = (tick / 60) * TWO_PI;
        const r = 1.0 + rand() * 0.09;
        push(Math.cos(a) * r, Math.sin(a) * r, layer, 0.4 + rand() * 0.5, 2);
      } else if (layer === 'hex') {
        const edge = (rand() * 6) | 0;
        const t = rand();
        const a0 = (edge / 6) * TWO_PI;
        const a1 = ((edge + 1) / 6) * TWO_PI;
        push((Math.cos(a0) * (1 - t) + Math.cos(a1) * t) * 0.66,
          (Math.sin(a0) * (1 - t) + Math.sin(a1) * t) * 0.66,
          layer, 0.5 + rand() * 0.8, rand() < 0.5 ? 0 : 1);
      } else if (layer === 'vertex') {
        const v = (rand() * 6) | 0;
        const a = (v / 6) * TWO_PI;
        push(Math.cos(a) * 0.66 + (rand() - 0.5) * 0.016,
          Math.sin(a) * 0.66 + (rand() - 0.5) * 0.016,
          layer, 0.9 + rand() * 0.6, 3);
      } else if (layer === 'stream') {
        const arm = (rand() * 3) | 0;
        const t = 1 - (1 - rand()) ** 2;
        const a = (arm / 3) * TWO_PI + t * 2.3;
        const r = 0.66 - t * 0.58 + (rand() - 0.5) * 0.02;
        push(Math.cos(a) * r, Math.sin(a) * r, layer,
          (0.55 + rand() * 0.8) * (1.15 - 0.5 * t), arm === 2 ? 1 : 0, { arm });
      } else if (layer === 'core') {
        const a = rand() * TWO_PI;
        const r = 0.055 * Math.sqrt(rand());
        push(Math.cos(a) * r, Math.sin(a) * r, layer, 0.7 + rand() * 0.8, 3);
      }
    }
  }
  return pts;
}

/* Entity graph for the constellation state, derived from real console
 * evidence only. Accepts data.js state pieces (Maps or plain
 * objects/arrays). Edges are validated identifiers; invalid ones
 * are dropped, never drawn. */
const KIND_ORDER = { manifest: 0, run: 1, plan: 2, report: 3 };
const asEntries = (m) => (m instanceof Map ? [...m.entries()] : Object.entries(m || {}));

export function deriveConstellation({ manifests, runs, plans, reports }) {
  const nodes = [];
  const byId = new Map();
  const add = (node) => { nodes.push(node); byId.set(node.id, node); };
  for (const [, m] of asEntries(manifests)) {
    if (m && m.manifest_id) {
      add({ id: `manifest:${m.manifest_id}`, kind: 'manifest', label: m.manifest_id, sub: m.benchmark_id || '', href: '../index.html#/audit', ref: m });
    }
  }
  for (const [runId, r] of asEntries(runs)) {
    const id = (r && r.runId) || runId;
    if (!id) continue;
    const split = String(id).startsWith('eval') ? 'eval' : 'dev';
    const base = String(id).includes('baseline-a') ? 'replay' : 'chimera';
    add({ id: `run:${id}`, kind: 'run', label: `${split}·${base}`, sub: id, href: `../index.html#/atlas?run=${encodeURIComponent(id)}`, ref: r });
  }
  for (const p of plans || []) {
    if (!p || !p.runId || !p.kind) continue;
    const short = String(p.runId).replace('20261028-', '');
    add({ id: `plan:${p.kind}:${p.runId}`, kind: 'plan', label: `${p.kind}·${short}`, sub: p.file || '', href: '../index.html#/audit', ref: p });
  }
  for (const [id, r] of asEntries(reports)) {
    if (!id) continue;
    add({ id: `report:${id}`, kind: 'report', label: (r && r.title) || id, sub: (r && r.file) || '', href: `../index.html#/archive?doc=${encodeURIComponent(id)}`, ref: r });
  }
  nodes.sort((a, b) => (KIND_ORDER[a.kind] - KIND_ORDER[b.kind]) || (a.id < b.id ? -1 : 1));
  // Golden-angle spiral: deterministic, even, no overlaps at 15 nodes.
  const n = nodes.length;
  nodes.forEach((node, i) => {
    const a = i * 2.399963;
    const r = n > 1 ? 0.38 + 0.84 * Math.sqrt(i / (n - 1)) : 0;
    node.x = Math.cos(a) * r;
    node.y = Math.sin(a) * r;
  });
  const edges = [];
  const maniById = new Map(nodes.filter((x) => x.kind === 'manifest').map((x) => [x.ref.manifest_id, x.id]));
  for (const node of nodes.filter((x) => x.kind === 'run')) {
    const mid = node.ref && (node.ref.data ? node.ref.data.manifest_id : node.ref.manifest_id);
    if (mid && maniById.has(mid)) edges.push({ a: maniById.get(mid), b: node.id, label: 'manifest' });
  }
  for (const node of nodes.filter((x) => x.kind === 'plan')) {
    const rid = `run:${node.ref.runId}`;
    if (byId.has(rid)) edges.push({ a: rid, b: node.id, label: 'sample' });
  }
  for (const node of nodes.filter((x) => x.kind === 'report')) {
    for (const run of nodes.filter((x) => x.kind === 'run')) {
      const runId = run.id.slice(4);
      const text = node.ref && node.ref.text;
      if (typeof text === 'string' && text.includes(runId)) edges.push({ a: run.id, b: node.id, label: 'cites' });
    }
  }
  return { nodes, edges };
}

/* Assign constellation targets: node clouds (gaussian puffs) plus
 * bridge particles flowing along validated edges. Members are
 * assigned in contiguous blocks so each node's arrival time follows
 * its layers; node.arrival records the mean window end. Also fixes
 * each particle's transit control point (bx,by). Mutates pts/nodes. */
export function assignConstellation(pts, nodes, edges, seed = 777) {
  const rand = mulberry32(seed);
  const gauss = () => (rand() + rand() + rand() - 1.5) * 0.66;
  const byId = new Map(nodes.map((x) => [x.id, x]));
  const block = Math.max(1, Math.floor((pts.length * 0.85) / nodes.length));
  const arrivals = new Map(nodes.map((x) => [x.id, []]));
  let members = 0;
  for (const p of pts) {
    if (edges.length && rand() < 0.15) {
      const e = edges[(rand() * edges.length) | 0];
      const a = byId.get(e.a);
      const b = byId.get(e.b);
      const t = rand();
      const mx = a.x + (b.x - a.x) * t;
      const my = a.y + (b.y - a.y) * t;
      p.tx = mx + gauss() * 0.03;
      p.ty = my + gauss() * 0.03;
      p.node = null;
      p.edgeA = e.a;
      p.edgeB = e.b;
    } else {
      const node = nodes[Math.min(nodes.length - 1, Math.floor(members / block))];
      members++;
      p.tx = node.x + gauss() * 0.085;
      p.ty = node.y + gauss() * 0.085;
      p.node = node.id;
      p.edgeA = null;
      p.edgeB = null;
      arrivals.get(node.id).push(p.m1);
    }
    // Transit control: midpoint bowed along a per-layer curve vector
    // (tangent peel for the ring, diverging arm vectors for streams,
    // outward exhale for the hexagon). Short trips stay near-linear
    // so the no-evidence fallback (target == seat) holds formation.
    const mx = (p.sx + p.tx) / 2;
    const my = (p.sy + p.ty) / 2;
    const dist = Math.hypot(p.tx - p.sx, p.ty - p.sy);
    const k = Math.min(1, dist / 0.5);
    const sr = Math.hypot(p.sx, p.sy) || 1;
    let cx = 0;
    let cy = 0;
    if (p.layer === 'ring' || p.layer === 'tick') {
      cx = (-p.sy / sr) * 0.5;
      cy = (p.sx / sr) * 0.5;
    } else if (p.layer === 'stream') {
      const aa = ((p.arm || 0) / 3) * TWO_PI;
      cx = Math.cos(aa) * 0.3;
      cy = Math.sin(aa) * 0.3;
    } else if (p.layer === 'hex' || p.layer === 'vertex') {
      cx = (p.sx / sr) * 0.2;
      cy = (p.sy / sr) * 0.2;
    }
    p.bx = mx + cx * k;
    p.by = my + cy * k;
  }
  for (const node of nodes) {
    const s = arrivals.get(node.id);
    node.arrival = s.length ? s.reduce((a, b) => a + b, 0) / s.length : 0.9;
  }
  return pts;
}

/* Morph position for scroll progress in [0,1]: quadratic bezier from
 * sigil seat through the transit control point to the constellation
 * target, eased within the particle's own window. */
export function morphTarget(p, progress) {
  const T = smootherstep((progress - p.m0) / (p.m1 - p.m0));
  const bx = p.bx === undefined ? (p.sx + p.tx) / 2 : p.bx;
  const by = p.by === undefined ? (p.sy + p.ty) / 2 : p.by;
  const u = 1 - T;
  return {
    x: u * u * p.sx + 2 * u * T * bx + T * T * p.tx,
    y: u * u * p.sy + 2 * u * T * by + T * T * p.ty,
  };
}

/* Intro convergence: dispersed shell → formation over introT in [0,1]. */
export function introTarget(p, introT, formation) {
  const t = easeOutCubic((introT - p.delay * 0.55) / 0.45);
  return { x: p.dx + (formation.x - p.dx) * t, y: p.dy + (formation.y - p.dy) * t };
}

/* Cursor force in world units: repulsion + motion-driven swirl. Pure. */
export function cursorForce(px, py, cx, cy, cvx, cvy) {
  const R = 0.70;
  const dx = px - cx;
  const dy = py - cy;
  const d2 = dx * dx + dy * dy;
  if (d2 > R * R || d2 < 1e-8) return { fx: 0, fy: 0 };
  const d = Math.sqrt(d2);
  const fall = (1 - d / R) ** 2;
  const speed = Math.min(2.5, Math.hypot(cvx, cvy));
  const nx = dx / d;
  const ny = dy / d;
  const push = 7.0 * fall;
  const swirl = 3.4 * fall * Math.min(1, speed);
  return {
    fx: nx * push + -ny * swirl * Math.sign(cvx - cvy || 1),
    fy: ny * push + nx * swirl * Math.sign(cvx - cvy || 1),
  };
}

/* Ambient drift: slow organic fields, per-particle phase. Pure. */
export function ambient(px, py, t, phase) {
  return {
    fx: 0.055 * Math.sin(py * 2.1 + t * 0.5 + phase) + 0.03 * Math.sin(t * 0.23 + phase * 2),
    fy: 0.055 * Math.cos(px * 1.7 - t * 0.42 + phase) + 0.03 * Math.cos(t * 0.31 + phase),
  };
}

/* Nearest node within radius (world units) or null. Pure. */
export function hitTest(nodes, wx, wy, radius) {
  let best = null;
  let bestD2 = radius * radius;
  for (const n of nodes) {
    const dd = (n.x - wx) * (n.x - wx) + (n.y - wy) * (n.y - wy);
    if (dd <= bestD2) { bestD2 = dd; best = n; }
  }
  return best;
}

/* Piecewise track: stops [[x0,v0],[x1,v1],...] sorted by x, with
 * smootherstep easing inside each segment and clamped ends. Drives
 * both the scroll→progress map and the camera. Pure. */
export function track(stops, x) {
  if (x <= stops[0][0]) return stops[0][1];
  for (let i = 1; i < stops.length; i++) {
    if (x <= stops[i][0]) {
      const [x0, v0] = stops[i - 1];
      const [x1, v1] = stops[i];
      return v0 + (v1 - v0) * smootherstep((x - x0) / (x1 - x0));
    }
  }
  return stops[stops.length - 1][1];
}

/* Label visibility for a node arrival at morph progress. Pure. */
export function labelAlpha(arrival, progress) {
  return smootherstep((progress - (0.52 + arrival * 0.36)) / 0.10);
}

/* Edge visibility once both endpoint arrivals are seated. Pure. */
export function edgeAlpha(arrA, arrB, progress) {
  return smootherstep((progress - Math.max(arrA, arrB) * 0.88) / 0.12);
}

/* Node-seat glow ramp. Pure. */
export function glowAlpha(arrival, progress) {
  return smootherstep((progress - arrival * 0.9) / 0.12);
}

/* Layer transit states at progress, from the real morph windows:
 * holding | transit | arrived. Pure. */
export function layerStates(progress) {
  const state = (l) => {
    const [w0, w1] = MORPH_WINDOWS[l];
    return progress < w0 ? 'holding' : progress >= w1 ? 'arrived' : 'transit';
  };
  return [
    { layer: 'ring', state: state('ring') },
    { layer: 'streams', state: state('stream') },
    { layer: 'hexagon', state: state('hex') },
    { layer: 'core', state: state('core') },
  ];
}

/* Text quiet-zone multiplier: 0 deep inside any protected rect,
 * feathering to 1 over PAD px outside it. Rects are viewport-space
 * {x0, y0, x1, y1}. Pure. */
export const QUIET_PAD = 26;
export function textQuiet(x, y, rects) {
  let m = 1;
  for (const r of rects || []) {
    const dx = Math.max(r.x0 - x, 0, x - r.x1);
    const dy = Math.max(r.y0 - y, 0, y - r.y1);
    const d = Math.hypot(dx, dy);
    if (d >= QUIET_PAD) continue;
    m = Math.min(m, smootherstep(d / QUIET_PAD));
    if (m <= 0) return 0;
  }
  return m;
}

/* Substring node filter for search across label, id, and kind. Pure. */
export function filterNodes(nodes, query) {
  const q = String(query || '').trim().toLowerCase();
  if (!q) return nodes.slice();
  return nodes.filter((n) =>
    String(n.label || '').toLowerCase().includes(q)
    || String(n.id || '').toLowerCase().includes(q)
    || String(n.kind || '').toLowerCase().includes(q));
}
