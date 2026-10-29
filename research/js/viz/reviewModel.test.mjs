/* Review model tests: decision rules, import, summary, storage, export.
 * Run: node --test research/js/viz/reviewModel.test.mjs (from repo root)
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import {
  DECISIONS_SCHEMA, validateDecision, validateImport, summarize,
  loadState, saveState, exportDoc, episodeKey,
} from './reviewModel.js';

const KEYS = ['r1::t1', 'r1::t2'];
const good = {
  assessment: 'verified-success', agreement: 'agrees', sufficiency: 'sufficient',
  reason: 'P1-P3 hold on the snapshot', missing_evidence: '',
  blinded: true, assessed_at: '2026-10-29T10:00:00.000Z',
  revealed_at: '2026-10-29T10:05:00.000Z', corrections: [],
};

test('validateDecision accepts a complete blinded decision', () => {
  assert.deepEqual(validateDecision('r1::t1', KEYS, good), []);
});

test('validateDecision rejects unknown episodes, bad enums, empty reasons', () => {
  assert.ok(validateDecision('nope::x', KEYS, good).length === 1);
  assert.ok(validateDecision('r1::t1', KEYS, { ...good, assessment: 'maybe' }).length);
  assert.ok(validateDecision('r1::t1', KEYS, { ...good, agreement: 'yes' }).length);
  assert.ok(validateDecision('r1::t1', KEYS, { ...good, sufficiency: 'ok' }).length);
  assert.ok(validateDecision('r1::t1', KEYS, { ...good, reason: '  ' }).length);
  assert.ok(validateDecision('r1::t1', KEYS, 'not-an-object').length);
});

test('inconclusive/insufficient decisions require missing evidence', () => {
  assert.ok(validateDecision('r1::t1', KEYS, { ...good, assessment: 'inconclusive' }).length);
  assert.ok(validateDecision('r1::t1', KEYS,
    { ...good, assessment: 'inconclusive', missing_evidence: 'snapshot unreadable' }).length === 0);
  assert.ok(validateDecision('r1::t1', KEYS, { ...good, sufficiency: 'insufficient' }).length);
});

test('agreement requires reveal; blinded flag must match timestamps', () => {
  const unrevealed = { ...good, revealed_at: null, blinded: true };
  assert.ok(validateDecision('r1::t1', KEYS, unrevealed).length); // agrees without reveal
  const und = { ...unrevealed, agreement: 'undetermined' };
  assert.deepEqual(validateDecision('r1::t1', KEYS, und), []);
  const early = { ...good, assessed_at: '2026-10-29T10:06:00.000Z', blinded: true };
  assert.ok(validateDecision('r1::t1', KEYS, early).length); // assessed after reveal
  const honest = { ...early, blinded: false };
  assert.deepEqual(validateDecision('r1::t1', KEYS, honest), []);
  assert.ok(validateDecision('r1::t1', KEYS, { ...good, assessed_at: 'yesterday' }).length);
});

test('corrections need timestamps, previous values, and reasons', () => {
  const bad = { ...good, corrections: [{ at: '2026-10-29T11:00:00.000Z' }] };
  assert.ok(validateDecision('r1::t1', KEYS, bad).length >= 2);
  const ok = {
    ...good, corrections: [{
      at: '2026-10-29T11:00:00.000Z', previous: { assessment: 'inconclusive' }, reason: 're-read the snapshot',
    }],
  };
  assert.deepEqual(validateDecision('r1::t1', KEYS, ok), []);
});

test('validateImport checks schema, packet binding, and every decision', () => {
  const doc = { schema: DECISIONS_SCHEMA, packet_sha256: 'abc', decisions: { 'r1::t1': good } };
  assert.deepEqual(validateImport(doc, { packetKeys: KEYS, packetSha: 'abc' }), []);
  assert.ok(validateImport({ ...doc, schema: 'wrong' }, { packetKeys: KEYS, packetSha: 'abc' }).length);
  assert.ok(validateImport(doc, { packetKeys: KEYS, packetSha: 'other' }).length);
  assert.ok(validateImport({ ...doc, decisions: { 'r1::t1': { ...good, reason: '' } } },
    { packetKeys: KEYS, packetSha: 'abc' }).length);
  assert.ok(validateImport({ ...doc, decisions: { 'zz::t9': good } }, { packetKeys: KEYS, packetSha: 'abc' }).length);
  assert.ok(validateImport(null, { packetKeys: KEYS, packetSha: 'abc' }).length);
});

test('summarize counts recorded decisions and gates completion on reviewer', () => {
  const packet = { episodes: [{ key: 'r1::t1', recorded: { outcome: 'failed' }, verifier: { checks: [] } }, { key: 'r1::t2', recorded: { outcome: 'failed' }, verifier: { checks: [] } }] };
  const empty = summarize(packet, { reviewer: 'ann', decisions: {} });
  assert.equal(empty.recorded, 0);
  assert.equal(empty.complete, false);
  const full = summarize(packet, { reviewer: 'ann', decisions: { 'r1::t1': good, 'r1::t2': good } });
  assert.equal(full.recorded, 2);
  assert.equal(full.complete, true);
  const anon = summarize(packet, { reviewer: '', decisions: { 'r1::t1': good, 'r1::t2': good } });
  assert.equal(anon.complete, false);
});

test('storage round-trips state and survives corruption', () => {
  const store = {};
  const storage = { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); } };
  assert.deepEqual(loadState(storage), { reviewer: '', decisions: {}, partials: {} });
  saveState(storage, { reviewer: 'ann', decisions: { a: 1 }, partials: { b: 2 } });
  assert.deepEqual(loadState(storage), { reviewer: 'ann', decisions: { a: 1 }, partials: { b: 2 } });
  store['chimera-mini-review:v1'] = '{broken';
  assert.deepEqual(loadState(storage), { reviewer: '', decisions: {}, partials: {} });
});

test('exportDoc binds decisions to packet bytes via sha256', async () => {
  const packetText = '{"episodes":[]}';
  const expected = createHash('sha256').update(packetText, 'utf8').digest('hex');
  const doc = await exportDoc({ packetText, state: { reviewer: 'ann', decisions: { k: good } }, exportedAt: '2026-10-29T12:00:00.000Z' });
  assert.equal(doc.schema, DECISIONS_SCHEMA);
  assert.equal(doc.packet_sha256, expected);
  assert.equal(doc.reviewer, 'ann');
  const fallback = await exportDoc({ packetText, state: {}, subtle: null });
  assert.equal(fallback.packet_sha256, null);
  assert.match(fallback.sha_note, /WebCrypto unavailable/);
});

test('episodeKey matches the packet key convention', () => {
  assert.equal(episodeKey('r', 't'), 'r::t');
});
