/* Failure Cartography: where the system fails, with honest boundaries. */
import { measuredEpisodes, getState, getRun, isHarnessError, isFalseSuccess, wilsonUpper,
  esc, fmtPct, fmtInt, SCENARIOS } from '../data.js';
import { link } from '../app.js';
import { pageHead, dataTable, bindTable, outcomePill, baselineTag, pill, epLink, art, secHead } from '../components.js';
import { heatmap, faultTransect } from '../charts.js';
import { groupSoundings } from '../viz/faultModel.js';
import { attachTip } from '../viz/tooltip.js';

export async function pageFailures(el, { query }) {
  const split = query.split === 'development' ? 'development' : 'evaluation';
  const eps = measuredEpisodes().filter((e) => e.split === split);
  if (!eps.length) {
    el.innerHTML = pageHead('Failure Cartography', [['Failure Cartography']])
      + `<div class="card"><p>No measured episodes for this split.</p></div>`;
    return;
  }
  const present = new Set(eps.map((e) => e.scenario_id));
  const scenarios = SCENARIOS.filter((s) => present.has(s));
  const inputs = [...new Set(eps.map((e) => e.input_id))].sort();
  const fails = eps.filter((e) => e.outcome !== 'succeeded');
  const fs = eps.filter(isFalseSuccess);
  const fsBound = wilsonUpper(fs.length, eps.length);

  const s = getState();
  const manRun = [...s.runs.values()].find((r) => r.split === split && r.data);
  const man = manRun ? s.manifests.get(manRun.manifestFile) : null;
  const expectedOf = (sc) => {
    const hit = man && (man.scenarios || []).find((x) => x.id === sc);
    return hit ? hit.expected_outcome : null;
  };
  const maps = ['chimera', 'baseline-a'].map((b, bi) => {
    const cells = [];
    for (const sc of scenarios) for (const inp of inputs) {
      const group = eps.filter((e) => e.scenario_id === sc && e.input_id === inp && e.baseline === b);
      cells.push({ row: sc, col: inp, k: group.filter((e) => e.outcome === 'succeeded').length, n: group.length,
        exp: expectedOf(sc), href: link('atlas', [], { scenario: sc, search: inp }) });
    }
    return `<div class="card">${art(bi)}<h2>${b === 'chimera' ? 'Chimera' : 'A — replay'} — success by scenario × input <span style="color:var(--ink-3);font-weight:400">(${esc(split)}, pooled over fault variants)</span></h2>`
      + heatmap({ rows: scenarios, cols: inputs, cells, id: `success map ${b} ${split}` }) + `</div>`;
  }).join('');

  let topo = '';
  {
    const tag = split === 'development' ? 'dev' : 'eval';
    const runs = [`${tag}-20261028-chimera`, `${tag}-20261028-baseline-a`].map(getRun).filter(Boolean);
    try {
      if (runs.length !== 2) throw new Error('both run files are required');
      const { soundings, levels } = groupSoundings(runs);
      const rows = [];
      for (const sc of scenarios) for (const b of ['chimera', 'baseline-a']) rows.push({ scenario: sc, baseline: b });
      const withLinks = soundings.map((s) => ({
        ...s,
        href: link('atlas', [], { scenario: s.scenario, baseline: s.baseline }),
        tip: `${s.scenario} · ${s.baseline} · slow=${s.slow}${s.disabled ? ' +disabled' : ''}: ${s.k}/${s.n} succeeded (inputs ${s.inputs.join(', ')})`,
      }));
      const tableRows = withLinks.map((s) => (
        `<tr><td class="mono">${esc(s.scenario)}</td><td>${esc(s.baseline)}</td><td class="num">${s.slow}</td>`
        + `<td>${s.disabled ? 'yes' : 'no'}</td><td class="num"><strong>${s.k}/${s.n}</strong></td>`
        + `<td class="mono" style="font-size:11.5px">${esc(s.inputs.join(', '))}</td>`
        + `<td>${s.unverified ? 'unverified present' : 'verified'}</td>`
        + `<td><a href="${s.href}">records →</a></td></tr>`)).join('');
      topo = `<div class="card"><h2>Failure topography — fault transect <span style="color:var(--ink-3);font-weight:400">(${fmtInt(soundings.length)} soundings)</span></h2>`
        + `<p style="color:var(--ink-2)">Discrete soundings at tested <code>slow_ms</code> levels, pooled over input variants. Soundings are not connected: nothing is implied about untested levels between the stakes. Marker links open the scenario × baseline pool in the Atlas, which cannot filter by fault level.</p>`
        + faultTransect({ rows, levels, soundings: withLinks, id: `fault transect ${split}` }) + `</div>`
        + `<div class="card"><h2>Soundings (list alternative)</h2><div class="table-wrap"><table class="data">`
        + `<thead><tr><th>Scenario</th><th>Baseline</th><th class="num">slow_ms</th><th>Disabled</th><th class="num">Succeeded</th><th>Inputs pooled</th><th>Verification</th><th></th></tr></thead>`
        + `<tbody>${tableRows}</tbody></table></div></div>`;
    } catch (err) {
      topo = `<div class="banner warn"><strong>Topography unavailable:</strong> ${esc(err.message)}. Refusing to render rather than misattributing trials.</div>`;
    }
  }

  const errGroups = new Map();
  for (const e of fails) {
    const key = e.error || '(no error text)';
    if (!errGroups.has(key)) errGroups.set(key, []);
    errGroups.get(key).push(e);
  }
  const errRows = [...errGroups.entries()].sort((a, b) => b[1].length - a[1].length).map(([err, list]) => (
    `<tr><td class="mono" style="font-size:12px;max-width:420px;overflow-wrap:anywhere">${esc(err)}</td>`
    + `<td class="num">${list.length}</td>`
    + `<td>${epLink(list[0].runId, list[0].trial_id, 'example →')}</td></tr>`)).join('');

  el.innerHTML = pageHead('Failure Cartography', [['Failure Cartography']], '', {
    kicker: `Routes #/failures · #/recovery · #/terrain · split = ${split}`,
    lede: 'Heat matrices become pastel tiles, the fault transect becomes a sounding stream, and every failure keeps its error text one click away.',
    meta: `${fails.length ? pill('bad', `${fails.length}/${eps.length} non-success (${split})`) : pill('ok', 'no failures')} ${(() => { const he = eps.filter(isHarnessError).length; return he === 0 ? pill('ok', '0 harness errors') : pill('bad', `${he} harness errors`); })()}`,
  })
    + `<div class="banner info"><strong>Reading guide.</strong> Green cells are unanimous success, red are unanimous failure — both are <em>observed</em> boundaries. Grey “—” cells are untested regions, not safe ones. The runner never sets <code>failure_category</code> (always null), so grouping below uses recorded outcomes and error text instead.</div>`
    + `<div class="card"><div class="filters fail-head"><div class="field"><label for="f-split">Split</label><select id="f-split">
        <option value="evaluation"${split === 'evaluation' ? ' selected' : ''}>evaluation (held out)</option>
        <option value="development"${split === 'development' ? ' selected' : ''}>development</option>
      </select></div>
      <div class="field"><label>Non-success episodes</label><div class="fail-stat"><strong>${fails.length}</strong> of ${eps.length} measured (${fmtPct(fails.length, eps.length)})</div></div>
      <div class="field"><label>False successes</label><div class="fail-stat"><strong>${fs.length}</strong> of ${eps.length}${fsBound == null ? '' : ` (95% Wilson ≤ ${(fsBound * 100).toFixed(1)}%)`} ${fs.length ? `<a href="${link('atlas', [], { outcome: 'false-success' })}">inspect →</a>` : ''}</div></div>
    </div></div>`
    + secHead('Sounding stream — fault transect', 'Soft-graph pattern soundings — discrete levels, no implied boundary between them.')
    + topo
    + secHead('Success tiles by scenario × input', 'Soft-graph pattern tilefield — rounded, luminous, k/n in every tile.')
    + maps
    + `<div class="card"><h2>Error text groups (${errGroups.size})</h2>
      <div class="table-wrap"><table class="data"><thead><tr><th>Error text</th><th class="num">Episodes</th><th></th></tr></thead><tbody>${errRows || '<tr><td colspan="3">No failures recorded.</td></tr>'}</tbody></table></div></div>`
    + `<div class="card"><h2>Non-success episodes</h2><div id="fail-table"></div></div>`;

  el.querySelector('#f-split').addEventListener('change', (e) => {
    window.location.hash = link('failures', [], { split: e.target.value });
  });
  el.querySelectorAll('.sounding[data-tip]').forEach((a) => attachTip(a, a.dataset.tip));
  const host = el.querySelector('#fail-table');
  const state = { sort: 'trial_id', dir: 1, page: 1 };
  const cols = [
    { key: 'trial_id', label: 'Trial', render: (e) => epLink(e.runId, e.trial_id) },
    { key: 'cell', label: 'Cell', value: (e) => `${e.scenario_id}/${e.input_id}`, render: (e) => `<span class="mono" style="font-size:12px">${esc(e.scenario_id)}/${esc(e.input_id)}</span>` },
    { key: 'baseline', label: 'Baseline', render: (e) => baselineTag(e.baseline) },
    { key: 'outcome', label: 'Outcome', render: (e) => outcomePill(e.outcome, isHarnessError(e)) },
    { key: 'reported', label: 'Agent said', value: (e) => e.agent_terminal_status, render: (e) => `<code>${esc(e.agent_terminal_status)}</code>` },
    { key: 'error', label: 'Error', value: (e) => e.error || '', render: (e) => `<span class="mono" style="font-size:11.5px">${esc((e.error || '—').slice(0, 90))}</span>` },
  ];
  const draw = () => {
    host.innerHTML = dataTable({ id: 'failures', columns: cols, rows: fails, sortKey: state.sort, sortDir: state.dir, page: state.page, perPage: 15,
      rowHref: (e) => link('evidence', [e.runId, e.trial_id]) });
    bindTable(host, {
      onSort: (k) => { if (state.sort === k) state.dir = -state.dir; else { state.sort = k; state.dir = 1; } state.page = 1; draw(); },
      onPage: (d) => { state.page += d; draw(); },
      onRow: (href) => { window.location.hash = href; },
    });
  };
  draw();
}
