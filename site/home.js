/* Home: hero figures + dossier evidence table. Concise by design. */
import { initShared } from '/site/nav.js';
import { loadRuns, renderHero, renderCoverage, paintLoadError } from '/site/figures.js';

initShared();
try {
  const runs = await loadRuns();
  renderHero(runs);
  renderCoverage(runs);
} catch (err) {
  paintLoadError(err, []);
}
