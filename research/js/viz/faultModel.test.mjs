/* Fault model tests against real run files.
 * Run: node --test research/js/viz/faultModel.test.mjs (from repo root)
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { groupSoundings } from './faultModel.js';

const root = join(dirname(fileURLToPath(import.meta.url)), '..', '..', '..');
const load = (p) => JSON.parse(readFileSync(join(root, p), 'utf8'));
const run = (runId, baseline, file) => ({ runId, baseline, data: load(file) });

test('eval soundings: 24 groups, denominators sum to 360, axis is real slow_ms', () => {
  const runs = [
    run('eval-20261028-chimera', 'chimera', 'artifacts/eval-20261028/run-chimera.json'),
    run('eval-20261028-baseline-a', 'baseline-a', 'artifacts/eval-20261028/run-baseline-a.json'),
  ];
  const { soundings, levels } = groupSoundings(runs);
  assert.deepEqual(levels, [0, 800, 1350, 2100, 3000, 3900]);
  assert.equal(soundings.length, 24);
  assert.equal(soundings.reduce((n, s) => n + s.n, 0), 360);
  assert.ok(soundings.every((s) => s.n === 15 && s.k >= 0 && s.k <= s.n));
  // S-NORM has no fault; S-DIS is disabled-only; SLOWDIS carries both.
  const norm = soundings.filter((s) => s.scenario === 'S-NORM');
  assert.ok(norm.every((s) => s.slow === 0 && s.disabled === false));
  const dis = soundings.filter((s) => s.scenario === 'S-DIS');
  assert.ok(dis.every((s) => s.slow === 0 && s.disabled === true));
  const slowdis = soundings.filter((s) => s.scenario === 'S-SLOWDIS');
  assert.ok(slowdis.every((s) => s.disabled === true && s.slow > 0));
  assert.equal(new Set(norm.map((s) => s.baseline)).size, 2);
});

test('dev soundings: 8 groups over the 2000ms fault level', () => {
  const runs = [
    run('dev-20261028-chimera', 'chimera', 'artifacts/dev-20261028/run-chimera.json'),
    run('dev-20261028-baseline-a', 'baseline-a', 'artifacts/dev-20261028/run-baseline-a.json'),
  ];
  const { soundings, levels } = groupSoundings(runs);
  assert.deepEqual(levels, [0, 2000]);
  assert.equal(soundings.length, 8);
  assert.equal(soundings.reduce((n, s) => n + s.n, 0), 160);
});

test('groupSoundings fails closed on unmappable cells', () => {
  const bad = [{ runId: 'r', baseline: 'chimera', data: { cells: [{ verifier_audit: null }], episodes: [] } }];
  assert.throws(() => groupSoundings(bad));
});
