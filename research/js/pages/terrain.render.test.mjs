/* Terrain render tests (Node, no browser).
 * Run: node --test research/js/pages/terrain.render.test.mjs (repo root)
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

const { loadAll, getRun } = await import('../data.js');
const { pageTerrain } = await import('./terrain.js');
const { sliceCells } = await import('../viz/stats.js');

function pageEl() {
  return fakeEl({
    '#t-split': { value: 'evaluation', addEventListener() {} },
    '#t-baseline': { value: 'chimera', addEventListener() {} },
    '#t-scenario': { value: '', addEventListener() {} },
    '#t-outcome': { value: '', addEventListener() {} },
    '#terrain-detail': { scrollIntoView() {} },
  });
}
const count = (html, s) => html.split(s).length - 1;

before(async () => { await loadAll(); });

test('eval terrain: 36 cells, 180 trials, provisional banner', async () => {
  const el = pageEl();
  await pageTerrain(el, { query: {} });
  assert.match(el.innerHTML, /Provisional/);
  assert.match(el.innerHTML, /<strong>36<\/strong> cells · <strong>180<\/strong> trials/);
  assert.equal(count(el.innerHTML, 'class="terrain-cell'), 36);
  assert.match(el.innerHTML, /dashed edge = verification unavailable/);
});

test('dev terrain: 16 cells; scenario filter narrows honestly', async () => {
  const el = pageEl();
  await pageTerrain(el, { query: { split: 'development' } });
  assert.match(el.innerHTML, /<strong>16<\/strong> cells · <strong>80<\/strong> trials/);

  const el2 = pageEl();
  await pageTerrain(el2, { query: { scenario: 'S-SLOW' } });
  assert.match(el2.innerHTML, /<strong>15<\/strong> cells · <strong>75<\/strong> trials/);
});

test('cell inspection shows trials, mirror baseline, and atlas link', async () => {
  const run = getRun('eval-20261028-chimera');
  const { cell } = sliceCells(run.data.cells, run.data.episodes)[0];
  const key = `${cell.scenario_id}|${cell.input_id}|${JSON.stringify(cell.fault_params || {})}`;
  const el = pageEl();
  await pageTerrain(el, { query: { cell: key } });
  assert.match(el.innerHTML, /Cell inspection/);
  assert.match(el.innerHTML, /mirror baseline/);
  assert.match(el.innerHTML, /All cell episodes in the Atlas/);
  // 5 trial rows link to the evidence inspector.
  const detail = el.innerHTML.slice(el.innerHTML.indexOf('Cell inspection'));
  assert.equal(count(detail, '#/evidence/'), 5);
});

test('outcome highlight dims non-matching trials without hiding counts', async () => {
  const el = pageEl();
  await pageTerrain(el, { query: { outcome: 'failed' } });
  assert.match(el.innerHTML, /opacity="0.18"/);
  assert.match(el.innerHTML, /<strong>36<\/strong> cells/);
});

test('scenario bands group tiles in run order; mirror cell is inspectable', async () => {
  const el = pageEl();
  await pageTerrain(el, { query: {} });
  assert.equal(count(el.innerHTML, '<section class="terrain-group"'), 4);
  assert.match(el.innerHTML, /manifest expects succeeded/);
  assert.match(el.innerHTML, /cells · <strong>\d+\/\d+<\/strong> succeeded/);

  const run = getRun('eval-20261028-chimera');
  const { cell } = sliceCells(run.data.cells, run.data.episodes)[0];
  const key = `${cell.scenario_id}|${cell.input_id}|${JSON.stringify(cell.fault_params || {})}`;
  const el2 = pageEl();
  await pageTerrain(el2, { query: { cell: key } });
  assert.match(el2.innerHTML, /terrain-cell anim-in sel/);
  assert.match(el2.innerHTML, /mirror-strip/);
  assert.match(el2.innerHTML, /Open mirror cell →/);
});
