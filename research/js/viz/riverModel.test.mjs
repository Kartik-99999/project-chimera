/* River model tests: real run files + unit edge cases.
 * Run: node --test research/js/viz/riverModel.test.mjs (from repo root)
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import {
  outcomeNode, outcomeFilter, buildAuditMap, aggregateFlows,
} from './riverModel.js';
import { isWarmup } from '../data.js';

const root = join(dirname(fileURLToPath(import.meta.url)), '..', '..', '..');
const load = (p) => JSON.parse(readFileSync(join(root, p), 'utf8'));
const run = (runId, baseline, file) => ({ runId, baseline, data: load(file) });

function transitionSums(flows) {
  const sums = new Map();
  for (const f of flows) {
    const k = `${f.fromCol}->${f.toCol}`;
    sums.set(k, (sums.get(k) || 0) + f.value);
  }
  return sums;
}

test('eval split: every measured episode counted exactly once per transition', () => {
  const runs = [
    run('eval-20261028-chimera', 'chimera', 'artifacts/eval-20261028/run-chimera.json'),
    run('eval-20261028-baseline-a', 'baseline-a', 'artifacts/eval-20261028/run-baseline-a.json'),
  ];
  const { episodes, flows } = aggregateFlows(runs);
  assert.equal(episodes.length, 360);
  assert.ok(episodes.every((e) => !isWarmup(e)));
  for (const [t, sum] of transitionSums(flows)) assert.equal(sum, 360, t);
  // Outcome column matches an independent recount from the episodes.
  const recount = new Map();
  for (const e of episodes) recount.set(outcomeNode(e), (recount.get(outcomeNode(e)) || 0) + 1);
  const col2 = new Map();
  for (const f of flows.filter((x) => x.toCol === 2)) col2.set(f.to, (col2.get(f.to) || 0) + f.value);
  assert.deepEqual(col2, recount);
});

test('dev split with audited runs: all cells audited, no double counting', () => {
  const runs = [
    run('dev-20261028-chimera', 'chimera', 'artifacts/dev-20261028/run-chimera.audited.json'),
    run('dev-20261028-baseline-a', 'baseline-a', 'artifacts/dev-20261028/run-baseline-a.audited.json'),
  ];
  const { episodes, flows } = aggregateFlows(runs);
  assert.equal(episodes.length, 160);
  for (const [t, sum] of transitionSums(flows)) assert.equal(sum, 160, t);
  const auditStates = new Set(flows.filter((x) => x.toCol === 3).map((x) => x.to));
  assert.deepEqual(auditStates, new Set(['cell audited']));
});

test('raw dev runs show pending audit state (no verdicts applied)', () => {
  const runs = [run('dev-20261028-chimera', 'chimera', 'artifacts/dev-20261028/run-chimera.json')];
  const { flows } = aggregateFlows(runs);
  const auditStates = new Set(flows.filter((x) => x.toCol === 3).map((x) => x.to));
  assert.deepEqual(auditStates, new Set(['cell pending']));
});

test('outcomeNode: harness errors form their own node; unknown outcomes kept visible', () => {
  assert.equal(outcomeNode({ outcome: 'failed', error: 'harness_error: boom' }), 'failed · harness error');
  assert.equal(outcomeNode({ outcome: 'succeeded', error: '' }), 'succeeded');
  assert.equal(outcomeNode({ outcome: 'weird', error: null }), 'other (weird)');
  assert.equal(outcomeFilter('failed · harness error'), 'harness-error');
  assert.equal(outcomeFilter('succeeded'), 'succeeded');
  assert.equal(outcomeFilter('other (weird)'), '');
});

test('buildAuditMap fails closed on unmappable cells', () => {
  const bad = [{ runId: 'r', baseline: 'chimera', data: { cells: [{ verifier_audit: null }], episodes: [] } }];
  assert.throws(() => buildAuditMap(bad));
});
