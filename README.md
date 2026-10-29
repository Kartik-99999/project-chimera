# Project Chimera

An **algorithm-first, deterministic** browser automation agent. No model
call, no randomness, no adaptive reasoning: the same input and
configuration produce the same terminal status.

This repository is at **Milestone 1 — project foundation**. It contains
a local demo app, a Playwright automation agent, and a 421-test suite
(83 application tests + 338 benchmark-harness tests: 90 contract tests,
41 runner tests, 41 verifier tests, 47 observer tests, 31 Baseline A
tests, 36 audit tests, 37 report tests, and 15 review-tool tests).

> The full setup, operation, and troubleshooting instructions are in
> **[`docs/user_guide.md`](docs/user_guide.md)**. This file is the entry
> point.

---

## What is implemented today

| Capability | What it means |
|---|---|
| **One deterministic workflow** | Create a project in the bundled demo app, with a verified outcome. |
| **Execution tracing** | Every run writes an ordered, timestamped JSON event log to `data/traces/<run_id>.json`. |
| **Failure screenshots** | A failed run captures a PNG of the page at `data/screenshots/<run_id>.png`. |
| **Cooperative cancellation** | A run can be asked to stop; it halts at a safe boundary and reports `status="cancelled"` — distinct from success and failure. |
| **Session isolation** | Each run gets its own browser process and its own `BrowserContext`; runs cannot observe each other's state. |
| **Bounded, honest failure** | Retries are bounded and refuse to repeat blindly; a failed run reports `status="failed"` with a diagnosable cause, and is never reported as a success. |
| **Deterministic fault injection** | `?slow=<ms>` (transient) and `?disabled=1` (persistent) reproduce page faults without randomness. |

Detailed behaviour and the design decisions behind each of these are in
[`docs/architecture.md`](docs/architecture.md) and [`docs/adr/`](docs/adr/).

---

## Setup

All commands below run **from the project root** (`project-chimera/`).

Verified against the repository's own environment: **Python 3.9.6**,
**Playwright 1.60.0**, **pytest 8.4.2**, macOS arm64. Python **3.9 is
the minimum**: `pyproject.toml` declares `requires-python = ">=3.9"`,
and the installed `playwright`, `pytest`, and `greenlet` all declare
`Requires-Python: >=3.9`.

The `.venv/` is already provisioned. To use it:

```bash
cd /Users/kartikbhardwaj/project-chimera
source .venv/bin/activate
```

To create it from scratch instead:

```bash
cd /Users/kartikbhardwaj/project-chimera
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m playwright install chromium
```

`requirements-dev.txt` and `pyproject.toml` declare the same dependency
ranges; `requirements-dev.txt` is the setup file and `pyproject.toml` is
the metadata file. Full instructions are in
[`docs/user_guide.md`](docs/user_guide.md).

---

## Run the agent

```bash
.venv/bin/python -m chimera.agent
# Success: 'My First Project' was created.
```

Or drive it from Python:

```python
from chimera.agent import create_project, create_project_with_faults

result = create_project("My First Project")
print(result["status"], result["trace_path"])

# With an injected fault:
result = create_project_with_faults("My First Project", slow_ms=2000)
```

## Run the tests

```bash
.venv/bin/python -m pytest -q                     # all 421 tests (~50 s)
.venv/bin/python -m pytest tests/test_safety.py tests/test_faults.py tests/test_tracing.py -q   # 62, no browser
.venv/bin/python -m pytest tests/test_agent.py tests/test_integration.py tests/test_verifier_browser.py tests/test_observer_browser.py tests/test_baseline_a_browser.py -q  # 30, needs Chromium
.venv/bin/python -m pytest tests/test_benchmark_manifest.py tests/test_benchmark_results.py tests/test_benchmark_runner.py tests/test_benchmark_verifier.py tests/test_benchmark_observer.py tests/test_baseline_a.py tests/test_audit.py tests/test_benchmark_report.py tests/test_audit_review.py -q # 329, no browser
```

## Inspect a run

```bash
ls -t data/traces/*.json | head -1 | xargs .venv/bin/python -m json.tool
open "$(ls -t data/screenshots/*.png | head -1)"
```

---

## Documentation

| Document | Purpose |
|---|---|
| **[`docs/user_guide.md`](docs/user_guide.md)** | Prerequisites, setup, running, traces, screenshots, fault scenarios, cancellation, troubleshooting. **Start here.** |
| [`docs/architecture.md`](docs/architecture.md) | Components, browser lifecycle, safety and retry boundary, data flow, implemented vs. planned. |
| [`docs/threat_model.md`](docs/threat_model.md) | Assets, trust boundaries, threats with their actual enforcement points, residual risks. |
| [`docs/adr/`](docs/adr/) | ADR-001 browser isolation · ADR-002 cooperative cancellation · ADR-003 trace persistence as a success precondition · ADR-004 requirement traceability · ADR-005 runner policy refusal. |
| [`docs/evaluation.md`](docs/evaluation.md) | Evaluation criteria, metrics, baselines, reporting rules, acceptance gates. |
| [`docs/benchmark_design.md`](docs/benchmark_design.md) | The benchmark: scenarios, manifests, independent verifier, trial protocol. **Run** — dev (16 cells × 5 trials) and held-out eval (36 cells × 5 trials) executions for Chimera and Baseline A; dev report audited at 100% agreement, eval report provisional pending the deferred human audit. |
| [`docs/evaluation_approaches.md`](docs/evaluation_approaches.md) | Survey of established browser-agent evaluation methods, with sources. |
| [`CURRENT_STATUS.md`](CURRENT_STATUS.md) | Measured state, what exists, the backlog, the next recommended task. |

---

## Research Console

An interactive 12-workspace console over the real benchmark
evidence — command overview, evidence constellation, experiment
explorer, evaluation charts, episode traces, failure maps, an
honest recovery study, audit status, the report archive, and
three visualization workspaces (Outcome Terrain, Evidence
River, Provenance Graph) plus Wilson signal views, a fault
transect, and an episode oscilloscope. It reads `artifacts/`
live, writes nothing, and labels every held-out figure
provisional. Details in
[`docs/research/FRONTEND_ARCHITECTURE.md`](docs/research/FRONTEND_ARCHITECTURE.md);
screenshots in `docs/research/img/`.

```bash
cd /Users/kartikbhardwaj/project-chimera
.venv/bin/python -m http.server 8123
# open http://127.0.0.1:8123/research/ in a browser
# console logic tests (no browser needed):
node --test research/js/*.test.mjs research/js/viz/*.test.mjs research/js/charts.test.mjs research/js/pages/*.render.test.mjs
# console browser tests (needs working Chromium + sockets):
.venv/bin/python -m pytest tests/test_research_console.py -q
```

## Limitations

**The current test suite is a regression suite, not proof of general
browser-agent performance.** Its tests show that specific behaviours
still work; no success rate, robustness figure, or generalisation
claim may be derived from them. The pytest suite holds 460 tests:
83 cover the agent, the safety layer, and the tracing layer; 338
cover the evaluation harness's *contracts, runner, verifier,
observer, Baseline A, audit tooling, report renderer, and review
tool*; 30 cover the research console in a browser; 9 cover the
eval mini-review packet tooling. A further 63 Node stdlib tests
cover the console's data models and renderers.
Measured benchmark numbers exist (see below), but the held-out
figures are provisional: no eval audit sample has been adjudicated.

- **Benchmark figures are provisional.** Dev runs (`dev-20261028-*`,
  16 cells × 5 trials × 2 baselines) and held-out eval runs
  (`eval-20261028-*`, 36 cells × 5 trials × 2 baselines) are complete
  with full trace/snapshot/action evidence under `artifacts/`; the dev
  report is audited at 100% agreement, while the eval report
  (`artifacts/eval-20261028/report.md`) is **PROVISIONAL** — no eval
  audit sample has been adjudicated (an 8-episode stratified sample is
  drawn and awaiting review). The observer is a benchmark-side
  detector, not a product safeguard: the agent's allowlist is still
  type-level only (NFR-016 half met). The §6 Baseline A prediction now
  holds at full-run rate level on both splits (replay succeeds only on
  `S-NORM`; Chimera additionally clears every `S-SLOW` cell), with zero
  measured false successes and zero harness errors — but eval rates
  stay provisional until audited. Passing audit-tooling tests say
  nothing about the verifier's accuracy on real episodes.
- **The action allowlist is type-level only.** It validates *which kinds*
  of browser operation may run (`navigate`, `fill`, `click`, `wait`,
  `observe`). It does **not** yet enforce URL, locator, or target
  allowlists — a named control is a planned safeguard, not an
  implemented one.
- **One workflow, one local target.** The demo app is a single local
  HTML file. Results do not transfer to other sites or workflows.
- **No recovery layer.** The agent waits and retries within a bounded
  budget; it does not learn or reuse recovery skills, and no recovery
  improvement is claimed.
- **No model integration.** There is no LLM in the execution path, so
  there is no model-driven baseline and no model cost to report.
- **Cancellation is cooperative, not immediate.** A cancel request is
  honoured at the next safe boundary; an action already in flight can
  delay the stop by up to ~5 s (the action timeout). See
  [ADR-002](docs/adr/ADR-002-cooperative-cancellation-at-safe-boundaries.md).
- **Not production-ready.** See
  [`docs/threat_model.md`](docs/threat_model.md) for the residual risks
  and the validation that would be required first.

**Requirement identifiers.** The SRS is the requirements authority. Note
that the project's internal label "FR-018" denotes *execution tracing*,
whereas **SRS FR-018** is *"use deterministic browser primitives"* —
different requirements. The crosswalk and six still-unresolved mapping
questions are in
[ADR-004](docs/adr/ADR-004-requirement-traceability-to-srs.md).

## License

No license has been chosen for this project yet.
