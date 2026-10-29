"""Benchmark harness for Project Chimera.

This package holds the **harness**, not the product. Per
``docs/benchmark_design.md`` §6, harness artifacts (including the
Baseline A replay driver) must never be added to ``chimera/``.

Stage 1 provides the *contracts*:

- :mod:`benchmarks.manifest` — the versioned scenario/manifest schema,
  its validation, and its content hash.
- :mod:`benchmarks.results` — the versioned result schema, including
  the explicit representation of metrics that are **not measurable**.

Stage 2 adds the runner:

- :mod:`benchmarks.runner` — manifest → episodes → results file,
  including the AMB-9/ADR-005 refusal on policy divergence.

Stage 3 adds the independent verifier:

- :mod:`benchmarks.verifier` — exact-match P1–P3 evaluation from a
  harness-observed state snapshot, plus the §5 false-success
  classification. It imports no agent verification code.

Stage 4 adds the harness-side action observer:

- :mod:`benchmarks.observer` — Playwright-boundary recording of
  navigations and element interactions, judged against the scenario's
  permitted set. A benchmark-side control; it does not close the
  product's NFR-016 target-allowlist gap.

Baseline A adds the deterministic replay driver:

- :mod:`benchmarks.baseline_a` — fixed navigate/fill/click steps with
  no waiting, no retry, and no tracing, scored by the same verifier
  and observer. A harness artifact; it must never enter `chimera/`.

The verifier audit adds the procedure's mechanical half:

- :mod:`benchmarks.audit` — seeded sampling, evidence bundles, and
  verdict validation/aggregation. The human adjudication itself stays
  a human act.

The report template renders persisted runs into the specified report:

- :mod:`benchmarks.report` — run/audited files → Markdown (§11,
  evaluation §6): per-cell/per-baseline summary with Wilson bounds,
  not-measurable reasons, the audit verdict, failure breakdown,
  verbatim disclaimers/limitations, and artifacts. No benchmark run
  has been performed yet.

Baseline B is a later stage and is deliberately absent.

:mod:`benchmarks.manifest` and :mod:`benchmarks.results` import nothing
outside the standard library. :mod:`benchmarks.runner` couples to ``chimera.agent`` (for the AMB-9
policy check and the default executor) and ``chimera.safety`` (for the
per-episode cancellation token). ``chimera.agent`` is imported lazily
inside the functions that need it, so an uninspectable agent fails
closed with a clear error instead of at import time; no browser is
opened at import time.
"""

from __future__ import annotations

__all__ = ["manifest", "results", "runner", "verifier", "observer",
         "baseline_a", "audit", "report"]
