/* Episode Oscilloscope data model (DOM-free; unit-tested).
 * Builds logic-analyzer lanes from a trace (or replay report),
 * observer action log, snapshot presence, verifier checks, and human
 * verdicts. Each lane keeps its own coordinate: trace sequence
 * numbers, observer sequence numbers, replay step indexes, or
 * categorical slots — never mixed on one axis. No values invented:
 * missing timestamps, sequences, and verdicts stay explicit.
 */

export function traceKind(ev) {
  const t = ev.event_type || '';
  if (ev.action_outcome === 'failure') return 'fail';
  if (t.startsWith('verification')) return 'verify';
  if (t.startsWith('run_')) return 'run';
  if (ev.action_outcome === 'ok') return 'ok';
  return 'info';
}

export function actionKind(rec) {
  if (rec.outcome !== 'ok') return 'fail';
  if (rec.policy != null && rec.policy !== 'allowed') return 'policy';
  return 'ok';
}

function str(v) {
  if (v == null) return '—';
  return typeof v === 'object' ? JSON.stringify(v) : String(v);
}

/* verdicts: [{ planKind, cellKey, agrees }] where agrees is
 * true/false/null (null = unauditable or uncomputable). */
export function buildScope({ trace, actions, snapshotOk, verification, verdicts = [] }) {
  const lanes = [];
  const isReplay = trace && (trace.schema === 'baseline-a-replay/1' || Array.isArray(trace.steps));
  if (trace && Array.isArray(trace.events)) {
    lanes.push({
      id: 'trace', title: 'Trace events', coord: 'trace sequence_number',
      marks: trace.events.map((ev, i) => ({
        x: Number.isFinite(Number(ev.sequence_number)) ? Number(ev.sequence_number) : i + 1,
        xLabel: String(ev.sequence_number ?? `#${i + 1} (no sequence_number)`),
        kind: traceKind(ev),
        title: `#${ev.sequence_number ?? i + 1} ${ev.event_type || '?'}${ev.action_type ? ` · ${ev.action_type}` : ''}${ev.action_outcome ? ` · ${ev.action_outcome}` : ''}`,
        detail: [
          ['Sequence', str(ev.sequence_number)], ['Timestamp', str(ev.timestamp)],
          ['Event', str(ev.event_type)], ['Action', str(ev.action_type)],
          ['Outcome', str(ev.action_outcome)], ['Error', str(ev.error_details)],
          ['Evidence refs', Array.isArray(ev.evidence_references) ? str(ev.evidence_references.length) : str(ev.evidence_references)],
        ],
        target: { kind: 'trace', index: i },
      })),
    });
  } else if (isReplay) {
    lanes.push({
      id: 'replay', title: 'Replay steps', coord: 'step index (no recorded sequence numbers)',
      marks: (trace.steps || []).map((st, i) => ({
        x: i + 1, xLabel: `step ${i + 1}`, kind: st.outcome === 'ok' ? 'ok' : 'fail',
        title: `step ${i + 1} · ${st.step || '?'} → ${st.target || '?'} · ${st.outcome || '?'}`,
        detail: [['Step', str(st.step)], ['Target', str(st.target)], ['Outcome', str(st.outcome)], ['Error type', str(st.error_type)]],
        target: { kind: 'replay', index: i },
      })),
    });
  }
  if (actions && Array.isArray(actions.records)) {
    lanes.push({
      id: 'actions', title: 'Observed actions', coord: 'observer sequence',
      marks: actions.records.map((r, i) => ({
        x: Number.isFinite(Number(r.seq)) ? Number(r.seq) : i + 1,
        xLabel: String(r.seq ?? `#${i + 1} (no seq)`),
        kind: actionKind(r),
        title: `obs #${r.seq ?? i + 1} · ${r.action_type || '?'} · ${r.outcome || '?'}${r.policy ? ` · policy ${r.policy}` : ''}`,
        detail: [
          ['Observer seq', str(r.seq)], ['Action', str(r.action_type)],
          ['Target', str(r.target_summary || r.target)], ['Outcome', str(r.outcome)],
          ['Error type', str(r.error_type)], ['Policy', str(r.policy)],
          ['Policy reason', str(r.policy_reason)], ['Elapsed', r.elapsed_ms == null ? '—' : `${r.elapsed_ms} ms`],
        ],
        target: { kind: 'actions', index: i },
      })),
    });
  }
  const verdictMarks = [];
  const v = verification || {};
  if (v.status === 'verified' && Array.isArray(v.checks)) {
    v.checks.forEach((c, i) => verdictMarks.push({
      x: i + 1, xLabel: c.postcondition_id || `check ${i + 1}`,
      kind: c.satisfied ? 'ok' : 'fail',
      title: `${c.postcondition_id || '?'}: ${c.satisfied ? 'satisfied' : 'NOT satisfied'} — ${c.detail || c.evidence_reference || 'no detail'}`,
      detail: [['Check', str(c.postcondition_id)], ['Satisfied', str(c.satisfied)],
        ['Evidence', str(c.evidence_reference)], ['Detail', str(c.detail)]],
      target: { kind: 'checks', index: i },
    }));
  } else {
    verdictMarks.push({
      x: 1, xLabel: 'verifier', kind: 'missing',
      title: `Independent verification unavailable: ${v.unavailable_reason || 'no reason recorded'}`,
      detail: [['Status', str(v.status)], ['Reason', str(v.unavailable_reason)]],
      target: { kind: 'checks', index: -1 },
    });
  }
  verdicts.forEach((hv, i) => verdictMarks.push({
    x: verdictMarks.length + 1, xLabel: `human (${hv.planKind || 'plan'})`,
    kind: hv.agrees === true ? 'ok' : hv.agrees === false ? 'disagree' : 'unau',
    title: hv.agrees == null ? `Human verdict (${hv.planKind || '?'}, ${hv.cellKey || '?'}): unauditable or uncomputable`
      : `Human verdict (${hv.planKind || '?'}, ${hv.cellKey || '?'}): ${hv.agrees ? 'agrees' : 'DISAGREES'} with verifier`,
    detail: [['Plan', str(hv.planKind)], ['Cell', str(hv.cellKey)],
      ['Agreement', hv.agrees == null ? 'unauditable / uncomputable' : String(hv.agrees)]],
    target: { kind: 'human', index: i },
  }));
  verdictMarks.push({
    x: verdictMarks.length + 1, xLabel: 'snapshot',
    kind: snapshotOk ? 'info' : 'missing',
    title: snapshotOk ? 'Harness-captured page snapshot loaded (see snapshot card)' : 'No snapshot artifact loaded for this episode',
    detail: [['Snapshot', snapshotOk ? 'loaded' : 'missing / unreadable']],
    target: { kind: 'snapshot', index: -1 },
  });
  lanes.push({ id: 'verdicts', title: 'Verdicts & snapshot', coord: 'categorical slots (not sequential)', marks: verdictMarks });

  let timeSpan = { unavailable: 'no trace timestamps' };
  const stamps = trace && Array.isArray(trace.events)
    ? trace.events.map((e) => Date.parse(e.timestamp)).filter((t) => Number.isFinite(t)) : [];
  if (stamps.length >= 2) {
    timeSpan = { start: new Date(Math.min(...stamps)).toISOString(), end: new Date(Math.max(...stamps)).toISOString(), spanMs: Math.max(...stamps) - Math.min(...stamps) };
  } else if (trace && trace.started_at && trace.completed_at
    && Number.isFinite(Date.parse(trace.started_at)) && Number.isFinite(Date.parse(trace.completed_at))) {
    timeSpan = { start: trace.started_at, end: trace.completed_at, spanMs: Date.parse(trace.completed_at) - Date.parse(trace.started_at) };
  }
  return { lanes, timeSpan };
}
