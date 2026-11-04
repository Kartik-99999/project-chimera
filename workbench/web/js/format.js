/* Shared formatting. Every label states what it means; missing
 * values render as an explicit dash, never as zero. */

export function esc(value) {
  return String(value === null || value === undefined ? '' : value)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

export function fmtMs(ms) {
  if (ms === null || ms === undefined) return '—';
  if (ms < 1000) return `${ms} ms`;
  return `${(ms / 1000).toFixed(ms < 10000 ? 2 : 1)} s`;
}

export function fmtWhen(iso) {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
      second: '2-digit',
    });
  } catch { return String(iso); }
}

export function fmtInt(n) {
  if (n === null || n === undefined) return '—';
  return Number(n).toLocaleString('en-US');
}

export function fmtPct(ratio) {
  if (ratio === null || ratio === undefined) return '—';
  return `${(ratio * 100).toFixed(1)}%`;
}

const VERDICTS = {
  'verified-success': ['ok', 'Verified success', 'st-pass'],
  'verified-failure': ['bad', 'Verified failure', 'st-fail'],
  'insufficient-evidence': ['warn', 'Insufficient evidence', 'st-pending'],
  'pending': ['info', 'Pending', 'st-running'],
};

const STATUSES = {
  'succeeded': ['ok', 'Succeeded', 'st-pass'],
  'failed': ['bad', 'Failed', 'st-fail'],
  'cancelled': ['warn', 'Cancelled', 'st-pending'],
  'running': ['info', 'Running', 'st-running'],
  'queued': ['info', 'Queued', 'st-running'],
  'error': ['bad', 'Error', 'st-fail'],
};

function icon(id) {
  return `<svg aria-hidden="true"><use href="#${id}"/></svg>`;
}

export function verdictPill(verdict) {
  const [cls, label, ic] = VERDICTS[verdict] || ['warn', verdict || '—', 'st-pending'];
  return `<span class="pill ${cls}">${icon(ic)}${esc(label)}</span>`;
}

export function statusPill(status) {
  const [cls, label, ic] = STATUSES[status] || ['warn', status || '—', 'st-pending'];
  return `<span class="pill ${cls}">${icon(ic)}${esc(label)}</span>`;
}

const DRIVERS = {
  'chimera': 'Chimera',
  'baseline-a': 'Baseline A',
  'replay-100': 'Replay · 100 ms',
  'replay-1000': 'Replay · 1 s',
  'replay-2500': 'Replay · 2.5 s',
  'replay-5000': 'Replay · 5 s',
};

export function driverLabel(driver) {
  return DRIVERS[driver] || driver || '—';
}

const SCENARIOS = {
  'S-NORM': 'Normal page',
  'S-SLOW': 'Slow load',
  'S-DIS': 'Broken submit',
  'S-SLOWDIS': 'Slow + broken',
};

export function scenarioLabel(id) {
  if (typeof id === 'string' && id.startsWith('studio:')) {
    return 'studio · ' + id.slice('studio:'.length).split(':').join(' · ');
  }
  if (typeof id === 'string' && id.startsWith('sauce-stress:')) {
    return 'stress · ' + id.slice('sauce-stress:'.length).split('/').join(' · ');
  }
  if (typeof id === 'string' && id.startsWith('sauce:')) {
    return id.slice('sauce:'.length).split('/').join(' · ');
  }
  if (typeof id === 'string' && id.startsWith('flipkart:')) {
    return id.slice('flipkart:'.length).split('/').join(' · ');
  }
  if (typeof id === 'string' && id.startsWith('amazon:')) {
    return id.slice('amazon:'.length).split('/').join(' · ');
  }
  if (typeof id === 'string' && id.startsWith('so:')) {
    return id.slice('so:'.length).split('/').join(' · ');
  }
  return SCENARIOS[id] || id || '—';
}

export function originPill(origin) {
  if (origin === 'external') return '<span class="pill vio">External app</span>';
  return '';
}

export function sourcePill(source) {
  if (source === 'benchmark') return '<span class="pill vio">Benchmark history</span>';
  if (source === 'matched-budget') return '<span class="pill">Matched-budget</span>';
  return '<span class="pill info">Workbench run</span>';
}

const WORKFLOWS = {
  'create-project': 'Create a project',
  'fill-contact-form': 'Fill a contact form',
  'saucedemo-order': 'Order from SauceDemo',
  'saucedemo-stress': 'Stress the SauceDemo store',
  'flipkart-add-to-cart': 'Add a Flipkart item to cart',
  'wikipedia-article-lookup': 'Look up a Wikipedia article',
  'wiktionary-word-lookup': 'Look up a Wiktionary word',
  'pypi-package-lookup': 'Look up a PyPI package',
  'bbc-headlines': 'Capture BBC section headlines',
  'github-profile': 'Look up a GitHub profile',
  'crates-lookup': 'Look up a Rust crate',
  'bbc-weather': 'Check a BBC Weather city forecast',
  'github-search': 'Search GitHub repositories',
  'steam-price-check': 'Check a Steam game price',
  'arxiv-search': 'Search arXiv papers',
  'stackoverflow-search': 'Search Stack Overflow questions',
  'amazon-price-check': 'Check an Amazon product price',
};

export function sessionLabel(session) {
  if (typeof session === 'string' && session.startsWith('user:')) {
    return `Your profile '${session.slice('user:'.length)}'`;
  }
  return 'Clean session';
}

export function workflowLabel(id) {
  if (typeof id === 'string' && id.startsWith('studio:')) {
    return `Studio ${id.slice('studio:'.length, 'studio:'.length + 8)}`;
  }
  return WORKFLOWS[id] || id || '—';
}

const BANNER_ICONS = { bad: 'st-fail', warn: 'st-pending', info: 'st-running' };

const BANNER_ROLES = { bad: 'role="alert"', warn: 'role="status"', info: 'role="status"' };

export function banner(kind, html) {
  return `<div class="banner ${kind}" ${BANNER_ROLES[kind] || 'role="status"'}>${icon(BANNER_ICONS[kind] || 'st-running')}<span>${html}</span></div>`;
}

export function emptyState(title, body, mark) {
  const markHtml = mark ? `<svg class="empty-mark" aria-hidden="true"><use href="#${mark}"/></svg>` : '';
  return `<div class="panel"><div class="empty">${markHtml}<div><h2>${esc(title)}</h2><p>${body}</p></div></div></div>`;
}

export function svgOpen(width, height, label) {
  return `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(label)}">`;
}

/* Summary-first tab grouping (elegance Part C). Render tabs + panels
 * from [key, label, html] groups, then call tabsInit(scope) to wire
 * roving tabindex, Arrow/Home/End, and jump-chip selection. */
export function tabsHtml(id, label, groups, active) {
  const tabs = groups.map(([key, tabLabel], i) => {
    const on = (active || groups[0][0]) === key;
    return `<button class="wb-tab" role="tab" id="${id}-tab-${key}" `
      + `aria-controls="${id}-panel-${key}" aria-selected="${on ? 'true' : 'false'}"`
      + `${on ? '' : ' tabindex="-1"'}>${esc(tabLabel)}</button>`;
  }).join('');
  const panels = groups.map(([key, tabLabel, html]) => {
    const on = (active || groups[0][0]) === key;
    return `<section class="wb-tabpanel" role="tabpanel" id="${id}-panel-${key}" `
      + `aria-labelledby="${id}-tab-${key}" tabindex="0"${on ? '' : ' hidden'}>${html}</section>`;
  }).join('');
  const chips = groups.map(([key, tabLabel]) =>
    `<a href="#${id}-panel-${key}" data-tab="${id}-tab-${key}">${esc(tabLabel)}</a>`).join('');
  return `<div class="wb-tabs" role="tablist" aria-label="${esc(label)}" id="${id}-tablist">${tabs}</div>`
    + panels
    + `<nav class="wb-chips" aria-label="Jump to ${esc(label.toLowerCase())}">${chips}</nav>`;
}

/* Decorative artwork (Direction 1, light-mode only): static,
 * aria-hidden SVG + wrappers. No copy, data, or routing inside. */
export function artWeave() {
  return `<div class="art" aria-hidden="true"><svg class="weave" viewBox="0 0 340 220" fill="none" focusable="false">`
    + `<path d="M-20 170 L200 -20" stroke="#1E9A8A" stroke-width="1.6" opacity="0.50"/>`
    + `<path d="M20 190 L240 0" stroke="#3A6EA5" stroke-width="1.6" opacity="0.50"/>`
    + `<path d="M60 210 L280 20" stroke="#C0563B" stroke-width="1.6" opacity="0.45"/>`
    + `<path d="M120 220 L340 30" stroke="#3A6EA5" stroke-width="1.6" opacity="0.40"/>`
    + `<path d="M-40 130 L160 -30" stroke="#0B5FFF" stroke-width="1.2" opacity="0.35"/>`
    + `<path d="M170 230 L360 60" stroke="#E94C91" stroke-width="1.2" opacity="0.35"/>`
    + `<circle cx="255" cy="70" r="46" stroke="#535BD5" stroke-width="1.4" opacity="0.40"/>`
    + `<circle cx="255" cy="70" r="30" stroke="#535BD5" stroke-width="1.4" opacity="0.45"/>`
    + `<circle cx="255" cy="70" r="14" stroke="#535BD5" stroke-width="1.4" opacity="0.40"/>`
    + `<g fill="#0f172a" opacity="0.25">`
    + `<circle cx="40" cy="40" r="1.2"/><circle cx="58" cy="40" r="1.2"/><circle cx="76" cy="40" r="1.2"/>`
    + `<circle cx="40" cy="58" r="1.2"/><circle cx="58" cy="58" r="1.2"/><circle cx="76" cy="58" r="1.2"/>`
    + `</g></svg></div>`;
}

export function routeBand(inner) {
  return `<div class="route-band">${artWeave()}<div class="route-band-inner">${inner}</div></div>`;
}

export function artGlobe() {
  let s = `<div class="art" aria-hidden="true"><svg class="globe" viewBox="0 0 420 300" fill="none" focusable="false">`;
  [46, 68, 90, 112, 134].forEach((r) => {
    s += `<circle cx="300" cy="150" r="${r}" stroke="#ffffff" stroke-width="1.1" opacity="0.22"/>`;
  });
  [30, 62, 94].forEach((rx) => {
    s += `<ellipse cx="300" cy="150" rx="${rx}" ry="134" stroke="#ffffff" stroke-width="1.1" opacity="0.16"/>`;
  });
  s += `<ellipse cx="300" cy="150" rx="112" ry="44" stroke="#22d3ee" stroke-width="1.4" opacity="0.55"/>`
    + `<ellipse cx="300" cy="150" rx="60" ry="134" stroke="#e94c91" stroke-width="1.4" opacity="0.45"/>`
    + `<path d="M84 52 l6 14 14 6 -14 6 -6 14 -6 -14 -14 -6 14 -6 z" fill="#ffffff" opacity="0.9"/>`
    + `<path d="M150 210 l4 10 10 4 -10 4 -4 10 -4 -10 -10 -4 10 -4 z" fill="#ffffff" opacity="0.5"/>`
    + `</svg></div>`;
  return s;
}

export function routeBandDark(inner) {
  return `<div class="route-band dark">${artGlobe()}<div class="route-band-inner">${inner}</div></div>`;
}

export function ctaArt() {
  return `<div class="art" aria-hidden="true"><svg class="dots" viewBox="0 0 150 96" fill="none" focusable="false">`
    + `<g fill="#0f172a" opacity="0.25">`
    + `<circle cx="12" cy="12" r="1.2"/><circle cx="30" cy="12" r="1.2"/><circle cx="48" cy="12" r="1.2"/><circle cx="66" cy="12" r="1.2"/><circle cx="84" cy="12" r="1.2"/>`
    + `<circle cx="12" cy="30" r="1.2"/><circle cx="30" cy="30" r="1.2"/><circle cx="48" cy="30" r="1.2"/><circle cx="66" cy="30" r="1.2"/><circle cx="84" cy="30" r="1.2"/>`
    + `<circle cx="12" cy="48" r="1.2"/><circle cx="30" cy="48" r="1.2"/><circle cx="48" cy="48" r="1.2"/><circle cx="66" cy="48" r="1.2"/>`
    + `<circle cx="12" cy="66" r="1.2"/><circle cx="30" cy="66" r="1.2"/><circle cx="48" cy="66" r="1.2"/>`
    + `</g>`
    + `<path d="M96 88 L150 34" stroke="#1E9A8A" stroke-width="1.6" opacity="0.50"/>`
    + `<path d="M108 92 L150 50" stroke="#3A6EA5" stroke-width="1.6" opacity="0.45"/>`
    + `</svg><svg class="glyph-corner" viewBox="0 0 24 24" focusable="false"><use href="#brand-chimera"/></svg></div>`;
}

/* Sarvam-grade v2 builders: hero fields, navy panels, banner art,
 * glass pills. All art is parametric (stop colors and radii retune
 * per surface without touching markup) and aria-hidden; IDs, routes,
 * and copy stay with the calling view. */
const HERO_BLOB = 'M150,215 C150,110 265,58 425,70 C600,84 645,182 785,170 '
  + 'C945,156 1052,120 1052,222 C1052,324 898,362 738,352 '
  + 'C560,340 518,302 378,312 C238,324 150,302 150,215 Z';

export function ornament() {
  return `<svg class="ornament" viewBox="0 0 150 26" aria-hidden="true" focusable="false">`
    + `<g fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round">`
    + `<path d="M73 20 C 58 20, 54 8, 40 10 C 30 11, 28 20, 36 21 C 41 22, 44 17, 40 15"/>`
    + `<path d="M77 20 C 92 20, 96 8, 110 10 C 120 11, 122 20, 114 21 C 109 22, 106 17, 110 15"/>`
    + `<circle cx="75" cy="20" r="1.6" fill="currentColor" stroke="none"/></g></svg>`;
}

/* Giant organic hero field. main/sub are [color, edgeOpacity,
 * midOpacity]; sat is [cx, cy, r, gradientR]. */
export function heroField(p, main, sub, sat) {
  return `<div class="hero-field" aria-hidden="true"><svg viewBox="0 0 1200 420" focusable="false">`
    + `<defs><radialGradient id="${p}-h1" gradientUnits="userSpaceOnUse" cx="600" cy="210" r="465">`
    + `<stop offset="0%" stop-color="${main[0]}" stop-opacity="${main[1]}"/>`
    + `<stop offset="55%" stop-color="${main[0]}" stop-opacity="${main[2]}"/>`
    + `<stop offset="100%" stop-color="${main[0]}" stop-opacity="0"/></radialGradient>`
    + `<radialGradient id="${p}-h2" gradientUnits="userSpaceOnUse" cx="${sat[0]}" cy="${sat[1]}" r="${sat[3]}">`
    + `<stop offset="0%" stop-color="${sub[0]}" stop-opacity="${sub[1]}"/>`
    + `<stop offset="60%" stop-color="${sub[0]}" stop-opacity="${sub[2]}"/>`
    + `<stop offset="100%" stop-color="${sub[0]}" stop-opacity="0"/></radialGradient></defs>`
    + `<path d="${HERO_BLOB}" fill="url(#${p}-h1)"/>`
    + `<circle cx="${sat[0]}" cy="${sat[1]}" r="${sat[2]}" fill="url(#${p}-h2)"/></svg></div>`;
}

/* Centered hero: ornament → kicker → head → lede → CTA row over a
 * giant organic field. Copy arrives as HTML from the calling view. */
export function hero({ kicker, head, lede, ctas, field, compact }) {
  return `<section class="hero${compact ? ' compact' : ''}" aria-labelledby="page-h1">`
    + field + `<div class="hero-inner">` + ornament()
    + `<p class="kicker">${kicker}</p>` + head
    + (lede ? `<p class="lede">${lede}</p>` : '')
    + (ctas ? `<div class="hero-ctas">${ctas}</div>` : '')
    + `</div></section>`;
}

const GLOBE_RINGS = `<g stroke="#ffffff" stroke-width="1.1">`
  + `<circle cx="300" cy="150" r="46" opacity=".22"/><circle cx="300" cy="150" r="68" opacity=".22"/>`
  + `<circle cx="300" cy="150" r="90" opacity=".22"/><circle cx="300" cy="150" r="112" opacity=".22"/>`
  + `<circle cx="300" cy="150" r="134" opacity=".22"/>`
  + `<ellipse cx="300" cy="150" rx="30" ry="134" opacity=".16"/>`
  + `<ellipse cx="300" cy="150" rx="62" ry="134" opacity=".16"/>`
  + `<ellipse cx="300" cy="150" rx="94" ry="134" opacity=".16"/></g>`;

export function navyGlobe() {
  return `<svg class="globe" viewBox="0 0 420 300" fill="none" aria-hidden="true" focusable="false">`
    + GLOBE_RINGS
    + `<ellipse cx="300" cy="150" rx="112" ry="44" stroke="#22d3ee" stroke-width="1.4" opacity=".55"/>`
    + `<ellipse cx="300" cy="150" rx="60" ry="134" stroke="#e94c91" stroke-width="1.4" opacity=".45"/>`
    + `<path d="M84 52 l6 14 14 6 -14 6 -6 14 -6 -14 -14 -6 14 -6 z" fill="#ffffff" opacity=".9"/>`
    + `<path d="M150 210 l4 10 10 4 -10 4 -4 10 -4 -10 -10 -4 10 -4 z" fill="#ffffff" opacity=".5"/></svg>`;
}

/* The one deep-navy immersive panel per surface. */
export function navySection(label, inner, attrs, cls) {
  return `<section class="${cls || 'navy'}"${attrs ? ` ${attrs}` : ''} aria-label="${label}">`
    + navyGlobe() + inner + `</section>`;
}

export function stripGlobe() {
  return `<svg class="strip-globe" viewBox="0 0 420 300" fill="none" aria-hidden="true" focusable="false">`
    + GLOBE_RINGS
    + `<ellipse cx="300" cy="150" rx="112" ry="44" stroke="#22d3ee" stroke-width="1.4" opacity=".55"/></svg>`;
}

/* Card-top art banner: tinted gradient + wireframe globe + weave or
 * bars + mono eyebrow. globe: 'left' | 'right'; deco: 'weave' | 'bars'. */
export function bannerArt({ id, stops, globe, deco, label }) {
  const gx = globe === 'left' ? 140 : 660;
  const rings = globe === 'left'
    ? `<circle cx="${gx}" cy="52" r="26"/><circle cx="${gx}" cy="52" r="42"/>`
      + `<ellipse cx="${gx}" cy="52" rx="15" ry="42"/>`
    : `<circle cx="${gx}" cy="52" r="30"/><circle cx="${gx}" cy="52" r="48"/>`
      + `<ellipse cx="${gx}" cy="52" rx="18" ry="48"/><ellipse cx="${gx}" cy="52" rx="48" ry="16"/>`;
  const weave = globe === 'left'
    ? `<g fill="none" stroke="#a8a29e" stroke-width="1" opacity=".5">`
      + `<path d="M810 84 L620 -10"/><path d="M760 110 L580 16"/></g>`
    : `<g fill="none" stroke="#94a3b8" stroke-width="1" opacity=".5">`
      + `<path d="M-10 84 L180 -10"/><path d="M40 110 L220 16"/><path d="M100 114 L260 32"/></g>`;
  const bars = `<g fill="#a5b4fc" opacity=".55"><rect x="96" y="52" width="26" height="40" rx="4"/>`
    + `<rect x="130" y="34" width="26" height="58" rx="4"/>`
    + `<rect x="164" y="62" width="26" height="30" rx="4"/></g>`;
  return `<div class="banner-art" aria-hidden="true">`
    + `<svg viewBox="0 0 800 104" preserveAspectRatio="xMidYMid slice" focusable="false">`
    + `<defs><linearGradient id="${id}" x1="0" y1="0" x2="1" y2="1">`
    + `<stop offset="0%" stop-color="${stops[0]}"/><stop offset="55%" stop-color="${stops[1]}"/>`
    + `<stop offset="100%" stop-color="${stops[2]}"/></linearGradient></defs>`
    + `<rect width="800" height="104" fill="url(#${id})"/>`
    + `<g fill="none" stroke="#ffffff" stroke-width="1.2" opacity=".9">${rings}</g>`
    + (deco === 'bars' ? bars : weave) + `</svg>`
    + `<span class="ba-label">${label}</span></div>`;
}

function glassPill(cls, label, ic) {
  return `<span class="glass${cls ? ` ${cls}` : ''}">${ic ? icon(ic) : ''}${esc(label)}</span>`;
}

export function statusGlass(status) {
  const [cls, label, ic] = STATUSES[status] || ['warn', status || '—', 'st-pending'];
  return glassPill(cls, label, ic);
}

export function verdictGlass(verdict) {
  const [cls, label, ic] = VERDICTS[verdict] || ['warn', verdict || '—', 'st-pending'];
  return glassPill(cls, label, ic);
}

export function tabsInit(scope) {
  const list = scope.querySelector('[role="tablist"]');
  if (!list || list.dataset.wired) return;
  list.dataset.wired = '1';
  const tabs = [...list.querySelectorAll('[role="tab"]')];
  function select(tab, focus) {
    tabs.forEach((t) => {
      const on = t === tab;
      t.setAttribute('aria-selected', String(on));
      t.tabIndex = on ? 0 : -1;
      const panel = scope.querySelector(`#${t.getAttribute('aria-controls')}`);
      if (panel) panel.hidden = !on;
    });
    if (focus) tab.focus();
  }
  tabs.forEach((tab, i) => {
    tab.addEventListener('click', () => select(tab, false));
    tab.addEventListener('keydown', (e) => {
      let j = null;
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') j = (i + 1) % tabs.length;
      else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') j = (i - 1 + tabs.length) % tabs.length;
      else if (e.key === 'Home') j = 0;
      else if (e.key === 'End') j = tabs.length - 1;
      else return;
      e.preventDefault();
      select(tabs[j], true);
    });
  });
  // Chips carry real hrefs (deep-linkable panel IDs) but must not
  // drive the hash router, so navigation is intercepted: select the
  // owning tab, then scroll the panel into view.
  scope.querySelectorAll('.wb-chips a[data-tab]').forEach((a) => {
    a.addEventListener('click', (e) => {
      e.preventDefault();
      const tab = scope.querySelector(`#${a.dataset.tab}`);
      if (tab) select(tab, false);
      const panel = scope.querySelector(a.getAttribute('href'));
      if (panel) panel.scrollIntoView({ block: 'start' });
    });
  });
}
