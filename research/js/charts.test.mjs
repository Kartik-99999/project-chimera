/* Shared chart-builder tests: dotPlot, heatmap, groupedBars, barCell.
 * Run: node --test research/js/charts.test.mjs (from repo root)
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { dotPlot, heatmap, groupedBars, barCell, constellation } from './charts.js';

test('dotPlot: estimates, Wilson whiskers, and explicit missing denominators', () => {
  const svg = dotPlot({ rows: [
    { label: 'A', k: 8, n: 10, color: '#39d0d8', tip: 'A: 8/10' },
    { label: 'B', k: 0, n: 0, color: '#a78bfa' },
  ] });
  assert.match(svg, /n=10/);
  assert.match(svg, /A: 8\/10/);
  assert.match(svg, /no denominator — unmeasurable/);
  // Whiskers are drawn for the measured row only (3 lines: bar + 2 caps).
  assert.equal(svg.split('stroke="#39d0d8"').length - 1, 3);
});

test('heatmap: observed rates as text, untested cells as em-dash', () => {
  const svg = heatmap({
    rows: ['R1'], cols: ['C1', 'C2'],
    cells: [{ row: 'R1', col: 'C1', k: 3, n: 5, href: '#/x' }],
  });
  assert.match(svg, /3\/5/);
  assert.match(svg, /no data/);
  assert.match(svg, />—</);
});

test('constellation: stable node/link/panel contract for the map workspace', () => {
  const model = {
    runs: [{ runId: 'dev-20261028-chimera', baseline: 'chimera', split: 'development',
      data: { cells: [{ scenario_id: 'S-SLOW' }], episodes: [{}, {}] } }],
    episodes: [{ scenario_id: 'S-SLOW', trial_id: 't1' }],
    auditNodes: [{ runId: 'dev-20261028-chimera', state: 'pending', label: '… dev·chimera', blurb: '0/9 cells' }],
  };
  const html = constellation({ compact: false }).render(model);
  assert.match(html, /data-node="hub"/);
  assert.match(html, /data-node="run:dev-20261028-chimera"/);
  assert.match(html, /data-node="sc:S-SLOW"/);
  assert.match(html, /data-node="audit:dev-20261028-chimera"/);
  assert.match(html, /data-link="hub run:dev-20261028-chimera"/);
  assert.match(html, /data-panel/);
  assert.match(html, /node-list/);
  // Orbit structure and radial labels: audits read left-to-right, scenarios centered.
  assert.match(html, /const-orbit/);
  assert.match(html, /text-anchor="start">… dev·chimera/);
  assert.match(html, /text-anchor="middle">S-SLOW/);
  // Links are curved paths carrying the same data-link contract.
  assert.match(html, /<path class="const-link" data-link="hub run:dev-20261028-chimera" d="M[^"]*Q[^"]*"/);
});

test('groupedBars and barCell label exact values', () => {
  const svg = groupedBars({ categories: ['c1'], series: [{ label: 's', values: [2], color: '#39d0d8' }] });
  assert.match(svg, /c1/);
  assert.match(barCell(5, 10, '5 ms'), /5 ms/);
  assert.match(barCell(null, 10, 'x'), /—/);
});
