/* Evidence: coverage chain, human review, audit status, provenance. */
import { initShared } from '/site/nav.js';
import { loadRuns, renderHero, renderCoverage, renderAuditStatus, paintLoadError } from '/site/figures.js';

initShared();
try {
  const runs = await loadRuns();
  renderHero(runs);
  await renderCoverage(runs);
  await renderAuditStatus();
} catch (err) {
  paintLoadError(err, ['#coverage', '#review-facts', '#audit-status']);
}
