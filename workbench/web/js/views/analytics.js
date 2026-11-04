/* Analytics: distinctive, honest figures over executions. Every
 * number carries its denominator; unverified rows never count as
 * successes; missing data is labelled, never zeroed. */
import { api, queryString } from '../api.js';
import { esc, fmtMs, fmtInt, fmtPct, driverLabel, scenarioLabel, workflowLabel, svgOpen, tabsHtml, tabsInit, hero, heroField, bannerArt, stripGlobe } from '../format.js';

export const C = { ok: '#0e7a3d', bad: '#d92d20', warn: '#b45309', cyan: '#0b9fb8', vio: '#535bd5', dim: '#c9cdd4', grid: '#c9cdd4' };

function filtersBar(state) {
  const sel = (name, label, options) =>
    `<div class="field"><label for="a-${name}">${label}</label><select id="a-${name}" data-f="${name}">`
    + `<option value="">All</option>` + options.map((o) =>
      `<option value="${esc(o)}"${state[name] === o ? ' selected' : ''}>${esc(o)}</option>`).join('')
    + `</select></div>`;
  return `<div class="panel float art-top float-lift">`
    + bannerArt({ id: 'an-b1', stops: ['#e6e4ff', '#f5f3ff', '#d2f5e8'], globe: 'right', deco: 'bars', label: 'Scope the figures' })
    + `<div class="filters">`
    + sel('source', 'Origin', state.facets.source || [])
    + sel('origin', 'Application', state.facets.origin || [])
    + sel('workflow_id', 'Workflow', state.facets.workflow_id || [])
    + sel('driver', 'Driver', state.facets.driver || [])
    + sel('scenario_id', 'Condition', state.facets.scenario_id || [])
    + sel('trial_kind', 'Trial kind', state.facets.trial_kind || [])
    + `</div><div class="btn-row" style="margin-top:12px">`
    + `<button class="btn primary" id="a-apply">Apply</button><span class="dim">All figures below respect these filters.</span></div></div>`;
}

export function matrixSvg(cells, linkFor) {
  const scenarios = [...new Set(cells.map((c) => c.scenario_id))].sort();
  const drivers = [...new Set(cells.map((c) => c.driver))].sort();
  const cw = 150; const ch = 64; const lx = 275; const ty = 34;
  const W = lx + drivers.length * cw + 20; const H = ty + scenarios.length * ch + 10;
  const byKey = new Map(cells.map((c) => [`${c.scenario_id}|${c.driver}`, c]));
  let s = svgOpen(W, H, 'Outcome matrix by condition and driver');
  drivers.forEach((d, j) => {
    s += `<text x="${lx + j * cw + cw / 2}" y="16" text-anchor="middle" class="tick">${esc(driverLabel(d))}</text>`;
  });
  scenarios.forEach((sc, i) => {
    s += `<text x="${lx - 10}" y="${ty + i * ch + ch / 2 + 4}" text-anchor="end" class="tick">${esc(scenarioLabel(sc))}</text>`;
    drivers.forEach((d, j) => {
      const c = byKey.get(`${sc}|${d}`);
      const x = lx + j * cw + 3; const y = ty + i * ch + 3;
      const w = cw - 6; const h = ch - 6;
      if (!c || !c.n) {
        s += `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="6" fill="none" stroke="${C.grid}" stroke-dasharray="4 3"/>`
          + `<text x="${x + w / 2}" y="${y + h / 2 + 4}" text-anchor="middle" class="tick">no runs</text>`;
        return;
      }
      const verified = c.ok + c.bad;
      const rate = verified ? c.ok / verified : null;
      const fill = rate === null ? C.dim : rate >= 0.95 ? C.ok : rate >= 0.5 ? C.warn : C.bad;
      const op = rate === null ? 0.35 : 0.28 + 0.62 * (c.n / (c.n + 8));
      const href = linkFor ? linkFor(c) : null;
      if (href) s += `<a href="${esc(href)}"><title>Open ${c.n} runs in history</title>`;
      s += `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="6" fill="${fill}" opacity="${op.toFixed(2)}"/>`
        + `<text x="${x + 10}" y="${y + 22}" class="val">${rate === null ? 'unverified' : fmtPct(rate) + ' verified-ok'}`
        + `<title>${c.n} runs · ${c.ok} ok · ${c.bad} bad · ${c.unknown} unknown · ${c.pending || 0} pending</title></text>`
        + `<text x="${x + 10}" y="${y + 40}" class="tick">n=${c.n} ✓${c.ok} ✗${c.bad} ?${c.unknown}</text>`;
      if (href) s += `</a>`;
    });
  });
  return s + '</svg>';
}

export function latencySvg(lat) {
  const W = 640; const H = 210; const padL = 46; const padB = 30; const padT = 14;
  const buckets = lat.buckets || [];
  const max = Math.max(1, ...buckets.map((b) => b.n));
  const bw = (W - padL - 14) / Math.max(1, buckets.length);
  let s = svgOpen(W, H, 'Latency distribution');
  [0.25, 0.5, 0.75, 1].forEach((f) => {
    const y = padT + (H - padT - padB) * (1 - f);
    s += `<line x1="${padL}" y1="${y}" x2="${W - 14}" y2="${y}" class="grid"/>`
      + `<text x="${padL - 6}" y="${y + 4}" text-anchor="end" class="tick">${Math.round(max * f)}</text>`;
  });
  buckets.forEach((b, i) => {
    const h = ((H - padT - padB) * b.n) / max;
    const x = padL + i * bw + 2; const y = H - padB - h;
    s += `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${(bw - 4).toFixed(1)}" height="${Math.max(h, b.n ? 2 : 0).toFixed(1)}" rx="3" fill="${C.cyan}" opacity="0.8"/>`;
    if (b.n) s += `<text x="${(x + bw / 2).toFixed(1)}" y="${(y - 5).toFixed(1)}" text-anchor="middle" class="val">${b.n}</text>`;
    const lbl = b.hi_ms === null ? `${b.lo_ms / 1000}s+` : b.lo_ms >= 1000 ? `${b.lo_ms / 1000}–${b.hi_ms / 1000}s` : `${b.lo_ms}–${b.hi_ms}`;
    s += `<text x="${(x + bw / 2).toFixed(1)}" y="${H - 12}" text-anchor="middle" class="tick">${lbl}</text>`;
  });
  return s + '</svg>';
}

export function hbars(rows, value, label, colorFn, fmt) {
  const W = 640; const rh = 30; const padL = 190;
  const H = rows.length * rh + 12;
  const max = Math.max(1, ...rows.map((r) => r[value] || 0));
  let s = svgOpen(W, H, label);
  rows.forEach((r, i) => {
    const y = 6 + i * rh;
    const w = ((W - padL - 70) * (r[value] || 0)) / max;
    const text = String(fmt(r));
    // Long values on near-full bars move inside the bar end instead
    // of clipping past the viewBox edge.
    const est = text.length * 6.2;
    const outside = padL + w + 8 + est <= W - 4;
    s += `<text x="${padL - 10}" y="${y + 15}" text-anchor="end" class="tick">${esc(r.label)}</text>`
      + `<rect x="${padL}" y="${y + 3}" width="${Math.max(w, r[value] ? 2 : 0).toFixed(1)}" height="14" rx="4" fill="${colorFn(r)}" opacity="0.85"/>`
      + (outside
        ? `<text x="${(padL + w + 8).toFixed(1)}" y="${y + 15}" class="val">${esc(text)}</text>`
        : `<text x="${(W - 6).toFixed(1)}" y="${y + 15}" text-anchor="end" class="val">${esc(text)}</text>`);
  });
  return s + '</svg>';
}

export function trendsSvg(days) {
  const W = 640; const H = 200; const padL = 40; const padB = 28; const padT = 16;
  const max = Math.max(1, ...days.map((d) => d.n));
  const n = Math.max(1, days.length);
  const bw = (W - padL - 14) / n;
  let s = svgOpen(W, H, 'Runs per day');
  days.forEach((d, i) => {
    const x = padL + i * bw + 2; const w = bw - 4;
    const hOk = ((H - padT - padB) * d.ok) / max;
    const hRest = ((H - padT - padB) * (d.n - d.ok)) / max;
    s += `<rect x="${x.toFixed(1)}" y="${(H - padB - hOk - hRest).toFixed(1)}" width="${w.toFixed(1)}" height="${Math.max(hRest, 0).toFixed(1)}" fill="${C.warn}" opacity="0.8"/>`
      + `<rect x="${x.toFixed(1)}" y="${(H - padB - hOk).toFixed(1)}" width="${w.toFixed(1)}" height="${Math.max(hOk, d.ok ? 2 : 0).toFixed(1)}" fill="${C.ok}" opacity="0.9"/>`
      + `<text x="${(x + w / 2).toFixed(1)}" y="${(H - padB - hOk - hRest - 5).toFixed(1)}" text-anchor="middle" class="val">${d.success_rate === null ? '—' : fmtPct(d.success_rate)}</text>`
      + `<text x="${(x + w / 2).toFixed(1)}" y="${H - 10}" text-anchor="middle" class="tick">${esc(String(d.day).slice(5))}</text>`;
  });
  return s + '</svg>';
}

export function coverageSvg(checks) {
  const W = 640; const rh = 34;
  const longest = Math.max(0, ...checks.map((c) => String(c.check_id || '').length));
  const padL = Math.min(220, Math.max(60, longest * 8 + 14));
  const H = checks.length * rh + 12;
  let s = svgOpen(W, H, 'Verification coverage per check');
  checks.forEach((c, i) => {
    const y = 6 + i * rh;
    const total = Math.max(1, c.n);
    const w = W - padL - 120;
    const wOk = (w * c.satisfied) / total;
    const wBad = (w * c.failed) / total;
    s += `<text x="${padL - 10}" y="${y + 17}" text-anchor="end" class="val">${esc(c.check_id)}</text>`
      + `<rect x="${padL}" y="${y + 4}" width="${wOk.toFixed(1)}" height="14" fill="${C.ok}" opacity="0.9"/>`
      + `<rect x="${padL + wOk}" y="${y + 4}" width="${wBad.toFixed(1)}" height="14" fill="${C.bad}" opacity="0.9"/>`
      + `<rect x="${padL + wOk + wBad}" y="${y + 4}" width="${(w - wOk - wBad).toFixed(1)}" height="14" fill="${C.dim}"/>`
      + `<text x="${padL + w + 8}" y="${y + 17}" class="tick">${c.satisfied}/${c.failed}/${c.unavailable} ok·bad·n/a</text>`;
  });
  return s + '</svg>';
}

export function saucePanelHtml(sc) {
  if (!sc || !sc.total) return '';
  const acc = sc.verification_accuracy || {};
  const dur = sc.durations || {};
  const checkLine = (sc.checks || []).map((c) =>
    `${esc(c.check_id)} ${fmtPct(c.rate)} (${fmtInt(c.satisfied)}/${fmtInt(c.n)})`).join(' · ');
  const agree = (acc.agree_success || 0) + (acc.agree_failure || 0);
  return `<div class="panel art-top"><h2>SauceDemo order funnel</h2>`
    + `<figure class="viz">${hbars(
      (sc.funnel || []).map((f) => ({ label: `${f.stage} (${f.check_id})`, n: f.n })),
      'n', 'SauceDemo funnel stages', () => C.cyan,
      (r) => `${r.n}/${sc.verified}`)}</figure>`
    + `<p class="caption">Cumulative: a run past checkout also passed login. `
    + `Sort (S2) is judged separately with its own denominator because it runs only when sorting is requested. `
    + `Per-check rates: <strong>${checkLine}</strong>.</p>`
    + `<h3>Failure stages</h3><figure class="viz">${hbars(
      (sc.failure_stages || []).map((s) => ({ label: s.stage, n: s.n })),
      'n', 'SauceDemo failure stages',
      (r) => (r.label.startsWith('none') ? C.ok : r.label === 'unverified' ? C.dim : C.bad),
      (r) => String(r.n))}</figure>`
    + `<p class="caption">First failed check per verified run; a driver gate refusal (e.g. empty cart) counts for the stage that refused. Unverified runs are listed, never assigned a stage.</p>`
    + `<h3>Reported vs verified</h3>`
    + `<p style="margin-top:0">Driver reports agreed with independent verification on `
    + `<strong>${agree}/${fmtInt(acc.denominator)}</strong> adjudicated runs`
    + ` (${fmtInt(acc.false_success)} false success · ${fmtInt(acc.false_failure)} false failure · `
    + `${fmtInt(acc.unadjudicated)} unadjudicated). Order durations: p50 ${fmtMs(dur.p50)} · `
    + `p95 ${fmtMs(dur.p95)} over ${fmtInt(dur.n)} measured runs.</p></div>`;
}

export function sauceStressPanelHtml(sc) {
  if (!sc || !sc.total) return '';
  const acc = sc.verification_accuracy || {};
  const dur = sc.durations || {};
  const checkLine = (sc.checks || []).map((c) =>
    `${esc(c.check_id)} ${fmtPct(c.rate)} (${fmtInt(c.satisfied)}/${fmtInt(c.n)})`).join(' · ');
  const agree = (acc.agree_success || 0) + (acc.agree_failure || 0);
  const accountName = { standard: 'Standard (control)', glitch: 'Slow login', problem: 'Problem user' };
  const readinessLine = (sc.readiness || []).map((r) =>
    `${esc(accountName[r.account] || r.account)} · ${esc(driverLabel(r.driver))}: `
    + `p50 ${fmtMs(r.p50)} (n=${fmtInt(r.n)}${r.missing ? `, ${fmtInt(r.missing)} unmeasured` : ''})`).join('<br>');
  const disagreeLine = (sc.check_disagreement || []).map((d) =>
    `${esc(d.check_id)}: chimera ${fmtPct(d.chimera.rate)} (n=${fmtInt(d.chimera.n)}) vs `
    + `baseline ${fmtPct(d.baseline.rate)} (n=${fmtInt(d.baseline.n)})`).join('<br>');
  return `<div class="panel art-top"><h2>SauceDemo stress funnel (T1–T6)</h2>`
    + `<figure class="viz">${hbars(
      (sc.funnel || []).map((f) => ({ label: `${f.stage} (${f.check_id})`, n: f.n })),
      'n', 'SauceDemo stress funnel stages', () => C.cyan,
      (r) => `${r.n}/${sc.verified}`)}</figure>`
    + `<p class="caption">Cumulative: a run past checkout also passed login. `
    + `Images (T2), sort (T3), and cart-after-remove (T5) are judged separately with their own denominators. `
    + `Per-check rates: <strong>${checkLine}</strong>.</p>`
    + `<h3>Login readiness by account × driver</h3>`
    + `<p style="margin-top:0">${readinessLine || 'No readiness measurements yet.'}</p>`
    + `<p class="caption">Click-to-readiness latency from the login stage states; unmeasured when the stage evidence is missing.</p>`
    + `<h3>Per-check driver comparison</h3>`
    + `<p style="margin-top:0">${disagreeLine}</p>`
    + `<p class="caption">Unpaired satisfied-rates per driver with both denominators; verdict-level pairing stays in Paired outcomes.</p>`
    + `<h3>Failure stages</h3><figure class="viz">${hbars(
      (sc.failure_stages || []).map((s) => ({ label: s.stage, n: s.n })),
      'n', 'SauceDemo stress failure stages',
      (r) => (r.label.startsWith('none') ? C.ok : r.label === 'unverified' ? C.dim : C.bad),
      (r) => String(r.n))}</figure>`
    + `<p class="caption">First failed T-check per verified run; a driver gate refusal counts for the stage that refused. Unverified runs are listed, never assigned a stage.</p>`
    + `<h3>Reported vs verified</h3>`
    + `<p style="margin-top:0">Driver reports agreed with independent verification on `
    + `<strong>${agree}/${fmtInt(acc.denominator)}</strong> adjudicated runs`
    + ` (${fmtInt(acc.false_success)} false success · ${fmtInt(acc.false_failure)} false failure · `
    + `${fmtInt(acc.unadjudicated)} unadjudicated). Flow durations: p50 ${fmtMs(dur.p50)} · `
    + `p95 ${fmtMs(dur.p95)} over ${fmtInt(dur.n)} measured runs.</p></div>`;
}

export async function viewAnalytics(el) {
  const facets = await api.facets().catch(() => ({ facets: {} }));
  const state = {
    source: '', origin: '', workflow_id: '', driver: '', scenario_id: '',
    trial_kind: '', facets: facets.facets || {},
  };

  function params(extra) {
    return queryString({
      source: state.source, origin: state.origin,
      workflow_id: state.workflow_id,
      driver: state.driver, scenario_id: state.scenario_id,
      trial_kind: state.trial_kind, ...(extra || {}),
    });
  }

  async function load() {
    const box = el.querySelector('#an-body');
    const prevTab = box.querySelector('[role="tab"][aria-selected="true"]');
    const activeTab = prevTab ? prevTab.id.replace('an-tab-', '') : 'overview';
    box.innerHTML = `<p class="dim">Computing figures…</p>`;
    try {
      const [ov, wf, mx, lat, fail, tr, st, dr, vc, sc, sst] = await Promise.all([
        api.analytics('overview', params()),
        api.analytics('workflows', params()),
        api.analytics('matrix', params()),
        api.analytics('latency', params()),
        api.analytics('failures', params()),
        api.analytics('trends', params()),
        api.analytics('stages', params()),
        api.analytics('drivers', params()),
        api.analytics('verification', params()),
        api.analytics('sauce', params()),
        api.analytics('sauce-stress', params()),
      ]);
      if (!ov.total) {
        box.innerHTML = await emptyHtml();
        wireClear(box);
        return;
      }
      const ovHtml = overviewHtml(ov);
      const runsHtml = `<div class="panel"><h2>Runs over time</h2><figure class="viz">${trendsSvg(tr.days)}</figure>`
        + `<p class="caption">Daily volume (green = verified successes) with the verified-success rate on top. Benchmark imports share one date; new workbench runs extend the line.</p></div>`;
      const compareHtml = `<div class="panel"><h2>Workflow comparison</h2><figure class="viz">${hbars(
        wf.workflows.map((w) => ({ label: workflowLabel(w.workflow_id), rate: w.success_rate, w })),
        'rate', 'Workflow success rates', () => C.vio,
        (r) => `${fmtPct(r.rate)} · n=${r.w.verified} verified · p50 ${fmtMs(r.w.p50)}`)}</figure>`
        + `<p class="caption">Verified-success rate per workflow with verified denominators and median durations. `
        + `Benchmark history covers the project workflow only — contact figures come from live workbench runs.</p></div>`
        + `<div class="panel"><h2>Outcome matrix — condition × driver</h2><figure class="viz">${matrixSvg(mx.cells)}</figure>`
        + `<p class="caption">Each cell is one condition–driver pair. The headline rate counts <strong>verified successes ÷ verified runs only</strong>; `
        + `unknown and pending runs are listed, never folded in. Deeper color means more runs behind the cell.</p></div>`;
      const latencyHtml = `<div class="panel"><h2>Latency landscape</h2><figure class="viz">${latencySvg(lat)}</figure>`
        + `<p class="caption">Run durations in fixed buckets over <strong>${fmtInt(lat.overall.n)} measured runs</strong> `
        + `(p50 ${fmtMs(lat.overall.p50)} · p95 ${fmtMs(lat.overall.p95)}${lat.overall.sampled ? ' · sampled at 50k rows' : ''}). `
        + `Slow-load runs legitimately sit right of normal ones.</p></div>`;
      const duelHtml = `<div class="panel"><h2>Driver duel</h2><figure class="viz">${hbars(
        dr.drivers.map((d) => ({ label: driverLabel(d.driver), rate: d.success_rate, d })),
        'rate', 'Driver success rates', () => C.cyan,
        (r) => `${fmtPct(r.rate)} · n=${r.d.verified} verified`)}</figure>`
        + `<p class="caption">Verified-success rate per driver with the verified denominator beside it. Drivers with no verified runs show a dash, not zero.</p></div>`;
      const failHtml = `<div class="panel"><h2>Failure map</h2><figure class="viz">${hbars(
        fail.by_category.map((c) => ({ label: c.name, n: c.n })),
        'n', 'Failures by category', () => C.bad, (r) => String(r.n))}</figure>`
        + `<p class="caption"><strong>${fmtInt(fail.total_failures)} failed, errored, or cancelled runs</strong> grouped by failure category. `
        + `Timeouts cluster on slow-load conditions; broken-submit conditions fail at the click.</p></div>`;
      const stageHtml = `<div class="panel"><h2>Stage analysis</h2><figure class="viz">${hbars(
        st.stages.map((s) => ({ label: `${s.action} (${s.errors} errors)`, avg: s.avg_ms || 0, s })),
        'avg', 'Mean stage durations', (r) => (r.s.errors ? C.warn : C.ok),
        (r) => `${r.s.avg_ms === null ? 'unmeasured' : fmtMs(r.s.avg_ms)} · n=${r.s.n}`)}</figure>`
        + `<p class="caption">Mean time per browser-action stage across <strong>observed actions only</strong>, with the error count beside each stage. Stages without timings say so.</p></div>`;
      const coverHtml = `<div class="panel"><h2>Verification coverage</h2><figure class="viz">${coverageSvg(vc.checks)}</figure>`
        + `<p class="caption">Per-check outcomes across recorded verifications: satisfied (green), failed (red), unavailable (grey). `
        + (vc.checks.some((c) => String(c.check_id).startsWith('S'))
          ? `P1 confirmation visible · P2 exactly the expected name · P3 exactly one entry. `
          + `S1 login reached inventory · S2 catalog order (when sorting) · S3 expected cart · S4 checkout accepted · S5 order confirmed.</p></div>`
          : `P1 confirmation visible · P2 exactly the expected name · P3 exactly one entry.</p></div>`);
      // Summary-first: sticky overview strip + tab-grouped panels.
      // Every panel keeps its heading, figure code, and order within
      // its group; nothing is removed.
      box.innerHTML = stripHtml(ov)
        + tabsHtml('an', 'Analytics sections', [
          ['overview', 'Overview', ovHtml + runsHtml],
          ['funnels', 'Funnels', saucePanelHtml(sc) + sauceStressPanelHtml(sst)],
          ['compare', 'Compare', compareHtml],
          ['reliability', 'Reliability', `<div class="split">${latencyHtml}${duelHtml}</div>` + failHtml + stageHtml],
          ['coverage', 'Coverage', coverHtml],
        ], activeTab);
      tabsInit(box);
    } catch (err) {
      box.innerHTML = `<div class="banner bad" role="alert"><strong>Analytics unavailable:</strong> ${esc(err.message)}</div>`;
    }
  }


  // Zero-match state: say which filters are active and how many
  // rows exist unfiltered, instead of rendering hollow panels.
  async function emptyHtml() {
    let total = null;
    try {
      const unfiltered = await api.list('?page_size=1');
      total = unfiltered.total;
    } catch { total = null; }
    const active = ['source', 'origin', 'workflow_id', 'driver', 'scenario_id', 'trial_kind']
      .filter((k) => state[k])
      .map((k) => `<strong>${esc(k)}</strong> = ${esc(state[k])}`);
    const scope = total === null ? '' : ` of ${fmtInt(total)} indexed`;
    const hint = total === 0
      ? `No executions are indexed yet — <a href="#/workspace">run a workflow</a> first.`
      : `Loosen the filters or clear them to see every indexed execution.`;
    return `<div class="banner warn" role="status"><strong>0${scope} executions match these filters.</strong> ${hint}`
      + (active.length ? `<br>Active filters: ${active.join(' · ')}.` : '')
      + `</div><div class="btn-row"><button class="btn" id="a-clear">Clear filters</button></div>`;
  }

  function wireClear(box) {
    const btn = box.querySelector('#a-clear');
    if (!btn) return;
    btn.addEventListener('click', () => {
      ['source', 'origin', 'workflow_id', 'driver', 'scenario_id', 'trial_kind'].forEach((k) => { state[k] = ''; });
      el.querySelectorAll('[data-f]').forEach((input) => { input.value = ''; });
      load();
    });
  }

  function stripHtml(ov) {
    const d = ov.durations || {};
    const by = ov.by_verdict || {};
    return `<div class="wb-strip" role="region" aria-label="Overview figures">` + stripGlobe()
      + `<figure><div class="n">${fmtInt(ov.total)}</div><div class="c">executions · n=${fmtInt(ov.total)}</div></figure>`
      + `<figure><div class="n">${fmtPct(ov.verified_success_rate)}</div><div class="c">verified-ok rate · ${fmtInt(ov.verified_denominator)} verified</div></figure>`
      + `<figure><div class="n">${fmtInt(by['insufficient-evidence'] || 0)}</div><div class="c">insufficient evidence · never counted as success</div></figure>`
      + `<figure><div class="n">${fmtMs(d.p50)}–${fmtMs(d.p95)}</div><div class="c">latency p50–p95 · ${fmtInt(d.missing)} unmeasured</div></figure>`
      + `</div>`;
  }

  function overviewHtml(ov) {
    const d = ov.durations || {};
    return `<div class="panel"><h2>Overview</h2><div class="kv">`
      + `<div class="cell"><div class="k">Executions</div><div class="v mono">${fmtInt(ov.total)}</div></div>`
      + `<div class="cell"><div class="k">Verified success rate</div><div class="v mono">${fmtPct(ov.verified_success_rate)}</div></div>`
      + `<div class="cell"><div class="k">Verified denominator</div><div class="v mono">${fmtInt(ov.verified_denominator)}</div></div>`
      + `<div class="cell"><div class="k">Insufficient evidence</div><div class="v mono">${fmtInt((ov.by_verdict || {})['insufficient-evidence'] || 0)}</div></div>`
      + `<div class="cell"><div class="k">p50 / p95</div><div class="v mono">${fmtMs(d.p50)} / ${fmtMs(d.p95)}</div></div>`
      + `<div class="cell"><div class="k">Missing durations</div><div class="v mono">${fmtInt(d.missing)}</div></div>`
      + `</div><p class="caption">The success rate divides by <strong>verified runs only</strong> (${fmtInt(ov.verified_denominator)} of ${fmtInt(ov.total)}). `
      + `Pending and unverifiable runs are counted beside it, never inside it.</p></div>`;
  }

  el.innerHTML = hero({
    kicker: 'Evidence · figures',
    head: '<h1 id="page-h1">Analytics</h1>',
    lede: `Figures computed live from the execution index — <strong>rates always show their denominators</strong>, `
      + `missing data is labelled, and benchmark history stays visibly separate from new runs via the origin filter. Default view: every indexed execution; narrow it with the filters.`,
    field: heroField('an', ['#c4b5fd', '.48', '.24'], ['#99f6e4', '.45', '.18'], [600, 320, 170, 182]),
  })
    + filtersBar(state) + `<div id="an-body"></div>`;
  el.querySelector('#a-apply').addEventListener('click', () => {
    el.querySelectorAll('[data-f]').forEach((input) => {
      state[input.dataset.f] = input.value;
    });
    load();
  });
  await load();
  return null;
}
