# Tooling Decisions — Research Console

Date: 2026-10-29. Scope: the `research/` browser console only. Outcome:
**zero new dependencies** — every capability below was evaluated and
either already existed in the repo or was hand-built where smaller
than any maintained alternative.

## Decision 1: static zero-dependency app (no framework, no bundler)

- **Problem:** serve an interactive multi-page console over frozen
  local JSON evidence (`artifacts/`, ~9 MB) with deep links.
- **Selected:** hand-written HTML/CSS/ES-module JavaScript under
  `research/`, served by the Python standard library
  (`python -m http.server`) for local use.
- **Why:** the data is static and frozen, so no backend, database, or
  build step is required; the repo has no JS toolchain
  (no `package.json`; verified) and Python 3.9 + Chromium already
  cover serving and testing. A framework would add hundreds of
  transitive packages to render local files.
- **License/compatibility:** no new code ships; everything runs from
  the repo. Requires only a static file server (documented).
- **Verification:** 12 routes registered; all load with zero
  console errors in Chromium (28/28 browser tests green in an
  approved unsandboxed run) plus Node render tests against the
  real evidence (45/45 green). Screenshots reviewed for the
  original routes and captured + sampled for the new ones
  (`docs/research/img/`).
- **Alternatives rejected:**
  - *Vite + React* — disproportionate toolchain for static JSON;
    build step buys nothing here.
  - *Streamlit* (repo skill available) — cannot deliver the custom
    constellation navigation, deep drill-down, or design-token
    system without fighting the framework; would also add a server
    dependency for static data.
  - *npm registry* was reachable (verified `npm ping`), but no
    package cleared the necessity bar, so none was installed.

## Decision 2: hand-rolled SVG charts and constellation

- **Problem:** grouped bars with Wilson whiskers, success heatmaps,
  latency bars, and a signature evidence graph.
- **Selected:** ~400 lines of purpose-built SVG in
  `research/js/charts.js` (nice-number axes, denominator labels,
  deterministic orbital layout, keyboard-accessible nodes plus a
  text-alternative node list).
- **Why:** the needed chart types are few and highly customized
  (k/n labels, whiskers, click-to-drill-down); d3 alone would exceed
  the hand-rolled size while still needing custom code, and a
  force-layout library would make the graph non-deterministic.
- **License/compatibility:** first-party code, no license to clear;
  no runtime network access.
- **Verification:** chart figures cross-checked against run files by
  independent Python assertions in the test suite; screenshots
  reviewed; `prefers-reduced-motion` honored (no animation at all).
- **Alternatives rejected:**
  - *d3.js* — would still require bespoke chart code; vendoring or
    CDN-loading it harms offline reproducibility for no gain.
  - *vis-network / cytoscape.js* — non-deterministic layouts and
    large footprints for a 13-node graph with a fixed better layout.
  - *Chart.js* — canvas rendering hurts the text/ARIA story and
    custom whisker/label needs.

## Decision 3: existing Playwright + pytest for console tests

- **Problem:** route, interaction, mobile, keyboard, and console-error
  verification of the console.
- **Selected:** repo's existing Playwright (Chromium already
  provisioned) driven from `tests/test_research_console.py` with a
  stdlib `http.server` thread fixture — the same pattern family as
  the existing browser tests.
- **Why:** zero installs, matches repo conventions, exercises the
  real served bytes including fetch paths and hash routing.
- **License/compatibility:** already a declared dev dependency.
- **Verification:** 28/28 green in an approved unsandboxed run
  (`28 passed in 19.79s`; the run must stay outside the shell
  sandbox, where Chromium SIGSEGVs). The 12 new visualization
  tests cover counts, drill-down, zoom, keyboard, and motion —
  and caught two real bugs (mobile-drawer stacking, `?cell=`
  key fragility), both fixed. Also used for the screenshot set
  in `docs/research/img/`.
- **Alternatives rejected:** `pytest-playwright` plugin and visual-
  regression services — unneeded machinery; screenshots are
  human-reviewed, not baselined (recorded as a gap).

## Decision 4 (revised): Node.js standard library for fast logic tests

- Node v24 is installed on this machine (verified). It is used only
  through the standard library (`node --test`, `node --check`):
  45 tests exercise the console's DOM-free data models and page
  renderers against the real frozen evidence, with `fetch` stubbed
  to local files. No `package.json`, no `node_modules`, no installs.
- **Why now:** the six signature visualizations concentrate their
  counting, slicing, and join logic in DOM-free modules
  (`research/js/viz/*Model.js`); testing that logic in-process is
  seconds-fast and independent of browser availability, while the
  Chromium suite keeps covering real rendering and interaction.
- **Verification:** `node --test research/js/viz/*.test.mjs
  research/js/charts.test.mjs research/js/pages/*.render.test.mjs`
  → 45 passed; every touched file also passes `node --check`.

## Decision 5: signature visualizations stay hand-rolled (no viz framework)

- **Problem:** six bespoke interactive visualizations (terrain,
  river, signal intervals, fault transect, oscilloscope strip,
  provenance graph) plus a restrained ambient particle field.
- **Selected:** hand-built SVG + one small Canvas 2D particle
  module (`research/js/viz/particles.js`), all DOM-free data models
  unit-tested in Node. No d3, no graph library, no chart framework.
- **Why:** each chart encodes console-specific integrity rules
  (positional cell slicing, fail-closed banners, explicit missing
  states, per-lane coordinates) that a framework would not supply;
  the largest dataset is 524 episodes, far below any GPU need; and
  SVG keeps every mark keyboard-focusable with `<title>` baselines
  plus table/list alternatives. Deterministic layouts keep tests
  stable.
- **License/compatibility:** first-party code, zero new
  dependencies, offline-safe.
- **Verification:** Node suite asserts denominators and joins
  against the real run files; browser suite (28 tests) asserts
  rendered counts, click-through, zoom, keyboard activation,
  motion toggle persistence, and reduced-motion rendering.
- **Alternatives rejected:**
  - *d3.js / vis-network / cytoscape.js* — same reasoning as
    Decision 2, now confirmed at larger scope: custom encodings,
    deterministic layout, no installs.
  - *Canvas/WebGL chart rendering* — rejected for data marks
    (hurts keyboard access and inspectability); Canvas is used
    only for the decorative ambient field, which renders a static
    frame under reduced motion or when toggled off.

## Standing rules applied

No `curl|sh` remote execution, no installs, no credentials touched,
no sandbox/TLS weakening, no pushes or external mutations. All
changes are project-local additive files under `research/`,
`tests/test_research_console.py`, and `docs/`.
