/* Workbench shell: nav, hash router, server status. */
import { api } from './api.js';
import { esc } from './format.js';
import { viewWorkspace } from './views/workspace.js';
import { viewRun } from './views/run.js';
import { viewHistory } from './views/history.js';
import { viewAnalytics } from './views/analytics.js';
import { viewLab } from './views/lab.js';
import { viewStudio } from './views/studio.js';

const ROUTES = [
  { id: 'workspace', num: '01', title: 'Workspace', icon: 'nav-workspace', sec: 'Run & inspect', render: viewWorkspace },
  { id: 'history', num: '02', title: 'History', icon: 'nav-history', render: viewHistory },
  { id: 'analytics', num: '03', title: 'Analytics', icon: 'nav-analytics', render: viewAnalytics },
  { id: 'lab', num: '04', title: 'Campaign Lab', icon: 'nav-lab', sec: 'Build', render: viewLab },
  { id: 'studio', num: '05', title: 'Workflow Studio', icon: 'nav-studio', render: viewStudio },
];

const main = document.getElementById('main');
const navList = document.getElementById('nav-list');
const topbarTitle = document.getElementById('topbar-title');
const topbarBadges = document.getElementById('topbar-badges');
let cleanup = null;

/* Mega-menu map: triggers reuse the ROUTES section labels; item labels
 * and hrefs stay byte-identical to ROUTES. Taglines + feature cards are
 * the only new copy (per the approved mega-menu system). */
const MENUS = [
  { sec: 'Run & inspect', icon: 'nav-workspace', items: [
    { id: 'workspace', tag: 'Run + inspect executions', color: '#0f172a' },
    { id: 'history', tag: 'Every past execution', color: '#b45309' },
    { id: 'analytics', tag: 'Trends + funnels', color: '#1d4ed8' },
  ], card: { href: '/research/#/command', art: 'Command Center', kicker: 'Research Console · Eval',
    title: 'Chimera vs replay, at a glance', link: 'Inspect the evidence →',
    svg: '<g fill="none" stroke="#ffffff" stroke-width="1.6" opacity=".5"><circle cx="144" cy="95" r="62"/><circle cx="144" cy="95" r="40"/><ellipse cx="144" cy="95" rx="62" ry="24"/><path d="M82 95h124M144 33v124"/></g>' } },
  { sec: 'Build', icon: 'nav-studio', items: [
    { id: 'lab', tag: 'Campaign analytics', color: '#1E9A8A' },
    { id: 'studio', tag: 'Compose step workflows', color: '#3A6EA5' },
  ], card: { href: '#/workspace', art: 'Run in a real browser', kicker: 'Workspace · Live runs',
    title: 'Pick a workflow, watch it run', link: 'Open the Workspace →',
    svg: '<g fill="none" stroke="#ffffff" stroke-width="1.6" opacity=".5"><rect x="34" y="42" width="220" height="106" rx="10"/><path d="M34 72h220"/><path d="M70 105l16 12-16 12M120 132h44" stroke-linecap="round"/></g>' } },
  { sec: 'Evidence', icon: 'nav-research', items: [
    { href: '/research/', title: 'Research Console', icon: 'nav-research', tag: 'Evidence explorer', color: '#0e7490' },
    { href: '/research/#/command', title: 'Command Center', icon: 'nav-analytics', tag: 'Chimera vs replay, at a glance', color: '#1d4ed8' },
    { href: '/research/#/audit', title: 'Audit & reproducibility', icon: 'st-pass', tag: 'Samples, verdicts, manifests', color: '#0e7a3d' },
  ], card: { href: '/results/#heldout', art: 'Held-out evaluation', kicker: 'Results · Chimera vs replay',
    title: 'The scoreboard, sealed', link: 'Open the results →',
    svg: '<g fill="none" stroke="#ffffff" stroke-width="1.6" opacity=".5"><path d="M30 150V78M80 150V52M130 150V96M180 150V64M230 150V104" stroke-linecap="round"/><path d="M22 150h244"/></g>' } },
];

function isActive(routeId, hash) {
  return hash === `#/${routeId}`
    || (routeId === 'workspace' && hash.startsWith('#/run/'))
    || (routeId === 'lab' && hash.startsWith('#/lab/'))
    || (routeId === 'studio' && hash.startsWith('#/studio/'));
}

function megaItem(route, tag, color, active) {
  return `<li><a href="#/${route.id}"${active ? ' aria-current="page"' : ''}>`
    + `<span class="tile" style="--t:${color}"><svg aria-hidden="true"><use href="#${route.icon}"/></svg></span>`
    + `<span><strong>${esc(route.title)}</strong><small>${esc(tag)}</small></span></a></li>`;
}

function megaCard(card) {
  return `<a class="mega-card" href="${card.href}">`
    + `<span class="mega-card-art" aria-hidden="true"><svg viewBox="0 0 288 190" preserveAspectRatio="xMidYMid slice">${card.svg}</svg><b>${esc(card.art)}</b></span>`
    + `<span class="mega-card-cap"><span>${esc(card.kicker)}</span><strong>${esc(card.title)}</strong><em>${esc(card.link)}</em></span></a>`;
}

function nav() {
  const hash = (window.location.hash || '#/workspace').split('?')[0];
  navList.innerHTML = MENUS.map((m) => {
    const items = m.items.map((it) => {
      if (it.id) {
        const route = ROUTES.find((r) => r.id === it.id);
        return megaItem(route, it.tag, it.color, isActive(it.id, hash));
      }
      return `<li><a href="${it.href}"><span class="tile" style="--t:${it.color}">`
        + `<svg aria-hidden="true"><use href="#${it.icon}"/></svg></span>`
        + `<span><strong>${esc(it.title)}</strong><small>${esc(it.tag)}</small></span></a></li>`;
    }).join('');
    return `<li class="nav-drop" data-menu="${esc(m.sec)}">`
      + `<button type="button" aria-haspopup="true" aria-expanded="false">`
      + `<svg class="nav-ic" aria-hidden="true"><use href="#${m.icon}"/></svg>${esc(m.sec)} `
      + `<svg class="nav-caret" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9.5l6 6 6-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></button>`
      + `<ul class="nav-menu" aria-label="${esc(m.sec)}"><li><div class="mega-inner">`
      + `<div><p class="mega-kicker">${esc(m.sec)}</p><ul class="mega-grid">${items}</ul></div>`
      + `${megaCard(m.card)}</div></li></ul></li>`;
  }).join('');
  bindMega();
}

/* Dropdowns open on hover/focus via CSS; JS keeps aria-expanded honest
 * and adds ArrowDown-to-first-item + Escape-to-close (nav re-renders
 * per route, so this rebinds after every render). */
function bindMega() {
  navList.querySelectorAll('.nav-drop').forEach((drop) => {
    const trigger = drop.querySelector(':scope > button');
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

async function status() {
  const dot = document.getElementById('data-dot');
  const label = document.getElementById('data-status');
  const foot = document.getElementById('footer-status');
  try {
    const health = await api.health();
    dot.className = 'data-dot ok';
    label.textContent = `${health.executions} executions indexed`;
    foot.textContent = 'Server connected · SQLite index';
  } catch {
    dot.className = 'data-dot bad';
    label.textContent = 'Server unreachable';
    foot.textContent = 'Start the server: .venv/bin/python -m workbench.server';
  }
}

function closeNav() {
  document.body.classList.remove('nav-open');
  const btn = document.getElementById('menu-btn');
  if (btn) btn.setAttribute('aria-expanded', 'false');
}

async function route() {
  if (cleanup) { try { cleanup(); } catch { /* next view */ } cleanup = null; }
  nav();
  closeNav();
  const hash = window.location.hash || '#/workspace';
  const [pathPart, queryPart] = hash.split('?');
  const [, id, param] = pathPart.split('/');
  const query = Object.fromEntries(new URLSearchParams(queryPart || ''));
  try {
    if (id === 'run' && param) {
      topbarTitle.textContent = 'Execution';
      topbarBadges.innerHTML = '';
      cleanup = await viewRun(main, decodeURIComponent(param), topbarBadges);
    } else {
      const found = ROUTES.find((r) => r.id === id) || ROUTES[0];
      topbarTitle.textContent = found.title;
      topbarBadges.innerHTML = '';
      cleanup = await found.render(main, topbarBadges, { param, query });
    }
  } catch (err) {
    topbarTitle.textContent = 'Error';
    main.innerHTML = `<div class="banner bad" role="alert"><svg aria-hidden="true"><use href="#st-fail"/></svg><span>`
      + `<strong>Could not load this view:</strong> ${esc(err.message)}. `
      + `Is the server running (<code>.venv/bin/python -m workbench.server</code>)?</span></div>`;
  }
  main.focus({ preventScroll: true });
}

document.getElementById('menu-btn').addEventListener('click', (e) => {
  const open = document.body.classList.toggle('nav-open');
  e.currentTarget.setAttribute('aria-expanded', String(open));
});
document.getElementById('scrim').addEventListener('click', closeNav);
navList.addEventListener('click', (e) => {
  if (e.target.closest('a')) closeNav();
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && document.body.classList.contains('nav-open')) {
    closeNav();
    document.getElementById('menu-btn').focus();
  }
});

window.addEventListener('hashchange', route);
status();
setInterval(status, 15000);
route();
