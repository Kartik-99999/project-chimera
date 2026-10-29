# Chimera User Guide

Setup, operation, and troubleshooting for Project Chimera at its current
milestone.

**Scope of this guide.** Everything described here is *implemented and
verified in this repository*. Planned but unbuilt capabilities are marked
as such and point at the planning documents rather than being presented
as working features. See §13 for the implemented-vs-planned table.

**Verified environment.** Every command in this guide was executed
against the repository's own `.venv`:

| Component | Version |
|---|---|
| Python | 3.9.6 (CPython, macOS arm64) |
| Playwright | 1.60.0 |
| pytest | 8.4.2 |
| pip | 26.0.1 |
| setuptools | 58.0.4 |

**Contents**

1. [What Chimera does](#1-what-chimera-does)
2. [Prerequisites](#2-prerequisites)
3. [The virtual environment](#3-the-virtual-environment)
4. [Installing dependencies and Chromium](#4-installing-dependencies-and-chromium)
5. [Repository layout](#5-repository-layout)
6. [Running the agent](#6-running-the-agent)
7. [Running the demo app](#7-running-the-demo-app)
8. [Fault scenarios](#8-fault-scenarios)
9. [Running the tests](#9-running-the-tests)
10. [Inspecting JSON traces](#10-inspecting-json-traces)
11. [Inspecting failure screenshots](#11-inspecting-failure-screenshots)
12. [Cancellation](#12-cancellation)
13. [Implemented vs. planned](#13-implemented-vs-planned)
14. [Configuration](#14-configuration)
15. [Reproducible evaluation commands](#15-reproducible-evaluation-commands)
16. [Troubleshooting](#16-troubleshooting)
17. [Related documents](#17-related-documents)

---

## 1. What Chimera does

Chimera is an **algorithm-first, deterministic** browser-automation
agent. "Deterministic" here means: no model call, no randomness, and no
adaptive reasoning. The same input and configuration produce the same
terminal status.

At the current milestone Chimera performs exactly one task — *create a
project in a local demo web application* — and does it with four
properties that are implemented and tested rather than asserted:

| Property | What it means in practice | Where it is specified |
|---|---|---|
| **Execution tracing** | Every run writes an ordered, timestamped JSON event log to `data/traces/`. | [`docs/architecture.md` §6](architecture.md), [ADR-003](adr/ADR-003-trace-persistence-precondition-for-success.md) |
| **Cooperative cancellation** | A run can be asked to stop; it stops at a safe boundary and reports `status="cancelled"`, distinct from success and failure. | [ADR-002](adr/ADR-002-cooperative-cancellation-at-safe-boundaries.md) |
| **Session isolation** | Each run gets its own browser process and its own `BrowserContext`; runs cannot observe each other's state. | [ADR-001](adr/ADR-001-per-run-browser-and-context-isolation.md) |
| **Honest reporting** | A run is not reported as successful unless its postconditions were verified *and* its trace was persisted. A failure is reported as a failure, with a diagnosable cause. | [ADR-003](adr/ADR-003-trace-persistence-precondition-for-success.md) |

The agent's own postcondition checks live in `chimera/agent.py`; the
*independent* verifier used for benchmark measurement is specified in
[`docs/benchmark_design.md`](benchmark_design.md) and is **not yet
built**.

---

## 2. Prerequisites

| Requirement | Detail |
|---|---|
| **OS** | macOS on Apple Silicon is the development platform of record (SRS NFR-027). The code is platform-neutral; no platform-specific calls exist in `chimera/`. |
| **Python** | **3.9 or newer.** `pyproject.toml` declares `requires-python = ">=3.9"`, and the installed `playwright`, `pytest`, and `greenlet` each declare `Requires-Python: >=3.9` — so 3.9 is the real floor, not a guess. The repository's `.venv` is 3.9.6 and the whole suite passes on it. |
| **Disk** | ~500 MB for the Playwright Chromium build and its cache. |
| **Network** | Needed **once**, to download dependencies and the Chromium build. The demo app and all tests run offline against `file://` URLs. |
| **Credentials** | None. Chimera reads no environment variables and needs no API key. There is no model integration yet (SRS §7.4 is a later phase). |

There is no paid-model dependency: SRS NFR-030 requires deterministic
workflows and evaluation tests to run without one, and the current
implementation satisfies that trivially because no model is involved.

---

## 3. The virtual environment

The repository ships with a `.venv/` at the project root, already
provisioned with the dependencies below. **Use it as-is; do not modify
it.**

```bash
cd /Users/kartikbhardwaj/project-chimera
source .venv/bin/activate
python --version      # Python 3.9.6
```

With the environment activated, `python`, `pip`, and `pytest` all resolve
to `.venv/bin/`. Every command in this guide is written in **explicit
path form** (e.g. `.venv/bin/pytest`) so it works whether or not you
activated the environment:

```bash
.venv/bin/python --version
.venv/bin/python -m pytest --version
```

To leave the environment: `deactivate`.

**If `.venv/` is missing or broken**, recreate it without touching the
system Python:

```bash
cd /Users/kartikbhardwaj/project-chimera
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m playwright install chromium
```

> **Note on the Python floor.** Python 3.9 is genuinely supported, not
> merely tolerated. The code uses `from __future__ import annotations`
> in `chimera/safety.py`, `chimera/tracing.py`, `benchmarks/manifest.py`,
> `benchmarks/results.py`, `benchmarks/runner.py`,
> `benchmarks/verifier.py`, `benchmarks/observer.py`,
> `benchmarks/baseline_a.py`, `benchmarks/audit.py`, and
> `benchmarks/report.py`, and the single `list[str]` annotation in
> `chimera/agent.py` is a *local variable*
> annotation, which is never evaluated at runtime. Python 3.9.6 runs
> the full 421-test suite, and the installed `playwright`, `pytest`, and
> `greenlet` all declare `Requires-Python: >=3.9`. (An earlier README
> claimed "Python 3.10 or newer"; that was wrong, and has been
> corrected.)

---

## 4. Installing dependencies and Chromium

Two separate steps: the Python packages, and the browser binary.

### 4.1 Python packages

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
```

`requirements-dev.txt` contains:

```
playwright>=1.40,<2.0
pytest>=7.4,<9.0
```

The same two constraints are declared in `pyproject.toml`
(`dependencies` and the `dev` extra) — see §14 for which file is
authoritative for what.

> **Verification note.** This install command was **not** executed during
> the most recent setup review — the environment already satisfies both
> constraints, and installing was out of scope. What *was* verified:
> `playwright` 1.60.0 and `pytest` 8.4.2 are installed, both satisfy
> the declared ranges, and the full 421-test suite passes.

### 4.2 Chromium

Playwright does **not** bundle a browser. The Chromium build is
downloaded separately:

```bash
.venv/bin/python -m playwright install chromium
```

This installs into the per-user Playwright cache, by default:

```
~/Library/Caches/ms-playwright/
```

To update an already-installed browser, re-run the same command — it is
idempotent and will fetch a newer build if one is needed.

To check the installation:

```bash
.venv/bin/python -m playwright --version
ls ~/Library/Caches/ms-playwright/
```

To see which build Playwright expects, without downloading anything:

```bash
.venv/bin/python -m playwright install --dry-run chromium
```

> **Verification note.** The install command itself was **not** executed
> during the most recent setup review, because the required build was
> already present and re-running it would attempt a network download.
> What *was* verified: `--dry-run` reports the expected build as
> `chromium-1223`, and `chromium-1223` is present in
> `~/Library/Caches/ms-playwright/`. The 21 browser tests pass against
> that build.

> Do **not** use `playwright install --with-deps` on macOS; the flag is
> for Linux system packages and is unnecessary on this platform.

---

## 5. Repository layout

```
project-chimera/
├── chimera/                 # the package
│   ├── __init__.py
│   ├── agent.py             # Playwright orchestration, URL builders, run entry
│   ├── safety.py            # action allowlist, retry policy, cancellation token
│   └── tracing.py           # trace recorder, failure screenshots
├── demo_app/
│   └── index.html           # the controlled test target (single file)
├── tests/
│   ├── test_safety.py       # 25 tests — stdlib only
│   ├── test_faults.py       # 17 tests — stdlib only
│   ├── test_tracing.py      # 20 tests — stdlib only
│   ├── test_agent.py        #  2 tests — browser
│   ├── test_integration.py  # 19 tests — browser
│   ├── test_benchmark_manifest.py  # 46 tests — stdlib only
│   ├── test_benchmark_results.py   # 44 tests — stdlib only
│   ├── test_benchmark_runner.py    # 41 tests — stdlib only
│   ├── test_benchmark_verifier.py  # 39 tests — stdlib only
│   ├── test_verifier_browser.py    #  2 tests — browser
│   ├── test_benchmark_observer.py  # 45 tests — stdlib only
│   ├── test_observer_browser.py    #  2 tests — browser
│   ├── test_baseline_a.py          # 26 tests — stdlib only
│   ├── test_baseline_a_browser.py  #  5 tests — browser
│   └── test_audit.py               # 28 tests — stdlib only
├── benchmarks/              # the evaluation harness (no Baseline B yet)
│   ├── manifest.py          # manifest schema, validation, content hash
│   ├── results.py           # result schema, metrics, false-success set
│   ├── runner.py            # manifest → episodes → results file
│   ├── verifier.py          # independent P1–P3 checks, false-success set
│   ├── observer.py          # Playwright-boundary action observation
│   ├── baseline_a.py        # deterministic replay driver
│   ├── audit.py             # verifier-audit sampling and verdicts
│   └── manifests/           # dev-v1.json, eval-v1.json
├── docs/
│   ├── architecture.md      # components, lifecycle, design decisions
│   ├── threat_model.md      # assets, trust boundaries, threats, residuals
│   ├── evaluation.md        # criteria, metrics, baselines, reporting rules
│   ├── benchmark_design.md  # the benchmark (audit/report not yet built)
│   ├── evaluation_approaches.md
│   ├── user_guide.md        # this file
│   └── adr/                 # ADR-001 … ADR-005
├── data/                    # generated at runtime, git-ignored
│   ├── traces/              # <run_id>.json
│   └── screenshots/         # <run_id>.png
├── .venv/
├── pyproject.toml           # project metadata + pytest configuration
├── requirements-dev.txt
├── .env.example             # documents that no env vars are read
├── .gitignore
├── README.md                # the entry point
└── CURRENT_STATUS.md        # measured state and backlog
```

`data/` is created on demand and is listed in `.gitignore`, along with
`artifacts/` and `.env`. Traces can capture page content — treat them
as sensitive and do not commit them.

---

## 6. Running the agent

### 6.1 The one-line entry point

```bash
.venv/bin/python -m chimera.agent
```

Verified output:

```
Success: 'My First Project' was created.
```

This runs the full workflow against the bundled demo app and writes a
trace to `data/traces/`.

### 6.2 From Python

The public API lives in `chimera.agent`:

```python
from chimera.agent import create_project, create_project_with_faults

result = create_project("My First Project")
print(result["success"], result["status"], result["trace_path"])
```

`create_project` accepts keyword-only options:

| Parameter | Default | Meaning |
|---|---|---|
| `url` | the bundled demo app | Target URL. |
| `trace_dir` | `data/traces/` | Where the JSON trace is written. |
| `cancel` | `None` | A `chimera.safety.CancellationToken`; see §12. |

`create_project_with_faults(project_name, *, slow_ms=0, disabled=False)`
is a convenience wrapper that builds the demo URL with fault parameters.
With both at their defaults the URL is identical to `get_demo_url()`.

### 6.3 The result dictionary

```python
{
    "success":    True,        # bool
    "cancelled":  False,       # bool
    "status":     "succeeded",  # "succeeded" | "failed" | "cancelled"
    "project_name": "My First Project",
    "error":      None,        # str when not successful
    "trace_path": "/abs/path/data/traces/<run_id>.json",
    "run_id":     "<uuid4>",
}
```

The three terminal statuses are distinct by design: a cancelled run is
never reported as a failure, and a failed run is never reported as a
success.

### 6.4 Running the agent from an async context

The Playwright **sync** API cannot be started inside a running asyncio
event loop. Calling `create_project()` from `async def` code, or from a
`pytest-asyncio` test, raises:

```
It looks like you are using Playwright Sync API inside the asyncio loop.
Please use the Async API instead.
```

The fix is to run the agent in a worker thread — the same pattern the
browser tests use:

```python
import concurrent.futures
from chimera.agent import create_project

with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
    result = pool.submit(create_project, "My First Project").result()
```

---

## 7. Running the demo app

The demo app is a single self-contained file with no server and no
network dependency.

**Open it in a browser:**

```bash
open demo_app/index.html
```

On Linux: `xdg-open demo_app/index.html`.

**Or serve it** (useful if you want to inspect it with devtools):

```bash
.venv/bin/python -m http.server 8000 --directory demo_app
# then browse to http://localhost:8000/index.html
```

Serving it changes the URL scheme from `file://` to `http://`, but the
agent's URL builders produce `file://` URLs by default. Both work; the
fault parameters behave identically.

**What the app does.** You type a project name and press *Create*. On
success it appends an `<li>` whose text is your trimmed name to
`#project-list` and shows the confirmation *"Project created
successfully!"*. It refuses to submit an empty name, and it refuses to
submit while the *Create* button is disabled. The *Reset* button clears
the list and clears any active fault.

The app also has two on-page fault controls: a *Slow load
milliseconds* number input and a *Disable Create button* checkbox. They
write the same state as the URL parameters, so you can drive faults
either way.

---

## 8. Fault scenarios

Faults are injected deterministically through URL parameters. There is
no randomness anywhere.

| Parameter | Meaning | Fault type |
|---|---|---|
| `?slow=<ms>` | The form is disabled for `<ms>` milliseconds, then re-enabled. | **Transient** — the wait layer should absorb it. |
| `?disabled=1` | The form stays disabled until *Reset* is pressed. | **Persistent** — no amount of waiting helps. |
| `?slow=<ms>&disabled=1` | Both. The persistent fault dominates. | **Persistent**. |

`?disabled=1` and `?disabled=true` are equivalent. A `slow` value of `0`
means no slow fault.

### 8.1 Driving faults from Python

```bash
.venv/bin/python -c "
from chimera.agent import create_project_with_faults
r = create_project_with_faults('Scenario Probe', slow_ms=2000, disabled=False)
print(r['status'], r['success'], r['error'])
"
```

### 8.2 Expected results (measured)

| Scenario | `status` | `success` | `error` |
|---|---|---|---|
| normal | `succeeded` | `True` | `None` |
| `slow=2000` | `succeeded` | `True` | `None` |
| `disabled=1` | `failed` | `False` | `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempts…` |
| `slow=2000` + `disabled=1` | `failed` | `False` | `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempts…` |

The transient case succeeds because the agent's action timeout and retry
policy outlast the 2 s delay. The persistent cases fail after the retry
budget is exhausted. The retry policy's `max_total_seconds = 5.0` is a
**wall-clock budget across all attempts of an action**, not a per-attempt
allowance — so a failing run takes roughly **5–6 s in total** (measured:
5.77 s for the `disabled=1` case, including browser start-up and
teardown), not 5 s per attempt.

### 8.3 Driving faults in a browser

```
file:///Users/kartikbhardwaj/project-chimera/demo_app/index.html?slow=2000
file:///Users/kartikbhardwaj/project-chimera/demo_app/index.html?disabled=1
```

To watch the slow fault from the UI, open the app, set *Slow load
milliseconds* to e.g. `3000`, and press *Create* — the form greys out
and recovers. To reproduce the persistent fault, tick *Disable Create
button*; the form stays grey until you press *Reset*.

---

## 9. Running the tests

The suite has 421 tests in three groups:

| Group | Files | Count | Needs a browser? | Runtime |
|---|---|---|---|---|
| **Standard library** | `test_safety.py`, `test_faults.py`, `test_tracing.py` | 62 | No | ~0.1 s |
| **Browser** | `test_agent.py`, `test_integration.py`, `test_verifier_browser.py`, `test_observer_browser.py`, `test_baseline_a_browser.py` | 30 | Yes | ~48 s |
| **Benchmark harness** | `test_benchmark_manifest.py`, `test_benchmark_results.py`, `test_benchmark_runner.py`, `test_benchmark_verifier.py`, `test_benchmark_observer.py`, `test_baseline_a.py`, `test_audit.py`, `test_benchmark_report.py`, `test_audit_review.py` | 329 | No | ~0.9 s |

The first two groups are the project's original regression baseline (83
tests) plus nine harness observation and baseline tests. The third
group tests the evaluation harness's *contracts, runner, verifier,
observer, Baseline A, audit tooling, report renderer, and review
tool* against fake executors and fixture traces; it is **not** a
benchmark run and produces no performance number. Separately, real
benchmark runs exist under `artifacts/` (dev audited, eval
provisional — see §15).

### 9.1 The whole suite

```bash
.venv/bin/python -m pytest -q
```

Verified: `421 passed in 50.02s`.

### 9.2 The standard-library group

```bash
.venv/bin/python -m pytest tests/test_safety.py tests/test_faults.py tests/test_tracing.py -q
```

Verified: `62 passed in 0.12s`. These also run under plain `unittest`,
which needs no pytest at all:

```bash
.venv/bin/python -m unittest tests.test_safety tests.test_faults tests.test_tracing -v
```

Verified: `Ran 62 tests … OK`.

### 9.3 The browser group

```bash
.venv/bin/python -m pytest tests/test_agent.py tests/test_integration.py tests/test_verifier_browser.py tests/test_observer_browser.py tests/test_baseline_a_browser.py -q
```

Verified: `30 passed in 48.26s`. This group launches a real Chromium, so
it needs the Chromium install from §4.2.

### 9.4 The benchmark-harness group

```bash
.venv/bin/python -m pytest tests/test_benchmark_manifest.py tests/test_benchmark_results.py tests/test_benchmark_runner.py tests/test_benchmark_verifier.py tests/test_benchmark_observer.py tests/test_baseline_a.py tests/test_audit.py tests/test_benchmark_report.py tests/test_audit_review.py -q
```

Verified: `329 passed in 0.91s`. These open no browser, so they are as
fast as the standard-library group. (Unlike the contract tests, the
runner tests do import the first-party `chimera.agent` and
`chimera.safety` modules — to exercise the live AMB-9 policy check —
but no third-party package. The verifier and observer tests
additionally drive `chimera.agent.create_project` through a fake
in-memory Playwright module, still with no browser. The Baseline A
tests drive the replay driver through fake pages the same way. The
audit tests run the real runner against fake executors that write
real files, still with no browser. The report tests render the real
runner's fixture output — including audited runs — through the real
renderer, still with no browser. The review-tool tests drive the
audit review CLI with scripted answers against plan copies, still
with no browser.)

### 9.5 What each file covers

| File | Covers |
|---|---|
| `test_safety.py` | The action allowlist, `RetryPolicy` bounds, `BlindRetryRefusedError`, `RetryBudgetExhaustedError`, `RunCancelledError`, and `CancellationToken` semantics. |
| `test_faults.py` | Fault-parameter construction (`?slow=`, `?disabled=`) and the URL builders. |
| `test_tracing.py` | Trace schema, monotonic sequence numbers, timestamp format, atomic write, `TraceWriteError` handling, and failure-screenshot capture. |
| `test_agent.py` | The agent's own end-to-end happy path and its result contract. |
| `test_integration.py` | Browser-level behaviour: session isolation, the slow and disabled fault paths, cancellation, and trace persistence against a live Chromium. |
| `test_benchmark_manifest.py` | The evaluation manifest contract: schema validation, the development/evaluation split discipline, and the content hash. |
| `test_benchmark_results.py` | The evaluation result contract: metric representation, the four outcomes, verification evidence, and false-success detection. |
| `test_benchmark_runner.py` | The benchmark runner: manifest loading, deterministic ordering, per-episode isolation, the AMB-9 policy refusal, timeouts, persistence, integrity failures, and unavailable-metric reasons — all against fake executors. |
| `test_benchmark_verifier.py` | The independent verifier: the snapshot schema, exact-match P1–P3, fail-closed evidence handling, false-success classification, runner wiring, import independence, and the agent's `observe` seam via a fake Playwright module. |
| `test_verifier_browser.py` | Harness observation against the real demo app: snapshot capture and P1–P3 evaluation on a success and a persistent-fault episode. |
| `test_benchmark_observer.py` | The action observer: the scenario policy, the action-log schema, fail-closed evaluation, the recording proxies against fake pages, runner wiring, the `browser_factory` seam via a fake Playwright module, and import independence. |
| `test_observer_browser.py` | Playwright-boundary observation against the real demo app: the exact action sequence and zero measured violations on a success and a persistent-fault episode. |
| `test_baseline_a.py` | The replay driver: the driver-report schema, fixed steps against fake pages (success, failure, single attempts, fixed timeout, cancellation, determinism), runner wiring, manifest/policy constraints, and harness-only placement. |
| `test_baseline_a_browser.py` | Baseline A against the real demo app: the §6 prediction on all four fault scenarios plus a two-cell runner run end to end. |
| `test_audit.py` | The verifier-audit tooling: seeded sampling (including targeted/limited samples), fault-aware cell identity, evidence bundles, strict agreement, malformed-verdict and tamper refusal, cell integration, and dev/eval separation — all against runner-produced fixture files. |
| `test_benchmark_report.py` | The report renderer: the Wilson bound against the §4.3 reference values, every §6.1 section, multi-run/multi-baseline reports, audit states, audit-coverage disclosure, unavailable-metric reasons, integrity refusals, determinism, privacy exclusion, verbatim drift against `evaluation.md`, and the §6.4 prohibited-claims guard — all against runner-produced fixture files. |
| `test_audit_review.py` | The guided review CLI: blind judging, strict booleans, verdict-only saves, quit/resume progress, and evidence safety — all with scripted answers against plan copies. |

### 9.6 Running a single test

```bash
.venv/bin/python -m pytest tests/test_integration.py -v -k "browser_context or session_state"
.venv/bin/python -m pytest "tests/test_safety.py::AllowlistTests" -v
```

### 9.7 Test configuration

`pyproject.toml` holds the pytest configuration:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

`pythonpath = ["."]` makes `import chimera` resolve no matter which
directory pytest is invoked from. `testpaths` means a bare `pytest` run
collects only `tests/`.

---

## 10. Inspecting JSON traces

Every run writes `data/traces/<run_id>.json`. The file is a single JSON
object:

```json
{
  "schema_version": 1,
  "agent_version": "milestone-1-foundation",
  "run_id": "086f75c9-a675-45b1-9798-e7466d4b2a62",
  "started_at": "2026-10-24T05:24:43.445Z",
  "completed_at": "2026-10-24T05:24:48.722Z",
  "terminal_status": "failed",
  "event_count": 6,
  "events": [ ... ]
}
```

| Field | Meaning |
|---|---|
| `schema_version` | Trace schema version (`1`). |
| `agent_version` | Version of the agent that produced the trace. |
| `run_id` | UUID4; also the stem of the trace filename and the screenshot filename. |
| `started_at` / `completed_at` | UTC ISO-8601 with millisecond precision and a `Z` suffix. |
| `terminal_status` | `succeeded`, `failed`, or `cancelled`. |
| `event_count` | Number of events; equal to `len(events)`. |
| `events` | The ordered event log (below). |

**Each event** carries `sequence_number` (monotonic, 1-indexed),
`timestamp`, `event_type`, `action_type`, `action_outcome`,
`error_details`, and `evidence_references`.

| `event_type` | Meaning |
|---|---|
| `run_started` | The run began; `evidence_references` holds the target URL. |
| `action_attempted` | An allowlisted action is about to run. |
| `action_succeeded` | The action completed. |
| `action_failed` | The action failed; `error_details` holds the cause chain. |
| `run_succeeded` | Terminal event for a successful run. |
| `run_failed` | Terminal event for a failed run. |
| `run_cancelled` | Terminal event for a cancelled run. |

`action_outcome` is `ok`, `failure`, or `cancelled`. `error_details` is
`null` unless the event failed.

**A real failed trace** (`?disabled=1`), read from a run in this
repository:

```
1 run_started  | outcome=ok      | action=None
2 action_attempted | outcome=ok  | action=navigate
3 action_succeeded | outcome=ok  | action=navigate
4 action_attempted | outcome=ok  | action=fill
5 action_failed| outcome=failure | action=fill
6 run_failed   | outcome=failure | action=None
```

### Reading a trace

```bash
# Most recent trace, pretty-printed
.venv/bin/python -m json.tool "$(ls -t data/traces/*.json | head -1)"

# Terminal status and event list of every trace
.venv/bin/python -c "
import glob, json, os
for p in sorted(glob.glob('data/traces/*.json'), key=os.path.getmtime):
    d = json.load(open(p))
    print(os.path.basename(p), d['terminal_status'], d['event_count'])
"
```

### Trace-writing guarantees

- The write is **atomic**: the recorder writes to a temporary file in
  the same directory and then `os.replace()`s it into position, so a
  reader never sees a half-written trace.
- If the write fails, the run is **not** reported as successful. It is
  downgraded to `status="failed"`, `success=False`, `cancelled=False`,
  with `trace_path=None` and the `TraceWriteError` in `error`. This is
  a deliberate design decision, recorded in
  [ADR-003](adr/ADR-003-trace-persistence-precondition-for-success.md):
  *a run whose evidence could not be persisted is not a successful run.*

---

## 11. Inspecting failure screenshots

On a **failed** run, a PNG screenshot of the page is written to
`data/screenshots/<run_id>.png` and attached as evidence on the failing
event.

```bash
ls -lt data/screenshots/ | head
open "$(ls -t data/screenshots/*.png | head -1)"
```

The screenshot filename matches the trace's `run_id`, so you can pair
them directly:

```bash
.venv/bin/python -c "
import glob, json, os
t = sorted(glob.glob('data/traces/*.json'), key=os.path.getmtime)[-1]
rid = json.load(open(t))['run_id']
shot = f'data/screenshots/{rid}.png'
print(shot, 'exists' if os.path.exists(shot) else 'no screenshot (run did not fail)')
"
```

**Scope limits, stated plainly:**

- Screenshots are captured for **failures only**. A successful run and a
  **cancelled** run produce no screenshot — a cancellation is not a
  failure. (Verified: a cancelled run produced a trace with
  `terminal_status: "cancelled"` and no PNG.)
- Screenshots capture whatever was on the page, which may include data
  you did not intend to expose. They are git-ignored for that reason.
- The screenshot is evidence of *page state at failure time*. It is not
  a proof of success — only the trace's verification events are.

---

## 12. Cancellation

Cancellation is **cooperative**: the run is asked to stop and stops at
the next safe execution boundary. It is not a forced interruption.

### 12.1 Requesting cancellation

```python
import threading
from chimera.agent import create_project, get_demo_url_with_faults
from chimera.safety import CancellationToken

token = CancellationToken()
threading.Timer(1.0, lambda: token.request("user requested stop")).start()

result = create_project(
    "Cancelled Project",
    url=get_demo_url_with_faults(slow_ms=3000),
    cancel=token,
)
print(result["status"], result["cancelled"], result["error"])
```

Verified output:

```
cancelled True RunCancelledError: user requested stop
```

The token is safe to call `request()` on from any thread: it is a flag
plus a `threading.Event`, and the agent only *reads* it from its own
thread. `request()` is idempotent, and the first reason wins.

### 12.2 How it behaves

- The agent checks the token at **five safe boundaries**: before each
  action, inside the retry loop, and before verification.
- On cancellation the agent raises `RunCancelledError`, closes the
  browser context and the browser, writes a trace whose
  `terminal_status` is `cancelled` with a `run_cancelled` terminal
  event, and returns `status="cancelled"`, `cancelled=True`.
- A cancelled run is **not** a failure and **not** a success. It is its
  own terminal state.

### 12.3 The limitation you must know about

**Cancellation cannot interrupt a synchronous Playwright action that is
already in flight.** The Playwright sync API is driven from the agent's
own thread; interrupting it from another thread would mean mutating
Playwright state from an unrelated thread, which is not safe. So the
agent can only *observe* the flag between actions.

The practical consequence, measured in this repository:

```
cancel requested at t = 1.0 s
slow=3000 page load still in flight
run actually stopped at t ≈ 3.6 s
```

The worst case is bounded by the action timeout, which is
`ACTION_TIMEOUT_MS = 5 000` ms (derived from the retry policy's
`max_total_seconds = 5.0`). **A cancellation request can therefore be
delayed by up to ~5 s.** This trade-off is recorded in
[ADR-002](adr/ADR-002-cooperative-cancellation-at-safe-boundaries.md).

Design implication: to cancel promptly, the run must be spending its
time in *waiting for the page* — which is exactly when a human wants to
cancel. A request made during a long in-flight action is honoured late.

---

## 13. Implemented vs. planned

| Capability | Status |
|---|---|
| Single hard-coded workflow (create a project in the demo app) | **Implemented** |
| Deterministic URL builders with fault parameters | **Implemented** |
| Playwright execution with an allowlisted action set | **Implemented** |
| Bounded retry with a total time budget; refusal of blind retries | **Implemented** |
| JSON execution trace, atomic write, schema versioned | **Implemented** |
| Failure screenshots | **Implemented** |
| Cooperative cancellation with a distinct terminal status | **Implemented** |
| Per-run browser and `BrowserContext` isolation | **Implemented** |
| Independent postcondition verification (as a *separate* component) | **Implemented** — `benchmarks/verifier.py` evaluates P1–P3 from a harness-observed snapshot; the verifier-*audit* tooling exists (`benchmarks/audit.py`, §15.1), the dev sample is adjudicated at 100% agreement, and the eval sample awaits deferred human review |
| Action allowlist restricted to specific URLs, locators, or targets | **Not implemented** — the allowlist is **type-level only** |
| Recovery from transient faults beyond waiting | **Not implemented** |
| Multi-task / multi-step workflows | **Not implemented** |
| Persistence of created projects beyond the demo app's in-memory list | **Not implemented** |
| Model-driven execution (Baseline B) | **Not implemented** — no model adapter exists |
| Dashboard, API server, database | **Not implemented** (SRS §14 stack) |
| Automated benchmark harness and report generation | **Implemented and run** — the harness's *contracts*, *runner*, *independent verifier*, *action observer*, *Baseline A*, *verifier-audit tooling*, *report renderer*, and *review tool* exist (338 tests, §15.1–§15.2). Dev and held-out eval runs are complete under `artifacts/`; the dev report is audited, the eval report is provisional pending deferred human review — see [`docs/benchmark_design.md`](benchmark_design.md) §13 |
| Environment-variable configuration | **Not implemented** — Chimera reads no environment variables; policy is in code. See §14. |

The "Not implemented" rows are planning targets, not defects. The
authoritative plan is in `CURRENT_STATUS.md`; the capability
requirements are in the SRS.

---

## 14. Configuration

### 14.1 There is currently no environment configuration

Chimera reads **no** environment variables. Nothing in `chimera/`,
`tests/`, or `demo_app/` calls `os.environ` or `os.getenv`, and there is
no dotenv loader. `.env.example` therefore documents no settings — it
exists so that the configuration surface is explicit and reviewable
rather than implicit, and to satisfy SRS NFR-025 and the repository
layout in SRS §16.

When a variable is added later, the four required steps are listed in
`.env.example` itself: declare it with a placeholder, read it with a
documented default, document it here, and never commit the value.

`.env` itself is excluded by `.gitignore` (`.env`, `.env.*`, with
`!.env.example` re-included), so a local override file can never be
committed by accident. `.env.example` is tracked and holds placeholders
only.

### 14.2 Where the tunables actually live

| Setting | Location | Current value |
|---|---|---|
| Retry attempts, base delay, max delay, total budget | `chimera/agent.py` → `DEFAULT_POLICY`; `chimera/safety.py` → `RetryPolicy` | 2 attempts, 50 ms base, 200 ms max, 5 s total |
| Per-action timeout | `chimera/agent.py` → `ACTION_TIMEOUT_MS` | 5 000 ms (derived from the 5 s total budget) |
| Trace output directory | `chimera/agent.py` → `DEFAULT_TRACE_DIR` | `data/traces/` |
| Screenshot output directory | `chimera/agent.py` → `DEFAULT_SCREENSHOT_DIR` | `data/screenshots/` |
| Allowed action types | `chimera/safety.py` → `ALLOWED_ACTIONS` | `navigate`, `fill`, `click`, `wait`, `observe` (type-level only) |
| Target URL | `chimera/agent.py` → `DEMO_APP_PATH`, `get_demo_url()` | the bundled `demo_app/index.html` |

### 14.3 Which file is authoritative

| File | Authoritative for | Not authoritative for |
|---|---|---|
| `pyproject.toml` | Package metadata, the `requires-python` floor, declared dependency ranges, the `dev` extra, the pytest configuration. | The exact pinned versions in the working environment. |
| `requirements-dev.txt` | The quick-setup dependency list used by `pip install -r`. | Package metadata and pytest configuration. |

The **dependency version ranges are identical** in both files
(`playwright>=1.40,<2.0`, `pytest>=7.4,<9.0`), and they are kept that
way deliberately. `requirements-dev.txt` is the file to run for setup;
`pyproject.toml` is the file to read for metadata. Neither pins an
exact version, and the exact versions in use are recorded in §2.

**Installing the package itself is optional.** Chimera runs directly
from the source tree — every command in this guide works without
installing it. `pyproject.toml` declares the standard setuptools
backend (`setuptools>=61`, which PEP 621 metadata requires) so that
`pip install -e ".[dev]"` is available if you want it. The working
environment's setuptools is 58.0.4, which is below that floor; pip
builds in an isolated environment and fetches a suitable setuptools, so
the existing `.venv` is **not** modified by installing the package.

> **Verification note.** `pip install -e .` was **not** executed — it
> would modify the working environment, which is out of scope for this
> review. What *was* verified: `pyproject.toml` parses as valid TOML
> and every declared field has the expected value.

---

## 15. Reproducible evaluation commands

SRS NFR-026 requires the repository to include reproducible evaluation
commands. **The state of that requirement today:**

- **Available now:** the regression suite (§9). It is reproducible, and
  it is a *regression* suite — it demonstrates that specific behaviours
  still work. It is **not** evidence of general browser-agent
  performance, and no success rate may be derived from it.
- **Available now:** the scenario probe in §8.1, which produces
  measurable terminal statuses for the four fault scenarios. The
  expected values are recorded in §8.2, so a reader can reproduce them
  and compare.
- **Available now, run:** the automated benchmark harness with a
  development/evaluation manifest split, a runner, an independent
  verifier, an action observer, Baseline A, the verifier-audit
  procedure, the report renderer, and the review tool (§15.1–§15.2).
  The harness's *contracts*, *runner*, *verifier*, *observer*,
  *replay driver*, *audit tooling*, *report renderer*, and *review
  tool* exist (`benchmarks/manifest.py`, `benchmarks/results.py`,
  `benchmarks/runner.py`, `benchmarks/verifier.py`,
  `benchmarks/observer.py`, `benchmarks/baseline_a.py`,
  `benchmarks/audit.py`, `benchmarks/report.py`,
  `tools/audit_review.py`, the `dev-v1.json` and `eval-v1.json`
  manifests, and their 338 tests). Dev runs (`dev-20261028-*`) and
  held-out eval runs (`eval-20261028-*`) are complete with full
  evidence under `artifacts/`; the dev report is audited at 100%
  agreement and the eval report is **PROVISIONAL** (no eval sample
  adjudicated yet). The observer is a benchmark-side detector, not a
  product safeguard: the agent's allowlist remains type-level only.
  The design is fully specified in
  [`docs/benchmark_design.md`](benchmark_design.md) and
  [`docs/evaluation.md`](evaluation.md). Only the rendered reports'
  figures may be cited, each with its provisional/audited status.

A reproducible, machine-readable snapshot of the current measurement
baseline is `CURRENT_STATUS.md`.

### 15.1 Auditing a run (verifier audit, design §5)

Before any rate is published, a human adjudicates a sample of the
run's episodes (§5). The tooling draws the sample and checks the
paperwork; the judgments stay human:

1. **Draw the sample** (2 episodes per cell here — the size is the
   auditor's choice and is recorded, not defaulted):
   ```bash
   .venv/bin/python -c "
   from benchmarks.audit import plan_audit
   plan_audit('run.json', 'benchmarks/manifests/dev-v1.json', 2,
              'run.audit-plan.json', auditor='your-name')"
   ```
   Sampling is a seeded permutation per cell (default seed derived
   from the run ID, recorded in the plan), over measured episodes
   only — warm-ups are never sampled. Episodes with incomplete
   evidence are skipped with reasons; asking for more than exist
   fails instead of silently capping. For a reduced workload,
   `plan_targeted_audit` samples only named cells (fault-aware keys);
   untargeted cells ride as empty samples and stay unaudited at
   apply time — the eval `*.audit-plan-mini.json` plans (4 episodes
   per baseline, one per scenario) were drawn this way.
2. **Adjudicate.** For each sampled episode, open its evidence bundle
   (trace or driver report, state snapshot, expected stored name —
   paths and digests are in the plan) and decide the verifier's P1–P3
   yourself. Record `{"checks": {"P1": …, "P2": …, "P3": …}}` per
   episode in the plan's `verdicts`, or `{"verdict": "unauditable",
   "reason": …}` when the evidence cannot support a judgment. Judge
   only the verifier's postcondition decisions; action-observer
   evidence is listed for completeness and plays no part. The guided
   review tool (`tools/audit_review.py`, tested in
   `tests/test_audit_review.py`) walks every sampled episode, hides
   the verifier's checks until you judge, validates each answer, and
   saves only `verdicts` — launch it as shown at the top of its
   docstring; `q` quits with progress saved and re-launching resumes.
3. **Apply the verdicts:**
   ```bash
   .venv/bin/python -c "
   from benchmarks.audit import apply_audit
   apply_audit('run.json', 'run.audit-plan.json', 'run.audited.json')"
   ```
   This validates every verdict (exact coverage, strict booleans,
   full check sets, evidence bytes unchanged since planning) and
   writes a new run file with each cell's `verifier_audit` filled as
   `{sampled, agreed, agreement_rate}`. Agreement is strict per-check
   equality. The input run file is never modified.
4. **Read the rate.** Below 95% agreement the run's rates are
   **provisional** and the disagreement cases are published (§5).
   `benchmarks.audit.is_provisional` is the rule's single
   implementation; the report stage (§15.2) applies it.

### 15.1.1 Eval mini-review packet (8 episodes, human gate)

The held-out eval runs carry a frozen 4+4 mini-sample (one episode
per scenario per baseline; see `artifacts/eval-20261028/
mini-review/PACKET.md` for the exact trial IDs). The review packet
is built and checked without touching frozen evidence:

```bash
.venv/bin/python tools/mini_review.py build-packet   # verifies digests, IDs, manifest sha
.venv/bin/python tools/mini_review.py validate       # checks decisions.json + freshness
```

Adjudicate in the console's **Mini-review queue** (`#/review`):
judge each episode's postconditions with the recorded verdict
masked, record assessment/sufficiency/reason, reveal, then judge
agreement. Phase order is enforced (no reveal control exists
until the assessment is saved). Blinding is partial (run IDs
stay visible for evidence lookup; trace shape differs by
driver) and the protocol timestamps prove the order. Decisions
export to `decisions.json` — stored separately from plans and
runs, with reviewer, timestamps, and a corrections history.
Validate the exported file with the command above. Eight
episodes describe only themselves: no reliability claim, and
the 95% rule applies to full audits, not this sample.
The audit is not complete until a human records all 8.

Finalize the distributable evidence with:

```bash
.venv/bin/python tools/mini_review.py build-bundle            # evidence-bundle.zip: 29 verified originals + manifest
.venv/bin/python tools/mini_review.py build-reviewer-packet   # reviewer-packet.json + separate answer-key.json
```

The reviewer-safe packet keeps stable episode references and
all P1–P3 evidence but excludes recorded outcomes, verifier
decisions, verdicts, and assessments (scan-enforced at build).
No cryptographic blinding is claimed: the console serves over
static HTTP, so anything served to the browser is inspectable.
For an independent review, distribute `reviewer-packet.json`
plus the evidence files only — withhold `answer-key.json`,
`packet.json`, `PACKET.md`, the mini plans (their sampled
entries record outcomes/checks), and `decisions.json` until
initial decisions are locked. Reviewer procedure:
`artifacts/eval-20261028/mini-review/READY_FOR_REVIEW.md`.

### 15.2 Rendering a report (design §11, evaluation §6)

`benchmarks/report.py` renders persisted run files — optionally
audited, optionally several baselines — into the specified Markdown
report. It reports only what the evidence supports: unavailable
metrics keep their reasons and are never zero, zero false-success
counts carry 95% Wilson upper bounds, and unaudited or
sub-95%-agreement cells make the report provisional.

```bash
.venv/bin/python -c "
from benchmarks.report import render_report
print(render_report(['run.audited.json'],
                    manifest_paths=['benchmarks/manifests/dev-v1.json'],
                    audit_plan_paths=['run.audit-plan.json']))"
```

- One run file per baseline; the manifests supply expected outcomes
  for the `(expected)` markers, and the audit plans supply the
  disagreement-case trial IDs. Each manifest and plan must belong to
  an input run.
- Results from different benchmark versions are never compared:
  mixing them refuses the whole render, as do duplicate
  baseline–manifest pairs and malformed inputs. There is no partial
  report.
- The §6.3 disclaimers and the limitations paragraph are carried
  verbatim (drift-tested against `docs/evaluation.md`), and the
  §6.4 prohibited claims are excluded by a test, not by review.

---

## 16. Troubleshooting

### 16.1 `ModuleNotFoundError: No module named 'playwright'`

You are not using the project environment.

```bash
.venv/bin/python -c "import playwright; print('ok')"
```

If that fails:

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
```

Check for a stray `pip`/`python` on your `PATH` — `which python` should
resolve inside `.venv/bin/` once the environment is activated.

### 16.2 `ModuleNotFoundError: No module named 'chimera'`

The working directory is not the project root, or `chimera/` is not
importable. From the project root:

```bash
.venv/bin/python -c "import chimera; print(chimera.__file__)"
```

When running a script from another directory, set `PYTHONPATH`:

```bash
PYTHONPATH=/Users/kartikbhardwaj/project-chimera .venv/bin/python /path/to/script.py
```

### 16.3 Chromium is missing

Symptom:

```
Executable doesn't exist at ~/Library/Caches/ms-playwright/chromium-XXXX/chrome-mac/Chromium.app/...
```

Fix:

```bash
.venv/bin/python -m playwright install chromium
```

If the browser binary is present but the *version* mismatches (the
number in the path differs from what the installed Playwright expects),
re-run the same command — it fetches the matching build. This happens
after a Playwright upgrade.

### 16.4 "It looks like you are using Playwright Sync API inside the asyncio loop"

The agent was called from async code. See §6.4 — run it in a worker
thread. This is the single most common integration mistake.

### 16.5 A test fails

1. **Read the assertion, then read the trace.** Browser-test failures
   leave a trace in `data/traces/`; the failing event's
   `error_details.cause_message` holds the underlying Playwright error
   (e.g. `Locator.fill: Timeout 5000ms exceeded`).
2. **Timing-sensitive failures:** the browser group takes ~36 s and
   starts a real Chromium per test. On a loaded machine, re-run the
   single failing test before suspecting a defect:
   ```bash
   .venv/bin/python -m pytest tests/test_integration.py -v -k <test_name>
   ```
3. **Expected failures in the fault tests:** a `disabled=1` scenario
   takes ~5–6 s by design — the retry policy's 5 s wall-clock budget
   across both attempts. A test that "hangs" for 6 s is behaving
   correctly.
4. **Import errors after a configuration change:** confirm
   `pyproject.toml` still parses and that `pythonpath = ["."]` is
   present under `[tool.pytest.ini_options]`.

### 16.6 Trace-write errors

Symptom: the run returns `success=False`, `status="failed"`,
`trace_path=None`, and `error` beginning with `TraceWriteError:`.

This is the designed behaviour of
[ADR-003](adr/ADR-003-trace-persistence-precondition-for-success.md):
a run whose trace could not be written is **not** a successful run. It
is reported as a failure, deliberately, rather than as a success with a
missing artifact.

Common causes and fixes:

| Cause | Fix |
|---|---|
| `data/traces/` does not exist and cannot be created | Check write permission on the project directory. The recorder creates the directory if it can. |
| The directory is read-only | `chmod u+w data/traces` or point `trace_dir` elsewhere. |
| Disk full | Free space. |
| A stale file locked by another process | Remove the specific `<run_id>.json.tmp` temp file. The write is atomic, so a leftover temp file is safe to delete. |

Because the write is atomic, a partially written trace is not a
failure mode — either the trace exists complete, or it does not exist.

Note that a trace-write failure **displaces** the original error: the
`error` field then describes the `TraceWriteError`, and the original
cause is not recoverable from the run's own output. Read the earlier
stdout/stderr of the run if the original cause matters.

### 16.7 A run takes ~5–6 s and fails

Expected for the persistent fault (`?disabled=1`): the `fill` action
cannot proceed, and the retry policy's 5 s wall-clock budget is spent
across both attempts. Not a hang. See §8.2.

### 16.8 Nothing appears under `data/`

`data/` is created on demand by the recorder. If a run fails *before*
the recorder is initialised — for example, if Chromium cannot launch —
no trace is written, because there is no run to trace. Check the
exception in the process output.

---

## 17. Related documents

| Document | Contents |
|---|---|
| [`CURRENT_STATUS.md`](../CURRENT_STATUS.md) | Measured state, what exists, the backlog, the next task. |
| [`docs/architecture.md`](architecture.md) | Components, browser lifecycle, safety boundary, data flow, requirement-label mapping. |
| [`docs/threat_model.md`](threat_model.md) | Assets, trust boundaries, 14 threats with their actual enforcement points, residual risks. |
| [`docs/adr/`](adr/) | ADR-001 browser isolation · ADR-002 cooperative cancellation · ADR-003 trace persistence as a success precondition · ADR-004 requirement traceability. |
| [`docs/evaluation.md`](evaluation.md) | Evaluation criteria, metrics, baselines, reporting rules, acceptance gates, prohibited claims. |
| [`docs/benchmark_design.md`](benchmark_design.md) | The proposed benchmark: scenarios, manifests, independent verifier, trial protocol, result schema. **Not yet built.** |
| [`docs/evaluation_approaches.md`](evaluation_approaches.md) | Survey of established browser-agent evaluation methods, with sources. |

**A note on requirement identifiers.** The SRS is the requirements
authority, and its identifiers (`FR-018`, `NFR-012`, …) are used
throughout these documents. The project's internal labels differ in one
important place: the project's "**FR-018**" denotes *execution tracing*,
whereas **SRS FR-018** is *"use deterministic browser primitives."* They
are different requirements and must not be conflated. The full
crosswalk, and the six still-unresolved mapping questions, are in
[ADR-004](adr/ADR-004-requirement-traceability-to-srs.md).
