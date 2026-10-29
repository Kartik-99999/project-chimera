# ADR-001 — Per-run browser and browser context isolation

- **Status:** Accepted
- **Date:** 2026-10-24
- **Deciders:** Project Chimera maintainers
- **Supersedes:** none
- **Related:** [ADR-002](ADR-002-cooperative-cancellation-at-safe-boundaries.md), [ADR-003](ADR-003-trace-persistence-precondition-for-success.md), [ADR-004](ADR-004-requirement-traceability-to-srs.md)

---

## Status

**Accepted** — implemented in `chimera/agent.py` and verified by the four
NFR-012 isolation tests in `tests/test_integration.py`. The decision
describes what the code does today, not an intention.

---

## Context

SRS NFR-012 requires that "browser sessions must be isolated between test runs
where practical", and SRS §7.3 lists "launch isolated browser contexts" as a
responsibility of the browser-execution component.

Chimera's first implementation created its page with
`browser.new_page()`. It was therefore necessary to establish whether that
already provided isolation, or whether an explicit
`browser.new_context()` → `context.new_page()` was required.

This was determined by reading Playwright's own behaviour rather than by
assumption. `Browser.new_page()` is documented as *"Creates a new page in a
new browser context"*, and Playwright's convenience API is a shorthand for
`browser.new_context().newPage()`. **The original implementation was
therefore already session-isolated** — each call to `create_project()` had
its own `BrowserContext`, with its own cookie jar, `localStorage`, and
storage state. A separate `Browser` process was already launched and closed
per run.

Two properties of that arrangement were nevertheless implicit:

1. The isolation unit was not a named object in the code, so it could not be
   asserted against directly by a test.
2. The context's lifetime was reclaimed only as a side effect of browser
   teardown, rather than being closed deterministically.

## Decision

Each run creates **its own `Browser` process and its own `BrowserContext`**,
using the explicit Playwright lifecycle:

```python
browser = playwright.chromium.launch(headless=True)
context = browser.new_context()      # the isolation unit
page = context.new_page()
...
finally:
    try:
        context.close()               # context first: it owns session state
    finally:
        browser.close()               # then the browser process
```

The context is closed explicitly on every exit path — success, failure, and
cancellation — before the browser is closed.

The two isolation levels are chosen deliberately:

- **The context** is the session-state boundary (cookies, `localStorage`,
  storage state). It is the object the requirement is actually about.
- **The browser process** is a stronger boundary. It guarantees no shared
  process-level profile or cache can carry state between runs.

## Alternatives Considered

1. **Keep `browser.new_page()` unchanged.** *Rejected on lifecycle
   clarity, not correctness.* It was already isolated, so the change was not
   a bug fix. But it hides the isolation unit, leaves the context lifetime
   implicit, and Playwright's own documentation recommends the explicit form
   for production code *"to control their exact life times."* The explicit
   form also made the NFR-012 isolation unit assertable by tests, which the
   implicit form was not.

2. **One shared browser process, a fresh context per run.** *Rejected for
   now; recorded as a deliberate trade-off.* This preserves the session
   isolation (the context is still the boundary) while removing the
   per-run browser launch. It is faster and remains a valid option for
   non-sensitive targets. It was not adopted because the cost of the
   stronger boundary is small in the current configuration, and revisiting
   the trade-off should be done with the threat model in hand rather than
   for a benchmark win.

3. **A shared context across runs.** *Rejected.* It would break session
   isolation outright. This variant was used as a **negative control** during
   the audit: mutating the agent to share one context across runs made the
   isolation tests fail, confirming the tests are load-bearing rather than
   vacuous.

## Consequences

**Positive**

- Session isolation between runs is structurally guaranteed, not incidental,
  and is now asserted by tests.
- Browser resources are closed deterministically on every exit path.
- The isolation unit is a first-class object, so a future executor can
  attach per-run state (storage seeding, route interception) to it directly.

**Negative / accepted cost**

- One browser launch per run. Measured in the integration suite at roughly
  0.1 s of setup overhead per browser, ≈0.9 s of a 20.2 s total — the
  dominant cost of the strongest isolation option, and acceptable against a
  local test target.

**Residual risk (not addressed by this decision)**

- Browser isolation covers *client-side* session state only. It does not
  address server-side state: a future real target with a database could
  leak state between runs regardless of how the browser is scoped. That
  belongs to the evaluation-environment design, not to this decision.

## Requirements / References

| Reference | Text / relevance |
|---|---|
| SRS NFR-012 | "Browser sessions must be isolated between test runs where practical." |
| SRS §7.3 | Browser execution responsibilities include "launch isolated browser contexts". |
| SRS §9 state 12 | `CANCELLED` — cleanup must be safe when a run stops. |

**Implementation evidence**

- `chimera/agent.py` — `create_project()`: `browser.new_context()`,
  `context.new_page()`, and the `finally: context.close() → browser.close()`
  block.
- `tests/test_integration.py`:
  - `test_each_run_gets_a_fresh_browser_context` — two runs create two
    distinct `BrowserContext` objects on two distinct `Browser` instances.
  - `test_session_state_does_not_leak_between_runs` — a probe cookie is
    seeded into every context the agent creates; each run's context is
    observed to start with an empty cookie jar.
  - `test_browser_resources_are_closed_after_each_run` — exactly one context
    and one browser closed per run, on both the success and failure paths.
  - `test_cancelled_run_also_closes_its_context` — the cancellation path
    closes its context and browser.
- `CURRENT_STATUS.md` — "Session isolation (NFR-012) — audit result: MET".
- `docs/architecture.md` §3 · `docs/threat_model.md` T-10, T-9.
