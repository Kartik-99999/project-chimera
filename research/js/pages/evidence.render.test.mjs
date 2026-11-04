/* Oscilloscope render + strip tests (Node, no browser).
 * Run: node --test research/js/pages/evidence.render.test.mjs (repo root)
 */
import { test, before } from 'node:test';
import assert from 'node:assert/strict';
import { register } from 'node:module';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { installFetch, fakeEl, countClass } from './test-setup.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..', '..', '..');
register('./render-hooks.mjs', { parentURL: import.meta.url });
installFetch(root);

const { loadAll, getRun } = await import('../data.js');
const { pageEvidence } = await import('./evidence.js');
const { scopeStrip } = await import('../charts.js');

function cardHost(store) {
  return {
    set innerHTML(v) { store.html = v; },
    get innerHTML() { return store.html || ''; },
    querySelector: () => ({ addEventListener() {}, value: '', dataset: {} }),
    querySelectorAll: () => [],
  };
}

async function renderEvidence(runId, trialId) {
  const stores = {};
  const el = fakeEl({
    '#ev-trace': cardHost(stores.trace ??= {}),
    '#ev-snapshot': cardHost(stores.snap ??= {}),
    '#ev-actions': cardHost(stores.act ??= {}),
    '#ev-scope': cardHost(stores.scope ??= {}),
  });
  await pageEvidence(el, { params: [runId, trialId] });
  return { el, stores };
}

const load = (p) => JSON.parse(readFileSync(join(root, p), 'utf8'));

before(async () => { await loadAll(); });

test('chimera episode renders one mark per recorded event, record, and verdict', async () => {
  const { stores } = await renderEvidence('eval-20261028-chimera', 'trial-0001');
  const html = stores.scope.html;
  assert.match(html, /Episode oscilloscope/);
  assert.match(html, /Trace events/);
  assert.match(html, /Observed actions/);
  assert.match(html, /Verdicts &amp; snapshot/);
  assert.match(html, /ms from recorded timestamps/);
  assert.match(html, /data-zoom="in"/);
  const ep = getRun('eval-20261028-chimera').data.episodes.find((e) => e.trial_id === 'trial-0001');
  const trace = load(ep.trace_artifact);
  const i = ep.trace_artifact.lastIndexOf('/');
  const actions = load(`${ep.trace_artifact.slice(0, i + 1)}${ep.trace_artifact.slice(i + 1).split('.')[0]}.actions.json`);
  const expected = trace.events.length + actions.records.length
    + (ep.verification.checks || []).length + 1; // + snapshot slot (no human verdicts on eval)
  assert.equal(countClass(html, 'scope-event'), expected);
});

test('baseline-a episode renders replay lane with honest coordinates', async () => {
  const { stores } = await renderEvidence('eval-20261028-baseline-a', 'trial-0001');
  assert.match(stores.scope.html, /Replay steps/);
  assert.match(stores.scope.html, /no recorded sequence numbers/);
});

test('missing episode keeps the not-found path', async () => {
  const { el } = await renderEvidence('no-such-run', 'trial-0001');
  assert.match(el.innerHTML, /Episode not found/);
});

test('scopeStrip: zoom changes pixel width; empty lanes stay explicit', () => {
  const lanes = [
    { id: 'trace', title: 'Trace', coord: 'seq', marks: [{ x: 2, xLabel: '2', kind: 'ok', title: 'second' }] },
    { id: 'verdicts', title: 'Verdicts', coord: 'categorical slots (not sequential)', marks: [] },
  ];
  const narrow = scopeStrip({ lanes, pxPerStep: 24 });
  const wide = scopeStrip({ lanes, pxPerStep: 96 });
  assert.ok(wide.width > narrow.width);
  assert.match(narrow.svg, /no marks recorded/);
  assert.match(narrow.svg, /categorical slots/);
  assert.equal(countClass(narrow.svg, 'scope-event'), 1);
  assert.match(narrow.svg, /Trace <tspan[^>]*>\(1\)<\/tspan>/);
  assert.match(narrow.svg, /Verdicts <tspan[^>]*>\(0\)<\/tspan>/);
});
