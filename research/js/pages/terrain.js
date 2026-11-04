/* Outcome Terrain: condition landscape with trial-level markers.
 * Cells map to episodes by the audit's positional rule (stats.sliceCells);
 * any inconsistency fails closed with an error banner. Tiles are uniform —
 * only observed categories (color+shape), counts, and expected-match tags
 * are encoded. Nothing unsupported becomes height or intensity.
 */
import { getState, getRun, mVal, wilsonUpper, esc, fmtMs } from '../data.js';
import { sliceCells, matchCellKey } from '../viz/stats.js';
import { attachTip } from '../viz/tooltip.js';
import { link } from '../app.js';
import { pageHead, pill, emptyState, epLink, globes, secHead } from '../components.js';

const DOT = { succeeded: '#15803d', failed: '#b91c1c', cancelled: '#b45309', inconclusive: '#b45309' };

function dotShape(outcome) {
  if (outcome === 'succeeded') return { fill: DOT.succeeded, ring: false };
  if (outcome === 'failed') return { fill: DOT.failed, ring: false };
  return { fill: 'none', ring: true }; // cancelled / inconclusive / other: amber ring
}

function dotInner(e, i, dim) {
  const shape = dotShape(e.outcome);
  const unverified = !e.verification || e.verification.status !== 'verified';
  const harness = (e.error || '').startsWith('harness_error:');
  const cx = 14 + (i % 5) * 20, cy = 12;
  return `<g opacity="${dim ? 0.18 : 1}"><title>${esc(e.trial_id)} · ${esc(e.outcome)}${unverified ? ' · verification unavailable' : ''}</title>`
    + `<circle cx="${cx}" cy="${cy}" r="7" fill="${shape.fill}" stroke="${unverified ? '#b45309' : shape.fill === 'none' ? '#b45309' : shape.fill}" stroke-width="2"${unverified ? ' stroke-dasharray="3 2"' : ''}/>`
    + (harness ? `<circle cx="${cx}" cy="${cy}" r="2.4" fill="#ffffff"/>` : '')
    + `</g>`;
}

function expectedOf(manifest, scenarioId) {
  const sc = manifest && (manifest.scenarios || []).find((s) => s.id === scenarioId);
  return sc ? sc.expected_outcome : null;
}

function asExpected(expected, k, n) {
  if (n <= 0) return false;
  return (expected === 'succeeded' && k === n) || (expected === 'failed' && k === 0);
}

function cellLabel(cell) {
  const f = cell.fault_params || {};
  const slow = f.slow_ms == null ? null : Number(f.slow_ms);
  const dis = f.disabled === true;
  let fault = 'no fault';
  if (slow != null && slow > 0 && dis) fault = `slow=${slow} +disabled`;
  else if (slow != null && slow > 0) fault = `slow=${slow}`;
  else if (dis) fault = 'disabled';
  return `${cell.input_id} · ${fault}`;
}

export async function pageTerrain(el, { query }) {
  const s = getState();
  const split = query.split === 'development' ? 'development' : 'evaluation';
  const baseline = query.baseline === 'baseline-a' ? 'baseline-a' : 'chimera';
  const scenarioFilter = query.scenario || '';
  const highlight = query.outcome || '';
  const selected = query.cell || '';
  const runId = `${split === 'development' ? 'dev' : 'eval'}-20261028-${baseline}`;
  const run = getRun(runId);
  if (!run) {
    el.innerHTML = pageHead('Outcome Terrain', [['Outcome Terrain']]) + emptyState(
      'Run evidence missing', `Run file for <code>${esc(runId)}</code> did not load.`);
    return;
  }
  const manifest = s.manifests.get(run.manifestFile);
  let sliced;
  try {
    sliced = sliceCells(run.data.cells || [], run.data.episodes || []);
  } catch (err) {
    el.innerHTML = pageHead('Outcome Terrain', [['Outcome Terrain']])
      + `<div class="banner warn"><strong>Cannot map episodes to cells:</strong> ${esc(err.message)}. Refusing to render rather than misattributing trials.</div>`;
    return;
  }
  const scenarios = [...new Set(sliced.map((x) => x.cell.scenario_id))].sort();
  const shown = sliced.filter((x) => !scenarioFilter || x.cell.scenario_id === scenarioFilter);
  const totalTrials = shown.reduce((n, x) => n + x.episodes.length, 0);

  const tileHtml = ({ cell, episodes }, ti) => {
    const stagger = ` style="animation-delay:${(ti % 12) * 28}ms"`;
    const k = episodes.filter((e) => e.outcome === 'succeeded').length;
    const n = episodes.length;
    const expected = expectedOf(manifest, cell.scenario_id);
    const match = asExpected(expected, k, n);
    const key = `${cell.scenario_id}|${cell.input_id}|${JSON.stringify(cell.fault_params || {})}`;
    const selTile = selected && matchCellKey(cell, selected);
    const dots = episodes.map((e, i) => {
      const unverified = !e.verification || e.verification.status !== 'verified';
      const harness = (e.error || '').startsWith('harness_error:');
      const dim = highlight && ((highlight === 'unverified' && !unverified)
        || (highlight !== 'unverified' && e.outcome !== highlight));
      return `<a href="${link('evidence', [runId, e.trial_id])}" aria-label="${esc(e.trial_id)}: ${esc(e.outcome)}${unverified ? ', verification unavailable' : ''}${harness ? ', harness error' : ''}">`
        + dotInner(e, i, dim) + `</a>`;
    }).join('');
    return `<div class="terrain-cell anim-in${selTile ? ' sel' : ''}"${stagger} data-cell="${esc(key)}" tabindex="0" role="button"${selTile ? ' aria-current="true"' : ''} aria-label="Inspect cell ${esc(cell.scenario_id)} ${esc(cellLabel(cell))}, ${k} of ${n} succeeded">
      <svg viewBox="0 0 112 30" width="112" height="30" aria-hidden="true">${dots}</svg>
      <div class="terrain-meta"><span class="mono">${esc(cell.scenario_id)}</span><br><span>${esc(cellLabel(cell))}</span><br>
      <strong>${k}/${n}</strong> ${match ? pill('ok', 'as expected') : pill('dim', `expected ${esc(expected || '?')}`)}</div>
    </div>`;
  };
  // Scenario bands preserve run-file tile order; headers only label changes.
  const groups = [];
  for (const x of shown) {
    const last = groups[groups.length - 1];
    if (!last || last.scenario !== x.cell.scenario_id) groups.push({ scenario: x.cell.scenario_id, items: [x] });
    else last.items.push(x);
  }
  let ti = 0;
  const tiles = groups.map((g) => {
    const gk = g.items.reduce((a, x) => a + x.episodes.filter((e) => e.outcome === 'succeeded').length, 0);
    const gn = g.items.reduce((a, x) => a + x.episodes.length, 0);
    const gExpected = expectedOf(manifest, g.scenario);
    const head = `<div class="terrain-group-head"><span class="mono">${esc(g.scenario)}</span>`
      + `<span class="terrain-group-count">${g.items.length} cells · <strong>${gk}/${gn}</strong> succeeded</span>`
      + (gExpected ? pill('dim', `manifest expects ${esc(gExpected)}`) : '') + `</div>`;
    return `<section class="terrain-group" aria-label="Scenario ${esc(g.scenario)}">${head}`
      + `<div class="terrain-grid">${g.items.map((x) => tileHtml(x, ti++)).join('')}</div></section>`;
  }).join('');

  const sel = selected && shown.find(({ cell }) => matchCellKey(cell, selected));
  let detail = '';
  if (sel) {
    const { cell, episodes } = sel;
    const k = episodes.filter((e) => e.outcome === 'succeeded').length;
    const fs = cell.false_successes && cell.false_successes.value;
    const bound = cell.trials > 0 && fs === 0 ? wilsonUpper(0, cell.trials) : null;
    const otherBaseline = baseline === 'chimera' ? 'baseline-a' : 'chimera';
    const otherId = `${split === 'development' ? 'dev' : 'eval'}-20261028-${otherBaseline}`;
    const other = getRun(otherId);
    let mirror = 'other baseline not loaded';
    let mirrorDots = '';
    let mirrorLink = '';
    if (other) {
      try {
        const sib = sliceCells(other.data.cells || [], other.data.episodes || [])
          .find((x) => x.cell.scenario_id === cell.scenario_id && x.cell.input_id === cell.input_id
            && JSON.stringify(x.cell.fault_params || {}) === JSON.stringify(cell.fault_params || {}));
        if (sib) {
          const sk = sib.episodes.filter((e) => e.outcome === 'succeeded').length;
          mirror = `${sk}/${sib.episodes.length} succeeded`;
          const sameKey = `${cell.scenario_id}|${cell.input_id}|${JSON.stringify(cell.fault_params || {})}`;
          mirrorDots = `<svg class="mirror-strip" viewBox="0 0 ${(sib.episodes.length * 20 + 8).toFixed(0)} 30" width="${sib.episodes.length * 20 + 8}" height="30" role="img" aria-label="Mirror cell trials: ${sk} of ${sib.episodes.length} succeeded">${sib.episodes.map((e, i) => dotInner(e, i, false)).join('')}</svg>`;
          mirrorLink = `<a href="${link('terrain', [], { split, baseline: otherBaseline, scenario: scenarioFilter, cell: sameKey })}">Open mirror cell →</a>`;
        } else mirror = 'no matching cell in other baseline';
      } catch { mirror = 'cell mapping unverifiable'; }
    }
    const rows = episodes.map((e) => {
      const v = e.verification || {};
      return `<tr><td>${epLink(runId, e.trial_id)}</td><td><code>${esc(e.outcome)}</code></td>`
        + `<td class="num">${fmtMs(e.duration_ms)}</td>`
        + `<td>${v.status === 'verified' ? (v.all_satisfied ? pill('ok', 'P1–P3 ✓') : pill('bad', 'P1–P3 ✗')) : `<span class="pill dim" title="${esc(v.unavailable_reason || '')}">unavailable</span>`}</td>`
        + `<td class="mono" style="font-size:11.5px">${esc((e.error || '—').slice(0, 60))}</td></tr>`;
    }).join('');
    detail = `<div class="card" id="terrain-detail"><h2>Cell inspection — <code>${esc(cell.scenario_id)} / ${esc(cellLabel(cell))}</code></h2>
      <p><strong>${k}/${episodes.length}</strong> succeeded · false successes: <strong>${fs == null ? 'null' : fs}</strong>${bound == null ? '' : ` (95% Wilson ≤ ${(bound * 100).toFixed(1)}%)`}</p>
      <p class="mirror-line">mirror baseline (<code>${esc(otherId)}</code>): <strong>${esc(mirror)}</strong>${mirrorDots ? ` ${mirrorDots}` : ''}${mirrorLink ? ` ${mirrorLink}` : ''}</p>
      <div class="table-wrap"><table class="data"><thead><tr><th>Trial</th><th>Outcome</th><th class="num">Duration</th><th>Verification</th><th>Error</th></tr></thead><tbody>${rows}</tbody></table></div>
      <p><a href="${link('atlas', [], { run: runId, scenario: cell.scenario_id, search: cell.input_id })}">All cell episodes in the Atlas →</a></p></div>`;
  }

  const matchN = shown.filter((x) => {
    const kk = x.episodes.filter((e) => e.outcome === 'succeeded').length;
    return asExpected(expectedOf(manifest, x.cell.scenario_id), kk, x.episodes.length);
  }).length;
  const navy = `<div class="navy">${globes()}<h2>Outcome Terrain</h2>`
    + `<p class="sub">${shown.length} cells as a trial-dotted landscape — uniform tiles, expected-match tags. Selecting a cell opens its trials with verification states.</p>`
    + `<p><span class="glass"><span class="dot" style="background:#6ee7a0"></span>${matchN}/${shown.length} cells match expectation</span>`
    + (shown.length - matchN > 0 ? `<span class="glass"><span class="dot" style="background:#f87171"></span>${shown.length - matchN} diverge</span>` : '')
    + `<span class="glass"><span class="dot" style="background:#fbbf24"></span>unverified trials ringed amber</span></p></div>`;
  el.innerHTML = pageHead('Outcome Terrain', [['Outcome Terrain']], '', {
    kicker: `Routes #/failures · #/recovery · #/terrain · ${esc(runId)}`,
    lede: 'The condition landscape with trial-level markers — uniform tiles, observed categories only, nothing unsupported becoming height or intensity.',
    meta: `<span class="pill"><span class="dot"></span>${shown.length} cells · ${totalTrials} trials</span>${matchN === shown.length ? pill('ok', 'all as expected') : pill('warn', `${shown.length - matchN} diverge`)}`,
  })
    + (split === 'evaluation' ? `<div class="banner warn"><strong>Provisional.</strong> Held-out trials below are observed outcomes; no eval audit sample is adjudicated.</div>` : '')
    + navy
    + secHead('Trial landscape', `${esc(runId)} · uniform tiles · 5 trial dots each`)
    + `<div class="card"><div class="filters">
        <div class="field"><label for="t-split">Split</label><select id="t-split">
          <option value="evaluation"${split === 'evaluation' ? ' selected' : ''}>evaluation</option>
          <option value="development"${split === 'development' ? ' selected' : ''}>development</option></select></div>
        <div class="field"><label for="t-baseline">Baseline</label><select id="t-baseline">
          <option value="chimera"${baseline === 'chimera' ? ' selected' : ''}>Chimera</option>
          <option value="baseline-a"${baseline === 'baseline-a' ? ' selected' : ''}>A — replay</option></select></div>
        <div class="field"><label for="t-scenario">Scenario</label><select id="t-scenario">
          <option value="">All scenarios</option>${scenarios.map((x) => `<option${scenarioFilter === x ? ' selected' : ''}>${x}</option>`).join('')}</select></div>
        <div class="field"><label for="t-outcome">Highlight</label><select id="t-outcome">
          ${['', 'succeeded', 'failed', 'cancelled', 'inconclusive', 'unverified'].map((o) => `<option value="${o}"${highlight === o ? ' selected' : ''}>${o === '' ? 'None' : o}</option>`).join('')}</select></div>
      </div>
      <div class="viz-legend" aria-label="Dot legend">
        <span class="key"><span class="sw dot" style="background:#15803d"></span>succeeded</span>
        <span class="key"><span class="sw dot" style="background:#b91c1c"></span>failed</span>
        <span class="key"><span class="sw ring"></span>cancelled / inconclusive</span>
        <span class="key"><span class="sw hollow"></span>dashed edge = verification unavailable</span>
        <span class="key"><span class="sw dot" style="background:#ffffff;border:2px solid #b91c1c"></span>paper center = harness error</span>
      </div>
      <p style="color:var(--ink-2)"><strong>${shown.length}</strong> cells · <strong>${totalTrials}</strong> trials · ${esc(runId)}</p>
      <div class="terrain-groups">${tiles}</div>
    </div>${detail}`;

  const nav = () => {
    const q = { split: el.querySelector('#t-split').value, baseline: el.querySelector('#t-baseline').value,
      scenario: el.querySelector('#t-scenario').value, outcome: el.querySelector('#t-outcome').value };
    window.location.hash = link('terrain', [], q);
  };
  for (const id of ['#t-split', '#t-baseline', '#t-scenario', '#t-outcome']) {
    el.querySelector(id).addEventListener('change', nav);
  }
  el.querySelectorAll('.terrain-cell').forEach((tile) => {
    const go = () => {
      window.location.hash = link('terrain', [], { split, baseline, scenario: scenarioFilter, outcome: highlight, cell: tile.dataset.cell });
    };
    tile.addEventListener('click', (e) => { if (e.target.closest('a')) return; go(); });
    tile.addEventListener('keydown', (e) => { if (e.key === 'Enter') go(); });
    attachTip(tile, `Inspect cell: ${esc(tile.getAttribute('aria-label') || '')}`);
  });
  if (sel) {
    const d = el.querySelector('#terrain-detail');
    if (d) d.scrollIntoView({ block: 'nearest' });
  }
}
