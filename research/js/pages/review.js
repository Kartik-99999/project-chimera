/* Review queues: blinded human adjudication of frozen audit
 * episodes. Two queues share this page (?packet=mini|full):
 * mini (default) replays the 8-episode assessment protocol;
 * full serves the 184-episode consolidated audit packet with
 * check-level decisions (the reviewer's own P1–P3 booleans) and
 * masked driver identity. Evidence renders from the live frozen
 * files (with packet digests alongside); recorded outcomes and
 * verifier checks stay masked until the reviewer reveals them.
 * Decisions persist to localStorage (separate keys per queue) and
 * export as decisions.json for the Python validator — the console
 * never writes repo files, so nothing here can mark an audit
 * complete on its own.
 *
 * Mini protocol (timestamps prove it): record assessment blinded
 * → reveal recorded verdict → record agreement. Full protocol:
 * record P1–P3 blinded (single phase; agreement is computed, not
 * judged) → optionally reveal. Revisions append to a corrections
 * history; nothing is overwritten silently.
 */
import { rootPath, esc, fmtInt } from '../data.js';
import { link } from '../app.js';
import { pageHead, emptyState, kvList, pill, globes, secHead } from '../components.js';
import { traceTimeline, replaySteps, recordTable, snapshotView } from './evidence.js';
import {
  validateDecision, validateAuditDecision, validateImport, summarize,
  summarizeAudit, loadState, saveState,
  exportDoc, ASSESSMENTS, AGREEMENTS, SUFFICIENCY, AUDIT_CHECKS,
  DECISIONS_SCHEMA, AUDIT_DECISIONS_SCHEMA, STORAGE_KEY, AUDIT_STORAGE_KEY,
} from '../viz/reviewModel.js';

const PACKETS = {
  mini: {
    path: 'artifacts/eval-20261028/mini-review/packet.json', expect: 8,
    label: 'Mini-review queue',
    decisionsPath: 'artifacts/eval-20261028/mini-review/decisions.json',
    schema: DECISIONS_SCHEMA, storageKey: STORAGE_KEY, audit: false,
  },
  full: {
    path: 'artifacts/audit-full-v1/review/packet.json', expect: 184,
    label: 'Full audit queue',
    decisionsPath: 'artifacts/audit-full-v1/review/decisions.json',
    schema: AUDIT_DECISIONS_SCHEMA, storageKey: AUDIT_STORAGE_KEY, audit: true,
  },
};

/* Absolute plan paths (matched-budget bundles) cannot be fetched by
 * the browser; relativize to the served repo root for fetch/href. */
function servePath(p) {
  const s = String(p || '');
  const m = s.match(/\/(artifacts|experiments|benchmarks|data)\//);
  return m ? s.slice(m.index + 1) : s;
}

/* plan_cell is scenario|input|baseline|faults — the baseline segment
 * names the driver, so the blinded view shows the rest only. */
function redactedCell(cell) {
  const parts = String(cell || '').split('|');
  if (parts.length < 4) return 'withheld until reveal';
  return `${parts[0]} / ${parts[1]} · faults ${parts.slice(3).join('|')} (driver withheld)`;
}

const queueQuery = (ctx) => (ctx.def.audit ? { packet: 'full' } : {});

const store = {
  getItem(k) { try { return globalThis.localStorage.getItem(k); } catch { return null; } },
  setItem(k, v) { try { globalThis.localStorage.setItem(k, v); } catch { /* private mode: session-only */ } },
};

async function fetchText(path) {
  const res = await fetch(rootPath(path), { cache: 'no-store' });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${path}`);
  return res.text();
}

async function fetchMaybe(path) {
  try {
    const res = await fetch(rootPath(path), { cache: 'no-store' });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

const nowIso = () => new Date().toISOString();
const fmtWhen = (iso) => {
  try { return new Date(iso).toLocaleString(); } catch { return iso; }
};

function statusOf(key, state) {
  if (state.decisions && state.decisions[key]) return 'reviewed';
  if (state.partials && state.partials[key] && state.partials[key].assessed_at) return 'assessing';
  return 'pending';
}

function statusPill(status) {
  if (status === 'reviewed') return pill('ok', 'reviewed');
  if (status === 'assessing') return pill('warn', 'assessed — awaiting agreement');
  return pill('dim', 'pending');
}

function decisionLabel(value) {
  return { 'verified-success': 'verified success', 'verified-failure': 'verified failure', inconclusive: 'inconclusive' }[value] || value;
}

function proofBanner(ctx) {
  if (ctx.audit) {
    return `<div class="banner info"><strong>Human review is the gate.</strong> Nothing here adjudicates on its own: `
      + `every decision below is recorded by a person — your own true/false judgment for P1, P2, and P3, blinded first. `
      + `Driver identity stays masked until you reveal each episode. Agreement is computed per population, never pooled.</div>`;
  }
  return `<div class="banner info"><strong>Human review is the gate.</strong> Nothing here adjudicates on its own: `
    + `every decision below is recorded by a person, blinded assessment first, with reasons tied to specific observations. `
    + `Eight episodes describe only themselves — agreement counts support no reliability claim.</div>`;
}

export async function pageReview(el, { params = [], query = {} }) {
  const which = query.packet === 'full' ? 'full' : 'mini';
  const def = PACKETS[which];
  const ctx = { which, def, audit: def.audit };
  let packetText;
  try {
    packetText = await fetchText(def.path);
  } catch (err) {
    el.innerHTML = pageHead(def.label, [[def.label]]) + emptyState(
      'Review packet unavailable', `Could not load <code>${esc(def.path)}</code> (${esc(err.message)}). `
      + 'Build it with <code>tools/mini_review.py build-packet</code>. No review can proceed without the packet.');
    return;
  }
  let packet;
  try {
    packet = JSON.parse(packetText);
  } catch {
    el.innerHTML = pageHead(def.label, [[def.label]]) + emptyState(
      'Review packet unreadable', 'packet.json is not valid JSON. Rebuild it; do not review from a corrupt packet.');
    return;
  }
  const episodes = packet.episodes || [];
  if (episodes.length !== def.expect) {
    el.innerHTML = pageHead(def.label, [[def.label]])
      + `<div class="banner bad"><strong>Unexpected selection:</strong> packet holds ${episodes.length} episodes, not the frozen ${def.expect}. Refusing to review a different selection.</div>`;
    return;
  }
  const looksAudit = Array.isArray(packet.populations) && typeof packet.title === 'string';
  if (looksAudit !== ctx.audit) {
    el.innerHTML = pageHead(def.label, [[def.label]])
      + `<div class="banner bad"><strong>Packet/queue mismatch:</strong> this packet is ${looksAudit ? 'a consolidated audit packet' : 'a mini packet'} but the queue is ${ctx.audit ? 'the audit queue' : 'the mini queue'}. Refusing to mix protocols.</div>`;
    return;
  }
  const state = loadState(store, def.storageKey);
  state.partials = state.partials && typeof state.partials === 'object' ? state.partials : {};
  const [p0, p1] = params;
  if (ctx.audit && p0 === 'ep' && p1 != null) {
    await renderItem(el, packet, packetText, state, ctx, Number(p1), query);
  } else if (!ctx.audit && p0 && p1) {
    await renderItem(el, packet, packetText, state, ctx, -1, query, p0, p1);
  } else {
    renderQueue(el, packet, packetText, state, ctx);
  }
}

/* -- queue + summary ---------------------------------------------- */

function queueSwitcher(ctx) {
  const other = ctx.audit ? 'mini' : 'full';
  const otherLabel = ctx.audit ? 'Mini-review queue (8 episodes)' : 'Full audit queue (184 episodes)';
  const q = ctx.audit ? {} : { packet: 'full' };
  return `<div class="card"><h2>Queues</h2><p style="margin:0;color:var(--ink-2)">You are in the <strong>${esc(ctx.def.label)}</strong> `
    + `(decisions stay in this queue's own local state). <a class="btn" href="${link('review', [], q)}">Open ${esc(otherLabel)} →</a></p></div>`;
}

function renderQueue(el, packet, packetText, state, ctx) {
  if (ctx.audit) return renderAuditQueue(el, packet, packetText, state, ctx);
  const summary = summarize(packet, state);
  const revealed = [...Object.values(state.decisions || {}), ...Object.values(state.partials || {})]
    .filter((d) => d && d.revealed_at).length;
  const items = packet.episodes.map((ep, i) => {
    const st = statusOf(ep.key, state);
    return `<div class="finding"><span class="marker" aria-hidden="true">${i + 1}</span><span>`
      + `<a href="${link('review', [ep.run_id, ep.trial_id])}"><strong>Episode ${i + 1}</strong></a> `
      + `${statusPill(st)}<br><span style="color:var(--ink-2)">${esc(ep.scenario_id)} / ${esc(ep.input_id)} · `
      + `expected ${esc(JSON.stringify(ep.expected_stored_name))} · <code>${esc(ep.trial_id)}</code></span></span></div>`;
  }).join('');
  const rows = summary.rows.map((r) => {
    const dec = (state.decisions || {})[r.key];
    const seen = dec && dec.revealed_at;
    return `<tr><td class="mono" style="font-size:11.5px">${esc(r.key)}</td>`
      + `<td>${seen ? `<code>${esc(r.recorded_outcome)}</code>` : '<span class="mask">•••</span>'}</td>`
      + `<td class="mono" style="font-size:11.5px">${seen ? esc(r.recorded_checks) : '<span class="mask">•••</span>'}</td>`
      + `<td>${r.assessment === 'pending' ? '<span style="color:var(--ink-3)">pending</span>' : `<strong>${esc(decisionLabel(r.assessment))}</strong>`}</td>`
      + `<td>${esc(r.agreement)}</td><td>${esc(r.sufficiency)}</td></tr>`;
  }).join('');

  const navy = `<div class="navy">${globes()}<h2>Eight episodes need you</h2>`
    + `<p class="sub">The mini sample (${summary.total} episodes) is the fastest path to a first audited eval claim. Blinded: baselines revealed only after you decide — record assessment, then reveal, then judge agreement.</p>`
    + `<p><span class="glass"><span class="dot" style="background:#fbbf24"></span>${summary.recorded}/${summary.total} decided</span>`
    + `<span class="glass"><span class="dot" style="background:#8fb4ff"></span>protocol: blinded, one reviewer each</span>`
    + `<span class="glass"><span class="dot" style="background:#6ee7a0"></span>export → decisions.json</span></p></div>`;
  el.innerHTML = pageHead('Mini-review queue', [['Mini-review queue']], '', {
    kicker: 'Routes #/audit · #/review',
    lede: 'Blinded human adjudication of frozen audit episodes — judge the postconditions from the evidence with recorded verdicts masked.',
    meta: `${summary.complete ? pill('ok', `COMPLETE — ${summary.recorded}/${summary.total}`) : pill('warn', `IN PROGRESS — ${summary.recorded}/${summary.total}`)}`,
  }) + proofBanner(ctx)
    + queueSwitcher(ctx)
    + navy
    + secHead('Mini-review queue', `Blinded protocol · ${summary.total} episodes · reviewer named per decision`)
    + `<div class="card"><h2>Protocol</h2><ol style="margin:0;padding-left:20px;color:var(--ink-2);font-size:13px">`
    + `<li>Open an episode and judge the postconditions from the evidence with recorded verdicts masked.</li>`
    + `<li>Record your assessment, sufficiency, and reason; then reveal the recorded verdict and judge agreement.</li>`
    + `<li>Export <code>decisions.json</code> and validate it with <code>tools/mini_review.py validate</code>.</li></ol>`
    + `<p style="color:var(--ink-3);font-size:12.5px">Blinding is partial: run IDs stay visible for evidence lookup and trace `
    + `structure differs by driver — do not use them to prejudge. Packet: <code>${esc(ctx.def.path)}</code> · `
    + `manifest sha <code>${esc((packet.manifest.sha256 || '').slice(0, 12))}…</code>.</p></div>`
    + `<div class="card"><h2>Reviewer</h2><div class="filters"><div class="field">`
    + `<label for="rv-name">Reviewer name (required to record)</label>`
    + `<input id="rv-name" type="text" value="${esc(summary.reviewer)}" placeholder="your-name" autocomplete="off"></div>`
    + `<div class="field"><label>Progress</label><div style="padding-top:6px"><strong>${summary.recorded}/${summary.total}</strong> reviewed · `
    + `${revealed} revealed</div></div></div></div>`
    + `<div class="card"><h2>Episodes (8)</h2>${items}</div>`
    + `<div class="card"><h2>Audit summary</h2>`
    + `<p>${summary.complete ? pill('ok', 'COMPLETE — 8/8 recorded') : pill('warn', `IN PROGRESS — ${summary.recorded}/8 recorded`)}</p>`
    + `<div class="table-wrap"><table class="data"><thead><tr><th>Episode</th><th>Recorded</th><th>Verifier P1–P3</th><th>Human</th><th>Agreement</th><th>Evidence</th></tr></thead>`
    + `<tbody>${rows}</tbody></table></div>`
    + `<p style="color:var(--ink-3);font-size:12.5px">Recorded columns stay masked until you reveal each episode. `
    + `Descriptive only: 8 episodes support no reliability claim; the 95% provisional rule applies to full audits, not this sample.</p></div>`
    + `<div class="card"><h2>Export / import</h2>`
    + `<p style="color:var(--ink-2)">This console cannot write repo files: export downloads <code>decisions.json</code> — save it over `
    + `<code>artifacts/eval-20261028/mini-review/decisions.json</code> and validate it. Import loads a decisions file for viewing.</p>`
    + `<div class="btn-row"><button class="btn" id="rv-export">Export decisions.json</button> `
    + `<label class="btn" for="rv-import">Import decisions.json</label>`
    + `<input type="file" id="rv-import" accept="application/json" hidden></div>`
    + `<div id="rv-io-msg" style="margin-top:8px"></div></div>`;

  el.querySelector('#rv-name').addEventListener('change', (e) => {
    state.reviewer = e.target.value.trim();
    saveState(store, state, ctx.def.storageKey);
  });
  el.querySelector('#rv-export').addEventListener('click', async () => {
    const msg = el.querySelector('#rv-io-msg');
    try {
      const doc = await exportDoc({ packetText, state, exportedAt: nowIso() });
      const keys = packet.episodes.map((e) => e.key);
      const problems = validateImport(doc, { packetKeys: keys, packetSha: doc.packet_sha256 });
      if (problems.length) {
        msg.innerHTML = `<div class="banner bad"><strong>Export blocked:</strong> ${problems.map(esc).join('<br>')}</div>`;
        return;
      }
      const blob = new Blob([JSON.stringify(doc, null, 2) + '\n'], { type: 'application/json' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'decisions.json';
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(a.href), 5000);
      msg.innerHTML = `<div class="banner info"><strong>Exported.</strong> Save the file over `
        + `<code>artifacts/eval-20261028/mini-review/decisions.json</code>, then run `
        + `<code>tools/mini_review.py validate</code>.</div>`;
    } catch (err) {
      msg.innerHTML = `<div class="banner bad"><strong>Export failed:</strong> ${esc(err.message)}</div>`;
    }
  });
  el.querySelector('#rv-import').addEventListener('change', (e) => {
    const msg = el.querySelector('#rv-io-msg');
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async () => {
      try {
        const doc = JSON.parse(String(reader.result));
        const keys = packet.episodes.map((x) => x.key);
        const mine = await exportDoc({ packetText, state: { reviewer: '', decisions: {} } });
        const problems = validateImport(doc, { packetKeys: keys, packetSha: mine.packet_sha256 });
        if (problems.length) {
          msg.innerHTML = `<div class="banner bad"><strong>Import refused:</strong> ${problems.map(esc).join('<br>')}</div>`;
          return;
        }
        const n = Object.keys(doc.decisions).length;
        if (!window.confirm(`Load ${n} decision(s) from ${file.name}? This replaces the queue's current local state.`)) return;
        saveState(store, { reviewer: doc.reviewer || '', decisions: doc.decisions, partials: {} }, ctx.def.storageKey);
        window.location.reload();
      } catch (err) {
        msg.innerHTML = `<div class="banner bad"><strong>Import failed:</strong> ${esc(err.message)}</div>`;
      }
    };
    reader.readAsText(file);
  });
}

/* -- full-audit queue -------------------------------------------- */

function renderAuditQueue(el, packet, packetText, state, ctx) {
  const summary = summarizeAudit(packet, state);
  const revealed = Object.values(state.decisions || {}).filter((d) => d && d.revealed_at).length;
  let lastPop = null; let lastRun = null;
  const items = packet.episodes.map((ep, i) => {
    const st = state.decisions && state.decisions[ep.key] ? 'reviewed' : 'pending';
    let head = '';
    if (ep.population !== lastPop) {
      lastPop = ep.population; lastRun = null;
      head += `<h3 style="margin:14px 0 6px">${esc(ep.population)}</h3>`;
    }
    if (ep.run_id !== lastRun) {
      lastRun = ep.run_id;
      const runN = packet.episodes.filter((e) => e.run_id === ep.run_id).length;
      head += `<p style="margin:6px 0;color:var(--ink-2)"><strong>${esc(ep.driver_code)}</strong> · `
        + `manifest <code>${esc((ep.manifest && ep.manifest.manifest_id) || '?')}</code> · ${runN} episodes</p>`;
    }
    return head + `<div class="finding"><span class="marker" aria-hidden="true">${i + 1}</span><span>`
      + `<a href="${link('review', ['ep', String(i)], queueQuery(ctx))}"><strong>Episode ${i + 1}</strong></a> `
      + `${statusPill(st)}<br><span style="color:var(--ink-2)">${esc(ep.driver_code)} · ${esc(ep.scenario_id)} / ${esc(ep.input_id)} · `
      + `expected ${esc(JSON.stringify(ep.expected_stored_name))}</span></span></div>`;
  }).join('');
  const rollups = summary.populations.map((pop) => (
    `<h3>${esc(pop.label)}</h3><div class="table-wrap"><table class="data"><thead><tr><th>Driver</th><th>Recorded</th>`
    + `<th>Agrees</th><th>Disagrees</th><th>Undetermined</th><th>Unauditable</th></tr></thead><tbody>`
    + pop.runs.map((r) => {
      const code = (packet.episodes.find((e) => e.run_id === r.runId) || {}).driver_code || r.runId;
      return `<tr><td><strong>${esc(code)}</strong></td><td>${r.recorded}/${r.total}</td><td>${r.agrees}</td>`
        + `<td>${r.disagrees}</td><td>${r.undetermined}</td><td>${r.unauditable}</td></tr>`;
    }).join('') + `</tbody></table></div>`
  )).join('');
  const rows = summary.rows.map((r, i) => {
    const dec = (state.decisions || {})[r.key];
    const seen = dec && dec.revealed_at;
    const human = r.agreement === 'pending' ? '<span style="color:var(--ink-3)">pending</span>'
      : r.agreement === 'unauditable' ? '<strong>unauditable</strong>'
      : `<code style="font-size:11.5px">${esc(r.human)}</code>`;
    return `<tr><td><a href="${link('review', ['ep', String(i)], queueQuery(ctx))}">${i + 1}</a></td>`
      + `<td>${esc(r.driverCode)}</td>`
      + `<td>${seen ? `<code style="font-size:11.5px">${esc(r.recordedChecks)}</code>` : '<span class="mask">•••</span>'}</td>`
      + `<td>${human}</td><td>${esc(r.agreement)}</td></tr>`;
  }).join('');

  el.innerHTML = pageHead('Full audit queue', [['Full audit queue']]) + proofBanner(ctx)
    + queueSwitcher(ctx)
    + `<div class="card"><h2>Protocol</h2><ol style="margin:0;padding-left:20px;color:var(--ink-2);font-size:13px">`
    + `<li>Open an episode and judge P1, P2, and P3 from the evidence with driver identity and recorded verdicts masked.</li>`
    + `<li>Record your own true/false for each check — or mark the episode unauditable with an explicit reason.</li>`
    + `<li>Reveal the recorded verdict only after saving. Then export <code>decisions.json</code>, validate it, and apply it to the plans.</li></ol>`
    + `<p style="color:var(--ink-3);font-size:12.5px">Blinding is partial: trace shape differs by driver and episode URLs carry `
    + `lookup identifiers — do not use them to prejudge. Agreement is strict per-check equality, per population, never pooled. `
    + `Packet: <code>${esc(ctx.def.path)}</code>.</p></div>`
    + `<div class="card"><h2>Reviewer</h2><div class="filters"><div class="field">`
    + `<label for="rv-name">Reviewer name (required to record)</label>`
    + `<input id="rv-name" type="text" value="${esc(summary.reviewer)}" placeholder="your-name" autocomplete="off"></div>`
    + `<div class="field"><label>Progress</label><div style="padding-top:6px"><strong>${summary.recorded}/${summary.total}</strong> reviewed · `
    + `${revealed} revealed</div></div></div></div>`
    + `<div class="card"><h2>Episodes (${summary.total})</h2>${items}</div>`
    + `<div class="card"><h2>Audit summary</h2>`
    + `<p>${summary.complete ? pill('ok', `COMPLETE — ${summary.total}/${summary.total} recorded`) : pill('warn', `IN PROGRESS — ${summary.recorded}/${summary.total} recorded`)}</p>`
    + rollups
    + `<h3>Episodes</h3><div class="table-wrap"><table class="data"><thead><tr><th>#</th><th>Driver</th><th>Recorded P1–P3</th><th>Human</th><th>Agreement</th></tr></thead>`
    + `<tbody>${rows}</tbody></table></div>`
    + `<p style="color:var(--ink-3);font-size:12.5px">Recorded columns stay masked until you reveal each episode. `
    + `The 95% provisional rule (user guide §15.1 step 4) applies per population once its required sample is fully adjudicated.</p></div>`
    + `<div class="card"><h2>Export / import</h2>`
    + `<p style="color:var(--ink-2)">This console cannot write repo files: export downloads <code>decisions.json</code> — save it over `
    + `<code>${esc(ctx.def.decisionsPath)}</code>, validate with <code>tools/mini_review.py validate ${esc(ctx.def.decisionsPath)} --packet ${esc(ctx.def.decisionsPath.replace(/\/decisions\.json$/, ''))}</code>, `
    + `then merge with <code>tools/mini_review.py apply-verdicts --packet ${esc(ctx.def.decisionsPath.replace(/\/decisions\.json$/, ''))}</code> (dry-run; add <code>--write</code> only when review is complete). `
    + `Import loads a decisions file for viewing.</p>`
    + `<div class="btn-row"><button class="btn" id="rv-export">Export decisions.json</button> `
    + `<label class="btn" for="rv-import">Import decisions.json</label>`
    + `<input type="file" id="rv-import" accept="application/json" hidden></div>`
    + `<div id="rv-io-msg" style="margin-top:8px"></div></div>`;

  el.querySelector('#rv-name').addEventListener('change', (e) => {
    state.reviewer = e.target.value.trim();
    saveState(store, state, ctx.def.storageKey);
  });
  el.querySelector('#rv-export').addEventListener('click', async () => {
    const msg = el.querySelector('#rv-io-msg');
    try {
      const doc = await exportDoc({ packetText, state, exportedAt: nowIso(), schema: ctx.def.schema });
      const keys = packet.episodes.map((e) => e.key);
      const problems = validateImport(doc, { packetKeys: keys, packetSha: doc.packet_sha256, schema: ctx.def.schema, audit: true });
      if (problems.length) {
        msg.innerHTML = `<div class="banner bad"><strong>Export blocked:</strong> ${problems.map(esc).join('<br>')}</div>`;
        return;
      }
      const blob = new Blob([JSON.stringify(doc, null, 2) + '\n'], { type: 'application/json' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'decisions.json';
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(a.href), 5000);
      msg.innerHTML = `<div class="banner info"><strong>Exported.</strong> Save the file over `
        + `<code>${esc(ctx.def.decisionsPath)}</code>, then validate and apply-verdicts (see above).</div>`;
    } catch (err) {
      msg.innerHTML = `<div class="banner bad"><strong>Export failed:</strong> ${esc(err.message)}</div>`;
    }
  });
  el.querySelector('#rv-import').addEventListener('change', (e) => {
    const msg = el.querySelector('#rv-io-msg');
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async () => {
      try {
        const doc = JSON.parse(String(reader.result));
        const keys = packet.episodes.map((x) => x.key);
        const mine = await exportDoc({ packetText, state: { reviewer: '', decisions: {} }, schema: ctx.def.schema });
        const problems = validateImport(doc, { packetKeys: keys, packetSha: mine.packet_sha256, schema: ctx.def.schema, audit: true });
        if (problems.length) {
          msg.innerHTML = `<div class="banner bad"><strong>Import refused:</strong> ${problems.map(esc).join('<br>')}</div>`;
          return;
        }
        const n = Object.keys(doc.decisions).length;
        if (!window.confirm(`Load ${n} decision(s) from ${file.name}? This replaces the queue's current local state.`)) return;
        saveState(store, { reviewer: doc.reviewer || '', decisions: doc.decisions, partials: {} }, ctx.def.storageKey);
        window.location.reload();
      } catch (err) {
        msg.innerHTML = `<div class="banner bad"><strong>Import failed:</strong> ${esc(err.message)}</div>`;
      }
    };
    reader.readAsText(file);
  });
}

/* -- single-episode review ----------------------------------------- */

function auditFormHtml(packet, key, decision, revising) {
  if (decision && !revising) {
    const corr = (decision.corrections || []).map((c) => (
      `<li>${esc(fmtWhen(c.at))} — ${esc(c.reason)} (was: <code>${esc(JSON.stringify(c.previous))}</code>)</li>`)).join('');
    const verdict = decision.verdict === 'unauditable'
      ? `<strong>unauditable</strong> — ${esc(decision.reason || '')}`
      : AUDIT_CHECKS.map((c) => `${c}=<strong>${decision.checks[c] ? 'true' : 'false'}</strong>`).join(' · ');
    return `<div class="card"><h2>Recorded decision</h2>${kvList([
      ['Your P1–P3', verdict],
      ['Note', decision.note ? esc(decision.note) : '—'],
      ['Blinded', decision.blinded ? 'yes — assessed before reveal' : 'no — revealed first'],
      ['Assessed', esc(fmtWhen(decision.assessed_at))],
    ])}${corr ? `<h3>Corrections (${decision.corrections.length})</h3><ul>${corr}</ul>` : ''}`
      + `<p><button class="btn" id="rv-revise">Revise decision</button> <span style="color:var(--ink-3);font-size:12px">Revisions append the previous judgment to the corrections history (provenance only — the latest checks are what gets applied).</span></p></div>`;
  }
  const pre = revising && decision ? decision : {};
  const preChecks = (pre && pre.checks) || {};
  const judge = {};
  for (const p of packet.postconditions || []) judge[p.id] = p.judge;
  const selects = AUDIT_CHECKS.map((c) => (
    `<div class="field"><label for="rv-${c.toLowerCase()}">${c} — ${esc(judge[c] || c)}</label>`
    + `<select id="rv-${c.toLowerCase()}"><option value="">— select —</option>`
    + `<option value="true"${preChecks[c] === true ? ' selected' : ''}>true</option>`
    + `<option value="false"${preChecks[c] === false ? ' selected' : ''}>false</option></select></div>`
  )).join('');
  return `<div class="card"><h2>${revising ? 'Revise decision' : 'Record decision — your own P1–P3'}</h2>`
    + `<div class="filters">${selects}</div>`
    + `<div class="field" style="margin-bottom:10px"><label for="rv-unauditable"><input type="checkbox" id="rv-unauditable"${pre.verdict === 'unauditable' ? ' checked' : ''} style="width:auto;margin-right:6px">Unauditable — the evidence cannot support a judgment (requires a reason; clears the checks above)</label></div>`
    + `<div class="field" style="margin-bottom:10px"><label for="rv-note">Note${' '}(${esc('optional — but required as the reason when unauditable')})</label>`
    + `<textarea id="rv-note" rows="3" style="width:100%" placeholder="e.g. snapshot shows confirmation_visible=true with exactly ['Padded Name']">${esc(pre.note || pre.reason || '')}</textarea></div>`
    + (revising ? `<div class="field" style="margin-bottom:10px"><label for="rv-creason">Correction reason (required)</label>`
      + `<input id="rv-creason" type="text" style="width:100%" placeholder="Why is the previous judgment being changed?"></div>` : '')
    + `<div class="btn-row"><button class="btn primary" id="rv-save-checks">${revising ? 'Save revision' : 'Record decision'}</button></div>`
    + `<div id="rv-form-msg" style="margin-top:8px"></div></div>`;
}

async function renderItem(el, packet, packetText, state, ctx, index, query, runIdParam, trialIdParam) {
  const audit = ctx.audit;
  const q = queueQuery(ctx);
  let ep = null; let idx = -1;
  if (audit) {
    idx = Number.isInteger(index) ? index : -1;
    ep = idx >= 0 && idx < packet.episodes.length ? packet.episodes[idx] : null;
  } else {
    ep = packet.episodes.find((e) => e.run_id === runIdParam && e.trial_id === trialIdParam);
    idx = ep ? packet.episodes.indexOf(ep) : -1;
  }
  if (!ep) {
    el.innerHTML = pageHead('Review episode', [[ctx.def.label, link('review', [], q)], ['Not found']]) + emptyState(
      'Episode not in the packet', audit
        ? `No packet episode at index <code>${esc(String(index))}</code>. The queue reviews only the frozen ${ctx.def.expect}, addressed by number.`
        : `No packet episode <code>${esc(runIdParam)}::${esc(trialIdParam)}</code>. The queue reviews only the frozen 8.`,
      `<p><a class="btn" href="${link('review', [], q)}">Back to queue</a></p>`);
    return;
  }
  const runId = ep.run_id; const trialId = ep.trial_id;
  const key = ep.key;
  const revising = query.revise === '1';
  const decision = state.decisions[key] || null;
  const partial = audit ? null : (state.partials[key] || null);
  const assessed = partial && partial.assessed_at ? partial : null;

  const live = {};
  for (const kind of ['trace', 'snapshot', 'actions']) {
    live[kind] = await fetchMaybe(servePath(ep.artifacts[kind].path));
  }
  const liveMissing = Object.entries(live).filter(([, v]) => v == null).map(([k]) => k);
  const revealedAt = (decision && decision.revealed_at) || (partial && partial.revealed_at) || null;

  const guide = (packet.postconditions || []).map((p) => (
    `<tr><td class="mono">${esc(p.id)}</td><td>${esc(p.name)}</td><td style="font-size:12.5px">${esc(p.judge)}</td></tr>`)).join('');
  const stepTitle = ep.evidence.kind === 'replay'
    ? (audit ? 'Step report' : 'Replay steps (driver report)')
    : 'Trace timeline';
  let evidenceHtml;
  if (ep.evidence.kind === 'replay') {
    evidenceHtml = `<h3>${stepTitle}</h3>`
      + (live.trace ? replaySteps(live.trace, { neutral: audit }) : `<div class="banner warn"><strong>Live ${audit ? 'step report' : 'driver report'} unreadable:</strong> packet copy has ${ep.evidence.steps.length} steps; open the file directly.</div>`);
  } else {
    evidenceHtml = `<h3>Trace timeline</h3>`
      + (live.trace ? traceTimeline(live.trace) : `<div class="banner warn"><strong>Live trace unreadable:</strong> packet copy has ${ep.evidence.steps.length} events; open the file directly.</div>`);
  }
  // Live snapshots carry run_id (driver identity); the blinded
  // view scrubs it before render (raw-JSON view included).
  const snapView = (audit && !revealedAt && live.snapshot)
    ? { ...live.snapshot, run_id: 'withheld until reveal' }
    : live.snapshot;
  evidenceHtml += `<h3>Snapshot</h3>`
    + (live.snapshot ? snapshotView(snapView) : `<div class="banner warn"><strong>Live snapshot unreadable:</strong> packet copy: confirmation_visible=${esc(String(ep.evidence.snapshot.confirmation_visible))}, items=${esc(JSON.stringify(ep.evidence.snapshot.items))}.</div>`);
  evidenceHtml += `<h3>Observed actions (context only — not judged)</h3>`
    + (live.actions ? `<p style="color:var(--ink-3)">attached=${esc(String(live.actions.attached))} · complete=${esc(String(live.actions.complete))}</p>${recordTable(live.actions.records)}`
      : `<div class="banner warn"><strong>Live action log unreadable:</strong> packet copy has ${ep.evidence.actions.length} records.</div>`);
  const shots = (ep.evidence.screenshots || []).map((s) => {
    const rel = String(s.path).includes('/data/screenshots/')
      ? `/data/screenshots/${String(s.path).split('/data/screenshots/')[1]}` : null;
    const label = (audit && !revealedAt) ? 'failure screenshot' : s.path;
    return `<div style="margin-bottom:10px"><code style="font-size:11.5px">${esc(label)}</code> — ${s.exists ? 'present' : '<strong>MISSING</strong>'}`
      + (rel && s.exists ? `<br><img src="${esc(rel)}" alt="failure screenshot for ${esc(trialId)}" style="max-width:100%;border:1px solid var(--line-1);border-radius:8px;margin-top:6px">` : '') + `</div>`;
  }).join('') || '<p style="color:var(--ink-3)">None attached (expected: the harness captures one only on action failure).</p>';

  const mayReveal = audit ? Boolean(decision) : Boolean(decision || assessed);
  const recordedCard = revealedAt
    ? `<div data-testid="recorded-values">${kvList([
      ['Baseline', `<code>${esc(ep.baseline)}</code>`],
      ['Recorded outcome', `<code>${esc(ep.recorded.outcome)}</code>`],
      ['Agent said', `<code>${esc(ep.recorded.agent_terminal_status)}</code>`],
      ['Error', ep.recorded.error ? `<code>${esc(ep.recorded.error.slice(0, 300))}</code>` : 'none'],
      ['Verifier', `${esc(ep.verifier.status)} · ${(ep.verifier.checks || []).map((c) => `${c.postcondition_id}=${c.satisfied}`).join(', ') || '—'}`],
    ])}<p style="color:var(--ink-3);font-size:12px">Revealed ${esc(fmtWhen(revealedAt))}.</p></div>`
    : `<div data-testid="recorded-masked"><p><span class="mask">•••</span> <span style="color:var(--ink-2)">${audit ? 'Driver identity, baseline, recorded outcome, and verifier checks' : 'Baseline, recorded outcome, and verifier checks'} are masked until you reveal them. Judge the postconditions from the evidence first.</span></p>`
    + (mayReveal
      ? `<p><button class="btn" id="rv-reveal">Reveal recorded verdict</button></p>`
      : `<p style="color:var(--ink-3);font-size:12px">Reveal unlocks after you record your assessment below — the two-phase order is enforced, not advisory.</p>`) + `</div>`;

  let formHtml;
  if (audit) {
    formHtml = auditFormHtml(packet, key, decision, revising);
  } else if (decision && !revising) {
    const corr = (decision.corrections || []).map((c) => (
      `<li>${esc(fmtWhen(c.at))} — ${esc(c.reason)} (was: <code>${esc(JSON.stringify(c.previous))}</code>)</li>`)).join('');
    formHtml = `<div class="card"><h2>Recorded decision</h2>${kvList([
      ['Assessment', `<strong>${esc(decisionLabel(decision.assessment))}</strong>`],
      ['Agreement', esc(decision.agreement)],
      ['Evidence', esc(decision.sufficiency)],
      ['Reason', esc(decision.reason)],
      ['Missing evidence', decision.missing_evidence ? esc(decision.missing_evidence) : '—'],
      ['Blinded', decision.blinded ? 'yes — assessed before reveal' : 'no — revealed first'],
      ['Assessed', esc(fmtWhen(decision.assessed_at))],
    ])}${corr ? `<h3>Corrections (${decision.corrections.length})</h3><ul>${corr}</ul>` : ''}`
      + `<p><button class="btn" id="rv-revise">Revise decision</button> <span style="color:var(--ink-3);font-size:12px">Revisions append the previous judgment to the corrections history — nothing is overwritten silently.</span></p></div>`;
  } else if (assessed && !revising) {
    formHtml = `<div class="card"><h2>Step 2 of 2 — judge agreement</h2>`
      + `<p style="color:var(--ink-2)">Assessment recorded ${esc(fmtWhen(assessed.assessed_at))}: `
      + `<strong>${esc(decisionLabel(assessed.assessment))}</strong> · ${esc(assessed.sufficiency)}.</p>`
      + (revealedAt ? '' : `<p><button class="btn" id="rv-reveal2">Reveal recorded verdict</button> `
        + `<span style="color:var(--ink-3);font-size:12px">Required unless you judge agreement undetermined.</span></p>`)
      + `<div class="field" style="margin-bottom:10px"><label for="rv-agreement">Verifier agreement</label><select id="rv-agreement">`
      + `<option value="">— select —</option>${AGREEMENTS.map((a) => `<option value="${a}">${a}</option>`).join('')}</select></div>`
      + `<div class="btn-row"><button class="btn primary" id="rv-complete">Complete review</button></div>`
      + `<div id="rv-form-msg" style="margin-top:8px"></div></div>`;
  } else {
    const pre = revising && decision ? decision : {};
    formHtml = `<div class="card"><h2>${revising ? 'Revise decision' : 'Step 1 of 2 — blinded assessment'}</h2>`
      + `<div class="filters"><div class="field"><label for="rv-assessment">Human assessment</label><select id="rv-assessment">`
      + `<option value="">— select —</option>${ASSESSMENTS.map((a) => `<option value="${a}"${pre.assessment === a ? ' selected' : ''}>${decisionLabel(a)}</option>`).join('')}</select></div>`
      + `<div class="field"><label for="rv-sufficiency">Evidence sufficiency</label><select id="rv-sufficiency">`
      + `<option value="">— select —</option>${SUFFICIENCY.map((s) => `<option value="${s}"${pre.sufficiency === s ? ' selected' : ''}>${s}</option>`).join('')}</select></div></div>`
      + `<div class="field" style="margin-bottom:10px"><label for="rv-reason">Reason (required — tie to specific observations)</label>`
      + `<textarea id="rv-reason" rows="3" style="width:100%" placeholder="e.g. snapshot shows confirmation_visible=true with exactly ['Padded Name']">${esc(pre.reason || '')}</textarea></div>`
      + `<div class="field" style="margin-bottom:10px"><label for="rv-missing">Missing evidence (required when inconclusive or insufficient)</label>`
      + `<textarea id="rv-missing" rows="2" style="width:100%" placeholder="What evidence would be needed?">${esc(pre.missing_evidence || '')}</textarea></div>`
      + (revising ? `<div class="field" style="margin-bottom:10px"><label for="rv-creason">Correction reason (required)</label>`
        + `<input id="rv-creason" type="text" style="width:100%" placeholder="Why is the previous judgment being changed?"></div>`
        + `<div class="field" style="margin-bottom:10px"><label for="rv-agreement">Verifier agreement</label><select id="rv-agreement">`
        + `<option value="">— select —</option>${AGREEMENTS.map((a) => `<option value="${a}"${decision.agreement === a ? ' selected' : ''}>${a}</option>`).join('')}</select></div>`
        : '')
      + `<div class="btn-row"><button class="btn primary" id="rv-save-assessment">${revising ? 'Save revision' : 'Record assessment'}</button></div>`
      + `<div id="rv-form-msg" style="margin-top:8px"></div></div>`;
  }

  const title = audit ? `Review Episode ${idx + 1}` : `Review ${trialId}`;
  const crumb = audit ? [[ctx.def.label, link('review', [], q)], [`Episode ${idx + 1}`]] : [['Mini-review queue', link('review')], [trialId]];
  const epRows = audit
    ? [
      ['Episode', `Episode ${idx + 1} of ${packet.episodes.length}`],
      ['Population', esc(ep.population)],
      ['Driver', `<strong>${esc(ep.driver_code)}</strong>`],
      ['Manifest', `<code>${esc((ep.manifest && ep.manifest.manifest_id) || '?')}</code>`],
      ['Condition', `${esc(ep.scenario_id)} / ${esc(ep.input_id)} · expected ${esc(JSON.stringify(ep.expected_stored_name))}`],
      ['Plan cell', revealedAt ? `<code>${esc(ep.plan_cell)}</code> (<code>${esc(ep.plan)}</code>)` : esc(redactedCell(ep.plan_cell))],
      ['Key', revealedAt ? `<code>${esc(key)}</code>` : '<span class="mask">•••</span> withheld until reveal'],
      ['Status', statusPill(decision ? 'reviewed' : 'pending')],
    ]
    : [
      ['Key', `<code>${esc(key)}</code>`],
      ['Condition', `${esc(ep.scenario_id)} / ${esc(ep.input_id)} · expected ${esc(JSON.stringify(ep.expected_stored_name))}`],
      ['Plan cell', `<code>${esc(ep.plan_cell)}</code> (<code>${esc(ep.plan)}</code>)`],
      ['Status', statusPill(decision ? 'reviewed' : assessed ? 'assessing' : 'pending')],
    ];
  const artRows = ['trace', 'snapshot', 'actions'].map((k) => {
    const a = ep.artifacts[k];
    const meta = `(${fmtInt(a.bytes)} bytes, sha256 <code>${esc(a.sha256.slice(0, 12))}…</code>, verified at packet build)`;
    if (audit && !revealedAt) {
      return [k, `${k} file ${meta} (direct file link unlocks after reveal: file names identify the driver — the live evidence above is rendered from this file)`];
    }
    return [k, `<code>${esc(a.path)}</code> ${meta}`];
  });
  // The inspector URL carries run/trial identifiers and that view
  // shows outcomes — in audit mode the link unlocks only after reveal.
  const inspector = (audit && !revealedAt)
    ? `<p style="color:var(--ink-3);font-size:12px">The full Evidence Inspector link unlocks after reveal — that view shows recorded outcomes and driver identity.</p>`
    : `<p><a class="btn" href="${link('evidence', [runId, trialId])}">Open full Evidence Inspector →</a> `
    + `<span style="color:var(--ink-3);font-size:12px">Warning: that view shows recorded outcomes${audit ? ' and driver identity' : ''} — using it before assessing unblinds you.</span></p>`;
  el.innerHTML = pageHead(title, crumb)
    + proofBanner(ctx)
    + (liveMissing.length ? `<div class="banner warn"><strong>Live evidence partially unreadable (${liveMissing.join(', ')})</strong> — packet copies are shown as fallback and labeled. Prefer the original files.</div>` : '')
    + `<div class="card"><h2>Episode</h2>${kvList(epRows)}${inspector}</div>`
    + `<div class="card"><h2>Task and postconditions</h2><p>${esc(packet.task)}</p>`
    + `<div class="table-wrap"><table class="data"><thead><tr><th>ID</th><th>Postcondition</th><th>Judge</th></tr></thead><tbody>${guide}</tbody></table></div>`
    + `<p style="color:var(--ink-3);font-size:12.5px">${esc(packet.p4_note)}</p></div>`
    + `<div class="card" id="rv-recorded"><h2>Recorded verdict (masked until reveal)</h2>${recordedCard}</div>`
    + `<div class="card"><h2>Evidence</h2>${evidenceHtml}</div>`
    + `<div class="card"><h2>Screenshots</h2>${shots}</div>`
    + `<div class="card"><h2>Artifact references</h2>${kvList(artRows)}${ep.gaps.length ? `<h3>Known gaps</h3><ul>${ep.gaps.map((g) => `<li>${esc(g)}</li>`).join('')}</ul>` : ''}</div>`
    + formHtml;

  const search = el.querySelector('#trace-search');
  if (search) search.addEventListener('input', () => {
    const q = search.value.trim().toLowerCase();
    el.querySelectorAll('#trace-timeline li').forEach((li) => {
      li.style.display = !q || (li.dataset.text || '').includes(q) ? '' : 'none';
    });
  });
  const itemLink = audit ? ['ep', String(idx)] : [runId, trialId];
  const markRevealed = () => {
    const at = nowIso();
    const cur = state.decisions[key];
    if (cur) cur.revealed_at = cur.revealed_at || at;
    else {
      const part = state.partials[key] || {};
      part.revealed_at = part.revealed_at || at;
      state.partials[key] = part;
    }
    saveState(store, state, ctx.def.storageKey);
    window.location.reload();
  };
  for (const id of ['#rv-reveal', '#rv-reveal2']) {
    const btn = el.querySelector(id);
    if (btn) btn.addEventListener('click', markRevealed);
  }
  const reviseBtn = el.querySelector('#rv-revise');
  if (reviseBtn) reviseBtn.addEventListener('click', () => {
    window.location.hash = link('review', itemLink, { ...q, revise: '1' });
  });
  const requireReviewer = (msg) => {
    if (state.reviewer) return true;
    msg.innerHTML = `<div class="banner bad"><strong>Reviewer name required.</strong> Set it on the <a href="${link('review', [], q)}">queue page</a> first.</div>`;
    return false;
  };
  const saveChecks = el.querySelector('#rv-save-checks');
  if (saveChecks) saveChecks.addEventListener('click', () => {
    const msg = el.querySelector('#rv-form-msg');
    if (!requireReviewer(msg)) return;
    const at = nowIso();
    const unauditable = el.querySelector('#rv-unauditable').checked;
    const note = el.querySelector('#rv-note').value.trim();
    const problems = [];
    const checks = {};
    if (unauditable) {
      if (!note) problems.push('a reason is required when unauditable');
    } else {
      for (const c of AUDIT_CHECKS) {
        const v = el.querySelector(`#rv-${c.toLowerCase()}`).value;
        if (v !== 'true' && v !== 'false') problems.push(`choose true or false for ${c}`);
        else checks[c] = v === 'true';
      }
    }
    let corrections = (decision && decision.corrections) || [];
    if (revising && decision) {
      const creason = el.querySelector('#rv-creason').value.trim();
      if (!creason) problems.push('correction reason is required');
      const { corrections: _dropped, ...previous } = decision;
      corrections = [...corrections, { at, previous, reason: creason }];
    }
    if (problems.length) {
      msg.innerHTML = `<div class="banner bad"><strong>Cannot record:</strong> ${problems.map(esc).join('<br>')}</div>`;
      return;
    }
    const revealed = (decision && decision.revealed_at) || null;
    const candidate = unauditable
      ? {
        verdict: 'unauditable', reason: note,
        blinded: revealed == null || at <= revealed,
        assessed_at: at, revealed_at: revealed, corrections,
      }
      : {
        checks, note,
        blinded: revealed == null || at <= revealed,
        assessed_at: at, revealed_at: revealed, corrections,
      };
    const errs = validateAuditDecision(key, packet.episodes.map((e) => e.key), candidate);
    if (errs.length) {
      msg.innerHTML = `<div class="banner bad"><strong>Cannot record:</strong> ${errs.map(esc).join('<br>')}</div>`;
      return;
    }
    state.decisions[key] = candidate;
    saveState(store, state, ctx.def.storageKey);
    window.location.hash = link('review', itemLink, q);
    window.location.reload();
  });
  const saveAssessment = el.querySelector('#rv-save-assessment');
  if (saveAssessment) saveAssessment.addEventListener('click', () => {
    const msg = el.querySelector('#rv-form-msg');
    if (!requireReviewer(msg)) return;
    const at = nowIso();
    const assessment = el.querySelector('#rv-assessment').value;
    const sufficiency = el.querySelector('#rv-sufficiency').value;
    const reason = el.querySelector('#rv-reason').value.trim();
    const missing = el.querySelector('#rv-missing').value.trim();
    const problems = [];
    if (!ASSESSMENTS.includes(assessment)) problems.push('choose a human assessment');
    if (!SUFFICIENCY.includes(sufficiency)) problems.push('choose evidence sufficiency');
    if (!reason) problems.push('reason is required');
    if ((assessment === 'inconclusive' || sufficiency === 'insufficient') && !missing) {
      problems.push('missing evidence is required when inconclusive or insufficient');
    }
    let corrections = (decision && decision.corrections) || [];
    let agreement = '';
    if (revising && decision) {
      const creason = el.querySelector('#rv-creason').value.trim();
      agreement = el.querySelector('#rv-agreement').value;
      if (!creason) problems.push('correction reason is required');
      if (!AGREEMENTS.includes(agreement)) problems.push('choose verifier agreement');
      const { corrections: _dropped, ...previous } = decision;
      corrections = [...corrections, { at, previous, reason: creason }];
    }
    if (problems.length) {
      msg.innerHTML = `<div class="banner bad"><strong>Cannot record:</strong> ${problems.map(esc).join('<br>')}</div>`;
      return;
    }
    const revealed = (decision && decision.revealed_at) || (partial && partial.revealed_at) || null;
    if (revising) {
      const candidate = {
        assessment, agreement, sufficiency, reason, missing_evidence: missing,
        blinded: revealed == null || at <= revealed,
        assessed_at: at, revealed_at: revealed, corrections,
      };
      const errs = validateDecision(key, packet.episodes.map((e) => e.key), candidate);
      if (errs.length) {
        msg.innerHTML = `<div class="banner bad"><strong>Cannot record:</strong> ${errs.map(esc).join('<br>')}</div>`;
        return;
      }
      state.decisions[key] = candidate;
      delete state.partials[key];
    } else {
      state.partials[key] = {
        assessment, sufficiency, reason, missing_evidence: missing,
        assessed_at: at, revealed_at: revealed,
      };
    }
    saveState(store, state, ctx.def.storageKey);
    window.location.hash = link('review', [runId, trialId]);
    window.location.reload();
  });
  const completeBtn = el.querySelector('#rv-complete');
  if (completeBtn) completeBtn.addEventListener('click', () => {
    const msg = el.querySelector('#rv-form-msg');
    if (!requireReviewer(msg)) return;
    const agreement = el.querySelector('#rv-agreement').value;
    const part = state.partials[key] || {};
    const candidate = {
      assessment: part.assessment, agreement, sufficiency: part.sufficiency,
      reason: part.reason, missing_evidence: part.missing_evidence,
      blinded: part.revealed_at == null || part.assessed_at <= part.revealed_at,
      assessed_at: part.assessed_at, revealed_at: part.revealed_at || null,
      corrections: [],
    };
    const errs = validateDecision(key, packet.episodes.map((e) => e.key), candidate);
    if (errs.length) {
      msg.innerHTML = `<div class="banner bad"><strong>Cannot record:</strong> ${errs.map(esc).join('<br>')}</div>`;
      return;
    }
    state.decisions[key] = candidate;
    delete state.partials[key];
    saveState(store, state, ctx.def.storageKey);
    window.location.hash = link('review', [runId, trialId]);
    window.location.reload();
  });
}
