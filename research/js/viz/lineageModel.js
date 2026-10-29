/* Provenance Graph data model (DOM-free; unit-tested).
 * Builds a validated lineage graph for one run cell:
 * manifest → run (→ audited) → cell → episodes → artifacts, with
 * verdict, plan, and report nodes joined by recorded identifiers.
 * Every edge is validated against those identifiers; mismatches and
 * missing files become explicit invalid edges / missing nodes, and
 * uncited reports are omitted rather than linked by convention.
 * hrefs are route descriptors {route, params, query}; the page turns
 * them into links.
 */
import { sliceCells } from './stats.js';
import { isHarnessError } from '../data.js';

export function sibArtifact(tracePath, suffix) {
  if (!tracePath) return null;
  const i = tracePath.lastIndexOf('/');
  const dir = i >= 0 ? tracePath.slice(0, i + 1) : '';
  const base = (i >= 0 ? tracePath.slice(i + 1) : tracePath).split('.')[0];
  return `${dir}${base}${suffix}`;
}

/* Human-vs-verifier agreement: true/false, or null when unauditable
 * or uncomputable. Shared with the Evidence page. */
export function checksAgree(verdict, verification) {
  if (!verdict || verdict.verdict === 'unauditable' || !verdict.checks) return null;
  const vc = (verification && verification.checks || [])
    .reduce((m, c) => ({ ...m, [c.postcondition_id]: c.satisfied }), {});
  const keys = Object.keys(verdict.checks);
  if (!keys.length || !Object.keys(vc).length) return null;
  return keys.every((k) => verdict.checks[k] === vc[k]) && keys.length === Object.keys(vc).length;
}

export function cellKeyOf(cell) {
  return `${cell.scenario_id}|${cell.input_id}|${JSON.stringify(cell.fault_params || {})}`;
}

function faultLabel(cell) {
  const f = cell.fault_params || {};
  const slow = Number(f.slow_ms ?? 0);
  const dis = f.disabled === true;
  if (slow > 0 && dis) return `slow=${slow} +disabled`;
  if (slow > 0) return `slow=${slow}`;
  if (dis) return 'disabled';
  return 'no fault';
}

/* plans: [{kind, data}], reports: [{id, title, text}],
 * presence: {artifactPath: bool}. Throws (fail closed) when the
 * cell cannot be mapped positionally. */
export function buildLineage({ manifest, manifestPath, run, auditedData, plans, reports, cellKey, presence = {} }) {
  const nodes = [];
  const edges = [];
  const issues = [];
  const N = (n) => { nodes.push(n); return n.id; };
  const E = (from, to, label, valid = true) => edges.push({ from, to, label, valid });

  const sliced = sliceCells(run.data.cells || [], run.data.episodes || []);
  const found = sliced.find(({ cell }) => cellKeyOf(cell) === cellKey);
  if (!found) throw new Error(`cell ${cellKey} not present in run ${run.runId}`);
  const { cell, episodes } = found;

  const sha = run.data.manifest_sha256 || '';
  N({
    id: 'manifest', layer: 0, kind: 'manifest', label: manifest ? manifest.manifest_id : '(manifest missing)',
    sub: manifest ? `${manifestPath}` : 'file did not load', missing: !manifest,
    meta: [['Manifest file', manifestPath], ['Run records sha', sha ? `${sha.slice(0, 12)}…` : '—'],
      ['Benchmark', manifest ? `${manifest.benchmark_id || '?'} v${manifest.benchmark_version || '?'}` : '—']],
    href: { route: 'audit', params: [], query: {} },
  });
  const measured = (run.data.episodes || []).filter((e) => !String(e.trial_id || '').startsWith('warmup:')).length;
  N({
    id: 'run', layer: 1, kind: 'run', label: run.runId,
    sub: `${(run.data.cells || []).length} cells · ${measured} measured (warm-ups excluded)`,
    meta: [['Baseline', run.baseline], ['Split', run.split], ['Manifest', `${run.data.manifest_id || '?'} v${run.data.manifest_version || '?'}`],
      ['Status', run.data.status || '?'], ['Audited file', auditedData ? 'present' : 'absent']],
    href: { route: 'atlas', params: [], query: { run: run.runId } },
  });
  E('manifest', 'run', manifest && manifest.manifest_id === run.data.manifest_id
    ? `manifest_id ${run.data.manifest_id} matches` : 'manifest_id MISMATCH',
  Boolean(manifest && manifest.manifest_id === run.data.manifest_id));
  if (!manifest || manifest.manifest_id !== run.data.manifest_id) {
    issues.push({ severity: 'error', text: `Run ${run.runId} names manifest ${run.data.manifest_id} but the loaded manifest differs or is missing.` });
  }

  if (auditedData) {
    const same = auditedData.run_id === run.runId;
    N({
      id: 'audited', layer: 1, kind: 'audited', label: `${run.runId} · audited`,
      sub: `${(auditedData.cells || []).filter((c) => c.verifier_audit).length}/${(auditedData.cells || []).length} cells carry audits`,
      meta: [['run_id', auditedData.run_id || '—']],
      href: { route: 'audit', params: [], query: {} },
    });
    E('run', 'audited', same ? 'same run_id, verdicts applied' : 'run_id MISMATCH', same);
    if (!same) issues.push({ severity: 'error', text: 'Audited file run_id does not match the raw run.' });
  }

  const k = episodes.filter((e) => e.outcome === 'succeeded').length;
  const va = cell.verifier_audit;
  N({
    id: 'cell', layer: 2, kind: 'cell', label: `${cell.scenario_id} · ${cell.input_id}`,
    sub: `${faultLabel(cell)} · ${k}/${episodes.length} succeeded`,
    meta: [['Fault params', JSON.stringify(cell.fault_params || {})], ['Trials', String(cell.trials)],
      ['Verifier audit', va ? `sampled ${va.sampled}, agreed ${va.agreed}` : 'none recorded']],
    href: { route: 'terrain', params: [], query: { split: run.split, baseline: run.baseline, cell: cellKey } },
  });
  E('run', 'cell', 'positional slice (audit rule)', true);

  // Index plan samples + verdicts by trial for exact joins.
  const sampledByTrial = new Map(); // trial -> [{planKind, entry}]
  const verdictsByTrial = new Map(); // trial -> [{planKind, verdict}]
  let planSampled = 0, planVerdicts = 0;
  for (const p of plans) {
    for (const [ckey, pc] of Object.entries((p.data && p.data.cells) || {})) {
      for (const s of pc.sampled || []) {
        planSampled += 1;
        if (!sampledByTrial.has(s.trial_id)) sampledByTrial.set(s.trial_id, []);
        sampledByTrial.get(s.trial_id).push({ planKind: p.kind, cellKey: ckey, entry: s });
      }
      for (const [t, v] of Object.entries(pc.verdicts || {})) {
        planVerdicts += 1;
        if (!verdictsByTrial.has(t)) verdictsByTrial.set(t, []);
        verdictsByTrial.get(t).push({ planKind: p.kind, verdict: v });
      }
    }
  }

  episodes.forEach((ep, i) => {
    const eid = `ep:${ep.trial_id}`;
    const tags = [];
    if (isHarnessError(ep)) tags.push('harness error');
    if (!ep.verification || ep.verification.status !== 'verified') tags.push('verification unavailable');
    const sampled = sampledByTrial.has(ep.trial_id);
    if (!sampled) tags.push('not sampled in any plan');
    N({
      id: eid, layer: 3, kind: 'episode', label: ep.trial_id,
      sub: `${ep.outcome}${tags.length ? ` · ${tags.join(', ')}` : ''}`,
      meta: [['Outcome', ep.outcome], ['Agent said', ep.agent_terminal_status || '—'],
        ['Error', ep.error || 'none'], ['Trace artifact', ep.trace_artifact || 'none recorded']],
      href: { route: 'evidence', params: [run.runId, ep.trial_id], query: {} },
    });
    E('cell', eid, `trial ${i + 1} of ${episodes.length}`, true);

    const trace = ep.trace_artifact || null;
    const snap = sibArtifact(trace, '.snapshot.json');
    const acts = sibArtifact(trace, '.actions.json');
    const states = [[trace, 'trace'], [snap, 'snapshot'], [acts, 'actions']]
      .map(([p, name]) => ({ path: p, name, present: p ? presence[p] === true : false }));
    const missing = states.filter((s) => !s.present);
    const aid = `art:${ep.trial_id}`;
    N({
      id: aid, layer: 4, kind: 'artifacts', label: 'artifacts', missing: missing.length > 0,
      sub: states.map((s) => `${s.name} ${s.present ? '✓' : '✗'}`).join(' · '),
      meta: states.map((s) => [s.name, `${s.path || 'no path'} — ${s.present ? 'present' : 'MISSING / unchecked'}`]),
      href: null,
    });
    E(eid, aid, missing.length ? `missing: ${missing.map((s) => s.name).join(', ')}` : 'trace + snapshot + actions present', missing.length === 0);
    if (missing.length) issues.push({ severity: 'error', text: `${ep.trial_id}: missing ${missing.map((s) => `${s.name} (${s.path})`).join(', ')}.` });

    for (const s of sampledByTrial.get(ep.trial_id) || []) {
      const vrec = (verdictsByTrial.get(ep.trial_id) || []).find((v) => v.planKind === s.planKind);
      const agree = vrec ? checksAgree(vrec.verdict, ep.verification) : null;
      const pathsAgree = s.entry.trace_path === trace;
      const vid = `ver:${ep.trial_id}:${s.planKind}`;
      const status = !vrec ? 'sampled, no verdict recorded'
        : vrec.verdict && vrec.verdict.verdict === 'unauditable' ? 'unauditable'
          : agree === true ? 'agrees with verifier' : agree === false ? 'DISAGREES with verifier' : 'verdict uncomputable';
      N({
        id: vid, layer: 5, kind: 'verdict', label: `${ep.trial_id} · ${s.planKind}`, missing: !vrec,
        sub: `${status}${pathsAgree ? '' : ' · trace path MISMATCH'}`,
        meta: [['Plan', s.planKind], ['Plan cell', s.cellKey], ['Expected name', s.entry.expected_stored_name || '—'],
          ['Verifier checks', JSON.stringify(s.entry.verifier_checks ?? '—')],
          ['Human verdict', vrec ? JSON.stringify(vrec.verdict) : 'none recorded'],
          ['Trace path agrees', pathsAgree ? 'yes' : `NO — plan: ${s.entry.trace_path}, episode: ${trace}`]],
        href: { route: 'evidence', params: [run.runId, ep.trial_id], query: {} },
      });
      E(eid, vid, `sampled in ${s.planKind} plan`, true);
      E(vid, `plan:${s.planKind}`, 'recorded in', true);
      if (!pathsAgree) issues.push({ severity: 'error', text: `${ep.trial_id}: plan ${s.planKind} trace_path differs from the episode record.` });
    }
  });

  for (const p of plans) {
    const runMatch = p.data && p.data.run_id === run.runId;
    const shaMatch = p.data && run.data.manifest_sha256 && p.data.manifest_sha256 === run.data.manifest_sha256;
    const pid = `plan:${p.kind}`;
    const cells = Object.values((p.data && p.data.cells) || {});
    const sampled = cells.reduce((n, c) => n + (c.sampled || []).length, 0);
    const nver = cells.reduce((n, c) => n + Object.keys(c.verdicts || {}).length, 0);
    N({
      id: pid, layer: 6, kind: 'plan', label: `${p.kind} audit plan`, missing: !runMatch,
      sub: `${sampled} sampled · ${nver} verdicts`,
      meta: [['plan.run_id', (p.data && p.data.run_id) || '—'], ['plan.manifest_sha256', ((p.data && p.data.manifest_sha256) || '').slice(0, 12) || '—']],
      href: { route: 'audit', params: [], query: {} },
    });
    E('run', pid, runMatch && shaMatch ? 'run_id + manifest sha agree' : 'identity MISMATCH', Boolean(runMatch && shaMatch));
    if (!runMatch || !shaMatch) issues.push({ severity: 'error', text: `${p.kind} plan identity does not match run ${run.runId}.` });
  }

  for (const r of reports) {
    if (!r.text || !r.text.includes(run.runId)) continue; // never link by convention alone
    const rid = `rep:${r.id}`;
    N({
      id: rid, layer: 6, kind: 'report', label: r.title, sub: 'cites this run_id',
      meta: [['Report', r.id]], href: { route: 'archive', params: [], query: { doc: r.id } },
    });
    E('run', rid, 'run_id cited in report text', true);
  }

  const unsampled = episodes.filter((e) => !sampledByTrial.has(e.trial_id)).length;
  if (unsampled) issues.push({ severity: 'info', text: `${unsampled}/${episodes.length} cell episodes were not sampled in any loaded plan.` });
  if (planVerdicts === 0 && planSampled > 0) issues.push({ severity: 'info', text: 'Loaded plans sample episodes but record zero verdicts — nothing is adjudicated.' });
  return { nodes, edges, issues };
}
