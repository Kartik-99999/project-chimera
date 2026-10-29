/* Lineage model tests: real runs/plans/reports + tamper cases.
 * Run: node --test research/js/viz/lineageModel.test.mjs (from repo root)
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { buildLineage, checksAgree, cellKeyOf, sibArtifact } from './lineageModel.js';

const root = join(dirname(fileURLToPath(import.meta.url)), '..', '..', '..');
const load = (p) => JSON.parse(readFileSync(join(root, p), 'utf8'));
const loadText = (p) => readFileSync(join(root, p), 'utf8');

function presenceFor(runData) {
  const presence = {};
  for (const e of runData.episodes || []) {
    if (!e.trace_artifact) continue;
    for (const s of ['', '.snapshot.json', '.actions.json']) {
      const p = s === '' ? e.trace_artifact : sibArtifact(e.trace_artifact, s);
      presence[p] = existsSync(join(root, p));
    }
  }
  return presence;
}

function evalCase() {
  const data = load('artifacts/eval-20261028/run-chimera.json');
  return {
    manifest: load('benchmarks/manifests/eval-v1.json'),
    manifestPath: 'benchmarks/manifests/eval-v1.json',
    run: { runId: 'eval-20261028-chimera', baseline: 'chimera', split: 'evaluation', data },
    auditedData: null,
    plans: [
      { kind: 'full', data: load('artifacts/eval-20261028/run-chimera.audit-plan.json') },
      { kind: 'mini', data: load('artifacts/eval-20261028/run-chimera.audit-plan-mini.json') },
    ],
    reports: [{ id: 'eval', title: 'Held-out evaluation report', text: loadText('artifacts/eval-20261028/report.md') }],
    cellKey: cellKeyOf(data.cells[0]),
    presence: presenceFor(data),
  };
}

test('eval cell: every edge validated, report cited, nothing invented', () => {
  const { nodes, edges, issues } = buildLineage(evalCase());
  const kinds = nodes.map((n) => n.kind);
  assert.equal(kinds.filter((k) => k === 'episode').length, 5);
  assert.equal(kinds.filter((k) => k === 'artifacts').length, 5);
  assert.ok(nodes.some((n) => n.kind === 'report'));
  assert.ok(nodes.some((n) => n.kind === 'plan' && n.id === 'plan:mini'));
  assert.ok(!nodes.some((n) => n.kind === 'audited'));
  const bad = edges.filter((e) => !e.valid);
  assert.deepEqual(bad, []);
  const errors = issues.filter((i) => i.severity === 'error');
  assert.deepEqual(errors, []);
  // Deliberately limited audit: sampled-but-unadjudicated is disclosed.
  assert.ok(issues.some((i) => /zero verdicts|not sampled/.test(i.text)));
});

test('dev audited cell: audited node joins by run_id, verdict paths agree', () => {
  const data = load('artifacts/dev-20261028/run-chimera.json');
  const { nodes, edges, issues } = buildLineage({
    manifest: load('benchmarks/manifests/dev-v1.json'),
    manifestPath: 'benchmarks/manifests/dev-v1.json',
    run: { runId: 'dev-20261028-chimera', baseline: 'chimera', split: 'development', data },
    auditedData: load('artifacts/dev-20261028/run-chimera.audited.json'),
    plans: [{ kind: 'full', data: load('artifacts/dev-20261028/run-chimera.audit-plan.json') }],
    reports: [
      { id: 'dev', title: 'Development report', text: loadText('artifacts/dev-20261028/report.md') },
      { id: 'eval', title: 'Held-out evaluation report', text: loadText('artifacts/eval-20261028/report.md') },
    ],
    cellKey: cellKeyOf(data.cells[0]),
    presence: presenceFor(data),
  });
  assert.ok(nodes.some((n) => n.kind === 'audited'));
  const auditEdge = edges.find((e) => e.from === 'run' && e.to === 'audited');
  assert.equal(auditEdge.valid, true);
  // The eval report does not cite this dev run: no edge is drawn.
  assert.ok(!nodes.some((n) => n.id === 'rep:eval'));
  assert.ok(nodes.some((n) => n.id === 'rep:dev'));
  // Verdicts recorded; plan trace paths match episode records.
  const verdicts = nodes.filter((n) => n.kind === 'verdict');
  assert.ok(verdicts.length > 0);
  assert.ok(verdicts.every((v) => !v.missing));
  assert.ok(!issues.some((i) => /trace_path differs/.test(i.text)));
});

test('missing artifacts and mismatched plans fail visibly, not silently', () => {
  const base = evalCase();
  const noFiles = buildLineage({ ...base, presence: {} });
  assert.ok(noFiles.edges.filter((e) => !e.valid).length >= 5);
  assert.ok(noFiles.issues.some((i) => /missing trace/.test(i.text)));

  const tampered = structuredClone(base.plans[0].data);
  tampered.run_id = 'some-other-run';
  const bad = buildLineage({ ...base, plans: [{ kind: 'full', data: tampered }] });
  const pe = bad.edges.find((e) => e.from === 'run' && e.to === 'plan:full');
  assert.equal(pe.valid, false);
  assert.ok(bad.issues.some((i) => /does not match run/.test(i.text)));

  assert.throws(() => buildLineage({ ...base, cellKey: 'NOPE|X|{}' }), /not present in run/);
});

test('checksAgree: agreement, disagreement, unauditable', () => {
  const ver = { checks: [{ postcondition_id: 'P1', satisfied: true }, { postcondition_id: 'P2', satisfied: false }] };
  assert.equal(checksAgree({ checks: { P1: true, P2: false } }, ver), true);
  assert.equal(checksAgree({ checks: { P1: true, P2: true } }, ver), false);
  assert.equal(checksAgree({ verdict: 'unauditable', reason: 'x' }, ver), null);
  assert.equal(checksAgree(null, ver), null);
  assert.equal(checksAgree({ checks: { P1: true } }, ver), false); // partial verdicts never agree
});
