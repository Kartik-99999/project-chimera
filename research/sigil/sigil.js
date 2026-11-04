/* Convergence Sigil renderer: spring particles on a fixed,
 * non-interactive canvas. World geometry comes from engine.js;
 * entity nodes come from real console evidence via data.js.
 * No metrics are visualized — this is a presence study only.
 *
 * Scroll drives a five-stage narrative (Convergence, Separation,
 * Assembly, Exploration, Resolution) through one continuous morph
 * parameter: it rises 0→1 into the constellation, then returns
 * 1→0 so the journey resolves on the sigil it started from. */
import {
  sigilLayout, assignConstellation, deriveConstellation, morphTarget,
  introTarget, cursorForce, ambient, hitTest, smootherstep, clamp01,
  track, labelAlpha, edgeAlpha, glowAlpha, layerStates, filterNodes,
  textQuiet,
} from './engine.js';
import { loadAll } from '../js/data.js';

const canvas = document.getElementById('stage');
const ctx = canvas.getContext('2d');
const labelLayer = document.getElementById('labels');
const countsEl = document.getElementById('counts');
const panelEl = document.getElementById('panel');
const heroEl = document.getElementById('hero');
const heroTextEl = document.getElementById('hero-text');
const captionEl = document.getElementById('caption');
const signatureEl = document.getElementById('signature');
const resolutionTextEl = document.getElementById('resolution-text');
const layerItems = [...document.querySelectorAll('#layer-states li')];
const seatedEl = document.getElementById('seated');
const seatedTotalEl = document.getElementById('seated-total');
const drawnEl = document.getElementById('drawn');
const drawnTotalEl = document.getElementById('drawn-total');
const arrivalReadoutEl = document.getElementById('arrival-readout');
const searchInput = document.getElementById('search');
const railEl = document.getElementById('rail');
const matchCountEl = document.getElementById('match-count');
const railLinks = [...document.querySelectorAll('#rail a')];
const stageSections = ['hero', 'separation', 'assembly', 'atlas', 'resolution']
  .map((id) => document.getElementById(id));

const REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;
const MOBILE = matchMedia('(pointer: coarse)').matches || innerWidth < 700;
const FULL_COUNT = MOBILE ? 1800 : 4200;

/* Scroll keyframes: section-center doc Y → morph progress. The arc
 * rises into the constellation and returns to the sigil. */
const STAGE_PROGRESS = [0, 0.38, 0.72, 1, 0];

const TINTS = [
  ['#0e7490', '#0e7490'], ['#6d28d9', '#6d28d9'],
  ['#46536a', '#5b6b80'], ['#e6dcc4', '#5f6b82'],
];
function sprite([inner, outer]) {
  const c = document.createElement('canvas');
  c.width = c.height = 64;
  const g = c.getContext('2d');
  const grad = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  grad.addColorStop(0, inner);
  grad.addColorStop(0.25, outer);
  grad.addColorStop(1, 'rgba(0,0,0,0)');
  g.fillStyle = grad;
  g.fillRect(0, 0, 64, 64);
  return c;
}
const SPRITES = TINTS.map(sprite);

const sim = {
  pts: [], active: 0, nodes: [], edges: [],
  progress: 0, target: 0, introT: REDUCED ? 1 : 0,
  W: 0, H: 0, dpr: 1, ox: 0,
  heroScale: 100, heroOy: 0, constScale: 100, constOy: 0,
  keys: [], spans: [], camOy: [], camS: [],
  cursor: { x: 0, y: 0, vx: 0, vy: 0, on: false, idle: 0 },
  selected: null, related: new Set(), query: null, pillH: 30,
  running: true, slowFrames: 0, lastShed: 0,
  _layerKey: '', _arrivalKey: '', _railKey: -1,
};

function resize() {
  sim.W = innerWidth; sim.H = innerHeight;
  sim.dpr = Math.min(devicePixelRatio || 1, 1.5);
  canvas.width = Math.round(sim.W * sim.dpr);
  canvas.height = Math.round(sim.H * sim.dpr);
  sim.ox = sim.W / 2;
  // Hero framing is measured, not eyeballed: the sigil ring clears
  // the top of both bottom-anchored text blocks on every viewport.
  const topA = heroTextEl.getBoundingClientRect().top + window.scrollY;
  const resEl = document.getElementById('resolution');
  const topE = resolutionTextEl.getBoundingClientRect().top + window.scrollY - resEl.offsetTop;
  const availH = Math.max(120, Math.min(topA, topE) - 16);
  sim.heroScale = Math.max(80, Math.min(availH / 2.25, sim.W * 0.42));
  sim.heroOy = availH / 2;
  // Constellation framing leaves a bottom band for caption + panel.
  // Small screens get a tighter, higher field to clear the UI stack.
  sim.constScale = Math.min(sim.W, sim.H) * (MOBILE ? 0.28 : 0.36);
  sim.constOy = sim.H * (MOBILE ? 0.31 : 0.44);
  // Scroll keyframes at section centers; rail spans at midpoints.
  const centers = stageSections.map((el) => el.offsetTop + el.offsetHeight / 2);
  sim.keys = centers.map((c, i) => [c, STAGE_PROGRESS[i]]);
  sim.spans = centers.map((c, i) => {
    const lo = i === 0 ? -Infinity : (centers[i - 1] + c) / 2;
    const hi = i === centers.length - 1 ? Infinity : (c + centers[i + 1]) / 2;
    return [lo, hi];
  });
  // Camera tracks over morph progress. Small screens bias the
  // transit field lower, clear of the taller copy bands.
  sim.camOy = MOBILE
    ? [[0, sim.heroOy], [0.38, sim.H * 0.68], [0.72, sim.H * 0.66], [1, sim.constOy]]
    : [[0, sim.heroOy], [0.38, sim.H * 0.60], [0.72, sim.H * 0.56], [1, sim.constOy]];
  sim.camS = [[0, sim.heroScale], [0.38, sim.heroScale * 1.18], [0.72, sim.constScale * 1.06], [1, sim.constScale]];
}

/* Field reframing follows the morph: compact hero composition,
 * low transit field under the editorial bands, constellation
 * settling above the exploration UI. */
function layout() {
  return { s: track(sim.camS, sim.progress), y: track(sim.camOy, sim.progress) };
}

function toWorld(cx, cy) {
  const { s, y } = layout();
  return { x: (cx - sim.ox) / s, y: (cy - y) / s };
}
function toScreen(wx, wy) {
  const { s, y } = layout();
  return { x: sim.ox + wx * s, y: y + wy * s };
}

function buildParticles() {
  sim.pts = sigilLayout(FULL_COUNT, 1337).map((p) => ({ ...p, x: p.dx, y: p.dy, vx: 0, vy: 0 }));
  if (!sim.nodes.length) for (const p of sim.pts) { p.tx = p.sx; p.ty = p.sy; }
  else assignConstellation(sim.pts, sim.nodes, sim.edges, 777);
  sim.active = sim.pts.length;
}

function buildLabels() {
  labelLayer.replaceChildren();
  for (const n of sim.nodes) {
    const b = document.createElement('button');
    b.type = 'button';
    b.dataset.kind = n.kind;
    b.setAttribute('aria-pressed', 'false');
    b.innerHTML = `<span class="dot" aria-hidden="true"></span><span></span>`;
    b.lastChild.textContent = n.label;
    b.title = n.sub || n.kind;
    b.addEventListener('click', () => select(n.id === (sim.selected && sim.selected.id) ? null : n));
    n.el = b;
    labelLayer.appendChild(b);
  }
  const first = labelLayer.querySelector('button');
  if (first) sim.pillH = first.offsetHeight || 30;
  for (const n of sim.nodes) {
    if (n.el) n.pillW = n.el.offsetWidth || 120;
  }
}

const KIND_TITLE = { manifest: 'Benchmark manifest', run: 'Benchmark run', plan: 'Audit plan', report: 'Report' };
function select(node) {
  sim.selected = node;
  sim.related = new Set();
  if (node) {
    sim.related.add(node.id);
    for (const e of sim.edges) {
      if (e.a === node.id) sim.related.add(e.b);
      else if (e.b === node.id) sim.related.add(e.a);
    }
  }
  requestRender(); // no-op unless reduced-motion static mode
  for (const n of sim.nodes) {
    if (!n.el) continue;
    n.el.setAttribute('aria-pressed', String(n === node));
    n.el.classList.toggle('related', !!node && n !== node && sim.related.has(n.id));
  }
  if (!node) {
    panelEl.innerHTML = '<p class="empty">Select a cluster to inspect a real workspace — runs, audit plans, reports.</p>';
    return;
  }
  const rel = sim.edges.filter((e) => e.a === node.id || e.b === node.id);
  const others = rel.map((e) => {
    const o = sim.nodes.find((n) => n.id === (e.a === node.id ? e.b : e.a));
    return o ? `<li>${e.label}: ${escapeHtml(o.label)}</li>` : '';
  }).join('');
  panelEl.innerHTML = `<p class="kind">${KIND_TITLE[node.kind] || node.kind}</p><h3></h3>`
    + `<p class="sub"></p>${others ? `<ul>${others}</ul>` : ''}`
    + `<div class="row"><a>Open in console →</a><button type="button">Clear</button></div>`;
  panelEl.querySelector('h3').textContent = node.label;
  panelEl.querySelector('.sub').textContent = node.sub || '—';
  const a = panelEl.querySelector('a');
  a.href = node.href;
  panelEl.querySelector('button').addEventListener('click', () => select(null));
}
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

/* Focus + context: related particles stay bright, the rest of the
 * network stays visible but recedes. Sigil state never dims. */
function isRelated(pt) {
  if (!sim.selected || sim.progress <= 0.5) return true;
  if (!pt.node && !pt.edgeA) return true;
  return (pt.node && sim.related.has(pt.node))
    || (pt.edgeA && (sim.related.has(pt.edgeA) || sim.related.has(pt.edgeB)));
}

const KIND_WORD = { manifest: 'manifests', run: 'runs', plan: 'audit plans', report: 'reports' };
async function loadEvidence() {
  try {
    const s = await loadAll();
    const { nodes, edges } = deriveConstellation({
      manifests: s.manifests, runs: s.runs, plans: s.plans, reports: s.reports,
    });
    if (!nodes.length) throw new Error('empty evidence');
    sim.nodes = nodes; sim.edges = edges;
    assignConstellation(sim.pts, nodes, edges, 777);
    buildLabels();
    const kinds = ['manifest', 'run', 'plan', 'report'];
    signatureEl.innerHTML = kinds.map((k) => {
      const n = nodes.filter((x) => x.kind === k).length;
      return `<span class="sig"><i class="dot ${k}" aria-hidden="true"></i>${n} ${KIND_WORD[k]}</span>`;
    }).join('') + `<span class="sig">${edges.length} validated relations</span>`;
    seatedTotalEl.textContent = String(nodes.length);
    drawnTotalEl.textContent = String(edges.length);
    searchInput.placeholder = `Filter ${nodes.length} entities…`;
    const kindNames = [...new Set(nodes.map((n) => n.kind))];
    countsEl.textContent = `${nodes.length} entities · ${edges.length} validated relations · ${kindNames.join(' / ')}`;
  } catch {
    document.body.classList.add('no-evidence');
    for (const el of document.querySelectorAll('.noev')) el.hidden = false;
    signatureEl.textContent = 'Evidence unavailable — the sigil stands alone.';
    countsEl.textContent = 'Evidence unavailable — showing the sigil only.';
    arrivalReadoutEl.textContent = 'Assembly unavailable — no evidence loaded.';
    searchInput.disabled = true;
    searchInput.placeholder = 'Evidence unavailable';
  }
}

function step(dt, t) {
  if (!REDUCED && sim.introT < 1) sim.introT = Math.min(1, sim.introT + dt / 3.2);
  sim.progress = REDUCED ? sim.target : sim.progress + (sim.target - sim.progress) * Math.min(1, dt * 3.5);
  if (Math.abs(sim.target - sim.progress) < 0.0005) sim.progress = sim.target;

  const c = sim.cursor;
  c.idle += dt;
  const cursorOn = !REDUCED && c.on && c.idle < 1.2;
  const fade = cursorOn ? Math.min(1, (1.2 - c.idle) / 0.4) : 0;

  const p = sim.progress;
  const pts = sim.pts;
  for (let i = 0; i < sim.active; i++) {
    const pt = pts[i];
    const f = morphTarget(pt, p);
    const a = introTarget(pt, sim.introT, f);
    let ax = (a.x - pt.x) * 3.5 - pt.vx * 2.3;
    let ay = (a.y - pt.y) * 3.5 - pt.vy * 2.3;
    if (cursorOn) {
      const cf = cursorForce(pt.x, pt.y, c.x, c.y, c.vx, c.vy);
      ax += cf.fx * fade; ay += cf.fy * fade;
    }
    if (!REDUCED) {
      const am = ambient(pt.x, pt.y, t, pt.phase);
      ax += am.fx; ay += am.fy;
    }
    pt.vx += ax * dt; pt.vy += ay * dt;
    pt.x += pt.vx * dt; pt.y += pt.vy * dt;
  }
}

/* Editorial readouts, updated only when their values change. */
function updateReadouts(p) {
  const states = layerStates(p);
  const layerKey = states.map((r) => r.state[0]).join('');
  if (layerKey !== sim._layerKey) {
    sim._layerKey = layerKey;
    for (const li of layerItems) {
      const row = states.find((r) => r.layer === li.dataset.layer);
      if (!row) continue;
      li.dataset.state = row.state;
      li.querySelector('.sstate').textContent = row.state;
    }
  }
  if (sim.nodes.length) {
    let seated = 0;
    for (const n of sim.nodes) if (glowAlpha(n.arrival ?? 0.9, p) > 0.5) seated++;
    let drawn = 0;
    const arr = new Map(sim.nodes.map((n) => [n.id, n.arrival ?? 0.9]));
    for (const e of sim.edges) if (edgeAlpha(arr.get(e.a), arr.get(e.b), p) > 0.5) drawn++;
    const key = `${seated}/${drawn}`;
    if (key !== sim._arrivalKey) {
      sim._arrivalKey = key;
      seatedEl.textContent = String(seated);
      drawnEl.textContent = String(drawn);
    }
  }
  const center = window.scrollY + sim.H / 2;
  const stage = sim.spans.findIndex(([lo, hi]) => center >= lo && center < hi);
  if (stage !== sim._railKey) {
    sim._railKey = stage;
    railLinks.forEach((a, i) => a.classList.toggle('active', i === stage));
  }
}

function draw(t) {
  ctx.setTransform(sim.dpr, 0, 0, sim.dpr, 0, 0);
  ctx.clearRect(0, 0, sim.W, sim.H);
  const p = sim.progress;
  const { s, y: oyV } = layout();
  const arrivalOf = new Map(sim.nodes.map((n) => [n.id, n.arrival ?? 0.9]));

  // Verified relationships fade in per edge, only after both
  // endpoints' particles have arrived. Selection recolors the
  // relevant edges and dims the rest.
  if (sim.edges.length && p > 0.4) {
    ctx.lineWidth = 1;
    const pos = new Map(sim.nodes.map((n) => [n.id, toScreen(n.x, n.y)]));
    for (const e of sim.edges) {
      const gate = edgeAlpha(arrivalOf.get(e.a), arrivalOf.get(e.b), p);
      if (gate <= 0.01) continue;
      const a = pos.get(e.a);
      const b = pos.get(e.b);
      if (!a || !b) continue;
      const hot = sim.selected && (e.a === sim.selected.id || e.b === sim.selected.id);
      const dim = sim.selected && !hot;
      ctx.strokeStyle = hot
        ? `rgba(14, 116, 144, ${0.9 * gate})`
        : `rgba(109, 40, 217, ${(dim ? 0.10 : 0.42) * gate})`;
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.stroke();
    }
  }

  // Node seats glow as their particles arrive.
  if (sim.nodes.length && p > 0.35) {
    for (const n of sim.nodes) {
      const glow = glowAlpha(arrivalOf.get(n.id), p);
      if (glow <= 0.01) continue;
      const q = toScreen(n.x, n.y);
      const size = s * 0.34;
      const dim = sim.selected && !sim.related.has(n.id);
      ctx.globalAlpha = (dim ? 0.05 : 0.16) * glow;
      ctx.drawImage(SPRITES[3], q.x - size / 2, q.y - size / 2, size, size);
    }
    ctx.globalAlpha = 1;
  }

  // Text quiet zones: particles fade out around measured copy and
  // control rects so drifting dust never crowds readable text. The
  // canvas already paints below all DOM content; this clears the
  // surrounding halo too. Rects are viewport-space, refreshed per
  // frame (six cheap measurements against thousands of sprites).
  const quiet = [];
  const protect = (el) => {
    if (!el || el.style.visibility === 'hidden') return;
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) return;
    if (r.bottom < 0 || r.top > sim.H || r.right < 0 || r.left > sim.W) return;
    quiet.push({ x0: r.left, y0: r.top, x1: r.right, y1: r.bottom });
  };
  protect(heroTextEl);
  protect(resolutionTextEl);
  protect(captionEl);
  protect(panelEl);
  protect(railEl);
  protect(searchInput);

  ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < sim.active; i++) {
    const pt = sim.pts[i];
    const px = sim.ox + pt.x * s;
    const py = oyV + pt.y * s;
    if (px < -20 || py < -20 || px > sim.W + 20 || py > sim.H + 20) continue;
    const size = pt.size * s * 0.020 * (pt.layer === 'core' ? 1 + 0.10 * Math.sin(t * 2.2) : 1);
    let alpha = pt.layer === 'dust' ? 0.42 : 0.85;
    if (!isRelated(pt)) alpha *= 0.3;
    if (quiet.length) {
      const q = textQuiet(px, py, quiet);
      if (q <= 0) continue;
      alpha *= q;
    }
    ctx.globalAlpha = alpha;
    ctx.drawImage(SPRITES[pt.tint], px - size / 2, py - size / 2, size, size);
  }
  ctx.globalAlpha = 1;
  ctx.globalCompositeOperation = 'source-over';

  // Core halo breathes while the sigil holds, releases with the morph.
  if (p < 0.4) {
    const halo = s * 0.38 * (1 + 0.06 * Math.sin(t * 1.4));
    ctx.globalAlpha = 0.12 * (1 - p * 2.5);
    ctx.drawImage(SPRITES[3], sim.ox - halo / 2, oyV - halo / 2, halo, halo);
    ctx.globalAlpha = 1;
  }

  // Labels stagger in by node arrival, then de-collide.
  const items = [];
  for (const n of sim.nodes) {
    if (!n.el) continue;
    const q = toScreen(n.x, n.y);
    const a = labelAlpha(arrivalOf.get(n.id), p);
    items.push({ n, x: q.x, y: q.y, a });
  }
  items.sort((u, v) => u.y - v.y);
  const gap = sim.pillH + 6;
  let floor = -Infinity;
  for (const it of items) {
    const want = Math.max(it.y, floor + gap);
    it.dy = Math.min(want - it.y, 60); // cap drift so pills stay near nodes
    it.dx = 0;
    floor = it.y + it.dy;
  }
  // Overlapping pills push apart along the min-penetration axis
  // (a few capped passes; drift stays near the node).
  for (let pass = 0; pass < 5; pass++) {
    let moved = false;
    for (let i = 0; i < items.length; i++) {
      for (let j = i + 1; j < items.length; j++) {
        const A = items[i];
        const B = items[j];
        const dx = (B.x + B.dx) - (A.x + A.dx);
        const dy = (B.y + B.dy) - (A.y + A.dy);
        const ox = ((A.n.pillW || 120) + (B.n.pillW || 120)) / 2 + 10 - Math.abs(dx);
        const oy = sim.pillH + 6 - Math.abs(dy);
        if (ox <= 0 || oy <= 0) continue;
        if (ox < oy) {
          const dir = dx >= 0 ? 1 : -1;
          const step = Math.min(ox / 2, 14);
          const ndxA = Math.max(-70, Math.min(70, A.dx - dir * step));
          const ndxB = Math.max(-70, Math.min(70, B.dx + dir * step));
          if (ndxA !== A.dx || ndxB !== B.dx) { A.dx = ndxA; B.dx = ndxB; moved = true; }
        } else {
          const dir = dy >= 0 ? 1 : -1;
          const step = Math.min(oy / 2, 14);
          const ndyA = Math.max(-30, Math.min(80, A.dy - dir * step));
          const ndyB = Math.max(-30, Math.min(80, B.dy + dir * step));
          if (ndyA !== A.dy || ndyB !== B.dy) { A.dy = ndyA; B.dy = ndyB; moved = true; }
        }
      }
    }
    if (!moved) break;
  }
  for (const it of items) {
    const { n } = it;
    const half = (n.pillW || 120) / 2 + 8;
    const cx = Math.min(Math.max(it.x + it.dx, half), sim.W - half);
    n.el.style.transform = `translate(${cx.toFixed(1)}px, ${(it.y + it.dy).toFixed(1)}px)`;
    let boost = n === sim.selected ? 1 : 0.92;
    if (sim.selected && p > 0.5 && !sim.related.has(n.id)) boost = 0.45;
    if (sim.query && !sim.query.has(n.id)) boost *= 0.18;
    n.el.style.opacity = (it.a * boost).toFixed(3);
    n.el.style.visibility = it.a > 0.02 ? 'visible' : 'hidden';
  }
  heroEl.style.opacity = clamp01(1 - p * 1.6).toFixed(3);
  heroEl.style.visibility = p < 0.6 ? 'visible' : 'hidden';
  captionEl.style.opacity = smootherstep((p - 0.45) / 0.25).toFixed(3);
  updateReadouts(p);
}

function frame(now) {
  if (!sim.running) return;
  const t = now / 1000;
  const dt = Math.min(0.05, t - (frame.prev || t));
  frame.prev = t;
  step(dt, t);
  draw(t);
  // Adaptive shed: sustained slow frames thin the field (never below 800).
  if (!REDUCED && dt > 0.024 && sim.active > 800 && t - sim.lastShed > 2) {
    if (++sim.slowFrames > 60) {
      sim.active = Math.max(800, Math.floor(sim.active * 0.75));
      sim.slowFrames = 0;
      sim.lastShed = t;
    }
  } else if (dt <= 0.024) sim.slowFrames = 0;
  requestAnimationFrame(frame);
}

function onScroll() {
  sim.target = track(sim.keys, window.scrollY + sim.H / 2);
}

function applySearch(q) {
  if (!q.trim()) {
    sim.query = null;
    matchCountEl.textContent = '';
    requestRender();
    return;
  }
  const matches = filterNodes(sim.nodes, q);
  sim.query = new Set(matches.map((n) => n.id));
  matchCountEl.textContent = `${matches.length} of ${sim.nodes.length}`;
  requestRender();
}

function bindInput() {
  const ctl = new AbortController();
  const { signal } = ctl;
  addEventListener('scroll', onScroll, { passive: true, signal });
  addEventListener('resize', resize, { signal });
  const c = sim.cursor;
  let last = null;
  const point = (cx, cy) => {
    const w = toWorld(cx, cy);
    const now = performance.now() / 1000;
    if (last) {
      const dt = Math.max(1e-3, now - last.t);
      const vx = (w.x - last.x) / dt;
      const vy = (w.y - last.y) / dt;
      c.vx += (vx - c.vx) * 0.35;
      c.vy += (vy - c.vy) * 0.35;
    }
    c.x = w.x; c.y = w.y; c.on = true; c.idle = 0;
    last = { x: w.x, y: w.y, t: now };
  };
  addEventListener('pointermove', (e) => point(e.clientX, e.clientY), { passive: true, signal });
  addEventListener('pointerdown', (e) => point(e.clientX, e.clientY), { passive: true, signal });
  addEventListener('pointerleave', () => { c.on = false; last = null; }, { signal });
  document.addEventListener('visibilitychange', () => {
    sim.running = !document.hidden;
    if (sim.running) { frame.prev = 0; requestAnimationFrame(frame); }
  }, { signal });
  addEventListener('pagehide', () => { sim.running = false; ctl.abort(); }, { signal });
  canvas.addEventListener('click', () => {}, { signal }); // canvas never intercepts; clicks hit labels
  addEventListener('click', (e) => {
    if (e.target.closest('#panel, #labels, #caption, a, button')) return;
    if (sim.progress < 0.55 || !sim.nodes.length) { select(null); return; }
    const w = toWorld(e.clientX, e.clientY);
    select(hitTest(sim.nodes, w.x, w.y, 0.20));
  }, { signal });
  addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && e.target !== searchInput) select(null);
  }, { signal });
  searchInput.addEventListener('input', () => applySearch(searchInput.value), { signal });
  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { searchInput.value = ''; applySearch(''); }
    else if (e.key === 'Enter') {
      const matches = filterNodes(sim.nodes, searchInput.value);
      if (matches.length) select(matches[0]);
    }
  }, { signal });
  return ctl;
}

/* Reduced motion: the final composed state as on-demand static
 * frames — no simulation loop, no perpetual redraw. */
let renderQueued = false;
function requestRender() {
  if (!REDUCED || renderQueued) return;
  renderQueued = true;
  requestAnimationFrame(() => {
    renderQueued = false;
    sim.progress = sim.target;
    for (let i = 0; i < sim.active; i++) {
      const pt = sim.pts[i];
      const f = morphTarget(pt, sim.target);
      const a = introTarget(pt, 1, f);
      pt.x = a.x; pt.y = a.y; pt.vx = 0; pt.vy = 0;
    }
    draw(0);
  });
}

/* Debug handle for evaluation and demos (read-only use). */
window.__sigil = sim;

resize();
buildParticles();
const inputCtl = bindInput();
onScroll();
loadEvidence().then(requestRender);
if (document.fonts && document.fonts.ready) {
  document.fonts.ready.then(() => { resize(); onScroll(); requestRender(); });
}
if (REDUCED) {
  requestRender();
  addEventListener('scroll', requestRender, { passive: true, signal: inputCtl.signal });
  addEventListener('resize', requestRender, { signal: inputCtl.signal });
} else {
  requestAnimationFrame(frame);
}
