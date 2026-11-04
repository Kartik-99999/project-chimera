/* Execution detail: what was expected, what happened, the proof. */
import { api } from '../api.js';
import { esc, fmtMs, fmtWhen, fmtInt, verdictPill, statusPill, driverLabel, scenarioLabel, sourcePill, originPill, workflowLabel, sessionLabel, banner, emptyState, hero, heroField, navySection } from '../format.js';
import { mountConvergence } from '/research/js/viz/convergence.js';

const STAGES = ['Action', 'Execution', 'Observation', 'Verification', 'Evidence'];

// Presentational journey stage derived from real run state: a judged
// run has travelled all five tributaries; a live run sits where its
// phase text and observed actions place it.
function journeyStage(r, live) {
  if (r.verdict === 'verified-success' || r.verdict === 'verified-failure') return 5;
  if (r.verdict === 'insufficient-evidence') return 4;
  if (!live) return 4;
  const phase = String((r.progress && r.progress.phase) || r.status || '');
  if (/verify|judg|teardown/i.test(phase)) return 4;
  if (/observ|snapshot|screenshot|captur/i.test(phase)) return 3;
  if (/queue/i.test(phase) && !(r.progress && r.progress.actions_seen)) return 1;
  return ((r.progress && r.progress.actions_seen) || 0) > 0 ? 2 : 1;
}

function waypoints(r, stage, live) {
  const sealed = r.verdict === 'verified-success';
  const failed = r.verdict === 'verified-failure';
  const subs = [
    live ? `${(r.progress && r.progress.actions_seen) || 0} observed` : `${r.actions_count ?? 0} recorded`,
    typeof r.duration_ms === 'number' ? fmtMs(r.duration_ms) : String((r.progress && r.progress.phase) || r.status || ''),
    r.snapshot_path ? 'snapshot kept' : 'no snapshot',
    (r.checks || []).length ? `${r.checks.length} checks` : 'no checks',
    sealed ? 'verified ✓' : failed ? 'verified ✗' : r.verdict === 'insufficient-evidence' ? 'unresolved' : 'awaiting',
  ];
  return `<ol class="waypoints" aria-label="Run journey: action to evidence">` + STAGES.map((name, i) => {
    const n = i + 1;
    const cls = n < stage ? 'done' : n === stage
      ? (n === 5 && sealed ? 'sealed' : n === 5 && failed ? 'failed' : 'now') : '';
    const mark = n < stage ? '✓' : n === 5 && sealed ? '✓' : n === 5 && failed ? '✗' : String(n);
    const cur = n === stage ? ' aria-current="step"' : '';
    return `<li class="${cls}"${cur}><span class="wp-dot" aria-hidden="true">${mark}</span>`
      + `<span class="wp-name">${name}</span><span class="wp-sub">${esc(subs[i])}</span></li>`;
  }).join('') + `</ol>`;
}

const SEAL_SVG = `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/><path d="M8 12.5l2.6 2.6L16 9.5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

function waterfall(actions, totalMs) {
  if (!actions || !actions.length) {
    return `<p class="dim">No action records attached to this execution.</p>`;
  }
  // Lanes stack in recorded order; widths use measured elapsed time when
  // present, otherwise share the run duration honestly as "unmeasured".
  const usable = actions.map((a) => (typeof a.elapsed_ms === 'number' ? a.elapsed_ms : null));
  const span = (typeof totalMs === 'number' && totalMs > 0) ? totalMs
    : usable.reduce((s, v) => s + (v || 0), 0) || 1;
  let cursor = 0;
  const lanes = actions.map((a, i) => {
    const width = usable[i] === null ? 0 : Math.max(0.6, (usable[i] / span) * 100);
    const left = Math.min(100, (cursor / span) * 100);
    cursor += usable[i] || 0;
    const label = `${a.action_type}${a.target_summary ? ` · ${a.target_summary}` : ''}${a.error_type ? ` · ${a.error_type}` : ''}`;
    const ms = usable[i] === null ? 'unmeasured' : fmtMs(usable[i]);
    return `<div class="lane"><span class="lbl" title="${esc(label)}">${esc(a.action_type)}</span>`
      + `<span class="track"><span class="seg ${a.outcome === 'error' ? 'error' : 'ok'}" style="left:${left.toFixed(2)}%;width:${width.toFixed(2)}%"></span></span>`
      + `<span class="ms">${esc(ms)}</span></div>`;
  }).join('');
  return `<div class="wfall" role="img" aria-label="Action timeline, ${actions.length} actions">${lanes}</div>`;
}

export async function viewRun(el, id, badges) {
  let timer = null;
  let failCount = 0;
  let conv = null;

  async function load() {
    let record;
    try {
      ({ execution: record } = await api.get(id));
      failCount = 0;
    } catch (err) {
      failCount += 1;
      // A missing id never resolves by retrying: fail fast instead of
      // holding the stale prior view through silent retries.
      if (err.status === 404 || failCount > 8) {
        el.innerHTML = banner('bad', `<strong>Execution unavailable:</strong> ${esc(err.message)}.`)
          + emptyState('Execution unavailable', `Could not load this execution: ${esc(err.message)}.`, 'empty-server');
        return null;
      }
      return 'retry';
    }
    const r = record;
    const live = r.status === 'queued' || r.status === 'running';
    const prog = r.progress || {};
    badges.innerHTML = statusPill(r.status) + ' ' + verdictPill(r.verdict);

    const checks = (r.checks || []).map((c) => {
      const mark = c.satisfied === 1 || c.satisfied === true ? ['t', '✓']
        : c.satisfied === 0 || c.satisfied === false ? ['f', '✗'] : ['u', '?'];
      return `<li><span class="mark ${mark[0]}" aria-hidden="true">${mark[1]}</span>`
        + `<span><strong>${esc(c.check_id)}</strong> — ${esc(c.detail || (mark[0] === 'u' ? 'no evidence recorded' : ''))}</span></li>`;
    }).join('') || '<li><span class="dim">No verification checks recorded.</span></li>';

    const submitted = (r.progress && r.progress.submitted) || null;
    const isStudio = typeof r.workflow_id === 'string' && r.workflow_id.startsWith('studio:');
    let expected;
    if (isStudio) {
      const p = (r.progress && r.progress.params) || {};
      const vars = p.variables ? Object.entries(p.variables).map(([k, v]) => `${k}=${v}`).join(', ') : '';
      expected = `Run studio workflow <strong>${esc(p.workflow_name || r.project_name || '—')}</strong> `
        + `(v${esc(String(p.version ?? '?'))})${vars ? ` with <code>${esc(vars)}</code>` : ''}: `
        + `every step's contract is judged from its recorded attempts and observations.`;
    } else if (r.workflow_id === 'fill-contact-form' && submitted && submitted.email !== undefined) {
      const entry = `${submitted.name} <${submitted.email}> [${submitted.subject || ''}] ${submitted.message || ''}`;
      expected = `Send the message from <strong>${esc(submitted.name || '—')}</strong> `
        + `(${esc(submitted.email || 'no address')})`
        + `${submitted.subject ? ` about <strong>${esc(submitted.subject)}</strong>` : ' (no subject)'}`
        + `${submitted.message ? '' : ' with an <strong>empty message</strong>'}: confirmation visible and exactly this entry in the sent list, `
        + `nothing else:<br><code>${esc(entry) || '(empty)'}</code>`;
    } else if (r.workflow_id === 'fill-contact-form') {
      expected = `Send the contact message and confirm it appears in the sent list exactly once.`;
    } else if (r.workflow_id === 'saucedemo-stress') {
      const p = (r.progress && r.progress.params) || {};
      if (p.account) {
        const user = p.account === 'glitch' ? 'performance_glitch_user'
          : p.account === 'problem' ? 'problem_user' : 'standard_user';
        const sortBit = p.sort && p.sort !== 'none' ? `, sort the catalog <strong>${esc(p.sort)}</strong>` : '';
        const removeBit = !p.remove_item || p.remove_item === 'last-added'
          ? `, remove the last-added item and re-verify the remainder`
          : `, keep the full cart (no removal)`;
        expected = `Log into SauceDemo as <strong>${esc(user)}</strong>${sortBit}, add the `
          + `<strong>${esc(p.cart_preset || 'preset')}</strong> items${removeBit}, and check out: `
          + `each reached stage is judged from recorded page states (T1–T6).`;
      } else {
        expected = `Run the fixed SauceDemo stress flow and judge each reached stage from recorded page states (T1–T6).`;
      }
    } else if (r.workflow_id === 'saucedemo-order') {
      const p = (r.progress && r.progress.params) || {};
      if (p.login_case) {
        const user = p.login_case === 'locked-out' ? 'locked_out_user' : 'standard_user';
        const loginBit = p.login_case === 'standard' ? `Log into SauceDemo as <strong>${esc(user)}</strong>`
          : `Attempt login as <strong>${esc(user)}</strong> (must be rejected)`;
        const sortBit = p.sort && p.sort !== 'none' ? `, sort the catalog <strong>${esc(p.sort)}</strong>` : '';
        const cartBit = p.cart_preset === 'empty-cart' ? `, leave the cart <strong>empty</strong> (checkout must be refused)`
          : `, add the <strong>${esc(p.cart_preset || 'preset')}</strong> items to the cart`;
        const infoBit = !p.checkout_case || p.checkout_case === 'complete' ? `, and check out`
          : `, and check out with <strong>${esc(p.checkout_case)}</strong> information (must be rejected)`;
        expected = `${loginBit}${sortBit}${cartBit}${infoBit}: each reached stage is judged from recorded page states (S1–S5).`;
      } else {
        expected = `Run the fixed SauceDemo order flow and judge each reached stage from recorded page states (S1–S5).`;
      }
    } else if (r.workflow_id === 'flipkart-add-to-cart') {
      const q = submitted && submitted.query;
      const pick = submitted && submitted.pick;
      expected = (q !== undefined && pick !== undefined
        ? `Search Flipkart for <strong>${esc(q)}</strong>, add result <strong>#${esc(String(pick))}</strong> to the guest cart, `
        : `Search Flipkart, add one result to the guest cart, `)
        + `and confirm the cart holds exactly that item (qty 1): each reached stage is judged from recorded page states (F1–F3).`;
    } else if (r.workflow_id === 'wikipedia-article-lookup') {
      const q = submitted && submitted.query;
      const pick = submitted && submitted.pick;
      expected = (q !== undefined && pick !== undefined
        ? `Search Wikipedia for <strong>${esc(q)}</strong> and open result <strong>#${esc(String(pick))}</strong>, `
        : `Search Wikipedia and open one article, `)
        + `then confirm the article heading matches the pick: each reached stage is judged from recorded page states (WI1–WI2).`;
    } else if (r.workflow_id === 'wiktionary-word-lookup') {
      const w = submitted && submitted.word;
      expected = (w !== undefined
        ? `Open the Wiktionary entry for <strong>${esc(w)}</strong> `
        : `Open one Wiktionary entry `)
        + `and confirm the word exists with recorded definitions: judged from the recorded entry state (WX1–WX2).`;
    } else if (r.workflow_id === 'pypi-package-lookup') {
      const p = submitted && submitted.package;
      expected = (p !== undefined
        ? `Open the PyPI project page for <strong>${esc(p)}</strong> `
        : `Open one PyPI project page `)
        + `and confirm the package name, version, and summary: judged from the recorded package state (PY1–PY2).`;
    } else if (r.workflow_id === 'bbc-headlines') {
      const s = submitted && submitted.section;
      expected = (s !== undefined
        ? `Open the BBC <strong>${esc(s)}</strong> section front `
        : `Open one BBC section front `)
        + `and confirm the section was served with recorded headlines: judged from the recorded section state (BB1–BB2).`;
    } else if (r.workflow_id === 'github-profile') {
      const u = submitted && submitted.username;
      expected = (u !== undefined
        ? `Open the public GitHub profile for <strong>${esc(u)}</strong> `
        : `Open one public GitHub profile `)
        + `and confirm the handle and display name: judged from the recorded profile state (GH1–GH2).`;
    } else if (r.workflow_id === 'crates-lookup') {
      const c = submitted && submitted.crate;
      expected = (c !== undefined
        ? `Open the crates.io page for <strong>${esc(c)}</strong> `
        : `Open one crates.io crate page `)
        + `and confirm the crate name, version, and summary: judged from the recorded crate state (CR1–CR2).`;
    } else if (r.workflow_id === 'bbc-weather') {
      const c = submitted && submitted.city;
      expected = (c !== undefined
        ? `Open the BBC Weather forecast for <strong>${esc(c)}</strong> `
        : `Open one BBC Weather city forecast `)
        + `and confirm the city was served with recorded temperatures: judged from the recorded forecast state (BW1–BW2).`;
    } else if (r.workflow_id === 'github-search') {
      const q = submitted && submitted.query;
      expected = (q !== undefined
        ? `Search GitHub repositories for <strong>${esc(q)}</strong> `
        : `Search GitHub repositories `)
        + `and confirm results were served with recorded repo names: judged from the recorded search state (GS1–GS2).`;
    } else if (r.workflow_id === 'steam-price-check') {
      const q = submitted && submitted.query;
      const pick = submitted && submitted.pick;
      expected = (q !== undefined && pick !== undefined
        ? `Search the Steam store for <strong>${esc(q)}</strong> and open result <strong>#${esc(String(pick))}</strong>, `
        : `Search the Steam store and open one game, `)
        + `then confirm the game name and displayed price: each reached stage is judged from recorded page states (ST1–ST2).`;
    } else if (r.workflow_id === 'arxiv-search') {
      const q = submitted && submitted.query;
      expected = (q !== undefined
        ? `Search arXiv papers for <strong>${esc(q)}</strong> `
        : `Search arXiv papers `)
        + `and confirm results were served with recorded paper titles: judged from the recorded search state (AX1–AX2).`;
    } else if (r.workflow_id === 'stackoverflow-search') {
      const q = submitted && submitted.query;
      expected = (q !== undefined
        ? `Search Stack Overflow questions for <strong>${esc(q)}</strong> `
        : `Search Stack Overflow questions `)
        + `and confirm results were served with recorded question titles: judged from the recorded search state (SO1–SO2).`;
    } else if (r.workflow_id === 'amazon-price-check') {
      const q = submitted && submitted.query;
      const pick = submitted && submitted.pick;
      expected = (q !== undefined && pick !== undefined
        ? `Search Amazon for <strong>${esc(q)}</strong> and open result <strong>#${esc(String(pick))}</strong>, `
        : `Search Amazon and open one product, `)
        + `then confirm the product name and displayed price: each reached stage is judged from recorded page states (AM1–AM2).`;
    } else if (r.project_name) {
      expected = `Create a project named <strong>${esc(r.project_name)}</strong>: confirmation visible, exactly that name in the list, nothing else.`;
    } else {
      expected = `Create the benchmark's expected project (historical record — the input name was not stored with the episode).`;
    }
    const nChecks = (r.checks || []).length;
    const held = nChecks ? `all ${nChecks} checks held` : 'all checks held';
    const broken = nChecks ? `at least one of ${nChecks} checks failed` : 'at least one check failed';
    const evidenceNote = isStudio
      ? `The recorded step attempts were judged after the run and <strong>${held}</strong>.`
      : (r.workflow_id === 'saucedemo-order' || r.workflow_id === 'saucedemo-stress' || r.workflow_id === 'flipkart-add-to-cart' || r.workflow_id === 'wikipedia-article-lookup' || r.workflow_id === 'wiktionary-word-lookup' || r.workflow_id === 'pypi-package-lookup' || r.workflow_id === 'bbc-headlines' || r.workflow_id === 'github-profile' || r.workflow_id === 'crates-lookup' || r.workflow_id === 'bbc-weather' || r.workflow_id === 'github-search' || r.workflow_id === 'steam-price-check' || r.workflow_id === 'arxiv-search' || r.workflow_id === 'stackoverflow-search' || r.workflow_id === 'amazon-price-check')
        ? `The recorded stage states were judged after the run and <strong>${held}</strong>.`
        : `The page was read back after the run and <strong>${held}</strong>.`;
    const actual = r.verdict === 'verified-success'
      ? evidenceNote
      : r.verdict === 'verified-failure'
        ? `The independent evidence was judged after the run and <strong>${broken}</strong> — see below.`
        : r.verdict === 'insufficient-evidence'
          ? `The result <strong>could not be verified</strong> (evidence missing or malformed). This is reported as unknown — never as success.`
          : `The run has <strong>not finished</strong>; nothing is claimed yet.`;

    el.innerHTML = `<p><a href="#/history">← All executions</a>`
      + (isStudio ? ` · <a href="#/studio/${encodeURIComponent(r.workflow_id.slice('studio:'.length))}">← Studio workflow</a>` : '')
      + `</p>`
      + hero({
        kicker: 'Run &amp; inspect · Execution',
        head: `<div class="runhead" style="justify-content:center;text-align:center"><div>`
          + `<h1 id="page-h1">${esc(r.project_name || `Execution ${r.id.slice(0, 8)}`)}</h1>`
          + `<span class="id">${esc(r.id)}</span></div></div>`
          + `<div style="margin:14px 0 0;display:flex;gap:8px;flex-wrap:wrap;justify-content:center">`
          + `${sourcePill(r.source)}${originPill(r.origin)}`
          + (r.source_ref ? `<span class="pill">${esc(r.source_ref.split(':')[0])}</span>` : '') + `</div>`,
        compact: true,
        field: heroField('rn', ['#fecdd3', '.48', '.22'], ['#c7d2fe', '.45', '.18'], [600, 320, 170, 182]),
      })
      + `<nav class="wb-chips" aria-label="Jump to run sections">`
      + `<a href="#run-journey">Journey</a><a href="#run-result">Result</a><a href="#run-checks">Checks</a>`
      + `<a href="#run-timeline">Timeline</a><a href="#run-final">Final</a><a href="#run-evidence">Evidence</a></nav>`
      + journeyPanel(r, live)
      + (live ? `<div class="panel"><h2>Running now</h2>`
        + `<div style="display:flex;gap:10px;align-items:center"><span class="pulse live" aria-hidden="true"></span>`
        + `<strong>Phase: ${esc(prog.phase || r.status)}</strong>`
        + `<span class="dim">actions observed: ${prog.actions_seen ?? 0}</span>`
        + `<span style="flex:1"></span><button class="btn danger" id="run-cancel">Cancel run</button></div>`
        + `<div class="progress"><div class="bar"><div class="fill" style="--fill:0.45"></div></div></div>`
        + `<p class="caption">Live state, refreshing every second. Actions appear below as the observer records them.</p></div>` : '')
      + `<div class="panel wb-anchor" id="run-result"><h2>Result</h2>`
      + `<div class="kv">`
      + `<div class="cell"><div class="k">Verdict</div><div class="v">${verdictPill(r.verdict)}`
      + (r.verdict === 'verified-success' ? ` <span class="seal">${SEAL_SVG}sealed</span>` : '') + `</div></div>`
      + `<div class="cell"><div class="k">Workflow</div><div class="v">${esc(workflowLabel(r.workflow_id))}</div></div>`
      + `<div class="cell"><div class="k">Driver</div><div class="v">${esc(driverLabel(r.driver))}</div></div>`
      + `<div class="cell"><div class="k">Session</div><div class="v">${esc(sessionLabel(r.session))}</div></div>`
      + `<div class="cell"><div class="k">Condition</div><div class="v">${esc(scenarioLabel(r.scenario_id))}</div></div>`
      + `<div class="cell"><div class="k">Duration</div><div class="v mono">${esc(fmtMs(r.duration_ms))}</div></div>`
      + `<div class="cell"><div class="k">Actions</div><div class="v mono">${esc(fmtInt(r.actions_count))}</div></div>`
      + `<div class="cell"><div class="k">Action errors</div><div class="v mono">${esc(fmtInt(r.retries))}</div></div>`
      + `</div>`
      + `<h3>Expected</h3><p style="margin-top:0">${expected}</p>`
      + `<h3>What actually happened</h3><p style="margin-top:0">${actual}</p>`
      + (r.error ? banner('bad', `<strong>${esc(r.error_type || 'Error')}:</strong> ${esc(r.error)}`) : '')
      + `</div>`
      + `<div class="panel wb-anchor" id="run-checks"><h2>Verification checks</h2><ul class="checks">${checks}</ul>`
      + (isStudio
        ? `<p class="caption">One check per step (<strong>NN-type</strong> in execution order): satisfied only when the step's `
        + `recorded postcondition held. Steps the flow never reached are unavailable — never silently passed. `
        + `Judged from step records — never from the driver's own claims.</p></div>`
        : r.workflow_id === 'saucedemo-stress'
        ? `<p class="caption"><strong>T1</strong> login reached the inventory (readiness timed) · <strong>T2</strong> every product shows its own image · `
        + `<strong>T3</strong> catalog in the requested order (only when sorting) · <strong>T4</strong> cart holds the added items · `
        + `<strong>T5</strong> cart holds the remainder after removal (only when removing) · <strong>T6</strong> order confirmation shown. `
        + `Judged from stage states captured mid-run — never from the driver's own claims.</p></div>`
        : r.workflow_id === 'saucedemo-order'
        ? `<p class="caption"><strong>S1</strong> login reached the inventory · <strong>S2</strong> catalog in the requested order (only when sorting) · `
        + `<strong>S3</strong> cart holds the expected items · <strong>S4</strong> checkout information accepted · <strong>S5</strong> order confirmation shown. `
        + `Judged from stage states captured mid-run — never from the driver's own claims.</p></div>`
        : r.workflow_id === 'flipkart-add-to-cart'
        ? `<p class="caption"><strong>F1</strong> search returned the picked result · <strong>F2</strong> product reached and added to cart · `
        + `<strong>F3</strong> cart holds exactly the picked item (qty 1). `
        + `Judged from stage states captured mid-run — never from the driver's own claims.</p></div>`
        : r.workflow_id === 'wikipedia-article-lookup'
        ? `<p class="caption"><strong>WI1</strong> search returned the picked article · <strong>WI2</strong> article heading matches the pick. `
        + `Judged from stage states captured mid-run — never from the driver's own claims.</p></div>`
        : r.workflow_id === 'wiktionary-word-lookup'
        ? `<p class="caption"><strong>WX1</strong> the entry exists and matches the word · <strong>WX2</strong> definitions recorded. `
        + `Judged from the entry state captured mid-run — never from the driver's own claims.</p></div>`
        : r.workflow_id === 'pypi-package-lookup'
        ? `<p class="caption"><strong>PY1</strong> the page header names the package · <strong>PY2</strong> version and summary present. `
        + `Judged from the package state captured mid-run — never from the driver's own claims.</p></div>`
        : r.workflow_id === 'bbc-headlines'
        ? `<p class="caption"><strong>BB1</strong> the requested section front was served · <strong>BB2</strong> headlines recorded. `
        + `Judged from the section state captured mid-run — never from the driver's own claims.</p></div>`
        : r.workflow_id === 'github-profile'
        ? `<p class="caption"><strong>GH1</strong> the profile handle matches the username · <strong>GH2</strong> display name present. `
        + `Judged from the profile state captured mid-run — never from the driver's own claims.</p></div>`
        : r.workflow_id === 'crates-lookup'
        ? `<p class="caption"><strong>CR1</strong> the page header names the crate · <strong>CR2</strong> version and summary present. `
        + `Judged from the crate state captured mid-run — never from the driver's own claims.</p></div>`
        : r.workflow_id === 'bbc-weather'
        ? `<p class="caption"><strong>BW1</strong> the requested city forecast was served · <strong>BW2</strong> temperatures recorded. `
        + `Judged from the forecast state captured mid-run — never from the driver's own claims.</p></div>`
        : r.workflow_id === 'github-search'
        ? `<p class="caption"><strong>GS1</strong> the results list was served with matches · <strong>GS2</strong> repo names recorded. `
        + `Judged from the search state captured mid-run — never from the driver's own claims.</p></div>`
        : r.workflow_id === 'steam-price-check'
        ? `<p class="caption"><strong>ST1</strong> search returned the picked game · <strong>ST2</strong> game page names it with a price. `
        + `Judged from stage states captured mid-run — never from the driver's own claims.</p></div>`
        : r.workflow_id === 'arxiv-search'
        ? `<p class="caption"><strong>AX1</strong> the results list was served with papers · <strong>AX2</strong> paper titles recorded. `
        + `Judged from the search state captured mid-run — never from the driver's own claims.</p></div>`
        : r.workflow_id === 'stackoverflow-search'
        ? `<p class="caption"><strong>SO1</strong> the results list was served with questions · <strong>SO2</strong> question titles recorded. `
        + `Judged from the search state captured mid-run — never from the driver's own claims.</p></div>`
        : r.workflow_id === 'amazon-price-check'
        ? `<p class="caption"><strong>AM1</strong> search returned the picked product · <strong>AM2</strong> product page names it with a price. `
        + `Judged from stage states captured mid-run — never from the driver's own claims.</p></div>`
        : `<p class="caption"><strong>P1</strong> confirmation visible · <strong>P2</strong> exactly one list entry equals the expected name · `
        + `<strong>P3</strong> exactly one list entry. Judged from an independent snapshot read after the run — never from the driver's own claims.</p></div>`)
      + `<div class="panel wb-anchor" id="run-timeline"><h2>Action timeline</h2>${waterfall(r.actions, r.duration_ms)}`
      + `<p class="caption">Each lane is one observed browser action in recorded order. Green ran clean; red errored. `
      + `Widths are measured durations where the observer timed them; lanes marked unmeasured had no timing.</p></div>`
      + `<div class="split">`
      + `<div class="panel wb-anchor" id="run-final"><h2>Final state</h2>`
      + (r.screenshot_path
        ? `<a href="${api.artifact(r.id, 'screenshot')}"><img class="evidence-shot" src="${api.artifact(r.id, 'screenshot')}" alt="Screenshot of the page after the run"></a>`
          + `<p class="caption">Screenshot captured during teardown — the page the verdict was judged from. Select it for full size.</p>`
        : `<div class="empty" style="padding:12px 0"><svg class="empty-mark" aria-hidden="true"><use href="#empty-shot"/></svg><div><p>No screenshot captured for this execution (historical benchmark runs did not take them).</p></div></div>`)
      + `</div>`
      + `<div class="panel wb-anchor" id="run-evidence"><h2>Evidence files</h2>`
      + `<ul class="checks">`
      + (r.trace_path ? `<li><span><strong>Trace</strong> — <a href="${api.artifact(r.id, 'trace')}">step-by-step event log</a></span></li>` : '')
      + (r.snapshot_path ? `<li><span><strong>Snapshot</strong> — <a href="${api.artifact(r.id, 'snapshot')}">independent page state</a></span></li>` : '')
      + (r.actions_path ? `<li><span><strong>Action log</strong> — <a href="${api.artifact(r.id, 'actions')}">observed actions</a></span></li>` : '')
      + (r.stages_available ? `<li><span><strong>Stage states</strong> — <a href="${api.artifact(r.id, 'stages')}">per-page evidence for ${r.workflow_id === 'saucedemo-stress' ? 'T1–T6' : 'S1–S5'}</a></span></li>` : '')
      + (r.steps_available ? `<li><span><strong>Step records</strong> — <a href="${api.artifact(r.id, 'steps')}">per-attempt evidence for every step</a></span></li>` : '')
      + `</ul>`
      + `<p class="caption">Started ${esc(fmtWhen(r.created_at))}${r.completed_at ? ` · finished ${esc(fmtWhen(r.completed_at))}` : ''}.</p>`
      + `</div></div>`;

    // Jump chips must not drive the hash router: scroll in place.
    el.querySelectorAll('.wb-chips a').forEach((a) => {
      a.addEventListener('click', (e) => {
        e.preventDefault();
        const target = el.querySelector(a.getAttribute('href'));
        if (target) target.scrollIntoView({ block: 'start' });
      });
    });
    if (conv) { conv.destroy(); conv = null; }
    const convEl = el.querySelector('#run-conv');
    if (convEl) conv = mountConvergence(convEl, {
      stage: journeyStage(r, live),
      outcome: r.verdict === 'verified-success' ? 'success' : r.verdict === 'verified-failure' ? 'failure' : null,
    });
    const cancel = el.querySelector('#run-cancel');
    if (cancel) cancel.addEventListener('click', async () => {
      cancel.disabled = true;
      await api.cancel(r.id);
      load();
    });
    return live ? 'live' : 'done';
  }

  el.innerHTML = `<div class="panel"><p class="dim" style="margin:0">Loading execution…</p></div>`;
  const first = await load();
  if (first === 'live' || first === 'retry') {
    timer = setInterval(async () => {
      const state = await load();
      if (state === 'done' || state === null) clearInterval(timer);
    }, 1000);
  }
  return () => { if (timer) clearInterval(timer); if (conv) conv.destroy(); };
}

function journeyPanel(r, live) {
  const stage = journeyStage(r, live);
  const note = stage >= 5
    ? 'All five tributaries arrived — the evidence below is what the verdict was judged from.'
    : 'The run is still travelling: tributaries light up as actions, evidence, and judgement land.';
  const chip = r.verdict === 'verified-success' ? ['ok', 'Verified success']
    : r.verdict === 'verified-failure' ? ['bad', 'Verified failure']
    : r.verdict === 'insufficient-evidence' ? ['', 'Insufficient evidence']
    : ['', live ? 'Running' : 'Pending'];
  return navySection('Run journey', `<div class="term-bar"><span class="term-dots" aria-hidden="true"><i></i><i></i><i></i></span>`
    + `<span class="term-title">run ${esc(r.id.slice(0, 8))} · ${esc(workflowLabel(r.workflow_id))}</span>`
    + `<span class="glass${chip[0] ? ` ${chip[0]}` : ''}" style="margin-left:auto">${esc(chip[1])}</span></div>`
    + `<h2>Journey</h2>`
    + `<div class="convergence-frame"><canvas id="run-conv" role="img" aria-label="Convergence diagram, stage ${stage} of 5: ${esc(STAGES[stage - 1])}"></canvas></div>`
    + waypoints(r, stage, live)
    + `<p class="caption">${note}</p>`, 'id="run-journey"', 'navy wb-anchor');
}
