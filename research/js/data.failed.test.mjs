/* data.js boot tests: persistent failures still degrade visibly.
 * Run: node --test research/js/data.failed.test.mjs (from repo root)
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const root = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const DEAD = 'artifacts/dev-20261028/report.md';

// One file always fails; everything else serves normally.
globalThis.fetch = async (url) => {
  const rel = String(url).replace(/^\/+/, '');
  if (rel === DEAD) throw new Error('persistent outage');
  try {
    const body = readFileSync(join(root, rel), 'utf8');
    return { ok: true, json: async () => JSON.parse(body), text: async () => body };
  } catch {
    return { ok: false, status: 404 };
  }
};

const { loadAll } = await import('./data.js');

test('loadAll records persistent failures after retrying', async () => {
  const s = await loadAll();
  assert.deepEqual(s.failed, [DEAD]);
  assert.equal(s.reports.size, 2);
  assert.equal(s.runs.size, 4);
});
