# Project Chimera — Architecture

Status: describes the **implemented** system as of Milestone 1 (SRS Phases 0–2
foundation). Requirements authority is
`PROJECT_CHIMERA_SRS.md`. Anything not present in the source tree is labelled
*planned* and is not a guarantee.

---

## 1. Scope of the current system

Chimera executes one hard-coded, deterministic browser workflow against a
controlled local demo application and emits an inspectable execution trace.

The current system has **no** model/LLM integration, no workflow compiler, no
persistence layer, no recovery engine, no evaluation framework, and no
dashboard. It is a foundation milestone, not a finished agent.

---

## 2. Components and responsibilities

| Component | File | Responsibility | Dependencies |
|---|---|---|---|
| Demo application | `demo_app/index.html` | Controlled test target (SRS NFR-011). Static task manager with deterministic fault injection via URL params `?slow=<ms>` and `?disabled=1`, an on-page fault panel, a Reset button, and a submit handler that refuses while Create is disabled. | none (stdlib browser JS) |
| Safety layer | `chimera/safety.py` | Action allowlist (`ActionType` → `ALLOWED_ACTIONS`), bounded retry policy (`RetryPolicy`), the non-blind retry wrapper `execute_with_retry`, and cooperative cancellation (`CancellationToken`, `RunCancelledError`). | Python stdlib only |
| Tracing layer | `chimera/tracing.py` | `TraceRecorder` (append-only event log, monotonic sequence numbers, UTC timestamps, atomic JSON write), `TraceWriteError`, and `capture_failure_screenshot`. | Python stdlib only |
| Agent / executor | `chimera/agent.py` | Playwright orchestration: URL construction, browser/context/page lifecycle, action execution, postcondition verification, trace finalisation, result assembly. | Playwright (sync API) |

`chimera/safety.py` and `chimera/tracing.py` are deliberately free of
third-party imports, so the whole safety and trace contract is unit-testable
with `unittest` and no browser. Playwright is imported lazily inside
`create_project()`, so the URL builders remain usable in environments where
Playwright is absent.

---

## 3. Browser execution lifecycle and context isolation

`create_project()` performs this sequence:

1. `sync_playwright()` context manager.
2. `playwright.chromium.launch(headless=True)` — **one browser per run**.
3. `browser.new_context()` — **one browser context per run**.
4. `context.new_page()` — one page per run.
5. Execute three allowlisted actions and two postcondition verifications (§5).
6. `finally:` → `context.close()` then `browser.close()` (context first: it
   owns the session state; the browser teardown then reclaims the process).

A `BrowserContext` is Playwright's isolation unit. Cookies, `localStorage`,
and every other piece of session state live in the context, so a fresh
context starts with an empty cookie jar. Because each run also gets its own
browser process, there is no shared profile to leak from either. This
satisfies SRS NFR-012 ("browser sessions isolated between test runs").

**Design decision — why one browser *and* one context per run.** The
strongest available isolation is a dedicated browser process with a
dedicated context inside it. The stronger of the two (a separate process)
costs ~0.1 s of launch overhead per run; the weaker (a shared browser with a
fresh context per run) would be faster but shares a process across runs.
Chimera chose the stronger boundary because the current workload is a local
test app where latency is irrelevant and isolation is the property under
audit. Revising this trade-off requires the threat model in
[`threat_model.md`](threat_model.md) to be in hand.

Note also that `browser.new_page()` would *also* have created a fresh context
("creates a new page in a new browser context"), but it hides the context
object and leaves its lifetime implicit. The explicit
`browser.new_context()` → `context.new_page()` form is Playwright's
documented production pattern, makes the isolation guarantee visible in the
code, and lets the tests assert against the context object directly.

---

## 4. Safety and retry boundary

All browser actions funnel through one wrapper:

```python
execute_with_retry(action_type, action, *,
                   policy=DEFAULT_POLICY,
                   is_effect_achieved=None,
                   cancellation_token=None)
```

**Allowlist (NFR-016).** `action_type` must be a member of
`ALLOWED_ACTIONS` — `navigate`, `fill`, `click`, `wait`, `observe`. Anything
else raises `ActionNotAllowedError` before it can reach Playwright.

> **Scope limit, stated plainly:** the allowlist validates the *type* of
> operation only. It does **not** validate the target — no URL allowlist, no
> locator allowlist, no value allowlist. SRS NFR-016 requires "an allowlist of
> permitted operations **and targets**"; only the operations half is
> implemented. See [`threat_model.md`](threat_model.md) §5 for the residual
> risk this leaves open.

**Bounded retry (FR-022, FR-027, FR-028).** `DEFAULT_POLICY` is
`RetryPolicy(max_attempts=2, base_delay_seconds=0.05, max_delay_seconds=0.2,
max_total_seconds=5.0)`. `ACTION_TIMEOUT_MS` is derived from that budget
(`int(max_total_seconds * 1000)` = 5000 ms) and passed to each Playwright
call, so a single action cannot outlive the policy — without it,
Playwright's 30 s default action timeout would silently override
`max_total_seconds`.

Per attempt the wrapper: checks cancellation → runs the action → on failure
checks the wall-clock cap → checks the attempt cap → consults the retry
policy.

**No blind retries (FR-028).** A retry is only granted if the caller supplies
`is_effect_achieved`, a callable that reports whether the intended effect
already happened. Without it, a failed action raises
`BlindRetryRefusedError` immediately rather than repeating. If the supplied
state check itself raises, the run aborts with
`RetryBudgetExhaustedError` instead of burning the remaining budget on a
permanently broken check. Only the CLICK action supplies the hook
(`#confirmation` visibility); NAVIGATE and FILL do not, so a failure in
either consumes exactly one timeout window rather than two.

**Duplicate-effect check (NFR-004).** The CLICK path re-checks
`is_effect_achieved` before any retry, so a state-changing action is not
repeated when the effect may already have occurred.

---

## 5. Cooperative cancellation and its limits

`CancellationToken` is a flag plus a `threading.Event`. A caller (a timer or
a sibling thread) calls `token.request(reason)`; the agent's own thread
observes it and aborts. `request()` is idempotent and the first reason wins.

**Where the token is checked** — every point is a *safe boundary* at which no
Playwright call is in flight:

- before each action (navigate, fill, click) and between actions;
- between the two verifications;
- at the top of every retry iteration inside `execute_with_retry`;
- inside the `is_effect_achieved` state check, so a retry waiting on a slow
  effect bails out promptly;
- immediately before the inter-retry sleep.

**Design decision — why cancellation is cooperative rather than pre-emptive.**
Playwright's synchronous API cannot be interrupted safely from another
thread: the page object is driven by a single greenlet-bound event loop, and
killing or signalling it mid-call risks corrupting the transport, leaking
the browser process, or leaving a half-applied action. Chimera therefore
never touches a Playwright object from an unrelated thread and never
force-kills a thread. An in-flight synchronous call runs to completion (or
to its own timeout) and the cancel is observed at the next boundary.

**The resulting bound.** The worst-case delay between `request()` and the
run stopping is the in-flight action's own timeout — `ACTION_TIMEOUT_MS`
(5 s) today. A user-visible "stop" control would feel sluggish on a slow
action. This is a deliberate, documented limitation, not an oversight.

**Outcome contract.** A cancelled run is a distinct third outcome, never
reported as success and never as an ordinary failure:

- result: `success=False`, `cancelled=True`, `status="cancelled"`;
- trace: exactly one `run_cancelled` terminal event with
  `action_outcome="cancelled"`, and top-level `terminal_status="cancelled"`;
- no failure screenshot is captured — a cancelled run is not an error state,
  and a screenshot would be misleading evidence;
- the context and browser are closed by the surrounding `finally` block.

Callers that pass no token see the previous behaviour unchanged
(`cancelled=False`; `status` is `"succeeded"` or `"failed"`).

---

## 6. Verification, execution traces, JSON artifacts, failure screenshots

**Verification is explicit and independent of the click.** Clicking the
button is not evidence that anything happened. After the click, two
postconditions are verified against live browser state:

1. `#confirmation` is visible;
2. `#project-list li` containing the project name is visible.

Each is a `wait_for(state="visible", timeout=ACTION_TIMEOUT_MS)`. Both must
pass for the run to succeed. A verification failure is a run-level failure
and produces a `run_failed` terminal.

**Trace artifact.** Every run — succeeded, failed, or cancelled — writes one
file to `data/traces/<run_id>.json` (`run_id` is a UUID4). The write is
atomic: a temporary file is written and then `replace()`d into position, so
a reader never observes a half-written artifact and no `.tmp` file is left
behind.

Top level:

```json
{
  "schema_version": 1,
  "run_id": "<uuid4>",
  "agent_version": "milestone-1-foundation",
  "started_at": "<UTC ISO-8601 ms>",
  "completed_at": "<UTC ISO-8601 ms>",
  "terminal_status": "succeeded" | "failed" | "cancelled",
  "event_count": <int>,
  "events": [ ... ]
}
```

Each event carries `sequence_number` (1-indexed, monotonic),
`event_type`, `timestamp` (UTC ISO-8601, millisecond precision, `Z`
suffix), `action_type`, `action_outcome` (`ok` | `failure` | `cancelled`),
`error_details` (type / message / cause chain on failure), and
`evidence_references` (URLs, screenshot paths, postcondition names).

Happy-path event sequence:
`run_started → action_attempted → action_succeeded → … →
verification_passed → run_succeeded`. A failure inserts an `action_failed`
event carrying screenshot evidence and terminates with `run_failed`; a
cancellation terminates with `run_cancelled`.

**Design decision — why a run cannot be reported as successful if trace
persistence fails.** The trace is the evidence record. If it cannot be
written, the run's outcome is unverifiable, and an unverifiable run must not
be reported as a success (SRS FR-034). `TraceRecorder.finish()` therefore
raises `TraceWriteError` on any `OSError`, and `create_project()` catches
it and forces the result to `success=False`, `status="failed"`,
`cancelled=False`, `trace_path=None`, with the write error surfaced in
`result["error"]`. This precedence holds even over a cancellation: a run
that cannot be traced is not a clean cancellation, it is a failure.

**Failure screenshots (NFR-019).** On an action failure, a best-effort
screenshot is captured to `data/screenshots/<run_id>.png` and attached to the
failing event's `evidence_references`. Capture is best-effort: if it fails,
the event records `screenshot_capture_failed` rather than aborting the run.
Screenshots are currently attached to `action_failed` events only, not to
`verification_failed` — an intentional coverage gap, noted in
[`threat_model.md`](threat_model.md) §5.

---

## 7. Data flow and repository layout

```
caller (test / script)
  └─ create_project(name, url=…, trace_dir=…, cancel=token)
       ├─ TraceRecorder(trace_dir)                    → run_id
       ├─ record("run_started", evidence=[url, name])
       ├─ sync_playwright() → chromium.launch()
       │    └─ browser.new_context() → context.new_page()
       ├─ NAVIGATE  page.goto(url)                     ─┐
       ├─ FILL      name_input.fill(name)              │ via execute_with_retry
       ├─ CLICK     create_button.click()              │ (allowlist + bounded retry
       ├─ VERIFY    #confirmation visible              │  + FR-028 + cancellation)
       ├─ VERIFY    #project-list li visible           ─┘
       │    └─ each action/verification emits
       │       action_attempted / action_succeeded / action_failed /
       │       verification_passed / verification_failed
       ├─ on failure: capture_failure_screenshot() → data/screenshots/
       ├─ finish("succeeded" | "failed" | "cancelled")
       │    └─ atomic write → data/traces/<run_id>.json
       │         (TraceWriteError ⇒ result forced to failed)
       └─ finally: context.close() → browser.close()
```

Repository layout:

```
project-chimera/
├── chimera/
│   ├── __init__.py
│   ├── agent.py          # Playwright orchestration
│   ├── safety.py         # allowlist, retry, cancellation   (stdlib only)
│   └── tracing.py        # trace recorder, screenshots        (stdlib only)
├── demo_app/
│   └── index.html        # controlled test target + fault injection
├── tests/
│   ├── test_agent.py         # pytest — browser
│   ├── test_integration.py   # pytest — browser (19 tests)
│   ├── test_safety.py        # unittest — stdlib only (25 tests)
│   ├── test_tracing.py       # unittest — stdlib only (20 tests)
│   └── test_faults.py        # unittest — stdlib only (17 tests)
├── data/
│   ├── traces/          # generated JSON artifacts  (gitignored)
│   └── screenshots/     # generated PNGs             (gitignored)
├── docs/
│   ├── architecture.md
│   └── threat_model.md
├── requirements-dev.txt
├── CURRENT_STATUS.md
└── README.md
```

`data/traces/` and `data/screenshots/` are runtime artifacts and are
gitignored. Traces are append-only per run and are never pruned by the
current code.

---

## 8. Implemented vs. planned capabilities

**Implemented and verified (83 tests: 62 stdlib + 21 Chromium):**

- Controlled local test target with deterministic fault injection and reset.
- One deterministic three-action workflow with explicit postcondition
  verification.
- Action allowlist (type-level) with bounded, non-blind retries.
- Per-run browser + browser context isolation (NFR-012).
- JSON execution trace per run, including failed and cancelled runs.
- Failure screenshots attached as evidence.
- Cooperative cancellation with a distinct terminal outcome (FR-021).
- Trace-write failure cannot be reported as success (FR-034).

**Planned (SRS §§5, 7, 10, 11, 13) — not implemented:**

| Capability | SRS area | State |
|---|---|---|
| Workflow representation and validation (§10) | FR-007…FR-014 | not started |
| Demonstration capture (record/replay) | FR-001…FR-006 | not started |
| Planner and model-provider adapter (§7.4) | FR-015…FR-017 | not started |
| Adaptive recovery | FR-025…FR-030 | not started |
| Independent verification engine (§5.5) | FR-031…FR-036 | partial (two hand-written postconditions only) |
| Persistence: workflow store + execution history | FR-037…FR-042 | not started |
| Dashboard / UI | FR-043…FR-049 | not started |
| Evaluation framework and benchmark (§11, §12) | §11 | not started |
| Execution state machine with validated transitions (§9) | §9 | not started |

---

## 9. Known design limitations

1. **The allowlist is type-level only.** No URL, locator, or value
   allowlisting. `create_project(url=…)` accepts a caller-supplied URL and
   `page.goto()` will open it. This is the largest gap against SRS NFR-016.
2. **No `INCONCLUSIVE` terminal state.** SRS §9 defines twelve states
   including `INCONCLUSIVE`, and NFR-001 requires a run to terminate in
   `succeeded`, `failed`, `cancelled`, **or inconclusive**. Chimera
   currently distinguishes only the first three. "Verification timed out" is
   reported as `failed`, which conflates "the action did not work" with
   "the agent could not tell".
3. **No code-validated state machine.** SRS §9 requires transitions to be
   validated by code. The current flow is a linear `try` block, not a state
   machine.
4. **The trace schema is a subset of SRS §8.3/§8.4.** Missing:
   `workflow_id`, `workflow_version`, `input_values`, `model_provider`,
   `model_identifier`, `final_verification`, `failure_category`,
   `resource_metrics` (run level); `event_id`, `observed_state_reference`,
   `action_proposal`, `executed_action`, `recovery_attempt` (event level).
   `action_outcome` currently carries the SRS `outcome` field.
5. **Cancellation is cooperative and therefore not instantaneous** (§5).
6. **One hard-coded workflow.** `create_project()` is a function, not a
   compiled, validated workflow object. Adding a second workflow means
   writing new orchestration code.
7. **Screenshots are not captured for `verification_failed`.**
8. **No redaction pass.** Traces and screenshots contain whatever the page
   contained. The current demo app holds no credentials or PII, so nothing
   is exposed today, but no scrubbing mechanism exists for real targets.
9. **No prompt-injection defences.** There is no model today, so there is no
   LLM attack surface — but page content is not sanitised, classified, or
   quarantined, so it is not ready for the model-integrated phase.
10. **No authorization layer for consequential actions** (SRS NFR-017).
11. **Unbounded artifact growth.** `data/traces/` and `data/screenshots/`
    accumulate with no rotation or retention policy.
12. **One browser per test** in the suite, which is correct isolation but
    slow.

---

## 10. Planned evolution

The intended direction, from the SRS, with the gaps named in §9 mapped to the
stage that closes them:

1. **Workflow layer (SRS §10).** A declarative, validated workflow
   representation — actions, targets, postconditions — so the executor
   consumes a validated plan instead of hard-coded Python. This is also the
   natural home for the *target* half of the NFR-016 allowlist, and it
   gives §9's state machine something to validate transitions over.
2. **Persistence (FR-037…FR-042).** A workflow store and an execution
   history store, so runs are queryable rather than one-file-per-run in a
   directory, and so the trace schema can grow the SRS §8.3/§8.4 fields.
3. **Planner and model adapter (FR-015…FR-017, §7.4).** A replaceable
   provider adapter so the model is optional and workflows remain
   deterministic without a paid API (NFR-030). The model's proposals enter
   the executor as *untrusted proposals* filtered by the same allowlist —
   see the trust-boundary section of [`threat_model.md`](threat_model.md).
4. **Recovery and verification.** An independent verification engine and
   bounded recovery, both of which require the `INCONCLUSIVE` state to be
   modelled honestly.
5. **Evaluation (§11, §12).** A benchmark and an adversarial test suite,
   including the §12.4 scenarios (prompt-injection text, unexpected
   redirects, ambiguous labels, duplicate records, delayed confirmations,
   stale browser state).
6. **Dashboard (SRS §13).** Read-only visibility over stored artifacts;
   it introduces no new execution authority.

---

## 11. Requirement-label mapping (important)

The project's internal shorthand labels do not all match the authoritative
SRS identifiers, and the mismatch is easy to misread. Where Chimera uses a
label, this is the SRS requirement it actually corresponds to:

| Chimera shorthand | SRS requirement |
|---|---|
| FR-018 (execution tracing) | **not** SRS FR-018 (which is "use deterministic browser primitives"). Tracing maps to SRS FR-036 (verification report), FR-038 (execution history), and the §8.3/§8.4 data model. |
| FR-021 (cancellation) | SRS FR-021 — support cancellation ✅ |
| FR-022 (bounded resources) | SRS FR-022 — limit execution resources ✅ |
| FR-028 (no blind retries) | SRS FR-028 — prevent blind retries ✅ |
| FR-034 (no unsupported success) | SRS FR-034 — prevent unsupported success claims ✅ |
| NFR-012 (session isolation) | SRS NFR-012 ✅ |
| NFR-016 (allowlist) | SRS NFR-016 — operations **and targets**; only operations are enforced |
| NFR-019 (screenshot/trace hygiene) | SRS NFR-019 — partial |

Use the SRS text, not the shorthand, when auditing compliance.

---

## 12. Related documents

- [`threat_model.md`](threat_model.md) — assets, trust boundaries, threats,
  mitigations and their enforcement points, residual risks.
- `CURRENT_STATUS.md` — the running session log: what was built, what was
  measured, known limitations, and the next recommended task.
- `PROJECT_CHIMERA_SRS.md` — the requirements authority.
