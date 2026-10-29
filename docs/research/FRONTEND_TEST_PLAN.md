# Frontend Test Plan — Research Console

## Automated browser suite (`tests/test_research_console.py`, 30 tests)

Serves the repo root via stdlib `http.server` on an ephemeral port
and drives Chromium (repo's existing Playwright). Status: **30/30
green**, executed 2026-10-29 in an approved unsandboxed run
(`.venv/bin/python -m pytest tests/test_research_console.py -q` →
`30 passed in 22.59s`). The run must stay outside the shell
sandbox (Chromium SIGSEGVs and sockets cannot bind inside it).
Intermittent infrastructure flakes have been observed and
addressed, not ignored: one transient recovery-sweep error
(passed alone and on repeat), and a cluster of lineage-test
failures traced to an occasionally dropped boot fetch (a 17-node
partial render with zero page errors) plus a stale-DOM race in
the test's own wait. Fixes: one boot-fetch retry in
`data.js` (persistent failures still surface in the footer),
deterministic polling waits in the test, and Node coverage for
both retry paths. Full file re-verified 30/30 after the fixes:

- **Route sweep (12):** every workspace renders its heading with the
  correct document title and **zero console errors / pageerrors**.
- **Unknown route:** `#/nope` renders the not-found page.
- **Figure fidelity (2):** Command Center KPIs and Observatory
  pooled k/n values asserted against run files read independently
  in Python; "provisional" wording asserted present.
- **Atlas deep link + navigation:** filtered URL shows the exact
  Python-computed row count; clicking a row lands on that trial's
  evidence page.
- **Evidence depth:** a dev-audited trial shows trace steps, P1–P3,
  snapshot fields, and the human agreement pill.
- **Constellation:** clicking the S-SLOW node then Open navigates to
  the Observatory with `scenario=S-SLOW` in the URL.
- **Mobile (390px):** hamburger opens nav, audit route works, node
  list is visible as the graph alternative.
- **Keyboard:** skip link focuses content without breaking hash
  routing (a real bug found and fixed), Tab reaches controls,
  Enter on a nav link navigates.
- **Terrain:** 36 tiles / 180 trials from the run files, tile click
  opens the inspection card, `?cell=` deep link renders the same card.
- **River:** per-transition denominators, list-row parity with links,
  segment click filters the Atlas.
- **Signal:** 30 per-cell rows for S-SLOW, Wilson tips, pooled k/n
  cards, descriptive-only wording.
- **Topography:** 24 soundings, fault-filter disclosure, sounding
  click reaches the Atlas with scenario+baseline.
- **Oscilloscope:** mark count from trace/action/verdict fixtures,
  zoom widens the strip, mark selection shows fields + source.
- **Provenance:** node/edge tables, node selection with neighbor
  dimming, search dimming without record loss.
- **Motion:** footer toggle flips label, persists `chimera-motion`,
  survives reload; reduced-motion context renders statically with
  no page errors.
- **Viz keyboard:** Enter on a river link navigates; Enter on a
  scope mark opens its detail.
- **Mini-review flow:** 8 pending items with masked summary,
  blinded assessment → reveal → agreement on a replay episode,
  queue/summary update, persistence across reload.

## Node suite (63 tests, stdlib only — green in this environment)

`node --test research/js/*.test.mjs research/js/viz/*.test.mjs
research/js/charts.test.mjs research/js/pages/*.render.test.mjs`
→ **63 passed, 0 failed**.
DOM-free models (`stats`, `riverModel`, `faultModel`,
`scopeModel`, `lineageModel`, `reviewModel`) are asserted against
the real frozen run/plan/report/packet files (denominators, joins,
decision rules, fail-closed mapping); boot fetch retry is covered
both ways (transient failure recovered, persistent failure
recorded);
page renderers run in Node with `fetch` stubbed to local files and
`app.js` stubbed (link-parity asserted), checking counts, banners,
tables, hrefs, and empty/missing paths. Every touched file also
passes `node --check`.

## Manual verification performed

- Screenshots reviewed for all 9 routes + filtered variants
  (docs set: `docs/research/img/`).
- Atlas: every filter, sort direction, both pagination buttons,
  Clear reset, empty-result state.
- Evidence: Chimera trace timeline + step filter, replay driver
  report shape, missing-artifact banners (paths render, no crash).
- Archive: all three reports render (tables verified visually).
- Text contrast computed for all foreground colors (lowest 5.61
  after fix; muted text raised from 4.02 to 6.36).
- Full repo suite green at console build time (see Implementation
  Status); this turn verified: 45/45 Node tests green, 28/28
  console browser tests green (approved unsandboxed run), 391
  non-browser Python tests pass. Remaining Python failures/errors
  elsewhere in the suite are the browser/socket sandbox blockade
  (Chromium SIGSEGV, bind denied), unrelated to these changes.
- Screenshots captured for all new routes/sections
  (`docs/research/img/`: terrain, terrain-detail, river,
  observatory-signal, failures-topography, evidence-scope,
  lineage, lineage-detail, review-queue, review-item) with zero
  page errors; river, lineage, topography, oscilloscope, and
  review shots reviewed in detail (counts cross-checked against
  run files).
- Mini-review tooling covered by `tests/test_mini_review.py`
  (9 tests: frozen-selection verification, determinism,
  fail-closed mutation cases, overwrite refusal, decision rules,
  evidence-drift detection, bundle determinism + damage refusal,
  reviewer-packet answer exclusion).
- The browser run caught two real bugs, both fixed and covered:
  a mobile-drawer stacking regression (scrim intercepted taps;
  fixed by moving `#scrim` inside `.shell`) and fragile
  `?cell=` key matching (now structural via
  `stats.matchCellKey`, unit-tested).

## Known gaps (not covered)

- No screen-reader pass (semantic landmarks and labels are in
  place but unverified with assistive tech).
- No persisted visual-regression baselines; screenshots are
  human-reviewed only.
- No performance profiling beyond local loads (~2–3 MB JSON,
  instant on localhost); no pagination stress beyond real data.
- `file://` opening is unsupported (fetch requires HTTP); the
  documented `http.server` command is the supported path.
- Reduced motion: global CSS kill-switch plus a static particle
  frame and a `prefers-reduced-motion`-aware scroll behavior are
  implemented and covered by a (not-yet-executed) emulation test,
  but no human pass under forced settings has been done.
