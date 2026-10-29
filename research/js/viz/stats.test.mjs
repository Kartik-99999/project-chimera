/* Node unit tests for the viz math kit. Run: node --test research/js/viz/ */
import test from 'node:test';
import assert from 'node:assert/strict';
import { wilson, wilsonUpper, percentile, sliceCells, sankeyLayout, niceStep, matchCellKey } from './stats.js';

test('wilson matches the evaluation §4.3 reference values', () => {
  assert.ok(Math.abs(wilson(0, 5).hi * 100 - 43.4) < 0.05);
  assert.ok(Math.abs(wilson(0, 50).hi * 100 - 7.1) < 0.05);
  assert.ok(Math.abs(wilson(0, 100).hi * 100 - 3.7) < 0.05);
  assert.equal(wilson(0, 5).lo, 0);
});

test('wilson is symmetric and null-safe', () => {
  const a = wilson(5, 5);
  const b = wilson(0, 5);
  assert.ok(Math.abs(a.lo - (1 - b.hi)) < 1e-12);
  assert.equal(wilson(0, 0), null);
  assert.equal(wilson(-1, 5), null);
  assert.equal(wilson(6, 5), null);
  assert.equal(wilsonUpper(3, 2), null);
});

test('percentile uses nearest-rank and ignores junk', () => {
  assert.equal(percentile([30, 10, 20], 50), 20);
  assert.equal(percentile([30, 10, 20], 95), 30);
  assert.equal(percentile([5], 50), 5);
  assert.equal(percentile([], 50), null);
  assert.equal(percentile([null, 10, NaN], 50), 10);
});

function fakeCell(scenario, n, trials = 2) {
  return { scenario_id: scenario, input_id: 'I-PLAIN', baseline: 'chimera', trials, fault_params: {} };
}
function fakeEp(scenario, trial) {
  return { trial_id: trial, scenario_id: scenario, input_id: 'I-PLAIN', baseline: 'chimera' };
}

test('sliceCells maps episodes positionally per cell', () => {
  const cells = [fakeCell('S-NORM'), fakeCell('S-SLOW')];
  const eps = [fakeEp('S-NORM', 't1'), fakeEp('S-NORM', 't2'), fakeEp('S-SLOW', 't3'), fakeEp('S-SLOW', 't4')];
  const out = sliceCells(cells, eps);
  assert.deepEqual(out[0].episodes.map((e) => e.trial_id), ['t1', 't2']);
  assert.deepEqual(out[1].episodes.map((e) => e.trial_id), ['t3', 't4']);
});

test('sliceCells skips warm-ups and fails closed on inconsistency', () => {
  const cells = [fakeCell('S-NORM')];
  const eps = [{ trial_id: 'warmup:1' }, fakeEp('S-NORM', 't1'), fakeEp('S-NORM', 't2')];
  assert.deepEqual(sliceCells(cells, eps)[0].episodes.map((e) => e.trial_id), ['t1', 't2']);
  const bad = [fakeEp('S-NORM', 't1'), fakeEp('S-SLOW', 't2')];
  assert.throws(() => sliceCells(cells, bad), /does not belong/);
  assert.throws(() => sliceCells(cells, [fakeEp('S-NORM', 't1')]), /sum to/);
});

test('sankeyLayout conserves flow and stacks links inside nodes', () => {
  const columns = [{ id: 'a' }, { id: 'b' }, { id: 'c' }];
  const flows = [
    { fromCol: 0, from: 'x', toCol: 1, to: 'y', value: 10 },
    { fromCol: 0, from: 'x', toCol: 1, to: 'z', value: 5 },
    { fromCol: 1, from: 'y', toCol: 2, to: 'w', value: 10 },
    { fromCol: 1, from: 'z', toCol: 2, to: 'w', value: 5 },
    { fromCol: 0, from: 'nil', toCol: 1, to: 'y', value: 0 },
  ];
  const { nodes, links } = sankeyLayout(columns, flows, { unit: 2, gap: 10, pad: 5 });
  assert.equal(links.length, 4, 'zero flows produce no links');
  const x = nodes.find((n) => n.id === 'x');
  assert.equal(x.out, 15);
  assert.equal(x.height, 30);
  for (const l of links) {
    assert.ok(l.y0 >= l.fromNode.y0 && l.y0 + l.height <= l.fromNode.y0 + l.fromNode.height + 1e-9);
    assert.ok(l.y1 >= l.toNode.y0 && l.y1 + l.height <= l.toNode.y0 + l.toNode.height + 1e-9);
  }
  const totalOut = nodes.filter((n) => n.col === 0).reduce((s, n) => s + n.out, 0);
  const totalIn = nodes.filter((n) => n.col === 2).reduce((s, n) => s + n.in, 0);
  assert.equal(totalOut, totalIn);
});

test('niceStep covers the max with round ticks', () => {
  assert.equal(niceStep(75), 20);
  assert.equal(niceStep(0), 1);
  for (const max of [3.7, 75, 0.4, 1000]) {
    const step = niceStep(max);
    assert.ok(step * 4 >= max, `step ${step} covers ${max}`);
    const norm = step / 10 ** Math.floor(Math.log10(step));
    assert.ok([1, 2, 2.5, 5, 10].some((m) => Math.abs(norm - m) < 1e-9));
  }
});

test('matchCellKey tolerates producer JSON differences, rejects mismatches', () => {
  const cell = { scenario_id: 'S-SLOW', input_id: 'I-PLAIN', fault_params: { disabled: false, slow_ms: 800 } };
  // Exact JS form, Python-spaced form, and reordered keys all match.
  assert.equal(matchCellKey(cell, 'S-SLOW|I-PLAIN|{"disabled":false,"slow_ms":800}'), true);
  assert.equal(matchCellKey(cell, 'S-SLOW|I-PLAIN|{"disabled": false, "slow_ms": 0}'.replace('0}', '800}')), true);
  assert.equal(matchCellKey(cell, 'S-SLOW|I-PLAIN|{"slow_ms":800,"disabled":false}'), true);
  // Wrong identity or faults never match; malformed keys fail closed.
  assert.equal(matchCellKey(cell, 'S-NORM|I-PLAIN|{"disabled":false,"slow_ms":800}'), false);
  assert.equal(matchCellKey(cell, 'S-SLOW|I-SPACE|{"disabled":false,"slow_ms":800}'), false);
  assert.equal(matchCellKey(cell, 'S-SLOW|I-PLAIN|{"disabled":false,"slow_ms":0}'), false);
  assert.equal(matchCellKey(cell, 'S-SLOW|I-PLAIN|not-json'), false);
  assert.equal(matchCellKey(cell, 'no-pipes-here'), false);
  assert.equal(matchCellKey(cell, ''), false);
  assert.equal(matchCellKey(cell, null), false);
});
