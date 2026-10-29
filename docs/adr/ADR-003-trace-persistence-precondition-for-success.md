# ADR-003 — A run cannot be reported successful when its trace cannot be persisted

- **Status:** Accepted
- **Date:** 2026-10-24
- **Deciders:** Project Chimera maintainers
- **Supersedes:** none
- **Related:** [ADR-001](ADR-001-per-run-browser-and-context-isolation.md), [ADR-002](ADR-002-cooperative-cancellation-at-safe-boundaries.md)

---

## Status

**Accepted** — implemented in `chimera/tracing.py` (`TraceRecorder.finish`)
and `chimera/agent.py` (`_finish_trace`), and verified by
`tests/test_tracing.py::TraceWriteFailureTests` plus two browser tests in
`tests/test_integration.py`. The decision describes what the code does
today, not an intention.

---

## Context

SRS FR-034 is unambiguous: *"If the required evidence is missing or
contradictory, the run must not be marked successful."*

Chimera emits a JSON execution trace for every run — successful, failed, or
cancelled — to `data/traces/<run_id>.json`. The trace is the run's evidence
record: it is what a reader consults to determine what the agent actually
did, in what order, and with what outcome. SRS FR-038 additionally requires
that the system "retain configurable run metadata, traces, and verification
outcomes".

Persistence of that artifact can fail for reasons entirely outside the
agent's control: a read-only or full filesystem, a missing or unwritable
directory, a permission change, a quota exhaustion. The decision has to
answer two questions:

1. What happens to the run's reported outcome when the write fails?
2. Does the answer differ for a run that was already failing, and for a run
   that was cancelled?

A second, related question is the atomicity of the write itself: a reader
must never observe a half-written artifact, which would be "contradictory
evidence" in the FR-034 sense.

## Decision

**A trace-persistence failure forces the run to `failed`, whatever the run's
outcome was otherwise.**

- `chimera/tracing.py` — `TraceRecorder.finish()` writes to a temporary
  file and then `replace()`s it into position, so a reader never sees a
  partial artifact and no `.tmp` file is left behind. Any `OSError` during
  the write is re-raised as `TraceWriteError`, with the original exception
  preserved as `__cause__`.
- `chimera/agent.py` — `_finish_trace()` catches `TraceWriteError` and sets
  `success=False`, `status="failed"`, `cancelled=False`, `trace_path=None`,
  and surfaces the write error as `result["error"]`.

**Effect on an ordinary failure.** A run that already failed stays failed —
the classification is unchanged. The visible difference is the error text:
the trace-write error replaces the original action failure in
`result["error"]`, and because the artifact could not be written, the
original cause survives only in the in-memory event log, not on disk. The
run's outcome is unchanged; the diagnosis available to the operator is
narrower.

**Effect on cancellation.** The write failure **overrides** the cancelled
outcome: `status` becomes `"failed"` and `cancelled` becomes `False`. A run
whose cancellation cannot be evidenced is not a clean cancellation; it is a
failure with an unrecorded outcome. This precedence is deliberate and is
asserted by tests at both the unit and browser level.

**Effect on success.** A run whose postconditions all verified still
reports `success=False` if its trace cannot be written. The verification
succeeded; the evidence of that verification does not exist. Reporting
success would assert something the system cannot substantiate.

## Alternatives Considered

1. **Treat the write failure as non-fatal** — report the run's real outcome
   and log a warning that the trace was lost. *Rejected.* It directly
   contradicts SRS FR-034: the run would be marked successful while the
   evidence backing that success is missing. It also creates a silent gap
   in the execution history (SRS FR-038) that a later reader could not
   detect.

2. **Report the run as failed but keep the original error text.** *Rejected
   as the default.* It hides the more actionable error — a run that failed
   because its trace could not be written is a different operational
   problem from a run that failed because the button was disabled. The
   original cause is still available in the in-memory event log and in the
   exception chain.

3. **Write the trace to a non-atomic file** (direct write, no temp file +
   replace). *Rejected.* A crash or a full disk mid-write would leave a
   truncated JSON file that parses as valid but describes fewer events than
   the run actually produced — exactly the "contradictory evidence" case
   FR-034 prohibits.

4. **Buffer traces in memory and persist them asynchronously** (after
   `create_project()` returns). *Rejected for now.* It would move the
   failure out of the run's outcome entirely, which is the option this ADR
   exists to reject. It remains a candidate for a future persistent
   execution-history store, provided that store has its own durability and
   error-reporting contract.

## Consequences

**Positive**

- A reported success always has a corresponding evidence artifact.
- The execution history cannot silently develop holes.
- A cancelled run is never reported as a clean cancellation when its
  outcome was not recorded.
- The write is atomic, so a concurrent reader never observes a partial
  artifact.

**Negative / accepted cost**

- A run can fail for a reason that has nothing to do with the task: a full
  disk or a permissions problem turns a successful workflow into a reported
  failure. This is the intended trade — the alternative is an unverifiable
  success.
- On a trace-write failure, the original action failure is displaced from
  `result["error"]` and is not recoverable from disk.
- The trace directory is created on demand, so the *first* write into a
  previously non-existent directory can fail for environmental reasons that
  were not present when the code was tested.

**Residual risk**

- FR-034 also covers *contradictory* evidence. This decision implements the
  **missing**-evidence half. There is currently no check for a trace whose
  own events contradict each other (for example an `action_succeeded` event
  followed by a `verification_failed` terminal). See the open questions in
  [ADR-004](ADR-004-requirement-traceability-to-srs.md).

## Requirements / References

| Reference | Text / relevance |
|---|---|
| SRS FR-034 | "Prevent unsupported success claims: If the required evidence is missing or contradictory, the run must not be marked successful." |
| SRS FR-036 | "Produce a verification report: The report must include the requested outcome, each postcondition, evidence references, final status, and unresolved uncertainties." — the trace is the current evidence record; see the open question in ADR-004. |
| SRS FR-038 | "Store execution history: The system must retain configurable run metadata, traces, and verification outcomes." |
| SRS NFR-005 | "The system must preserve enough execution metadata to investigate failures after a run ends." |
| SRS §8.3 | Execution run fields (`status`, `final_verification`, `failure_category`) — partially represented today. |
| SRS §8.4 | Execution event fields — the trace event schema is currently a subset. |

**Implementation evidence**

- `chimera/tracing.py` — `TraceRecorder.finish()` (atomic write, `TraceWriteError`),
  `TRACE_SCHEMA_VERSION`, the three terminal statuses.
- `chimera/agent.py` — `_finish_trace()` and the three terminal handlers
  (`succeeded` / `failed` / `cancelled`).
- `tests/test_tracing.py` — `TraceWriteFailureTests`:
  `test_finish_raises_trace_write_error_on_oserror`,
  `test_write_error_message_surfaces_cause`; plus
  `test_artifact_write_is_atomic_no_tmp_left` and the terminal-status tests.
- `tests/test_integration.py` — `test_trace_write_failure_forces_run_to_failure`,
  `test_trace_write_failure_overrides_cancelled_result`.
- `docs/architecture.md` §6 · `docs/threat_model.md` T-6, T-8, T-12.
