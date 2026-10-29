# Frontend Architecture — Research Console

Static multi-workspace console at `research/`. No framework, no
build step, no backend: ES modules fetch frozen evidence over HTTP
and render it. Source of truth stays in `artifacts/`,
`benchmarks/manifests/`, and `docs/` — the console duplicates
nothing and writes nothing.

## Routes

| Hash route | Workspace | Functionality |
|---|---|---|
| `#/command` | Command Center | Provisional/audited status, KPI cards (all link to evidence), constellation panel, derived findings, pending audits, run table |
| `#/map` | Constellation | Fullscreen evidence graph + text-alternative node list |
| `#/atlas` | Experiment Atlas | Run cards + episode explorer: search, run/scenario/baseline/outcome filters, sortable columns, pagination, URL-synced state, row → evidence |
| `#/observatory` | Evaluation Observatory | Split/scenario selectors, pooled success bars, false-success bars with Wilson whiskers, **Signal vs Uncertainty** (per-cell Wilson dot-plot when a scenario is selected, pooled otherwise, descriptive-only overlap note), latency table recomputed from durations, drill-down numbers table |
| `#/evidence/:run/:trial` | Evidence Inspector | Episode record, outcome explainer, P1–P3 table, **Episode Oscilloscope** (zoomable logic-analyzer lanes over trace/observer/verdict coordinates with detail panel), trace timeline with step filter (or replay driver report), snapshot, action log, joined human verdicts, backlinks |
| `#/failures` | Failure Cartography | Reading guide, split selector, **Failure Topography** (fault transect: discrete soundings at tested `slow_ms` levels, no interpolated boundaries, soundings table), per-baseline success heatmaps (click cell → filtered atlas), error-text groups, paginated non-success table |
| `#/recovery` | Recovery Studio | Honest bounded-failure inspection (terminal correctness, duration percentiles, retries), study episodes, PROPOSED-only future experiments — no simulation controls |
| `#/audit` | Audit & Reproducibility | Per-run audit status, plan/verdict counts with agree/disagree tallies, deferred mini-sample review queue, manifests, execution environments |
| `#/archive` | Research Archive | Rendered Markdown reports with verdict pills, run-file windows, plan inventory, manifest JSON viewer |
| `#/terrain` | Outcome Terrain | **A.** Condition landscape: uniform fault-aware tiles with per-trial dots (shape+color+edge encodings), split/baseline/scenario/highlight filters, cell inspection with mirror baseline |
| `#/river` | Evidence River | **B.** Scenario → baseline → outcome → cell-audit flow with exact per-transition counts, click-to-filter, full record-list alternative |
| `#/lineage` | Provenance Graph | **F.** Validated lineage for one run cell: manifest → run → cell → episodes → artifacts + verdict/plan/report nodes, identifier-checked edges, search, neighbor highlight, node/edge tables |
| `#/review` (+`/:run/:trial`) | Mini-review queue | Blinded 8-episode adjudication: masked recorded verdicts, two-phase verdict form (assess → reveal → agree), localStorage + export/import `decisions.json`, pending/reviewed status, human-vs-verifier summary with n=8 caveat. Console never writes repo files. |
| unknown | Not found | Recovery link back to Command Center |

## Structure

```
research/
  index.html          shell: sidebar nav, topbar, main, footer, scrim
  css/tokens.css      design tokens (color, type, spacing, radii, focus)
  css/app.css         layout, components, charts, pages, responsive, a11y
  js/app.js           hash router, nav, chrome, boot/loading sequence
  js/data.js          data layer: fetch, indexes, metrics, Wilson, filters
  js/components.js    pills, cards, tables, disclosures, Markdown, links
  js/charts.js        SVG charts + constellation graph (+ dotPlot,
                      faultTransect, scopeStrip builders)
  js/pages/*.js       one module per workspace (render + bind)
  js/viz/stats.js     pure math kit: Wilson, percentiles, positional
                      cell slicing, Sankey layout, nice steps
  js/viz/*Model.js    DOM-free data models per visualization
                      (river, fault soundings, oscilloscope lanes,
                      lineage graph) — unit-tested in Node
  js/viz/tooltip.js   shared accessible tooltip (caller-supplied text)
  js/viz/particles.js ambient Canvas field: dt-based, adaptive,
                      static under reduced motion / toggle
  **/*.test.mjs       Node stdlib tests (models + render smoke tests)
```

## Data flow

1. `data.js` fetches 4 run files, 2 manifests, 6 audit plans,
   2 audited runs, 3 reports with `Promise.allSettled`; failures
   are recorded per-file and pages render explicit empty states.
2. Episodes and cells are flattened once into indexes carrying
   their run/baseline/split context.
3. Episode detail (trace, snapshot, actions) is fetched lazily by
   the Evidence Inspector from artifact-relative paths resolved
   against the server root.
4. Human verdicts are joined read-only from plans by
   `runId::trialId`; agreement is recomputed for display from the
   stored verifier checks — never edited.
5. Cell→episode mapping for the new visualizations is positional
   (`sliceCells`, mirroring `benchmarks/audit.py`); any
   inconsistency fails closed with a banner instead of rendering.
6. The Provenance Graph checks artifact presence live (fetch
   status, no parsing) and draws only identifier-validated edges;
   uncited reports are omitted, mismatches render as invalid.

## Integrity rules (enforced in code, not prose)

- Unavailable metrics render as `null` with their recorded reason;
  denominators are always shown; zero is never substituted.
- Wilson upper bounds use the evaluation's 95% definition.
- Percentiles are recomputed from raw episode durations (pooling
  cell percentiles would be invalid).
- `failure_category` (always null from the runner) is disclosed;
  grouping uses outcomes and error text instead.
- Provisional vs audited status is computed from loaded files on
  every render; the word "provisional" appears wherever eval rates
  are shown. No verdict, audit, or experiment is ever fabricated.
- New-visualization rules: terrain tiles are uniform (no height or
  intensity encoding); river links count each episode exactly once
  per transition with harness errors as their own node; Wilson
  intervals are descriptive only (overlap is not significance);
  topography soundings are discrete stakes with no connecting lines;
  oscilloscope lanes never mix coordinates (trace seq, observer
  seq, step index, categorical); lineage edges state their check
  and fail visibly. Every chart has a table/list alternative and
  never relies on color alone.

## Design system

Dark instrument theme: graphite surfaces with a faint grid,
cyan primary focus, violet reserved for relationships/groupings,
green/amber/red reserved for outcome semantics. System font stack
(offline-safe), tabular numerals for data, visible focus rings,
`prefers-reduced-motion` support (ambient field renders one static
frame; strip/tile transitions are instant), text contrast ≥ 4.5:1.
A footer `Motion: on/off` toggle persists the ambient field state
(`chimera-motion`). Mobile: sidebar becomes an overlay drawer; the
constellation degrades to its node list; wide strips scroll
horizontally in place.
