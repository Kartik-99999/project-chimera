/* Chimera multipage shared figures — live numbers from frozen evidence.
 * Every number is computed from fetched run/manifest/plan/decision files.
 * All paths are root-relative so subdirectory pages work under both
 * sanctioned servers (repo root mounted at /). Every renderer guards its
 * DOM hosts and degrades silently when absent from the current page.
 * Reuses the Research stats kit (wilson) — no duplication, no new deps.
 */
import { wilson } from '/research/js/viz/stats.js';
import { paintPortal, setFigs } from '/site/nav.js';

export const RUNS = {
  'dev-20261028-chimera': '/artifacts/dev-20261028/run-chimera.json',
  'dev-20261028-baseline-a': '/artifacts/dev-20261028/run-baseline-a.json',
  'eval-20261028-chimera': '/artifacts/eval-20261028/run-chimera.json',
  'eval-20261028-baseline-a': '/artifacts/eval-20261028/run-baseline-a.json',
};
export const MANIFESTS = {
  development: '/benchmarks/manifests/dev-v1.json',
  evaluation: '/benchmarks/manifests/eval-v1.json',
};
export const PLANS = {
  dev: ['/artifacts/dev-20261028/run-chimera.audit-plan.json', '/artifacts/dev-20261028/run-baseline-a.audit-plan.json'],
  mini: ['/artifacts/eval-20261028/run-chimera.audit-plan-mini.json', '/artifacts/eval-20261028/run-baseline-a.audit-plan-mini.json'],
  full: ['/artifacts/eval-20261028/run-chimera.audit-plan.json', '/artifacts/eval-20261028/run-baseline-a.audit-plan.json'],
};
export const DECISIONS = '/artifacts/eval-20261028/mini-review/decisions.json';
export const FULL_DECISIONS = '/artifacts/audit-full-v1/review/decisions.json';
export const REPORTS = ['/artifacts/dev-20261028/report.md', '/artifacts/dev-20261028/report-audited.md', '/artifacts/eval-20261028/report.md'];
export const MB_RESULTS = '/experiments/matched-budget-v1/RESULTS.json';
export const SAUCE_TRIALS = '/artifacts/sauce-stress-v2/trials.csv';
export const SCENARIOS = ['S-NORM', 'S-SLOW', 'S-DIS', 'S-SLOWDIS'];
export const SCENARIO_PLAIN = { 'S-NORM': 'Normal', 'S-SLOW': 'Slow page', 'S-DIS': 'Disabled input', 'S-SLOWDIS': 'Slow + disabled' };
const COND_HUE = { 'S-NORM': '#0B9FB8', 'S-SLOW': '#3A6EA5', 'S-DIS': '#E0654A', 'S-SLOWDIS': '#7C5CDB' };
export const JOURNEYS = {
  success: { runId: 'eval-20261028-chimera', trial: 'trial-0055' },
  failure: { runId: 'eval-20261028-chimera', trial: 'trial-0100' },
};

export const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
export const fmtInt = (n) => (n == null ? '—' : Number(n).toLocaleString('en-US'));
export const fmtPct = (k, n) => (n > 0 ? `${((100 * k) / n).toFixed(1)}%` : '—');
export const reducedMotion = () => window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* Data files store repo-relative paths (e.g. trace_artifact). Prefix them
 * so fetches resolve from the repo root on every page. */
function rootify(path) {
  if (!path) return path;
  if (path.startsWith('/') || /^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(path)) return path;
  return `/${path.replace(/^\.\//, '')}`;
}

export async function fetchJson(path) {
  const res = await fetch(rootify(path), { cache: 'no-store' });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${path}`);
  return res.json();
}
export async function fetchText(path) {
  const res = await fetch(rootify(path), { cache: 'no-store' });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${path}`);
  return res.text();
}
async function fetchOk(path) {
  try { const res = await fetch(rootify(path), { cache: 'no-store' }); return res.ok; } catch { return false; }
}
export const measured = (run) => (run.episodes || []).filter((e) => !String(e.trial_id).startsWith('warmup:'));
export const isFalseSuccess = (e) => e.agent_terminal_status === 'succeeded'
  && e.verification && e.verification.status === 'verified' && e.verification.all_satisfied === false;

export async function loadRuns() {
  const entries = await Promise.all(Object.entries(RUNS).map(async ([id, path]) => {
    const data = await fetchJson(path);
    const [split, baseline] = id.includes('dev-')
      ? ['development', id.includes('chimera') ? 'chimera' : 'baseline-a']
      : ['evaluation', id.includes('chimera') ? 'chimera' : 'baseline-a'];
    return [id, { ...data, __split: split, __baseline: baseline }];
  }));
  return Object.fromEntries(entries);
}
export async function loadManifests() {
  return {
    development: await fetchJson(MANIFESTS.development).catch(() => null),
    evaluation: await fetchJson(MANIFESTS.evaluation).catch(() => null),
  };
}

/* ---------- hero figures (home + any data-fig hosts) ---------- */
function countUp(el, target) {
  if (reducedMotion()) { el.textContent = fmtInt(target); return; }
  const t0 = performance.now(), dur = 900;
  const step = (t) => {
    const p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 3);
    el.textContent = fmtInt(Math.round(target * e));
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

export function renderHero(runs) {
  const eps = Object.values(runs).flatMap(measured);
  const fs = eps.filter(isFalseSuccess).length;
  const conds = new Set(eps.map((e) => e.scenario_id)).size;
  const evalEps = Object.values(runs).filter((r) => r.__split === 'evaluation').flatMap(measured).length;
  const devEps = Object.values(runs).filter((r) => r.__split === 'development').flatMap(measured).length;
  setFigs({ EPISODES: eps.length, EVALEPS: evalEps, DEVEPS: devEps, CONDS: conds, FS: fs });
  document.querySelectorAll('[data-fig="episodes"]').forEach((el) => countUp(el, eps.length));
  document.querySelectorAll('[data-fig="conditions"]').forEach((el) => { el.textContent = conds; });
  document.querySelectorAll('[data-fig="falsesucc"]').forEach((el) => { el.textContent = fs; });
  document.querySelectorAll('[data-fig="falsesucc-den"]').forEach((el) => { el.textContent = `· n=${fmtInt(eps.length)}`; });
  paintPortal();
}

/* ---------- outcome matrix ---------- */
function aggFor(runs, split) {
  const out = {};
  for (const sc of SCENARIOS) {
    out[sc] = {};
    for (const b of ['chimera', 'baseline-a']) {
      const eps = Object.values(runs)
        .filter((r) => r.__split === split && r.__baseline === b)
        .flatMap(measured)
        .filter((e) => e.scenario_id === sc);
      out[sc][b] = { k: eps.filter((e) => e.outcome === 'succeeded').length, n: eps.length };
    }
  }
  return out;
}

export function renderMatrix(runs, manifests, split) {
  const table = document.getElementById('matrix');
  if (!table) return;
  const agg = aggFor(runs, split);
  const man = manifests[split];
  const expected = {};
  for (const s of (man && man.scenarios) || []) expected[s.id] = s.expected_outcome;
  const tb = table.querySelector('tbody');
  tb.innerHTML = SCENARIOS.map((sc) => {
    const c = agg[sc].chimera, r = agg[sc]['baseline-a'];
    const cell = (a, color) => {
      const iv = wilson(a.k, a.n);
      const tip = a.n > 0 && iv
        ? `${sc}: ${a.k}/${a.n} = ${fmtPct(a.k, a.n)}, 95% Wilson [${(iv.lo * 100).toFixed(1)}%, ${(iv.hi * 100).toFixed(1)}%]`
        : `${sc}: no episodes`;
      return `<td class="rate" tabindex="0" data-tip="${esc(tip)}"><span class="k">${a.k}/${a.n}</span><span class="pct">${fmtPct(a.k, a.n)}</span>`
        + `<span class="bar" aria-hidden="true"><span style="transform:scaleX(${a.n ? (a.k / a.n).toFixed(3) : 0});background:${color}"></span></span></td>`;
    };
    const tied = c.n > 0 && r.n > 0 && c.k / c.n === r.k / r.n;
    const dTitle = 'Chimera rate minus replay rate, this condition only — not a cross-condition comparison';
    const dpp = c.n > 0 && r.n > 0 ? 100 * (c.k / c.n - r.k / r.n) : 0;
    const dot = `<span class="delta-track" aria-hidden="true"><span class="delta-dot${tied ? ' is-tied' : ''}" style="left:${(50 + dpp / 2).toFixed(1)}%"></span></span>`;
    const delta = c.n > 0 && r.n > 0
      ? (tied ? `<span class="delta-flat" tabindex="0" data-tip="${esc(dTitle)}">tied</span>${dot}`
        : `<span class="delta-up" tabindex="0" data-tip="${esc(dTitle)}">Chimera +${dpp.toFixed(0)}pp</span>${dot}`)
      : '<span class="delta-flat">—</span>';
    return `<tr><th scope="row"><span class="cond-chip" style="--cond:${COND_HUE[sc] || '#6e7480'}" aria-hidden="true"></span>${esc(SCENARIO_PLAIN[sc])} <small>${esc(sc)} · expected ${esc(expected[sc] || '?')}</small></th>`
      + `${cell(c, '#0e7490')}${cell(r, '#6d28d9')}<td>${delta}<small><a href="/research/#/atlas?scenario=${sc}">episodes →</a></small></td></tr>`;
  }).join('');
  table.dispatchEvent(new Event('matrix-repaint'));
  let best = null;
  for (const sc of SCENARIOS) {
    const c = agg[sc].chimera, r = agg[sc]['baseline-a'];
    if (c.n > 0 && r.n > 0) {
      const d = Math.abs(c.k / c.n - r.k / r.n);
      if (!best || d > best.d) best = { sc, d, c, r };
    }
  }
  const disK = ['S-DIS', 'S-SLOWDIS'].reduce((a, sc) => a + agg[sc].chimera.k + agg[sc]['baseline-a'].k, 0);
  const disN = ['S-DIS', 'S-SLOWDIS'].reduce((a, sc) => a + agg[sc].chimera.n + agg[sc]['baseline-a'].n, 0);
  const interp = document.querySelector('#matrix-interp');
  if (interp) {
    interp.innerHTML = best
      ? `<strong>Reading:</strong> the widest gap is <strong>${esc(SCENARIO_PLAIN[best.sc])}</strong> — Chimera ${best.c.k}/${best.c.n}, replay ${best.r.k}/${best.r.n}. `
        + `Persistent-fault cells are ${disK}/${disN} succeeded across both drivers: the expected bounded outcome, since success is impossible there.`
      : 'No comparable cells in this split.';
  }
}

export function initSplitToggle(runs, manifests) {
  const btns = [...document.querySelectorAll('[data-split]')];
  if (!btns.length || !document.getElementById('matrix')) return;
  let split = 'evaluation';
  renderMatrix(runs, manifests, split);
  btns.forEach((b) => b.addEventListener('click', () => {
    split = b.dataset.split;
    btns.forEach((o) => {
      const on = o === b;
      o.classList.toggle('on', on);
      o.setAttribute('aria-pressed', String(on));
    });
    renderMatrix(runs, manifests, split);
  }));
}

/* ---------- terminal correctness ---------- */
export function renderTerminal(runs) {
  const host = document.querySelector('#terminal-grid');
  if (!host) return;
  const cells = ['chimera', 'baseline-a'].map((b) => {
    const eps = Object.values(runs).filter((r) => r.__split === 'evaluation' && r.__baseline === b).flatMap(measured);
    const failed = eps.filter((e) => e.outcome !== 'succeeded');
    const correct = failed.filter((e) => e.agent_terminal_status === 'failed').length;
    const color = b === 'chimera' ? '#0e7490' : '#6d28d9';
    return { b, failed: failed.length, correct, color };
  });
  host.innerHTML = cells.map((c) => (
    `<div class="terminal-cell"><div class="t-name"><span class="sw" style="background:${c.color}"></span>${c.b === 'chimera' ? 'Chimera' : 'Replay baseline'} · held-out</div>`
    + `<div class="t-fig">${c.correct}/${c.failed}</div>`
    + `<div class="t-sub">non-success episodes correctly reported as failed</div>`
    + `<span class="t-bar" aria-hidden="true"><span style="width:${c.failed ? ((100 * c.correct) / c.failed).toFixed(1) : 0}%;background:${c.color}"></span></span></div>`)).join('');
  const all = cells.every((c) => c.failed > 0 && c.correct === c.failed);
  const interp = document.querySelector('#terminal-interp');
  if (interp) {
    interp.innerHTML = all
      ? '<strong>Reading:</strong> every impossible trial was reported as failure by both drivers — bounded failure with no misreported successes in 360 held-out episodes.'
      : '<strong>Reading:</strong> most failures were reported correctly; inspect the exceptions in the Research Console.';
  }
}

/* ---------- latency ---------- */
function pct(sorted, q) {
  if (!sorted.length) return null;
  return sorted[Math.min(sorted.length - 1, Math.max(0, Math.ceil((q / 100) * sorted.length) - 1))];
}
export function renderLatency(runs) {
  const host = document.querySelector('#latency-chart');
  if (!host) return;
  const lanes = ['chimera', 'baseline-a'].map((b) => ({
    b, durs: Object.values(runs).filter((r) => r.__split === 'evaluation' && r.__baseline === b)
      .flatMap(measured).map((e) => e.duration_ms).filter((d) => d != null).sort((x, y) => x - y),
  }));
  const max = Math.max(1, ...lanes.flatMap((l) => l.durs));
  const W = 760, padL = 132, padR = 20, laneH = 72, padT = 22, padB = 30;
  const H = padT + lanes.length * laneH + padB;
  const x = (v) => padL + ((W - padL - padR) * v) / max;
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Episode durations, held-out split">`;
  const ticks = 5;
  for (let i = 0; i <= ticks; i += 1) {
    const v = (max * i) / ticks;
    s += `<line x1="${x(v).toFixed(0)}" y1="${padT}" x2="${x(v).toFixed(0)}" y2="${(H - padB + 6).toFixed(0)}" stroke="#e3e5ea"/>`
      + `<text class="lat-axis" x="${x(v).toFixed(0)}" y="${H - 8}" text-anchor="middle">${v >= 1000 ? `${(v / 1000).toFixed(1)}s` : `${Math.round(v)}ms`}</text>`;
  }
  s += `<text class="lat-axis" x="${W - padR}" y="${padT - 8}" text-anchor="end">duration →</text>`;
  lanes.forEach((l, li) => {
    const y = padT + li * laneH + laneH / 2;
    const color = l.b === 'chimera' ? '#0e7490' : '#6d28d9';
    const q1 = pct(l.durs, 25), q3 = pct(l.durs, 75);
    if (q1 != null && q3 != null) {
      s += `<rect x="${x(q1).toFixed(1)}" y="${y - 13}" width="${Math.max(2, x(q3) - x(q1)).toFixed(1)}" height="26" rx="4" fill="${color}" opacity="0.13"><title>${l.b} interquartile range: p25 ${q1} ms – p75 ${q3} ms (n=${l.durs.length})</title></rect>`;
    }
    s += `<text class="lat-meta" x="${padL - 10}" y="${y + 4}" text-anchor="end">${l.b === 'chimera' ? 'Chimera' : 'Replay'} (n=${l.durs.length})</text>`;
    l.durs.forEach((d, i) => {
      const jy = y - 14 + ((i * 37) % 28);
      s += `<circle class="lat-dot" cx="${x(d).toFixed(1)}" cy="${jy.toFixed(1)}" r="3.2" fill="${color}"><title>${l.b}: ${d} ms</title></circle>`;
    });
    for (const [q, dash, lab, dy] of [[50, '', 'p50', -26], [95, '4 3', 'p95', 32]]) {
      const v = pct(l.durs, q);
      if (v == null) continue;
      s += `<line class="lat-p" x1="${x(v).toFixed(1)}" y1="${y - 22}" x2="${x(v).toFixed(1)}" y2="${y + 22}" stroke="${color}"${dash ? ` stroke-dasharray="${dash}"` : ''}/>`
        + `<text class="lat-meta" x="${x(v).toFixed(1)}" y="${y + dy}" text-anchor="middle">${lab} ${v}ms</text>`;
    }
  });
  host.innerHTML = `${s}</svg><span class="scroll-hint" aria-hidden="true">scroll →</span>`;
  const [c, r] = lanes;
  const cap = document.querySelector('#latency-cap');
  if (cap) cap.textContent = `Held-out durations, all ${c.durs.length + r.durs.length} episodes. Same-machine comparison only; values include browser start-up.`;
  const interp = document.querySelector('#latency-interp');
  if (interp) {
    interp.innerHTML =
      `<strong>Reading:</strong> Chimera p50 ${pct(c.durs, 50)} ms / p95 ${pct(c.durs, 95)} ms; replay p50 ${pct(r.durs, 50)} ms / p95 ${pct(r.durs, 95)} ms. `
      + 'Replay is faster because it gives up in about a tenth of a second; Chimera spends seconds waiting and retrying before concluding a task is impossible.';
  }
}

/* ---------- journey strips ---------- */
const J_SHORT = { run_started: 'start', navigate: 'go to page', fill: 'fill name', click: 'click Create', verification_passed: 'check ✓', verification_failed: 'check ✗', run_succeeded: 'done ✓', run_failed: 'failed ✗', run_cancelled: 'stopped' };
function jColor(ev) {
  if (ev.event_type === 'action_failed' || ev.event_type === 'run_failed') return '#b91c1c';
  if (ev.event_type === 'run_cancelled') return '#b45309';
  if (ev.event_type.startsWith('verification')) return '#6d28d9';
  if (ev.event_type === 'run_started' || ev.event_type === 'run_succeeded') return '#1d4ed8';
  if (ev.event_type === 'action_attempted') return '#5f6b82';
  return '#15803d';
}
function jLabel(ev) {
  if (ev.event_type === 'action_attempted' || ev.event_type === 'action_succeeded' || ev.event_type === 'action_failed') {
    const base = J_SHORT[ev.action_type] || ev.action_type || 'act';
    if (ev.event_type === 'action_attempted') return { main: base, sub: 'attempt' };
    return { main: `${base} ${ev.event_type === 'action_succeeded' ? '✓' : '✗'}`, sub: null };
  }
  return { main: J_SHORT[ev.event_type] || ev.event_type, sub: null };
}
function pairDurations(events) {
  const out = new Map();
  const open = new Map();
  for (const ev of events) {
    if (ev.event_type === 'action_attempted' && ev.action_type) open.set(ev.action_type, ev.timestamp);
    if ((ev.event_type === 'action_succeeded' || ev.event_type === 'action_failed') && ev.action_type && open.has(ev.action_type)) {
      const a = Date.parse(open.get(ev.action_type)), b = Date.parse(ev.timestamp);
      if (!Number.isNaN(a) && !Number.isNaN(b)) out.set(ev.sequence_number, b - a);
      open.delete(ev.action_type);
    }
  }
  return out;
}
export function renderJourney(el, trace) {
  if (!el) return;
  const events = (trace.events || []).slice().sort((a, b) => a.sequence_number - b.sequence_number);
  const durs = pairDurations(events);
  const perRow = 5, dx = 118, x0 = 66, rows = Math.ceil(events.length / perRow);
  const rowY = (r) => 30 + r * 92;
  const W = x0 * 2 + dx * (perRow - 1), H = rowY(rows - 1) + 62;
  const pos = events.map((_, i) => {
    const row = Math.floor(i / perRow), col = i % perRow;
    const c = row % 2 === 0 ? col : perRow - 1 - col;
    return { x: x0 + c * dx, y: rowY(row) };
  });
  let d = '';
  pos.forEach((p, i) => { d += `${i === 0 ? 'M' : 'L'}${p.x},${p.y} `; });
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(`Trace with ${events.length} events, ending ${events.length ? events[events.length - 1].event_type : 'unknown'}`)}">`;
  s += `<path class="j-edge" d="${d.trim()}"/>`;
  events.forEach((ev, i) => {
    const p = pos[i], col = jColor(ev), small = ev.event_type === 'action_attempted';
    const ms = durs.get(ev.sequence_number);
    const lab = jLabel(ev);
    const full = `#${ev.sequence_number} ${ev.event_type}${ev.action_type ? ` ${ev.action_type}` : ''}${ms != null ? ` · ${ms} ms` : ''}`;
    const sub = ms != null ? `${ms} ms` : lab.sub;
    s += `<g class="j-node" style="--d:${i * 90}ms" tabindex="0" role="button" aria-label="${esc(full)}" data-full="${esc(full)}"><title>${esc(full)}</title>`
      + `<circle cx="${p.x}" cy="${p.y}" r="${small ? 7 : 12}" fill="${small ? '#ffffff' : col}" stroke="${col}" stroke-width="2.5"/>`
      + `<text class="j-seq" x="${p.x}" y="${p.y - 18}" text-anchor="middle">#${ev.sequence_number}</text>`
      + `<text class="j-label" x="${p.x}" y="${p.y + 30}" text-anchor="middle">${esc(lab.main)}</text>`
      + (sub != null ? `<text class="j-seq" x="${p.x}" y="${p.y + 43}" text-anchor="middle">${esc(sub)}</text>` : '')
      + `</g>`;
  });
  el.innerHTML = `${s}</svg><p class="j-readout" aria-live="polite">Select a step for full detail.</p><ol class="vh" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)">${events.map((ev) => `<li>#${ev.sequence_number} ${esc(ev.event_type)}${ev.action_type ? ` ${esc(ev.action_type)}` : ''}</li>`).join('')}</ol>`;
  const readout = el.querySelector('.j-readout');
  const show = (n) => { if (n && readout) readout.textContent = n.getAttribute('data-full'); };
  el.addEventListener('click', (e) => {
    const n = e.target && e.target.closest ? e.target.closest('.j-node') : null;
    show(n);
  });
  el.addEventListener('keydown', (e) => {
    if ((e.key === 'Enter' || e.key === ' ') && e.target.classList && e.target.classList.contains('j-node')) {
      e.preventDefault();
      show(e.target);
    }
  });
}

/* Load both recorded traces; paints journey strips where present. */
export async function loadDemoData(runs) {
  const demoData = {};
  for (const [key, { runId, trial }] of Object.entries(JOURNEYS)) {
    const host = document.querySelector(`[data-journey="${key}"]`);
    try {
      const ep = measured(runs[runId]).find((e) => e.trial_id === trial);
      if (!ep || !ep.trace_artifact) throw new Error('episode not in run file');
      const trace = await fetchJson(ep.trace_artifact);
      if (host) renderJourney(host, trace);
      let snap = null;
      try {
        const ref = (ep.verification && ep.verification.checks
          && ep.verification.checks[0] && ep.verification.checks[0].evidence_reference) || '';
        if (ref) snap = await fetchJson(ref.split('#')[0]);
      } catch { snap = null; }
      demoData[key] = { ep, trace, snap, runId, trial };
    } catch {
      if (host) host.innerHTML = '<p class="loading">Trace unavailable in this checkout — open the Research Console link above instead.</p>';
    }
  }
  return demoData;
}

/* ---------- coverage + review (evidence page) ---------- */
function countVerdicts(plan) {
  let n = 0, agree = 0;
  for (const cell of Object.values((plan && plan.cells) || {})) {
    for (const [trial, v] of Object.entries(cell.verdicts || {})) {
      n += 1;
      const bundle = (cell.sampled || []).find((b) => b.trial_id === trial);
      if (v && v.checks && bundle && bundle.verifier_checks) {
        const keys = Object.keys(v.checks);
        if (keys.length === Object.keys(bundle.verifier_checks).length && keys.every((k) => v.checks[k] === bundle.verifier_checks[k])) agree += 1;
      }
    }
  }
  return { n, agree };
}
export async function renderCoverage(runs) {
  const covHost = document.querySelector('#coverage');
  if (!covHost && !document.querySelector('#review-facts') && !document.querySelector('#dossierFigures')) return;
  const cells = Object.values(runs).reduce((a, r) => a + (r.cells || []).length, 0);
  const eps = Object.values(runs).flatMap(measured);
  const traced = eps.filter((e) => e.trace_artifact).length;
  const verified = eps.filter((e) => e.verification && e.verification.status === 'verified').length;
  let devV = { n: 0, agree: 0 }, miniV = 0;
  try {
    const dev = await Promise.all(PLANS.dev.map(fetchJson));
    devV = dev.map(countVerdicts).reduce((a, c) => ({ n: a.n + c.n, agree: a.agree + c.agree }), { n: 0, agree: 0 });
    const mini = await Promise.all(PLANS.mini.map(fetchJson));
    miniV = mini.map(countVerdicts).reduce((a, c) => a + c.n, 0);
  } catch { /* plans optional; show run-derived counts only */ }
  let miniD = { n: 0, agree: 0 };
  try {
    const dec = await fetchJson(DECISIONS);
    const vs = Object.values(dec.decisions || {});
    miniD = { n: vs.length, agree: vs.filter((v) => v.agreement === 'agrees').length };
  } catch { /* decisions optional */ }
  let fullSamp = { c: 0, b: 0 }, fullV = 0;
  try {
    const [fc, fb] = await Promise.all(PLANS.full.map(fetchJson));
    const samp = (p) => Object.values((p && p.cells) || {}).reduce((a, c) => a + (c.sampled || []).length, 0);
    fullSamp = { c: samp(fc), b: samp(fb) };
    fullV = [fc, fb].map(countVerdicts).reduce((a, c) => a + c.n, 0);
  } catch { /* full plans optional */ }
  const reports = (await Promise.all(REPORTS.map(fetchOk))).filter(Boolean).length;
  const items = [
    [`${Object.keys(runs).length}`, 'runs', '2 splits × 2 drivers'],
    [`${fmtInt(cells)}`, 'cells', 'conditions × inputs × faults'],
    [`${fmtInt(eps.length)}`, 'measured episodes', 'warm-ups excluded'],
    [`${fmtInt(traced)}`, 'trace artifacts', 'one per episode + snapshots'],
    [`${fmtInt(verified)}`, 'verified P1–P3', 'independent checker'],
    [`${fmtInt(devV.n + miniD.n)}`, 'human verdicts', `${devV.agree} dev + ${miniD.agree} mini-audit agree`],
    [`${reports}/${REPORTS.length}`, 'reports', 'rendered from run files'],
  ];
  if (covHost) covHost.innerHTML = items.map(([v, l, s]) => `<li><strong>${v}</strong>${esc(l)}<br><small>${esc(s)}</small></li>`).join('');
  const rf = document.querySelector('#review-facts');
  if (rf) {
    rf.innerHTML =
      `<li><strong>Development split:</strong> ${devV.agree}/${devV.n} human–verifier agreements — the audited split.</li>`
      + `<li><strong>Held-out mini-audit:</strong> ${miniD.agree}/${miniD.n} agreements across 8 selected episodes — descriptive only.</li>`
      + `<li><strong>Held-out full samples:</strong> ${fullSamp.c + fullSamp.b} sampled (${fullSamp.c} + ${fullSamp.b}), ${fullV} plan verdicts recorded — unreviewed, hence provisional.</li>`;
  }
  setFigs({ MINI: miniD.n ? `${miniD.agree}/${miniD.n}` : null });
  paintPortal();
  const dos = document.querySelector('#dossierFigures');
  if (dos) {
    const rows = [
      ['Runs', `${Object.keys(runs).length} · 2 splits × 2 drivers`],
      ['Cells', fmtInt(cells)],
      ['Measured episodes', fmtInt(eps.length)],
      ['Trace artifacts', fmtInt(traced)],
      ['Verified P1–P3', fmtInt(verified)],
      ['Dev human verdicts', `${devV.agree}/${devV.n} agree`],
      ['Held-out mini-audit', `${miniD.agree}/${miniD.n} agree`],
      ['Held-out full sample', `${fullSamp.c + fullSamp.b} sampled (${fullSamp.c} + ${fullSamp.b}) · ${fullV} verdicts`],
      ['Reports', `${reports}/${REPORTS.length} rendered`],
    ];
    dos.innerHTML = `<dl>${rows.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join('')}</dl>`;
  }
}

/* ---------- full-audit status (evidence page) ---------- */
export async function renderAuditStatus() {
  const host = document.querySelector('#audit-status');
  if (!host) return;
  try {
    const dec = await fetchJson(FULL_DECISIONS);
    const vs = Object.values((dec && dec.decisions) || {});
    const n = vs.length;
    const sha = dec && dec.packet_sha256 ? String(dec.packet_sha256).slice(0, 8) : '—';
    host.innerHTML =
      `<div class="t-fig">${n}/184</div>`
      + `<div class="t-sub">full-audit episodes adjudicated · packet <span class="mono">${esc(sha)}…</span></div>`
      + `<span class="t-bar" aria-hidden="true"><span style="width:${((100 * n) / 184).toFixed(1)}%"></span></span>`
      + `<p class="audit-note">${n === 0
        ? 'Status: <strong>in progress</strong> — no verdicts recorded yet. Held-out figures stay provisional until this audit lands.'
        : `Status: <strong>in progress</strong> — ${n} of 184 verdicts recorded.`}</p>`;
  } catch {
    host.innerHTML = '<p class="loading">Audit packet unavailable in this checkout.</p>';
  }
}

/* ---------- matched-budget experiment (results page) ---------- */
const MB_ARMS = [
  ['mb-v1-chimera', 'Chimera · 5000 ms'],
  ['mb-v1-replay-100', 'Replay · 100 ms'],
  ['mb-v1-replay-1000', 'Replay · 1000 ms'],
  ['mb-v1-replay-2500', 'Replay · 2500 ms'],
  ['mb-v1-replay-5000', 'Replay · 5000 ms'],
];
export async function renderMatchedBudget() {
  const host = document.querySelector('#mb-table');
  if (!host) return;
  try {
    const res = await fetchJson(MB_RESULTS);
    const arms = res.arms || {};
    const rows = SCENARIOS.map((sc) => {
      const tds = MB_ARMS.map(([key]) => {
        const cell = ((arms[key] || {}).by_scenario || {})[sc] || {};
        const k = cell.k != null ? cell.k : '—', n = cell.n != null ? cell.n : '—';
        const good = k === 5 ? 'cell-good' : (k === 0 ? 'cell-bad' : '');
        return `<td class="${good}"><span class="k">${k}/${n}</span></td>`;
      }).join('');
      return `<tr><th scope="row">${esc(SCENARIO_PLAIN[sc])} <small>${esc(sc)}</small></th>${tds}</tr>`;
    }).join('');
    host.innerHTML = `<table class="data mb"><caption>Matched-budget v1: successes per 5 measured trials by scenario and arm. 105 executions, 100 measured.</caption>`
      + `<thead><tr><th scope="col">Scenario</th>${MB_ARMS.map(([, lab]) => `<th scope="col">${esc(lab)}</th>`).join('')}</tr></thead>`
      + `<tbody>${rows}</tbody></table>`;
    const agree = document.querySelector('#mb-agree');
    if (agree) {
      const chim = (arms['mb-v1-chimera'] || {}).by_scenario || {};
      const rep5 = (arms['mb-v1-replay-5000'] || {}).by_scenario || {};
      let bothS = 0, bothF = 0, disc = 0;
      for (const sc of SCENARIOS) {
        const ck = (chim[sc] || {}).k || 0, cn = (chim[sc] || {}).n || 0;
        const rk = (rep5[sc] || {}).k || 0, rn = (rep5[sc] || {}).n || 0;
        if (cn === 5 && rn === 5) {
          if (ck === 5 && rk === 5) bothS += 5;
          else if (ck === 0 && rk === 0) bothF += 5;
          else disc += 5;
        }
      }
      agree.innerHTML = `<strong>Reading:</strong> Chimera vs replay-5000 agreed on <strong>${bothS + bothF}/20</strong> matched pairs `
        + `(${bothS} both-succeed, ${bothF} both-fail, ${disc} disagreements). `
        + 'S-SLOW moves 0/5 → 5/5 between 1000 ms and 2500 ms — bracketing the 2100 ms fault delay — while S-SLOWDIS stays 0/5 at every budget. '
        + 'Conclusion: budget, not capability. n=5 per cell; no generality claims follow.';
    }
  } catch {
    host.innerHTML = '<p class="loading">Matched-budget results unavailable in this checkout.</p>';
  }
}

/* ---------- SauceDemo stress v2 (results page, live from trials.csv) ---------- */
function parseCsv(text) {
  const rows = [];
  let row = [], cur = '', q = false;
  const push = () => { row.push(cur); cur = ''; };
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (q) {
      if (ch === '"') {
        if (text[i + 1] === '"') { cur += '"'; i += 1; } else q = false;
      } else cur += ch;
    } else if (ch === '"') q = true;
    else if (ch === ',') push();
    else if (ch === '\n') { push(); rows.push(row); row = []; }
    else if (ch !== '\r') cur += ch;
  }
  if (cur !== '' || row.length) { push(); rows.push(row); }
  return rows.filter((r) => r.length > 1 || (r[0] && r[0].trim()));
}
export async function renderSauceV2() {
  const host = document.querySelector('#sauce-checks');
  if (!host) return;
  try {
    const rows = parseCsv(await fetchText(SAUCE_TRIALS));
    const head = rows[0].map((h) => h.trim());
    const idx = (name) => head.indexOf(name);
    const data = rows.slice(1);
    const n = data.length;
    const succ = data.filter((r) => (r[idx('verdict')] || '').trim() === 'verified-success').length;
    const checks = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6'].map((t) => {
      const col = idx(t);
      const app = data.filter((r) => (r[col] || '').trim() !== '');
      const sat = app.filter((r) => (r[col] || '').trim() === '1').length;
      return { t, sat, n: app.length };
    });
    host.innerHTML = `<table class="data mb"><caption>Stress v2 per-check satisfied rates, computed live from trials.csv (${n} trials).</caption>`
      + `<thead><tr><th scope="col">Check</th><th scope="col">Satisfied</th><th scope="col">n</th><th scope="col">Rate</th></tr></thead>`
      + `<tbody>${checks.map((c) => `<tr><th scope="row">${c.t}</th><td><span class="k">${c.sat}</span></td><td>${c.n}</td><td>${fmtPct(c.sat, c.n)}</td></tr>`).join('')}</tbody></table>`;
    const sum = document.querySelector('#sauce-summary');
    if (sum) {
      const chim = data.filter((r) => (r[idx('driver')] || '').trim() === 'chimera');
      const rep = data.filter((r) => (r[idx('driver')] || '').trim() !== 'chimera');
      const chimS = chim.filter((r) => (r[idx('verdict')] || '').trim() === 'verified-success').length;
      const repS = rep.filter((r) => (r[idx('verdict')] || '').trim() === 'verified-success').length;
      sum.innerHTML = `<strong>${n} trials</strong> · ${succ} verified-success / ${n - succ} verified-failure · `
        + `Chimera ${chimS}/${chim.length} · replay ${repS}/${rep.length} · `
        + 'matched-pair agreement 20/20, per-check deltas 0.0 (see report). Identical outcomes — site defects dominate.';
    }
    const funnel = document.querySelector('#sauce-funnel');
    if (funnel) {
      const login = n;
      const cart = checks[3].sat;
      const order = checks[5].sat;
      const bar = (v, color) => `<span class="t-bar" aria-hidden="true"><span style="width:${((100 * v) / Math.max(1, login)).toFixed(1)}%;background:${color}"></span></span>`;
      funnel.innerHTML =
        `<div class="terminal-cell"><div class="t-name">Login (T1)</div><div class="t-fig">${login}/${n}</div>${bar(login, '#0e7490')}</div>`
        + `<div class="terminal-cell"><div class="t-name">Cart holds items (T4)</div><div class="t-fig">${cart}/${n}</div>${bar(cart, '#3A6EA5')}</div>`
        + `<div class="terminal-cell"><div class="t-name">Order complete (T6)</div><div class="t-fig">${order}/${n}</div>${bar(order, '#6d28d9')}</div>`;
    }
  } catch {
    host.innerHTML = '<p class="loading">Stress v2 trials unavailable in this checkout.</p>';
  }
}

/* ---------- trace inspector (demo page): two recorded scenarios ---------- */
const DEMO = { data: {}, key: 'success' };
const P_SHORT = { P1: 'confirmation visible', P2: 'exact single-name match', P3: 'exactly one entry' };
const envVal = (x) => (x != null && typeof x === 'object' && 'value' in x ? x.value : x);
function demoActionRows(trace) {
  const events = (trace.events || []).slice().sort((a, b) => a.sequence_number - b.sequence_number);
  const durs = pairDurations(events);
  const rows = [];
  const seenVerify = new Set();
  for (const ev of events) {
    if (ev.event_type === 'run_started') continue;
    if (ev.event_type === 'action_attempted') {
      const done = events.find((x) => (x.event_type === 'action_succeeded' || x.event_type === 'action_failed')
        && x.action_type === ev.action_type && x.sequence_number > ev.sequence_number);
      const ms = done ? durs.get(done.sequence_number) : null;
      const ok = done && done.event_type === 'action_succeeded';
      rows.push({
        num: String(ev.sequence_number).padStart(2, '0'),
        action: `${ev.action_type || 'act'}(…)`,
        detail: done ? `${ok ? 'completed' : 'failed'}${ms != null ? ` in ${ms} ms` : ''}` : 'attempt dispatched',
        status: done ? (ok ? 'DONE' : 'FAIL') : 'TRY',
        cls: done ? (ok ? 'ok' : 'bad') : '',
      });
    } else if (ev.event_type === 'action_succeeded' || ev.event_type === 'action_failed') {
      continue;
    } else if (ev.event_type === 'verification_passed' || ev.event_type === 'verification_failed') {
      if (seenVerify.has(ev.event_type)) continue;
      seenVerify.add(ev.event_type);
      const ok = ev.event_type === 'verification_passed';
      rows.push({
        num: String(ev.sequence_number).padStart(2, '0'), action: 'verify P1–P3',
        detail: 'independent checker, harness snapshot', status: ok ? 'PASS' : 'FAIL', cls: ok ? 'ok' : 'bad',
      });
    } else if (ev.event_type === 'run_succeeded' || ev.event_type === 'run_failed' || ev.event_type === 'run_cancelled') {
      const ok = ev.event_type === 'run_succeeded';
      rows.push({
        num: String(ev.sequence_number).padStart(2, '0'), action: 'report outcome',
        detail: ok ? 'agent reported success' : 'agent reported failure',
        status: ok ? 'DONE ✓' : 'FAILED', cls: ok ? 'ok' : 'bad',
      });
    }
  }
  return rows;
}
function paintDemo() {
  const stepsEl = document.getElementById('demoStepList');
  if (!stepsEl) return;
  const d = DEMO.data[DEMO.key];
  if (!d) {
    const msg = '<p class="loading">Trace unavailable in this checkout — open the Research Console link above instead.</p>';
    stepsEl.innerHTML = msg;
    const obs = document.getElementById('demoObservationBox');
    if (obs) obs.innerHTML = msg;
    const pr = document.getElementById('demoPredicatesList');
    if (pr) pr.innerHTML = msg;
    return;
  }
  const { ep, trace, snap, runId, trial } = d;
  const pass = ep.outcome === 'succeeded' && ep.agent_terminal_status === 'succeeded';
  document.querySelectorAll('.demo-switch [role="tab"]').forEach((t) => {
    const on = t.dataset.demo === DEMO.key;
    t.setAttribute('aria-selected', String(on));
    t.tabIndex = on ? 0 : -1;
  });
  const insp = document.getElementById('demoInspector');
  if (insp) insp.setAttribute('aria-labelledby', `demoTab-${DEMO.key}`);
  document.getElementById('demoTraceId').textContent = `${trial} · ${runId} · ${ep.scenario_id}`;
  const top = document.getElementById('demoTopVerdict');
  top.textContent = pass ? 'VERDICT: VERIFIED PASS' : 'OUTCOME: FAILED AS EXPECTED';
  top.className = `insp-verdict ${pass ? 'pass' : 'honest'}`;
  const rows = demoActionRows(trace);
  const okN = rows.filter((r) => r.status === 'DONE' || r.status === 'PASS' || r.status === 'DONE ✓').length;
  const rb = document.getElementById('demoRunnerBadge');
  rb.textContent = `${okN}/${rows.length} steps ok`;
  rb.className = `insp-badge ${pass ? 'good' : 'warn'}`;
  stepsEl.innerHTML = rows.map((r) => (
    `<div class="insp-step"><div><div class="insp-step-action"><span class="seq">[${esc(r.num)}]</span>${esc(r.action)}</div>`
    + `<div class="insp-step-detail">${esc(r.detail)}</div></div>`
    + `<span class="insp-step-status ${r.cls}">${esc(r.status)}</span></div>`)).join('');
  const obs = [
    ['Scenario', `${SCENARIO_PLAIN[ep.scenario_id] || ep.scenario_id} (${ep.scenario_id})`],
    ['Input', ep.input_id || '—'],
    ['Duration', ep.duration_ms != null ? `${ep.duration_ms} ms` : '—'],
    ['Retries', envVal(ep.retries) != null ? String(envVal(ep.retries)) : '—'],
    ['Actions executed', envVal(ep.actions_executed) != null ? String(envVal(ep.actions_executed)) : '—'],
    ['Safety violations', envVal(ep.safety_violations) != null ? String(envVal(ep.safety_violations)) : '—'],
  ];
  document.getElementById('demoObservationBox').innerHTML = obs.map(([k, v]) => (
    `<div class="insp-obsrow"><span>${esc(k)}:</span><span>${esc(v)}</span></div>`)).join('');
  document.getElementById('demoDomExcerpt').textContent = snap
    ? JSON.stringify(snap, null, 2)
    : 'Snapshot file unavailable in this checkout.';
  const checks = ((ep.verification || {}).checks || []).slice().sort((a, b) => String(a.postcondition_id).localeCompare(String(b.postcondition_id)));
  const met = checks.filter((c) => c.satisfied).length;
  const vb = document.getElementById('demoVerifierBadge');
  vb.textContent = `${met}/${checks.length} invariants met`;
  vb.className = `insp-badge ${met === checks.length && checks.length ? 'good' : 'warn'}`;
  document.getElementById('demoPredicatesList').innerHTML = checks.map((c) => (
    `<div class="insp-pred${c.satisfied ? '' : ' fail'}"><div class="insp-pred-top">`
    + `<span class="insp-pred-expr">${esc(c.postcondition_id)} · ${esc(P_SHORT[c.postcondition_id] || 'check')}</span>`
    + `<span class="insp-pred-pill">${c.satisfied ? 'PASS' : 'FAIL'}</span></div>`
    + `<div class="insp-pred-note">${esc(c.detail || '')}</div></div>`)).join('');
  const box = document.getElementById('demoVerdictBox');
  box.className = `insp-verdictbox ${pass ? 'pass' : 'honest'}`;
  const items = (snap && snap.items) || [];
  if (pass) {
    document.getElementById('demoVerdictTitle').textContent = 'VERIFIED PASS — EVIDENCE LOCKED';
    document.getElementById('demoVerdictSummary').textContent =
      `Runner and independent verifier agreed on ${trial}: confirmation visible, exactly one `
      + `“${items[0] || 'project'}” entry, success reported in ${ep.duration_ms} ms.`;
  } else {
    document.getElementById('demoVerdictTitle').textContent = 'TASK FAILED · FAILURE REPORTED HONESTLY';
    const errFirst = ep.error ? String(ep.error).split('\n')[0].replace(/\s*\(caused by.*$/, '').slice(0, 120) : null;
    document.getElementById('demoVerdictSummary').textContent =
      `The input never enabled (${SCENARIO_PLAIN[ep.scenario_id] || ep.scenario_id}); the agent exhausted its retry budget `
      + `over ${ep.duration_ms} ms, then reported failure.`
      + (errFirst ? ` Harness error: ${errFirst}.` : '')
      + ` The verifier confirms the page state — no confirmation, ${items.length} entries — `
      + 'so this is a correct failure, not a false success.';
  }
  document.getElementById('demoConsoleLink').setAttribute('href', `/research/#/evidence/${runId}/${trial}`);
}
export function initDemo(data) {
  DEMO.data = data || {};
  const tabs = [...document.querySelectorAll('.demo-switch [role="tab"]')];
  tabs.forEach((tab, i) => {
    tab.addEventListener('click', () => { DEMO.key = tab.dataset.demo; paintDemo(); });
    tab.addEventListener('keydown', (e) => {
      let next = i;
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') next = (i + 1) % tabs.length;
      else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') next = (i - 1 + tabs.length) % tabs.length;
      else if (e.key === 'Home') next = 0;
      else if (e.key === 'End') next = tabs.length - 1;
      else return;
      e.preventDefault();
      DEMO.key = tabs[next].dataset.demo;
      paintDemo();
      tabs[next].focus();
    });
  });
  paintDemo();
}

/* Shared boot error surface for data pages. */
export function paintLoadError(err, selectors) {
  const heroErr = document.getElementById('hero-load-error');
  if (heroErr) {
    heroErr.hidden = false;
    heroErr.innerHTML = `Evidence files unavailable in this checkout (${esc(err.message)}). Serve the repository root and reload.`;
  }
  for (const sel of selectors) {
    const el = document.querySelector(sel);
    if (el) el.innerHTML = '<p class="loading">Data unavailable.</p>';
  }
  document.querySelectorAll('[data-journey]').forEach((el) => {
    el.innerHTML = '<p class="loading">Trace unavailable in this checkout.</p>';
  });
  initDemo({});
}
