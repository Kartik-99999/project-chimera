/* Constellation map: fullscreen evidence graph + text alternative. */
import { getState, auditStatus } from '../data.js';
import { pageHead, emptyState } from '../components.js';
import { constellation } from '../charts.js';

export async function pageMap(el) {
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
  const cons = constellation({ compact: false });
  el.innerHTML = pageHead('Constellation', [['Constellation']])
    + `<div class="card"><p style="color:var(--ink-2)">Every node is real: runs, shared scenarios, and audit states drawn from loaded evidence. Select a node to inspect it, double-click (or use Open) to travel to its workspace. Run nodes link to filtered atlases; scenario nodes to the Observatory.</p>`
    + cons.render({ runs, episodes: s.episodes, auditNodes: audits }) + `</div>`
    + `<details class="disclosure"><summary>Node list (text alternative)</summary><div class="body"><ul>`
    + runs.map((r) => `<li><a href="#/atlas?run=${encodeURIComponent(r.runId)}">${r.runId}</a> — ${(r.data.cells || []).length} cells, ${(r.data.episodes || []).length} episodes</li>`).join('')
    + ['S-NORM', 'S-SLOW', 'S-DIS', 'S-SLOWDIS'].map((sc) => `<li><a href="#/observatory?scenario=${sc}">${sc}</a> — shared scenario</li>`).join('')
    + `</ul></div></details>`;
  cons.bind(el);
}
