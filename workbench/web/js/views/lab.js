/* Campaign Lab: repeatable execution campaigns and deep analytics.
 * Every figure carries its denominator; aggregates drill down into
 * the underlying executions and evidence. */
import { api, queryString } from '../api.js';
import { esc, fmtMs, fmtWhen, fmtInt, fmtPct, verdictPill, statusPill, driverLabel, scenarioLabel, workflowLabel, banner, emptyState, svgOpen, tabsHtml, tabsInit, hero, heroField, navySection } from '../format.js';
import { C, matrixSvg, latencySvg, hbars, saucePanelHtml, sauceStressPanelHtml } from './analytics.js';

const SAUCE_PRESETS = [
  { label: 'Successful checkout',
    params: { login_case: 'standard', cart_preset: 'backpack+bike-light', sort: 'az', checkout_case: 'complete' } },
  { label: 'Locked-out login', params: { login_case: 'locked-out' } },
  { label: 'Empty cart', params: { cart_preset: 'empty-cart' } },
  { label: 'Missing postal code', params: { checkout_case: 'missing-postal' } },
];

const STRESS_ACCOUNTS = [
  ['standard', 'Control'], ['glitch', 'Slow login'], ['problem', 'Problem user'],
];
const STRESS_SORTS = ['az', 'za', 'lohi'];
const STRESS_REMOVES = [['last-added', 'remove'], ['none', 'keep']];
const STRESS_PRESETS = [];
STRESS_ACCOUNTS.forEach(([account, accountLabel]) => {
  STRESS_SORTS.forEach((sort) => {
    STRESS_REMOVES.forEach(([remove_item, removeLabel]) => {
      STRESS_PRESETS.push({
        label: `${accountLabel} · ${sort} · ${removeLabel}`,
        params: { account, cart_preset: 'backpack+bike-light', sort, remove_item },
      });
    });
  });
});
// The pilot showed the slow account blocks both drivers at the sort
// step, so two no-sort conditions isolate its downstream behaviour.
STRESS_REMOVES.forEach(([remove_item, removeLabel]) => {
  STRESS_PRESETS.push({
    label: `Slow login · none · ${removeLabel}`,
    params: { account: 'glitch', cart_preset: 'backpack+bike-light', sort: 'none', remove_item },
  });
});

function campaignPill(status) {
  const map = {
    draft: ['warn', 'Draft', 'st-pending'], running: ['info', 'Running', 'st-running'],
    paused: ['warn', 'Paused', 'act-pause'], cancelled: ['warn', 'Cancelled', 'st-pending'],
    completed: ['ok', 'Completed', 'st-pass'], failed: ['bad', 'Failed', 'st-fail'],
  };
  const [cls, label, ic] = map[status] || ['warn', status || '—', 'st-pending'];
  return `<span class="pill ${cls}"><svg aria-hidden="true"><use href="#${ic}"/></svg>${esc(label)}</span>`;
}

function historyHref(params) {
  return `#/history${queryString(params)}`;
}

export async function viewLab(el, badges, extra) {
  const campaignId = extra && extra.param
    ? decodeURIComponent(extra.param) : null;
  if (campaignId) return viewDetail(el, badges, campaignId);
  return viewList(el);
}

async function viewList(el) {
  let workflows = [];
  try {
    ({ workflows } = await api.workflows());
  } catch { /* form shows the error */ }
  const runnable = workflows.filter((w) => !w.future);
  let selected = runnable.find((w) => w.workflow_id === 'saucedemo-order')
    || runnable[0] || null;
  let conditions = SAUCE_PRESETS.map((p) => ({
    label: p.label, params: JSON.stringify(p.params),
  }));

  async function loadTable() {
    const box = el.querySelector('#lab-list');
    try {
      const { campaigns } = await api.campaigns();
      if (!campaigns.length) {
        box.innerHTML = `<div class="empty"><svg class="empty-mark" aria-hidden="true"><use href="#empty-flask"/></svg><div><h2>No campaigns yet</h2>`
          + `<p>Define one below — every trial runs for real in its own fresh browser.</p></div></div>`;
        return;
      }
      box.innerHTML = `<div class="table-wrap"><table class="data"><thead><tr>`
        + `<th>Campaign</th><th>Workflow</th><th>Status</th><th>Progress</th><th>Created</th></tr></thead><tbody>`
        + campaigns.map((c) => {
          const pct = c.total_trials
            ? Math.round((100 * c.finished_trials) / c.total_trials) : 0;
          return `<tr><td><a href="#/lab/${encodeURIComponent(c.id)}">${esc(c.name)}</a></td>`
            + `<td>${esc(workflowLabel(c.workflow_id))}</td>`
            + `<td>${campaignPill(c.status)}</td>`
            + `<td class="mono">${fmtInt(c.finished_trials)}/${fmtInt(c.total_trials)} (${pct}%)</td>`
            + `<td class="mono">${esc(fmtWhen(c.created_at))}</td></tr>`;
        }).join('') + `</tbody></table></div>`;
    } catch {
      box.innerHTML = `<div class="empty"><svg class="empty-mark" aria-hidden="true"><use href="#empty-server"/></svg><div><h2>Campaigns unavailable</h2><p>Could not reach the server.</p></div></div>`;
    }
  }

  function conditionRows() {
    return conditions.map((c, i) =>
      `<div class="cond-row" data-i="${i}"><div class="field"><label for="lc-label-${i}">Label</label>`
      + `<input type="text" id="lc-label-${i}" data-c="label" value="${esc(c.label)}"></div>`
      + `<div class="field grow"><label for="lc-params-${i}">Parameters (JSON)</label>`
      + `<input type="text" id="lc-params-${i}" data-c="params" value="${esc(c.params)}" spellcheck="false"></div>`
      + `<button class="btn danger" data-del="${i}" aria-label="Remove condition">✕</button></div>`).join('');
  }

  function render() {
    const wf = selected;
    el.innerHTML = hero({
      kicker: 'Build · campaigns',
      head: '<h1 id="page-h1">Campaign Lab</h1>',
      lede: `Define a <strong>repeatable browser-execution campaign</strong>: fixed conditions, `
        + `configurable repetitions, one browser at a time with fresh contexts and controlled pacing. `
        + `Every trial is a real execution with independent verification — nothing is simulated.`,
      ctas: '<a class="btn primary" href="#lab-form">Create campaign</a>',
      field: heroField('lb', ['#a5f3c8', '.5', '.24'], ['#fbcfe8', '.48', '.2'], [880, 300, 150, 162]),
    })
      + `<div id="lab-msg"></div>`
      + `<div class="panel flush float art-top float-lift"><div class="panel-head"><h2>Campaigns</h2></div><div id="lab-list"></div></div>`
      + `<div class="panel"><h2>New campaign</h2><form id="lab-form">`
      + `<div class="field"><label for="lc-name">Name</label>`
      + `<input type="text" id="lc-name" name="name" value="SauceDemo balanced v1" maxlength="120" required></div>`
      + `<div class="field"><label for="lc-workflow">Workflow</label><select id="lc-workflow" name="workflow_id">`
      + runnable.map((w) => `<option value="${esc(w.workflow_id)}"${wf && w.workflow_id === wf.workflow_id ? ' selected' : ''}>`
        + `${esc(w.title)} — ${esc(w.environment)}</option>`).join('')
      + `</select></div>`
      + `<div class="field"><span class="lbl">Drivers</span><div class="checks-inline" id="lc-drivers">`
      + (wf ? wf.drivers.map((d) => `<label><input type="checkbox" name="drivers" value="${esc(d)}" checked> ${esc(driverLabel(d))}</label>`).join('')
        : '<span class="dim">No runnable workflows.</span>')
      + `</div></div>`
      + `<div class="field"><span class="lbl">Conditions</span>`
      + `<div id="lc-conditions">${conditionRows()}</div>`
      + `<div class="btn-row" style="margin-top:8px"><button class="btn" type="button" id="lc-add">Add condition</button>`
      + `<button class="btn" type="button" id="lc-presets">Load SauceDemo presets</button>`
      + `<button class="btn" type="button" id="lc-stress-presets">Load stress presets (v2)</button></div>`
      + `<div class="help">Each condition is a label plus the workflow parameters to run. Unspecified parameters use the workflow defaults.</div></div>`
      + `<div class="split"><div class="field"><label for="lc-reps">Repetitions per driver × condition</label>`
      + `<input type="number" id="lc-reps" name="repetitions" value="10" min="1" max="500"></div>`
      + `<div class="field"><label for="lc-pacing">Pacing between trials (ms)</label>`
      + `<input type="number" id="lc-pacing" name="pacing_ms" value="2000" min="0" max="120000"></div>`
      + `<div class="field"><label for="lc-stop">Stop after N consecutive executor errors</label>`
      + `<input type="number" id="lc-stop" name="stop_after_consecutive_errors" value="5" min="1" max="100"></div></div>`
      + `<div class="help">Total trials = repetitions × drivers × conditions (max 2000). Verified-failure verdicts are legitimate `
      + `outcomes and never trigger the stop safeguard — only infrastructure errors do.</div>`
      + `<div class="btn-row"><button class="btn primary" type="submit" id="lc-create">Create campaign</button></div>`
      + `</form></div>`;
    wire();
    loadTable();
  }

  function readConditions() {
    const rows = [];
    el.querySelectorAll('.cond-row').forEach((row) => {
      rows.push({
        label: row.querySelector('[data-c="label"]').value,
        params: row.querySelector('[data-c="params"]').value,
      });
    });
    return rows;
  }

  function wire() {
    el.querySelector('#lc-workflow').addEventListener('change', (e) => {
      selected = runnable.find((w) => w.workflow_id === e.target.value) || null;
      conditions = readConditions();
      render();
    });
    el.querySelector('#lc-add').addEventListener('click', () => {
      conditions = readConditions();
      conditions.push({ label: `Condition ${conditions.length + 1}`, params: '{}' });
      el.querySelector('#lc-conditions').innerHTML = conditionRows();
      wireConditions();
    });
    el.querySelector('#lc-presets').addEventListener('click', () => {
      conditions = SAUCE_PRESETS.map((p) => ({ label: p.label, params: JSON.stringify(p.params) }));
      el.querySelector('#lc-conditions').innerHTML = conditionRows();
      wireConditions();
    });
    el.querySelector('#lc-stress-presets').addEventListener('click', () => {
      conditions = STRESS_PRESETS.map((p) => ({ label: p.label, params: JSON.stringify(p.params) }));
      el.querySelector('#lc-conditions').innerHTML = conditionRows();
      wireConditions();
    });
    wireConditions();
    el.querySelector('#lab-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const msg = el.querySelector('#lab-msg');
      const btn = el.querySelector('#lc-create');
      btn.disabled = true;
      try {
        const form = e.target;
        const drivers = [...form.querySelectorAll('input[name="drivers"]:checked')].map((c) => c.value);
        const parsed = readConditions().map((c) => {
          let params;
          try {
            params = c.params.trim() ? JSON.parse(c.params) : {};
          } catch {
            throw new Error(`condition "${c.label || '?'}": parameters must be valid JSON`);
          }
          if (params === null || typeof params !== 'object' || Array.isArray(params)) {
            throw new Error(`condition "${c.label || '?'}": parameters must be a JSON object`);
          }
          return { label: c.label, params };
        });
        const { id } = await api.createCampaign({
          name: form.elements['name'].value,
          workflow_id: form.elements['workflow_id'].value,
          drivers,
          conditions: parsed,
          repetitions: Number(form.elements['repetitions'].value),
          pacing_ms: Number(form.elements['pacing_ms'].value),
          stop_after_consecutive_errors: Number(form.elements['stop_after_consecutive_errors'].value),
        });
        window.location.hash = `#/lab/${encodeURIComponent(id)}`;
      } catch (err) {
        msg.innerHTML = banner('bad', `<strong>Could not create:</strong> ${esc(err.message)}`);
        btn.disabled = false;
      }
    });
  }

  function wireConditions() {
    el.querySelectorAll('[data-del]').forEach((btn) => {
      btn.addEventListener('click', () => {
        conditions = readConditions();
        conditions.splice(Number(btn.dataset.del), 1);
        el.querySelector('#lc-conditions').innerHTML = conditionRows();
        wireConditions();
      });
    });
  }

  render();
  return null;
}

function pairedSvg(paired) {
  const s = paired.summary || {};
  const W = 640; const lx = 150; const ty = 40; const cw = 215; const ch = 96;
  const H = ty + 2 * ch + 14;
  const cells = [
    { r: 0, c: 0, n: s.both_success || 0, label: 'both succeed', fill: C.ok },
    { r: 0, c: 1, n: s.chimera_only || 0, label: 'Chimera only', fill: C.warn },
    { r: 1, c: 0, n: s.baseline_only || 0, label: 'Baseline A only', fill: C.warn },
    { r: 1, c: 1, n: s.both_failure || 0, label: 'both fail', fill: C.bad },
  ];
  let h = svgOpen(W, H, 'Paired driver outcomes');
  h += `<text x="${lx + cw / 2}" y="14" text-anchor="middle" class="tick">Baseline A succeeds</text>`
    + `<text x="${lx + cw * 1.5}" y="14" text-anchor="middle" class="tick">Baseline A fails</text>`
    + `<text x="${lx - 10}" y="${ty + ch / 2 + 4}" text-anchor="end" class="tick">Chimera succeeds</text>`
    + `<text x="${lx - 10}" y="${ty + ch * 1.5 + 4}" text-anchor="end" class="tick">Chimera fails</text>`;
  cells.forEach((cell) => {
    const x = lx + cell.c * cw + 3; const y = ty + cell.r * ch + 3;
    const op = cell.n ? 0.85 : 0.25;
    h += `<rect x="${x}" y="${y}" width="${cw - 6}" height="${ch - 6}" rx="6" fill="${cell.fill}" opacity="${op}">`
      + `<title>${cell.n} pairs: ${cell.label}</title></rect>`
      + `<text x="${x + (cw - 6) / 2}" y="${y + (ch - 6) / 2 - 4}" text-anchor="middle" class="val">${fmtInt(cell.n)} pairs</text>`
      + `<text x="${x + (cw - 6) / 2}" y="${y + (ch - 6) / 2 + 16}" text-anchor="middle" class="tick">${cell.label}</text>`;
  });
  return h + '</svg>';
}

function heatSvg(byScenario, campaignId) {
  const scenarios = [...new Set(byScenario.map((r) => r.scenario_id))].sort();
  const categories = [...new Set(byScenario.map((r) => r.category))].sort();
  if (!scenarios.length || !categories.length) {
    return '<p class="dim">No failed, errored, or cancelled runs in scope.</p>';
  }
  const cw = 130; const ch = 46; const lx = 300; const ty = 30;
  const W = lx + categories.length * cw + 14;
  const H = ty + scenarios.length * ch + 10;
  const max = Math.max(1, ...byScenario.map((r) => r.n));
  const byKey = new Map(byScenario.map((r) => [`${r.scenario_id}|${r.category}`, r.n]));
  let h = svgOpen(W, H, 'Failure heatmap by condition and category');
  categories.forEach((cat, j) => {
    h += `<text x="${lx + j * cw + cw / 2}" y="14" text-anchor="middle" class="tick">${esc(cat)}</text>`;
  });
  scenarios.forEach((sc, i) => {
    h += `<text x="${lx - 10}" y="${ty + i * ch + ch / 2 + 4}" text-anchor="end" class="tick">${esc(scenarioLabel(sc))}</text>`;
    categories.forEach((cat, j) => {
      const n = byKey.get(`${sc}|${cat}`) || 0;
      const x = lx + j * cw + 3; const y = ty + i * ch + 3;
      const href = historyHref({ campaign_id: campaignId, scenario_id: sc });
      h += `<a href="${esc(href)}"><title>${n} failures · ${esc(sc)} · ${esc(cat)}</title>`
        + `<rect x="${x}" y="${y}" width="${cw - 6}" height="${ch - 6}" rx="6" fill="${C.bad}" opacity="${(0.12 + 0.78 * (n / max)).toFixed(2)}"/>`
        + `<text x="${x + (cw - 6) / 2}" y="${y + (ch - 6) / 2 + 5}" text-anchor="middle" class="val">${n || ''}</text></a>`;
    });
  });
  return h + '</svg>';
}

function trendSvg(buckets) {
  const W = 640; const H = 220; const padL = 44; const padB = 34; const padT = 16;
  const n = Math.max(1, buckets.length);
  const bw = (W - padL - 14) / n;
  let h = svgOpen(W, H, 'Success rate across trial order');
  [0.25, 0.5, 0.75, 1].forEach((f) => {
    const y = padT + (H - padT - padB) * (1 - f);
    h += `<line x1="${padL}" y1="${y}" x2="${W - 14}" y2="${y}" class="grid"/>`
      + `<text x="${padL - 6}" y="${y + 4}" text-anchor="end" class="tick">${Math.round(f * 100)}%</text>`;
  });
  buckets.forEach((b, i) => {
    const x = padL + i * bw + 3; const w = bw - 6;
    const rate = b.success_rate;
    if (rate === null || rate === undefined) {
      h += `<rect x="${x.toFixed(1)}" y="${padT}" width="${w.toFixed(1)}" height="${(H - padT - padB).toFixed(1)}" fill="none" stroke="${C.grid}" stroke-dasharray="4 3">`
        + `<title>trials ${b.lo}–${b.hi}: no verified runs</title></rect>`;
    } else {
      const bh = (H - padT - padB) * rate;
      const fill = rate >= 0.95 ? C.ok : rate >= 0.5 ? C.warn : C.bad;
      h += `<rect x="${x.toFixed(1)}" y="${(H - padB - bh).toFixed(1)}" width="${w.toFixed(1)}" height="${Math.max(bh, 2).toFixed(1)}" rx="3" fill="${fill}" opacity="0.85">`
        + `<title>trials ${b.lo}–${b.hi}: ${fmtPct(rate)} verified-ok, n=${b.verified} verified, p50 ${fmtMs(b.p50)}</title></rect>`
        + `<text x="${(x + w / 2).toFixed(1)}" y="${(H - padB - bh - 5).toFixed(1)}" text-anchor="middle" class="val">${fmtPct(rate)}</text>`;
    }
    h += `<text x="${(x + w / 2).toFixed(1)}" y="${H - 12}" text-anchor="middle" class="tick">${b.lo}–${b.hi}</text>`;
  });
  return h + '</svg>';
}

async function viewDetail(el, badges, campaignId) {
  let timer = null;
  let lastFinished = -1;
  const state = { driver: '' };
  const table = { page: 1, page_size: 20, q: '', sort: 'trial_seq' };

  function params(extra) {
    return queryString({
      campaign_id: campaignId, driver: state.driver, ...(extra || {}),
    });
  }

  function headerHtml(c) {
    const pct = c.total_trials ? Math.round((100 * c.finished_trials) / c.total_trials) : 0;
    const counts = c.trial_counts || {};
    const countLine = Object.keys(counts).sort().map((k) => `${k}: ${counts[k]}`).join(' · ') || 'no trials yet';
    const live = c.status === 'running';
    let controls = '';
    if (c.status === 'draft') controls = `<button class="btn primary" data-act="start">Start campaign</button>`;
    else if (c.status === 'running') controls = `<button class="btn" data-act="pause">Pause</button> <button class="btn danger" data-act="cancel">Cancel</button>`;
    else if (c.status === 'paused') controls = `<button class="btn primary" data-act="resume">Resume</button> <button class="btn danger" data-act="cancel">Cancel</button>`;
    const cfg = c.config || {};
    const condLine = (cfg.conditions || []).map((k) => esc(k.label)).join(' · ') || '—';
    const ver = c.versions || {};
    return `<p><a href="#/lab">← All campaigns</a></p>`
      + `<div class="runhead"><div><h1>${esc(c.name)}</h1><span class="id">${esc(c.id)}</span></div></div>`
      + `<div style="margin:10px 0 18px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">${campaignPill(c.status)}`
      + `<span class="pill">${esc(workflowLabel(c.workflow_id))}</span>`
      + `<span class="dim">${esc((cfg.drivers || []).join(' + '))} · ${condLine} · ${fmtInt(cfg.repetitions)} reps · `
      + `pace ${fmtInt(cfg.pacing_ms)} ms</span></div>`
      + (c.stop_reason ? `<div class="banner warn" role="status"><strong>Stopped:</strong> ${esc(c.stop_reason)}</div>` : '')
      + (c.error ? `<div class="banner bad" role="alert"><strong>Campaign error:</strong> ${esc(c.error)}</div>` : '')
      + navySection('Campaign progress', `<h2>Progress</h2>`
      + `<div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">`
      + `<span class="pulse${live ? ' live' : ''}" aria-hidden="true"></span>`
      + `<strong class="mono">${fmtInt(c.finished_trials)}/${fmtInt(c.total_trials)} trials (${pct}%)</strong>`
      + `<span class="dim">${esc(countLine)}</span>`
      + (c.current_exec_id ? `<span class="dim">live trial: <a href="#/run/${encodeURIComponent(c.current_exec_id)}">${esc(c.current_exec_id.slice(0, 8))}</a></span>` : '')
      + `<span style="flex:1"></span><span class="btn-row">${controls}</span></div>`
      + `<div class="progress"><div class="bar"><div class="fill" style="--fill:${(pct / 100).toFixed(3)}"></div></div></div>`
      + `<p class="caption">Sequential execution, one browser at a time, fresh context per trial. `
      + `Started ${esc(fmtWhen(c.started_at))}${c.completed_at ? ` · finished ${esc(fmtWhen(c.completed_at))}` : ''} · `
      + `agent ${esc(ver.chimera_agent || '—')}${ver.saucedemo_adapter ? ` · store ${esc(ver.saucedemo_adapter.origin || '—')}` : ''}</p>`);
  }

  async function refreshHeader() {
    try {
      const { campaign } = await api.campaign(campaignId);
      const box = el.querySelector('#lab-head');
      if (box) {
        box.innerHTML = headerHtml(campaign);
        wireControls(box);
      }
      badges.innerHTML = campaignPill(campaign.status);
      if (campaign.finished_trials !== lastFinished) {
        lastFinished = campaign.finished_trials;
        loadAnalytics();
        loadTrials();
      }
      return campaign.status;
    } catch {
      return null;
    }
  }

  function wireControls(scope) {
    scope.querySelectorAll('[data-act]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        btn.disabled = true;
        try {
          await api.campaignAction(campaignId, btn.dataset.act);
        } catch (err) {
          const box = el.querySelector('#lab-head');
          box.insertAdjacentHTML('afterbegin',
            banner('bad', `<strong>Action failed:</strong> ${esc(err.message)}`));
        }
        refreshHeader();
      });
    });
  }

  function matrixInterpretation(cells) {
    const n = cells.reduce((s, c) => s + c.n, 0);
    const ok = cells.reduce((s, c) => s + c.ok, 0);
    const verified = cells.reduce((s, c) => s + c.ok + c.bad, 0);
    if (!n) return 'No trials finished yet — figures appear as trials complete.';
    return `${fmtInt(ok)} of ${fmtInt(verified)} verified trials succeeded (${fmtPct(verified ? ok / verified : null)}). `
      + `Select any cell to open its trials.`;
  }

  async function loadAnalytics() {
    const box = el.querySelector('#lab-body');
    if (!box) return;
    box.querySelectorAll('[id^="lab-p-"]').forEach((slot) => {
      if (slot.id !== 'lab-p-trials') slot.innerHTML = `<p class="dim">Computing figures…</p>`;
    });
    try {
      const [mx, lat, fail, dr, vc, sc, sst, pr, sd, tr, st] = await Promise.all([
        api.analytics('matrix', params()),
        api.analytics('latency', params()),
        api.analytics('failures', params()),
        api.analytics('drivers', params()),
        api.analytics('verification', params()),
        api.analytics('sauce', params()),
        api.analytics('sauce-stress', params()),
        api.analytics('paired', params()),
        api.analytics('stage-durations', params()),
        api.analytics('campaign-trends', params()),
        api.analytics('stages', params()),
      ]);
      const linkFor = (c) => historyHref({
        campaign_id: campaignId, scenario_id: c.scenario_id, driver: c.driver,
      });
      const agree = pr.denominator
        ? `${fmtInt((pr.summary.both_success || 0) + (pr.summary.both_failure || 0))}/${fmtInt(pr.denominator)} adjudicated pairs agree (${fmtPct(pr.agreement)})`
        : 'no adjudicated pairs yet';
      const slow = (sd.stages || []).filter((s) => s.p50 !== null)
        .sort((a, b) => b.p50 - a.p50)[0];
      const stageNote = slow
        ? `Slowest measured stage: <strong>${esc(slow.stage)}</strong> on ${esc(driverLabel(slow.driver))} (p50 ${fmtMs(slow.p50)} over ${fmtInt(slow.n)} measurements).`
        : 'No stage durations measured yet.';
      const trendNote = (tr.buckets || []).length
        ? `First bucket ${fmtPct(tr.buckets[0].success_rate)} → last bucket ${fmtPct(tr.buckets[tr.buckets.length - 1].success_rate)} `
        + `(descriptive across trial order, not a significance claim).`
        : (tr.reason ? esc(tr.reason) : 'No trials yet.');
      // Summary-first: the same numbered panels grouped into tabs.
      // Headings, figure code, #lab-false, and loaders are unchanged.
      const matrixHtml = `<div class="panel"><h2>1 · Campaign outcome matrix</h2><figure class="viz">${matrixSvg(mx.cells, linkFor)}</figure>`
        + `<p class="caption">${esc(matrixInterpretation(mx.cells))}</p></div>`;
      const driversHtml = `<div class="split">`
        + `<div class="panel"><h2>2 · Driver duel</h2><figure class="viz">${hbars(
          dr.drivers.map((d) => ({ label: driverLabel(d.driver), rate: d.success_rate, d })),
          'rate', 'Driver success rates', () => C.cyan,
          (r) => `${fmtPct(r.rate)} · n=${r.d.verified} verified · p50 ${fmtMs(r.d.p50)}`)}</figure>`
        + `<p class="caption">Verified-success rate per driver. <a href="${historyHref({ campaign_id: campaignId })}">Open all trials</a>.</p></div>`
        + `<div class="panel"><h2>Paired outcomes</h2><figure class="viz">${pairedSvg(pr)}</figure>`
        + `<p class="caption">${esc(agree)} · ${fmtInt(pr.summary.unpaired || 0)} unpaired · `
        + `${fmtInt(pr.summary.unknown || 0)} with an unverified side. Pairs match by condition and repetition order.</p></div>`
        + `</div>`;
      const latencyHtml = `<div class="panel"><h2>3 · Latency landscape</h2><figure class="viz">${latencySvg(lat)}</figure>`
        + `<p class="caption">Run durations over <strong>${fmtInt(lat.overall.n)} measured runs</strong> `
        + `(p50 ${fmtMs(lat.overall.p50)} · p90 ${fmtMs(lat.overall.p90)} · p95 ${fmtMs(lat.overall.p95)}).</p></div>`;
      const stagesHtml = `<div class="panel"><h2>4 · Stage durations by driver</h2><figure class="viz">${hbars(
        (sd.stages || []).map((s) => ({ label: `${s.stage} · ${driverLabel(s.driver)}`, p50: s.p50 || 0, s })),
        'p50', 'Stage p50 durations',
        (r) => (r.s.driver === 'chimera' ? C.cyan : C.vio),
        (r) => (r.s.p50 === null ? `unmeasured · n=0` : `${fmtMs(r.s.p50)} · n=${r.s.n}${r.s.missing_durations ? ` (+${r.s.missing_durations} unmeasured)` : ''}${r.s.sampled ? ' · sampled' : ''}`))}</figure>`
        + `<p class="caption">${stageNote} Each run's final capture has no measured end. `
        + `Per-trial waterfalls live on the <a href="${historyHref({ campaign_id: campaignId })}">trial pages</a>.</p></div>`;
      const failHtml = `<div class="panel"><h2>5 · Failure heatmap</h2><figure class="viz">${heatSvg(fail.by_scenario || [], campaignId)}</figure>`
        + `<p class="caption"><strong>${fmtInt(fail.total_failures)} failed, errored, or cancelled trials</strong>. `
        + `Darker cells hold more trials; select any cell to open its trials.</p></div>`
        + `<div class="panel"><h2>7 · False-success drill-down</h2><div id="lab-false"></div></div>`;
      const funnelsHtml = saucePanelHtml(sc) + sauceStressPanelHtml(sst);
      const qualityHtml = `<div class="panel"><h2>8 · Performance across repetitions</h2><figure class="viz">${trendSvg(tr.buckets || [])}</figure>`
        + `<p class="caption">${trendNote}</p></div>`
        + `<div class="panel"><h2>9 · Per-action reliability</h2><figure class="viz">${hbars(
          st.stages.map((s) => ({ label: `${s.action} (${s.errors} errors)`, avg: s.avg_ms || 0, s })),
          'avg', 'Mean action durations', (r) => (r.s.errors ? C.warn : C.ok),
          (r) => `${r.s.avg_ms === null ? 'unmeasured' : fmtMs(r.s.avg_ms)} · n=${r.s.n}`)}</figure>`
        + `<p class="caption">Mean time per browser-action type across <strong>observed actions only</strong>, with error counts. `
        + `Verification coverage: ${(vc.checks || []).map((c) => `${esc(c.check_id)} ${c.satisfied}/${c.n}`).join(' · ') || 'none yet'} satisfied/total.</p></div>`;
      const fill = (key, html) => {
        const slot = box.querySelector(`#lab-p-${key}`);
        if (slot) slot.innerHTML = html;
      };
      fill('matrix', matrixHtml);
      fill('drivers', driversHtml);
      fill('latency', latencyHtml);
      fill('stages', stagesHtml);
      fill('failures', failHtml);
      fill('funnels', funnelsHtml);
      fill('quality', qualityHtml);
      loadFalse(box);
    } catch (err) {
      const slot = box.querySelector('#lab-p-matrix');
      if (slot) slot.innerHTML = `<div class="banner bad" role="alert"><strong>Analytics unavailable:</strong> ${esc(err.message)}</div>`;
    }
  }

  async function loadFalse(scope) {
    const box = (scope || el).querySelector('#lab-false');
    if (!box) return;
    try {
      const page = await api.list(queryString({
        campaign_id: campaignId, status: 'succeeded',
        verdict: 'verified-failure', page_size: 10, sort: '-created_at',
      }));
      if (!page.rows.length) {
        box.innerHTML = `<p style="margin:0"><span class="pill ok">No false successes</span> `
          + `<span class="dim">— no trial reported success while failing verification.</span></p>`;
        return;
      }
      box.innerHTML = `<ul class="checks">` + page.rows.map((r) =>
        `<li><span><a href="#/run/${encodeURIComponent(r.id)}">${esc(r.project_name || r.id.slice(0, 8))}</a> `
        + `<span class="dim">${esc(driverLabel(r.driver))} · ${esc(scenarioLabel(r.scenario_id))}</span></span></li>`).join('')
        + `</ul><p class="caption">${fmtInt(page.total)} false successes in this campaign. `
        + `<a href="${historyHref({ campaign_id: campaignId, status: 'succeeded', verdict: 'verified-failure' })}">Open all in history</a> — `
        + `each links to its trace and independent evidence.</p>`;
    } catch {
      box.innerHTML = `<p class="dim">False-success list unavailable.</p>`;
    }
  }

  async function loadTrials() {
    const box = el.querySelector('#lab-trials');
    if (!box) return;
    try {
      const page = await api.list(queryString({
        campaign_id: campaignId, q: table.q, sort: table.sort,
        page: table.page, page_size: table.page_size,
      }));
      box.innerHTML = `<div class="field search" style="max-width:340px;padding:14px 24px 0"><label for="lab-q">Search trial name, error, or id</label>`
        + `<input type="search" id="lab-q" value="${esc(table.q)}" placeholder="e.g. locked, TimeoutError…"></div>`
        + `<div class="table-wrap"><table class="data"><thead><tr>`
        + `<th>Trial</th><th>Driver</th><th>Condition</th><th>Status</th><th>Verdict</th><th>Duration</th></tr></thead><tbody>`
        + (page.rows.map((r) => `<tr><td class="mono">${r.trial_seq === null || r.trial_seq === undefined ? '—' : esc(r.trial_seq)}</td>`
          + `<td><a href="#/run/${encodeURIComponent(r.id)}">${esc(r.project_name || r.id.slice(0, 8))}</a><br>`
          + `<span class="dim">${esc(driverLabel(r.driver))}</span></td>`
          + `<td>${esc(scenarioLabel(r.scenario_id))}</td>`
          + `<td>${statusPill(r.status)}</td><td>${verdictPill(r.verdict)}</td>`
          + `<td class="mono">${esc(fmtMs(r.duration_ms))}</td></tr>`).join('')
          || `<tr><td colspan="6"><span class="dim">No trials match.</span></td></tr>`)
        + `</tbody></table></div>`
        + `<div class="pager"><button class="btn" id="lab-prev"${page.page <= 1 ? ' disabled' : ''}>← Newer</button>`
        + `<button class="btn" id="lab-next"${page.page >= page.pages ? ' disabled' : ''}>Older →</button>`
        + `<span class="spacer"></span><span>${fmtInt(page.total)} total</span>`
        + `<span class="dim">sort:</span><select id="lab-sort" aria-label="Sort trials">`
        + [['trial_seq', 'Trial ↑'], ['-trial_seq', 'Trial ↓'], ['-duration_ms', 'Slowest'], ['-created_at', 'Newest']]
          .map(([v, l]) => `<option value="${v}"${table.sort === v ? ' selected' : ''}>${l}</option>`).join('')
        + `</select></div>`;
      const q = box.querySelector('#lab-q');
      q.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') { table.q = q.value; table.page = 1; loadTrials(); }
      });
      q.addEventListener('change', () => { table.q = q.value; table.page = 1; loadTrials(); });
      box.querySelector('#lab-prev').addEventListener('click', () => { table.page -= 1; loadTrials(); });
      box.querySelector('#lab-next').addEventListener('click', () => { table.page += 1; loadTrials(); });
      box.querySelector('#lab-sort').addEventListener('change', (e) => { table.sort = e.target.value; table.page = 1; loadTrials(); });
    } catch {
      box.innerHTML = `<div class="empty"><svg class="empty-mark" aria-hidden="true"><use href="#empty-server"/></svg><div><h2>Trials unavailable</h2><p>Could not reach the server.</p></div></div>`;
    }
  }

  el.innerHTML = `<div class="section-split" id="lab-detail"><h2>Campaign detail, drilled to evidence.</h2>`
    + `<p>Every figure carries its denominator; aggregates drill down into the underlying executions and evidence.</p></div>`
    + `<div id="lab-head"><p class="dim">Loading campaign…</p></div>`
    + `<div class="panel"><div class="filters">`
    + `<div class="field"><label for="lab-driver">Driver scope (all figures below)</label>`
    + `<select id="lab-driver"><option value="">Both drivers</option>`
    + `<option value="chimera">Chimera</option><option value="baseline-a">Baseline A</option></select></div>`
    + `</div></div>`
    + `<div id="lab-body"></div>`;
  el.querySelector('#lab-body').innerHTML = tabsHtml('lab', 'Campaign sections', [
    ['matrix', 'Matrix', `<div id="lab-p-matrix"><p class="dim">Computing figures…</p></div>`],
    ['drivers', 'Drivers', `<div id="lab-p-drivers"><p class="dim">Computing figures…</p></div>`],
    ['latency', 'Latency', `<div id="lab-p-latency"><p class="dim">Computing figures…</p></div>`],
    ['stages', 'Stages', `<div id="lab-p-stages"><p class="dim">Computing figures…</p></div>`],
    ['failures', 'Failures', `<div id="lab-p-failures"><p class="dim">Computing figures…</p></div>`],
    ['funnels', 'Funnels', `<div id="lab-p-funnels"><p class="dim">Computing figures…</p></div>`],
    ['quality', 'Quality', `<div id="lab-p-quality"><p class="dim">Computing figures…</p></div>`],
    ['trials', 'Trials', `<div id="lab-p-trials"><div class="panel flush"><div class="panel-head"><h2>10 · Trial records</h2></div><div id="lab-trials"></div></div></div>`],
  ]);
  tabsInit(el.querySelector('#lab-body'));
  el.querySelector('#lab-driver').addEventListener('change', (e) => {
    state.driver = e.target.value;
    loadAnalytics();
  });
  const status = await refreshHeader();
  if (status === null) {
    el.innerHTML = emptyState('Campaign unavailable', 'Could not load this campaign.', 'empty-server');
    return null;
  }
  timer = setInterval(async () => {
    if (!el.querySelector('#lab-head')) { clearInterval(timer); return; }
    const s = await refreshHeader();
    if (s === 'completed' || s === 'cancelled' || s === 'failed') {
      clearInterval(timer);
      timer = setInterval(async () => {
        if (!el.querySelector('#lab-head')) clearInterval(timer);
      }, 15000);
    }
  }, 2000);
  return () => { if (timer) clearInterval(timer); };
}
