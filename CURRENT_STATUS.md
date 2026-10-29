# Project Chimera — Current Status

> Concise progress log. Read this first when resuming in a new session.

## Milestone 1 — Foundation (SRS Phases 0–2)

### What exists
- `demo_app/index.html` — static task manager with deterministic fault
  injection: URL params `?slow=<ms>` and `?disabled=1`, an on-page
  "Fault injection" panel (Slow load / Disable Create), a Reset button,
  and a submit handler that refuses when the Create button is disabled
- `chimera/agent.py` — Playwright `create_project()` plus
  `get_demo_url_with_faults()` and `create_project_with_faults()`.
  Per-action timeout `ACTION_TIMEOUT_MS` derived from
  `DEFAULT_POLICY.max_total_seconds`. Lazy import of Playwright so
  the URL builders are usable without it. Every browser action goes
  through exactly one recorded execution path (one `page.goto`, one
  `name_input.fill`, one `create_button.click`, one verification
  `wait_for` per postcondition). FR-018 events are emitted via a
  `TraceRecorder`; on any failure a best-effort screenshot is
  captured under `data/screenshots/` (NFR-019) and attached as
  evidence on the failing event. Result fields: `success`,
  `cancelled`, `status` (`succeeded`/`failed`/`cancelled`),
  `project_name`, `error`, `trace_path`, `run_id`. A trace-write
  failure forces the result to `success=False`, `status="failed"`,
  `cancelled=False` with the write error surfaced (FR-034).
  Optional `cancel=` token (FR-021) aborts the run at the next safe
  boundary. Each run gets its OWN `BrowserContext` and is closed
  explicitly (NFR-012). Optional `observe=` hook (Stage 3) captures a
  harness snapshot from the live page before teardown; absent by
  default, adds no trace events, and never changes the outcome.
  Optional `browser_factory=` hook (Stage 4) replaces browser
  acquisition so the harness can hand the agent a recording page
  proxy; absent by default, close discipline unchanged.
- `chimera/safety.py` — allowlist + bounded-retry module
  (NFR-016, FR-022, FR-027, FR-028) plus cooperative cancellation
  (FR-021): `CancellationToken` (flag + `threading.Event`, first
  reason wins) and `RunCancelledError`. `execute_with_retry` accepts
  an optional `cancellation_token` and checks it at the top of every
  retry iteration, inside `is_effect_achieved`, and before the retry
  sleep.
- `chimera/tracing.py` — `TraceRecorder` dataclass with append-only
  event log, monotonic `sequence_number`, UTC millisecond timestamps,
  atomic JSON write (temp file + rename), and `TraceWriteError` for
  FR-034. Helpers: `action_attempted`, `action_succeeded`,
  `action_failed`, `verification_passed`, `verification_failed`,
  `capture_failure_screenshot`. Three terminal statuses:
  `run_succeeded` (outcome `ok`), `run_failed` (outcome `failure`),
  `run_cancelled` (outcome `cancelled`).
- `tests/test_agent.py` — 2 browser tests (pytest)
- `tests/test_integration.py` — 19 browser tests (5 fault/Reset + 4
  tracing + 6 cancellation + 4 session isolation) verified end-to-end
  in Chromium
- `tests/test_safety.py` — 25 stdlib-unittest tests (15 allowlist/
  retry + 10 cancellation)
- `tests/test_faults.py` — 17 stdlib-unittest tests (URL builder + HTML
  contract)
- `tests/test_tracing.py` — 20 stdlib-unittest tests (schema, atomic
  write, FR-034 write-failure, terminal statuses, helper methods)
- `requirements-dev.txt` — pinned `playwright>=1.40,<2.0`, `pytest>=7.4,<9.0`
- `pyproject.toml` — PEP 621 project metadata: `name = "chimera"`,
  `requires-python = ">=3.9"`, runtime `dependencies =
  ["playwright>=1.40,<2.0"]`, a `dev` extra with
  `pytest>=7.4,<9.0`, the setuptools backend (`setuptools>=61`, which
  PEP 621 metadata requires), an explicit `[tool.setuptools] packages =
  ["chimera"]` (flat-layout auto-discovery would fail because `tests/`
  also has an `__init__.py`), and `[tool.pytest.ini_options]` with
  `testpaths = ["tests"]` and `pythonpath = ["."]`. The declared
  dependency ranges are **identical** to `requirements-dev.txt`; neither
  file pins an exact version. No license is declared — none has been
  chosen, and inventing one would be an unsupported claim.
- `.env.example` — declares **no** settings, because the code reads no
  environment variables. Documents the four steps required to add one,
  and states explicitly why no model-provider API-key placeholder
  exists (no model integration yet — SRS §7.4).
- `.gitignore` — Python/test caches plus `data/traces/`,
  `data/screenshots/`, `artifacts/` (generated runtime artifacts), and
  `.env` / `.env.*` with `!.env.example` re-included, so a local
  override file can never be committed by accident.
- `docs/architecture.md` — actual implemented architecture: component
  responsibilities, browser/context lifecycle and isolation, the safety
  and retry boundary, cooperative cancellation and its limits, the
  verification/trace/screenshot contract, data flow and repository
  layout, implemented vs. planned capabilities, known limitations, the
  planned evolution, and the requirement-label mapping (§11)
- `docs/threat_model.md` — assets and security goals, trust boundaries
  (untrusted page content, future model proposals), 14 named threats with
  the **actual** enforcement point for each mitigation, 13 residual
  risks with no control yet implemented, and the validation required
  before broader or production use
- `docs/adr/README.md` — ADR index and the status vocabulary
- `docs/adr/ADR-001-per-run-browser-and-context-isolation.md` —
  **Accepted.** Per-run browser *and* per-run `BrowserContext`; why
  `browser.new_page()` was already isolating and why the explicit
  lifecycle was adopted anyway (lifecycle clarity and testability, not
  a bug fix).
- `docs/adr/ADR-002-cooperative-cancellation-at-safe-boundaries.md` —
  **Accepted.** Cancellation is checked at safe boundaries only; the
  in-flight synchronous Playwright action is not interrupted from
  another thread; `ACTION_TIMEOUT_MS` (5 s) is the derived bound and the
  user-visible trade-off.
- `docs/adr/ADR-003-trace-persistence-precondition-for-success.md` —
  **Accepted.** A trace-persistence failure forces the run to `failed`,
  including over a cancellation; the effect on ordinary failures and on
  cancellation is spelled out.
- `docs/adr/ADR-004-requirement-traceability-to-srs.md` — **Accepted.**
  The SRS text is authoritative; a verified crosswalk (each row checked
  against the SRS in this session) plus six open mapping questions that
  need an owner ruling.
- `docs/adr/ADR-005-runner-refuses-on-policy-divergence.md` —
  **Accepted** (implemented 2026-10-28, harness Stage 2). A manifest
  whose declared retry policy diverges from the agent's effective
  policy is **refused** by the runner, not run with a warning. It rules
  on AMB-9; the enforcement is
  `benchmarks/runner.py::check_policy_alignment`, proven by
  `tests/test_benchmark_runner.py::PolicyAlignmentTests`.
- `docs/evaluation_approaches.md` — survey of browser-agent evaluation
  methods and benchmarks: 7 families, 22 sources **verified against the
  arXiv API and the official `webarena.dev` site on 2026-10-24** (titles,
  authors, v1 dates, URLs). Covers WebArena, WorkArena, BrowserGym,
  VisualWebArena, TheAgentCompany, OSWorld, Mind2Web, WebLINX, MiniWoB++,
  WebShop, WebVoyager, τ-bench (`pass^k`), AgentDojo, AgentHarm,
  Agent-SafetyBench, TRAP, BrowseSafe, the ABC rigorous-benchmark
  checklist, the WebArena-Lite human audit, and the statistical diagnosis
  of web agents. States the survey's own limits (arXiv-centric; abstracts
  only; paper-reported numbers, not live leaderboards).
- `docs/benchmark_design.md` — **implemented and run.** The initial
  benchmark: target/task/postcondition spec, a scenario catalogue
  (normal, transient-slow, persistent-disabled, combined — plus six
  planned-but-unimplementable ones), a development/evaluation manifest
  split, the independent-verifier design for the false-success metric,
  Baselines A/B/C, the trial protocol, a metrics table split into
  *measurable now* vs. *blocked*, the JSON result schema, an explicitly
  **illustrative** example report, statistical reporting rules (Wilson
  bounds, n, `pass^k`), threats to validity, and a 10-item list of what
  must be built before it can run. Dev runs are complete and audited;
  held-out eval runs are complete with a provisional report (§13
  items 1–7 all done; item 8+ still future work).
- `docs/evaluation.md` — Chimera's evaluation criteria (C-1…C-7), the
  benchmark protocol summary, the metrics catalogue, baseline policy and
  attribution rules, the required report format and mandatory
  disclaimers, the SRS §11.2 acceptance-gate table with current status
  (**all gates "not measured" except the regression suite**), the
  limitations of current evaluation capability, the six unresolved
  mapping questions with their evaluation impact, and a capability
  roadmap.
- `docs/user_guide.md` — the operational entry point: prerequisites
  (with the Python floor verified against the installed dependencies'
  own `Requires-Python` metadata, not just the local interpreter),
  the existing `.venv` and how to recreate it, dependency and Chromium
  installation, the repository layout, running the agent and the demo
  app, the four fault scenarios with their **measured** expected
  results, the per-group test commands, reading JSON traces and
  failure screenshots, cancellation and its limits, an
  implemented-vs-planned table, the configuration surface, the
  reproducible evaluation commands, and troubleshooting. Every command
  in it was executed unless explicitly labelled otherwise. Its test
  commands cover **all three** groups (83 application + 338 harness
  = 421), not the original 83.
- `README.md` — refreshed into a concise entry point: purpose, what is
  implemented today, setup, test commands, documentation links, and the
  explicit limitations. The stale "recovers from failures and learns
  reusable recovery skills" claim and the incorrect "Python 3.10 or
  newer" prerequisite were removed. Detailed instructions live in
  `docs/user_guide.md`. The suite size and the "no benchmark has been
  run" limitation were corrected in the close-out session to state the
  harness's *contracts* exist while the runner and verifier do not.

### Benchmark harness — Stage 1 (contracts)

The harness lives in a top-level `benchmarks/` package, **not** in
`chimera/`: `docs/benchmark_design.md` §6 requires harness artifacts
(including the Baseline A replay driver) to stay out of the product
package. Nothing under `benchmarks/` imports Playwright, opens a
browser, or touches `chimera.agent`; the modules are pure-stdlib.

- `benchmarks/manifest.py` — the versioned manifest contract:
  `MANIFEST_SCHEMA_VERSION = 1`, `Manifest` (schema version, benchmark
  ID and version, manifest ID, split, description, `slow_band_ms`,
  `RunConfig`, and the scenario list), `Scenario` (ID, description,
  fault **variants**, expected outcome, timeout, preconditions,
  postconditions, inputs), `FaultConfig` (with `url_params()`),
  `TaskInput` (with an explicit `expected_stored_name`), `Postcondition`,
  `RunConfig`, `RetryPolicyConfig`, `SlowBand`, and `Cell`.
  `Manifest.cells()` derives the **fixed, manifest-declared cell
  order** deterministically; `Manifest.sha256()` computes the content
  hash over a canonical JSON encoding. `validate_manifest` rejects
  malformed documents, duplicate scenario/input/postcondition IDs,
  invalid timeouts, invalid trial counts, out-of-band `slow` values,
  an invalid expected outcome or split, and an inconsistent retry
  policy. Every rejection names the offending field.
- `benchmarks/results.py` — the versioned result contract:
  `RESULT_SCHEMA_VERSION = 1`, `EpisodeOutcome` (succeeded, failed,
  cancelled, inconclusive), `Metric` (measured **or** unavailable with
  a mandatory reason — never a bare `null` and never a `0` standing in
  for a missing measurement), `PostconditionCheck`, `VerifierAudit`,
  `VerificationEvidence`, `EpisodeResult`, `CellResult`,
  `EnvironmentInfo`, `RunTotals`, `RunResult`, and `false_success_set()`
  implementing design §5's formula.
- `benchmarks/manifests/dev-v1.json` — development manifest. The
  `slow=2000` value already exercised by the test suite, and the full
  input-variation list (`I-PLAIN`, `I-SUBSTR`, `I-SPACE`, `I-UNICODE`).
  16 cells, 80 episodes.
- `benchmarks/manifests/eval-v1.json` — held-out evaluation manifest.
  Five `slow` values inside the documented [500, 4000] ms band
  (800, 1350, 2100, 3000, 3900), none of them overlapping the
  development manifest, and a subset of the input variations.
  36 cells, **180 episodes** — above SRS §11.2's 100-episode minimum.
- `tests/test_benchmark_manifest.py` — 46 tests: valid manifests, the
  dev/eval split discipline, content hashing, invalid manifests, and
  schema-version handling.
- `tests/test_benchmark_results.py` — 44 tests: metric representation,
  the four outcomes, verification evidence, false-success detection,
  and serialisation round-trips.
- `docs/benchmark_design.md` §14 — **eight open ambiguities** (AMB-1 …
  AMB-8) recorded rather than decided silently, including the
  per-episode record the design's §9 does not define, the input
  subset choice, the per-scenario expected outcome against the trim
  input, and the conflict between §9's bare `null` and §8.3's
  "null with the reason". **AMB-9** (must a manifest's declared retry
  policy match the agent's?) has been **ruled on and implemented**:
  see ADR-005 (now **Accepted**) and `benchmark_design.md` §14.1.
  The Stage 2 runner enforces the refusal plus the timeout and warm-up
  rules in §§14.2–14.3; AMB-1 … AMB-8 still await owner rulings.

### Benchmark harness — Stage 2 (runner)

- `benchmarks/runner.py` — one manifest in, one `RunResult` file out:
  `Runner` (single-manifest runs, so dev and eval episodes are never
  mixed), `run_manifest`, `load_run_result`, `collect_environment`,
  `episode_budget_seconds`, `default_executor`, and
  `check_policy_alignment`. Cells run in manifest-declared order with
  sequential trials; each episode gets a fresh `CancellationToken` and
  its own trace artifact; the budget is
  `min(scenario.timeout, episode_timeout)` enforced by a timer through
  the cooperative token (§14.2); warm-up episodes run outside any cell
  with a `warmup:` trial ID and are excluded from every aggregate
  (§14.3). The agent-reported outcome is read from the persisted trace
  artifact, never from the executor's return value (§5); retries and
  action counts are derived from verified trace events. Every
  verifier/observer/model-gated metric is `unavailable` with an
  explicit reason — no zero stands in for a missing measurement.
  `RunnerError` / `ConfigurationError` (refusal before execution, no
  artifacts) / `PolicyMismatchError` (AMB-9) / `TraceIntegrityError`
  (abort with partial results persisted).
- AMB-9 enforcement reads the **effective** runtime policy live from
  `chimera.agent` (`DEFAULT_POLICY` + `ACTION_TIMEOUT_MS`, floats with
  tolerance, integers exactly); it duplicates no policy constant, and
  fails closed with a clear error when the agent is uninspectable or
  self-contradictory.
- `tests/test_benchmark_runner.py` — 41 tests, all against fake
  executors and fixture traces (no browser): manifest loading and
  invalid manifests, deterministic ordering, per-episode isolation,
  matching/mismatching policies, refusal before execution,
  fail-closed inspection, timeout budgets and timeout outcomes,
  persistence and round-trips, harness and trace-integrity failures,
  and unavailable-metric reasons. One test runs the full shipped dev
  manifest (16 cells × 5 trials + 1 warm-up) with a fake executor.
- `benchmarks/__init__.py` — documents the Stage 2 module and its
  `chimera.agent` coupling (lazy import; no browser at import time).
- ADR-005 promoted **Proposed → Accepted**; `docs/adr/README.md`,
  `docs/benchmark_design.md` (§13 item 2, §14, AMB-9 row, §14.1),
  `README.md`, and `docs/user_guide.md` updated to the verified state
  (214 tests; runner exists, verifier does not).

### Benchmark harness — Stage 3 (independent verifier)

- `benchmarks/verifier.py` — exact-match P1–P3 evaluation from a
  harness-observed state snapshot plus the §5 classification:
  `DOMSnapshot` (strict schema, fail closed), `capture_page_state`
  (raw visibility + `textContent` reads, duck-typed, no Playwright
  import), `verify_postconditions` (P1 visible; P2 exactly one item
  **equals** the expected stored name; P3 count equals 1),
  `classify_false_success` (`None` when unverifiable),
  `is_verifier_disagreement`, `summarize_checks` (refuses unverified
  evidence), `load_snapshot` / `snapshot_path_for`. Missing, malformed,
  or run-mismatched snapshots yield `unavailable` evidence with an
  explicit reason — never a classification.
- Lifecycle finding: `create_project()` closes its browser context
  before returning and the demo app's state is in-memory per page
  load, so **no live page exists for a post-hoc verifier**. The
  minimal mechanism is `chimera/agent.py`'s new optional `observe`
  hook: called once with the live page after the workflow settles and
  before teardown, on the agent's own thread; its return becomes
  `result["observation"]`, a raise becomes
  `result["observation_error"]` with the outcome unchanged, no trace
  event is added, and both keys are absent when `observe` is not
  supplied — the default path is bit-identical.
- Runner wiring (no schema change): `EpisodeExecution` carries
  `state_snapshot` / `snapshot_ref` / `observation_error`;
  `default_executor` captures via the hook and persists
  `<run_id>.snapshot.json` next to the trace; each episode's
  `verification` evidence comes from `verify_postconditions`;
  per-cell `independent_verification`, `false_successes`, and
  `verifier_disagreements` are **measured** only when every episode
  is verified, else the whole aggregate is `unavailable` with its
  reason. `RunTotals.false_success_rate` stays unavailable (rate +
  bounds are report-stage work).
- Independence: `benchmarks/verifier.py` imports only stdlib +
  `benchmarks.results`; enforced by a subprocess import-hygiene test
  (`chimera.agent` and `playwright` absent from `sys.modules`) and
  an AST source scan (no chimera/playwright imports, no
  `has_text`/`create_project`/`TraceRecorder` in code).
- `tests/test_benchmark_verifier.py` — 39 tests (stdlib only):
  snapshot schema, capture selectors, exact-match P1–P3 including
  whitespace/case/substring traps, fail-closed evidence, the
  classification matrix, runner wiring (measured 0/2 false successes,
  measured disagreements, partial-verification unavailability,
  round-trips), independence, and the `observe` seam via a fake
  in-memory Playwright module.
- `tests/test_verifier_browser.py` — 2 Chromium tests: a success
  episode's snapshot verifies exactly, a `disabled=1` episode's
  snapshot shows hidden confirmation and an empty list.
- `docs/benchmark_design.md` §13 item 3 marked done;
  `docs/user_guide.md` (layout tree, §9 table/commands, §13 row, §15,
  Python-floor note) and `README.md` updated to the verified state
  (255 tests; runner and verifier exist, observer and Baseline A do
  not). The user guide's §13/§15 rows also carried Stage 2 staleness
  ("runner not implemented") — corrected in this session.

### Benchmark harness — Stage 4 (harness-side action observer)

- `benchmarks/observer.py` — Playwright-boundary recording judged
  against the §8.2 permitted set: `RecordingPage` / `RecordingLocator`
  proxies (one record per call; locator creation records nothing, so
  retries appear as repeats and nothing double-counts), `ActionLog`
  (gapless seq, attached/complete flags), `ActionPolicy`
  (allowed/denied/unknown), `episode_policy`, `evaluate_log`,
  `judge_log`, `recording_browser_factory`. Genuinely observable:
  navigation URLs (`goto`), fill/click targets (locator construction:
  label/role/css), reads (`is_visible`, `all_text_contents`,
  `wait_for`, `screenshot`, permitted by type), ordering, and
  per-call outcomes. Fill values persist as lengths only; error
  messages persist as exception-type names only (privacy).
- Fail-closed evaluation: counts are measured only when the log is
  attached, complete, non-empty, and every judged action has a
  definite decision; unresolvable targets (e.g. mid-chain derived
  locators) judge `unknown`, never assumed. `unauthorized_actions`
  counts every denied action; `safety_violations` counts every denied
  action too — in this single workflow each denied action is
  out-of-scope by definition (§8.1), so the two coincide and are
  reported separately because the design defines them separately.
- `chimera/agent.py` — new optional `browser_factory` hook (mirrors
  the Stage 3 `observe` seam): called with the `sync_playwright`
  handle, returns `(browser, context, page)`; close discipline
  unchanged; default path launches exactly as before.
- Runner wiring (no schema change): `EpisodeExecution` carries
  `episode_url` / `action_log`; `default_executor` records via the
  factory and persists a judged `<run_id>.actions.json` next to the
  trace; per-episode metrics come from `evaluate_log` (re-judged from
  raw records, never trusting stored decisions); cell aggregates use
  the all-or-nothing rule (`{"total", "mean_per_trial"}`); run total
  is a measured int over non-warm-up episodes.
- Independence: the observer reads Playwright calls, never the
  agent's trace events or terminal status (a failed episode with
  allowed targets measures zero violations); `benchmarks/observer.py`
  imports only stdlib + `benchmarks.results`, enforced by a subprocess
  import test and an AST import-allowlist test; it shares nothing with
  `benchmarks/verifier.py`. Recording can never raise into the agent
  (failures mark the log incomplete). Benchmark-side control only:
  the NFR-016 target-allowlist gap is unchanged (threat-model R-1).
- `tests/test_benchmark_observer.py` — 45 tests (stdlib only):
  policy matrix, log schema, fail-closed evaluation, proxies against
  fake pages (ordering, exactly-once records, privacy, transparency,
  recording-failure survival), runner wiring (measured 0/1/2 counts,
  terminal-status independence, all unavailable paths, round-trips),
  the `browser_factory` seam via a fake Playwright module (including
  outcome-identity with and without instrumentation), and import
  independence.
- `tests/test_observer_browser.py` — 2 Chromium tests: a success
  episode records exactly navigate/fill/click/wait/wait and measures
  zero violations; a `disabled=1` episode records a failed fill on the
  permitted input and still measures zero violations.
- `docs/benchmark_design.md` §13 item 4 marked done; `README.md` and
  `docs/user_guide.md` updated to the verified state (302 tests;
  contracts, runner, verifier, and observer exist — Baseline A does
  not).

### Benchmark harness — Baseline A (deterministic replay driver)

- `benchmarks/baseline_a.py` — harness-only replay (`BASELINE_ID =
  "baseline-a"`): fixed navigate/fill/click with the same label/role
  locators, `REPLAY_ACTION_TIMEOUT_MS = 100` on fill/click (fixed and
  tiny — never waits out the 500 ms+ slow band; Playwright `timeout=0`
  would disable the timeout and wait indefinitely), one attempt per
  step, no postcondition waits, no screenshots, no Chimera trace
  events. Per-episode browser + context (isolation parity); token
  checked between steps so budgets stay enforceable; snapshot via the
  same `capture_page_state`; action recording via the same
  `RecordingPage`; fault URL built harness-side from
  `FaultConfig.url_params()` with parity against the agent's builder
  pinned by test. Never imports `chimera.agent`.
- Driver-report artifact (schema `baseline-a-replay/1`,
  `<run_id>.replay.json`): run ID, terminal, steps attempted with
  per-step outcomes, timestamps. Single-attempt order is structural
  (steps unique, in fixed order; empty steps allowed only for
  pre-start cancellation). The runner reads replay terminals from
  this persisted file and integrity-checks it like a trace; retries
  are 0 by construction, actions = steps attempted, and the report
  path is recorded as the episode's evidence artifact.
- Runner integration (no schema change, no `chimera/` change):
  `SUPPORTED_BASELINES = ("chimera", "baseline-a")`; baseline-aware
  default executor (`replay_executor` for replay runs); same cells,
  ordering, warm-ups, budgets, verifier, observer, and AMB-9 check
  (the manifest must still be coherent; replay ignores retry policy
  by definition — single attempts). Exactly one baseline per run;
  cross-baseline comparison files are report-stage work.
- `tests/test_baseline_a.py` — 26 tests (stdlib only): report schema,
  replay against fake pages (success, failure stops before click,
  exactly-once attempts, fixed timeout below every shipped slow
  value, pre-start cancellation, snapshot-failure survival,
  determinism), runner wiring (report-sourced terminals, shared
  verifier/observer scoring, corrupt/missing-report aborts, AMB-9 and
  manifest rules, default executor selection, round-trip), URL parity,
  and harness-only placement (path, import hygiene, AST scan).
- `tests/test_baseline_a_browser.py` — 5 Chromium tests confirming
  the §6 prediction on single episodes: replay succeeds on `S-NORM`
  (verifier agrees), fails on `S-SLOW` (`TimeoutError` at the fill
  step — fill precedes click in the fixed order), `S-DIS`, and
  `S-SLOWDIS`, plus a two-cell runner run end to end. Single
  episodes, not measured rates.
- `docs/benchmark_design.md` §13 item 5 and the §6 heading marked
  done; `README.md` and `docs/user_guide.md` updated to the verified
  state (333 tests; audit and report template remain).

### Benchmark harness — verifier audit procedure

- `benchmarks/audit.py` — the mechanical half of design §5 (the
  judgments stay human): `plan_audit` draws a seeded per-cell sample
  from a persisted run file and writes an audit plan (schema
  `chimera-audit-plan/1`); the human records P1–P3 booleans or
  `unauditable` per sampled episode; `apply_audit` validates and
  writes an audited copy with `CellResult.verifier_audit` filled.
  `is_provisional` implements the 95% rule; no sample size of its
  own (the human chooses, the plan records it).
- Sampling: hash-ordered seeded permutation per cell
  (`sha256(seed : trial_id)`, reproducible on any Python version),
  warm-ups excluded, first-N-auditable taken, skips recorded with
  reasons, oversubscription fails instead of capping. Default seed
  derives from run ID + cell key (reproducible from the run file).
- Evidence bundle per episode: expected stored name (manifest —
  hence `plan_audit` takes the manifest and refuses dev/eval mixing),
  trace or driver report, state snapshot, observer log listing,
  verifier checks, agent terminal/outcome, and sha256 digests.
  Incomplete bundles (missing bytes, ref mismatch, no verifier
  verdict) are skipped, never adjudicated; plan files copy no
  snapshot contents (references + digests only). Observer evidence
  is listed but plays no part in verdicts.
- Agreement is strict per-check equality (a check-level mismatch is
  a disagreement even when conjunctions coincide — the conservative
  reading). Verdicts must cover exactly the sampled episodes with
  strict booleans and full check sets; evidence bytes are re-hashed
  at apply time and changed bytes refuse the whole application. The
  input run file is never modified. Unauditable-by-human episodes
  are excluded from the fraction; all-unauditable cells keep
  `verifier_audit: null`. Skip counts and seed/auditor go in the
  audit `note`. The per-episode `VerificationEvidence.audit` slot is
  left alone — the design never defines its semantics. No schema
  changes; no runner, verifier, observer, or Baseline A changes.
- `tests/test_audit.py` — 28 tests (stdlib only, real runner output
  via fake executors writing real files): sampling (permutation,
  reproducibility, seeds, warm-up exclusion, oversubscription,
  skips), bundles (digests, ref mismatch, missing verdict/scenario,
  no content copying), verdicts (strict agreement, malformed/
  partial/missing/extra verdicts, tampered bytes, run/manifest
  mismatch), apply (per-cell fractions, unauditable exclusion,
  null-on-zero, byte-identical input, round-trip), the provisional
  matrix, dev/eval separation, and import hygiene.
- `docs/benchmark_design.md` §13 item 6 marked done (procedure;
  adjudication stays a per-run human act); `docs/user_guide.md` §15.1
  documents the human flow; `README.md` updated (361 tests; report
  template remains; **no human sample has been adjudicated**).
  Passing audit-tooling tests prove the machinery only — they say
  nothing about the verifier's accuracy on real episodes.

### Benchmark harness — report template (design §11, evaluation §6)

- `benchmarks/report.py` — `render_report` consumes persisted run
  files (optionally audited, optionally several baselines) plus the
  runs' own manifests and audit plans, and renders the specified
  Markdown report: Runs header (identity, manifests, configuration,
  environment), per-cell/per-baseline summary table, not-measurable
  table with reasons, verifier-audit section with the
  AUDITED/PROVISIONAL verdict, failure breakdown, exclusions,
  verbatim limitations, claim list, verbatim disclaimers, and
  artifacts (format marker `chimera-report/1`).
- Honesty rules enforced in code, not prose: unavailable metrics
  keep their reasons and are never zero; zero false-success counts
  carry the 95% Wilson upper bound (`wilson_upper`, pinned to the
  §4.3 reference values 43.4/7.1/3.7%); the 95% provisional rule is
  applied via `benchmarks.audit.is_provisional`; cross-version
  comparison, duplicate baseline–manifest pairs, foreign manifests
  or plans, and malformed inputs refuse the whole render
  (`ReportError`) — no partial report. The §6.3 disclaimers and the
  §8 limitations paragraph are carried verbatim and drift-tested
  against `docs/evaluation.md`; the §6.4 prohibited claims are
  excluded by test. Renders are deterministic (sorted runs/cells,
  input-order independent) and print artifact paths only — no form
  contents, names, or manifest descriptions.
- Document quirks resolved in favour of the documents: §6.1's
  "(expected) result" is the unanimous-match marker in the §11
  example's `(0%, expected)` format; one Baseline B `null` row per
  reported split (the single-split case matches the example
  exactly); §6.1 item 6 cites "§7" but the limitations paragraph
  lives in §8 at this revision, which is what is reproduced (noted
  in the report itself); the §11 bare `0/5` entries give way to the
  explicit §4.3 rule (every zero count carries its bound); rate
  reporting stays report-side, so the runner's unavailable
  `totals.false_success_rate` is listed, not computed.
- `tests/test_benchmark_report.py` — 34 tests (stdlib only, real
  runner output via fake executors, real `plan_audit`/`apply_audit`
  for audit states): Wilson reference values and edge cases, every
  §6.1 section, expected markers both directions, multi-baseline and
  dev/eval runs, full/sub-95%/missing-plan/unauditable audit states,
  null metrics with reasons, all integrity refusals, shortfall and
  harness-error disclosure, determinism, privacy exclusion,
  verbatim drift, and the prohibited-claims guard.
- `docs/benchmark_design.md` §13 item 7 marked done (with an
  "Implemented" pointer under §11); `docs/user_guide.md` gains
  §15.2 (rendering a report) and updated §9.4/§9.5/§13/§15 counts;
  `README.md` updated (395 tests; harness fully built, still
  unrun). The §13 minimum set (items 1–7) is now fully
  implemented. **No benchmark run has been performed and no human
  sample has been adjudicated** — fixture renders assert report
  shape only.

### Benchmark runs — development (audited) and held-out evaluation (provisional)

- Dev runs `dev-20261028-chimera` and `dev-20261028-baseline-a`
  (`artifacts/dev-20261028/`): 16 cells × 5 trials + 1 warm-up each,
  full trace/snapshot/action evidence. Chimera: S-NORM 20/20, S-SLOW
  20/20, persistent faults bounded 0/40; Baseline A: S-NORM 20/20
  only. Human audit complete at 100% agreement on all 32 sampled
  episodes per baseline; `report-audited.md` verdict **AUDITED**.
- Eval runs `eval-20261028-chimera` and `eval-20261028-baseline-a`
  (`artifacts/eval-20261028/`): 36 cells × 5 trials + 1 warm-up
  each (held-out slow values 800–3900 ms; I-SUBSTR held out), frozen
  `eval-v1.json` verified by content hash before execution and never
  edited. Chimera: S-NORM 15/15, S-SLOW 75/75, S-DIS 0/15 and
  S-SLOWDIS 0/75 bounded as expected; Baseline A: S-NORM 15/15,
  all fault cells 0. Zero measured false successes and zero harness
  errors in both runs. `report.md` verdict **PROVISIONAL**: no eval
  sample adjudicated (human adjudication deferred).
- Full 144-episode eval audit plans drawn (2/cell, 0 skips); reduced
  8-episode stratified mini-plans
  (`run-*.audit-plan-mini.json`: 4 per baseline, one median cell per
  scenario, seeded first-auditable draw) await the deferred review.

### Audit support added during evaluation

- `tools/audit_review.py` + `tests/test_audit_review.py` (15 tests):
  guided blind-judging CLI (verifier checks hidden until judged,
  strict booleans, verdict-only atomic saves, quit/resume).
- Fault-aware audit cell keys (eval exposed a 36→12 key collision):
  `cell_key` now includes fault params, episode→cell mapping is
  positional with integrity checks, and the report refuses
  stale-keyed plans loudly. Covered by multi-variant audit tests.
- `benchmarks.audit.plan_targeted_audit` (+ tests): draws named
  cells only; untargeted cells ride as empty samples and stay
  unaudited at apply time. No validation weakened; 95% rule intact.
- Report audit section now discloses
  `**Coverage:** X of Y cells audited (Z episodes adjudicated).`

### Documentation decisions recorded (Phase 0)

The three design decisions made so far are now written down with their
rationale and their enforcement points, as ADR-001, ADR-002, and
ADR-003 (a fourth ADR, ADR-004, records the requirement-label
traceability and is summarised in the next section):
- **Per-run browser *and* per-run browser context** — strongest available
  isolation; the cost is ~0.1 s launch overhead per run, which is
  irrelevant against a local test app. See `docs/architecture.md` §3.
- **Cooperative, not pre-emptive, cancellation** — Playwright's sync API
  cannot be safely interrupted from another thread, so the agent never
  touches a Playwright object off-thread and never force-kills a thread.
  The cost is a worst-case stop delay of `ACTION_TIMEOUT_MS` (5 s). See
  `docs/architecture.md` §5.
- **A run cannot be reported successful if trace persistence fails** —
  the trace is the evidence record; an unverifiable run is a failure.
  This precedence holds even over a cancellation. See
  `docs/architecture.md` §6.

### Requirement-label mapping — read before auditing compliance

The project's internal shorthand does **not** match the authoritative SRS
for every label. Notably, the project's "FR-018" (execution tracing) is
**not** SRS FR-018 (which is "use deterministic browser primitives");
tracing corresponds to SRS FR-036/FR-038 and the §8.3/§8.4 data model.
Full mapping in `docs/architecture.md` §11; the normative crosswalk, with
per-row implementation status and six open questions, is
`docs/adr/ADR-004-requirement-traceability-to-srs.md`.

**Unresolved requirement-mapping questions** (recorded, not decided — they
need an owner ruling, not a coding task):
1. Does SRS FR-018's "validated locators" require a *target* allowlist, or
   is it satisfied by fixed semantic locators? (This repo tracks the
   stricter reading.)
2. What satisfies SRS FR-022's "number of actions"? Today only duration
   and retries are bounded; there is no run-level action budget.
3. Is the JSON trace the SRS FR-036 "verification report", or a separate
   artifact? FR-036 also requires "unresolved uncertainties", which the
   trace does not carry.
4. How do the three terminal statuses map onto the twelve SRS §9 states?
   `INCONCLUSIVE` is not implemented, and §9's "transitions must be
   validated by code" is not implemented.
5. Must FR-034's "contradictory" evidence be detected explicitly? Only
   the *missing*-evidence half is implemented.
6. Does SRS §8.3/§8.4 replace the trace schema (`schema_version: 1`) or
   extend it under a version bump?

### What is verified in this session
Dependencies installed in the existing `.venv` (Python 3.9.6):
```bash
python -m pip install --upgrade pip            # 21.2.4 → 26.0.1
python -m pip install -r requirements-dev.txt  # playwright 1.60.0, pytest 8.4.2
python -m playwright install chromium          # ~170 MB to ~/Library/Caches/ms-playwright/
```

Test commands and actual results:
```bash
# Focused session-isolation tests:
.venv/bin/pytest tests/test_integration.py -k "isolat or fresh_browser or leak or resources or closes" -v
# 4 passed, 15 deselected in 7.11s

# Browser integration, including the new isolation tests:
.venv/bin/pytest tests/test_integration.py tests/test_agent.py -v
# 21 passed in 35.53s

# Full stdlib suite (excludes pytest-only integration):
.venv/bin/python -m unittest tests.test_safety tests.test_faults tests.test_tracing
# 62 passed in 0.059s
```

**Total: 83 tests pass, 0 failed (62 stdlib + 21 browser).**

The Phase 0 documentation work (`docs/architecture.md`,
`docs/threat_model.md`, `docs/adr/`, `docs/evaluation_approaches.md`,
`docs/benchmark_design.md`, `docs/evaluation.md`) changed **no application
or test code**, so the suite was **not** re-run against it; the 83/0 result
above remains the measured baseline for the unchanged code. No discrepancy
was found while writing the docs. Every SRS identifier cited in ADR-004 was
read directly from `PROJECT_CHIMERA_SRS.md` in that session rather than
carried over from an earlier note, and every external source in
`docs/evaluation_approaches.md` was retrieved and its title, authors, date
and abstract read in the session that wrote it.

#### Verification performed in the Phase 0 close-out session

This session added `docs/user_guide.md`, `pyproject.toml`, `.env.example`,
and the refreshed `README.md`. Adding `pyproject.toml` made it the pytest
inifile, so the suite **was** re-run against the new configuration:

```bash
.venv/bin/python -m pytest -q
# 83 passed in 36.46s          (rootdir now the project root, configfile pyproject.toml)

.venv/bin/python -m pytest tests/test_safety.py tests/test_faults.py tests/test_tracing.py -q
# 62 passed in 0.12s

.venv/bin/python -m pytest tests/test_agent.py tests/test_integration.py -q
# 21 passed in 35.79s

.venv/bin/python -m unittest tests.test_safety tests.test_faults tests.test_tracing
# Ran 62 tests — OK
```

**Total: 83 tests pass, 0 failed (62 stdlib + 21 browser) — re-confirmed
under the new `pyproject.toml` configuration.**

Also verified in this session:

- `pyproject.toml` parses as valid TOML, and every declared field has the
  expected value. The package was **not** installed (`pip install -e .`
  would modify the working environment, which is out of scope).
- The Python floor is **3.9**, checked against the installed packages'
  own metadata rather than assumed: `playwright`, `pytest`, and
  `greenlet` each declare `Requires-Python: >=3.9`.
- The four fault scenarios were run end-to-end and their terminal
  statuses measured: normal → `succeeded`; `slow=2000` → `succeeded`;
  `disabled=1` → `failed` (`RetryBudgetExhaustedError`); both together →
  `failed`.
- A `disabled=1` run was **timed**: 5.77 s. The retry policy's
  `max_total_seconds = 5.0` is a wall-clock budget across *all* attempts
  of an action, not a per-attempt allowance. An earlier draft of the
  user guide wrongly said ~10 s; this was corrected.
- Cancellation was exercised: a token requested at t = 1.0 s against a
  3 000 ms slow load produced `status="cancelled"`,
  `cancelled=True`, `RunCancelledError`, and the run stopped at
  t ≈ 3.6 s — a concrete demonstration of the cooperative-cancellation
  limit documented in ADR-002.
- The trace JSON shape, event vocabulary
  (`run_started`, `action_attempted`, `action_succeeded`,
  `action_failed`, `run_succeeded`/`run_failed`/`run_cancelled`), the
  atomic-write behaviour, and the failure-only screenshot rule were all
  confirmed against real artifacts.
- `playwright install --dry-run chromium` reports the expected build as
  `chromium-1223`, which is present in `~/Library/Caches/ms-playwright/`.
  The install command itself was **not** executed — it would attempt a
  network download.
- All internal Markdown links in `README.md`, `docs/user_guide.md`,
  `docs/evaluation.md`, `docs/benchmark_design.md`,
  `docs/architecture.md`, and `docs/threat_model.md` resolve; code
  fences are balanced and all Markdown tables are well-formed.

**Not executed, and not claimed as verified:** `pip install -r
requirements-dev.txt`, `pip install -e .`, `python -m playwright install
chromium`, `open demo_app/index.html`, and `python -m http.server` as a
server for the demo app. The first three were out of scope (installs are
prohibited and the environment already satisfies the constraints); the
last two open a GUI or bind a port and are documented as optional
alternatives to opening the file directly.

**No benchmark run has been performed.** `docs/benchmark_design.md` and
`docs/evaluation.md` specify a benchmark; they report no results. Every
number in those two documents is either a schema placeholder, an explicitly
labelled illustrative example, or a confidence bound computed from a stated
sample size.

#### Verification performed in the benchmark-harness Stage 1 session

Stage 1 added the harness contracts, the two manifests, and 90 tests.
The harness imports nothing outside the standard library, so **no
package was added and none was installed**, and **no application, safety,
tracing, or test code was modified**. The 83-test regression baseline
was re-run unchanged and still passes.

```bash
.venv/bin/python -m pytest -q
# 173 passed in 36.11s

# The pre-existing baseline, unchanged:
.venv/bin/python -m pytest tests/test_safety.py tests/test_faults.py tests/test_tracing.py -q
# 62 passed
.venv/bin/python -m pytest tests/test_agent.py tests/test_integration.py -q
# 21 passed
```

Per-file counts: `test_benchmark_manifest.py` 46, `test_benchmark_results.py`
44, `test_safety.py` 25, `test_tracing.py` 20, `test_integration.py` 19,
`test_faults.py` 17, `test_agent.py` 2 — **173 total, of which 83 are the
pre-existing baseline and 90 are new harness tests.**

Two real defects were found by the new tests and fixed:

1. **Manifest trial-count coercion.** `int(2.5)` silently truncated an
   invalid trial count of `2.5` to a valid `2` *before* validation ran,
   so a malformed manifest was accepted. Fixed by type-checking every
   coerced field before conversion (`_require_int` / `_require_number` /
   `_require_str`), which also separated *malformed* (wrong type) from
   *invalid* (wrong value) rejections.
2. **Result metric deserialisation.** `Metric.from_dict` branched on
   whether the key `"value"` was present, but `Metric.to_dict` always
   emits both keys — so an unavailable metric (`value: null`, reason
   present) was read back as `measured(None)` and then rejected by
   `__post_init__`, breaking every unavailable-metric round trip. Fixed
   by making the discriminator the **value** of `unavailable_reason`
   rather than key presence, which also permits a legitimately null
   *measurement* to round-trip as a measured metric.

Also verified in this session: both shipped manifests load and validate;
the content hash is stable across reloads and independent of key order
in the file, and changes when a parameter value changes; the cell order
is deterministic; the two manifests share the same scenario IDs and
fault *types* but no `slow` *value*; the evaluation manifest's input
variations are a strict subset of the development manifest's; and the
evaluation manifest yields 180 episodes, above SRS §11.2's 100-episode
minimum.

#### Verification performed in the Phase 0 close-out correction session

Documentation-only. **No application, test, or harness code was changed,
no package was installed, and the `.venv` was not touched.** The suite
was re-run against the unchanged code to confirm the configuration and
the doc corrections did not disturb it:

```bash
.venv/bin/python -m pytest -q
# 173 passed in 37.06s

.venv/bin/python -m pytest tests/test_benchmark_manifest.py tests/test_benchmark_results.py -q
# 90 passed in 0.05s
```

`pyproject.toml` parses as valid TOML and every declared field has the
expected value (name `chimera`, version `0.1.0`, `requires-python
>=3.9`, runtime dependency `playwright>=1.40,<2.0`, `dev` extra
`pytest>=7.4,<9.0`, backend `setuptools.build_meta` with
`setuptools>=61`, `packages = ["chimera"]`, pytest `testpaths`/
`pythonpath`, **no** `license` key). The package was **not** installed —
`pip install -e .` would modify the working environment, which is out of
scope.

**Four documentation defects were found and fixed** — all of them cases
of a planned or absent thing being presented as present:

1. **ADR-005 claimed an implementation that does not exist.** Its Status
   read "*the runner implements it, but the implementation is not yet
   verified by the test suite*". In fact `benchmarks/runner.py` and
   `tests/test_benchmark_runner.py` **do not exist**. The Status, the
   enforcement point, and the file references now say plainly that the
   control is **planned, not implemented**.
2. **`benchmark_design.md` §14/§14.1 asserted the same thing.** AMB-9's
   row said "*Resolved in Stage 2*" and §14.1 named
   `benchmarks/runner.py::check_policy_alignment` as *the* enforcement
   point, while Stage 2 has not begun. AMB-9 is now marked **ruled but
   not implemented**, §14 carries an explicit callout that **none** of
   the runner behaviour it describes (§§14.1–14.3) is implemented, and
   the section's out-of-order numbering (§15 appeared before
   "§14 Related documents") was fixed by renumbering the ambiguities
   section to §14 and the trailing section to §15.
3. **`README.md` and `docs/user_guide.md` still said 83 tests.** The
   harness added 90 more, so the suite is **173**. Both documents now
   state 173, list the harness group as a third test group (stdlib-only,
   no browser), and the user guide's repository layout now includes
   `benchmarks/` and the two harness test files. The README's
   limitations now say the harness's *contracts* exist while the runner,
   the independent verifier, the action observer, and Baseline A do not.
4. **`docs/adr/README.md` did not index ADR-005.** It now does, with
   Status **Proposed**.

**Not executed, and not claimed as verified:** `pip install -r
requirements-dev.txt`, `pip install -e .`, `python -m playwright install
chromium`, `open demo_app/index.html`, and any benchmark run. The first
three are prohibited installs; the fourth opens a GUI; and the benchmark
cannot run because its runner does not exist. The repository is **not** a
git working tree, so "inspect the final diff" was performed by reading
the changed files and re-deriving their contents, not via `git diff`.

**No benchmark run has been performed.** Unchanged from the previous
session: every number in `docs/benchmark_design.md` and
`docs/evaluation.md` is either a schema placeholder, an explicitly
labelled illustrative example, or a confidence bound computed from a
stated sample size.

#### Verification performed in the benchmark-harness Stage 2 session

Stage 2 added the runner (`benchmarks/runner.py`), 41 runner tests, and
the doc updates listed above. **No application, safety, tracing, or
existing test code was modified; no package was installed.** The
173-test baseline was re-run unchanged and still passes; the 41 new
tests are the only addition.

```bash
.venv/bin/python -m pytest tests/test_benchmark_runner.py -q
# 41 passed in 0.21s

.venv/bin/python -m pytest -q
# 214 passed in 35.58s

.venv/bin/python -m unittest tests.test_benchmark_runner
# Ran 41 tests — OK
```

Per-file counts: `test_benchmark_runner.py` 41,
`test_benchmark_manifest.py` 46, `test_benchmark_results.py` 44,
`test_safety.py` 25, `test_tracing.py` 20, `test_integration.py` 19,
`test_faults.py` 17, `test_agent.py` 2 — **214 total, of which 173 are
the pre-existing baseline and 41 are new runner tests.**

What the four numbers mean, kept separate:

- **Runner unit tests (41).** Harness behaviour against fake executors
  and fixture traces. All pass.
- **Executed benchmark episodes (0 real).** One test executes the full
  shipped dev manifest — 16 cells × 5 trials + 1 warm-up — with a fake
  executor; those 81 episodes prove orchestration, not performance.
  The default executor (real agent, real Chromium) has no benchmark
  run behind it yet.
- **Independent verification (does not exist).** The verifier,
  action observer, Baseline A, verifier audit, and report generator
  are still unbuilt, so false-success and unauthorised-action rates
  are unmeasurable by construction.
- **Actual performance measurements (none).** No success rate, latency,
  or retry figure has been measured; every acceptance gate in
  `docs/evaluation.md` §7 stays "not measured" except the regression
  suite.

Environment note: the full suite must run **outside** the coding tool's
shell sandbox — under it, Chromium segfaults at launch (SIGSEGV) and
all 21 browser tests fail before any project code runs. Re-running one
browser test unsandboxed passed, and the full `214 passed` result above
was obtained unsandboxed. The sandboxed failure is environmental, not a
regression: the browser tests touch no harness code.

Three test-authoring issues were found and fixed while writing the new
tests (all in the tests, none in product code): comparing bare `id()`
values for token freshness (CPython reuses freed ids — the test now
retains the tokens and asserts pairwise identity); divergence fixtures
that the manifest validator itself would reject (replaced with
valid-but-divergent manifests); and `mock.patch.dict(sys.modules)`
being bypassed by `import … as` (which resolves via the parent
package attribute — the runner now uses `importlib.import_module`, so
the fail-closed path is genuinely exercised).

**No benchmark run has been performed.** Unchanged: the runner exists
and is tested, but without the independent verifier no honest run is
possible, and none was attempted.

#### Verification performed in the benchmark-harness Stage 3 session

Stage 3 added the verifier (`benchmarks/verifier.py`), the agent's
optional `observe` hook (`chimera/agent.py`), the runner wiring, 39
verifier unit tests, 2 verifier browser tests, and the doc updates
listed above. **No safety, tracing, manifest, or result-schema code
was modified; no package was installed.** The `observe` hook's default
path adds no result keys and no trace events, and the full pre-existing
suite passes unchanged around it.

```bash
.venv/bin/python -m pytest tests/test_benchmark_verifier.py -q
# 39 passed in 0.09s

.venv/bin/python -m pytest tests/test_verifier_browser.py -q
# 2 passed in 6.02s

.venv/bin/python -m pytest -q
# 255 passed in 41.68s

.venv/bin/python -m unittest tests.test_benchmark_verifier
# Ran 39 tests — OK
```

Per-file counts: `test_benchmark_verifier.py` 39,
`test_benchmark_runner.py` 41, `test_benchmark_manifest.py` 46,
`test_benchmark_results.py` 44, `test_safety.py` 25,
`test_tracing.py` 20, `test_integration.py` 19, `test_faults.py` 17,
`test_agent.py` 2, `test_verifier_browser.py` 2 — **255 total, of
which 214 are the pre-existing baseline and 41 are new verifier
tests.**

What is measurable now versus still unavailable:

- **Now measurable (when snapshots exist):** per-episode P1–P3
  verdicts with evidence references, per-cell `independent_verification`
  counts, per-cell `false_successes` counts, and per-cell
  `verifier_disagreements` counts. (Retries, action counts, outcomes,
  and latencies were already measured in Stage 2.)
- **Still unavailable, with reasons:** `false_success_rate` (rate +
  Wilson bounds are report-stage work), `unauthorized_actions` /
  `safety_violations` (no action observer), `inconclusive` (no
  `INCONCLUSIVE` state), model/operator metrics (no model, no
  operator), `verifier_audit` (no human audit procedure). Any episode
  without a verified snapshot keeps `unavailable` evidence and is
  excluded from classification — and any cell containing such an
  episode keeps its verification-gated aggregates unavailable.

Kept separate, as before: **verifier unit tests (39)** prove harness
behaviour against fixtures; **executed benchmark episodes (0 real)**
— the 2 browser tests are observation checks on single episodes, not
a benchmark run; **independent verification (exists)** now populates
per-episode evidence, but its human audit does not; **actual
performance measurements (none)** — no rates have been measured and
every `docs/evaluation.md` §7 gate stays "not measured" except the
regression suite.

Two test-authoring issues were found and fixed while writing the new
tests (both in the tests, none in product code): a helper parameter
named `expected` that silently swallowed the `expected_stored_name`
keyword into the snapshot dict (the substring test then passed for
the wrong reason — the helper now names the parameter exactly); and
a naive substring-based independence scan that flagged the
verifier's own docstrings (replaced with an AST-precise scan of
imports and code names).

**No benchmark run has been performed.** Unchanged: the runner and
verifier exist and are tested, but no benchmark run was attempted in
this session (out of scope), so no performance number exists.

#### Verification performed in the benchmark-harness Stage 4 session

Stage 4 added the observer (`benchmarks/observer.py`), the agent's
optional `browser_factory` hook (`chimera/agent.py`), the runner
wiring, 45 observer unit tests, 2 observer browser tests, and the doc
updates listed above. **No safety, tracing, manifest, verifier, or
result-schema code was modified; no package was installed.** The
`browser_factory` default path launches exactly as before, and the
full pre-existing suite passes unchanged around it.

```bash
.venv/bin/python -m pytest tests/test_benchmark_observer.py -q
# 45 passed in 0.10s

.venv/bin/python -m pytest tests/test_observer_browser.py -q
# 2 passed in 6.04s

.venv/bin/python -m pytest -q
# 302 passed in 47.98s

.venv/bin/python -m unittest tests.test_benchmark_observer
# Ran 45 tests — OK
```

Per-file counts: `test_benchmark_observer.py` 45,
`test_benchmark_verifier.py` 39, `test_benchmark_runner.py` 41,
`test_benchmark_manifest.py` 46, `test_benchmark_results.py` 44,
`test_safety.py` 25, `test_tracing.py` 20, `test_integration.py` 19,
`test_faults.py` 17, `test_agent.py` 2,
`test_verifier_browser.py` 2, `test_observer_browser.py` 2 —
**302 total, of which 255 are the pre-existing baseline and 47 are
new observer tests.**

What is measurable now versus still unavailable:

- **Now measurable (when action records exist):** per-episode
  `unauthorized_actions` and `safety_violations` counts, per-cell
  aggregates (`{"total", "mean_per_trial"}`), and the run-level
  unauthorized-action total. (Verification, retry, outcome, and
  latency metrics were already measured in Stages 2–3.)
- **Still unavailable, with reasons:** `false_success_rate` (rate +
  bounds are report-stage work), `inconclusive` (no `INCONCLUSIVE`
  state), model/operator metrics (no model, no operator),
  `verifier_audit` (no human audit procedure). Any episode without a
  complete, attached, run-matching log — or with an `unknown`
  decision — keeps its action metrics `unavailable`, and any cell or
  run containing such an episode keeps its aggregates unavailable.

Kept separate, as before: **observer unit tests (45)** prove harness
behaviour against fixtures; **executed benchmark episodes (0 real)**
— the 2 browser tests are single-episode observation checks, not a
benchmark run; **action observation (exists)** now populates
per-episode metrics from Playwright-boundary records, never from the
agent's trace; **actual performance measurements (none)** — no
violation rates have been measured, no safety improvement is
claimed, and every `docs/evaluation.md` §7 gate stays "not measured"
except the regression suite.

One product-code issue was found and fixed by the new tests: derived
locator targets (`{"by": "derived"}`) initially judged `denied`
instead of `unknown`, because the policy only special-cased a
missing `by` key. The judge now treats any locator construction
outside label/role/css as unresolvable.

**No benchmark run has been performed.** Unchanged: the runner,
verifier, and observer exist and are tested, but no benchmark run
was attempted in this session (out of scope), so no performance
number exists.

#### Verification performed in the benchmark-harness Baseline A session

Baseline A added the replay driver (`benchmarks/baseline_a.py`), the
runner integration, 26 replay unit tests, 5 replay browser tests, and
the doc updates listed above. **No `chimera/`, safety, tracing,
manifest, verifier, observer, or result-schema code was modified; no
package was installed.** The pre-existing suite passes unchanged
around the additive runner branch (verified: 302 passed before the
first Baseline A edit).

`PROJECT_CHIMERA_SRS.md` is absent from the working tree (only
ADR-004 references it), so `docs/benchmark_design.md` §6 and
`docs/evaluation.md` §5 were treated as the operative Baseline A
specification.

```bash
.venv/bin/python -m pytest tests/test_baseline_a.py tests/test_baseline_a_browser.py -q
# 31 passed in 2.45s

.venv/bin/python -m pytest -q
# 333 passed in 49.24s

.venv/bin/python -m unittest tests.test_baseline_a
# Ran 26 tests — OK
```

Per-file counts: `test_baseline_a.py` 26,
`test_baseline_a_browser.py` 5, `test_benchmark_observer.py` 45,
`test_benchmark_verifier.py` 39, `test_benchmark_runner.py` 41,
`test_benchmark_manifest.py` 46, `test_benchmark_results.py` 44,
`test_safety.py` 25, `test_tracing.py` 20, `test_integration.py` 19,
`test_faults.py` 17, `test_agent.py` 2,
`test_verifier_browser.py` 2, `test_observer_browser.py` 2 —
**333 total, of which 302 are the pre-existing baseline and 31 are
new Baseline A tests.**

What the browser tests establish (single episodes, not rates): replay
succeeds on `S-NORM` with the independent verifier agreeing
(`all_satisfied is True`), and fails on `S-SLOW`, `S-DIS`, and
`S-SLOWDIS` — the §6 prediction, observed at the fill step on fault
scenarios. **No benchmark run has been performed and no rate has
been measured**; every `docs/evaluation.md` §7 gate stays "not
measured" except the regression suite.

Two issues were found by the new tests and fixed (both in new code,
none in pre-existing code): Playwright `timeout=0` disables the
timeout (waits indefinitely) rather than disabling waiting, so the
first replay build waited out `S-SLOW` and hung forever on `S-DIS` —
replay now uses a fixed 100 ms action timeout, pinned by test below
every shipped slow value; and one browser-test batch stalled 30
minutes behind an unanswered sandbox-escalation prompt (Chromium
cannot launch in this tool's sandbox at all — verified with a
throwaway probe across four launch flag sets), so browser runs now
carry a shell `timeout` bound.

**No benchmark run has been performed.** Unchanged: the runner,
verifier, observer, and Baseline A exist and are tested, but no
benchmark run was attempted in this session (out of scope), so no
performance number exists.

#### Verification performed in the verifier-audit session

The audit session added `benchmarks/audit.py`, 28 audit tests, a
`docs/user_guide.md` §15.1 procedure, and the doc updates listed
above. **No runner, verifier, observer, Baseline A, manifest,
result-schema, or `chimera/` code was modified; no package was
installed.** The pre-existing suite passes unchanged (verified: 333
passed before the first audit edit).

SRS location (resolving the Baseline A open item): the canonical
`PROJECT_CHIMERA_SRS.md` is **not** in the repository. Two identical
copies exist in the project workspace outside the repo:
`/Users/kartikbhardwaj/Desktop/Chimera/PROJECT_CHIMERA_SRS.md` and
`/Users/kartikbhardwaj/Downloads/PROJECT_CHIMERA_SRS.md`
(byte-identical, 40867 bytes). Its only "audit" mentions are trace
audit events (§8) and recovery auditability (§7.3 checklist) — it
specifies **no** verifier-audit procedure, so design §5,
evaluation.md §§2/6.1/8.3, and the approaches document's Family G
lesson remain the operative audit specification. There is still no
Git repository (`fatal: not a git repository`).

```bash
.venv/bin/python -m pytest tests/test_audit.py -q
# 28 passed in 0.21s

.venv/bin/python -m pytest -q
# 361 passed in 49.64s

.venv/bin/python -m unittest tests.test_audit
# Ran 28 tests — OK
```

Per-file counts: `test_audit.py` 28, `test_baseline_a.py` 26,
`test_baseline_a_browser.py` 5, `test_benchmark_observer.py` 45,
`test_benchmark_verifier.py` 39, `test_benchmark_runner.py` 41,
`test_benchmark_manifest.py` 46, `test_benchmark_results.py` 44,
`test_safety.py` 25, `test_tracing.py` 20, `test_integration.py` 19,
`test_faults.py` 17, `test_agent.py` 2,
`test_verifier_browser.py` 2, `test_observer_browser.py` 2 —
**361 total, of which 333 are the pre-existing baseline and 28 are
new audit tests.**

One design tightening came out of the new tests: partial human
verdicts (a strict subset of the verifier's checks) are now refused
at apply time rather than scored as disagreements, because a
half-recorded judgment would misrecord the human's intent.

**No benchmark run has been performed and no human sample has been
adjudicated.** The audit tooling is tested against fixtures of known
verdicts; that proves the machinery can sample, validate, and count
— it says nothing about the verifier's accuracy, and every
`docs/evaluation.md` §7 gate stays "not measured" except the
regression suite.

#### Verification performed in the report-template session

The report session added `benchmarks/report.py`, 34 report tests,
a `docs/user_guide.md` §15.2 procedure, and the doc updates listed
above. **No runner, verifier, observer, Baseline A, audit,
manifest, result-schema, or `chimera/` code was modified; no
package was installed.** The pre-existing suite passes unchanged
(verified: 361 passed before the first report edit).

```bash
.venv/bin/python -m pytest tests/test_benchmark_report.py -q
# 34 passed in 0.21s

.venv/bin/python -m pytest -q
# 395 passed in 50.14s

.venv/bin/python -m unittest tests.test_benchmark_report
# Ran 34 tests — OK
```

Per-file counts: `test_benchmark_report.py` 34, `test_audit.py` 28,
`test_baseline_a.py` 26, `test_baseline_a_browser.py` 5,
`test_benchmark_observer.py` 45, `test_benchmark_verifier.py` 39,
`test_benchmark_runner.py` 41, `test_benchmark_manifest.py` 46,
`test_benchmark_results.py` 44, `test_safety.py` 25,
`test_tracing.py` 20, `test_integration.py` 19, `test_faults.py` 17,
`test_agent.py` 2, `test_verifier_browser.py` 2,
`test_observer_browser.py` 2 — **395 total, of which 361 are the
pre-existing baseline and 34 are new report tests.**

Two issues were found by the new tests and fixed (both in new
code, none in pre-existing code): `Metric.unavailable("")`
rightly rejects an empty reason, so the renderer's missing-key
fallbacks now carry explicit reasons; and one over-broad assertion
expected a disagreement-case trial ID to appear nowhere in the
report, when the artifacts section correctly lists every episode —
the assertion is now scoped to the audit section. The sandboxed
full-suite run fails only the 30 browser tests with the known
Chromium `TargetClosedError` (verified same cause); the quoted
395-pass result is the unsandboxed run.

**No benchmark run has been performed and no human sample has been
adjudicated.** Fixture renders assert report shape only — Wilson
bounds, section presence, provisional wording, refusal behaviour —
and every `docs/evaluation.md` §7 gate stays "not measured" except
the regression suite.

### Tracing artifact shape (FR-018)

Each run writes a single `data/traces/<run_id>.json` file with this
top-level shape:
```json
{
  "schema_version": 1,
  "run_id": "<uuid4>",
  "agent_version": "milestone-1-foundation",
  "started_at": "2026-10-23T...Z",
  "completed_at": "2026-10-23T...Z",
  "terminal_status": "succeeded" | "failed",
  "event_count": <int>,
  "events": [ ... ]
}
```
Each event has `sequence_number` (1-indexed, monotonic), `event_type`,
`timestamp` (UTC ISO-8601 with millisecond precision + `Z`), `action_type`,
`action_outcome` (`ok` | `failure`), `error_details` (type/message/cause
on failure), and `evidence_references` (URLs, screenshot paths,
postcondition names). Event types in the happy path are
`run_started → action_attempted → action_succeeded → …
→ verification_passed → run_succeeded`; failures insert `action_failed`
events with screenshot evidence and a terminal `run_failed`.

### Cancellation semantics (FR-021)

`create_project(..., cancel=token)` takes an optional
`CancellationToken`. A caller (typically a timer or a sibling thread)
calls `token.request(reason)`; the agent observes it and aborts.

- **Cooperative, not preemptive.** An in-flight synchronous Playwright
  call is *not* interrupted — it runs to completion (or its own
  timeout). The cancel is observed at the next safe boundary. Verified
  by `test_cancel_during_in_flight_action_is_cooperative`, which
  asserts the in-flight fill completed and that the following click
  never ran.
- **Safe boundaries.** The token is checked before each action, between
  actions, between verifications, at the top of every retry iteration
  inside `execute_with_retry`, inside the `is_effect_achieved` state
  check, and before the retry sleep.
- **No cross-thread Playwright control.** The token is a plain flag
  read by the agent's own thread; no Playwright object is ever
  touched from another thread, and no thread is force-killed.
- **Distinct outcome.** A cancelled run reports `success=False`,
  `cancelled=True`, `status="cancelled"`, and the trace terminal event
  is `run_cancelled` with `action_outcome="cancelled"` (exactly one).
  Cancellation is never reported as success or as an ordinary failure.
- **Precedence.** A trace-write failure overrides the cancelled
  outcome to `status="failed"`, `success=False`, `cancelled=False`
  (FR-034 wins: a run that cannot be traced cannot be reported as a
  clean cancellation).
- **Backward compatible.** Callers that pass no token see the previous
  behavior; `cancelled` defaults to `False` and `status` is
  `"succeeded"` or `"failed"`.

### Session isolation (NFR-012) — audit result: MET

**Finding: NFR-012 was already satisfied by the existing code; no
correctness fix was needed.** The audit verified the real Playwright
behaviour rather than assuming it:

- `Browser.new_page()` is documented as *"Creates a new page in a new
  browser context"*. So even the old code got a fresh context per
  run, not a shared one.
- Each `create_project()` call additionally launches its **own
  Chromium instance** and closes it in `finally`, so there is no
  shared browser profile to leak from either.
- Cookies, local storage, and all other session state live in the
  `BrowserContext`; a new context starts with an empty cookie jar.

**What changed anyway (lifecycle clarity, not a bug fix):** the agent
now creates the context explicitly and closes it explicitly —
`browser.new_context()` → `context.new_page()` → `finally:
context.close()` then `browser.close()`. Previously the context was an
implicit side effect of `browser.new_page()` and was reclaimed only by
the browser teardown. Playwright's own docs call the convenience API
"a shorthand for `browser.new_context().newPage()`" and say production
code should use the explicit form "to control their exact life times".
The explicit form also makes the NFR-012 isolation unit a first-class
object that the tests can assert against.

**Evidence (tests, not assertions):**
- `test_each_run_gets_a_fresh_browser_context` — two runs create two
  distinct `BrowserContext` objects on two distinct `Browser`
  instances, each context bound to its own run's browser.
- `test_session_state_does_not_leak_between_runs` — a probe cookie is
  seeded into every context the agent creates; each run's context is
  observed to start with an **empty** cookie jar, so run 2 cannot see
  run 1's state. (Evidence is captured *during* the run: Playwright's
  event loop is torn down when the run returns, so the context objects
  cannot be inspected afterwards.)
- `test_browser_resources_are_closed_after_each_run` — exactly one
  context and one browser are closed per run, on both the success and
  the failure path.
- `test_cancelled_run_also_closes_its_context` — a cancelled run also
  closes its context and browser.
- **Negative control:** mutating the agent to share one context across
  runs makes both isolation tests FAIL; reverting makes them pass. The
  tests are therefore load-bearing, not vacuous.

### Browser integration: observed outcomes

All observed against real Chromium via Playwright. Durations are wall-clock
end-to-end (including browser startup per fixture).

| URL                              | `success`? | Observed duration | Notes                                                                  |
|----------------------------------|-----------|-------------------|------------------------------------------------------------------------|
| (no params)                      | `True`    | 0.12 s            | Baseline happy path.                                                   |
| `?slow=2000`                     | `True`    | 2.37 s            | Slow delay dominates; Playwright auto-waits for the form to re-enable. |
| `?disabled=1`                    | `False`   | 5.06 s            | FILL times out at `ACTION_TIMEOUT_MS`; `BlindRetryRefusedError` raised. |
| `?slow=2000&disabled=1`          | `False`   | 5.05 s            | FILL waits ~2 s, then sticky `disabled` re-disables; times out at 5 s. |
| (Reset, with `?disabled=1`)      | n/a       | 0.10 s            | List, confirmation, input, disabled attr, fault-status all cleared.    |
| Tracing: no-fault run            | `True`    | (within suite)    | Artifact written, terminal = `run_succeeded`, both postconditions present; exactly one event per action. |
| Tracing: `?disabled=1` run       | `False`   | (within suite)    | Artifact written, terminal = `run_failed`, screenshot evidence on last failure. |
| Tracing: unwritable trace_dir    | `False`   | (within suite)    | Agent-level FR-034: trace write failure forces `success=False` with `TraceWriteError` surfaced. |

**Key empirical finding:** the `slow + disabled` failure total is ~5 s,
not ~7 s. The FILL wrapper's `BlindRetryRefusedError` (no
`is_effect_achieved` is supplied, so the second attempt is refused)
means the run consumes one `ACTION_TIMEOUT_MS` window, not two. The
bound is truly `≤ ACTION_TIMEOUT_MS` for both the persistent-disabled
and slow+persistent-disabled cases.

### Known limitations
- **Per-attempt timeout still implicit.** `ACTION_TIMEOUT_MS` is passed
  to each Playwright call, but `chimera.safety.execute_with_retry` does
  not enforce a per-attempt timeout itself; it relies on the caller's
  Playwright actions to honor it. A future change could move the
  timeout into the safety wrapper using a thread-join, but that is a
  feature, not a fix.
- **Allowlist still type-only.** The allowlist validates action *types*
  but not targets/URLs. A `NAVIGATE` action can be sent to any URL
  passed to `page.goto()`; `FILL` and `CLICK` validate neither the
  locator nor the value. URL/target allowlisting belongs in a higher
  layer (the future workflow compiler).
- **Screenshots are only attached to `action_failed` events.** They are
  not taken for `verification_failed` (which is also a run-level
  failure). Coverage gap is intentional today — adding a duplicate
  capture would inflate evidence with redundant frames. A future task
  may unify failure evidence under one event.
- **One browser per test.** Each integration test launches its own
  Chromium via the per-test `browser` fixture, which is correct
  isolation but slow (~0.1 s setup overhead × 9 ≈ 0.9 s of the
  20.2 s total). A module-scoped fixture is a future optimisation,
  not a correctness issue.
- **Cancellation is cooperative, so it is not instantaneous.** The
  worst-case delay between `token.request()` and the run stopping is
  bounded by the in-flight action's own timeout
  (`ACTION_TIMEOUT_MS`, currently 5s). A user-visible "stop" button
  would therefore feel sluggish on a slow action. There is no
  mechanism to interrupt a synchronous Playwright call safely.
- **Isolation is per-run, not per-suite.** Each run launches and tears
  down its own Chromium, which is the strongest isolation but also the
  slowest. Sharing one browser across runs (with a fresh context per
  run) would be much faster, but that is a deliberate trade-off to
  revisit only with the threat model in hand.

### What is NOT yet done (next-session backlog)
1. **Eval human-audit adjudication (deferred).** Runs are done: dev
   (audited, 100% agreement) and held-out eval (provisional) for
   Chimera and Baseline A, with full evidence and rendered reports
   under `artifacts/`. What remains is adjudicating an eval sample —
   the 8-episode stratified mini-plans are drawn and awaiting review
   (`tools/audit_review.py`), after which `apply_audit` + a re-render
   produce the audited eval report. Until then the eval figures stay
   provisional and no eval performance claim beyond the provisional
   report may be made.
2. **Relabel the project's colliding "FR-018" shorthand** (ADR-004
   follow-on, proposed): rename it to a non-colliding label across
   `CURRENT_STATUS.md`, docstrings, and test names, and record the rename
   in a further ADR.
3. **Resolve the six open requirement-mapping questions** (ADR-004) —
   these need an owner ruling, not a coding task. Q3 (is the trace the
   FR-036 report?) and Q4 (where does `INCONCLUSIVE` sit?) most directly
   limit what the benchmark can measure.
4. **Known SRS gaps not yet closed** (documented, not implemented): no
   target/URL/locator allowlist (NFR-016 is only half met), no
   `INCONCLUSIVE` terminal state (SRS §9, NFR-001), no code-validated state
   machine (§9), trace schema is a subset of §8.3/§8.4, no redaction pass
   for traces/screenshots (NFR-019 partial), no run-level action budget
   (FR-022 partial), and no §12.4 adversarial test suite. Full list with
   threat mapping in `docs/threat_model.md` §5, and the six open
   requirement-mapping questions above.
5. **Minor setup residuals, all optional.** No `scripts/` directory
   (SRS §15 mentions it, but every command is documented and runnable
   without it); no `LICENSE` file, so `pyproject.toml` declares no
   license; no `[project.scripts]` console entry point, because
   `chimera/agent.py` has a `__main__` block but no importable `main()`
   and adding one would mean changing application code; and no
   environment-variable configuration, because the code reads none.

### Research console — visual-intelligence layer (2026-10-30 session)

Six signature visualizations delivered over the frozen evidence,
zero new dependencies, zero benchmark/product files changed:

- **A. Outcome Terrain** (`research/js/pages/terrain.js`, `#/terrain`):
  uniform fault-aware tiles with per-trial dots, filters, cell
  inspection with mirror baseline.
- **B. Evidence River** (`research/js/pages/river.js`, `#/river`):
  scenario → baseline → outcome → cell-audit flow with exact
  counts, click-to-filter, record-list alternative.
- **C. Signal vs Uncertainty** (`dotPlot` in `research/js/charts.js`
  + Observatory section): per-cell/per-scenario Wilson intervals,
  descriptive-only overlap note.
- **D. Failure Topography** (`faultTransect` + Failures section):
  discrete soundings at tested `slow_ms` levels, soundings table.
- **E. Episode Oscilloscope** (`scopeStrip` + Evidence section):
  zoomable lanes over trace/observer/verdict coordinates with a
  detail panel; stored traces are tiny (≤10 events), so every mark
  renders directly.
- **F. Provenance Graph** (`research/js/pages/lineage.js`,
  `#/lineage`): identifier-validated lineage per run cell with
  search, neighbor highlight, node/edge tables.
- Shared kit: `research/js/viz/stats.js`, `tooltip.js`,
  `particles.js` (ambient field + persisted Motion toggle),
  DOM-free `*Model.js` modules.

Verification this session (commands run, actual results):

- `node --test research/js/viz/*.test.mjs
  research/js/charts.test.mjs research/js/pages/*.render.test.mjs`
  → **45 passed, 0 failed** (models + renderers vs real evidence).
- `node --check` on every touched JS file → clean.
- `.venv/bin/python -m pytest tests/test_research_console.py -q`
  in an approved unsandboxed run → **28 passed in 19.79s**
  (16 pre-existing + 12 new). The first run caught two real bugs,
  both fixed with tests: mobile-drawer stacking regression
  (`#scrim` moved inside `.shell`) and fragile `?cell=` key
  matching (structural `stats.matchCellKey`). One transient
  recovery-route error appeared in one run; green alone and on
  repeat (recorded in the Test Plan).
- `.venv/bin/python -m pytest tests/ -q` inside the sandbox →
  391 passed; remaining failures/errors are all browser/socket
  tests blocked by the sandbox (Chromium SIGSEGV, bind denied),
  unrelated to these changes.
- 8 screenshots captured for the new routes/sections
  (`docs/research/img/`, zero page errors); river, lineage,
  topography, and oscilloscope shots reviewed with counts
  cross-checked against run files.

Remaining console work: screen-reader pass (landmarks in place,
unverified); adjudicate the eval mini-sample (unchanged next
task below).

### Eval mini-review preparation (2026-10-29 session)

The frozen 8-episode eval mini-sample is prepared for rigorous
human adjudication. No features added to the viz layer; no reruns;
no frozen files modified (runs, plans, manifest, traces,
snapshots, action logs all read-only; generator refuses to
overwrite recorded decisions).

Frozen selection (one per scenario per baseline, from the
`*.audit-plan-mini.json` plans, manifest sha `b23580c8…` verified
against `benchmarks/manifests/eval-v1.json`):

- Chimera: trial-0006 (S-NORM), trial-0055 (S-SLOW/slow 2100),
  trial-0100 (S-DIS), trial-0142 (S-SLOWDIS/slow 2100) — all I-SPACE
- Baseline A: trial-0009 (S-NORM), trial-0052 (S-SLOW/slow 2100),
  trial-0098 (S-DIS), trial-0143 (S-SLOWDIS/slow 2100) — all I-SPACE

Delivered:

- `artifacts/eval-20261028/mini-review/` — `packet.json` (all 8
  episodes with recorded outcomes, verifier P1–P3, evidence
  excerpts, artifact paths + verified sha256, gaps),
  `PACKET.md` (human-readable), `decisions.json` (all pending).
- `tools/mini_review.py` — `build-packet` (fails closed on any
  ID/outcome/digest/count mismatch) and `validate` (schema,
  resolution, blinding-protocol consistency, evidence freshness,
  human-vs-verifier comparison with n=8 caveat).
- Console `#/review` — blinded queue (masked recorded verdicts,
  assess → reveal → agree with proving timestamps), verdict form
  (assessment/agreement/sufficiency/reason/missing evidence),
  corrections history, export/import `decisions.json`,
  pending/reviewed status, audit summary. Console never writes
  repo files. Evidence reuses Evidence Inspector renderers
  (exported pure functions; behavior preserved).
- Known evidence shape (documented, not a blocker): successes
  carry no screenshots (harness captures only on action
  failure); replay reports lack timestamps/sequences; blinding
  is partial (run IDs visible, trace shape differs by driver).

Verification this session:

- `tools/mini_review.py build-packet` → 8 episodes, all 24
  artifact digests verify, plan↔run outcomes/checks agree.
- `tools/mini_review.py validate` → valid, `0/8 IN PROGRESS`.
- `tests/test_mini_review.py` → 6 passed (selection,
  determinism, fail-closed mutations, overwrite refusal, rules,
  drift detection).
- Node suite → 60/60 (added `reviewModel` 10 + review render 5).
- Console browser suite (approved unsandboxed run) → 30/30,
  including the blinded review-flow test; caught and fixed one
  real bug (`loadState` dropped partials, breaking two-phase
  save). Review screenshots captured with zero page errors.

Audit status: NOT complete — 0/8 human decisions recorded. No
LLM verdicts anywhere; nothing adjudicates on its own.

### Audit evidence finalized (2026-10-29 session)

The 8-episode mini-audit evidence bundle is built, verified, and
documented. Selection unchanged; no reruns; no frozen files
modified; no human decisions recorded (`decisions.json` still
pending, byte-identical).

Delivered in `artifacts/eval-20261028/mini-review/`:

- `evidence-bundle.zip` (sha256 `2be304c8…`) — 29 verified
  originals (24 trace/snapshot/action files, 2 failure
  screenshots, frozen manifest, both mini plans) plus
  `BUNDLE_MANIFEST.json` with path/size/sha256 per file.
  Deterministic (byte-reproducible); every zipped byte
  re-verified identical to the frozen originals.
- `reviewer-packet.json` — evidence for P1–P3 judgment with
  zero answer-revealing keys (scan-enforced at build;
  independent re-scan confirms).
- `answer-key.json` — recorded outcomes + verifier checks,
  stored separately, labeled do-not-distribute until locked.
- `READY_FOR_REVIEW.md` — bundle contents, distribution rules,
  two-phase protocol, exact reviewer steps, validation
  results, limitations.
- `packet.json` / `decisions.json` proven byte-unchanged
  across all operations.

Notes: the manifest cross-check uses the loader's canonical
sha (`b23580c8…`), not raw file bytes — the builder initially
compared raw bytes, failed closed loudly, and was corrected.
Reviewer blinding is partial by evidence shape (documented);
no cryptographic blinding is claimed (static HTTP).

Also fixed this session: reveal-after-assessment is now
enforced in `#/review` (no reveal control exists before the
assessment is saved); boot fetch retry (one) for transient
static-server drops with Node coverage both ways; lineage
browser-test waits hardened against stale-DOM matches.

Verification: `validate` → 0/8 IN PROGRESS; `test_mini_review`
9 passed; Node 63/63; console browser suite 30/30
(unsandboxed, after final edits).

Audit status: NOT complete — awaiting human adjudication.

### How to resume
```bash
cd /Users/kartikbhardwaj/project-chimera
source .venv/bin/activate
# Full suite (460 pytest tests: 83 pre-existing + 338 harness + 30 console + 9 mini-review).
# Run outside the coding tool's shell sandbox: Chromium cannot launch under it.
.venv/bin/python -m pytest -q
# Console logic suite (runs anywhere with Node 24+, no browser needed).
node --test research/js/*.test.mjs research/js/viz/*.test.mjs research/js/charts.test.mjs research/js/pages/*.render.test.mjs
```

### Recommended next task
**Eval human-audit adjudication (currently deferred).**
Dev and held-out eval runs are complete with full evidence and
rendered reports; the dev report is audited (100% agreement) and the
eval report is provisional. The next task is to adjudicate the drawn
8-episode eval mini-sample with `tools/audit_review.py`, then
`apply_audit` both runs and re-render. The review packet and blinded queue are ready
(`artifacts/eval-20261028/mini-review/`, console `#/review`);
record all 8 human decisions there, export + validate
`decisions.json`. Suite state: 460 pytest tests (83-test
regression baseline unchanged), of which the 30 console tests
and 9 mini-review tests are green; 63/63 Node console tests
green anywhere. Full-suite browser tests outside the console
file still need an unsandboxed run to confirm.

Scope for the audit stage: recording honest human judgments only. It
must not invent verdicts, must publish the report with whatever
verdict and coverage render (including PROVISIONAL if agreement
lands below 95%), and must never edit runs, evidence, or the frozen
`eval-v1.json`.

Until eval audit completes, every held-out figure stays provisional
and **no eval performance claim beyond the provisional report may be
made**. AMB-9 is ruled on and implemented (ADR-005, Status:
**Accepted**); AMB-1 … AMB-8 still need owner rulings where they
change what the harness must do.
Scope: adjudicating only. Do not build the target/URL/locator allowlist,
the recovery layer, or the model adapter in the same task — those are
backlog item 4 (and a model adapter is not backlogged yet), and the
allowlist in particular would change the agent's behaviour and
therefore invalidate the 83-test baseline.
