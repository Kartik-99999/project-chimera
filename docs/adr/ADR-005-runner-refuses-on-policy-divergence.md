# ADR-005 — The benchmark runner refuses to execute a manifest whose retry policy diverges from the agent's

- **Status:** Accepted
- **Date:** 2026-10-24
- **Implemented:** 2026-10-28 (benchmark harness Stage 2)
- **Deciders:** Project Chimera maintainers
- **Supersedes:** none
- **Related:** [ADR-002](ADR-002-cooperative-cancellation-at-safe-boundaries.md), [ADR-003](ADR-003-trace-persistence-precondition-for-success.md), [ADR-004](ADR-004-requirement-traceability-to-srs.md)

---

## Status

**Accepted** — the decision is implemented in the current code. The
benchmark runner (`benchmarks/runner.py`) enforces the refusal in
`check_policy_alignment`, called by `Runner.run` before any episode is
scheduled, and `tests/test_benchmark_runner.py` proves the refusal and
that no episode executes under a divergent manifest. `CURRENT_STATUS.md`
records the verifying test run (214 passed, 2026-10-28).

---

## Context

SRS FR-022 requires that retries be "bounded and non-blind", and
`docs/benchmark_design.md` §7.6 requires that a benchmark run record the
policy it executed under. The manifest schema (§9) therefore carries a
`config.policy` block, and the result schema carries the same block in the
run's `config`.

Two things make the relationship between the manifest's policy and the
agent's policy a genuine question rather than a copy-and-paste:

1. **The agent has exactly one policy.** `chimera.agent.DEFAULT_POLICY` is
   `max_attempts=2`, `base_delay_seconds=0.05`, `max_delay_seconds=0.2`,
   `max_total_seconds=5.0`, and `chimera.agent.ACTION_TIMEOUT_MS` is
   derived from it. `create_project()` passes `DEFAULT_POLICY` at every
   call site. There is **no injection seam**: a manifest can describe a
   policy, but nothing can make the agent run under it.
2. **The two can drift apart silently.** Nothing in the product or in the
   Stage 1 contracts compares them. A manifest that declares
   `max_attempts: 5` would validate, hash, and run — under a policy of
   `max_attempts: 2` — and the result file, if it copied the manifest,
   would assert a policy that was never in force.

The Stage 1 implementation raised this as **AMB-9** in
[`benchmark_design.md`](../benchmark_design.md) §14, with the question left
for Stage 2 (the runner).

---

## Decision

**A manifest whose declared execution policy diverges from the agent's
effective policy is refused. The runner does not execute a single episode
under it.**

- The check compares, field by field, the manifest's `config.policy`
  against `chimera.agent.DEFAULT_POLICY`, and the manifest's
  `config.action_timeout_ms` against `chimera.agent.ACTION_TIMEOUT_MS`.
- Floats are compared with a tolerance; integers exactly.
- On divergence the runner raises `PolicyMismatchError`, which is a
  `RunnerError` and a `ConfigurationError`. The error message **names every
  diverging field** with the manifest's value and the agent's value.
- The check runs **before** the first episode, so a refused run costs no
  browser time and leaves no partial artifacts.
- The result file of a run that *did* execute records the policy it
  executed under, in `config.policy`, alongside the agent version.

**Enforcement point:**
`benchmarks/runner.py::check_policy_alignment`, called by
`benchmarks/runner.py::Runner.run` before any episode is scheduled.
Proven by `tests/test_benchmark_runner.py::PolicyAlignmentTests`
(`test_refusal_executes_no_episode` asserts zero executor calls and no
artifacts on refusal).

---

## Alternatives Considered

1. **Run anyway, and record the agent's *effective* policy in the result.**
   *Rejected.* The manifest's `config.policy` would be silently ignored.
   A manifest that misdeclares its policy would still run and still
   produce a result file, so the mistake would never surface. It also
   breaks §4.1: the manifest hash is the versioning mechanism, and if the
   declared policy does not determine the executed policy, two runs with
   the same manifest hash can have run under different policies.

2. **Run anyway, record the manifest's declared policy, and emit a
   warning.** *Rejected.* This is the worst of the three: the result file
   asserts a policy that was not in force, and the warning is not a
   control. It is the "missing metric reported as a zero" failure mode
   applied to a policy.

3. **Add a policy-injection seam to `chimera.agent` so the manifest's
   policy is honoured.** *Not rejected on merit — deferred.* This is how
   the restriction would be lifted: `create_project()` would take a
   `policy` argument, and the runner would pass the manifest's. It is a
   **product** change: it alters the agent's behaviour and therefore
   invalidates the 83-test regression baseline, and it is a decision for
   the product owner rather than the harness. It is out of scope for the
   benchmark harness and is not claimed as backlog item 4.

4. **Refuse, but only for the evaluation split.** *Rejected.* The
   development split is where a policy mistake is cheapest to find and
   most tempting to leave in place; the evaluation split is the one where
   a misconfigured run would be least likely to be noticed and most
   costly. The rule is the same for both splits.

---

## Consequences

**Positive**

- A result file's `config.policy` always describes the policy that was
  actually in force.
- A manifest whose policy has drifted from the agent's is caught in
  milliseconds, before any measurement is taken, with a message that names
  the diverging fields.
- The manifest hash continues to identify what was executed (§4.1,
  AMB-7).

**Negative / accepted cost**

- A manifest cannot currently request a different retry policy. Anyone
  who wants to measure, say, a 3-attempt policy must first change the
  product and the baseline, not the manifest. This is a real limit on
  what the benchmark can vary, and it is stated in the result file's
  notes.
- If the agent's policy changes, the shipped manifests must change in the
  same change or the runner will refuse them. That is the intended
  coupling: the manifest and the agent are one measured configuration.
- The check couples the harness to `chimera.agent`'s module-level names.
  If the agent's policy moves, the harness check moves with it. The
  alternative — duplicating the policy's values in the harness — would
  create a second source of truth that could itself drift.

**Residual risk**

- The check compares *values*, not *behaviour*. A manifest that declares
  the agent's current policy would still be refused if the agent's retry
  *semantics* changed (for example, if `max_total_seconds` were
  reinterpreted as a per-attempt budget) without the numbers changing.
  Nothing in the harness can detect that; only a change to the agent's
  retry semantics requires a manifest review, and the numbers check is
  there to catch the common case.

---

## Requirements / References

- SRS FR-022 (bounded, non-blind retries), FR-027 (bounded retry budget),
  FR-028 (retry policy applied to observable actions).
- `docs/benchmark_design.md` §7.6 (the run records its policy), §14.1
  (the resolution of AMB-9), §4.1 (the manifest hash is the versioning
  mechanism).
- `docs/evaluation.md` §4.1 (retry count is measured from the trace),
  §4.2 (a metric that cannot be measured is reported as `null` with a
  reason, never `0`).
- `chimera/agent.py` — `DEFAULT_POLICY`, `ACTION_TIMEOUT_MS`.
- `benchmarks/manifest.py` — `RetryPolicyConfig`, `RunConfig`.
- `benchmarks/runner.py` — `check_policy_alignment`, `PolicyMismatchError`.
- `tests/test_benchmark_runner.py` — the refusal, the itemised reason, and
  the proof that no episode is executed.
