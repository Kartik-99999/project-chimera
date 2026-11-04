/* Constellation map: fullscreen evidence graph + text alternative. */
import { getState, auditStatus, esc } from '../data.js';
import { pageHead, emptyState, secHead } from '../components.js';
import { link } from '../app.js';
import { constellation } from '../charts.js';

export async function pageMap(el, { query }) {
  const s = getState();
  const runs = [...s.runs.values()].filter((r) => r.data);
  if (!runs.length) {
    el.innerHTML = pageHead('Constellation', [['Constellation']]) + emptyState(
      'No run evidence loaded', 'Serve the repository root and reload.');
    return;
  }
  const audits = runs.map((r) => {
    const a = auditStatus(r.runId);
    const tag = `${r.split === 'development' ? 'dev' : 'eval'}·${r.baseline === 'chimera' ? 'chimera' : 'replay'}`;
    return {
      runId: r.runId, state: a.state === 'audited' ? 'audited' : 'pending',
      label: a.state === 'audited' ? `✓ ${tag}` : `… ${tag}`,
      blurb: a.state === 'audited'
        ? `${a.auditedCells}/${a.cells} cells, ${a.agreed}/${a.episodes} agreed`
        : `${a.auditedCells}/${a.cells} cells adjudicated — provisional`,
    };
  });
  const q = query.q || '', kind = query.kind || '';
  const cons = constellation({ compact: false });
  el.innerHTML = pageHead('Constellation', [['Constellation']], '', {
    kicker: 'Routes #/map · #/atlas · #/evidence/:run/:trial',
    lede: 'Constellation for orientation, Atlas for search, Inspector for the single trial. Every row deep-links; every link carries its filter.',
    meta: `<span class="pill"><span class="dot"></span>${1 + runs.length * 2 + 4} nodes</span><span class="pill"><span class="dot"></span>${s.episodes.length} episodes indexed</span>`,
  })
    + secHead('Constellation', 'Select a node to inspect it, double-click to travel.')
    + `<div class="card"><p style="color:var(--ink-2)">Every node is real: runs, shared scenarios, and audit states drawn from loaded evidence. Select a node to inspect it, double-click (or use Open) to travel to its workspace. Run nodes link to filtered atlases; scenario nodes to the Observatory.</p>`
    + `<div class="map-tools" role="search">`
    + `<div class="field"><label for="map-q">Search nodes</label><input type="search" id="map-q" value="${esc(q)}" placeholder="run, scenario, audit…" autocomplete="off"></div>`
    + `<div class="field"><label for="map-kind">Category</label><select id="map-kind">`
    + [['', 'All categories'], ['run', 'Runs'], ['scenario', 'Scenarios'], ['audit', 'Audits']].map(([v, t]) => `<option value="${v}"${v === kind ? ' selected' : ''}>${t}</option>`).join('')
    + `</select></div><span class="map-count" data-map-count aria-live="polite"></span></div>`
    + cons.render({ runs, episodes: s.episodes, auditNodes: audits }) + `</div>`
    + `<details class="disclosure"><summary>Node list (text alternative)</summary><div class="body"><ul>`
    + runs.map((r) => `<li><a href="#/atlas?run=${encodeURIComponent(r.runId)}">${r.runId}</a> — ${(r.data.cells || []).length} cells, ${(r.data.episodes || []).length} episodes</li>`).join('')
    + ['S-NORM', 'S-SLOW', 'S-DIS', 'S-SLOWDIS'].map((sc) => `<li><a href="#/observatory?scenario=${sc}">${sc}</a> — shared scenario</li>`).join('')
    + `</ul></div></details>`;
  cons.bind(el);
  const apply = () => cons.filter(el, {
    q: el.querySelector('#map-q').value, kind: el.querySelector('#map-kind').value,
  });
  apply();
  let deb = 0;
  el.querySelector('#map-q').addEventListener('input', () => {
    clearTimeout(deb);
    deb = setTimeout(() => {
      apply();
      window.history.replaceState(null, '', link('map', [], { q: el.querySelector('#map-q').value, kind: el.querySelector('#map-kind').value }));
    }, 180);
  });
  el.querySelector('#map-kind').addEventListener('change', () => {
    apply();
    window.history.replaceState(null, '', link('map', [], { q: el.querySelector('#map-q').value, kind: el.querySelector('#map-kind').value }));
  });
}
