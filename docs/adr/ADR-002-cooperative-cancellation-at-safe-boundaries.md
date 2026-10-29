# ADR-002 — Cooperative cancellation at safe execution boundaries

- **Status:** Accepted
- **Date:** 2026-10-24
- **Deciders:** Project Chimera maintainers
- **Supersedes:** none
- **Related:** [ADR-001](ADR-001-per-run-browser-and-context-isolation.md), [ADR-003](ADR-003-trace-persistence-precondition-for-success.md)

---

## Status

**Accepted** — implemented in `chimera/safety.py` and `chimera/agent.py`,
and verified by 5 unit tests in `tests/test_safety.py` and 6 browser tests
in `tests/test_integration.py`. The decision describes what the code does
today, not an intention.

---

## Context

SRS FR-021 requires that "the user must be able to stop an active run. The
system must stop scheduling further actions and handle browser cleanup
safely." SRS §9 defines `CANCELLED` as a distinct terminal state.

Chimera drives Playwright's **synchronous** API. A synchronous Playwright
call is a blocking call into a greenlet-bound event loop that owns the page
object. Two properties follow, and they constrain every possible design:

1. The page object cannot be safely driven from a second thread.
2. A call already in flight cannot be interrupted from outside without
   risking a corrupted transport, a half-applied action, or a leaked browser
   process.

The requirement is nonetheless a *stop* requirement, so the decision has to
be made on two axes: **how** the run is stopped, and **how quickly**.

## Decision

Cancellation is **cooperative**. It is implemented as a flag the agent reads
from its own thread; no Playwright object is ever touched from another
thread, and no thread is ever force-killed.

- `chimera/safety.py` provides `CancellationToken` — a `threading.Event`
  plus a reason string. `request(reason)` is idempotent and the first reason
  wins. `check()` raises `RunCancelledError` if cancellation was requested.
- `chimera/agent.py` calls `_check_cancel()` at every point where no
  Playwright call is in flight: before each action (navigate, fill, click),
  between actions, and between the two verifications.
- `chimera/safety.py`'s `execute_with_retry()` additionally checks the token
  at the top of every retry iteration, inside the `is_effect_achieved` state
  check (so a retry waiting on a slow effect bails out promptly), and
  immediately before the inter-retry sleep.

An in-flight synchronous Playwright action is **not** interrupted. It runs to
completion or to its own timeout, and the cancellation is observed at the
next safe boundary.

**Configured timeout.** Every Playwright action is bounded by
`ACTION_TIMEOUT_MS`, derived from the retry policy's wall-clock budget:

```python
DEFAULT_POLICY = RetryPolicy(max_attempts=2, base_delay_seconds=0.05,
                              max_delay_seconds=0.2, max_total_seconds=5.0)
ACTION_TIMEOUT_MS = int(DEFAULT_POLICY.max_total_seconds * 1000)   # 5000
```

The derivation is deliberate: without it, Playwright's own 30 s default
action timeout would silently override `max_total_seconds`, and a
persistently disabled control would block the run for 30 s instead of
failing inside the policy's stated bound.

**Therefore the worst-case stop latency is `ACTION_TIMEOUT_MS` — 5 seconds
today.** This is the documented, user-visible trade-off of the decision.

**Outcome contract.** A cancelled run is a distinct third outcome, never
reported as success and never as an ordinary failure:

| Field | Value |
|---|---|
| `success` | `False` |
| `cancelled` | `True` |
| `status` | `"cancelled"` |
| trace terminal | exactly one `run_cancelled` event, `action_outcome="cancelled"` |
| top-level `terminal_status` | `"cancelled"` |

No failure screenshot is captured on the cancellation path: a cancelled run
is not an error state, and a screenshot would be misleading evidence. The
browser context and browser are closed by the surrounding `finally` block.

Callers that pass no token see the previous behaviour unchanged
(`cancelled=False`; `status` is `"succeeded"` or `"failed"`).

## Alternatives Considered

1. **Interrupt the in-flight action from another thread** (drive the page
   from the canceller thread, or signal the action mid-call). *Rejected.*
   The synchronous Playwright page is not safe to use from a second thread;
   the action could be interrupted between its effect and its observation,
   leaving the run's state ambiguous — precisely the "contradictory
   evidence" case SRS FR-034 prohibits. The project's standing constraint
   against controlling a synchronous Playwright page from an unrelated thread
   also rules this out.

2. **Force-kill the agent thread** (e.g. `PyThreadState_SetAsyncExc`, or
   terminating the process). *Rejected.* Unsafe thread termination can
   corrupt interpreter state, skips the `finally` block, and leaks the
   browser process and its profile. It would also bypass
   `context.close()`/`browser.close()`, defeating ADR-001's cleanup
   guarantee.

3. **Enforce the per-action timeout inside `execute_with_retry`** (for
   example by running the action in a worker thread and joining with a
   deadline). *Rejected for now; recorded as a possible future feature.* The
   current design already bounds each action by `ACTION_TIMEOUT_MS` at the
   Playwright call site, so a run cannot exceed the policy budget. Moving
   the timeout into the safety wrapper would add thread-management
   complexity without changing the observable bound. It remains an option if
   a future workflow layer needs a single enforcement point.

4. **Do not check for cancellation at all** (let the run finish and discard
   the result). *Rejected.* It fails SRS FR-021's "stop scheduling further
   actions" requirement and wastes the run's remaining time.

## Consequences

**Positive**

- The stop is always safe: no interrupted action, no corrupted transport, no
  leaked browser process.
- Cancellation is never misreported as success or as an ordinary failure.
- Callers that do not use cancellation are entirely unaffected.
- Cleanup is unconditional: the `finally` block closes the context and
  browser on the cancellation path too.

**Negative / accepted cost**

- Stop latency is **not instantaneous**. The worst case is the in-flight
  action's own timeout, currently 5 s. A user-visible "stop" control will
  feel sluggish on a slow action, and any UI must present "stopping" as a
  distinct state rather than implying immediacy.
- A cancel request that arrives during a long action is not noticed until
  that action finishes; the run may complete one more action than the
  canceller expected.

**Residual risk**

- The delay is inherent to the synchronous API, not a defect. It becomes
  materially worse if `ACTION_TIMEOUT_MS` is raised for other reasons, so
  the timeout derivation in `chimera/agent.py` should be treated as a
  coupled change.

## Requirements / References

| Reference | Text / relevance |
|---|---|
| SRS FR-021 | "Support cancellation: The user must be able to stop an active run. The system must stop scheduling further actions and handle browser cleanup safely." |
| SRS FR-022 | "Limit execution resources: Each run must have configurable limits on duration, number of actions, retries, and model calls." — bounds the stop latency. |
| SRS §9 state 12 | `CANCELLED`: "The user or execution policy stopped the run." |

**Implementation evidence**

- `chimera/safety.py` — `CancellationToken`, `RunCancelledError`, and the
  four cancellation checks inside `execute_with_retry()`.
- `chimera/agent.py` — `_check_cancel()` calls, the
  `except RunCancelledError` handler, `DEFAULT_POLICY`, `ACTION_TIMEOUT_MS`.
- `tests/test_safety.py` — `CancellationTokenTests` (5) and
  `ExecuteWithRetryCancellationTests` (5): cancel-before-start, cancel during
  retry, cancel inside the effect check, unchanged behaviour with no token,
  and cancellation distinct from budget exhaustion.
- `tests/test_integration.py` — `test_cancel_before_execution_runs_no_actions`,
  `test_cancel_between_actions_stops_at_next_boundary`,
  `test_cancel_during_in_flight_action_is_cooperative`,
  `test_trace_write_failure_overrides_cancelled_result`,
  `test_run_without_cancel_token_keeps_default_shape`,
  `test_action_failure_is_not_classified_as_cancellation`.
  The in-flight test uses a deterministic handshake (not a sleep) to prove
  the in-flight fill completed and the following click never ran.
- `docs/architecture.md` §5 · `docs/threat_model.md` T-7.
