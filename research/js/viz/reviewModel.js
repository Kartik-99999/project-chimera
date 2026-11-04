/* Mini-review data model (DOM-free; unit-tested).
 * Queues the 8 frozen eval episodes for human adjudication. Decision
 * rules mirror tools/mini_review.py exactly; the Python validator is
 * authoritative for files on disk, this module for the live form.
 * Nothing here invents judgments: unrecorded episodes stay pending.
 */
export const DECISIONS_SCHEMA = 'chimera-mini-review-decisions/1';
export const STORAGE_KEY = 'chimera-mini-review:v1';
export const ASSESSMENTS = ['verified-success', 'verified-failure', 'inconclusive'];
export const AGREEMENTS = ['agrees', 'disagrees', 'undetermined'];
export const SUFFICIENCY = ['sufficient', 'insufficient'];
/* Full-audit mode: check-level decisions (the human's own P1–P3
 * booleans, appliable to plan verdicts). Separate schema and
 * separate localStorage key so the two queues can never mix. */
export const AUDIT_DECISIONS_SCHEMA = 'chimera-audit-decisions/1';
export const AUDIT_STORAGE_KEY = 'chimera-audit-full-v1:v1';
export const AUDIT_CHECKS = ['P1', 'P2', 'P3'];

export function episodeKey(runId, trialId) {
  return `${runId}::${trialId}`;
}

function parseIso(value) {
  if (typeof value !== 'string' || !value) return null;
  const t = new Date(value).getTime();
  if (!Number.isFinite(t)) return null;
  // Require an explicit timezone designator (Z or ±hh:mm).
  if (!/(Z|[+-]\d{2}:?\d{2})$/.test(value.trim())) return null;
  return t;
}

/* Validate one decision object. Returns a list of error strings. */
export function validateDecision(key, packetKeys, decision) {
  const errors = [];
  if (!packetKeys.includes(key)) {
    errors.push(`${key}: not one of the packet episodes`);
    return errors;
  }
  if (!decision || typeof decision !== 'object') return [`${key}: decision must be an object`];
  if (!ASSESSMENTS.includes(decision.assessment)) errors.push(`${key}: assessment must be one of ${ASSESSMENTS.join(', ')}`);
  if (!AGREEMENTS.includes(decision.agreement)) errors.push(`${key}: agreement must be one of ${AGREEMENTS.join(', ')}`);
  if (!SUFFICIENCY.includes(decision.sufficiency)) errors.push(`${key}: sufficiency must be one of ${SUFFICIENCY.join(', ')}`);
  if (typeof decision.reason !== 'string' || !decision.reason.trim()) errors.push(`${key}: reason is required`);
  const needsMissing = decision.assessment === 'inconclusive' || decision.sufficiency === 'insufficient';
  if (needsMissing && (typeof decision.missing_evidence !== 'string' || !decision.missing_evidence.trim())) {
    errors.push(`${key}: missing_evidence is required when the assessment is inconclusive or the evidence is insufficient`);
  }
  const assessed = parseIso(decision.assessed_at);
  if (assessed == null) errors.push(`${key}: assessed_at must be an ISO-8601 timestamp with timezone`);
  const revealed = decision.revealed_at ? parseIso(decision.revealed_at) : null;
  if (decision.revealed_at && revealed == null) errors.push(`${key}: revealed_at must be null or an ISO-8601 timestamp with timezone`);
  if ((decision.agreement === 'agrees' || decision.agreement === 'disagrees') && revealed == null) {
    errors.push(`${key}: agreement with the verifier requires revealing the recorded verdict first`);
  }
  const expectedBlind = revealed == null || (assessed != null && assessed <= revealed);
  if (decision.blinded !== expectedBlind) {
    errors.push(`${key}: blinded flag is inconsistent with the assessment/reveal timestamps`);
  }
  const corrections = decision.corrections == null ? [] : decision.corrections;
  if (!Array.isArray(corrections)) errors.push(`${key}: corrections must be a list`);
  else {
    corrections.forEach((corr, i) => {
      if (!corr || typeof corr !== 'object') { errors.push(`${key}: corrections[${i}] must be an object`); return; }
      if (parseIso(corr.at) == null) errors.push(`${key}: corrections[${i}].at must be an ISO-8601 timestamp with timezone`);
      if (!corr.previous || typeof corr.previous !== 'object') errors.push(`${key}: corrections[${i}].previous must be an object`);
      if (typeof corr.reason !== 'string' || !corr.reason.trim()) errors.push(`${key}: corrections[${i}].reason is required`);
    });
  }
  return errors;
}

/* Validate one check-level audit decision. Mirrors
 * tools/mini_review.py::_audit_decision_errors exactly. */
export function validateAuditDecision(key, packetKeys, decision) {
  const errors = [];
  if (!packetKeys.includes(key)) {
    errors.push(`${key}: not one of the ${packetKeys.length} packet episodes`);
    return errors;
  }
  if (!decision || typeof decision !== 'object') return [`${key}: decision must be an object`];
  if (decision.verdict === 'unauditable') {
    if (typeof decision.reason !== 'string' || !decision.reason.trim()) {
      errors.push(`${key}: unauditable verdicts need a non-empty reason`);
    }
    if ('checks' in decision) errors.push(`${key}: unauditable verdicts must not carry checks`);
  } else {
    const checks = decision.checks;
    if (!checks || typeof checks !== 'object') {
      errors.push(`${key}: checks must be an object keyed by ${AUDIT_CHECKS.join(', ')}`);
    } else {
      const have = Object.keys(checks).sort().join(',');
      if (have !== [...AUDIT_CHECKS].sort().join(',')) {
        errors.push(`${key}: checks must cover exactly ${AUDIT_CHECKS.join(', ')}, got ${Object.keys(checks).sort().join(', ')}`);
      }
      for (const cid of AUDIT_CHECKS) {
        if (cid in checks && typeof checks[cid] !== 'boolean') {
          errors.push(`${key}: checks.${cid} must be a JSON boolean, got ${JSON.stringify(checks[cid])}`);
        }
      }
    }
  }
  if ('note' in decision && typeof decision.note !== 'string') errors.push(`${key}: note must be a string`);
  const assessed = parseIso(decision.assessed_at);
  if (assessed == null) errors.push(`${key}: assessed_at must be an ISO-8601 timestamp with timezone`);
  const revealed = decision.revealed_at ? parseIso(decision.revealed_at) : null;
  if (decision.revealed_at && revealed == null) errors.push(`${key}: revealed_at must be null or an ISO-8601 timestamp with timezone`);
  const expectedBlind = revealed == null || (assessed != null && assessed <= revealed);
  if (decision.blinded !== expectedBlind) {
    errors.push(`${key}: blinded flag is inconsistent with the assessment/reveal timestamps`);
  }
  return errors;
}

/* Validate a full imported/exported decisions document. */
export function validateImport(doc, { packetKeys, packetSha, schema = DECISIONS_SCHEMA, audit = false } = {}) {
  const errors = [];
  if (!doc || typeof doc !== 'object') return ['decisions file must be a JSON object'];
  if (doc.schema !== schema) errors.push(`schema must be ${schema}`);
  if (doc.packet_sha256 != null && doc.packet_sha256 !== packetSha) {
    errors.push('packet_sha256 does not match the loaded packet — decisions were recorded against different bytes');
  }
  if (!doc.decisions || typeof doc.decisions !== 'object') return [...errors, 'decisions must be an object keyed by episode'];
  for (const [key, decision] of Object.entries(doc.decisions)) {
    errors.push(...(audit
      ? validateAuditDecision(key, packetKeys, decision)
      : validateDecision(key, packetKeys, decision)));
  }
  return errors;
}

/* Human-vs-recorded comparison rows + completion state. */
export function summarize(packet, state) {
  const entries = (state && state.decisions) || {};
  const rows = (packet.episodes || []).map((ep) => {
    const dec = entries[ep.key];
    const recorded = (ep.verifier.checks || []).map((c) => `${c.postcondition_id}=${c.satisfied ? 'T' : 'F'}`).join(', ') || '—';
    return {
      key: ep.key, recorded_outcome: ep.recorded.outcome, recorded_checks: recorded,
      assessment: (dec && dec.assessment) || 'pending',
      agreement: (dec && dec.agreement) || 'pending',
      sufficiency: (dec && dec.sufficiency) || 'pending',
    };
  });
  const recorded = rows.filter((r) => r.assessment !== 'pending').length;
  return {
    reviewer: (state && state.reviewer) || '',
    recorded, total: rows.length,
    complete: recorded === rows.length && Boolean(state && state.reviewer),
    rows,
  };
}

/* Check-level human-vs-recorded comparison, grouped by population.
 * Mirrors tools/mini_review.py::summarize_audit: strict per-check
 * agreement, kept per population and per run — never pooled. */
export function summarizeAudit(packet, state) {
  const entries = (state && state.decisions) || {};
  const rows = (packet.episodes || []).map((ep) => {
    const dec = entries[ep.key];
    const raw = (ep.verifier && ep.verifier.checks) || [];
    let recordedMap = null;
    if (Array.isArray(raw)) {
      const m = {};
      for (const c of raw) {
        if (!c || typeof c !== 'object' || !AUDIT_CHECKS.includes(c.postcondition_id) || typeof c.satisfied !== 'boolean') {
          recordedMap = null; break;
        }
        m[c.postcondition_id] = c.satisfied;
      }
      if (m && AUDIT_CHECKS.every((c) => c in m)) recordedMap = m;
    }
    const fmt = (m) => AUDIT_CHECKS.map((c) => `${c}=${m[c] ? 'T' : 'F'}`).join(', ');
    let agreement; let human;
    const hc = dec && dec.checks;
    if (!dec || typeof dec !== 'object' || ((typeof hc !== 'object' || !hc) && dec.verdict !== 'unauditable')) {
      agreement = 'pending'; human = 'pending';
    } else if (dec.verdict === 'unauditable') {
      agreement = 'unauditable'; human = 'unauditable';
    } else if (!recordedMap) {
      agreement = 'undetermined'; human = fmt(hc);
    } else {
      agreement = AUDIT_CHECKS.every((c) => hc[c] === recordedMap[c]) ? 'agrees' : 'disagrees';
      human = fmt(hc);
    }
    return {
      key: ep.key, population: ep.population || '(unlabeled)',
      driverCode: ep.driver_code || ep.run_id, runId: ep.run_id,
      recordedChecks: recordedMap ? fmt(recordedMap) : '—',
      human, agreement, blinded: (dec && dec.blinded) || 'pending',
    };
  });
  const pops = {};
  for (const r of rows) {
    const pop = pops[r.population] || (pops[r.population] = { runs: {} });
    const run = pop.runs[r.runId] || (pop.runs[r.runId] = {
      total: 0, recorded: 0, agrees: 0, disagrees: 0, undetermined: 0, unauditable: 0,
    });
    run.total += 1;
    if (r.agreement !== 'pending') { run.recorded += 1; run[r.agreement] += 1; }
  }
  const recorded = rows.filter((r) => r.agreement !== 'pending').length;
  return {
    reviewer: (state && state.reviewer) || '',
    recorded, total: rows.length,
    complete: recorded === rows.length && Boolean(state && state.reviewer),
    populations: Object.entries(pops).sort(([a], [b]) => (a < b ? -1 : 1)).map(([label, data]) => ({
      label, runs: Object.entries(data.runs).sort(([a], [b]) => (a < b ? -1 : 1)).map(([runId, counts]) => ({ runId, ...counts })),
    })),
    rows,
  };
}

export function loadState(storage, key = STORAGE_KEY) {
  const blank = () => ({ reviewer: '', decisions: {}, partials: {} });
  try {
    const raw = storage.getItem(key);
    if (!raw) return blank();
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return blank();
    return {
      reviewer: typeof parsed.reviewer === 'string' ? parsed.reviewer : '',
      decisions: parsed.decisions && typeof parsed.decisions === 'object' ? parsed.decisions : {},
      partials: parsed.partials && typeof parsed.partials === 'object' ? parsed.partials : {},
    };
  } catch {
    return blank();
  }
}

export function saveState(storage, state, key = STORAGE_KEY) {
  storage.setItem(key, JSON.stringify(state));
}

async function sha256Hex(text, impl) {
  if (!impl) return { sha: null, note: 'WebCrypto unavailable in this browser context' };
  const digest = await impl.digest('SHA-256', new TextEncoder().encode(text));
  return { sha: [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join(''), note: null };
}

/* Build the exportable decisions document. timestamps/decisions come
 * from the caller; this only binds them to the packet bytes. Pass
 * subtle explicitly in tests; browsers resolve WebCrypto by default. */
export async function exportDoc({ packetText, state, exportedAt, subtle, schema = DECISIONS_SCHEMA } = {}) {
  const impl = subtle === undefined ? (globalThis.crypto && globalThis.crypto.subtle) : subtle;
  const { sha, note } = await sha256Hex(packetText || '', impl);
  const doc = {
    schema, packet: 'packet.json', packet_sha256: sha,
    reviewer: (state && state.reviewer) || '', exported_at: exportedAt || null,
    decisions: JSON.parse(JSON.stringify((state && state.decisions) || {})),
  };
  if (note) doc.sha_note = note;
  return doc;
}
