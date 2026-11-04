/* Results: held-out matrix, terminal correctness, latency, matched-budget, Sauce v2. */
import { initShared } from '/site/nav.js';
import {
  loadRuns, loadManifests, renderHero, initSplitToggle, renderTerminal,
  renderLatency, renderMatchedBudget, renderSauceV2, paintLoadError,
} from '/site/figures.js';

initShared();
try {
  const runs = await loadRuns();
  const manifests = await loadManifests();
  renderHero(runs);
  initSplitToggle(runs, manifests);
  renderTerminal(runs);
  renderLatency(runs);
  await renderMatchedBudget();
  await renderSauceV2();
} catch (err) {
  paintLoadError(err, ['#matrix tbody', '#terminal-grid', '#latency-chart', '#mb-table', '#sauce-checks']);
}
