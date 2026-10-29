/* Shared chart-builder tests: dotPlot, heatmap, groupedBars, barCell.
 * Run: node --test research/js/charts.test.mjs (from repo root)
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { dotPlot, heatmap, groupedBars, barCell } from './charts.js';

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

test('groupedBars and barCell label exact values', () => {
  const svg = groupedBars({ categories: ['c1'], series: [{ label: 's', values: [2], color: '#39d0d8' }] });
  assert.match(svg, /c1/);
  assert.match(barCell(5, 10, '5 ms'), /5 ms/);
  assert.match(barCell(null, 10, 'x'), /—/);
});
