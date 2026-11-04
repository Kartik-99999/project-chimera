/* Workflows: static catalog + hero figure tokens. No live data tables. */
import { initShared } from '/site/nav.js';
import { loadRuns, renderHero, paintLoadError } from '/site/figures.js';

initShared();
try {
  const runs = await loadRuns();
  renderHero(runs);
} catch (err) {
  paintLoadError(err, []);
}
