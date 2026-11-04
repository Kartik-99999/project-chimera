/* Failure topography render + chart tests (Node, no browser).
 * Run: node --test research/js/pages/failures.render.test.mjs (repo root)
 */
import { test, before } from 'node:test';
import assert from 'node:assert/strict';
import { register } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { installFetch, fakeEl, fakeHost, countClass } from './test-setup.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..', '..', '..');
register('./render-hooks.mjs', { parentURL: import.meta.url });
installFetch(root);

const { loadAll } = await import('../data.js');
const { pageFailures } = await import('./failures.js');
const { faultTransect } = await import('../charts.js');

before(async () => { await loadAll(); });

function pageEl() {
  return fakeEl({ '#f-split': { addEventListener() {} }, '#fail-table': fakeHost() });
}

test('eval failures page renders 24 soundings with table alternative', async () => {
  const el = pageEl();
  await pageFailures(el, { query: {} });
  assert.match(el.innerHTML, /24 soundings/);
  assert.equal(countClass(el.innerHTML, 'sounding'), 24);
  assert.doesNotMatch(el.innerHTML, /Topography unavailable/);
  // Every sounding has a table row with exact denominators.
  assert.equal(el.innerHTML.split('<tr><td class="mono">S-').length - 1, 24);
  assert.match(el.innerHTML, /#\/atlas\?scenario=S-SLOW&baseline=chimera/);
  assert.match(el.innerHTML, /cannot filter by fault level/);
});

test('dev failures page renders 8 soundings over slow 0 and 2000', async () => {
  const el = pageEl();
  await pageFailures(el, { query: { split: 'development' } });
  assert.match(el.innerHTML, /8 soundings/);
  assert.equal(countClass(el.innerHTML, 'sounding'), 8);
});

test('faultTransect: untested rows, split markers, unverified rings', () => {
  const svg = faultTransect({
    rows: [{ scenario: 'S-X', baseline: 'chimera' }, { scenario: 'S-Y', baseline: 'chimera' }],
    levels: [0, 100],
    soundings: [
      { scenario: 'S-X', baseline: 'chimera', slow: 100, disabled: false, k: 2, n: 5, unverified: true, href: '#/x', tip: 'split' },
      { scenario: 'S-X', baseline: 'chimera', slow: 0, disabled: true, k: 0, n: 5, href: '#/y' },
    ],
  });
  assert.match(svg, /— untested/); // S-Y has no soundings
  assert.match(svg, /2\/5/); // exact k/n text, not color alone
  assert.match(svg, /stroke-dasharray/); // unverified ring
  assert.match(svg, /<rect[^>]*width="15"/); // disabled square marker
  assert.match(svg, /A 8 8/); // split half-disc arc
  assert.equal(svg.split('>n=5<').length - 1, 2); // per-level denominators
});
