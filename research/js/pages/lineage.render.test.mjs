/* Provenance graph render tests (Node, no browser).
 * Run: node --test research/js/pages/lineage.render.test.mjs (repo root)
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

const { loadAll } = await import('../data.js');
const { pageLineage } = await import('./lineage.js');

function pageEl(values = {}) {
  return fakeEl({
    '#l-run': { value: values.run || 'eval-20261028-chimera', addEventListener() {} },
    '#l-cell': { value: values.cell || '', addEventListener() {} },
    '#l-q': { value: values.q || '', addEventListener() {} },
  });
}
const count = (html, s) => html.split(s).length - 1;

before(async () => { await loadAll(); });

test('default cell graph: validated joins, tables mirror the svg', async () => {
  const el = pageEl();
  await pageLineage(el, { query: {} });
  assert.match(el.innerHTML, /Provenance Graph/);
  assert.match(el.innerHTML, /eval-20261028-chimera/);
  assert.match(el.innerHTML, /Held-out evaluation report/);
  assert.match(el.innerHTML, /full audit plan/);
  assert.match(el.innerHTML, /mini audit plan/);
  // Tables list exactly the rendered nodes and edges.
  assert.equal(count(el.innerHTML, '<tr><td>Manifest</td>'), 1);
  const svgNodes = count(el.innerHTML, 'class="lineage-node');
  const tableNodes = count(el.innerHTML, '<tr><td>Manifest</td>') + count(el.innerHTML, '<tr><td>Run</td>')
    + count(el.innerHTML, '<tr><td>Cell</td>') + count(el.innerHTML, '<tr><td>Episodes</td>')
    + count(el.innerHTML, '<tr><td>Artifacts</td>') + count(el.innerHTML, '<tr><td>Verdicts</td>')
    + count(el.innerHTML, '<tr><td>Plans &amp; reports</td>');
  assert.equal(tableNodes, svgNodes);
  assert.ok(svgNodes > 15);
  assert.equal(count(el.innerHTML, '<tr><td class="mono"'), count(el.innerHTML, 'class="lineage-edge'));
  // Eval is unaudited: disclosed, not an error.
  assert.doesNotMatch(el.innerHTML, /banner bad/);
  assert.match(el.innerHTML, /zero verdicts|not sampled/);
});

test('dev run shows the audited node joined by run_id', async () => {
  const el = pageEl({ run: 'dev-20261028-chimera' });
  await pageLineage(el, { query: { run: 'dev-20261028-chimera' } });
  assert.match(el.innerHTML, /audited/);
  assert.match(el.innerHTML, /same run_id, verdicts applied/);
});

test('node selection renders identifiers and search dims the rest', async () => {
  const el = pageEl();
  await pageLineage(el, { query: { node: 'run' } });
  assert.match(el.innerHTML, /Node detail/);
  assert.match(el.innerHTML, /Audited file/);
  assert.match(el.innerHTML, /Open record/);

  const el2 = pageEl({ q: 'trial-0001' });
  await pageLineage(el2, { query: { q: 'trial-0001' } });
  assert.match(el2.innerHTML, /dimmed/);
});

test('missing run keeps the unavailable path', async () => {
  const el = pageEl({ run: 'no-such-run' });
  await pageLineage(el, { query: { run: 'no-such-run' } });
  assert.match(el.innerHTML, /Run evidence missing/);
});
