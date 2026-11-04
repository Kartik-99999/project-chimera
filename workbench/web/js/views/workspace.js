/* Workspace: pick a supported workflow, fill its parameters, run it
 * for real, and watch it execute. */
import { api, queryString } from '../api.js';
import { esc, fmtMs, fmtWhen, verdictPill, statusPill, statusGlass, verdictGlass, driverLabel, scenarioLabel, sourcePill, banner, hero, heroField, bannerArt, navySection } from '../format.js';

const ACTIVE_KEY = 'chimera-workbench:active';

function fieldHtml(p) {
  const help = p.help ? `<div class="help">${esc(p.help)}</div>` : '';
  const dis = p.disabled ? ' disabled' : '';
  if (p.kind === 'select') {
    const opts = p.options.map((o) =>
      `<option value="${esc(o.value)}"${o.value === p.default ? ' selected' : ''}>${esc(o.label)}</option>`).join('');
    return `<div class="field"><label for="wf-${p.name}">${esc(p.label)}</label>`
      + `<select id="wf-${p.name}" name="${p.name}"${dis}>${opts}</select>${help}</div>`;
  }
  if (p.kind === 'number') {
    return `<div class="field"><label for="wf-${p.name}">${esc(p.label)}</label>`
      + `<input type="number" id="wf-${p.name}" name="${p.name}" value="${esc(p.default ?? '')}"`
      + `${p.min_value !== null && p.min_value !== undefined ? ` min="${p.min_value}"` : ''}`
      + `${p.max_value !== null && p.max_value !== undefined ? ` max="${p.max_value}"` : ''}${dis}>${help}</div>`;
  }
  if (p.kind === 'checkbox') {
    return `<div class="field"><label for="wf-${p.name}">`
      + `<input type="checkbox" id="wf-${p.name}" name="${p.name}"${p.default ? ' checked' : ''}${dis}> ${esc(p.label)}</label>${help}</div>`;
  }
  return `<div class="field"><label for="wf-${p.name}">${esc(p.label)}</label>`
    + `<input type="text" id="wf-${p.name}" name="${p.name}" value="${esc(p.default ?? '')}"`
    + `${p.max_length ? ` maxlength="${p.max_length}"` : ''}${p.required ? ' required' : ''}${dis}>${help}</div>`;
}

function readForm(form, workflow) {
  const params = {};
  for (const p of workflow.parameters) {
    const el = form.elements[p.name];
    if (!el) continue;
    if (p.kind === 'number') params[p.name] = el.value === '' ? 0 : Number(el.value);
    else if (p.kind === 'checkbox') params[p.name] = el.checked;
    else params[p.name] = el.value;
  }
  return params;
}

export async function viewWorkspace(el, badges) {
  const { workflows } = await api.workflows();
  const runnable = workflows.filter((w) => !w.future);
  const future = workflows.filter((w) => w.future);
  let selected = runnable[0] || null;
  let driver = 'chimera';
  let activeId = null;
  try { activeId = sessionStorage.getItem(ACTIVE_KEY); } catch { /* private mode */ }
  let timer = null;

  function workflowTile(w, i) {
    const open = selected && selected.workflow_id === w.workflow_id;
    const num = String(i + 1).padStart(2, '0');
    return `<div class="wf tile${open ? ' selected' : ''}">`
      + `<button class="wf-head" data-wf="${esc(w.workflow_id)}" aria-expanded="${open}" aria-label="${esc(w.title)}">`
      + `<svg class="wf-emblem" aria-hidden="true"><use href="#wfart-${esc(w.workflow_id)}"/></svg>`
      + `<span class="wf-index">${num}</span><span class="wf-title">${esc(w.title)}</span>`
      + `<span class="wf-env">${esc(w.environment)}</span></button></div>`;
  }

  function futureCard(w) {
    return `<div class="wf future"><div class="wf-head"><span class="wf-index">${esc(w.workflow_id)}</span>`
      + `<span class="wf-title">${esc(w.title)}</span>`
      + `<span class="wf-env">${esc(w.environment)}</span></div>`
      + `<div class="wf-body"><p>${esc(w.description)}</p><span class="pill warn">Not supported — roadmap only</span></div></div>`;
  }

  function render() {
    const wf = selected;
    el.innerHTML = hero({
      kicker: 'Run &amp; inspect',
      head: '<h1 id="page-h1">Workspace</h1>',
      lede: `Run a <strong>supported browser workflow</strong> against a real browser and get a `
        + `verified result with evidence. Chimera's drivers are <strong>fixed scripts, not a general AI</strong> — `
        + `only the workflows below can run. Anything else is listed as roadmap so the boundary stays visible.`,
      ctas: '<a class="btn primary" href="#ws-form">Run in a real browser</a><a class="btn" href="#/history">Open full history</a>',
      field: heroField('ws', ['#c7d2fe', '.55', '.26'], ['#fed7aa', '.5', '.2'], [880, 300, 150, 162]),
    })
      + `<div id="ws-msg"></div>`
      + `<div class="panel float art-top float-lift">`
      + bannerArt({ id: 'ws-b1', stops: ['#dbe7ff', '#eef2ff', '#ffe7d1'], globe: 'right', deco: 'weave', label: 'Supported workflows' })
      + `<h2>1 · Select a workflow</h2>`
      + `<div class="wf-grid4" role="group" aria-label="Runnable workflows">`
      + runnable.map(workflowTile).join('') + `</div>`
      + (wf ? `<div class="wf-detail"><p>${esc(wf.description)}</p></div>` : '')
      + future.map(futureCard).join('') + `</div>`
      + (wf ? `<div class="panel"><h2>2 · Provide the inputs — ${esc(wf.title)}</h2><form id="ws-form">`
        + wf.parameters.map(fieldHtml).join('')
        + ((wf.sessions || []).includes('user')
          ? `<div class="field"><label for="ws-profile">Browser profile (optional)</label>`
          + `<input type="text" id="ws-profile" name="profile" value="" placeholder="clean session">`
          + `<div class="help">Leave blank for a clean session. Name a logged-in profile (created with `
          + `<span class="mono">python -m workbench.sessions login &lt;name&gt;</span>) when the site gates automation. `
          + `The run is labeled with its session.</div></div>` : '')
        + `<div class="field"><label for="ws-driver">Driver</label><select id="ws-driver">`
        + wf.drivers.map((d) => `<option value="${esc(d)}"${d === driver ? ' selected' : ''}>${esc(driverLabel(d))}</option>`).join('')
        + `</select><div class="help">Chimera attempts each step once, with one guarded second try on the submit click only — and only if the first try fails fast. Steps that time out are not retried. Baseline A attempts each step exactly once, with no retries at all. The timeout override applies to Baseline A only.</div></div>`
        + `<div class="btn-row"><button class="btn primary" type="submit" id="ws-run">Run in a real browser</button></div>`
        + `</form></div>` : '')
      + (wf ? `<div class="panel flush"><div class="panel-head"><h2>Last ${esc(wf.title)} runs</h2>`
        + `<span class="meta"><a href="#/history">All history →</a></span></div><div id="ws-wf-recent"></div></div>` : '')
      + navySection('Live execution', `<h2>3 · Live execution</h2><div id="ws-active"></div>`, 'id="ws-active-wrap"')
      + `<div class="panel flush"><div class="panel-head"><h2>Recent executions</h2>`
      + `<span class="meta"><a href="#/history">Open full history →</a></span></div><div id="ws-recent"></div></div>`;
    wire();
    pollActive();
    loadRecent();
    if (wf) loadWorkflowRecent(wf.workflow_id);
  }

  async function loadWorkflowRecent(workflowId) {
    const box = el.querySelector('#ws-wf-recent');
    if (!box) return;
    try {
      const page = await api.list(queryString({
        workflow_id: workflowId, page_size: 3, sort: '-created_at',
      }));
      if (!page.rows.length) {
        box.innerHTML = `<div class="empty"><svg class="empty-mark" aria-hidden="true"><use href="#empty-runs"/></svg><div><h2>No runs yet</h2><p>Fill the inputs above and run this workflow for the first time.</p></div></div>`;
        return;
      }
      box.innerHTML = `<div class="table-wrap"><table class="data"><thead><tr>`
        + `<th>Started</th><th>Run</th><th>Driver</th><th>Status</th><th>Verdict</th></tr></thead><tbody>`
        + page.rows.map((r) => `<tr><td class="mono">${esc(fmtWhen(r.created_at))}</td>`
          + `<td><a href="#/run/${encodeURIComponent(r.id)}">${esc(r.project_name || r.id.slice(0, 8))}</a> ${sourcePill(r.source)}</td>`
          + `<td>${esc(driverLabel(r.driver))}</td><td>${statusPill(r.status)}</td><td>${verdictPill(r.verdict)}</td></tr>`).join('')
        + `</tbody></table></div>`;
    } catch {
      box.innerHTML = `<div class="empty"><svg class="empty-mark" aria-hidden="true"><use href="#empty-server"/></svg><div><h2>Runs unavailable</h2><p>Could not reach the server.</p></div></div>`;
    }
  }

  function wire() {
    el.querySelectorAll('[data-wf]').forEach((btn) => {
      btn.addEventListener('click', () => {
        selected = runnable.find((w) => w.workflow_id === btn.dataset.wf) || selected;
        render();
      });
    });
    const form = el.querySelector('#ws-form');
    if (form) {
      const driverSel = form.querySelector('#ws-driver');
      const timeoutEl = form.elements['action_timeout_ms'];
      const syncTimeout = () => {
        if (timeoutEl) {
          timeoutEl.disabled = driverSel.value !== 'baseline-a';
          if (timeoutEl.disabled) timeoutEl.value = '0';
        }
      };
      driverSel.addEventListener('change', () => { driver = driverSel.value; syncTimeout(); });
      syncTimeout();
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const msg = el.querySelector('#ws-msg');
        const btn = el.querySelector('#ws-run');
        btn.disabled = true;
        try {
          const profileEl = form.elements['profile'];
          const profile = profileEl ? profileEl.value.trim() : '';
          const { id } = await api.start({
            workflow_id: selected.workflow_id, driver: driverSel.value,
            params: readForm(form, selected),
            ...(profile ? { profile } : {}),
          });
          activeId = id;
          try { sessionStorage.setItem(ACTIVE_KEY, id); } catch { /* ignore */ }
          window.location.hash = `#/run/${encodeURIComponent(id)}`;
        } catch (err) {
          msg.innerHTML = banner('bad', `<strong>Could not start:</strong> ${esc(err.message)}`);
          btn.disabled = false;
        }
      });
    }
  }

  async function pollActive() {
    const box = el.querySelector('#ws-active');
    if (!box) return;
    if (!activeId) {
      box.innerHTML = `<p class="dim" style="margin:0">No run in progress. Start one above, or open any execution from history.</p>`;
      return;
    }
    try {
      const { execution: r } = await api.get(activeId);
      const live = r.status === 'queued' || r.status === 'running';
      const prog = r.progress || {};
      box.innerHTML = `<div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">`
        + `<span class="pulse${live ? ' live' : ''}" aria-hidden="true"></span>`
        + `<strong><a href="#/run/${encodeURIComponent(r.id)}">${esc(r.project_name || r.id.slice(0, 8))}</a></strong>`
        + statusGlass(r.status) + verdictGlass(r.verdict)
        + `<span class="dim">${esc(driverLabel(r.driver))} · ${esc(scenarioLabel(r.scenario_id))}</span></div>`
        + `<div class="progress" role="status" aria-label="Execution progress"><div class="bar"><div class="fill" style="--fill:${live ? 0.45 : 1}"></div></div></div>`
        + `<p class="dim" style="margin:0">Phase: <strong>${esc(prog.phase || r.status)}</strong> · `
        + `actions observed: <strong>${prog.actions_seen ?? (r.actions ? r.actions.length : 0)}</strong> · `
        + `elapsed: <strong>${esc(fmtMs(r.duration_ms))}</strong>${live ? ` · <button class="linklike" id="ws-cancel">Cancel</button>` : ''}</p>`;
      const cancel = box.querySelector('#ws-cancel');
      if (cancel) cancel.addEventListener('click', async () => {
        await api.cancel(r.id);
        pollActive();
      });
    } catch {
      box.innerHTML = `<p class="dim" style="margin:0">The tracked run is no longer available.</p>`;
    }
  }

  async function loadRecent() {
    const box = el.querySelector('#ws-recent');
    try {
      const page = await api.list(queryString({ page_size: 8, sort: '-created_at' }));
      if (!page.rows.length) {
        box.innerHTML = `<div class="empty"><svg class="empty-mark" aria-hidden="true"><use href="#empty-runs"/></svg><div><h2>No executions yet</h2><p>Run your first workflow above — it will appear here with its verdict and evidence.</p></div></div>`;
        return;
      }
      box.innerHTML = `<div class="table-wrap"><table class="data"><thead><tr>`
        + `<th>Started</th><th>Run</th><th>Driver</th><th>Condition</th><th>Status</th><th>Verdict</th><th>Duration</th></tr></thead><tbody>`
        + page.rows.map((r) => `<tr><td>${esc(fmtWhen(r.created_at))}</td>`
          + `<td><a href="#/run/${encodeURIComponent(r.id)}">${esc(r.project_name || r.id.slice(0, 8))}</a> ${sourcePill(r.source)}</td>`
          + `<td>${esc(driverLabel(r.driver))}</td><td>${esc(scenarioLabel(r.scenario_id))}</td>`
          + `<td>${statusPill(r.status)}</td><td>${verdictPill(r.verdict)}</td>`
          + `<td class="mono">${esc(fmtMs(r.duration_ms))}</td></tr>`).join('')
        + `</tbody></table></div>`;
    } catch {
      box.innerHTML = `<div class="empty"><svg class="empty-mark" aria-hidden="true"><use href="#empty-server"/></svg><div><h2>History unavailable</h2><p>Could not reach the server.</p></div></div>`;
    }
  }

  render();
  timer = setInterval(() => { if (el.querySelector('#ws-active')) pollActive(); }, 1200);
  return () => clearInterval(timer);
}
