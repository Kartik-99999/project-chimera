/* Evidence Inspector: one episode, fully expanded from stored files. */
import { getState, getRun, mVal, isHarnessError, isFalseSuccess, verdictIndex, rootPath,
  esc, fmtInt, fmtMs, baselineLabel } from '../data.js';
import { link } from '../app.js';
import { pageHead, outcomePill, baselineTag, pill, emptyState, kvList, metricCell, jsonView, art, globes, secHead } from '../components.js';
import { scopeStrip } from '../charts.js';
import { buildScope } from '../viz/scopeModel.js';
import { attachTip } from '../viz/tooltip.js';

async function fetchMaybe(path) {
  try {
    const res = await fetch(rootPath(path), { cache: 'no-store' });
    if (!res.ok) return { ok: false, error: `HTTP ${res.status}` };
    return { ok: true, data: await res.json() };
  } catch (err) { return { ok: false, error: String(err && err.message || err) }; }
}

function outcomeExplainer(ep, checks) {
  const lines = [];
  const reported = ep.agent_terminal_status;
  lines.push(`The agent's persisted trace reports terminal status <strong>${esc(reported)}</strong>; the recorded outcome is <strong>${esc(ep.outcome)}</strong>.`);
  if (isHarnessError(ep)) {
    lines.push(`A harness error occurred (<code>${esc(ep.error)}</code>), so trace-derived metrics are unavailable with reasons rather than zero.`);
    return lines;
  }
  const v = ep.verification || {};
  if (v.status !== 'verified') {
    lines.push(`Independent verification is <strong>unavailable</strong> (${esc(v.unavailable_reason || 'no reason recorded')}), so the outcome rests on the trace terminal alone and the episode is excluded from false-success classification.`);
    return lines;
  }
  const all = v.all_satisfied;
  lines.push(`The independent verifier evaluated P1–P3 from a harness-captured snapshot: <strong>${all ? 'all satisfied' : 'not all satisfied'}</strong>.`);
  if (reported === 'succeeded' && all === false) {
    lines.push(`<strong>False success:</strong> the agent claimed success while the page state failed postconditions.`);
  } else if (reported === 'succeeded' && all === true) {
    lines.push(`Claim and page state agree — a verified success.`);
  } else if (reported !== 'succeeded') {
    lines.push(`The agent reported <strong>${esc(reported)}</strong>, so this episode cannot be a false success regardless of page state.`);
  }
  if (checks && checks.length) {
    lines.push(`A human adjudicated this episode in ${checks.length} plan(s) — see Human review below.`);
  }
  return lines;
}

/* Human-vs-verifier agreement: true/false, or null when the episode
 * was marked unauditable or no check comparison is possible. */
function verdictAgree(verdict, ep) {
  if (!verdict || verdict.verdict === 'unauditable' || !verdict.checks) return null;
  const vc = (ep.verification && ep.verification.checks || []).reduce((m, c) => ({ ...m, [c.postcondition_id]: c.satisfied }), {});
  const keys = Object.keys(verdict.checks);
  return keys.every((k) => verdict.checks[k] === vc[k]) && keys.length === Object.keys(vc).length;
}

function checksTable(ep) {
  const v = ep.verification || {};
  if (v.status !== 'verified') {
    return `<p>Verification status: ${pill('dim', 'unavailable')} <span style="color:var(--ink-3)">${esc(v.unavailable_reason || '')}</span></p>`;
  }
  const rows = (v.checks || []).map((c) => (
    `<tr><td class="mono">${esc(c.postcondition_id)}</td>`
    + `<td>${c.satisfied ? pill('ok', 'satisfied') : pill('bad', 'not satisfied')}</td>`
    + `<td class="mono" style="font-size:11.5px;overflow-wrap:anywhere">${esc(c.evidence_reference || '')}</td>`
    + `<td style="font-size:12.5px">${esc(c.detail || '')}</td></tr>`)).join('');
  return `<div class="table-wrap"><table class="data"><thead><tr><th>Check</th><th>Verdict</th><th>Evidence reference</th><th>Detail</th></tr></thead><tbody>${rows}</tbody></table></div>
    <p style="color:var(--ink-3);font-size:12.5px">Verifier version: <code>${esc(v.verifier_version || 'unrecorded')}</code> · conjunction: <strong>${v.all_satisfied ? 'satisfied' : 'not satisfied'}</strong></p>`;
}

export function traceTimeline(trace) {
  if (!trace || !Array.isArray(trace.events)) return '';
  const items = trace.events.map((ev) => {
    const cls = ev.action_outcome === 'failure' ? 'fail' : (ev.action_outcome === 'ok' ? 'ok' : '');
    const head = `#${ev.sequence_number} · ${esc(ev.event_type)}${ev.action_type ? ` · ${esc(ev.action_type)}` : ''}`;
    const sub = `${esc(ev.timestamp || '')}${ev.action_outcome ? ` · outcome: ${esc(ev.action_outcome)}` : ''}`;
    const extra = [];
    if (ev.error_details) extra.push(`<div><strong>Error:</strong> <code>${esc(typeof ev.error_details === 'string' ? ev.error_details : JSON.stringify(ev.error_details))}</code></div>`);
    if (ev.evidence_references && ev.evidence_references.length) {
      extra.push(`<div><strong>Evidence:</strong> ${ev.evidence_references.map((r) => `<code>${esc(typeof r === 'string' ? r : JSON.stringify(r))}</code>`).join(' ')}</div>`);
    }
    return `<li class="${cls}" data-text="${esc(`${ev.event_type} ${ev.action_type || ''} ${ev.action_outcome || ''} ${JSON.stringify(ev.error_details || '')}`.toLowerCase())}">`
      + `<span class="t-dot" aria-hidden="true"></span><div class="t-head">${head}</div><div class="t-sub">${sub}</div>${extra.join('')}</li>`;
  }).join('');
  return `<div class="field" style="margin-bottom:10px"><label for="trace-search">Filter ${trace.events.length} steps</label>`
    + `<input type="search" id="trace-search" placeholder="e.g. click, failed, verification…"></div>`
    + `<ol class="timeline" id="trace-timeline">${items}</ol>`;
}

export function replaySteps(report, { neutral = false } = {}) {
  if (!report || !Array.isArray(report.steps)) return '';
  const items = report.steps.map((st, i) => {
    const ok = st.outcome === 'ok';
    return `<li class="${ok ? 'ok' : 'fail'}"><span class="t-dot" aria-hidden="true"></span>`
      + `<div class="t-head">step ${i + 1} · ${esc(st.step || '?')} → <code>${esc(st.target || '')}</code></div>`
      + `<div class="t-sub">outcome: ${esc(st.outcome || '?')}${st.error_type ? ` · ${esc(st.error_type)}` : ''}</div></li>`;
  }).join('');
  // Neutral wording for blinded review: the step SHAPE still differs
  // by driver (a documented residual), but the label must not name it.
  const kind = neutral ? 'Single-attempt execution' : 'Single-attempt replay';
  return `<ol class="timeline">${items}</ol>
    <p style="color:var(--ink-3);font-size:12.5px">${kind}: each fixed step runs at most once. Attempts per step: ${esc(String(report.attempts_per_step ?? 'unrecorded'))}.</p>`;
}

export function snapshotView(d) {
  const items = Array.isArray(d.items) ? d.items : [];
  return kvList([
    ['confirmation_visible', `<strong>${esc(String(d.confirmation_visible))}</strong>`],
    [`items (${items.length})`, items.length ? `<ol style="margin:0;padding-left:20px">${items.map((x) => `<li><code>${esc(typeof x === 'string' ? x : JSON.stringify(x))}</code></li>`).join('')}</ol>` : '<span style="color:var(--ink-3)">empty list</span>'],
    ['captured_at', esc(d.captured_at || '?')],
    ['run_id', `<code>${esc(d.run_id || '')}</code>`],
  ]) + jsonView(d, 'Raw snapshot JSON');
}

export function recordTable(records) {
  if (!records || !records.length) return '<p style="color:var(--ink-3)">No action records attached.</p>';
  const keys = [...new Set(records.flatMap((r) => Object.keys(r || {})))].slice(0, 8);
  const rows = records.map((r) => `<tr>${keys.map((k) => {
    const v = r[k];
    const s = v == null ? '—' : (typeof v === 'object' ? JSON.stringify(v) : String(v));
    return `<td class="mono" style="font-size:11.5px;max-width:260px;overflow:hidden;text-overflow:ellipsis" title="${esc(s)}">${esc(s.length > 80 ? `${s.slice(0, 80)}…` : s)}</td>`;
  }).join('')}</tr>`).join('');
  return `<div class="table-wrap"><table class="data"><thead><tr>${keys.map((k) => `<th>${esc(k)}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table></div>`;
}

export async function pageEvidence(el, { params }) {
  const [runId, trialId] = params;
  const run = runId ? getRun(runId) : null;
  const ep = run && run.data ? (run.data.episodes || []).find((e) => e.trial_id === trialId) : null;
  if (!run || !ep) {
    el.innerHTML = pageHead('Evidence Inspector', [['Atlas', link('atlas')], ['Not found']]) + emptyState(
      'Episode not found',
      runId && trialId
        ? `No episode <code>${esc(trialId)}</code> in run <code>${esc(runId)}</code> among loaded evidence. It may belong to an unloadable run file.`
        : 'Give a run and trial, e.g. from the Atlas.',
      `<p><a class="btn" href="${link('atlas')}">Open Atlas</a></p>`);
    return;
  }
  const verdicts = verdictIndex().get(`${runId}::${trialId}`) || [];
  const auditCards = verdicts.length ? verdicts.map((v) => {
    const verdict = v.verdict;
    let body;
    if (verdict && verdict.verdict === 'unauditable') {
      body = `${pill('warn', 'unauditable')} <span>${esc(verdict.reason || '')}</span>`;
    } else if (verdict && verdict.checks) {
      const agree = verdictAgree(verdict, ep);
      body = `${agree ? pill('ok', 'agrees with verifier') : pill('bad', 'disagrees with verifier')}
        <code>${esc(Object.entries(verdict.checks).map(([k, val]) => `${k}=${val}`).join(' '))}</code>`;
    } else {
      body = `<code>${esc(JSON.stringify(verdict))}</code>`;
    }
    return `<div class="finding"><span class="marker" aria-hidden="true">◆</span><span>${esc(v.planKind)} plan · cell <code>${esc(v.cellKey)}</code><br>${body}</span></div>`;
  }).join('') : '<p style="color:var(--ink-3)">This episode carries no recorded human verdict in any loaded audit plan. Absence of a verdict is not agreement.</p>';

  const vstat = ep.verification || {};
  const vPill = vstat.status === 'verified'
    ? `<span class="glass"><span class="dot" style="background:#8fb4ff"></span>verified · ${(vstat.checks || []).filter((c) => c.satisfied).length}/${(vstat.checks || []).length} satisfied</span>`
    : `<span class="glass"><span class="dot" style="background:#fbbf24"></span>verification unavailable</span>`;
  const navy = `<div class="navy">${globes()}`
    + `<p class="sub" style="margin-bottom:4px">Trial ${esc(trialId)} · ${esc(ep.scenario_id)} / ${esc(ep.input_id)} · ${esc(baselineLabel(ep.baseline))} · ${esc(run.split || '')}</p>`
    + `<h2>${esc(ep.outcome === 'succeeded' ? 'Succeeded' : ep.outcome)} in ${esc(fmtMs(ep.duration_ms))}</h2>`
    + `<p><span class="glass"><span class="dot" style="background:${ep.outcome === 'succeeded' ? '#6ee7a0' : '#f87171'}"></span>${esc(ep.outcome)}</span>${vPill}`
    + `<span class="glass"><span class="dot" style="background:#c4b5fd"></span>${isFalseSuccess(ep) ? 'false success' : 'not a false success'}</span></p></div>`;
  el.innerHTML = pageHead(`Trial ${trialId}`, [
    ['Atlas', link('atlas', [], { run: runId })],
    [runId.replace('20261028-', ''), link('atlas', [], { run: runId })],
    [trialId],
  ], '', {
    kicker: `#/evidence/${esc(runId)}/${esc(trialId)}`,
    lede: 'One episode, fully expanded from stored files — record, outcome narrative, verification, oscilloscope, trace, snapshot, actions, and human review.',
    meta: `${outcomePill(ep.outcome, isHarnessError(ep))} ${baselineTag(ep.baseline)}`,
  }) + navy + secHead('Evidence Inspector', 'Episode record · outcome narrative · P1–P3 · lazy-loaded artifacts')
    + `<div class="grid g2"><div class="card"><h2>Episode record</h2>
      <p>${outcomePill(ep.outcome, isHarnessError(ep))} ${baselineTag(ep.baseline)} ${isFalseSuccess(ep) ? pill('bad', 'false success') : ''}</p>
      ${kvList([
        ['Run', `<code>${esc(runId)}</code>`],
        ['Cell', `<code>${esc(ep.scenario_id)} / ${esc(ep.input_id)}</code> <a href="${link('atlas', [], { scenario: ep.scenario_id, search: ep.input_id })}">cell episodes →</a>`],
        ['Started / completed', `${esc(ep.started_at || '?')} → ${esc(ep.completed_at || '?')}`],
        ['Duration', fmtMs(ep.duration_ms)],
        ['Agent terminal status', `<code>${esc(ep.agent_terminal_status)}</code>`],
        ['Retries', metricCell(ep.retries)],
        ['Actions executed', metricCell(ep.actions_executed)],
        ['Unauthorized actions', metricCell(ep.unauthorized_actions)],
        ['Safety violations', metricCell(ep.safety_violations)],
        ['Failure category', ep.failure_category ? `<code>${esc(ep.failure_category)}</code>` : '<span style="color:var(--ink-3)">null — the runner never sets failure categories; group by outcome and error instead</span>'],
        ['Error', ep.error ? `<code>${esc(ep.error)}</code>` : '<span style="color:var(--ink-3)">none</span>'],
        ['Trace artifact', ep.trace_artifact ? `<code>${esc(ep.trace_artifact)}</code>` : '<span style="color:var(--ink-3)">none recorded</span>'],
      ])}
    </div>
    <div class="card"><h2>Why this outcome</h2>${outcomeExplainer(ep, verdicts).map((t) => `<p>${t}</p>`).join('')}</div></div>
    <div class="card" id="ev-checks">${art(2)}<h2>Independent verification (P1–P3)</h2>${checksTable(ep)}</div>
    <div class="card" id="ev-scope"><h2>Episode oscilloscope</h2><p style="color:var(--ink-3)">Loading lanes…</p></div>
    <div class="card" id="ev-trace"><h2>Execution trace</h2><p style="color:var(--ink-3)">Loading ${esc(ep.trace_artifact || 'artifact')}…</p></div>
    <div class="card" id="ev-snapshot"><h2>Captured page snapshot</h2><p style="color:var(--ink-3)">Loading…</p></div>
    <div class="card" id="ev-actions"><h2>Observed actions</h2><p style="color:var(--ink-3)">Loading…</p></div>
    <div class="card" id="ev-human"><h2>Human review</h2>${auditCards}</div>`;

  // Trace / driver report. Loaded artifacts are stashed for the oscilloscope.
  let traceData = null, actionsData = null, snapshotOk = false;
  const traceHost = el.querySelector('#ev-trace');
  if (!ep.trace_artifact) {
    traceHost.innerHTML = '<h2>Execution trace</h2>' + emptyState('No artifact recorded', 'This episode names no trace or driver-report file.');
  } else {
    const t = await fetchMaybe(ep.trace_artifact);
    if (!t.ok) {
      traceHost.innerHTML = `<h2>Execution trace</h2><div class="banner warn"><strong>Artifact unreadable:</strong> <code>${esc(ep.trace_artifact)}</code> (${esc(t.error)}). The file may be missing from this checkout.</div>`;
    } else if (t.data.schema === 'baseline-a-replay/1' || Array.isArray(t.data.steps)) {
      traceData = t.data;
      traceHost.innerHTML = `<h2>Replay driver report</h2><p>Terminal: ${outcomePill(t.data.terminal_status)} <span style="color:var(--ink-3)">schema <code>${esc(t.data.schema || '?')}</code> · run <code>${esc(t.data.run_id || '')}</code></span></p>${replaySteps(t.data)}${jsonView(t.data, 'Raw driver report')}`;
    } else {
      traceData = t.data;
      traceHost.innerHTML = `<h2>Execution trace</h2><p>Terminal: ${outcomePill(t.data.terminal_status)} <span style="color:var(--ink-3)">${t.data.event_count || (t.data.events || []).length} events · run <code>${esc(t.data.run_id || '')}</code></span></p>${traceTimeline(t.data)}${jsonView(t.data, 'Raw trace JSON')}`;
      const search = traceHost.querySelector('#trace-search');
      if (search) search.addEventListener('input', () => {
        const q = search.value.trim().toLowerCase();
        traceHost.querySelectorAll('#trace-timeline li').forEach((li) => {
          li.style.display = !q || (li.dataset.text || '').includes(q) ? '' : 'none';
        });
      });
    }
  }
  // Snapshot + actions are siblings of the trace artifact by harness convention.
  const sib = (suffix) => {
    if (!ep.trace_artifact) return null;
    const i = ep.trace_artifact.lastIndexOf('/');
    const dir = i >= 0 ? ep.trace_artifact.slice(0, i + 1) : '';
    const base = (i >= 0 ? ep.trace_artifact.slice(i + 1) : ep.trace_artifact).split('.')[0];
    return `${dir}${base}${suffix}`;
  };
  const snapHost = el.querySelector('#ev-snapshot');
  const snapPath = sib('.snapshot.json');
  if (!snapPath) { snapHost.innerHTML = '<h2>Captured page snapshot</h2><p style="color:var(--ink-3)">No trace artifact, so no sibling snapshot path exists.</p>'; }
  else {
    const s = await fetchMaybe(snapPath);
    if (!s.ok) {
      snapHost.innerHTML = `<h2>Captured page snapshot</h2><div class="banner warn"><strong>Snapshot unreadable:</strong> <code>${esc(snapPath)}</code> (${esc(s.error)}).</div>`;
    } else {
      snapshotOk = true;
      snapHost.innerHTML = '<h2>Captured page snapshot</h2>' + snapshotView(s.data);
    }
  }
  const actHost = el.querySelector('#ev-actions');
  const actPath = sib('.actions.json');
  if (!actPath) { actHost.innerHTML = '<h2>Observed actions</h2><p style="color:var(--ink-3)">No trace artifact, so no sibling action-log path exists.</p>'; }
  else {
    const a = await fetchMaybe(actPath);
    if (!a.ok) {
      actHost.innerHTML = `<h2>Observed actions</h2><div class="banner warn"><strong>Action log unreadable:</strong> <code>${esc(actPath)}</code> (${esc(a.error)}).</div>`;
    } else {
      actionsData = a.data;
      const d = a.data;
      actHost.innerHTML = `<h2>Observed actions</h2><p style="color:var(--ink-3)">Observer attached: <strong>${esc(String(d.attached))}</strong> · log complete: <strong>${esc(String(d.complete))}</strong> · run <code>${esc(d.run_id || '')}</code></p>${recordTable(d.records)}${jsonView(d, 'Raw action log')}`;
    }
  }

  // Oscilloscope: logic-analyzer lanes over the loaded artifacts.
  // Stored traces are tiny (≤10 events, ≤7 records), so every mark is
  // rendered directly — virtualization is unnecessary at this size.
  const scopeHost = el.querySelector('#ev-scope');
  const hv = verdicts.map((v) => ({ planKind: v.planKind, cellKey: v.cellKey, agrees: verdictAgree(v.verdict, ep) }));
  const scope = buildScope({ trace: traceData, actions: actionsData, snapshotOk, verification: ep.verification, verdicts: hv });
  const SOURCES = {
    trace: ['#ev-trace', 'Execution trace'], replay: ['#ev-trace', 'Replay driver report'],
    actions: ['#ev-actions', 'Observed actions'], checks: ['#ev-checks', 'Independent verification'],
    human: ['#ev-human', 'Human review'], snapshot: ['#ev-snapshot', 'Captured page snapshot'],
  };
  const timeCaption = scope.timeSpan.spanMs != null
    ? `Trace spans <code>${esc(scope.timeSpan.start)}</code> → <code>${esc(scope.timeSpan.end)}</code> (${fmtInt(scope.timeSpan.spanMs)} ms from recorded timestamps).`
    : `Time span unavailable (${esc(scope.timeSpan.unavailable)}); positions use sequence numbers only.`;
  let px = 48;
  const reduced = typeof window !== 'undefined' && window.matchMedia
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function drawScope() {
    const strip = scopeStrip({ lanes: scope.lanes, pxPerStep: px, id: `oscilloscope ${trialId}` });
    scopeHost.innerHTML = `<h2>Episode oscilloscope</h2>
      <p style="color:var(--ink-2)">Logic-analyzer lanes over recorded events. Each lane keeps its own coordinate — trace and observer sequences are independent. ${timeCaption}</p>
      <div class="scope-controls" role="group" aria-label="Strip zoom">
        <button class="btn" data-zoom="out">− zoom out</button>
        <button class="btn" data-zoom="in">+ zoom in</button>
        <button class="btn" data-zoom="reset">reset</button>
      </div>
      <div class="table-wrap" tabindex="0" aria-label="Oscilloscope strip, scrollable">${strip.svg}</div>
      <div id="scope-detail"><p style="color:var(--ink-3)">Select a mark to inspect its recorded fields. The timeline and tables below list the same records.</p></div>`;
    scopeHost.querySelectorAll('[data-zoom]').forEach((b) => b.addEventListener('click', () => {
      const z = b.dataset.zoom;
      px = z === 'in' ? Math.min(120, px + 24) : z === 'out' ? Math.max(24, px - 24) : 48;
      drawScope();
    }));
    const detail = scopeHost.querySelector('#scope-detail');
    const marks = [...scopeHost.querySelectorAll('.scope-event')];
    marks.forEach((g) => {
      const fire = () => {
        const lane = scope.lanes.find((l) => l.id === g.dataset.lane);
        const idx = Number(g.dataset.idx);
        const mark = lane && lane.marks[idx];
        if (!mark) return;
        const [href, label] = SOURCES[mark.target.kind] || ['#ev-trace', 'Evidence'];
        detail.innerHTML = `<p class="scope-pos">Mark ${idx + 1} of ${lane.marks.length} on lane “${esc(lane.title)}” · coordinate ${esc(lane.coord)}</p>`
          + `<h3 style="font-size:13px;margin:10px 0 6px">${esc(mark.title)}</h3>`
          + kvList(mark.detail.map(([k, v]) => [k, `<code>${esc(v)}</code>`]))
          + `<p><a href="${href}">source: ${esc(label)} ↓</a></p>`;
        scopeHost.querySelectorAll('.scope-event').forEach((o) => o.classList.toggle('sel', o === g));
        el.querySelectorAll('.timeline li.scope-hi').forEach((li) => li.classList.remove('scope-hi'));
        if (mark.target.kind === 'trace') {
          const li = traceHost.querySelectorAll('#trace-timeline li')[mark.target.index];
          if (li) {
            li.classList.add('scope-hi');
            if (li.scrollIntoView) li.scrollIntoView({ block: 'nearest', behavior: reduced ? 'auto' : 'smooth' });
          }
        }
      };
      g.addEventListener('click', fire);
      g.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fire(); }
        else if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
          e.preventDefault();
          const at = marks.indexOf(g);
          const next = marks[at + (e.key === 'ArrowRight' ? 1 : -1)];
          if (next) { next.focus(); next.dispatchEvent(new Event('scope:select')); }
        }
      });
      g.addEventListener('scope:select', fire);
      attachTip(g, g.dataset.tip);
    });
  }
  drawScope();
}
