# Chimera Evaluation — Criteria, Protocol, and Reporting

**Status: criteria and protocol are DEFINED; no evaluation has been run.**
This document states what "good" means for Chimera, how it will be
measured, and what may and may not be claimed from the results.

Companions: [`benchmark_design.md`](benchmark_design.md) (the concrete
benchmark: scenarios, trial protocol, result schema, example report) and
[`evaluation_approaches.md`](evaluation_approaches.md) (the survey of
established browser-agent evaluation methods this borrows from).

Requirements authority: SRS §11 (Evaluation and Acceptance Criteria), §12
(Testing Strategy), §15 (Phase 0). Requirement identifiers in this document
are **SRS** identifiers; see
[`adr/ADR-004-requirement-traceability-to-srs.md`](adr/ADR-004-requirement-traceability-to-srs.md)
for the project-label crosswalk. In particular, the project's internal
"FR-018" label denotes execution tracing and is **not** SRS FR-018 (which
is "use deterministic browser primitives").

---

## 1. Three kinds of evidence — do not conflate them

| Kind | What it is | What it can support |
|---|---|---|
| **Regression suite** | `tests/` — 83 assertions of specific behaviours (62 stdlib + 21 Chromium) | "This behaviour still works." Nothing about robustness, reliability, or general performance. |
| **Benchmark** | The harness in [`benchmark_design.md`](benchmark_design.md) | Measured rates on a declared scenario set, with n and confidence bounds, on the local demo target. |
| **Acceptance review** | SRS §11.1 / §18 checklist, read by a human against artifacts | Whether a release criterion is met. |

**The 83 passing tests are a regression suite, not evidence of general
browser-agent performance.** No number derived from them may be presented as
a success rate, a robustness figure, or a generalisation claim. They also
must not be reused verbatim as benchmark scenarios — the benchmark's
development/evaluation split exists precisely to keep that separation
(`benchmark_design.md` §4).

---

## 2. Evaluation criteria

Chimera's quality criteria at this milestone, in priority order.

### C-1 — Verifiable success

A run counts as successful only when its postconditions are **independently**
confirmed by a component that does not share the agent's verification path.
A click is not evidence. A self-reported success is not evidence.

*Grounded in:* SRS FR-034 (prevent unsupported success claims),
SRS FR-036 (produce a verification report), SRS §11.1 ("failed verification
cannot result in a successful terminal status").

### C-2 — Honest failure

When the task cannot be completed, the run must terminate as `failed`,
within a bounded time, with a diagnosable cause — and must never be
reported as a success. A bounded failure is a *correct* outcome on the
persistent-fault scenarios.

*Grounded in:* SRS NFR-001, NFR-002, NFR-003, FR-022, FR-028.

### C-3 — No unsupported side effects

The agent must not perform actions outside the task's scope. Today this is
enforced by the benchmark's independent action observer, not by the product
(the product's allowlist is type-level only — see §6.3).

*Grounded in:* SRS NFR-016, NFR-017, NFR-020; threat model T-2, T-3.

### C-4 — Determinism and reproducibility

The same input and configuration must produce the same terminal status. The
agent contains no model call, no randomness, and no adaptive reasoning, so
this is a property to be *verified*, not hoped for.

*Grounded in:* SRS §11.1 ("runs can be inspected and reproduced"), SRS
§11.2 ("reproducible terminal status: 100% of completed test episodes").

### C-5 — Inspectable evidence

Every run — succeeded, failed, or cancelled — must leave a durable,
ordered, timestamped record of what happened.

*Grounded in:* SRS FR-038, NFR-005, §8.3/§8.4.

### C-6 — Bounded, safe stop

Cancellation must stop the run at a safe boundary, close the browser
resources, and report a distinct terminal status. The stop latency must be
disclosed, not implied.

*Grounded in:* SRS FR-021, §9 state 12; ADR-002.

### C-7 — Session isolation

Runs must not observe each other's session state.

*Grounded in:* SRS NFR-012; ADR-001.

---

## 3. Benchmark protocol (summary)

Full specification in [`benchmark_design.md`](benchmark_design.md). In brief:

1. **Target** — the local demo app, `file://`, with its two fault
   parameters (`slow` transient, `disabled` persistent).
2. **Scenarios** — normal, transient-slow, persistent-disabled, and
   combined; each with a declared expected outcome. Planned but not yet
   implementable: multi-task, redirect, ambiguous-label, delayed-
   confirmation, prompt-injection, off-target.
3. **Splits** — a development manifest (may be debugged against) and a
   frozen, hashed evaluation manifest (held out). The split varies
   *parameter values and input values*, not *fault types*; that limit is
   stated in every report.
4. **Trials** — ≥5 per cell, plus a discarded warm-up; fresh browser
   context and page per episode; fixed manifest-declared order.
5. **Independent verification** — a separate component re-implementing the
   postconditions with **exact-match** semantics against the live page, plus
   a **human-audited sample** of the verifier's own decisions.
6. **Baselines** — A (deterministic replay), B (model-driven, unavailable),
   C (Chimera).
7. **Reporting** — every rate with its denominator, a 95% Wilson upper
   bound for every zero count, all cells reported including failures, and
   manifest hashes.

---

## 4. Metrics

### 4.1 Measurable with the current implementation

| Metric | Notes |
|---|---|
| Task success rate | Requires the independent verifier; agent self-report is not sufficient |
| **False-success rate** | The central metric. SRS §11.2 target: **0%** |
| Genuine failure rate | |
| Verifier disagreement (false-negative) rate | Reported separately; never merged into success |
| Unauthorised-action count | Harness-side observer (§4.3) |
| Safety-violation count | Any out-of-scope action or navigation |
| Retry count; actions per episode | From the trace |
| Latency: median, p95, min, max | |
| Reproducible terminal status | Fraction of re-executed episodes with the same status |
| Failure categories | WebArena-Lite taxonomy: unfinished exploration, premature response, invalid action, incomplete form workflow, timeout, other |
| Cancellation latency | With the ADR-002 bound stated alongside |

### 4.2 Not measurable yet — and must be reported as `null`, never `0`

| Metric | Blocked on |
|---|---|
| Recovery success rate | A recovery implementation **and** a defined set of designated recoverable failures **and** a baseline to compare against. Until all three exist, no recovery claim of any kind may be made. |
| Inconclusive rate | SRS §9's `INCONCLUSIVE` state (ADR-004 Q4). Today a verification timeout is reported as `failed`, so *inconclusive is not an observable category* — the metric has no denominator. |
| Generalisation success | More than one workflow and more than one target |
| Actions per successful task (comparative) | Baseline B |
| Model calls, token count, estimated cost | A model adapter |
| Human intervention frequency | A UI in which a human can intervene |
| Prompt-injection resistance | A model, plus the `S-INJECT` scenario. There is no LLM surface today, so there is nothing to resist. |
| Verification-report completeness (SRS FR-036) | The trace is not yet the FR-036 report: it lacks "unresolved uncertainties" (ADR-004 Q3) |

### 4.3 The false-success metric, precisely

```
false_success := (agent reported "succeeded") AND NOT (P1 AND P2 AND P3)
```

where `P1`–`P3` are the independently checked postconditions, and the
agent's report is read from the **persisted trace artifact's**
`terminal_status`, not from a return value in the same process.

The independent verifier must not import the agent's verification code. If
it did, the metric would be a tautology.

**A zero count is a bound, not a zero.** With 5 trials per cell, the 95%
Wilson upper bound on a 0/5 observation is **43.4%**; at 0/50 it is 7.1%;
at 0/100 it is 3.7%. A report claiming "0% false success" on 5 trials is a
reporting error. SRS §11.2's own "at least 100 task episodes" is the
minimum run size that makes a zero-rate claim meaningful.

---

## 5. Baselines and what the comparison may attribute

| Baseline | Definition (SRS §11.3) | Status | Purpose |
|---|---|---|---|
| **A — Deterministic replay** | Execute the recorded steps with fixed locators and no adaptive reasoning | **Not implemented** (harness artifact, must not enter `chimera/`) | Isolates the contribution of waiting + retry + verification |
| **B — Model-assisted execution** | A model interprets the task and chooses actions, without a learned reusable workflow | **Not available** — no model adapter exists | Isolates the contribution of learned workflows |
| **C — Chimera** | Structured workflows, state observation, constrained recovery, independent postcondition checks | **Partially exists** — structured workflow (one, hard-coded) and independent postcondition checks; **no** state observation layer, **no** constrained recovery | The system under test |

**Attribution rules.**

- With only Baseline A available, the A-vs-C difference is attributable to
  **waiting, retry, and verification** — and to nothing else. A single
  delta must never be presented as "the value of Chimera".
- SRS §11.3's stated goal — separating the contributions of workflow
  learning, recovery, and verification — is **not achievable** at this
  milestone, because only one of those three exists. This is stated in
  every report.
- Baseline B cells are `null` with the reason "not implemented", never `0`,
  and never omitted from the table.
- All baselines run under **the same scenario manifest, the same
  execution limits, and the same independent verifier**.

---

## 6. Reporting format

### 6.1 Required elements of a benchmark report

1. **Header** — benchmark id and version, run id, agent version, both
   manifest hashes, demo-app content hash, Playwright version, browser
   build, Python version, platform, trial count, warm-up policy, start and
   end timestamps.
2. **A summary table** — one row per (scenario × input × baseline) cell
   with: n, success count, false-success count, unauthorised actions,
   safety violations, retries/episode, latency p50 and p95, and the
   confidence bound on any zero count.
3. **A "not measurable" table** — every metric that is `null`, with its
   blocking reason.
4. **The verifier audit** — sample size, agreement rate, and whether the
   run's rates are therefore provisional.
5. **Failure breakdown** — by category, with a pointer to the underlying
   trace artifacts.
6. **A limitations paragraph** — §7 of this document, reproduced (not
   paraphrased) in the report.
7. **An explicit claim list** — what the run *does* support, and what it
   *does not*.
8. **Artifacts** — the result JSON, and the path of every episode's trace.

### 6.2 Rules

- Every rate carries its denominator.
- Every zero count carries its 95% Wilson upper bound.
- All manifest cells are reported, including failures.
- Harness errors are reported separately from agent failures, and are
  never silently dropped.
- Any exclusion is declared with its reason and count.
- Results from different manifest versions are not compared.

### 6.3 Required disclaimers

Every report carries, verbatim:

> The current test suite is a regression suite, not proof of general
> browser-agent performance.
>
> These results are measured on one local workflow against one local target
> with a two-parameter fault taxonomy. They do not generalise to other
> websites, workflows, fault models, browsers, or to model-driven agents.
>
> Baseline A compares fixed-step replay against Chimera's waiting, retry,
> and verification layers. It does not measure workflow learning, recovery,
> or the value of a model.
>
> No recovery improvement is claimed: no recovery implementation and no
> recovery baseline exist.

### 6.4 Prohibited claims

The following may **not** appear in a report, a slide, or a summary:

- Any statement that Chimera "performs at X%" on web tasks, or any
  comparison of Chimera's numbers with a published benchmark's numbers.
- Any recovery, generalisation, or model-performance claim.
- "0% false success" without its denominator and confidence bound.
- Any use of the project label "FR-018" to refer to SRS FR-018.
- Any implication that the 83 passing tests constitute an evaluation.
- Any claim of production readiness, or of conformance with SRS NFR-016,
  NFR-019, or FR-022 in full (all three are partially met — see
  `docs/threat_model.md` §1.2 and ADR-004).

---

## 7. Acceptance gates

SRS §11.2's targets are, in the SRS's own words, *"proposed initial release
gates, not established performance claims"*, and *"must be reported with
sample sizes and scenario definitions"*. Their current status:

| SRS §11.2 target | Target | Status at this milestone |
|---|---|---|
| Success on baseline workflows | ≥95% | **Not measured** — benchmark not built |
| Success on supported interface variations | ≥80% | **Not measurable** — no interface-variation scenario exists (the demo app's interface is fixed) |
| Recovery success on designated recoverable failures | ≥70% | **Not measurable** — no recovery implementation, no designated recoverable set |
| False-success rate | 0% on the release acceptance suite | **Not measured**; and note the sample-size bound (§4.3) |
| Unauthorized destructive actions | 0 | **Not measurable** — no destructive action exists in the current workflow; the harness observer (§4.3) can measure out-of-scope actions once built |
| Reproducible terminal status | 100% of completed episodes | **Not measured** — protocol defined, not run |
| Critical regression tests passing | 100% | **Met** — 83/83 as of the last full run (2026-10-24, re-confirmed under the new `pyproject.toml` pytest configuration) |

**Targets are goals, not results.** A table that shows a target and a
current-value column where the current value is "not measured" is the
required form; a table that shows a target and a blank or a zero is
misleading.

---

## 8. Limitations of the current evaluation capability

1. **Scale.** One workflow, one target, four fault scenarios, three input
   variations. Roughly 10–30 episodes per run at the default trial count —
   far below SRS §11.2's 100-episode minimum for a meaningful zero-rate
   claim.
2. **Fault taxonomy width.** Two parameters. The evaluation split varies
   values, not types. No unseen-fault generalisation can be assessed.
3. **Verifier risk.** The independent verifier is itself a component that
   can be wrong, in both directions. The human audit mitigates this; it does
   not eliminate it.
4. **Baseline coverage.** Only Baseline A is specified; B is unavailable and
   C lacks the recovery and observation layers SRS §11.3 assumes. The
   attribution SRS §11.3 asks for is out of reach.
5. **Metric gaps.** `INCONCLUSIVE` is not an observable category (§4.2),
   which limits how precisely "could not tell" can be distinguished from
   "failed".
6. **No adversarial coverage.** None of the SRS §12.4 adversarial scenarios
   are implementable against the current demo app.
7. **Latency comparability.** Absolute latencies are machine-specific;
   only same-machine before/after comparisons are meaningful, and the
   measured baseline set (happy path ≈0.12 s) is small relative to
   start-up overhead, which must be excluded or disclosed.

---

## 9. The six unresolved requirement-mapping questions

Carried from [`adr/ADR-004-requirement-traceability-to-srs.md`](adr/ADR-004-requirement-traceability-to-srs.md),
with the evaluation impact of each. **All six remain unresolved**; each is
marked below where it gates part of the evaluation.

| # | Question | Evaluation impact |
|---|---|---|
| 1 | Does SRS FR-018's "validated locators" mean a *target* allowlist, or are fixed semantic locators sufficient? | Affects how the unauthorised-action metric (§4.1) is framed: harness-observed vs. product-enforced. **Unresolved.** |
| 2 | What satisfies SRS FR-022's "number of actions"? | Affects whether "actions per episode" is a compliance metric or only a cost metric. **Unresolved.** |
| 3 | Is the JSON trace the SRS FR-036 verification report, or a separate artifact? | **Gates** C-5 and the completeness of the verification report. **Unresolved.** |
| 4 | How do the three terminal statuses map onto SRS §9's twelve states, and where does `INCONCLUSIVE` sit? | **Gates** the inconclusive metric (§4.2) and the failure-category taxonomy. **Unresolved.** |
| 5 | Must FR-034's "contradictory" evidence be detected explicitly? | Affects whether the false-success metric needs a second consistency check over the trace's own events. **Unresolved.** |
| 6 | Does SRS §8.3/§8.4 replace the trace schema or extend it under a version bump? | Affects the result schema's alignment with the run/event data model, and cross-run comparability. **Unresolved.** |

Questions 3 and 4 are the ones that most directly limit what the benchmark
can measure, and both should be settled before the first real run.

---

## 10. Capability roadmap

What unlocks what, in dependency order.

| Enables | Requires |
|---|---|
| A first honest benchmark run | Harness, manifests, independent verifier, Baseline A, verifier audit (§13 of the benchmark design) |
| A meaningful false-success rate | The same, at ≥100 episodes across the false-success path (§4.3) |
| An inconclusive rate | SRS §9 `INCONCLUSIVE` (ADR-004 Q4) |
| A recovery rate | A recovery implementation, a designated recoverable set, and a baseline |
| A model comparison (Baseline B) | A model adapter, with the model, prompt, and cost recorded per episode |
| An adversarial safety rate | The `S-INJECT` scenario **and** a model to inject into |
| An unauthorised-navigation rate | A second target and the `S-OFFTARGET` scenario |
| A generalisation rate | ≥2 workflows and ≥2 targets |

---

## 11. Related documents

- [`benchmark_design.md`](benchmark_design.md) — scenarios, trial protocol,
  result schema, example report, threats to validity.
- [`evaluation_approaches.md`](evaluation_approaches.md) — the survey of
  established browser-agent evaluation methods and the source for every
  methodological choice above.
- [`architecture.md`](architecture.md) — the behaviour being measured.
- [`threat_model.md`](threat_model.md) — R-1, R-2, R-5, R-9 are the
  controls the planned adversarial scenarios would exercise.
- [`adr/`](adr/) — ADR-002 (cancellation bounds), ADR-003 (trace
  persistence as a success precondition), ADR-004 (the six open questions).
- `CURRENT_STATUS.md` — measured results and the open backlog.
