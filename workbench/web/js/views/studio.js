/* Workflow Studio: compose, validate, run, and inspect browser workflows.
 * Definitions live server-side with versions; runs reuse the standard
 * execution pipeline, so history and analytics treat studio trials
 * like any other execution. */
import { api, queryString } from '../api.js';
import { esc, fmtMs, fmtWhen, fmtInt, fmtPct, verdictPill, statusPill, driverLabel, banner, emptyState, hero, heroField, navySection } from '../format.js';
import { C, hbars, latencySvg, coverageSvg } from './analytics.js';

const TYPE_HELP = {
  navigate: 'Open a page in the workflow environment.',
  click: 'Click an element. Non-idempotent by default: retried only with an observable effect.',
  fill: 'Type into a field. Supports {{variables}}.',
  select: 'Choose an option in a dropdown.',
  wait: 'Wait for a page condition (Chimera polls; replay reads once).',
  'verify-text': 'Assert text presence or absence.',
  'verify-count': 'Assert how many elements match.',
  capture: 'Save a screenshot as evidence.',
  'verify-state': 'Terminal step: assert final application state.',
};

const ENV_LABEL = { demo: 'Demo Task Manager (bundled, local)', saucedemo: 'SauceDemo practice store (external)' };

export async function viewStudio(el, badges, extra) {
  const id = extra && extra.param ? decodeURIComponent(extra.param) : null;
  if (id) return viewDetail(el, badges, id);
  return viewList(el);
}

async function viewList(el) {
  let rows = [];
  try {
    ({ workflows: rows } = await api.studioList());
  } catch { /* form shows the error */ }
  el.innerHTML = hero({
    kicker: 'Build · workflows',
    head: '<h1 id="page-h1">Workflow Studio</h1>',
    lede: `Compose <strong>configurable browser workflows</strong> from explicit steps — `
      + `navigate, click, fill, select, wait, verify, capture — each with its own timeout, retry policy, `
      + `and evidence contract. Runs execute in real Chromium under either driver and are judged from `
      + `recorded step evidence, never from driver claims. Supported environments: the bundled Demo Task `
      + `Manager and the SauceDemo practice store only.`,
    ctas: '<a class="btn primary" href="#st-new">Create workflow</a>',
    field: heroField('st', ['#f9a8d4', '.42', '.2'], ['#93c5fd', '.45', '.18'], [320, 300, 150, 162]),
  })
    + `<div id="st-msg"></div>`
    + `<div class="panel flush float art-top float-lift"><div class="panel-head"><h2>Workflows</h2></div><div id="st-list"></div></div>`
    + `<div class="panel"><h2>New workflow</h2><form id="st-new">`
    + `<div class="split"><div class="field"><label for="st-name">Name</label>`
    + `<input type="text" id="st-name" name="name" maxlength="120" required></div>`
    + `<div class="field"><label for="st-env">Environment</label>`
    + `<select id="st-env" name="environment">`
    + `<option value="demo">${esc(ENV_LABEL.demo)}</option>`
    + `<option value="saucedemo">${esc(ENV_LABEL.saucedemo)}</option>`
    + `</select></div></div>`
    + `<div class="field"><label for="st-desc">Description</label>`
    + `<input type="text" id="st-desc" name="description" maxlength="300"></div>`
    + `<div class="btn-row"><button class="btn primary" type="submit">Create workflow</button></div>`
    + `</form></div>`;
  const box = el.querySelector('#st-list');
  if (!rows.length) {
    box.innerHTML = `<div class="empty"><svg class="empty-mark" aria-hidden="true"><use href="#empty-layers"/></svg><div><h2>No studio workflows yet</h2>`
      + `<p>Create one above — steps, variables, and versions are saved per workflow.</p></div></div>`;
  } else {
    box.innerHTML = `<div class="table-wrap"><table class="data"><thead><tr>`
      + `<th>Workflow</th><th>Environment</th><th>Version</th><th>Updated</th></tr></thead><tbody>`
      + rows.map((w) => `<tr><td><a href="#/studio/${encodeURIComponent(w.id)}">${esc(w.name)}</a></td>`
        + `<td>${esc(ENV_LABEL[w.environment] || w.environment)}</td>`
        + `<td class="mono">${w.current_version ? `v${w.current_version}` : 'no saved version'}</td>`
        + `<td class="mono">${esc(fmtWhen(w.updated_at))}</td></tr>`).join('')
      + `</tbody></table></div>`;
  }
  el.querySelector('#st-new').addEventListener('submit', async (e) => {
    e.preventDefault();
    const msg = el.querySelector('#st-msg');
    const form = e.target;
    try {
      const { id } = await api.studioCreate({
        name: form.name.value, environment: form.environment.value,
        description: form.description.value,
      });
      window.location.hash = `#/studio/${encodeURIComponent(id)}`;
    } catch (err) {
      msg.innerHTML = banner('bad', `<strong>Could not create:</strong> ${esc(err.message)}`);
    }
  });
}

function blankStep(type) {
  const step = { key: `s${Date.now().toString(36)}`, type, label: '', timeout_ms: 5000, max_attempts: 3 };
  if (type === 'navigate') step.url = '';
  if (['click', 'fill', 'select'].includes(type)) step.selector = '';
  if (['fill', 'select'].includes(type)) step.value = '';
  if (type === 'wait') { step.condition = 'visible'; step.selector = ''; step.text = ''; }
  if (type === 'verify-text') { step.text = ''; step.expect = 'present'; step.selector = ''; }
  if (type === 'verify-count') { step.selector = ''; step.op = 'eq'; step.count = 1; }
  if (type === 'verify-state') step.assertions = [{ kind: 'visible', selector: '' }];
  return step;
}

function stepSummary(step) {
  const bits = [];
  if (step.url) bits.push(step.url);
  if (step.selector) bits.push(step.selector);
  if (step.value !== undefined && step.value !== '') bits.push(`= ${step.value}`);
  if (step.text) bits.push(`“${step.text}”`);
  if (step.type === 'verify-count') bits.push(`${step.op || 'eq'} ${step.count ?? '?'}`);
  if (step.condition) bits.push(step.condition);
  if (step.type === 'verify-state') bits.push(`${(step.assertions || []).length} assertions`);
  bits.push(`${step.timeout_ms || 5000}ms`, `×${step.max_attempts || 3}`);
  if (step.idempotent === false) bits.push('non-idempotent');
  if (step.effect) bits.push('effect-gated');
  return bits.join(' · ');
}

async function viewDetail(el, badges, id) {
  const S = {
    id, record: null, meta: null,
    doc: { steps: [], variables: [] },
    editing: -1, errors: [], versionSel: null, dirty: false,
  };
  try {
    const [got, meta] = await Promise.all([api.studioGet(id), api.studioMeta()]);
    S.record = got.workflow;
    S.meta = meta;
  } catch (err) {
    el.innerHTML = banner('bad', `<strong>Workflow unavailable:</strong> ${esc(err.message)}`);
    return;
  }
  S.versionSel = S.record.version;
  if (S.record.definition) {
    S.doc = {
      steps: structuredClone(S.record.definition.steps || []),
      variables: structuredClone(S.record.definition.variables || []),
    };
  }

  function params(extra) {
    return queryString({ workflow_id: `studio:${id}`, ...(extra || {}) });
  }

  function render() {
    const r = S.record;
    const vlist = (r.versions || []).map((v) =>
      `<option value="${v}"${String(v) === String(S.versionSel) ? ' selected' : ''}>v${v}</option>`).join('');
    const nSteps = S.doc.steps.length;
    el.innerHTML = `<div class="section-split" id="st-detail"><h2>One workflow, ${nSteps} judged step${nSteps === 1 ? '' : 's'}.</h2>`
      + `<p>Definitions live server-side with versions; runs reuse the standard execution pipeline, so history and analytics treat studio trials like any other execution.</p></div>`
      + `<p><a href="#/studio">← All studio workflows</a></p>`
      + `<div class="runhead"><div><h1>${esc(r.name)}</h1><span class="id">${esc(r.id)}</span></div></div>`
      + `<div style="margin:10px 0 18px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}>`
      + `<span class="pill">${esc(ENV_LABEL[r.environment] || r.environment)}</span>`
      + `<span class="dim">${esc(r.description || 'No description')}</span></div>`
      + `<div id="st-msg"></div>`
      + `<div class="panel"><h2>1 · Steps</h2><ol class="st-steps" id="st-steps"></ol>`
      + `<h3>Add a step</h3><div class="st-palette" id="st-palette">`
      + S.meta.step_types.map((t) =>
        `<button class="btn" data-add="${esc(t)}" title="${esc(TYPE_HELP[t] || '')}">+ ${esc(t)}</button>`).join('')
      + `</div></div>`
      + `<div class="panel"><h2>2 · Variables</h2><div id="st-vars"></div>`
      + `<p class="caption">Reference as <code>{{name}}</code> in urls, selectors, values, and texts. `
      + `Secrets accept no saved default — supply them at run time; <code>***</code> is recorded instead of the value, everywhere.</p></div>`
      + `<div class="panel"><h2>3 · Validation</h2><div id="st-validation"></div>`
      + `<div class="btn-row" style="margin-top:8px"><button class="btn primary" id="st-save">Save as new version</button>`
      + `<button class="btn" id="st-clone">Clone workflow</button>`
      + `<span class="dim">viewing <select id="st-version" aria-label="Version">${vlist || '<option value="">no versions</option>'}</select></span></div></div>`
      + navySection('Run workflow', `<h2>4 · Run</h2><div id="st-run"></div>`)
      + `<div id="st-figures"><p class="dim">Computing figures…</p></div>`
      + `<div class="panel flush"><div class="panel-head"><h2>Execution history</h2></div><div id="st-history"></div></div>`;
    renderSteps();
    renderVars();
    renderValidation();
    renderRun();
    loadFigures();
    loadHistory();
    wire();
  }

  function renderSteps() {
    const box = el.querySelector('#st-steps');
    if (!S.doc.steps.length) {
      box.innerHTML = `<div class="empty"><svg class="empty-mark" aria-hidden="true"><use href="#empty-layers"/></svg><div><h2>No steps yet</h2><p>Add the first step below — a workflow usually opens with a navigate step.</p></div></div>`;
      return;
    }
    box.innerHTML = S.doc.steps.map((s, i) => {
      const open = S.editing === i;
      return `<li class="st-step${open ? ' open' : ''}"><div class="st-num">${i + 1}</div>`
        + `<div class="st-card"><div class="st-card-top">`
        + `<span class="st-type t-${esc(s.type)}">${esc(s.type)}</span>`
        + `<span class="st-label">${esc(s.label || '(no label)')}</span>`
        + `<span class="st-ops">`
        + `<button class="btn" data-up="${i}"${i === 0 ? ' disabled' : ''} aria-label="Move up">↑</button>`
        + `<button class="btn" data-down="${i}"${i === S.doc.steps.length - 1 ? ' disabled' : ''} aria-label="Move down">↓</button>`
        + `<button class="btn" data-edit="${i}">${open ? 'Done' : 'Edit'}</button>`
        + `<button class="btn danger" data-del="${i}" aria-label="Delete step">✕</button>`
        + `</span></div>`
        + `<div class="st-sum">${esc(stepSummary(s))}</div>`
        + (open ? stepForm(s, i) : '')
        + `</div></li>`;
    }).join('');
    box.querySelectorAll('[data-up]').forEach((b) => b.addEventListener('click', () => moveStep(+b.dataset.up, -1)));
    box.querySelectorAll('[data-down]').forEach((b) => b.addEventListener('click', () => moveStep(+b.dataset.down, 1)));
    box.querySelectorAll('[data-del]').forEach((b) => b.addEventListener('click', () => {
      S.doc.steps.splice(+b.dataset.del, 1);
      S.editing = -1;
      changed();
    }));
    box.querySelectorAll('[data-edit]').forEach((b) => b.addEventListener('click', () => {
      const i = +b.dataset.edit;
      if (S.editing === i) { readStepForm(i); S.editing = -1; }
      else { if (S.editing >= 0) readStepForm(S.editing); S.editing = i; }
      changed(false);
    }));
    box.querySelectorAll('[data-assert-add]').forEach((b) => b.addEventListener('click', () => {
      const i = +b.dataset.assertAdd;
      readStepForm(i, true);
      S.doc.steps[i].assertions.push({ kind: 'visible', selector: '' });
      changed(false);
    }));
    box.querySelectorAll('[data-assert-del]').forEach((b) => b.addEventListener('click', () => {
      const [i, j] = b.dataset.assertDel.split(':').map(Number);
      readStepForm(i, true);
      S.doc.steps[i].assertions.splice(j, 1);
      changed(false);
    }));
  }

  function field(name, label, inner, wide) {
    return `<div class="field${wide ? ' wide' : ''}"><label>${esc(label)}${inner}</label></div>`;
  }

  function stepForm(s, i) {
    const t = s.type;
    const num = (name, label, value, min, max) =>
      field(name, label, `<input type="number" data-f="${name}" value="${esc(String(value ?? ''))}" min="${min}" max="${max}">`);
    const txt = (name, label, value, wide, ph) =>
      field(name, label, `<input type="text" data-f="${name}" value="${esc(value || '')}" spellcheck="false"${ph ? ` placeholder="${esc(ph)}"` : ''}>`, wide);
    const sel = (name, label, value, options) =>
      field(name, label, `<select data-f="${name}">` + options.map(([v, l]) =>
        `<option value="${esc(v)}"${String(value) === String(v) ? ' selected' : ''}>${esc(l)}</option>`).join('') + `</select>`);
    const chk = (name, label, value) =>
      field(name, label, `<input type="checkbox" data-f="${name}"${value ? ' checked' : ''}>`);
    let h = `<div class="st-form" data-form="${i}">`
      + txt('label', 'Label', s.label, true, 'Human-readable purpose')
      + txt('key', 'Step key', s.key, false, 'unique id');
    if (t === 'navigate') h += txt('url', 'URL (demo/contact, /path, or full URL)', s.url, true);
    if (['click', 'fill', 'select', 'verify-count'].includes(t)) h += txt('selector', 'Selector', s.selector, true);
    if (['fill', 'select'].includes(t)) h += txt('value', 'Value ({{variables}} allowed)', s.value, true);
    if (t === 'wait') {
      h += sel('condition', 'Condition', s.condition || 'visible',
        [['visible', 'Element visible'], ['hidden', 'Element hidden'], ['text-present', 'Text present']]);
      h += txt('selector', 'Selector', s.selector, false);
      h += txt('text', 'Text', s.text, false);
    }
    if (t === 'verify-text') {
      h += txt('text', 'Expected text', s.text, true);
      h += sel('expect', 'Expect', s.expect || 'present', [['present', 'Present'], ['absent', 'Absent']]);
      h += txt('selector', 'Within selector (blank = page)', s.selector, false);
    }
    if (t === 'verify-count') {
      h += sel('op', 'Comparison', s.op || 'eq', [['eq', '='], ['gte', '≥'], ['lte', '≤']]);
      h += num('count', 'Count', s.count ?? 1, 0, 100000);
    }
    if (t === 'verify-state') {
      h += `<div class="field wide"><span class="lbl">Assertions</span><div data-asserts>`
        + (s.assertions || []).map((a, j) => assertionRow(a, j)).join('') + `</div>`
        + `<div class="btn-row" style="margin-top:6px"><button class="btn" data-assert-add="${i}">Add assertion</button></div></div>`;
    }
    if (['click', 'fill', 'select'].includes(t)) {
      const idemDefault = t !== 'click';
      h += chk('idempotent', `Safe to repeat (default ${idemDefault ? 'yes' : 'no'})`,
        s.idempotent === undefined ? idemDefault : !!s.idempotent);
      const e = s.effect || {};
      h += sel('effect.kind', 'Effect check (for safe retry)', e.kind || '',
        [['', 'None'], ['visible', 'Visible'], ['hidden', 'Hidden'],
         ['text-present', 'Text present'], ['text-absent', 'Text absent'], ['count', 'Count']]);
      h += txt('effect.selector', 'Effect selector', e.selector || '', false);
      h += txt('effect.text', 'Effect text', e.text || '', false);
      h += num('effect.count', 'Effect count', e.count ?? '', 0, 100000);
      const p = s.precondition || {};
      h += sel('precondition.kind', 'Precondition', p.kind || '',
        [['', 'None'], ['visible', 'Visible'], ['hidden', 'Hidden']]);
      h += txt('precondition.selector', 'Precondition selector', p.selector || '', true);
    }
    h += num('timeout_ms', 'Timeout (ms)', s.timeout_ms ?? 5000,
      S.meta.bounds.timeout_ms[0], S.meta.bounds.timeout_ms[1]);
    h += num('max_attempts', 'Max attempts (Chimera)', s.max_attempts ?? 3,
      S.meta.bounds.max_attempts[0], S.meta.bounds.max_attempts[1]);
    return h + `<p class="caption wide">Execution contract: precondition → action → postcondition/effect, `
      + `with evidence on every attempt. Non-idempotent steps without an observable effect run once — `
      + `retries are refused, never repeated blindly.</p></div>`;
  }

  function assertionRow(a, j) {
    return `<div class="cond-row" data-assert="${j}">`
      + `<div class="field"><label>Kind<select data-a="kind">`
      + ['visible', 'hidden', 'text-present', 'text-absent', 'count'].map((k) =>
        `<option value="${k}"${a.kind === k ? ' selected' : ''}>${k}</option>`).join('')
      + `</select></label></div>`
      + `<div class="field grow"><label>Selector<input type="text" data-a="selector" value="${esc(a.selector || '')}" spellcheck="false"></label></div>`
      + `<div class="field grow"><label>Text<input type="text" data-a="text" value="${esc(a.text || '')}" spellcheck="false"></label></div>`
      + `<div class="field"><label>Count<input type="number" data-a="count" value="${esc(String(a.count ?? ''))}" min="0"></label></div>`
      + `<button class="btn danger" data-assert-del="${S.editing}:${j}" aria-label="Remove assertion">✕</button></div>`;
  }

  function readStepForm(i, keep) {
    const form = el.querySelector(`[data-form="${i}"]`);
    if (!form) return;
    const s = S.doc.steps[i];
    const val = (name) => {
      const input = form.querySelector(`[data-f="${name}"]`);
      if (!input) return undefined;
      if (input.type === 'checkbox') return input.checked;
      if (input.type === 'number') return input.value === '' ? undefined : +input.value;
      return input.value;
    };
    for (const name of ['label', 'key', 'url', 'selector', 'value', 'text', 'condition', 'expect', 'op']) {
      const v = val(name);
      if (v !== undefined) s[name] = v;
    }
    for (const name of ['count', 'timeout_ms', 'max_attempts']) {
      const v = val(name);
      if (v !== undefined) s[name] = v;
    }
    const idem = val('idempotent');
    if (idem !== undefined) {
      const def = s.type !== 'click';
      if (idem === def) delete s.idempotent;
      else s.idempotent = idem;
    }
    const ekind = val('effect.kind');
    if (ekind !== undefined) {
      if (!ekind) delete s.effect;
      else {
        s.effect = { kind: ekind };
        const es = val('effect.selector'), et = val('effect.text'), ec = val('effect.count');
        if (es) s.effect.selector = es;
        if (et) s.effect.text = et;
        if (ec !== undefined) s.effect.count = ec;
      }
    }
    const pkind = val('precondition.kind');
    if (pkind !== undefined) {
      if (!pkind) delete s.precondition;
      else s.precondition = { kind: pkind, selector: val('precondition.selector') || '' };
    }
    const rows = form.querySelectorAll('[data-assert]');
    if (rows.length || (s.assertions && s.type === 'verify-state')) {
      s.assertions = [...rows].map((row) => {
        const get = (n) => row.querySelector(`[data-a="${n}"]`).value;
        const a = { kind: get('kind') };
        if (get('selector')) a.selector = get('selector');
        if (get('text')) a.text = get('text');
        if (get('count') !== '') a.count = +get('count');
        return a;
      });
    }
    if (!keep) S.dirty = true;
  }

  function moveStep(i, dir) {
    if (S.editing >= 0) readStepForm(S.editing);
    S.editing = -1;
    const j = i + dir;
    const [s] = S.doc.steps.splice(i, 1);
    S.doc.steps.splice(j, 0, s);
    changed();
  }

  function renderVars() {
    const box = el.querySelector('#st-vars');
    box.innerHTML = (S.doc.variables.length ? '' : `<p class="dim">No variables — add one if steps need user-supplied data.</p>`)
      + S.doc.variables.map((v, i) => `<div class="cond-row" data-var="${i}">`
        + `<div class="field"><label>Name<input type="text" data-v="name" value="${esc(v.name || '')}" spellcheck="false"></label></div>`
        + `<div class="field"><label>Label<input type="text" data-v="label" value="${esc(v.label || '')}" spellcheck="false"></label></div>`
        + `<div class="field grow"><label>Default<input type="text" data-v="default" value="${esc(v.default || '')}" spellcheck="false"></label></div>`
        + `<div class="field"><label>Secret<input type="checkbox" data-v="secret"${v.secret ? ' checked' : ''}></label></div>`
        + `<button class="btn danger" data-var-del="${i}" aria-label="Remove variable">✕</button></div>`).join('')
      + `<div class="btn-row"><button class="btn" id="st-var-add">Add variable</button></div>`;
    box.querySelector('#st-var-add').addEventListener('click', () => {
      readVars();
      S.doc.variables.push({ name: '', label: '', secret: false, default: '' });
      changed(false);
    });
    box.querySelectorAll('[data-var-del]').forEach((b) => b.addEventListener('click', () => {
      readVars();
      S.doc.variables.splice(+b.dataset.varDel, 1);
      changed();
    }));
    box.querySelectorAll('input').forEach((input) => input.addEventListener('change', () => {
      readVars();
      changed(false);
    }));
  }

  function readVars() {
    el.querySelectorAll('[data-var]').forEach((row) => {
      const i = +row.dataset.var;
      const get = (n) => row.querySelector(`[data-v="${n}"]`);
      S.doc.variables[i] = {
        name: get('name').value, label: get('label').value,
        secret: get('secret').checked, default: get('default').value,
      };
    });
    S.dirty = true;
  }

  let validateTimer = null;
  function changed(validate = true) {
    S.dirty = true;
    renderSteps();
    renderVars();
    if (!validate) return;
    clearTimeout(validateTimer);
    validateTimer = setTimeout(runValidation, 350);
  }

  async function runValidation() {
    const box = el.querySelector('#st-validation');
    if (S.editing >= 0) readStepForm(S.editing, true);
    readVarsSilent();
    try {
      const { errors } = await api.studioValidate(
        { steps: S.doc.steps, variables: S.doc.variables }, S.record.environment);
      S.errors = errors || [];
    } catch (err) {
      box.innerHTML = banner('bad', `<strong>Validation failed:</strong> ${esc(err.message)}`);
      return;
    }
    renderValidation();
  }

  function readVarsSilent() {
    el.querySelectorAll('[data-var]').forEach((row) => {
      const i = +row.dataset.var;
      const get = (n) => row.querySelector(`[data-v="${n}"]`);
      if (S.doc.variables[i]) {
        S.doc.variables[i].name = get('name').value;
        S.doc.variables[i].label = get('label').value;
        S.doc.variables[i].secret = get('secret').checked;
        S.doc.variables[i].default = get('default').value;
      }
    });
  }

  function renderValidation() {
    const box = el.querySelector('#st-validation');
    if (!box) return;
    if (!S.errors.length) {
      box.innerHTML = `<p class="st-ok" style="margin:0">✓ Definition valid — ${S.doc.steps.length} steps, `
        + `${S.doc.variables.length} variables. Saving creates v${(S.record.current_version || 0) + 1}.</p>`;
      return;
    }
    box.innerHTML = `<ul class="st-errs">` + S.errors.map((e) =>
      `<li><code>${esc(e.code)}</code> ${esc(e.step ? `${e.step}: ` : '')}${esc(e.message)}</li>`).join('')
      + `</ul><p class="caption">Saving is blocked until every error is resolved.</p>`;
  }

  function renderRun() {
    const box = el.querySelector('#st-run');
    const vars = S.doc.variables || [];
    box.innerHTML = (S.record.current_version
      ? `<div class="split">`
        + vars.map((v) => `<div class="field"><label>${esc(v.label || v.name)}${v.secret ? ' (secret)' : ''}`
          + `<input type="${v.secret ? 'password' : 'text'}" data-runvar="${esc(v.name)}" `
          + `value="${esc(v.secret ? '' : (v.default || ''))}" autocomplete="off" spellcheck="false"></label></div>`).join('')
        + `<div class="field"><label>Driver<select id="st-driver">`
        + `<option value="chimera">Chimera (retries + recovery)</option>`
        + `<option value="baseline-a">Baseline A (single attempt)</option>`
        + `</select></label></div></div>`
        + `<div class="btn-row"><button class="btn primary" id="st-execute">Execute v${esc(String(S.versionSel || S.record.current_version))} in a real browser</button>`
        + `<span class="dim" id="st-run-status"></span></div>`
        + `<div id="st-run-result" style="margin-top:8px"></div>`
      : `<p class="dim">Save a valid version before executing.</p>`);
    const btn = box.querySelector('#st-execute');
    if (btn) btn.addEventListener('click', executeRun);
  }

  async function executeRun() {
    const status = el.querySelector('#st-run-status');
    const out = el.querySelector('#st-run-result');
    const btn = el.querySelector('#st-execute');
    const variables = {};
    el.querySelectorAll('[data-runvar]').forEach((input) => {
      variables[input.dataset.runvar] = input.value;
    });
    const driver = el.querySelector('#st-driver').value;
    btn.disabled = true;
    status.textContent = 'starting…';
    try {
      const { id: execId } = await api.start({
        workflow_id: `studio:${S.id}`, driver,
        params: { variables, version: S.versionSel ? +S.versionSel : undefined },
      });
      status.innerHTML = `running — <a href="#/run/${encodeURIComponent(execId)}">watch live</a>`;
      const rec = await pollRun(execId);
      out.innerHTML = `<p style="margin:0">${verdictPill(rec.verdict)} ${statusPill(rec.status)} `
        + `<a href="#/run/${encodeURIComponent(execId)}">open execution</a> `
        + `<span class="dim">${esc(fmtMs(rec.duration_ms))}${rec.error ? ` · ${esc(String(rec.error).slice(0, 120))}` : ''}</span></p>`;
      loadFigures();
      loadHistory();
    } catch (err) {
      out.innerHTML = banner('bad', `<strong>Execution failed to start:</strong> ${esc(err.message)}`);
    } finally {
      btn.disabled = false;
      status.textContent = '';
    }
  }

  async function pollRun(execId) {
    for (;;) {
      const { execution } = await api.get(execId);
      if (execution.status !== 'queued' && execution.status !== 'running') return execution;
      await new Promise((r) => setTimeout(r, 1000));
    }
  }

  async function loadFigures() {
    const box = el.querySelector('#st-figures');
    if (!box) return;
    try {
      const [ov, lat, dr, vc, fail] = await Promise.all([
        api.analytics('overview', params()),
        api.analytics('latency', params()),
        api.analytics('drivers', params()),
        api.analytics('verification', params()),
        api.analytics('failures', params()),
      ]);
      if (!ov.total) {
        box.innerHTML = `<div class="panel"><h2>5 · Results</h2>`
          + `<p class="dim" style="margin:0">No executions yet — run the workflow to populate success rates, latency, and coverage.</p></div>`;
        return;
      }
      const failLine = (fail.by_category || []).map((c) => `${esc(c.name)} ${fmtInt(c.n)}`).join(' · ') || 'no failures';
      box.innerHTML = `<div class="panel"><h2>5 · Results</h2>`
        + `<div class="kv">`
        + `<div class="cell"><div class="k">Executions</div><div class="v mono">${fmtInt(ov.total)}</div></div>`
        + `<div class="cell"><div class="k">Verified success rate</div><div class="v mono">${fmtPct(ov.verified_success_rate)} <span class="dim">n=${fmtInt(ov.verified_denominator)}</span></div></div>`
        + `<div class="cell"><div class="k">Duration p50 / p95</div><div class="v mono">${fmtMs(ov.durations.p50)} / ${fmtMs(ov.durations.p95)}</div></div>`
        + `</div>`
        + `<h3>Driver duel</h3><figure class="viz">${hbars(
          dr.drivers.map((d) => ({ label: driverLabel(d.driver), rate: d.success_rate, d })),
          'rate', 'Driver success rates', () => C.cyan,
          (r) => `${fmtPct(r.rate)} · n=${r.d.verified} verified · p50 ${fmtMs(r.d.p50)}`)}</figure>`
        + `<h3>Latency distribution</h3><figure class="viz">${latencySvg(lat)}</figure>`
        + `<h3>Verification coverage per step</h3><figure class="viz">${coverageSvg(vc.checks || [])}</figure>`
        + `<p class="caption">Failures by category: <strong>${failLine}</strong>. `
        + `Each bar segments per-step satisfied / failed / unavailable counts with exact denominators.</p></div>`;
    } catch {
      box.innerHTML = '';
    }
  }

  async function loadHistory() {
    const box = el.querySelector('#st-history');
    if (!box) return;
    try {
      const page = await api.list(queryString({
        workflow_id: `studio:${S.id}`, page_size: 20, sort: '-created_at',
      }));
      if (!page.rows.length) {
        box.innerHTML = `<div class="empty"><svg class="empty-mark" aria-hidden="true"><use href="#empty-runs"/></svg><div><h2>No executions yet</h2></div></div>`;
        return;
      }
      box.innerHTML = `<div class="table-wrap"><table class="data"><thead><tr>`
        + `<th>Run</th><th>Driver</th><th>Condition</th><th>Status</th><th>Verdict</th><th>Duration</th></tr></thead><tbody>`
        + page.rows.map((r) => `<tr><td><a href="#/run/${encodeURIComponent(r.id)}">${esc(r.id.slice(0, 8))}</a></td>`
          + `<td>${esc(driverLabel(r.driver))}</td>`
          + `<td class="mono">${esc(r.scenario_id || '—')}</td>`
          + `<td>${statusPill(r.status)}</td><td>${verdictPill(r.verdict)}</td>`
          + `<td class="mono">${esc(fmtMs(r.duration_ms))}</td></tr>`).join('')
        + `</tbody></table></div>`;
    } catch {
      box.innerHTML = `<div class="empty"><svg class="empty-mark" aria-hidden="true"><use href="#empty-server"/></svg><div><h2>History unavailable</h2></div></div>`;
    }
  }

  function wire() {
    el.querySelector('#st-palette').addEventListener('click', (e) => {
      const btn = e.target.closest('[data-add]');
      if (!btn) return;
      if (S.editing >= 0) readStepForm(S.editing);
      S.doc.steps.push(blankStep(btn.dataset.add));
      S.editing = S.doc.steps.length - 1;
      changed();
    });
    el.querySelector('#st-save').addEventListener('click', async () => {
      const msg = el.querySelector('#st-msg');
      if (S.editing >= 0) { readStepForm(S.editing); S.editing = -1; }
      readVarsSilent();
      renderSteps();
      renderVars();
      await runValidation();
      if (S.errors.length) {
        msg.innerHTML = banner('bad', `<strong>Cannot save:</strong> resolve the ${S.errors.length} validation error(s) first.`);
        return;
      }
      try {
        const { version } = await api.studioSave(S.id, {
          steps: S.doc.steps, variables: S.doc.variables,
        });
        const got = await api.studioGet(S.id);
        S.record = got.workflow;
        S.versionSel = version;
        S.dirty = false;
        msg.innerHTML = banner('info', `<strong>Saved as v${version}.</strong> Earlier versions stay pinned to their runs.`);
        render();
      } catch (err) {
        const errs = (err.data && err.data.errors) || [];
        S.errors = errs;
        renderValidation();
        msg.innerHTML = banner('bad', `<strong>Save refused:</strong> ${esc(err.message)}`);
      }
    });
    el.querySelector('#st-clone').addEventListener('click', async () => {
      const msg = el.querySelector('#st-msg');
      try {
        const { id: nid } = await api.studioClone(S.id);
        window.location.hash = `#/studio/${encodeURIComponent(nid)}`;
      } catch (err) {
        msg.innerHTML = banner('bad', `<strong>Clone failed:</strong> ${esc(err.message)}`);
      }
    });
    el.querySelector('#st-version').addEventListener('change', async (e) => {
      S.versionSel = e.target.value || null;
      if (!S.versionSel) return;
      const got = await api.studioGet(S.id, S.versionSel);
      S.record = await (await api.studioGet(S.id)).workflow;
      const pinned = got.workflow;
      if (pinned.definition) {
        S.doc = {
          steps: structuredClone(pinned.definition.steps || []),
          variables: structuredClone(pinned.definition.variables || []),
        };
        S.editing = -1;
        render();
      }
    });
  }

  render();
  runValidation();
}
