/* Chimera console data layer.
 * Sole reader of benchmark evidence. Every page consumes run files,
 * manifests, audit plans, and reports through this module — nothing
 * invents metrics. Missing files surface as explicit unavailable
 * states, never as zeros.
 */

export const RUNS = [
  { runId: 'dev-20261028-chimera', file: 'artifacts/dev-20261028/run-chimera.json',
    manifestFile: 'benchmarks/manifests/dev-v1.json', baseline: 'chimera', split: 'development' },
  { runId: 'dev-20261028-baseline-a', file: 'artifacts/dev-20261028/run-baseline-a.json',
    manifestFile: 'benchmarks/manifests/dev-v1.json', baseline: 'baseline-a', split: 'development' },
  { runId: 'eval-20261028-chimera', file: 'artifacts/eval-20261028/run-chimera.json',
    manifestFile: 'benchmarks/manifests/eval-v1.json', baseline: 'chimera', split: 'evaluation' },
  { runId: 'eval-20261028-baseline-a', file: 'artifacts/eval-20261028/run-baseline-a.json',
    manifestFile: 'benchmarks/manifests/eval-v1.json', baseline: 'baseline-a', split: 'evaluation' },
];

export const AUDIT_PLANS = [
  { runId: 'dev-20261028-chimera', kind: 'full', file: 'artifacts/dev-20261028/run-chimera.audit-plan.json' },
  { runId: 'dev-20261028-baseline-a', kind: 'full', file: 'artifacts/dev-20261028/run-baseline-a.audit-plan.json' },
  { runId: 'eval-20261028-chimera', kind: 'full', file: 'artifacts/eval-20261028/run-chimera.audit-plan.json' },
  { runId: 'eval-20261028-baseline-a', kind: 'full', file: 'artifacts/eval-20261028/run-baseline-a.audit-plan.json' },
  { runId: 'eval-20261028-chimera', kind: 'mini', file: 'artifacts/eval-20261028/run-chimera.audit-plan-mini.json' },
  { runId: 'eval-20261028-baseline-a', kind: 'mini', file: 'artifacts/eval-20261028/run-baseline-a.audit-plan-mini.json' },
];

export const AUDITED_RUNS = [
  { runId: 'dev-20261028-chimera', file: 'artifacts/dev-20261028/run-chimera.audited.json' },
  { runId: 'dev-20261028-baseline-a', file: 'artifacts/dev-20261028/run-baseline-a.audited.json' },
];

export const REPORTS = [
  { id: 'dev', title: 'Development report (initial)', file: 'artifacts/dev-20261028/report.md' },
  { id: 'dev-audited', title: 'Development report (audited)', file: 'artifacts/dev-20261028/report-audited.md' },
  { id: 'eval', title: 'Held-out evaluation report (provisional)', file: 'artifacts/eval-20261028/report.md' },
];

export const SCENARIOS = ['S-NORM', 'S-SLOW', 'S-DIS', 'S-SLOWDIS'];
export const BASELINES = ['chimera', 'baseline-a'];

const state = {
  runs: new Map(), manifests: new Map(), plans: [], audited: new Map(),
  reports: new Map(), episodes: [], cells: [],
  loaded: false, loadError: null, failed: [],
};

/** Evidence paths are repo-root-relative; the app is served from /research/. */
export function rootPath(path) {
  const p = String(path || '');
  return p.startsWith('/') ? p : `/${p}`;
}

async function fetchJson(path) {
  const url = rootPath(path);
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json();
}

async function fetchText(path) {
  const url = rootPath(path);
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.text();
}

export async function loadAll(onProgress) {
  if (state.loaded) return state;
  const jobs = [];
  const track = async (label, fn) => {
    // One retry: boot fires ~30 parallel fetches at a toy static
    // server, which intermittently drops one. Persistent failures
    // still land in state.failed and surface in the footer.
    for (let attempt = 0; attempt < 2; attempt++) {
      try {
        await fn();
        break;
      } catch (err) {
        if (attempt === 1) state.failed.push(label);
        else await new Promise((r) => setTimeout(r, 200));
      }
    }
    if (onProgress) onProgress(state);
  };
  for (const r of RUNS) {
    jobs.push(track(r.runId, async () => {
      state.runs.set(r.runId, { ...r, data: await fetchJson(r.file) });
    }));
    jobs.push(track(r.manifestFile, async () => {
      if (!state.manifests.has(r.manifestFile)) {
        state.manifests.set(r.manifestFile, await fetchJson(r.manifestFile));
      }
    }));
  }
  for (const p of AUDIT_PLANS) {
    jobs.push(track(p.file, async () => {
      state.plans.push({ ...p, data: await fetchJson(p.file) });
    }));
  }
  for (const a of AUDITED_RUNS) {
    jobs.push(track(a.file, async () => {
      state.audited.set(a.runId, await fetchJson(a.file));
    }));
  }
  for (const rep of REPORTS) {
    jobs.push(track(rep.file, async () => {
      state.reports.set(rep.id, { ...rep, text: await fetchText(rep.file) });
    }));
  }
  await Promise.all(jobs);
  indexAll();
  state.loaded = true;
  return state;
}

function indexAll() {
  state.episodes = [];
  state.cells = [];
  for (const [runId, run] of state.runs) {
    if (!run.data) continue;
    for (const cell of run.data.cells || []) {
      state.cells.push({ ...cell, runId, baseline: run.baseline, split: run.split });
    }
    for (const ep of run.data.episodes || []) {
      state.episodes.push({ ...ep, runId, baseline: run.baseline, split: run.split });
    }
  }
}

export function getState() { return state; }
export function getRun(runId) { const r = state.runs.get(runId); return r && r.data ? r : null; }
export function getManifest(path) { return state.manifests.get(path) || null; }

/** Metric contract: {value, unavailable_reason} — never zero-fill. */
export function mVal(metric) {
  if (!metric || metric.unavailable_reason != null) {
    return { ok: false, value: null, reason: (metric && metric.unavailable_reason) || 'not recorded' };
  }
  return { ok: true, value: metric.value, reason: null };
}

export function isWarmup(ep) { return (ep.trial_id || '').startsWith('warmup:'); }
export function isHarnessError(ep) { return (ep.error || '').startsWith('harness_error:'); }

export function isFalseSuccess(ep) {
  return ep.agent_terminal_status === 'succeeded'
    && ep.verification && ep.verification.status === 'verified'
    && ep.verification.all_satisfied === false;
}

export function measuredEpisodes(runId) {
  return state.episodes.filter((e) => (!runId || e.runId === runId) && !isWarmup(e));
}

/** Wilson score upper bound (95%, z=1.96), same definition as evaluation §4.3. */
export function wilsonUpper(k, n, z = 1.96) {
  if (n <= 0 || k < 0 || k > n) return null;
  const denom = 1 + (z * z) / n;
  const center = (k / n + (z * z) / (2 * n)) / denom;
  const spread = (z * Math.sqrt(((k / n) * (1 - k / n)) / n + (z * z) / (4 * n * n))) / denom;
  return Math.min(1, center + spread);
}

/** Human verdicts joined by run+trial across all loaded plans. */
export function verdictIndex() {
  const idx = new Map();
  for (const p of state.plans) {
    if (!p.data) continue;
    for (const [cellKey, cell] of Object.entries(p.data.cells || {})) {
      for (const [trialId, verdict] of Object.entries(cell.verdicts || {})) {
        const key = `${p.runId}::${trialId}`;
        if (!idx.has(key)) idx.set(key, []);
        idx.get(key).push({ planKind: p.kind, cellKey, verdict });
      }
    }
  }
  return idx;
}

/** Per-run audit rollup. Audited runs (applied verdicts) take precedence. */
export function auditStatus(runId) {
  const run = getRun(runId);
  const audited = state.audited.get(runId);
  const source = audited || (run && run.data);
  if (!source) return { state: 'missing', cells: 0, auditedCells: 0, episodes: 0, agreed: 0 };
  const cells = source.cells || [];
  let auditedCells = 0, episodes = 0, agreed = 0;
  for (const c of cells) {
    if (c.verifier_audit) {
      auditedCells += 1;
      episodes += c.verifier_audit.sampled || 0;
      agreed += c.verifier_audit.agreed || 0;
    }
  }
  const plans = state.plans.filter((p) => p.runId === runId && p.data);
  const sampled = plans.reduce((n, p) => n + Object.values(p.data.cells || {})
    .reduce((m, c) => m + (c.sampled || []).length, 0), 0);
  const state_ = auditedCells === cells.length && cells.length > 0 ? 'audited'
    : auditedCells > 0 ? 'partial' : 'pending';
  return { state: state_, cells: cells.length, auditedCells, episodes, agreed, plansSampled: sampled };
}

export function filterEpisodes({ runId = '', scenario = '', baseline = '', outcome = '', search = '' } = {}) {
  const q = search.trim().toLowerCase();
  return state.episodes.filter((e) => {
    if (isWarmup(e)) return false;
    if (runId && e.runId !== runId) return false;
    if (scenario && e.scenario_id !== scenario) return false;
    if (baseline && e.baseline !== baseline) return false;
    if (outcome === 'harness-error') { if (!isHarnessError(e)) return false; }
    else if (outcome === 'false-success') { if (!isFalseSuccess(e)) return false; }
    else if (outcome && e.outcome !== outcome) return false;
    if (q && !(e.trial_id.toLowerCase().includes(q) || (e.error || '').toLowerCase().includes(q)
      || e.scenario_id.toLowerCase().includes(q) || e.input_id.toLowerCase().includes(q))) return false;
    return true;
  });
}

export function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

export function fmtInt(n) { return n == null ? '—' : Number(n).toLocaleString('en-US'); }
export function fmtMs(ms) {
  if (ms == null) return '—';
  return `${Number(ms).toLocaleString('en-US')} ms`;
}
export function fmtPct(k, n) {
  if (n == null || n <= 0) return '—';
  const v = (100 * k) / n;
  return `${Number.isInteger(v) ? v : v.toFixed(1)}%`;
}
export function shortHash(h) { return h ? `${String(h).slice(0, 12)}…` : '—'; }
export function baselineLabel(b) { return b === 'chimera' ? 'Chimera' : b === 'baseline-a' ? 'A — replay' : b; }
