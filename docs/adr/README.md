# Architecture Decision Records

Decision records for Project Chimera. The SRS (`PROJECT_CHIMERA_SRS.md`) is
the requirements authority; these ADRs record decisions the project has made
*within* that authority, or gaps it has consciously left open.

SRS §15 lists "Architecture decision records" as a Phase 0 deliverable and
SRS §16 requires a `docs/adr/` directory.

## Index

| ADR | Title | Status | Date |
|---|---|---|---|
| [ADR-001](ADR-001-per-run-browser-and-context-isolation.md) | Per-run browser and browser context isolation | Accepted | 2026-10-24 |
| [ADR-002](ADR-002-cooperative-cancellation-at-safe-boundaries.md) | Cooperative cancellation at safe execution boundaries | Accepted | 2026-10-24 |
| [ADR-003](ADR-003-trace-persistence-precondition-for-success.md) | A run cannot be reported successful when its trace cannot be persisted | Accepted | 2026-10-24 |
| [ADR-004](ADR-004-requirement-traceability-to-srs.md) | Requirement traceability to the authoritative SRS | Accepted | 2026-10-24 |
| [ADR-005](ADR-005-runner-refuses-on-policy-divergence.md) | The benchmark runner refuses to execute a manifest whose retry policy diverges from the agent's | Accepted | 2026-10-24 |

## Status vocabulary

| Status | Meaning |
|---|---|
| **Accepted** | The decision is implemented in the current code and supported by the project status. The ADR describes what the code does, not an intention. |
| **Proposed** | Recorded for discussion; **not** implemented. Nothing in the codebase should be described as satisfying a Proposed decision. |
| **Superseded** | Replaced by a later ADR. The superseding ADR is named in the header. |
| **Deprecated** | No longer relevant, and not replaced. |

Each ADR carries the sections **Status, Context, Decision, Alternatives
Considered, Consequences, and Requirements/References**.

## Writing a new ADR

1. Number sequentially: `ADR-NNN-<short-kebab-title>.md`. Do not renumber
   existing records.
2. Set **Status** to `Proposed` unless the decision is already implemented
   and supported by `CURRENT_STATUS.md`. Do not use `Accepted` for a
   decision that only exists in the ADR.
3. Cite **SRS identifiers and their text**, not the project's internal
   shorthand — see [ADR-004](ADR-004-requirement-traceability-to-srs.md).
4. List alternatives that were actually considered. Do not claim an
   alternative was tested or benchmarked unless a result exists in
   `CURRENT_STATUS.md`.
5. Name the enforcement point: the file and construct that implements the
   decision, and the test that proves it.
6. Update this index and the ADR list in `CURRENT_STATUS.md`.
