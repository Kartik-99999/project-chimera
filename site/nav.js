/* Chimera multipage shared UI — header/drawer/dropdowns, motion, portal,
 * weave inspector, matrix tooltip, dossier. No data fetching here; live
 * figure tokens arrive via setFigs() from figures.js. Every initializer
 * guards its DOM hosts so pages include only what they use.
 */

const FIGS = { EPISODES: null, EVALEPS: null, DEVEPS: null, CONDS: null, FS: null, MINI: null };
export function setFigs(vals) {
  Object.assign(FIGS, vals);
}
const reducedMotion = () => window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* ---------- motion ---------- */
export function initMotion() {
  const bands = [...document.querySelectorAll('.band')];
  bands.forEach((e) => e.classList.add('reveal'));
  const stags = [...document.querySelectorAll('.pipeline, .coverage, .limits-grid, .terminal-grid, .teaser-grid, .wf-grid, .spec-grid')];
  stags.forEach((e) => e.classList.add('stag'));
  if (reducedMotion()) { [...bands, ...stags].forEach((e) => e.classList.add('in')); return; }
  const io = new IntersectionObserver((entries) => entries.forEach((x) => {
    if (x.isIntersecting) { x.target.classList.add('in'); io.unobserve(x.target); }
  }), { threshold: 0.12 });
  [...bands, ...stags].forEach((e) => io.observe(e));
  const jo = new IntersectionObserver((entries) => entries.forEach((x) => {
    if (x.isIntersecting) { x.target.classList.add('drawn'); jo.unobserve(x.target); }
  }), { threshold: 0.3 });
  document.querySelectorAll('.journey').forEach((j) => jo.observe(j));
}

/* ---------- scroll hints ---------- */
export function initScrollHints() {
  const sync = (el) => {
    const hint = el.querySelector(':scope > .scroll-hint');
    if (!hint) return;
    const left = Math.abs(el.scrollLeft);
    hint.classList.toggle('is-end', el.scrollWidth - el.clientWidth - left <= 4);
  };
  const scrollers = [...document.querySelectorAll('.table-wrap, #latency-chart')];
  scrollers.forEach((el) => {
    el.addEventListener('scroll', () => sync(el), { passive: true });
    sync(el);
  });
  window.addEventListener('resize', () => scrollers.forEach(sync));
}

/* ---------- proof portal ---------- */
const PORTAL_STAGES = [
  { tag: '01 · ACTION', title: 'From action,<br>to proof', sub: 'Stage 01 · Action — one fixed script, explicit bounds',
    narrative: 'One create-a-project flow enters the weave: navigate, fill, click, wait and retry, verify, report. The only task Chimera performs.',
    snippet: 'task: "create-a-project" · target: local demo page', scales: [1.62, 1.26, 0.95, 0.68] },
  { tag: '02 · EXECUTION', title: 'Defined steps,<br>in motion', sub: 'Stage 02 · Execution — every run counts',
    narrative: '{EPISODES} measured episodes: {EVALEPS} held-out plus {DEVEPS} development, Chimera and replay through identical cells.',
    snippet: 'episodes: {EPISODES} · held-out {EVALEPS} + dev {DEVEPS}', scales: [1.68, 1.32, 1.00, 0.72] },
  { tag: '03 · OBSERVATION', title: 'Every state,<br>observed', sub: 'Stage 03 · Observation — harness snapshots, never agent claims',
    narrative: '{CONDS} fault conditions watched: normal, slow page, disabled input, slow plus disabled.',
    snippet: 'conditions: normal · slow · disabled · slow+disabled', scales: [1.56, 1.22, 0.91, 0.64] },
  { tag: '04 · VERIFICATION', title: 'Verified,<br>independently', sub: 'Stage 04 · Verification — Chimera never grades itself',
    narrative: 'A separate checker grades P1–P3 from harness snapshots: {FS} false successes of n = {EPISODES}.',
    snippet: 'P1 confirmation · P2 exact name · P3 single entry', scales: [1.64, 1.28, 0.98, 0.70] },
  { tag: '05 · EVIDENCE', title: 'Evidence,<br>you can inspect', sub: 'Stage 05 · Evidence — traces, verdicts, reports',
    narrative: 'Every episode sealed: trace artifacts, independent verification, seed 20261030, human mini-audit {MINI}.',
    snippet: 'seed 20261030 · 2 drivers · identical cells', scales: [1.60, 1.25, 0.94, 0.66] },
];
const PORTAL_YSCALES = [1.28, 1.12, 0.96, 0.80];
let portalIdx = 0;
function portalTok(s) {
  return String(s).replace(/\{(\w+)\}/g, (_, k) => (FIGS[k] == null ? '…' : FIGS[k]));
}
export function paintPortal(i) {
  const head = document.getElementById('portal-heading');
  if (!head) return;
  const idx = i == null ? portalIdx : ((i % PORTAL_STAGES.length) + PORTAL_STAGES.length) % PORTAL_STAGES.length;
  const st = PORTAL_STAGES[idx];
  portalIdx = idx;
  head.innerHTML = st.title;
  const sub = document.getElementById('portalCenterSubtitle');
  if (sub) sub.textContent = st.sub;
  const tag = document.getElementById('portalStepTag');
  if (tag) tag.textContent = st.tag;
  const ind = document.getElementById('portalStageIndicator');
  if (ind) ind.textContent = `Threshold 0${portalIdx + 1} / 05`;
  const nar = document.getElementById('portalStageNarrative');
  if (nar) nar.textContent = portalTok(st.narrative);
  const snip = document.getElementById('portalCodeSnippet');
  if (snip) snip.textContent = portalTok(st.snippet);
  for (let g = 1; g <= 4; g += 1) {
    const el = document.getElementById(`portalGroup${g}`);
    if (el) el.setAttribute('transform', `translate(720, 410) scale(${st.scales[g - 1]}, ${PORTAL_YSCALES[g - 1]})`);
  }
  document.querySelectorAll('.portal-tabs [role="tab"]').forEach((t, k) => {
    const on = k === portalIdx;
    t.setAttribute('aria-selected', String(on));
    t.tabIndex = on ? 0 : -1;
  });
}
export function initPortal() {
  const tabs = [...document.querySelectorAll('.portal-tabs [role="tab"]')];
  if (!tabs.length) return;
  tabs.forEach((tab, i) => {
    tab.addEventListener('click', () => paintPortal(i));
    tab.addEventListener('keydown', (e) => {
      let next = i;
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') next = (i + 1) % tabs.length;
      else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') next = (i - 1 + tabs.length) % tabs.length;
      else if (e.key === 'Home') next = 0;
      else if (e.key === 'End') next = tabs.length - 1;
      else return;
      e.preventDefault();
      paintPortal(next);
      tabs[next].focus();
    });
  });
  paintPortal(0);
}

/* ---------- computational-weave stage inspector (home hero) ---------- */
const WEAVE_STAGES = [
  'STAGE 01/05 · One create-a-project flow enters the weave — the only thing Chimera is asked to do.',
  'STAGE 02/05 · 520 measured episodes: 360 held-out, 160 development. Every run counts.',
  'STAGE 03/05 · 4 fault conditions watched: normal, slow, disabled, slow plus disabled.',
  'STAGE 04/05 · 0 false successes of n = 520. The checker grades; Chimera never grades itself.',
  'STAGE 05/05 · 2 drivers on identical cells, seed 20261030. Deterministic and sealed.',
];
const WEAVE_DURATION_MS = 4800;
export function initWeave() {
  const hero = document.getElementById('top');
  const tabs = [...document.querySelectorAll('.hero-stage-tabs [role="tab"]')];
  const nodes = [...document.querySelectorAll('.weave-node')];
  const detail = document.getElementById('stage-note');
  const artwork = document.getElementById('weaveArtwork');
  const playBtn = document.getElementById('playPauseBtn');
  const playIcon = document.getElementById('playPauseIcon');
  const playLabel = document.getElementById('playPauseLabel');
  if (!hero || !tabs.length) return;
  let active = 0;
  let playing = !reducedMotion();
  let lastSwitch = performance.now();
  let loopRunning = false;
  const select = (idx, user) => {
    active = ((idx % tabs.length) + tabs.length) % tabs.length;
    if (user) lastSwitch = performance.now();
    tabs.forEach((t, k) => {
      const on = k === active;
      t.setAttribute('aria-selected', String(on));
      t.tabIndex = on ? 0 : -1;
    });
    nodes.forEach((n, k) => n.classList.toggle('is-active', k === active));
    if (artwork) artwork.dataset.stage = String(active);
    if (detail) detail.textContent = WEAVE_STAGES[active];
    paintPortal(active);
  };
  const paintPlay = () => {
    if (!playBtn) return;
    playBtn.setAttribute('aria-label', playing ? 'Pause stage sequence' : 'Play stage sequence');
    if (playIcon) playIcon.textContent = playing ? 'Ⅱ' : '▶';
    if (playLabel) playLabel.textContent = playing ? 'Pause sequence' : 'Play sequence';
  };
  const tick = (now) => {
    if (!playing) { loopRunning = false; return; }
    if (now - lastSwitch > WEAVE_DURATION_MS) { select(active + 1, false); lastSwitch = now; }
    requestAnimationFrame(tick);
  };
  const ensureLoop = () => {
    if (!loopRunning && playing) { loopRunning = true; requestAnimationFrame(tick); }
  };
  tabs.forEach((tab, i) => {
    tab.addEventListener('click', () => select(i, true));
    tab.addEventListener('keydown', (e) => {
      let next = i;
      if (e.key === 'ArrowRight') next = (i + 1) % tabs.length;
      else if (e.key === 'ArrowLeft') next = (i - 1 + tabs.length) % tabs.length;
      else if (e.key === 'ArrowDown') next = (i + 1) % tabs.length;
      else if (e.key === 'ArrowUp') next = (i - 1 + tabs.length) % tabs.length;
      else if (e.key === 'Home') next = 0;
      else if (e.key === 'End') next = tabs.length - 1;
      else return;
      e.preventDefault();
      select(next, true);
      tabs[next].focus();
    });
  });
  playBtn?.addEventListener('click', () => {
    playing = !playing;
    lastSwitch = performance.now();
    paintPlay();
    ensureLoop();
  });
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) lastSwitch = performance.now();
  });
  select(0, false);
  paintPlay();
  ensureLoop();
  requestAnimationFrame(() => requestAnimationFrame(() => hero.classList.add('ready')));
}

/* ---------- floating header: mobile drawer + dropdown menus ---------- */
export function initHeader() {
  const btn = document.getElementById('menuBtn');
  const drawer = document.getElementById('mobileDrawer');
  if (btn && drawer) {
    const set = (open) => {
      drawer.hidden = !open;
      btn.setAttribute('aria-expanded', String(open));
    };
    btn.addEventListener('click', () => set(drawer.hidden));
    drawer.querySelectorAll('a, button').forEach((el) => el.addEventListener('click', () => set(false)));
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !drawer.hidden) { set(false); btn.focus(); }
    });
  }
  // Dropdowns open on hover/focus via CSS; JS adds Escape-to-close and
  // keeps aria-expanded honest for pointer and keyboard users.
  document.querySelectorAll('.nav-drop').forEach((drop) => {
    const trigger = drop.querySelector(':scope > a, :scope > button');
    const menu = drop.querySelector(':scope > .nav-menu');
    if (!trigger || !menu) return;
    const links = [...menu.querySelectorAll('a')];
    const setExpanded = (open) => trigger.setAttribute('aria-expanded', String(open));
    setExpanded(false);
    drop.addEventListener('mouseenter', () => setExpanded(true));
    drop.addEventListener('mouseleave', () => setExpanded(false));
    trigger.addEventListener('focus', () => setExpanded(true));
    drop.addEventListener('focusout', (e) => {
      if (!drop.contains(e.relatedTarget)) setExpanded(false);
    });
    drop.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        setExpanded(false);
        trigger.focus();
      } else if (e.key === 'ArrowDown' && document.activeElement === trigger && links.length) {
        e.preventDefault();
        setExpanded(true);
        links[0].focus();
      }
    });
  });
}

/* ---------- matrix tooltip (never covers its cell) ---------- */
export function initMatrixTip() {
  const table = document.getElementById('matrix');
  if (!table) return;
  let tip = document.getElementById('matrix-tip');
  if (!tip) {
    tip = document.createElement('div');
    tip.id = 'matrix-tip';
    tip.setAttribute('role', 'tooltip');
    tip.hidden = true;
    document.body.appendChild(tip);
  }
  let anchor = null;
  const place = () => {
    if (!anchor || !anchor.isConnected) return;
    tip.hidden = false;
    tip.style.left = '0px';
    tip.style.top = '0px';
    const r = anchor.getBoundingClientRect();
    const tw = tip.offsetWidth, th = tip.offsetHeight;
    const vw = document.documentElement.clientWidth, vh = document.documentElement.clientHeight;
    const clampX = (v) => Math.min(Math.max(8, v), Math.max(8, vw - tw - 8));
    const roomL = r.left + r.width / 2 - 8, roomR = vw - (r.left + r.width / 2) - 8;
    let x;
    if (roomL >= tw / 2 && roomR >= tw / 2) x = r.left + r.width / 2 - tw / 2;
    else if (roomR >= roomL) x = r.left;
    else x = r.right - tw;
    const above = r.top - 8, below = vh - r.bottom - 8;
    const fitsAbove = above >= th + 10, fitsBelow = below >= th + 10;
    const row = anchor.closest ? anchor.closest('tr') : null;
    const bodyRows = table.tBodies && table.tBodies[0] ? table.tBodies[0].rows : [];
    const inFirstRow = !!(row && bodyRows.length && row === bodyRows[0]);
    const inLastRow = !!(row && bodyRows.length && row === bodyRows[bodyRows.length - 1]);
    const sideL = r.left - 8, sideR = vw - r.right - 8;
    const sideY = r.top + r.height / 2 - th / 2;
    const sideDir = sideR >= sideL ? 1 : -1;
    const fitsSide = sideY >= 8 && sideY + th <= vh - 8
      && (sideDir > 0 ? sideR >= tw + 10 : sideL >= tw + 10);
    const rectHits = (x0, y0, el) => {
      if (!el) return false;
      const b = el.getBoundingClientRect();
      if (!b.width || !b.height) return false;
      return !(x0 + tw <= b.left || x0 >= b.right || y0 + th <= b.top || y0 >= b.bottom);
    };
    const xc = clampX(x);
    const coversHead = rectHits(xc, r.top - th - 10, table.tHead)
      || rectHits(xc, r.top - th - 10, table.querySelector('caption'));
    const coversNote = rectHits(xc, r.bottom + 10, document.getElementById('matrix-interp'));
    const edgeEscape = fitsSide
      && ((inFirstRow && fitsAbove && !fitsBelow && coversHead)
        || (inLastRow && fitsBelow && !fitsAbove && coversNote));
    let y;
    if (edgeEscape || (!fitsAbove && !fitsBelow)) {
      x = sideDir > 0 ? r.right + 10 : r.left - tw - 10;
      y = Math.min(Math.max(8, sideY), Math.max(8, vh - th - 8));
      tip.style.left = `${Math.round(clampX(x))}px`;
      tip.style.top = `${Math.round(y)}px`;
      requestAnimationFrame(() => tip.classList.add('show'));
      return;
    }
    if (fitsAbove && fitsBelow && inFirstRow) y = r.bottom + 10;
    else if (fitsAbove && fitsBelow && inLastRow) y = r.top - th - 10;
    else if (fitsAbove && fitsBelow) y = below > above ? r.bottom + 10 : r.top - th - 10;
    else if (fitsAbove) y = r.top - th - 10;
    else y = r.bottom + 10;
    x = clampX(x);
    if (y + th > vh - 8) y = Math.max(8, vh - th - 8);
    tip.style.left = `${Math.round(x)}px`;
    tip.style.top = `${Math.round(y)}px`;
    requestAnimationFrame(() => tip.classList.add('show'));
  };
  const show = (el) => {
    anchor = el;
    tip.textContent = el.getAttribute('data-tip') || '';
    el.setAttribute('aria-describedby', 'matrix-tip');
    place();
  };
  const hide = () => {
    if (anchor) anchor.removeAttribute('aria-describedby');
    anchor = null;
    tip.classList.remove('show');
    tip.hidden = true;
  };
  table.addEventListener('matrix-repaint', hide);
  table.addEventListener('mouseover', (e) => {
    const c = e.target && e.target.closest ? e.target.closest('[data-tip]') : null;
    if (c && table.contains(c) && c !== anchor) show(c);
  });
  table.addEventListener('mouseout', (e) => {
    const c = e.target && e.target.closest ? e.target.closest('[data-tip]') : null;
    if (c && !(e.relatedTarget && c.contains(e.relatedTarget))) hide();
  });
  table.addEventListener('focusin', (e) => {
    const c = e.target && e.target.closest ? e.target.closest('[data-tip]') : null;
    if (c) show(c);
  });
  table.addEventListener('focusout', hide);
  table.addEventListener('transitionend', () => { if (anchor) place(); });
  table.addEventListener('animationend', () => { if (anchor) place(); });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && anchor) { const a = anchor; hide(); if (a.blur) a.blur(); }
  });
  window.addEventListener('scroll', () => {
    if (!anchor || !anchor.isConnected) { hide(); return; }
    const r = anchor.getBoundingClientRect();
    const vw = document.documentElement.clientWidth, vh = document.documentElement.clientHeight;
    if (r.bottom > 0 && r.top < vh && r.right > 0 && r.left < vw) place();
    else hide();
  }, { passive: true, capture: true });
  window.addEventListener('resize', hide);
}

/* ---------- dossier modal (home only) ---------- */
export function initDossier() {
  const modal = document.getElementById('dossierModal');
  if (!modal) return;
  const tabs = [...modal.querySelectorAll('[role="tab"]')];
  const panes = [...modal.querySelectorAll('.dossier-pane')];
  let opener = null;
  const switchTab = (key, focus) => {
    tabs.forEach((t) => {
      const on = t.dataset.dossier === key;
      t.setAttribute('aria-selected', String(on));
      t.tabIndex = on ? 0 : -1;
      if (on && focus) t.focus();
    });
    panes.forEach((p) => { p.hidden = p.id !== `dossierPane-${key}`; });
  };
  const open = (key, invoker) => {
    opener = invoker || document.activeElement;
    modal.hidden = false;
    document.body.style.overflow = 'hidden';
    switchTab(key || 'studies', true);
  };
  const close = () => {
    if (modal.hidden) return;
    modal.hidden = true;
    document.body.style.overflow = '';
    if (opener && opener.focus) opener.focus();
  };
  document.querySelectorAll('[data-open-dossier]').forEach((b) => {
    b.addEventListener('click', () => open(b.getAttribute('data-open-dossier'), b));
  });
  modal.querySelector('[data-close-dossier]').addEventListener('click', close);
  modal.addEventListener('click', (e) => { if (e.target === modal) close(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') close(); });
  modal.addEventListener('keydown', (e) => {
    if (e.key !== 'Tab') return;
    const f = [...modal.querySelectorAll('button, [href], [tabindex]:not([tabindex="-1"])')]
      .filter((el) => !el.disabled && el.offsetParent !== null);
    if (!f.length) return;
    const first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });
  tabs.forEach((tab, i) => {
    tab.addEventListener('click', () => switchTab(tab.dataset.dossier, false));
    tab.addEventListener('keydown', (e) => {
      let next = i;
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') next = (i + 1) % tabs.length;
      else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') next = (i - 1 + tabs.length) % tabs.length;
      else if (e.key === 'Home') next = 0;
      else if (e.key === 'End') next = tabs.length - 1;
      else return;
      e.preventDefault();
      switchTab(tabs[next].dataset.dossier, true);
    });
  });
}

/* ---------- skip link ---------- */
export function initSkip() {
  const skip = document.querySelector('.skip-link');
  if (skip) skip.addEventListener('click', (e) => {
    e.preventDefault();
    const main = document.getElementById('main');
    main.focus({ preventScroll: true });
    main.scrollIntoView();
  });
}

/* One call boots every shared UI behavior present on the page. */
export function initShared() {
  initMotion();
  initScrollHints();
  initPortal();
  initHeader();
  initDossier();
  initMatrixTip();
  initWeave();
  initSkip();
}

