/* Sigil engine tests: determinism, layout invariants, staged morph
 * transit, arrival ordering, field math, and real-entity
 * constellation derivation.
 * Run: node --test research/sigil/engine.test.mjs (from repo root)
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import {
  sigilLayout, assignConstellation, deriveConstellation, morphTarget,
  introTarget, cursorForce, ambient, hitTest, track, labelAlpha,
  edgeAlpha, glowAlpha, layerStates, filterNodes, textQuiet, QUIET_PAD,
} from './engine.js';

const here = dirname(fileURLToPath(import.meta.url));
const mean = (xs) => xs.reduce((a, b) => a + b, 0) / xs.length;

test('sigil layout is deterministic per seed and bounded', () => {
  const a = sigilLayout(600, 42);
  const b = sigilLayout(600, 42);
  assert.deepEqual(a, b);
  assert.equal(a.length, 600);
  const c = sigilLayout(600, 43);
  assert.notDeepEqual(a, c);
  const r = (p) => Math.hypot(p.sx, p.sy);
  const byLayer = (l) => a.filter((p) => p.layer === l);
  assert.ok(byLayer('ring').every((p) => Math.abs(r(p) - 1) < 0.05));
  assert.ok(byLayer('tick').every((p) => r(p) >= 1 && r(p) <= 1.1));
  assert.ok(byLayer('core').every((p) => r(p) <= 0.06));
  assert.ok(byLayer('dust').every((p) => r(p) <= 1.7));
  assert.ok(a.every((p) => Math.hypot(p.dx, p.dy) >= 2.2 && Math.hypot(p.dx, p.dy) <= 3.7));
  assert.ok(a.every((p) => p.delay >= 0 && p.delay < 1 && Number.isFinite(p.phase)));
  // Vertex nodes sit on the hexagon corners; streams know their arm.
  const verts = [0, 1, 2, 3, 4, 5].map((v) => (v / 6) * Math.PI * 2);
  assert.ok(byLayer('vertex').length > 0);
  assert.ok(byLayer('vertex').every((p) => verts.some((av) => {
    const vx = Math.cos(av) * 0.66;
    const vy = Math.sin(av) * 0.66;
    return Math.hypot(p.sx - vx, p.sy - vy) < 0.03;
  })));
  assert.ok(byLayer('stream').every((p) => p.arm === 0 || p.arm === 1 || p.arm === 2));
  // Morph windows are valid and stage layers in order.
  assert.ok(a.every((p) => p.m0 >= 0 && p.m1 <= 1 && p.m1 - p.m0 >= 0.19));
  const m0 = (l) => mean(byLayer(l).map((p) => p.m0));
  const m1 = (l) => mean(byLayer(l).map((p) => p.m1));
  assert.ok(m0('dust') < m0('ring') && m0('ring') < m0('stream')
    && m0('stream') < m0('hex') && m0('hex') < m0('core'));
  assert.ok(m1('dust') < m1('ring') && m1('ring') < m1('stream')
    && m1('stream') < m1('hex') && m1('hex') < m1('core'));
});

test('morph and intro hit exact endpoints', () => {
  const pts = assignConstellation(sigilLayout(200, 7),
    [{ id: 'n0', x: 0.5, y: -0.3 }, { id: 'n1', x: -0.4, y: 0.2 }], [], 9);
  const near = (got, want) => assert.ok(
    Math.abs(got.x - want.x) < 1e-9 && Math.abs(got.y - want.y) < 1e-9,
    `expected ${JSON.stringify(got)} near ${JSON.stringify(want)}`);
  for (const p of pts) {
    near(morphTarget(p, 0), { x: p.sx, y: p.sy });
    near(morphTarget(p, 1), { x: p.tx, y: p.ty });
    near(introTarget(p, 0, { x: 1, y: 2 }), { x: p.dx, y: p.dy });
    near(introTarget(p, 1, { x: 1, y: 2 }), { x: 1, y: 2 });
  }
});

test('transit curves away from the chord; fallback holds still', () => {
  const pts = assignConstellation(sigilLayout(300, 11),
    [{ id: 'n0', x: 2.0, y: 0 }, { id: 'n1', x: -2.0, y: 0 }], [], 9);
  const ring = pts.find((p) => p.layer === 'ring');
  const mid = morphTarget(ring, (ring.m0 + ring.m1) / 2);
  const linx = (ring.sx + ring.tx) / 2;
  const liny = (ring.sy + ring.ty) / 2;
  assert.ok(Math.hypot(mid.x - linx, mid.y - liny) > 0.15); // tangent peel
  // The three arms take diverging control offsets.
  const off = (p) => [p.bx - (p.sx + p.tx) / 2, p.by - (p.sy + p.ty) / 2];
  const arms = [0, 1, 2].map((k) => pts.filter((p) => p.layer === 'stream' && p.arm === k).map(off));
  const mo = (xs) => [mean(xs.map(([x]) => x)), mean(xs.map(([, y]) => y))];
  const [o0, o1, o2] = arms.map(mo);
  assert.ok(Math.hypot(o0[0] - o1[0], o0[1] - o1[1]) > 0.25);
  assert.ok(Math.hypot(o1[0] - o2[0], o1[1] - o2[1]) > 0.25);
  // No-evidence fallback: target == seat, no control point stored.
  const still = { sx: 0.5, sy: -0.2, tx: 0.5, ty: -0.2, m0: 0.2, m1: 0.8 };
  const at = morphTarget(still, 0.5);
  assert.ok(Math.abs(at.x - 0.5) < 1e-9 && Math.abs(at.y + 0.2) < 1e-9);
});

test('members record nodes; arrivals spread in assignment order', () => {
  const nodes = [
    { id: 'n0', x: 0, y: 0 }, { id: 'n1', x: 1, y: 0 }, { id: 'n2', x: 0, y: 1 },
  ];
  const pts = assignConstellation(sigilLayout(300, 5), nodes, [], 9);
  assert.ok(pts.every((p) => p.node && p.edgeA === null && p.edgeB === null));
  assert.ok(pts.every((p) => {
    const n = nodes.find((x) => x.id === p.node);
    return Math.hypot(p.tx - n.x, p.ty - n.y) < 0.3;
  }));
  const [a0, a1, a2] = nodes.map((n) => n.arrival);
  assert.ok([a0, a1, a2].every((a) => a >= 0 && a <= 1));
  assert.ok(a0 < 0.65 && a1 > 0.65 && a2 > 0.65); // early → late layers
  assert.ok(Math.max(a0, a1, a2) - Math.min(a0, a1, a2) > 0.15);
});

test('bridge particles record their edge endpoints', () => {
  const nodes = [{ id: 'n0', x: 0, y: 0 }, { id: 'n1', x: 1, y: 0 }];
  const edges = [{ a: 'n0', b: 'n1', label: 'manifest' }];
  const pts = assignConstellation(sigilLayout(300, 5), nodes, edges, 9);
  const bridge = pts.filter((p) => p.node === null);
  const members = pts.filter((p) => p.node !== null);
  assert.ok(bridge.length > 10 && members.length > 100);
  assert.ok(bridge.every((p) => p.edgeA === 'n0' && p.edgeB === 'n1'));
  assert.ok(bridge.every((p) => p.tx >= -0.2 && p.tx <= 1.2 && Math.abs(p.ty) < 0.2));
});

test('cursor force repels nearby, ignores far, swirls with motion', () => {
  assert.deepEqual(cursorForce(5, 5, 0, 0, 0, 0), { fx: 0, fy: 0 });
  const still = cursorForce(0.2, 0, 0, 0, 0, 0);
  assert.ok(still.fx > 0 && Math.abs(still.fy) < 1e-9); // pure radial push
  const moving = cursorForce(0.2, 0, 0, 0, 1.5, 0);
  assert.ok(moving.fx > 0 && Math.abs(moving.fy) > 0.1); // swirl joins in
  const fast = cursorForce(0.2, 0, 0, 0, 9, 0);
  const capped = cursorForce(0.2, 0, 0, 0, 99, 0);
  assert.deepEqual(fast, capped); // speed influence saturates
});

test('ambient drift stays small and varies with time', () => {
  const a = ambient(0.3, -0.2, 1, 0.5);
  const b = ambient(0.3, -0.2, 50, 0.5);
  assert.ok(Math.hypot(a.fx, a.fy) < 0.12);
  assert.notDeepEqual(a, b);
});

test('hitTest returns the nearest node in radius or null', () => {
  const nodes = [{ id: 'a', x: 0, y: 0 }, { id: 'b', x: 1, y: 0 }];
  assert.equal(hitTest(nodes, 0.05, 0, 0.2).id, 'a');
  assert.equal(hitTest(nodes, 0.6, 0, 0.5).id, 'b');
  assert.equal(hitTest(nodes, 5, 5, 0.5), null);
});

test('deriveConstellation validates edges, drops invalid ones', () => {
  const { nodes, edges } = deriveConstellation({
    manifests: new Map([['m.json', { manifest_id: 'm1', benchmark_id: 'b' }]]),
    runs: new Map([['eval-1-chimera', { runId: 'eval-1-chimera', data: { manifest_id: 'm1' } }]]),
    plans: [
      { runId: 'eval-1-chimera', kind: 'full', file: 'p.json' },
      { runId: 'ghost-run', kind: 'full', file: 'g.json' },
    ],
    reports: new Map([
      ['r1', { id: 'r1', title: 'R', file: 'r.md', text: 'run eval-1-chimera did well' }],
      ['r2', { id: 'r2', title: 'R2', file: 'r2.md', text: 'nothing cited here' }],
    ]),
  });
  assert.equal(nodes.length, 6); // 1 manifest + 1 run + 2 plans + 2 reports
  const pairs = edges.map((e) => `${e.a}>${e.b}`);
  assert.ok(pairs.includes('manifest:m1>run:eval-1-chimera'));
  assert.ok(pairs.includes('run:eval-1-chimera>plan:full:eval-1-chimera'));
  assert.ok(pairs.includes('run:eval-1-chimera>report:r1'));
  assert.ok(!pairs.some((p) => p.includes('ghost-run')));
  assert.ok(!pairs.some((p) => p.includes('report:r2')));
  // Placement is deterministic and bounded.
  const data = {
    manifests: new Map([['m.json', { manifest_id: 'm1', benchmark_id: 'b' }]]),
    runs: new Map([['eval-1-chimera', { runId: 'eval-1-chimera', data: { manifest_id: 'm1' } }]]),
    plans: [{ runId: 'eval-1-chimera', kind: 'full', file: 'p.json' }],
    reports: new Map(),
  };
  const once = deriveConstellation(data).nodes.map((n) => [n.x, n.y]);
  const twice = deriveConstellation(data).nodes.map((n) => [n.x, n.y]);
  assert.deepEqual(once, twice);
  assert.ok(once.every(([x, y]) => Math.hypot(x, y) <= 1.25));
});

test('real evidence yields the 15-entity constellation', async () => {
  const { installFetch } = await import('../js/pages/test-setup.mjs');
  installFetch(join(here, '..', '..'));
  const { loadAll } = await import('../js/data.js');
  const s = await loadAll();
  const { nodes, edges } = deriveConstellation({
    manifests: s.manifests, runs: s.runs, plans: s.plans, reports: s.reports,
  });
  const kinds = nodes.map((n) => n.kind).sort().join(',');
  assert.equal(nodes.length, 15);
  assert.equal(kinds, 'manifest,manifest,plan,plan,plan,plan,plan,plan,report,report,report,run,run,run,run');
  assert.equal(edges.filter((e) => e.label === 'manifest').length, 4);
  assert.equal(edges.filter((e) => e.label === 'sample').length, 6);
  assert.ok(edges.filter((e) => e.label === 'cites').length >= 3);
  assert.ok(nodes.every((n) => n.href.startsWith('../index.html#/')
    && Number.isFinite(n.x) && Math.hypot(n.x, n.y) <= 1.25));
  // Nodes keep a minimum separation for label legibility.
  let minD2 = Infinity;
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const d2 = (nodes[i].x - nodes[j].x) ** 2 + (nodes[i].y - nodes[j].y) ** 2;
      if (d2 < minD2) minD2 = d2;
    }
  }
  assert.ok(Math.sqrt(minD2) > 0.15);
  // Materialization follows the evidence pipeline: manifests first.
  assignConstellation(sigilLayout(1800, 1337), nodes, edges, 777);
  const arr = (kind) => nodes.filter((n) => n.kind === kind).map((n) => n.arrival);
  assert.ok(Math.max(...arr('manifest')) < Math.min(...arr('report')));
});

test('track hits every stop, eases between, clamps ends', () => {
  const stops = [[0, 0], [10, 0.38], [20, 0.72], [30, 1], [40, 0]];
  for (const [x, v] of stops) assert.equal(track(stops, x), v);
  assert.equal(track(stops, -5), 0);
  assert.equal(track(stops, 99), 0);
  assert.equal(track([[0, 0], [1, 10]], 0.5), 5); // smootherstep(0.5) = 0.5
  const mid = track(stops, 15);
  assert.ok(mid > 0.38 && mid < 0.72);
  // Triangle wave: the return journey descends through assembly.
  const back = track(stops, 35);
  assert.ok(back > 0 && back < 1);
});

test('alpha gates open with progress and arrival', () => {
  assert.equal(labelAlpha(0.5, 0), 0);
  assert.equal(edgeAlpha(0.5, 0.5, 0), 0);
  assert.equal(glowAlpha(0.5, 0), 0);
  assert.equal(labelAlpha(1, 1), 1);
  assert.equal(edgeAlpha(1, 1, 1), 1);
  // The glow ramp tops out at 0.96 for the latest arrival — visually
  // complete by design, just short of the mathematical gate end.
  assert.ok(glowAlpha(1, 1) > 0.95);
  // Earlier arrivals open first; edges wait for the later endpoint.
  assert.ok(labelAlpha(0.4, 0.75) > labelAlpha(0.9, 0.75));
  assert.ok(edgeAlpha(0.5, 0.5, 0.8) > edgeAlpha(0.5, 1.0, 0.8));
  assert.ok(glowAlpha(0.4, 0.6) > glowAlpha(0.9, 0.6));
});

test('layer states follow the real morph windows', () => {
  const at = (p) => Object.fromEntries(layerStates(p).map((r) => [r.layer, r.state]));
  assert.deepEqual(at(0), { ring: 'holding', streams: 'holding', hexagon: 'holding', core: 'holding' });
  assert.deepEqual(at(1), { ring: 'arrived', streams: 'arrived', hexagon: 'arrived', core: 'arrived' });
  assert.deepEqual(at(0.29), { ring: 'transit', streams: 'transit', hexagon: 'holding', core: 'holding' });
  assert.deepEqual(at(0.6), { ring: 'arrived', streams: 'transit', hexagon: 'transit', core: 'transit' });
});

test('filterNodes matches label, id, and kind', () => {
  const nodes = [
    { id: 'manifest:dev-v1', kind: 'manifest', label: 'dev-v1' },
    { id: 'run:eval-1-chimera', kind: 'run', label: 'eval·chimera' },
    { id: 'report:r1', kind: 'report', label: 'Held-out report' },
  ];
  assert.equal(filterNodes(nodes, '').length, 3);
  assert.equal(filterNodes(nodes, '   ').length, 3);
  assert.deepEqual(filterNodes(nodes, 'chimera').map((n) => n.id), ['run:eval-1-chimera']);
  assert.deepEqual(filterNodes(nodes, 'REPORT').map((n) => n.id), ['report:r1']);
  assert.deepEqual(filterNodes(nodes, 'manifest:').map((n) => n.id), ['manifest:dev-v1']);
  assert.deepEqual(filterNodes(nodes, 'zzz'), []);
});

test('textQuiet clears protected rects and feathers outside them', () => {
  const r = [{ x0: 100, y0: 100, x1: 300, y1: 200 }];
  assert.equal(textQuiet(200, 150, r), 0);
  assert.equal(textQuiet(100, 100, r), 0);
  assert.equal(textQuiet(0, 0, []), 1);
  assert.equal(textQuiet(0, 0, null), 1);
  assert.equal(textQuiet(100 - QUIET_PAD - 1, 150, r), 1);
  const mid = textQuiet(100 - QUIET_PAD / 2, 150, r);
  assert.ok(mid > 0 && mid < 1);
  const two = [...r, { x0: 500, y0: 500, x1: 600, y1: 600 }];
  assert.equal(textQuiet(550, 550, two), 0);
  assert.equal(textQuiet(200, 150, two), 0);
  assert.equal(textQuiet(400, 400, two), 1);
});
