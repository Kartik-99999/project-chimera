/* History: searchable, filterable, paginated execution index. */
import { api, queryString } from '../api.js';
import { esc, fmtMs, fmtWhen, fmtInt, verdictPill, statusPill, driverLabel, scenarioLabel, sourcePill, originPill, workflowLabel, sessionLabel, hero, heroField, bannerArt, navySection } from '../format.js';

const COLUMNS = [
  ['created_at', 'Started'],
  ['project_name', 'Run'],
  ['driver', 'Driver'],
  ['session', 'Session'],
  ['scenario_id', 'Condition'],
  ['status', 'Status'],
  ['verdict', 'Verdict'],
  ['duration_ms', 'Duration'],
];

export async function viewHistory(el, _badges, extra) {
  const facets = await api.facets().catch(() => ({ facets: {} }));
  const seed = (extra && extra.query) || {};
  const seeded = (name, fallback) =>
    (typeof seed[name] === 'string' && seed[name] ? seed[name] : fallback);
  const state = {
    source: seeded('source', ''), origin: seeded('origin', ''),
    workflow_id: seeded('workflow_id', ''),
    driver: seeded('driver', ''),
    scenario_id: seeded('scenario_id', ''),
    verdict: seeded('verdict', ''), status: seeded('status', ''),
    trial_kind: seeded('trial_kind', ''),
    campaign_id: seeded('campaign_id', ''),
    q: seeded('q', ''), sort: seeded('sort', '-created_at'),
    page: 1, page_size: 50,
  };

  function select(name, label, options) {
    const opts = [`<option value="">All</option>`].concat(options.map((o) =>
      `<option value="${esc(o)}"${state[name] === o ? ' selected' : ''}>${esc(o)}</option>`)).join('');
    return `<div class="field"><label for="h-${name}">${label}</label>`
      + `<select id="h-${name}" data-f="${name}">${opts}</select></div>`;
  }

  let scopeSeq = 0;

  function render() {
    const f = facets.facets || {};
    el.innerHTML = hero({
      kicker: 'Run &amp; inspect',
      head: '<h1 id="page-h1">History</h1>',
      lede: `Every execution, newest first — <strong>workbench runs and benchmark history side by side</strong>, `
        + `always labelled so you know which is which. Filter, sort, page through thousands of rows, export, or open any row for its evidence.`,
      ctas: '<a class="btn primary" href="#h-q">Search executions</a><a class="btn" href="#h-csv">Export CSV</a>',
      field: heroField('hi', ['#fde68a', '.48', '.24'], ['#bbf7d0', '.5', '.2'], [320, 300, 150, 162]),
    })
      + (state.campaign_id ? `<div class="banner info" role="status">Scoped to campaign <code>${esc(state.campaign_id.slice(0, 8))}</code> `
        + `— <a href="#/lab/${encodeURIComponent(state.campaign_id)}">open in Campaign Lab</a>. Reset clears the scope.</div>` : '')
      + `<div class="panel float art-top float-lift">`
      + bannerArt({ id: 'hi-b1', stops: ['#fef3c7', '#fffbeb', '#d3f8d3'], globe: 'left', deco: 'weave', label: 'Filter the index' })
      + `<div class="filters">`
      + select('source', 'Origin', f.source || [])
      + select('origin', 'Application', f.origin || [])
      + select('workflow_id', 'Workflow', f.workflow_id || [])
      + select('driver', 'Driver', f.driver || [])
      + select('scenario_id', 'Condition', f.scenario_id || [])
      + select('verdict', 'Verdict', f.verdict || [])
      + select('status', 'Status', f.status || [])
      + select('trial_kind', 'Trial kind', f.trial_kind || [])
      + `<div class="field search"><label for="h-q">Search name, error, or id</label>`
      + `<input type="search" id="h-q" data-f="q" value="${esc(state.q)}" placeholder="e.g. TimeoutError, Acme…"></div>`
      + `</div>`
      + `<div class="btn-row" style="margin-top:12px"><button class="btn primary" id="h-apply">Apply</button>`
      + `<button class="btn" id="h-reset">Reset</button>`
      + `<a class="btn" id="h-csv" href="#"><svg aria-hidden="true"><use href="#act-download"/></svg>Export CSV</a>`
      + `<span class="dim" id="h-count"></span></div></div>`
      + navySection('Scope summary', `<h2>In scope</h2>`
        + `<div style="display:flex;gap:10px;flex-wrap:wrap">`
        + `<span class="glass info" id="h-scope-total">… executions</span>`
        + `<span class="glass ok" id="h-scope-ok">… verified successes</span>`
        + `<span class="glass bad" id="h-scope-bad">… verified failures</span>`
        + `<span class="glass" id="h-scope-unknown">… insufficient evidence</span></div>`
        + `<p class="caption">Figures mirror the active filters — Apply recomputes them. Unverified rows never count as successes.</p>`)
      + `<div class="panel flush"><div id="h-rows"></div><div class="pager" id="h-pager"></div></div>`;
    el.querySelector('#h-apply').addEventListener('click', () => {
      el.querySelectorAll('[data-f]').forEach((input) => {
        state[input.dataset.f] = input.value;
      });
      state.page = 1;
      load();
    });
    el.querySelector('#h-q').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') el.querySelector('#h-apply').click();
    });
    el.querySelector('#h-reset').addEventListener('click', () => {
      Object.assign(state, {
        source: '', origin: '', workflow_id: '', driver: '',
        scenario_id: '', verdict: '', status: '', trial_kind: '',
        campaign_id: '', q: '',
        sort: '-created_at', page: 1,
      });
      render();
      load();
    });
    load();
  }

  function params() {
    return queryString({
      source: state.source, origin: state.origin,
      workflow_id: state.workflow_id,
      driver: state.driver, scenario_id: state.scenario_id,
      verdict: state.verdict, status: state.status,
      trial_kind: state.trial_kind, campaign_id: state.campaign_id,
      q: state.q, sort: state.sort,
      page: state.page, page_size: state.page_size,
    });
  }

  async function updateScope(total) {
    const my = ++scopeSeq;
    const set = (id, html) => {
      const node = el.querySelector(id);
      if (node) node.innerHTML = html;
    };
    set('#h-scope-total', `${esc(fmtInt(total))} executions`);
    const scopeParams = (verdict) => queryString({
      source: state.source, origin: state.origin,
      workflow_id: state.workflow_id,
      driver: state.driver, scenario_id: state.scenario_id,
      verdict, status: state.status,
      trial_kind: state.trial_kind, campaign_id: state.campaign_id,
      q: state.q, page_size: 1,
    });
    try {
      const [ok, bad, unk] = await Promise.all([
        api.list(scopeParams('verified-success')),
        api.list(scopeParams('verified-failure')),
        api.list(scopeParams('insufficient-evidence')),
      ]);
      if (my !== scopeSeq) return;
      set('#h-scope-ok', `<svg aria-hidden="true"><use href="#st-pass"/></svg>${esc(fmtInt(ok.total))} verified successes`);
      set('#h-scope-bad', `<svg aria-hidden="true"><use href="#st-fail"/></svg>${esc(fmtInt(bad.total))} verified failures`);
      set('#h-scope-unknown', `${esc(fmtInt(unk.total))} insufficient evidence`);
    } catch {
      if (my !== scopeSeq) return;
      set('#h-scope-ok', '— verified successes');
      set('#h-scope-bad', '— verified failures');
      set('#h-scope-unknown', '— insufficient evidence');
    }
  }

  async function load() {
    const box = el.querySelector('#h-rows');
    const pager = el.querySelector('#h-pager');
    try {
      const page = await api.list(params());
      el.querySelector('#h-count').textContent =
        `${fmtInt(page.total)} executions · page ${page.page} of ${Math.max(1, page.pages)}`;
      el.querySelector('#h-csv').href = api.exportCsv(params());
      updateScope(page.total);
      if (!page.rows.length) {
        box.innerHTML = `<div class="empty"><svg class="empty-mark" aria-hidden="true"><use href="#empty-filter"/></svg><div><h2>No executions match</h2><p>Loosen the filters, or run a workflow from the workspace.</p></div></div>`;
        pager.innerHTML = '';
        return;
      }
      const arrow = (col) => (state.sort === col ? ' ▲' : state.sort === `-${col}` ? ' ▼' : '');
      box.innerHTML = `<div class="table-wrap"><table class="data"><thead><tr>`
        + COLUMNS.map(([col, label]) => {
          const sortable = ['created_at', 'driver', 'scenario_id', 'status', 'verdict', 'duration_ms'].includes(col);
          const next = state.sort === col ? `-${col}` : col;
          return `<th>${sortable ? `<a href="#" data-sort="${next}">${esc(label)}${esc(arrow(col))}</a>` : esc(label)}</th>`;
        }).join('') + `<th></th></tr></thead><tbody>`
        + page.rows.map((r) => `<tr><td class="mono">${esc(fmtWhen(r.created_at))}</td>`
          + `<td><a href="#/run/${encodeURIComponent(r.id)}">${esc(r.project_name || r.id.slice(0, 8))}</a><br>${sourcePill(r.source)}${originPill(r.origin)} <span class="dim">${esc(workflowLabel(r.workflow_id))}</span></td>`
          + `<td>${esc(driverLabel(r.driver))}</td><td>${esc(sessionLabel(r.session))}</td><td>${esc(scenarioLabel(r.scenario_id))}</td>`
          + `<td>${statusPill(r.status)}</td><td>${verdictPill(r.verdict)}</td>`
          + `<td class="mono">${esc(fmtMs(r.duration_ms))}</td>`
          + `<td>${r.source === 'workbench' ? `<button class="linklike" data-del="${encodeURIComponent(r.id)}" aria-label="Delete execution">Delete</button>` : ''}</td></tr>`).join('')
        + `</tbody></table></div>`;
      pager.innerHTML = `<button class="btn" id="pg-prev"${page.page <= 1 ? ' disabled' : ''}>← Newer</button>`
        + `<button class="btn" id="pg-next"${page.page >= page.pages ? ' disabled' : ''}>Older →</button>`
        + `<span class="spacer"></span><span>${fmtInt(page.total)} total</span>`
        + `<label class="dim" for="h-pagesize">per page</label>`
        + `<select id="h-pagesize" aria-label="Rows per page">`
        + [25, 50, 100].map((n) => `<option value="${n}"${state.page_size === n ? ' selected' : ''}>${n}</option>`).join('')
        + `</select>`;
      box.querySelectorAll('[data-sort]').forEach((a) => {
        a.addEventListener('click', (e) => {
          e.preventDefault();
          state.sort = a.dataset.sort;
          state.page = 1;
          load();
        });
      });
      const prev = pager.querySelector('#pg-prev');
      const next = pager.querySelector('#pg-next');
      if (prev) prev.addEventListener('click', () => { state.page -= 1; load(); });
      if (next) next.addEventListener('click', () => { state.page += 1; load(); });
      const size = pager.querySelector('#h-pagesize');
      if (size) size.addEventListener('change', () => {
        state.page_size = Number(size.value) || 50;
        state.page = 1;
        load();
      });
      box.querySelectorAll('[data-del]').forEach((btn) => {
        btn.addEventListener('click', async () => {
          if (!window.confirm('Delete this workbench execution and its index rows? Evidence files stay on disk.')) return;
          await api.remove(decodeURIComponent(btn.dataset.del));
          load();
        });
      });
    } catch {
      box.innerHTML = `<div class="empty"><svg class="empty-mark" aria-hidden="true"><use href="#empty-server"/></svg><div><h2>History unavailable</h2><p>Could not reach the server.</p></div></div>`;
    }
  }

  render();
  return null;
}
