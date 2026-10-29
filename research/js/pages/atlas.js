/* Experiment Atlas: run cards + searchable, filterable episode explorer. */
import { getState, getRun, filterEpisodes, isWarmup, isHarnessError, isFalseSuccess,
  esc, fmtInt, fmtMs, SCENARIOS, BASELINES, baselineLabel, shortHash } from '../data.js';
import { link } from '../app.js';
import { pageHead, dataTable, bindTable, outcomePill, baselineTag, emptyState, epLink, pill } from '../components.js';

const PER_PAGE = 20;

export async function pageAtlas(el, { query }) {
  const s = getState();
  const runs = [...s.runs.values()].filter((r) => r.data);
  if (!runs.length) {
    el.innerHTML = pageHead('Experiment Atlas', [['Experiment Atlas']]) + emptyState(
      'No run evidence loaded', 'Serve the repository root and reload.');
    return;
  }
  const f = {
    search: query.search || '', run: query.run || '', scenario: query.scenario || '',
    baseline: query.baseline || '', outcome: query.outcome || '',
    sort: query.sort || 'trial_id', dir: query.dir === '-1' ? -1 : 1,
    page: Math.max(1, parseInt(query.page || '1', 10) || 1),
  };
  const runCards = runs.map((r) => {
    const d = r.data;
    const measured = (d.episodes || []).filter((e) => !String(e.trial_id).startsWith('warmup:')).length;
    const sel = f.run === r.runId;
    return `<div class="card tight stat" style="${sel ? 'border-color:var(--cyan)' : ''}">
      <div class="stat-value" style="font-size:16px"><a class="mono" href="${link('atlas', [], { ...q(f), run: r.runId, page: 1 })}">${esc(r.runId)}</a></div>
      <div class="stat-label">${esc(r.split)} · ${baselineTag(r.baseline)}</div>
      <div class="stat-sub">${(d.cells || []).length} cells · ${measured} measured episodes<br>manifest <code>${esc(d.manifest_id)}</code> ${shortHash(d.manifest_sha256)}</div>
    </div>`;
  }).join('');

  el.innerHTML = pageHead('Experiment Atlas', [['Experiment Atlas']])
    + `<div class="grid two" style="grid-template-columns:repeat(auto-fit,minmax(260px,1fr))">${runCards}</div>`
    + `<div class="card"><h2>Episode explorer</h2>
      <div class="filters" role="search">
        <div class="field"><label for="f-search">Search</label><input type="search" id="f-search" value="${esc(f.search)}" placeholder="trial, scenario, input, error…"></div>
        <div class="field"><label for="f-run">Run</label><select id="f-run"><option value="">All runs</option>${runs.map((r) => `<option value="${esc(r.runId)}"${f.run === r.runId ? ' selected' : ''}>${esc(r.runId)}</option>`).join('')}</select></div>
        <div class="field"><label for="f-scenario">Scenario</label><select id="f-scenario"><option value="">All</option>${SCENARIOS.map((x) => `<option${f.scenario === x ? ' selected' : ''}>${x}</option>`).join('')}</select></div>
        <div class="field"><label for="f-baseline">Baseline</label><select id="f-baseline"><option value="">All</option>${BASELINES.map((x) => `<option value="${x}"${f.baseline === x ? ' selected' : ''}>${baselineLabel(x)}</option>`).join('')}</select></div>
        <div class="field"><label for="f-outcome">Outcome</label><select id="f-outcome">
          ${['', 'succeeded', 'failed', 'cancelled', 'inconclusive', 'false-success', 'harness-error'].map((o) => `<option value="${o}"${f.outcome === o ? ' selected' : ''}>${o === '' ? 'All' : o}</option>`).join('')}
        </select></div>
        <div class="field"><label>&nbsp;</label><button class="btn" id="f-clear">Clear</button></div>
      </div>
      <div id="atlas-table"></div></div>`;

  const renderTable = () => {
    const rows = filterEpisodes(f);
    const cols = [
      { key: 'trial_id', label: 'Trial', render: (e) => epLink(e.runId, e.trial_id) },
      { key: 'runId', label: 'Run', render: (e) => `<span class="mono" style="font-size:12px">${esc(e.runId.replace('20261028-', ''))}</span>` },
      { key: 'cell', label: 'Cell', value: (e) => `${e.scenario_id}/${e.input_id}`,
        render: (e) => `<span class="mono" style="font-size:12px">${esc(e.scenario_id)}/${esc(e.input_id)}</span>` },
      { key: 'baseline', label: 'Baseline', render: (e) => baselineTag(e.baseline) },
      { key: 'outcome', label: 'Outcome', render: (e) => outcomePill(e.outcome, isHarnessError(e)) },
      { key: 'fs', label: 'False succ.', value: (e) => (isFalseSuccess(e) ? 1 : 0),
        render: (e) => (isFalseSuccess(e) ? pill('bad', 'yes') : '<span style="color:var(--ink-3)">no</span>') },
      { key: 'duration_ms', label: 'Duration', num: true, render: (e) => `<span class="num">${fmtMs(e.duration_ms)}</span>` },
    ];
    const host = el.querySelector('#atlas-table');
    host.innerHTML = rows.length ? dataTable({
      id: 'episodes', columns: cols, rows, sortKey: f.sort, sortDir: f.dir, page: f.page, perPage: PER_PAGE,
      rowHref: (e) => link('evidence', [e.runId, e.trial_id]),
    }) : emptyState('No episodes match', 'Loosen the filters — every control above narrows this table.');
    bindTable(host, {
      onSort: (key) => {
        if (f.sort === key) f.dir = -f.dir; else { f.sort = key; f.dir = 1; }
        f.page = 1; sync(); renderTable();
      },
      onPage: (d) => { f.page += d; sync(); renderTable(); },
      onRow: (href) => { window.location.hash = href; },
    });
  };

  const sync = () => {
    const qs = q(f);
    window.history.replaceState(null, '', link('atlas', [], qs));
  };
  function q(ff) {
    return { search: ff.search, run: ff.run, scenario: ff.scenario, baseline: ff.baseline, outcome: ff.outcome, sort: ff.sort, dir: String(ff.dir), page: String(ff.page) };
  }

  let debounce = null;
  el.querySelector('#f-search').addEventListener('input', (e) => {
    clearTimeout(debounce);
    debounce = setTimeout(() => { f.search = e.target.value; f.page = 1; sync(); renderTable(); }, 220);
  });
  for (const [id, key] of [['#f-run', 'run'], ['#f-scenario', 'scenario'], ['#f-baseline', 'baseline'], ['#f-outcome', 'outcome']]) {
    el.querySelector(id).addEventListener('change', (e) => { f[key] = e.target.value; f.page = 1; sync(); renderTable(); });
  }
  el.querySelector('#f-clear').addEventListener('click', () => {
    window.location.hash = link('atlas');
  });
  renderTable();
}
