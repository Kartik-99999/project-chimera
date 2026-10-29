# ADR-004 — Requirement traceability to the authoritative SRS

- **Status:** Accepted
- **Date:** 2026-10-24
- **Deciders:** Project Chimera maintainers
- **Supersedes:** none
- **Related:** [ADR-001](ADR-001-per-run-browser-and-context-isolation.md), [ADR-002](ADR-002-cooperative-cancellation-at-safe-boundaries.md), [ADR-003](ADR-003-trace-persistence-precondition-for-success.md)

---

## Status

**Accepted** — the crosswalk was verified directly against
`PROJECT_CHIMERA_SRS.md` in the session in which this ADR was written, and
is published in `docs/architecture.md` §11 and `CURRENT_STATUS.md`. The
*rule* (SRS text is authoritative) is accepted and in force; the
**relabelling follow-on described under Consequences is Proposed and not
implemented**.

---

## Context

`PROJECT_CHIMERA_SRS.md` is the requirements authority for Project Chimera.
It defines functional requirements `FR-001…FR-049` and non-functional
requirements `NFR-001…NFR-030`.

During implementation, the project adopted an internal shorthand for
milestone work. That shorthand was **not** derived from the SRS identifier
space, and in one case it collides with a live SRS requirement of a
different meaning:

- The project's **"FR-018"** labels *execution tracing*.
- **SRS FR-018** is *"Use deterministic browser primitives (P0): Playwright
  must execute approved browser operations using validated locators and
  bounded timeouts."*

These are different requirements. A reader who assumes the project label
refers to SRS FR-018 would conclude that tracing was the requirement
addressed; in fact the tracing work corresponds to SRS FR-036, SRS FR-038,
and the §8.3/§8.4 data model, while SRS FR-018 addresses the executor
itself.

A label collision like this is not merely cosmetic. Compliance auditing,
gap analysis, and the release acceptance checklist (SRS §18) all run
against the SRS identifiers. A vocabulary that silently disagrees with the
authority makes every such audit unreliable.

This ADR therefore records the crosswalk explicitly, and states the rule
for resolving any future mismatch.

## Decision

**The SRS text is authoritative. The project's internal shorthand is
non-authoritative, and is retained only as a convenience label.**

Where a project label is used in this repository, it resolves through the
crosswalk below rather than by numeric identity.

### Verified crosswalk

Every row below was checked against the SRS text in this session (not
against prior notes).

| Project label | SRS requirement | SRS text (abridged) | Implementation status |
|---|---|---|---|
| **FR-018** (project: *execution tracing*) | *not* SRS FR-018 | SRS FR-018 = "Use deterministic browser primitives: Playwright must execute approved browser operations using validated locators and bounded timeouts." | **Label collision.** Tracing maps to SRS FR-036 + FR-038 + §8.3/§8.4. Separately, SRS FR-018 is *partially* met by the implemented executor: approved operations (allowlist) and bounded timeouts (`ACTION_TIMEOUT_MS`) yes; "validated locators" only as fixed semantic locators — there is no locator allowlist, so see NFR-016. |
| FR-021 | SRS FR-021 | "Support cancellation: The user must be able to stop an active run. The system must stop scheduling further actions and handle browser cleanup safely." | **Accepted** — [ADR-002](ADR-002-cooperative-cancellation-at-safe-boundaries.md). |
| FR-022 | SRS FR-022 | "Limit execution resources: Each run must have configurable limits on duration, number of actions, retries, and model calls." | **Partial.** Duration and retries are configurable via `RetryPolicy`. There is no run-level limit on *number of actions*, and no model-call budget (no model exists yet). |
| FR-028 | SRS FR-028 | "Prevent blind retries: The system must not repeat an action merely because a response was delayed. Before retrying, it must check whether the intended effect already occurred." | **Accepted** for the CLICK path (the `is_effect_achieved` hook). NAVIGATE and FILL refuse the retry outright (`BlindRetryRefusedError`), which satisfies the requirement conservatively. |
| FR-034 | SRS FR-034 | "Prevent unsupported success claims: If the required evidence is missing or contradictory, the run must not be marked successful." | **Accepted** for missing evidence — [ADR-003](ADR-003-trace-persistence-precondition-for-success.md). The *contradictory*-evidence half is not implemented. |
| NFR-012 | SRS NFR-012 | "Browser sessions must be isolated between test runs where practical." | **Accepted** — [ADR-001](ADR-001-per-run-browser-and-context-isolation.md). |
| NFR-016 | SRS NFR-016 | "The action executor must enforce an allowlist of permitted operations **and targets**." | **Partial.** Operations are enforced (`ALLOWED_ACTIONS`); targets (URL, locator, value) are **not**. |
| NFR-019 | SRS NFR-019 | "Screenshots and traces must avoid capturing unnecessary credentials or personal data." | **Partial.** Nothing unnecessary is captured given the controlled target; there is no redaction mechanism for other targets. |

### Recording rules

1. New work cites **SRS identifiers**. A project shorthand may be used in
   prose, but never as the sole reference to a requirement.
2. Where the project shorthand and an SRS identifier collide (as with
   FR-018), the SRS identifier governs and the shorthand is disambiguated in
   the same sentence.
3. Any claim of the form "requirement X is met" requires the SRS text, not
   the project label, and requires the enforcement point in the source.

### Open questions (unresolved, need an owner ruling)

These are recorded rather than answered, because answering them requires a
judgement about intent that the source and the SRS do not settle:

1. **Does SRS FR-018's "validated locators" mean a target allowlist?** It
   can be read as (a) locators that are validated *structurally* — role- and
   label-based rather than brittle CSS, which the implementation does — or
   (b) locators validated against a *permitted set*, which would duplicate
   NFR-016's "and targets" and is not implemented. This repository takes the
   stricter reading (b) for gap-tracking purposes.
2. **What satisfies SRS FR-022's "number of actions"?** The current
   `RetryPolicy.max_attempts` bounds *retries* per action, not the number of
   actions in a run. A run-level action budget belongs to the workflow
   layer, which does not exist yet.
3. **Is the JSON trace the SRS FR-036 "verification report", or a separate
   artifact?** FR-036 requires the report to include "the requested outcome,
   each postcondition, evidence references, final status, and **unresolved
   uncertainties**" — the last of which the current trace does not carry.
   The relationship between the trace artifact and a future FR-036 report is
   undecided.
4. **How do the three terminal statuses map onto the twelve SRS §9
   states?** Chimera distinguishes `succeeded` / `failed` / `cancelled`;
   §9 also defines `INCONCLUSIVE` ("evidence is insufficient to establish
   success or failure"), and NFR-001 requires that every run terminate in
   an explicit state including inconclusive. The mapping — including which
   intermediate states the current linear flow actually traverses — is
   unresolved, and §9's "state transitions must be validated by code" is not
   implemented.
5. **Must FR-034's "contradictory" evidence be detected explicitly?** The
   implementation covers *missing* evidence. Whether a self-contradictory
   trace (e.g. `action_succeeded` followed by `verification_failed`) needs
   an explicit consistency check, or whether the existing verification
   logic already makes it impossible, is undecided.
6. **Does the SRS §8.3/§8.4 data model replace the current trace schema, or
   extend it?** The current event schema is a subset of §8.4 (no
   `event_id`, `observed_state_reference`, `action_proposal`,
   `executed_action`, `recovery_attempt`; the outcome field is named
   `action_outcome` rather than `outcome`). Whether the future schema
   supersedes `schema_version: 1` or evolves under a version bump is
   undecided.

## Alternatives Considered

1. **Rename the project labels immediately to match the SRS.** *Proposed,
   not yet done.* It would remove the collision outright, but it churns
   `CURRENT_STATUS.md`, module docstrings, and test names across the whole
   repository, and several labels (`FR-018` for tracing) are already
   embedded in the milestone history. Recorded as a follow-on action, not
   done here.
2. **Abandon the internal shorthand and cite only SRS identifiers
   everywhere.** *Rejected for now.* It loses the project's own stable
   milestone vocabulary mid-project, and the shorthand is only a problem
   where it *collides* — which is now precisely recorded.
3. **Keep the crosswalk implicit in prose.** *Rejected.* A crosswalk that
   lives only in a document's prose is one refactor away from being wrong.
   Recording it as an ADR with per-row status makes it auditable.
4. **Treat the SRS as advisory and the project labels as the contract.**
   *Rejected.* The SRS is the requirements authority; the release
   acceptance checklist (SRS §18) and the required deliverables
   (SRS §17) are written against it.

## Consequences

**Positive**

- Any future compliance audit, gap analysis, or release checklist run can
  use the crosswalk directly and will not silently mis-attribute the
  tracing work to SRS FR-018.
- The row-level status column makes the partial requirements (FR-022,
  NFR-016, NFR-019) visible instead of implied.
- The open questions are written down where they will be found, rather than
  rediscovered later.

**Negative / accepted cost**

- Two vocabularies coexist. The disambiguation rule (always cite the SRS
  identifier) is a discipline that must be maintained by hand.
- The crosswalk will itself go stale as work proceeds and must be updated
  with each ADR.

**Follow-on action (proposed, not implemented)**

- Relabel the project's internal `FR-018` (tracing) to a non-colliding
  shorthand — for example `TR-018` or `FR-036` — across `CURRENT_STATUS.md`,
  the module docstrings, and the test names — and record the rename in a
  further ADR.

## Requirements / References

| Reference | Relevance |
|---|---|
| SRS §17 | Required Project Deliverables — written against the SRS identifiers. |
| SRS §18 | Release Acceptance Checklist — all items currently unchecked; each must be assessed against the SRS text. |
| SRS §15 Phase 0 | "Architecture decision records" is an explicit Phase 0 deliverable. |
| SRS §16 | Required repository layout includes `docs/adr/`. |
| SRS §9 | Execution State Machine — twelve states, including `INCONCLUSIVE`. |
| SRS §8.3 / §8.4 | Execution run and execution event data models. |
| SRS NFR-001 | "Every run must terminate in an explicit state: succeeded, failed, cancelled, or inconclusive." |

**Implementation evidence**

- `docs/architecture.md` §11 — the mapping summary this ADR makes
  normative.
- `docs/threat_model.md` §1.2 — the requirement-status table for the
  security and reliability goals.
- `CURRENT_STATUS.md` — the "Requirement-label mapping" section.
- Verification method: each SRS identifier and its text was read directly
  from `PROJECT_CHIMERA_SRS.md` in the session in which this ADR was
  written; no row rests on memory or on a prior note.
