# Implementation Status — Research Console

Date: 2026-10-29 (visual-intelligence layer completed 2026-10-30).
Definition of done: all 12 master-prompt criteria met (see
verification notes below).

## Completed

- 12 connected workspaces (Command, Constellation, Atlas,
  Observatory, Evidence, Failures, Recovery, Audit, Archive,
  Terrain, River, Provenance) + not-found route; every control
  performs its advertised function.
- Six signature visualizations over real evidence: (A) Outcome
  Terrain route, (B) Evidence River route, (C) Signal vs
  Uncertainty in the Observatory, (D) Failure Topography in
  Failures, (E) Episode Oscilloscope in Evidence, (F) Provenance
  Graph route — each with list/table alternatives, keyboard
  access, missing-data states, and fail-closed mapping.
- Real-data integration: 4 runs (524 episodes), 2 manifests,
  6 audit plans, 3 reports, on-demand traces/snapshots/action logs.
- Signature constellation: deterministic, clickable, keyboard
  accessible, deep-links into Atlas/Observatory/Audit; list
  fallback on small screens.
- Integrity preserved: nulls with reasons, denominators, Wilson
  bounds, provisional labeling, no fabricated audits/metrics;
  Recovery Studio is an honest inspection workspace (no fake
  simulation controls).
- Design system: tokens, responsive layout, focus management,
  reduced-motion support, ≥4.5:1 text contrast; restrained
  ambient particle field with persisted Motion toggle.
- 30 browser tests (16 original + 14 viz/review), all green,
  + 63 Node stdlib tests, all green; zero benchmark/product files
  changed; zero new dependencies.
- Eval mini-review prepared and finalized: frozen 8-episode
  packet with digest-verified evidence, enforced two-phase
  blinded queue (`#/review`), separate `decisions.json` store,
  `tools/mini_review.py` build/validate/bundle/reviewer-split,
  `evidence-bundle.zip` (29 verified originals),
  reviewer-safe packet + separate answer key, and
  `READY_FOR_REVIEW.md` — awaiting human adjudication (0/8).

## Route functionality (verified)

Command KPIs→evidence links; map select→panel→Open; atlas
search/filter/sort/paginate/row-navigation with URL sync;
observatory split/scenario selectors + drill-down + per-cell
Wilson signal view; evidence trace filter, disclosures, verdict
join + oscilloscope lanes/zoom/detail; failures heatmap
click-through + fault transect + paginated failure table;
recovery split selector + study links; audit review queue links;
archive report viewer (`?doc=`) + JSON disclosures; terrain
tiles/filters/cell inspection; river flows + record list;
lineage validated graph + search + tables. New-viz behavior is
verified by the Node suite against real evidence and by the
28/28 browser suite (approved unsandboxed run).

## Limitations

- Eval figures are provisional (0 eval verdicts; mini-sample
  review deferred) — stated on every surface that shows them.
- Static console: no live re-run capability by design (runs stay
  reproducible Python invocations, not buttons).
- See Frontend Test Plan for verification gaps.

## Next priorities (not started)

1. Adjudicate the 8-episode eval mini-sample in `#/review`
   (packet + queue ready, 0/8 recorded), export + validate
   `decisions.json` — then decide the apply/report follow-on
   separately; the console's audit surfaces update automatically.
2. Screen-reader pass over the new visualizations (landmarks
   and labels in place, unverified with assistive tech).
3. Failure-category support if the runner ever sets it.
4. Client-side caching/pagination of run JSON if evidence grows
   past comfortable fetch size.
