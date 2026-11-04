/* Demo: recorded traces only — journey strips + inspector from frozen files. */
import { initShared } from '/site/nav.js';
import { loadRuns, renderHero, loadDemoData, initDemo, paintLoadError } from '/site/figures.js';

initShared();
try {
  const runs = await loadRuns();
  renderHero(runs);
  const demoData = await loadDemoData(runs);
  initDemo(demoData);
} catch (err) {
  paintLoadError(err, []);
}
