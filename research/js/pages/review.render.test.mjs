/* Mini-review render tests (Node, no browser).
 * Run: node --test research/js/pages/review.render.test.mjs (repo root)
 */
import { test, before } from 'node:test';
import assert from 'node:assert/strict';
import { register } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { installFetch, fakeEl } from './test-setup.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..', '..', '..');
register('./render-hooks.mjs', { parentURL: import.meta.url });
installFetch(root);

const { pageReview } = await import('./review.js');

function memStorage(seed = {}) {
  const data = { ...seed };
  return {
    getItem: (k) => (k in data ? data[k] : null),
    setItem: (k, v) => { data[k] = String(v); },
  };
}

function pageEl() {
  return fakeEl({
    '#rv-name': { value: '', addEventListener() {} },
    '#rv-export': { addEventListener() {} },
    '#rv-import': { addEventListener() {} },
    '#trace-search': { value: '', addEventListener() {} },
  });
}
const count = (html, s) => html.split(s).length - 1;

before(() => {
  globalThis.localStorage = memStorage();
});

test('queue renders 8 pending episodes with masked summary', async () => {
  globalThis.localStorage = memStorage();
  const el = pageEl();
  await pageReview(el, { params: [], query: {} });
  assert.match(el.innerHTML, /Mini-review queue/);
  assert.equal(count(el.innerHTML, 'Episode '), 8);
  assert.match(el.innerHTML, /<strong>0\/8<\/strong> reviewed/);
  assert.match(el.innerHTML, /IN PROGRESS/);
  // Recorded columns stay masked until each episode is revealed.
  assert.ok(count(el.innerHTML, 'class="mask"') >= 8);
  assert.match(el.innerHTML, /Export decisions\.json/);
  assert.match(el.innerHTML, /support no reliability claim/);
});

test('chimera item masks the recorded verdict but shows live evidence', async () => {
  globalThis.localStorage = memStorage();
  const el = pageEl();
  await pageReview(el, { params: ['eval-20261028-chimera', 'trial-0006'], query: {} });
  assert.match(el.innerHTML, /data-testid="recorded-masked"/);
  assert.doesNotMatch(el.innerHTML, /data-testid="recorded-values"/);
  assert.match(el.innerHTML, /Trace timeline/);
  assert.match(el.innerHTML, /confirmation_visible/);
  assert.match(el.innerHTML, /Step 1 of 2 — blinded assessment/);
  // Reveal is gated: no reveal button exists before assessment is saved.
  assert.doesNotMatch(el.innerHTML, /rv-reveal/);
  assert.match(el.innerHTML, /Reveal unlocks after you record your assessment/);
  assert.match(el.innerHTML, /Padded Name/); // expected name is review input, not verdict
});

test('baseline-a item renders replay steps with honest coordinates note', async () => {
  globalThis.localStorage = memStorage();
  const el = pageEl();
  await pageReview(el, { params: ['eval-20261028-baseline-a', 'trial-0009'], query: {} });
  assert.match(el.innerHTML, /Replay steps/);
  assert.match(el.innerHTML, /data-testid="recorded-masked"/);
});

test('recorded decisions surface status, detail, and summary rows', async () => {
  const decision = {
    assessment: 'verified-success', agreement: 'agrees', sufficiency: 'sufficient',
    reason: 'snapshot shows exactly the expected name', missing_evidence: '',
    blinded: true, assessed_at: '2026-10-29T10:00:00.000Z',
    revealed_at: '2026-10-29T10:05:00.000Z', corrections: [],
  };
  globalThis.localStorage = memStorage({
    'chimera-mini-review:v1': JSON.stringify({
      reviewer: 'ann',
      decisions: { 'eval-20261028-chimera::trial-0006': decision },
      partials: {},
    }),
  });
  const el = pageEl();
  await pageReview(el, { params: [], query: {} });
  assert.match(el.innerHTML, /<strong>1\/8<\/strong> reviewed/);
  assert.match(el.innerHTML, /verified success/);
  // Revealed row shows recorded values; the other 7 stay masked.
  assert.ok(count(el.innerHTML, 'class="mask"') >= 7);
  const item = pageEl();
  await pageReview(item, { params: ['eval-20261028-chimera', 'trial-0006'], query: {} });
  assert.match(item.innerHTML, /Recorded decision/);
  assert.match(item.innerHTML, /data-testid="recorded-values"/);
  assert.match(item.innerHTML, /Revise decision/);
});

test('recorded assessment unlocks reveal and the agreement step', async () => {
  globalThis.localStorage = memStorage({
    'chimera-mini-review:v1': JSON.stringify({
      reviewer: 'ann',
      decisions: {},
      partials: {
        'eval-20261028-chimera::trial-0006': {
          assessment: 'verified-success', sufficiency: 'sufficient',
          reason: 'snapshot matches', missing_evidence: '',
          assessed_at: '2026-10-29T10:00:00.000Z', revealed_at: null,
        },
      },
    }),
  });
  const el = pageEl();
  await pageReview(el, { params: ['eval-20261028-chimera', 'trial-0006'], query: {} });
  assert.match(el.innerHTML, /Step 2 of 2 — judge agreement/);
  assert.match(el.innerHTML, /id="rv-reveal2"/);
  assert.match(el.innerHTML, /data-testid="recorded-masked"/);
});

test('episodes outside the frozen 8 are refused', async () => {
  globalThis.localStorage = memStorage();
  const el = pageEl();
  await pageReview(el, { params: ['eval-20261028-chimera', 'trial-0001'], query: {} });
  assert.match(el.innerHTML, /not in the packet/);
});
