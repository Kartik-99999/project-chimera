/* River render smoke test: exercises the real page module in Node
 * with repo evidence served from disk and app.js stubbed.
 * Run: node --test research/js/pages/river.render.test.mjs (repo root)
 */
import { test, before } from 'node:test';
import assert from 'node:assert/strict';
import { register } from 'node:module';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..', '..', '..');
register('./render-hooks.mjs', { parentURL: import.meta.url });

// Serve repo files for data.js fetch calls (paths are repo-root-relative).
globalThis.fetch = async (url) => {
  const rel = String(url).replace(/^\/+/, '');
  try {
    const body = readFileSync(join(root, rel), 'utf8');
    return {
      ok: true,
      json: async () => JSON.parse(body),
      text: async () => body,
    };
  } catch {
    return { ok: false, status: 404 };
  }
};

const { loadAll } = await import('../data.js');
const { pageRiver } = await import('./river.js');

function fakeEl() {
  return {
    innerHTML: '',
    querySelector: () => ({ addEventListener() {} }),
    querySelectorAll: () => [],
  };
}
const count = (html, cls) => html.split(`class="${cls}"`).length - 1;

before(async () => { await loadAll(); });

test('eval river renders 360 counted episodes with links, nodes, and list rows', async () => {
  const el = fakeEl();
  await pageRiver(el, { query: {} });
  assert.match(el.innerHTML, /360 measured episodes/);
  assert.match(el.innerHTML, /Provisional/);
  assert.doesNotMatch(el.innerHTML, /Cannot map episodes/);
  // 4 scenarios × 2 baselines + 2 × outcomes + outcomes × audit states.
  assert.ok(count(el.innerHTML, 'flow-link') >= 8 + 4);
  assert.equal(count(el.innerHTML, 'flow-node'), 4 + 2 + 2 + 1); // sc, base, outcome, audit
  // List alternative covers every link.
  const rows = el.innerHTML.split('<tr><td>').length - 1;
  assert.equal(rows, count(el.innerHTML, 'flow-link'));
  // Click-through targets keep their filter parameters.
  assert.match(el.innerHTML, /#\/atlas\?scenario=S-SLOW&baseline=chimera/);
  assert.match(el.innerHTML, /#\/audit/);
  // Every stage header carries its honest column total; links expose identity.
  assert.equal(count(el.innerHTML, 'river-col-total'), 4);
  assert.match(el.innerHTML, /Σ 360/);
  assert.match(el.innerHTML, /data-from="S-SLOW" data-to-col="1" data-to="chimera"/);
});

test('dev river renders 160 episodes across audited cells', async () => {
  const el = fakeEl();
  await pageRiver(el, { query: { split: 'development' } });
  assert.match(el.innerHTML, /160 measured episodes/);
  assert.match(el.innerHTML, /cell audited/);
  assert.doesNotMatch(el.innerHTML, /cell pending/);
});

test('app-stub link() matches the real implementation textually', () => {
  const real = readFileSync(join(here, '..', 'app.js'), 'utf8');
  const stub = readFileSync(join(here, 'app-stub.mjs'), 'utf8');
  const body = (src) => src.slice(src.indexOf('export function link'), src.indexOf('}\n', src.indexOf('export function link')));
  assert.equal(body(stub).replace('export function link', 'function link'), body(real).replace('export function link', 'function link'));
});
