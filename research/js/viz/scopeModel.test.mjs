/* Oscilloscope model tests: real trace/action fixtures + edge cases.
 * Run: node --test research/js/viz/scopeModel.test.mjs (from repo root)
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { buildScope, traceKind, actionKind } from './scopeModel.js';

const root = join(dirname(fileURLToPath(import.meta.url)), '..', '..', '..');
const load = (p) => JSON.parse(readFileSync(join(root, p), 'utf8'));

function episodeCase(runFile) {
  const run = load(runFile);
  const ep = run.episodes.find((e) => !String(e.trial_id).startsWith('warmup:') && e.trace_artifact);
  const trace = load(ep.trace_artifact);
  const i = ep.trace_artifact.lastIndexOf('/');
  const base = ep.trace_artifact.slice(i + 1).split('.')[0];
  const actions = load(`${ep.trace_artifact.slice(0, i + 1)}${base}.actions.json`);
  return { ep, trace, actions };
}

test('chimera episode: trace + observer lanes keep separate coordinates', () => {
  const { ep, trace, actions } = episodeCase('artifacts/eval-20261028/run-chimera.json');
  const { lanes, timeSpan } = buildScope({ trace, actions, snapshotOk: true, verification: ep.verification, verdicts: [] });
  const ids = lanes.map((l) => l.id);
  assert.deepEqual(ids, ['trace', 'actions', 'verdicts']);
  const [tl, al, vl] = lanes;
  assert.equal(tl.marks.length, trace.events.length);
  assert.match(tl.coord, /sequence_number/);
  assert.equal(al.marks.length, actions.records.length);
  assert.match(al.coord, /observer/);
  assert.ok(tl.marks.every((m) => m.title && m.detail.length && m.target));
  assert.ok(timeSpan.spanMs >= 0 && timeSpan.start && timeSpan.end);
  const kinds = new Set(tl.marks.map((m) => m.kind));
  assert.ok(kinds.has('run') && kinds.has('ok'));
  // Verdict lane ends with a snapshot slot.
  assert.equal(vl.marks[vl.marks.length - 1].xLabel, 'snapshot');
});

test('baseline-a episode: replay lane discloses missing sequence numbers', () => {
  const { ep, trace, actions } = episodeCase('artifacts/eval-20261028/run-baseline-a.json');
  assert.ok(Array.isArray(trace.steps));
  const { lanes } = buildScope({ trace, actions, snapshotOk: true, verification: ep.verification, verdicts: [] });
  assert.equal(lanes[0].id, 'replay');
  assert.match(lanes[0].coord, /no recorded sequence numbers/);
  assert.equal(lanes[0].marks.length, trace.steps.length);
});

test('unavailable verification and human verdicts stay explicit', () => {
  const { lanes } = buildScope({
    trace: { events: [] }, actions: { records: [] }, snapshotOk: false,
    verification: { status: 'unavailable', unavailable_reason: 'snapshot unreadable' },
    verdicts: [
      { planKind: 'full', cellKey: 'c1', agrees: true },
      { planKind: 'mini', cellKey: 'c2', agrees: false },
      { planKind: 'full', cellKey: 'c3', agrees: null },
    ],
  });
  const vl = lanes.find((l) => l.id === 'verdicts');
  assert.deepEqual(vl.marks.map((m) => m.kind), ['missing', 'ok', 'disagree', 'unau', 'missing']);
  assert.match(vl.marks[0].title, /snapshot unreadable/);
  assert.match(vl.marks[4].title, /No snapshot/);
  assert.match(vl.coord, /categorical/);
});

test('kind classifiers follow recorded outcomes, not assumptions', () => {
  assert.equal(traceKind({ event_type: 'action_attempted', action_outcome: 'failure' }), 'fail');
  assert.equal(traceKind({ event_type: 'verification_passed', action_outcome: 'ok' }), 'verify');
  assert.equal(traceKind({ event_type: 'run_started', action_outcome: 'ok' }), 'run');
  assert.equal(traceKind({ event_type: 'mystery', action_outcome: null }), 'info');
  assert.equal(actionKind({ outcome: 'ok', policy: 'allowed' }), 'ok');
  assert.equal(actionKind({ outcome: 'ok', policy: 'denied' }), 'policy');
  assert.equal(actionKind({ outcome: 'error', policy: 'allowed' }), 'fail');
});
