/* Review model tests: decision rules, import, summary, storage, export.
 * Run: node --test research/js/viz/reviewModel.test.mjs (from repo root)
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import {
  DECISIONS_SCHEMA, AUDIT_DECISIONS_SCHEMA, AUDIT_STORAGE_KEY,
  validateDecision, validateAuditDecision, validateImport, summarize,
  summarizeAudit, loadState, saveState, exportDoc, episodeKey,
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

const auditGood = {
  checks: { P1: true, P2: true, P3: false }, note: '',
  blinded: true, assessed_at: '2026-10-30T10:00:00.000Z', revealed_at: null,
};

test('validateAuditDecision enforces check-level shapes', () => {
  assert.deepEqual(validateAuditDecision('r1::t1', KEYS, auditGood), []);
  assert.ok(validateAuditDecision('nope::x', KEYS, auditGood).length === 1);
  assert.match(validateAuditDecision('nope::x', KEYS, auditGood)[0], /not one of the 2 packet episodes/);
  assert.ok(validateAuditDecision('r1::t1', KEYS, { ...auditGood, checks: { P1: true } }).length);
  assert.ok(validateAuditDecision('r1::t1', KEYS, { ...auditGood, checks: { P1: true, P2: 'yes', P3: false } }).length);
  assert.ok(validateAuditDecision('r1::t1', KEYS, 'not-an-object').length);
  const unaud = {
    verdict: 'unauditable', reason: 'snapshot missing', blinded: true,
    assessed_at: '2026-10-30T10:00:00.000Z', revealed_at: null,
  };
  assert.deepEqual(validateAuditDecision('r1::t1', KEYS, unaud), []);
  assert.ok(validateAuditDecision('r1::t1', KEYS, { ...unaud, reason: '  ' }).length);
  assert.ok(validateAuditDecision('r1::t1', KEYS, { ...unaud, checks: { P1: true, P2: true, P3: true } }).length);
  const early = { ...auditGood, revealed_at: '2026-10-30T09:00:00.000Z', blinded: true };
  assert.ok(validateAuditDecision('r1::t1', KEYS, early).length); // assessed after reveal
  assert.deepEqual(validateAuditDecision('r1::t1', KEYS, { ...early, blinded: false }), []);
});

test('validateImport and exportDoc honor the audit schema', async () => {
  const doc = { schema: AUDIT_DECISIONS_SCHEMA, packet_sha256: 'abc', decisions: { 'r1::t1': auditGood } };
  const opts = { packetKeys: KEYS, packetSha: 'abc', schema: AUDIT_DECISIONS_SCHEMA, audit: true };
  assert.deepEqual(validateImport(doc, opts), []);
  assert.ok(validateImport({ ...doc, schema: DECISIONS_SCHEMA }, opts).length);
  assert.ok(validateImport(doc, { packetKeys: KEYS, packetSha: 'abc' }).length); // mini schema rejects checks
  const out = await exportDoc({ packetText: '{}', state: {}, schema: AUDIT_DECISIONS_SCHEMA });
  assert.equal(out.schema, AUDIT_DECISIONS_SCHEMA);
});

test('summarizeAudit keeps populations separate and computes strict agreement', () => {
  const mk = (key, runId, pop, code, checks) => ({
    key, run_id: runId, population: pop, driver_code: code, verifier: { checks },
  });
  const rec = [
    { postcondition_id: 'P1', satisfied: true },
    { postcondition_id: 'P2', satisfied: true },
    { postcondition_id: 'P3', satisfied: true },
  ];
  const packet = {
    episodes: [
      mk('a::1', 'a', 'pop-one', 'Driver A', rec),
      mk('b::1', 'b', 'pop-two', 'Driver B', rec),
      mk('b::2', 'b', 'pop-two', 'Driver B', rec),
    ],
  };
  const s = summarizeAudit(packet, {
    reviewer: 'ann',
    decisions: {
      'a::1': { ...auditGood, checks: { P1: true, P2: true, P3: true } },
      'b::1': { ...auditGood, checks: { P1: false, P2: true, P3: true } },
    },
  });
  assert.equal(s.recorded, 2);
  assert.equal(s.total, 3);
  assert.equal(s.complete, false);
  assert.deepEqual(s.populations.map((p) => p.label), ['pop-one', 'pop-two']);
  const one = s.populations[0].runs[0];
  const two = s.populations[1].runs[0];
  assert.equal(one.agrees, 1);
  assert.equal(two.disagrees, 1);
  assert.equal(two.recorded, 1);
  assert.equal(two.total, 2);
  assert.ok(!('agrees' in s) && !('disagrees' in s)); // never pooled at top level
});

test('storage keys keep the mini and audit queues apart', () => {
  const store = {};
  const storage = { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); } };
  saveState(storage, { reviewer: 'mini', decisions: {}, partials: {} });
  saveState(storage, { reviewer: 'audit', decisions: {}, partials: {} }, AUDIT_STORAGE_KEY);
  assert.equal(loadState(storage).reviewer, 'mini');
  assert.equal(loadState(storage, AUDIT_STORAGE_KEY).reviewer, 'audit');
});
