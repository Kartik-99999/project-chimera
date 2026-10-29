/* data.js boot tests: transient fetch failures are retried.
 * Run: node --test research/js/data.test.mjs (from repo root)
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const root = join(dirname(fileURLToPath(import.meta.url)), '..', '..');

// Fail the FIRST request for the eval report only, then behave.
let failuresLeft = 1;
globalThis.fetch = async (url) => {
  const rel = String(url).replace(/^\/+/, '');
  if (rel === 'artifacts/eval-20261028/report.md' && failuresLeft > 0) {
    failuresLeft -= 1;
    throw new Error('transient connection drop');
  }
  try {
    const body = readFileSync(join(root, rel), 'utf8');
    return { ok: true, json: async () => JSON.parse(body), text: async () => body };
  } catch {
    return { ok: false, status: 404 };
  }
};

const { loadAll } = await import('./data.js');

test('loadAll retries a transient fetch failure instead of degrading', async () => {
  const s = await loadAll();
  assert.equal(failuresLeft, 0);
  assert.deepEqual(s.failed, []);
  assert.equal(s.reports.size, 3);
  assert.equal(s.runs.size, 4);
});
