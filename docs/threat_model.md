# Project Chimera — Threat Model

Status: describes the **implemented** system as of Milestone 1 (SRS Phases 0–2
foundation), with forward-looking sections clearly marked as *planned*.
Requirements authority is `PROJECT_CHIMERA_SRS.md`; implementation evidence is
the source tree. Controls are named with the file and line-level construct
that actually enforces them, so each claim can be checked.

**Scope caveat.** Chimera today drives a controlled local demo application
(SRS NFR-011) with a single hard-coded workflow and no model. The threat
surface is therefore small today and grows substantially in the planned
phases. Sections marked **Future** describe requirements for capabilities
that do not exist yet and are not guarantees of anything.

---

## 1. Assets and security goals

### 1.1 Assets

| Asset | Where it lives today | Why it matters |
|---|---|---|
| Execution trace artifacts | `data/traces/<run_id>.json` | The evidence record for every run. Contains the target URL, the project name typed into the form, error messages, and postcondition names. |
| Failure screenshots | `data/screenshots/<run_id>.png` | Pixel capture of the page at the moment of failure. Can contain anything rendered on screen, including values a user typed. |
| Test application state | in-page DOM of `demo_app/index.html` | The system under test. Today: a list of project names. |
| Local machine / filesystem | the developer's workstation | Trace and screenshot directories are written under the repo. |
| Model API credentials | **none present** | No model integration exists, so no key is stored, read, or logged today. Any future adapter must keep it out of source, traces, and logs (NFR-013). |
| Workflow definitions | **not present** | Planned. A workflow store would become an executable artifact and therefore a privileged asset. |
| Execution history | only per-run JSON files today | Planned persistent store (FR-038…FR-042). |

### 1.2 Security goals (from SRS §6.3 and §6.1)

| Goal | SRS ref | Status |
|---|---|---|
| Use a controlled test application by default | NFR-011 | **Met** — the only shipped target is the local demo app. |
| Isolate browser sessions between runs | NFR-012 | **Met** — one browser and one `BrowserContext` per run (`chimera/agent.py`, `create_project`). |
| Keep secrets out of source control and ordinary logs | NFR-013 | **Met by absence** — no credential is read or written anywhere. No scrubbing mechanism exists, so this depends on there being nothing to scrub. |
| Treat browser content as untrusted input, not authoritative instructions | NFR-014 | **Not enforced** — no model exists yet, so there is no instruction channel to abuse, but page content is neither sanitised nor classified. |
| Defend against prompt injection in page content | NFR-015 | **Not implemented** — no LLM surface today. Required before any planner is added. |
| Enforce an allowlist of permitted operations **and targets** | NFR-016 | **Partial** — operations are enforced (`chimera/safety.py`, `ALLOWED_ACTIONS`); targets are not. |
| Require explicit authorization for destructive/consequential actions | NFR-017 | **Not implemented** — no such action type exists today. |
| Never automatically bypass authentication, access controls, or CAPTCHAs | NFR-018 | **Met by absence** — no such code path exists. |
| Avoid capturing unnecessary credentials or personal data in screenshots and traces | NFR-019 | **Partial** — nothing unnecessary is captured *by design of the target*, but there is no redaction mechanism. |
| Keep the test environment resettable | NFR-020 | **Met** — the demo app has an in-page Reset button that clears the list, the confirmation, the input, the disabled attribute, and the fault status. |
| Terminate every run in an explicit state | NFR-001 | **Partial** — `succeeded` / `failed` / `cancelled` exist; the SRS's `inconclusive` does not. |
| Never let an unhandled exception silently produce success | NFR-002 | **Met** — the agent's `except Exception` branch forces `success=False`. |
| Bound retries and record them | NFR-003 | **Met** — `RetryPolicy` in `chimera/safety.py`, enforced in `execute_with_retry`. |
| Check for duplicate effects before repeating a state-changing action | NFR-004 | **Met for CLICK** — the `is_effect_achieved` hook is consulted before any retry. |
| Preserve execution metadata to investigate failures | NFR-005 | **Met** — the JSON trace, written for every run including failures. |

---

## 2. Trust boundaries

```
┌────────────────────────────────────────────────────────────────┐
│ TB-1  Developer / CI workstation  (trusted)                    │
│        - source code, virtualenv, test scripts                 │
│        - writes data/traces/, data/screenshots/                │
└───────────────┬────────────────────────────────────────────────┘
                │ subprocess / file read-write
┌───────────────▼────────────────────────────────────────────────┐
│ TB-2  Agent process  (semi-trusted)                            │
│   ┌──────────────────────────────────────────────────────┐     │
│   │ TB-3  Browser page  — UNTRUSTED CONTENT              │     │
│   │        DOM text, labels, attributes, URLs, timings    │     │
│   │        Anything rendered or served is attacker-        │     │
│   │        controlled if the target is not trusted.        │     │
│   └──────────────────────────────────────────────────────┘     │
│   ┌──────────────────────────────────────────────────────┐     │
│   │ TB-4  Model provider — UNTRUSTED PROPOSALS (Future)  │     │
│   │        Model output is a *proposal*, never an         │     │
│   │        instruction and never a terminal status.       │     │
│   └──────────────────────────────────────────────────────┘     │
└───────────────┬────────────────────────────────────────────────┘
                │ CDP
┌───────────────▼────────────────────────────────────────────────┐
│ TB-5  Browser process  (isolated per run)                      │
└────────────────────────────────────────────────────────────────┘
```

**TB-3 — webpage content is untrusted.** The demo app is trusted *only
because it is the controlled target* (NFR-011). The executor must never
treat page text as an instruction, a policy, or evidence of intent. Today the
agent reads page text only through fixed locators (`get_by_label("Project
Name")`, `get_by_role("button", name="Create Project")`) and checks two
fixed postconditions. There is no path by which page content can change
what the agent does next. This is the property that must be preserved when
a planner is added.

**TB-4 — future model proposals are untrusted.** SRS §9 requires that "the
language model may propose actions, but it must not directly assign the run's
terminal status". The intended shape is: the model proposes an action; the
executor validates it against the allowlist (and, once implemented, the
target allowlist) and the workflow definition; the terminal status is
assigned by deterministic verification code only. **This boundary does not
exist yet** — there is no model integration. It is recorded here so the
future adapter is built to it rather than around it.

**TB-1/TB-2 — filesystem boundary.** The agent writes only to the trace and
screenshot directories, using atomic writes. There is no sandboxing of the
process itself; the agent has the developer's filesystem permissions.

---

## 3. Adversary model

Two classes of adversary are considered:

- **A compromised or hostile target page.** The page can display arbitrary
  text, delay arbitrarily, remove or re-label elements, redirect, or attempt
  to induce the agent into an unintended action.
- **A malicious or mistaken instruction source (Future).** Today this is
  the developer writing the hard-coded workflow; in the planned phases it is
  the model provider or a model response. Its proposals are assumed to be
  wrong until validated.

Out of scope: an adversary with local code execution on the workstation
(they can edit the agent directly), and physical access to the browser
process.

---

## 4. Threats, mitigations, and enforcement points

Each row names the mitigation and the **actual** code that enforces it.
"Met" means the control is implemented and exercised by a test. "Partial"
means some of the threat is addressed. "Not implemented" means the control
does not exist — no mitigation is claimed.

### T-1 — Prompt injection via page content

*Attacker-controlled page text attempts to redirect the agent's behaviour.*
Today there is no LLM in the loop, so there is no prompt to inject. The
executor reads only fixed locators, so page text cannot currently change
control flow.

- **Current mitigation:** none beyond the absence of a model. The fixed-locator
  design is what makes the absence tolerable.
- **Enforcement point:** `chimera/agent.py`, `create_project()` — the locator
  choices (`page.get_by_label("Project Name")`,
  `page.get_by_role("button", name="Create Project")`) and the two fixed
  postcondition selectors.
- **Residual risk:** **High** for the planned model-integrated phase. Any
  future planner that consumes page text as context inherits the injection
  surface. Required before that phase: sanitise/quote page content, keep
  model output in the proposal role only, and validate every proposal
  against the allowlist and the workflow definition (NFR-015, §12.4
  adversarial tests).

### T-2 — Unauthorized navigation

*The agent navigates somewhere it should not.*

- **Current mitigation:** the allowlist permits the `navigate` *type*; the
  target URL is not checked. The URL originates from
  `get_demo_url()` / `get_demo_url_with_faults()` — which build a
  `file://` URL for the bundled demo app — **or** from the caller-supplied
  `url=` argument of `create_project()`. A caller (or anything that can
  influence that argument, such as a future workflow compiler or a model
  proposal) can direct the browser to any URL, including a remote host.
  There is no scheme allowlist, no host allowlist, and no origin check.
- **Enforcement point:** none today. The only constraint is that the URL
  string reaches `page.goto(target_url)`.
- **Residual risk:** **Medium** in the current configuration (the URL is
  chosen by trusted code in every shipped call path), **High** once a
  workflow compiler or model can supply it. Required control: an
  explicit URL/target allowlist enforced in the executor, closing the
  "and targets" half of NFR-016.

### T-3 — Unsafe click

*The agent clicks a destructive or unintended control.*

- **Current mitigation:** the allowlist permits the `click` type generally;
  the *specific* target is fixed in code to the "Create Project" button, and
  the demo app's submit handler refuses while the button is disabled. A
  state-changing action is not repeated without an effect check (NFR-004).
- **Enforcement point:** `chimera/agent.py` — the fixed
  `get_by_role("button", name="Create Project")` locator and the
  `is_effect_achieved` hook passed to the CLICK's `execute_with_retry`.
- **Residual risk:** **Low** today, because the workflow is hard-coded.
  It becomes **High** for any general executor: a type-level allowlist
  cannot distinguish a safe click from a destructive one. Required control:
  target allowlisting (NFR-016) and an explicit-authorization gate for
  consequential actions (NFR-017).

### T-4 — Sensitive data captured in traces or screenshots

*A run's artifacts contain credentials, tokens, or personal data.*

- **Current mitigation:** the demo app renders no credentials and no PII, and
  the target is local, so the captured content is inherently uninteresting.
  Screenshots are only taken on action failure (NFR-019) and only of the
  local demo.
- **Enforcement point:** `chimera/tracing.py` —
  `capture_failure_screenshot()` is called from `chimera/agent.py` only on
  the action-failure path.
- **Residual risk:** **Medium** for any real target. There is no redaction,
  no masking, no allowlist of captured fields, and no retention policy; a
  screenshot of a logged-in page would capture the whole viewport. The
  trace additionally embeds the target URL and the typed form value
  (`project_name`) verbatim, so a future target that echoes secrets into
  the field would leak them into the artifact. Required control: a
  redaction pass over trace fields and screenshots, plus an explicit
  capture policy for the dashboard (NFR-019).

### T-5 — Runaway retries / resource exhaustion

*The agent loops, or a run never terminates.*

- **Current mitigation:** `RetryPolicy(max_attempts=2, base_delay_seconds=0.05,
  max_delay_seconds=0.2, max_total_seconds=5.0)` bounds both attempt count
  and wall-clock time; `ACTION_TIMEOUT_MS` (5000 ms) is derived from that
  budget and passed to every Playwright call so Playwright's 30 s default
  cannot override it; retries without an effect check are refused
  outright (FR-028).
- **Enforcement point:** `chimera/safety.py` — `execute_with_retry()`;
  `chimera/agent.py` — `DEFAULT_POLICY`, `ACTION_TIMEOUT_MS`.
- **Residual risk:** **Low** for the current code path. Not yet covered: a
  per-*run* total budget across many actions (the policy is currently
  per-action), and a bound on the number of browser processes if a caller
  runs many runs concurrently. Both belong with the workflow compiler.

### T-6 — Ambiguous completion reported as success

*The agent believes the task succeeded when it did not, or cannot tell.*

- **Current mitigation:** completion is established by two explicit
  postcondition checks against live browser state
  (`#confirmation` visible; `#project-list li` with the project name
  visible) — never inferred from the click returning. A run whose
  verification times out is reported `failed`.
- **Enforcement point:** `chimera/agent.py` — the two `wait_for(...,
  state="visible")` blocks and the `verification_passed` /
  `verification_failed` recorder calls.
- **Residual risk:** **Medium.** There is no `INCONCLUSIVE` state, so
  "verification could not be established" is reported as `failed`, which
  conflates *the action failed* with *the agent could not tell* (SRS §9,
  NFR-001). A verification that is slow-but-eventually-true, or a page that
  renders the expected text for the wrong reason, is not distinguished.
  Required control: the `INCONCLUSIVE` terminal state and a verification
  engine that states which postconditions were established.

### T-7 — Cancellation delay

*The user asks to stop; the run keeps going.*

- **Current mitigation:** cancellation is cooperative. It is checked before
  every action, between actions, between verifications, at the top of every
  retry iteration, inside the effect check, and before the retry sleep. A
  cancelled run is a distinct terminal outcome, and the context and browser
  are closed in `finally`.
- **Enforcement point:** `chimera/safety.py` — `CancellationToken.check()`;
  `chimera/agent.py` — the `_check_cancel()` calls and the
  `except RunCancelledError` handler.
- **Residual risk:** **Medium.** An in-flight synchronous Playwright call is
  *not* interrupted: it runs to completion or to its own timeout, so the
  worst-case delay between `request()` and the stop is `ACTION_TIMEOUT_MS`
  (5 s). A user-visible stop control would feel sluggish. The agent
  deliberately never touches a Playwright object from another thread and
  never force-kills a thread, so this delay is a safety choice, not a bug.
  A future dashboard needs to reflect "stopping" as a distinct state
  rather than implying immediacy.

### T-8 — Trace-write failure silently becomes success

*The run succeeded but the evidence record is missing; the caller sees
success.*

- **Current mitigation:** `TraceRecorder.finish()` writes atomically and
  raises `TraceWriteError` on any `OSError`; `create_project()` catches it
  and forces `success=False`, `status="failed"`, `cancelled=False`,
  `trace_path=None`, and surfaces the write error in `result["error"]`.
  This precedence applies even over a cancellation: a run that cannot be
  traced is a failure, not a clean cancellation.
- **Enforcement point:** `chimera/tracing.py` — `TraceRecorder.finish()`;
  `chimera/agent.py` — `_finish_trace()`.
- **Residual risk:** **Low** for the "silent success" case, which is
  covered by tests at both the unit and browser level. One residual: the
  trace directory is created on demand, so a *first* write into a
  previously non-existent directory can fail for environmental reasons
  that were not present in testing; the failure is surfaced, not hidden.

### T-9 — Leaked browser processes or contexts

*A run leaves a Chromium process or an open context behind.*

- **Current mitigation:** `context.close()` then `browser.close()` in a
  `finally` block, executed on the success, failure, and cancellation paths.
  Each run launches its own browser process, so there is no shared
  lifecycle to orphan.
- **Enforcement point:** `chimera/agent.py` — the `finally` block inside
  `create_project()`.
- **Residual risk:** **Low.** A hard kill of the agent process (SIGKILL)
  bypasses `finally`; that is outside the current threat model.

### T-10 — Session state leaking between runs

*Run 2 observes run 1's cookies, storage, or pages.*

- **Current mitigation:** each run creates its own `BrowserContext` and its
  own browser process. Cookies and `localStorage` live in the context, so a
  fresh context starts with an empty cookie jar. The isolation is verified
  by tests that seed a probe cookie into every context the agent creates
  and assert each run's context starts empty, and by a negative control in
  which sharing one context makes the isolation tests fail.
- **Enforcement point:** `chimera/agent.py` — `browser.new_context()` per
  run; `tests/test_integration.py` — the four NFR-012 isolation tests.
- **Residual risk:** **Low** for browser session state. The demo app is
  served from `file://` and holds no server-side state, so a shared backend
  (a future real target with a database) would introduce a cross-run leak
  channel that browser isolation cannot address. That belongs to the
  evaluation-environment design.

### T-11 — Malformed, stale, or ambiguous page state

*The page changes shape between the fill and the click, or offers an
ambiguous label.*

- **Current mitigation:** locator failures raise; the failure is caught,
  recorded as `action_failed` with error details and a screenshot, and
  surfaced as `failed`. Locators are semantic
  (`get_by_label`, `get_by_role(name=...)`) rather than brittle CSS, which
  reduces but does not eliminate ambiguity — a page with two "Create
  Project" buttons would raise a strict-mode violation rather than
  silently pick one.
- **Enforcement point:** `chimera/agent.py` — the locator calls and the
  `except Exception` failure handler.
- **Residual risk:** **Medium.** There is no explicit stale-state detection
  (the agent does not check that the page is still the one it navigated to),
  no ambiguity resolution policy beyond Playwright's strict mode, and no
  recovery. The SRS §12.4 adversarial scenarios (unexpected redirects,
  ambiguous button labels, delayed confirmations, stale browser state) are
  **not yet** covered by the test suite.

### T-12 — Artifact tampering

*An artifact is altered after the fact, or an untrusted party writes into
the trace directory.*

- **Current mitigation:** none. Traces are plain JSON with no signature, no
  hash chain, and no integrity metadata. The trace directory is writable by
  anyone with the developer's permissions.
- **Enforcement point:** none.
- **Residual risk:** **Medium** for forensic use. Today the trace is a
  debugging aid, not an audit record. If the trace is ever used to assert
  that a run was correct, it needs integrity protection and an
  append-only store. The atomic write (temp file + `replace()`) protects
  against *partial* reads, not against *modification*.

### T-13 — Secrets in logs or reports

*A credential appears in a log line, an error message, or a trace field.*

- **Current mitigation:** the code reads, writes, and logs no credentials;
  the demo target has no authentication. The failure path surfaces
  exception type and message — which for a real target could contain
  page-derived text.
- **Enforcement point:** none beyond the absence of credentials.
- **Residual risk:** **Low** today, **High** in the model-integrated phase
  (API keys) and against real targets (tokens echoed in error text). A
  future model adapter must read its key from the environment (NFR-025)
  and must never place it in a trace, a log line, or a dashboard payload.

### T-14 — Concurrent runs interfering

*Two runs at once share state or race on the artifact directory.*

- **Current mitigation:** browser state is isolated per run (T-10). Artifact
  files are named by UUID4 `run_id`, so concurrent runs do not overwrite
  each other's traces; the atomic write makes each file independently
  readable. There is no locking, but no shared mutable file requires it.
- **Enforcement point:** `chimera/tracing.py` — `run_id` naming and atomic
  write.
- **Residual risk:** **Low** today. Not yet tested: concurrent execution of
  multiple runs (there is no test for it, and the demo app is a local file
  so the surface is small).

---

## 5. Residual risks and controls that are not yet implemented

Consolidated list. **None of these are implemented.** They are the gap
between the current system and a system that could be pointed at a real
target or exposed to a user.

| # | Missing control | SRS ref | Threat | Concrete requirement |
|---|---|---|---|---|
| R-1 | Target allowlist (URL, locator, value) | NFR-016 | T-2, T-3 | Enforce an allowed-scheme/host/selector set in the executor, not in the caller. |
| R-2 | Authorization gate for consequential actions | NFR-017 | T-3 | A distinct action class that requires explicit per-run approval; refuse to auto-approve. |
| R-3 | `INCONCLUSIVE` terminal state | §9, NFR-001 | T-6 | Model "outcome not established" as a first-class state with its own trace terminal, and report which postconditions were established. |
| R-4 | Code-validated state machine | §9 | T-6, T-11 | Transitions validated by code; the model may propose but not assign status. |
| R-5 | Prompt-injection defence for the planner | NFR-015, NFR-014 | T-1 | Treat page content as data; validate every model proposal; adversarial test per §12.4. |
| R-6 | Redaction for traces and screenshots | NFR-019 | T-4, T-13 | Mask known-secret patterns and PII fields; restrict what a screenshot may contain. |
| R-7 | Retention and rotation for artifacts | NFR-005 vs. disk | T-12, T-14 | Bound `data/traces/` and `data/screenshots/` growth; a retention policy. |
| R-8 | Artifact integrity protection | — (future) | T-12 | Only needed if traces become an audit record rather than a debug aid. |
| R-9 | Adversarial test suite | §12.4 | T-1, T-11 | Prompt-injection text, unexpected redirects, ambiguous labels, duplicate records, delayed confirmations, stale browser state, missing permissions, malformed model responses. |
| R-10 | Per-run total resource budget | FR-022 | T-5 | The retry policy is currently per-action; a run-level budget is needed for multi-step workflows. |
| R-11 | Concurrency tests | — | T-14 | Test multiple simultaneous runs, including artifact writes. |
| R-12 | Model key handling | NFR-013, NFR-025 | T-13 | Environment-sourced key, never in a trace, log, or dashboard payload. |
| R-13 | Independent verification engine | §5.5, FR-031…FR-036 | T-6 | Verification separated from execution, per the SRS module split. |

---

## 6. Testing and validation required before broader or production use

### 6.1 Already done (Milestone 1)

- Allowlist and bounded-retry unit tests, including refusal of blind
  retries (`tests/test_safety.py`).
- Trace schema, ordering, atomicity, and terminal-status tests, including
  the FR-034 write-failure precedence (`tests/test_tracing.py`).
- Fault-injection and HTML-contract tests without a browser
  (`tests/test_faults.py`).
- Browser integration tests in real Chromium: fault scenarios, reset
  behaviour, one-event-per-action trace checks, trace-write failure,
  cancellation (pre-cancelled, between actions, in-flight), and four
  NFR-012 isolation tests with a negative control
  (`tests/test_integration.py`).

### 6.2 Required before pointing the agent at anything other than the
controlled demo app

1. **Target allowlist tests (R-1).** Assert that a URL outside the
   allowlist, a locator outside the allowlist, and a disallowed action type
   are each refused *before* reaching Playwright, and that the refusal is
   recorded in the trace.
2. **Authorization tests (R-2).** Assert that a consequential action
   without approval is refused and that approval is per-run and not
   reusable.
3. **Injection tests (R-5).** Once a planner exists: page content that
   instructs the agent to navigate elsewhere, exfiltrate, or disable
   verification must not change the executed action set.
4. **Redaction tests (R-6).** Traces and screenshots produced against a
   page containing a known secret must not contain that secret.
5. **Ambiguity and staleness tests (R-9).** Duplicate labels, elements
   removed between actions, delayed confirmations, unexpected redirects.
6. **Concurrency and soak tests (R-11, R-10).** Many runs in parallel;
   sustained runs to confirm artifact growth stays within a policy and
   no browser process leaks.
7. **Resource-bound tests (R-10).** A run must terminate within a stated
   wall-clock budget regardless of target behaviour.

### 6.3 Required before the system is exposed to a user or connected to a
model

8. **Cancellation-latency UX.** The cooperative bound (5 s today) must be
   surfaced honestly in any UI — "stopping" is a state, not an
   instantaneous effect (T-7).
9. **Secrets handling review (R-12).** Environment-sourced keys; a
   repository scan for credential patterns before any public release
   (NFR-013).
10. **Untrusted-content review.** Any code path that feeds page text to a
    model, a log, or a dashboard must be reviewed against the trust
    boundaries in §2.
11. **Release checklist.** SRS §18's eighteen acceptance items are
    currently unchecked; none should be marked complete on the basis of
    this document.

### 6.4 Explicitly out of scope for the current milestone

- A local adversary with code execution on the workstation.
- Physical access to the browser process.
- Side-channel attacks on the Playwright transport.
- Denial of service by a target that the run-level budget (R-10) does not
  yet bound.

---

## 7. Related documents

- [`architecture.md`](architecture.md) — components, lifecycle, safety and
  retry boundary, cancellation semantics, trace format, implemented vs.
  planned capabilities.
- `CURRENT_STATUS.md` — the running session log with measured results.
- `PROJECT_CHIMERA_SRS.md` — the requirements authority.
