/* Chimera console shell: hash router, navigation, boot. */
import { loadAll, getState, esc } from './data.js';
import { pageCommand } from './pages/command.js';
import { pageMap } from './pages/map.js';
import { pageAtlas } from './pages/atlas.js';
import { pageObservatory } from './pages/observatory.js';
import { pageEvidence } from './pages/evidence.js';
import { pageFailures } from './pages/failures.js';
import { pageRecovery } from './pages/recovery.js';
import { pageAudit } from './pages/audit.js';
import { pageArchive } from './pages/archive.js';
import { pageTerrain } from './pages/terrain.js';
import { pageRiver } from './pages/river.js';
import { pageLineage } from './pages/lineage.js';
import { pageReview } from './pages/review.js';
import { start as startAmbient, setMotionEnabled, isMotionEnabled } from './viz/particles.js';

const ICONS = {
  command: '<circle cx="10" cy="10" r="3.2" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M10 1.5v3M10 15.5v3M1.5 10h3M15.5 10h3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
  map: '<circle cx="10" cy="10" r="2.4" fill="currentColor"/><circle cx="10" cy="10" r="6.4" fill="none" stroke="currentColor" stroke-width="1.4"/><circle cx="16.5" cy="4.5" r="1.6" fill="currentColor"/>',
  atlas: '<path d="M3 5.5h14M3 10h14M3 14.5h14" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><circle cx="6" cy="5.5" r="1.8" fill="currentColor"/><circle cx="13" cy="14.5" r="1.8" fill="currentColor"/>',
  observatory: '<path d="M3 16.5v-5M8 16.5V8M13 16.5v-8M18 16.5V4" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>',
  evidence: '<circle cx="9" cy="9" r="5.5" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M13.5 13.5 18 18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
  failures: '<path d="M10 2.5 17.5 16.5h-15z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M10 8v3.4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><circle cx="10" cy="13.8" r="1" fill="currentColor"/>',
  recovery: '<path d="M16.5 10a6.5 6.5 0 1 1-2-4.7" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M16.8 1.8v3.4h-3.4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
  audit: '<path d="M10 2 4 5v5.2c0 3.6 2.6 6.1 6 7.3 3.4-1.2 6-3.7 6-7.3V5z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M7.5 10l1.8 1.8 3.4-3.6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
  archive: '<rect x="3" y="3.5" width="14" height="4.5" rx="1" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M4.5 8v8.5h11V8" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  terrain: '<path d="M2 15.5 6.5 9l3.5 4 3-6 5 8.5z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><circle cx="6.5" cy="9" r="1.4" fill="currentColor"/><circle cx="13" cy="7" r="1.4" fill="currentColor"/>',
  river: '<path d="M2 5.5c4 0 4 3 8 3s4-3 8-3M2 10.5c4 0 4 3 8 3s4-3 8-3M2 15.5c4 0 4 3 8 3s4-3 8-3" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>',
  lineage: '<circle cx="5" cy="5" r="2.2" fill="currentColor"/><circle cx="15" cy="5" r="2.2" fill="currentColor"/><circle cx="10" cy="15" r="2.2" fill="currentColor"/><path d="M5 7.5 10 12.5M15 7.5 10 12.5" stroke="currentColor" stroke-width="1.4"/>',
  review: '<rect x="4" y="3" width="12" height="14" rx="2" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M7 10.5l2 2 4-4.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
};

export const ROUTES = [
  { id: 'command', title: 'Command Center', render: pageCommand },
  { id: 'map', title: 'Constellation', render: pageMap },
  { id: 'atlas', title: 'Experiment Atlas', render: pageAtlas },
  { id: 'observatory', title: 'Evaluation Observatory', render: pageObservatory },
  { id: 'evidence', title: 'Evidence Inspector', render: pageEvidence, hidden: true },
  { id: 'failures', title: 'Failure Cartography', render: pageFailures },
  { id: 'recovery', title: 'Recovery Studio', render: pageRecovery },
  { id: 'audit', title: 'Audit & Reproducibility', render: pageAudit },
  { id: 'archive', title: 'Research Archive', render: pageArchive },
  { id: 'terrain', title: 'Outcome Terrain', render: pageTerrain },
  { id: 'river', title: 'Evidence River', render: pageRiver },
  { id: 'lineage', title: 'Provenance Graph', render: pageLineage },
  { id: 'review', title: 'Mini-review queue', render: pageReview },
];

function icon(id) {
  return `<svg viewBox="0 0 20 20" aria-hidden="true">${ICONS[id] || ''}</svg>`;
}

export function parseHash() {
  const raw = (window.location.hash || '#/command').replace(/^#/, '');
  const [pathPart, queryPart] = raw.split('?');
  const segments = pathPart.split('/').filter(Boolean);
  const query = {};
  if (queryPart) {
    for (const pair of queryPart.split('&')) {
      const [k, v] = pair.split('=');
      if (k) query[decodeURIComponent(k)] = decodeURIComponent(v || '');
    }
  }
  return { segments, query };
}

export function link(id, params = [], query = {}) {
  let h = `#/${id}`;
  for (const p of params) h += `/${encodeURIComponent(p)}`;
  const qs = Object.entries(query).filter(([, v]) => v !== '' && v != null)
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join('&');
  return qs ? `${h}?${qs}` : h;
}

function buildNav() {
  const ul = document.getElementById('nav-list');
  ul.innerHTML = ROUTES.filter((r) => !r.hidden).map((r) => (
    `<li><a href="${link(r.id)}" data-route="${r.id}">${icon(r.id)}<span>${esc(r.title)}</span></a></li>`
  )).join('');
}

function setActive(routeId) {
  document.querySelectorAll('#nav-list a').forEach((a) => {
    if (a.dataset.route === routeId) a.setAttribute('aria-current', 'page');
    else a.removeAttribute('aria-current');
  });
}

function notFound(main, segments) {
  document.getElementById('topbar-title').textContent = 'Not found';
  document.title = 'Not found · Chimera Research Console';
  main.innerHTML = `<div class="page-head"><div><h1>Route not found</h1></div></div>
    <div class="card"><p>No workspace matches <code>#/${esc(segments.join('/'))}</code>.</p>
    <p><a href="${link('command')}">Return to the Command Center</a>.</p></div>`;
}

function updateDataChrome() {
  const s = getState();
  const dot = document.getElementById('data-dot');
  const label = document.getElementById('data-status');
  const foot = document.getElementById('footer-status');
  if (!s.loaded) {
    dot.className = 'data-dot';
    label.textContent = 'Loading evidence…';
    foot.textContent = '';
    return;
  }
  const runsOk = [...s.runs.values()].filter((r) => r.data).length;
  if (runsOk === 0) {
    dot.className = 'data-dot bad';
    label.textContent = 'Evidence unavailable';
    foot.textContent = `${s.failed.length} source(s) failed to load`;
    return;
  }
  dot.className = s.failed.length ? 'data-dot' : 'data-dot ok';
  label.textContent = `${runsOk}/4 runs · ${s.episodes.length} episodes`;
  foot.textContent = s.failed.length
    ? `${s.failed.length} optional source(s) missing`
    : `${s.episodes.length} episodes · ${s.cells.length} cells indexed`;
}

async function render() {
  const main = document.getElementById('main');
  const { segments, query } = parseHash();
  const routeId = segments[0] || 'command';
  const route = ROUTES.find((r) => r.id === routeId);
  document.body.classList.remove('nav-open');
  document.getElementById('menu-btn').setAttribute('aria-expanded', 'false');
  if (!route) { setActive(''); notFound(main, segments); return; }
  document.getElementById('topbar-title').textContent = route.title;
  document.title = `${route.title} · Chimera Research Console`;
  setActive(route.hidden ? '' : route.id);
  updateTopBadges(route.id, segments);
  main.innerHTML = '<div class="card"><p>Loading…</p></div>';
  try {
    await route.render(main, { params: segments.slice(1), query });
  } catch (err) {
    main.innerHTML = `<div class="page-head"><div><h1>${esc(route.title)}</h1></div></div>
      <div class="banner warn"><strong>This view failed to render.</strong> ${esc(err.message || err)}</div>`;
  }
  main.focus({ preventScroll: true });
  window.scrollTo(0, 0);
}

function updateTopBadges(routeId, segments) {
  const el = document.getElementById('topbar-badges');
  const s = getState();
  if (routeId === 'evidence' && segments[1]) {
    el.innerHTML = `<span class="pill dim mono">${esc(segments[1])}</span>`
      + (segments[2] ? `<span class="pill dim mono">${esc(segments[2])}</span>` : '');
    return;
  }
  const evalOk = s.runs.get('eval-20261028-chimera') && s.runs.get('eval-20261028-baseline-a');
  el.innerHTML = evalOk
    ? '<span class="pill warn"><span class="dot"></span>Eval provisional</span>'
    : '<span class="pill dim">Evidence loading</span>';
}

function bindMotionToggle() {
  const btn = document.getElementById('motion-toggle');
  const paint = () => {
    const on = isMotionEnabled();
    btn.textContent = `Motion: ${on ? 'on' : 'off'}`;
    btn.setAttribute('aria-pressed', String(on));
  };
  paint();
  btn.addEventListener('click', () => { setMotionEnabled(!isMotionEnabled()); paint(); });
}

function bindChrome() {
  // Skip link must focus content without touching the hash router.
  document.querySelector('.skip-link').addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('main').focus();
  });
  const btn = document.getElementById('menu-btn');
  const scrim = document.getElementById('scrim');
  btn.addEventListener('click', () => {
    const open = document.body.classList.toggle('nav-open');
    btn.setAttribute('aria-expanded', String(open));
    scrim.hidden = !open;
  });
  scrim.addEventListener('click', () => {
    document.body.classList.remove('nav-open');
    btn.setAttribute('aria-expanded', 'false');
    scrim.hidden = true;
  });
  window.addEventListener('hashchange', render);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.body.classList.remove('nav-open');
      scrim.hidden = true;
      btn.setAttribute('aria-expanded', 'false');
    }
  });
}

async function boot() {
  buildNav();
  bindChrome();
  bindMotionToggle();
  startAmbient();
  updateDataChrome();
  await loadAll(() => updateDataChrome());
  updateDataChrome();
  if (!window.location.hash) window.location.hash = '#/command';
  await render();
}

boot();
