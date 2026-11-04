# Chimera Initial Benchmark — Design

**Status: IMPLEMENTED AND RUN.** Dev runs are complete and audited;
held-out eval runs are complete with a provisional report (human audit
deferred). Everything in this document is still the design: no number
in this file is a measured result — measured figures live only in the
rendered reports under `artifacts/`.

Companion to [`evaluation.md`](evaluation.md) (criteria, baselines, reporting)
and [`evaluation_approaches.md`](evaluation_approaches.md) (the survey this
design borrows from). Requirements authority: SRS §11, §12, §15.

---

## 1. Purpose and scope

A reproducible, versioned harness that measures Chimera's **deterministic
browser execution** against the local demo application under injected faults,
with postconditions verified by a component that is **independent of the
agent's own verification path**.

The harness itself is future work. This document specifies it; it does not
build it. No application code is changed by this design.

### 1.1 What this benchmark can support

- Whether the agent completes the task when the page behaves as expected.
- Whether it completes the task when the page is **temporarily** degraded
  (slow load) versus **persistently** degraded (disabled control).
- Whether a reported success is **independently** confirmed (false-success
  rate).
- Whether the agent ever performs an action outside the scenario's
  permitted set (unauthorized-action rate).
- Per-scenario latency, retry count, and outcome distribution, with
  confidence intervals.

### 1.2 What it cannot support — read this before quoting any number

- **No claim about general browser-agent performance.** One workflow, one
  local target, two fault parameters. This is a regression-and-robustness
  harness. It is not in the same class as WebArena, WorkArena, or Mind2Web
  and must never be described as such.
- **No generalisation claim.** The fault space is `{slow, disabled}` — two
  parameters. The evaluation split varies *parameter values and input
  values*, not *fault types*. A held-out set here measures robustness to
  parameter variation within a known taxonomy, **not** generalisation to
  unseen faults.
- **No recovery claim.** There is no recovery implementation. The
  "recovery success" metric in SRS §11.2 is **not measurable** and is
  reported as `null`, not as `0` and not as "N/A" in prose.
- **No model claim.** There is no model. Model calls and model cost are
  `0` by construction, not by measurement.
- **No comparison to published numbers.** No published result uses this
  task, this target, or this fault taxonomy. Cross-paper numbers are not
  comparable.
- **The existing test suite is not this benchmark.** `tests/` is a
  regression suite asserting specific behaviours; it is not an evaluation
  and its pass rate says nothing about robustness. The two must not be
  conflated, and the test suite's scenarios may not be reused verbatim as
  evaluation scenarios (§4).

---

## 2. Target, task, and postconditions

**Target.** `demo_app/index.html`, served over `file://`. Two fault
parameters, read from the URL on load:

| Param | Effect | Class |
|---|---|---|
| `?slow=<ms>` | The name input and Create button start `disabled` and are re-enabled after `<ms>`. | **Transient** — resolves on its own. |
| `?disabled=1` | The Create button and name input stay `disabled` until the in-page Reset is pressed. | **Persistent** — does not resolve on its own. |
| both | The `slow` timer re-enables the controls only if `disabled` is not set, so the combined case stays disabled. | **Persistent**, with an initial transient phase. |

**Task.** Create a project with a given name. The agent must navigate to the
target, fill the name, click "Create Project", and satisfy the
postconditions.

**Postconditions (independently verified).** Derived from the demo app's
actual behaviour (`item.textContent = projectName`, where `projectName` is
the *trimmed* input; the submit handler returns early for an empty name or
a disabled button):

| ID | Postcondition | Check |
|---|---|---|
| `P1` | Confirmation is visible | `#confirmation` is visible |
| `P2` | The project appears in the list, **exactly once** | exactly one `#project-list li` whose `textContent` **equals** the expected trimmed name |
| `P3` | The list contains no unexpected entries | the count of `#project-list li` equals 1 |
| `P4` | The task was not created by the page's own state | the list is empty before the agent's click (checked by the harness at navigation time) |

`P1`–`P3` are the agent's own postconditions, restated; `P2`/`P3` are
evaluated by the **independent verifier** (§5), not by
`chimera/agent.py`. `P4` is harness-only and exists to make the
"duplicate/pre-existing record" scenario expressible.

**Why `P2` is exact-match, not substring.** The agent's own verification
uses `page.locator("#project-list li", has_text=project_name)`.
Playwright's `has_text` with a string is a **case-insensitive substring**
match. The independent verifier instead compares `textContent` for
**equality** with the expected trimmed name. The two differ in a way the
benchmark must be able to detect:

- *Trim*: the app stores the trimmed name. A request of `"  Alpha  "` makes
  the app store `"Alpha"`, while the agent looks for the substring
  `"  Alpha  "` — which is not present. This is a **false negative** (a
  genuine failure reported as a failure). Safe direction.
- *Substring/case*: had the list contained `"Alpha Beta"` or `"alpha"`, a
  request for `"Alpha"` would satisfy the agent's check without the exact
  project existing. This is a **false positive** — and therefore a
  false-success candidate. It is **not reachable in the current
  single-task flow** (the list is empty at every run start, because each run
  gets a fresh context and a fresh page load). It *is* reachable in any
  multi-task or pre-populated-list variant, which is why the verifier is
  specified to be exact-match from the start and why §12.2 lists the
  multi-task variant as a planned scenario.

This is recorded as a **risk to be measured**, not as a confirmed defect.

---

## 3. Scenario catalogue

### 3.1 Fault scenarios (implementable today)

| ID | Split | URL params | Fault class | Expected outcome |
|---|---|---|---|---|
| `S-NORM` | dev + eval | *(none)* | none | success |
| `S-SLOW` | dev + eval | `?slow=<ms>` | transient | success (the agent must wait for the control to become enabled) |
| `S-DIS` | dev + eval | `?disabled=1` | persistent | **failure** — success is impossible; the correct behaviour is to fail within the budget |
| `S-SLOWDIS` | dev + eval | `?slow=<ms>&disabled=1` | persistent (with transient phase) | **failure** — the transient phase must not be mistaken for success |

The `S-DIS` and `S-SLOWDIS` scenarios are **negative** scenarios. Their
expected outcome is failure, and the benchmark's job is to confirm the agent
fails *correctly* (bounded time, clear error, terminal `failed`, no false
success) rather than to maximise their success rate. Reporting a high
success rate on `S-DIS` would be a **bug indicator**, not an achievement.

### 3.2 Planned scenarios (require work before they can run)

| ID | Requires | Purpose |
|---|---|---|
| `S-MULTI` | A demo-app variant that pre-populates the list and/or accepts multiple projects | Makes the substring-vs-exact-match difference reachable; tests duplicate-record handling (SRS §12.4) |
| `S-REDIRECT` | A demo-app variant that redirects | Unexpected redirects (SRS §12.4) |
| `S-AMBIG` | A demo-app variant with two "Create Project" controls | Ambiguous button labels (SRS §12.4) |
| `S-DELAY` | A demo-app variant that delays the confirmation | Delayed confirmations (SRS §12.4) |
| `S-INJECT` | A demo-app variant that renders adversarial instruction text | Prompt injection in page content (SRS §12.4, NFR-015) — **not** currently a surface, since there is no model |
| `S-OFFTARGET` | A harness that points the agent at a second, non-permitted target | Unauthorized navigation (threat model T-2) |

### 3.3 Input variations

Applied within each scenario. These vary the *input*, not the fault, and are
split between dev and eval.

| ID | Input | Why |
|---|---|---|
| `I-PLAIN` | `Benchmark Project` | Baseline |
| `I-SUBSTR` | `Benchmark` (a prefix of `Benchmark Project`) | Probes the substring/exact-match distinction |
| `I-SPACE` | `  Padded Name  ` | Probes trim behaviour (§2) |
| `I-UNICODE` | `Проект — Ünïcode ✓` | Probes non-ASCII handling in fill and verification |

---

## 4. Development vs. evaluation split, and split discipline

The current test suite exercises the demo app with `?slow=2000`,
`?disabled=1`, and `?slow=2000&disabled=1`. If the benchmark reused those
exact scenarios, the benchmark would be measuring the agent on cases it was
tuned against.

**Rule.** Two manifests, both versioned and content-hashed:

- `benchmarks/manifests/dev-v1.json` — scenarios the agent may be developed
  and debugged against. Contains the parameter values already used by the
  test suite (`slow=2000`) and the full input-variation list.
- `benchmarks/manifests/eval-v1.json` — held out. Contains **different
  parameter values** within a documented band, and a **subset** of input
  variations.

| Parameter | Development band | Evaluation band | Constraint |
|---|---|---|---|
| `slow` | 2000 ms | 800, 1350, 2100, 3000, 3900 ms | **Both bands are within [500, 4000] ms.** The band is documented so that the scenario's class (transient, resolvable inside `ACTION_TIMEOUT_MS` = 5000 ms) is stable. A `slow` value above 4000 ms would change the scenario's class and is excluded. |
| `disabled` | `1` | `1` | The only value the demo app accepts. |

**Discipline rules.**

1. The evaluation manifest is **frozen** (content hash recorded) before a
   run. Changing it invalidates the run.
2. Evaluation-scenario parameter values are **never** used to debug the
   agent. If a defect is found via an evaluation scenario, the *dev*
   manifest gains a regression scenario and the evaluation manifest is
   re-versioned (never silently edited).
3. The honest limit of this split is recorded in the report: the split
   varies **values**, not **fault types**. §12.3.
4. A report states the manifest hash of both manifests. Results from
   different manifest versions are not compared.

---

## 5. Independent verification (the false-success mechanism)

This is the most important part of the design. The agent's own verification
is part of the system under test; using it to grade the system would make
the false-success metric measure nothing.

**The verifier is a separate component** that:

1. Reads the final DOM state **from the page**, not from the agent's
   result dict or its trace.
2. Checks `P1`–`P3` with exact-match semantics (§2).
3. Determines the **agent-reported outcome** from the trace artifact's
   `terminal_status` — read from the persisted JSON, not from a return
   value in the same process.
4. Computes the false-success set:

```
false_success := (agent reported "succeeded") AND NOT (P1 AND P2 AND P3)
```

5. Records a `verifier_disagreement` for any case where the agent reported
   `failed` but the independent verifier finds all postconditions hold
   (a **false negative**, which the WebArena-Lite audit shows is the more
   common grader error) — reported separately, never merged into success.

**Verifier audit.** The verifier is itself fallible. Before any rate is
published, a human must adjudicate a random sample of the run's episodes
and the agreement rate between the verifier and the human must be reported
alongside the results. This is the direct lesson of the WebArena-Lite audit
(`evaluation_approaches.md` §8). If verifier/human agreement is below 95%
on the sample, the run's rates are reported as **provisional** and the
disagreement cases are published.

**The verifier must not share code with the agent.** It re-implements the
postcondition checks against the raw page. Sharing a helper would make the
false-success metric a tautology.

---

## 6. Baselines

SRS §11.3 requires three approaches compared on the same scenarios with
comparable execution limits.

### Baseline A — Deterministic replay *(implemented: `benchmarks/baseline_a.py`)*

A scripted driver that performs the fixed steps — navigate, fill, click —
with fixed locators and **no** adaptive waiting, no retry, no fault
awareness, and no tracing. It is scored by the same independent verifier.

Purpose: isolate the value of the safety layer. Prediction: Baseline A
succeeds on `S-NORM` and fails on `S-SLOW` (it clicks a disabled control
too early), `S-DIS` and `S-SLOWDIS`. The gap between A and C is the
measured contribution of waiting-and-retry behaviour.

Implementation note: Baseline A is a **harness artifact**, not production
code. It must not be added to `chimera/`.

### Baseline B — Model-driven execution *(not available)*

A model interprets the task and chooses actions, without a learned reusable
workflow. Requires a model adapter, which does not exist.

When it becomes available it must be run under **the same scenario
manifest, the same action/time budget, and the same independent verifier**,
and it must record model calls, token counts, and estimated cost per
episode. Until then, every Baseline B cell in a report is `null` with the
reason "not implemented" — never `0`, and never omitted from the table.

### Chimera (C) — the system under test

The current implementation: allowlisted actions, bounded non-blind retries,
cooperative cancellation, explicit postcondition verification, per-run
browser and context isolation, and a JSON trace per run.

### 6.1 What the comparison can and cannot attribute

With only Baseline A available, the comparison attributes the difference
between A and C to **waiting + retry + verification**, and to nothing else.
It cannot separate the contributions of workflow learning, recovery, or
independent verification, because none of those exist. The report must say
so rather than presenting a single delta as "the value of Chimera".

---

## 7. Trial protocol

1. **Reset.** Before every episode, the harness opens a **fresh** browser
   context and a **fresh** page (the demo app's state is in-memory and
   per-page-load, so a fresh page load is a full reset). The in-page Reset
   button is exercised separately as a scenario, not as the per-episode
   reset mechanism.
2. **Trial count.** Default **5 trials per (scenario, input, baseline)**
   cell. Justification and its limits are in §10.2.
3. **Order.** Trials within a cell are executed in sequence; cells are
   executed in a **fixed, manifest-declared order**. The order is recorded
   in the result file. No randomisation at this size — with n=5, a random
   order adds variance without adding coverage.
4. **Isolation.** Each episode gets its own browser and context, per
   ADR-001. No state carries between episodes.
5. **Warm-up.** The first episode of a run is a **warm-up** and is
   excluded from the reported statistics but retained in the artifacts.
   Browser start-up cost is otherwise charged to the first cell measured.
6. **Determinism.** The agent is deterministic; the harness records the
   demo-app content hash, the manifest hash, the agent version, the
   Playwright version, the browser build, the Python version, and the
   platform in every result file.
7. **Cancellation.** Cancelled episodes are a distinct outcome and are
   reported separately. The cancellation latency distribution (§8.3) is
   reported, with the ADR-002 bound stated alongside it.
8. **Artifacts.** Every episode's trace artifact path is recorded, so any
   number in a report can be traced back to a per-episode event log.

---

## 8. Metrics

### 8.1 Measurable now

| Metric | Definition | Source |
|---|---|---|
| Task success rate | Episodes where the agent reported `succeeded` **and** the independent verifier confirms `P1 ∧ P2 ∧ P3` | verifier + trace |
| **False-success rate** | Episodes where the agent reported `succeeded` but the verifier fails a postcondition | §5 |
| Genuine failure rate | Episodes correctly reported `failed` | trace |
| Verifier disagreement (false-negative) rate | Agent reported `failed`, verifier confirms success | §5 |
| Unauthorised-action count | Actions observed outside the scenario's permitted set | harness action observer (§8.2) |
| Safety-violation count | Any destructive or out-of-scope action; any navigation away from the permitted target | harness action observer |
| Retry count | Total retries observed, from `action_attempted` events minus one per action | trace |
| Actions per episode | Total actions executed | trace |
| Latency | Wall-clock per episode: median, p95, min, max | harness |
| Terminal-status reproducibility | Fraction of episodes whose terminal status matches a re-execution of the same cell | §10.3 |
| Failure categories | Categorised per the WebArena-Lite taxonomy: unfinished exploration, premature response, invalid action, incomplete form workflow, timeout, other | trace + human review |
| Model calls / cost | `0` by construction (no model) — recorded as `null` with reason, not `0` | — |
| Human interventions | `0` by construction (no operator in the loop) | — |

### 8.2 How unauthorised actions are detected

The current action allowlist is **type-level only** (NFR-016 is half met),
so the agent cannot be trusted to police its own targets. The **harness**
therefore observes actions independently: it wraps the browser at the
Playwright boundary and records every navigation URL and every element
interaction, then compares that record against the scenario's declared
permitted set (`file://<demo_app>`; the "Project Name" input; the "Create
Project" button).

This is a benchmark-side control, not a product control. It does **not**
close the NFR-016 gap — that gap is in `chimera/safety.py` and is listed as
R-1 in the threat model.

### 8.3 Measurable only after future work

| Metric | Blocked on |
|---|---|
| Recovery success rate | A recovery implementation, plus a defined set of "designated recoverable failures" |
| Inconclusive rate | SRS §9's `INCONCLUSIVE` state (ADR-004 Q4) — today a verification timeout is reported as `failed`, so *inconclusive is not an observable category* |
| Generalisation success | More than one workflow and more than one target |
| Actions per successful task (comparative) | Baseline B |
| Model calls, token count, estimated cost | A model adapter |
| Human intervention frequency | A UI in which a human can intervene |
| Prompt-injection resistance | A model (there is no LLM surface today) and the `S-INJECT` scenario |

These are reported as `null` with the blocking reason. **Never** as `0`.

---

## 9. Result schema

`schema_version: 1`. One JSON file per run.

```json
{
  "schema_version": 1,
  "benchmark_id": "chimera-local",
  "benchmark_version": "1.0.0",
  "run_id": "<uuid4>",
  "started_at": "<UTC ISO-8601 ms>",
  "completed_at": "<UTC ISO-8601 ms>",
  "status": "proposed | measured",
  "agent_version": "milestone-1-foundation",
  "srs_mapping": "adr-004",
  "environment": {
    "python_version": "3.9.6",
    "playwright_version": "1.60.0",
    "browser": "chromium",
    "browser_build": "<chromium version string>",
    "platform": "darwin 27.2.0",
    "demo_app_sha256": "<hash>",
    "dev_manifest_sha256": "<hash>",
    "eval_manifest_sha256": "<hash>"
  },
  "config": {
    "trials_per_cell": 5,
    "warmup_episodes": 1,
    "policy": {
      "max_attempts": 2,
      "base_delay_seconds": 0.05,
      "max_delay_seconds": 0.2,
      "max_total_seconds": 5.0
    },
    "action_timeout_ms": 5000
  },
  "cells": [
    {
      "scenario_id": "S-SLOW",
      "split": "evaluation",
      "input_id": "I-PLAIN",
      "baseline": "chimera",
      "fault_params": {"slow": 1350},
      "trials": 5,
      "outcomes": {"succeeded": 5, "failed": 0, "cancelled": 0, "inconclusive": null},
      "independent_verification": {
        "P1_confirmation_visible": 5,
        "P2_exact_name_in_list": 5,
        "P3_no_unexpected_entries": 5
      },
      "false_successes": 0,
      "verifier_disagreements": 0,
      "unauthorized_actions": 0,
      "safety_violations": 0,
      "retries": {"total": 0, "mean_per_trial": 0.0},
      "actions": {"total": 15, "mean_per_trial": 3.0},
      "latency_ms": {"p50": null, "p95": null, "min": null, "max": null},
      "model_calls": null,
      "model_cost_usd": null,
      "human_interventions": null,
      "failure_categories": {},
      "trace_artifacts": ["data/traces/<run_id>.json", "..."],
      "verifier_audit": {"sampled": 0, "agreed": 0, "agreement_rate": null}
    }
  ],
  "totals": {
    "episodes": 0,
    "by_baseline": {},
    "false_success_rate": null,
    "unauthorized_actions": 0
  },
  "notes": ""
}
```

Rules:

- `inconclusive`, `model_calls`, `model_cost_usd`, `human_interventions`,
  and all latency percentiles are `null` when **not measurable** — never `0`
  and never omitted.
- `false_success_rate` is `null` if the denominator is 0.
- Every episode's trace artifact path is listed, so any number is auditable.
- `status` is `proposed` for this file's own design illustration and
  `measured` only for an actual run.

> **Implemented form.** The Stage 1 implementation (`benchmarks/results.py`)
> serialises a not-measurable metric as `{"value": null,
> "unavailable_reason": "<why>"}` rather than as a bare `null`, because a
> bare `null` cannot carry the reason that §8.3 requires. It also adds a
> per-episode `episodes` array, which the example above does not show.
> Both differences are recorded in §14 (AMB-8, AMB-2).

---

## 10. Statistical reporting rules

### 10.1 Every rate carries its denominator

SRS §11.2 requires targets to be "reported with sample sizes and scenario
definitions". A percentage without `n` is not a report.

### 10.2 A zero-failure rate is a bound, not a zero

SRS §11.2 sets a **0%** false-success target. Observing zero failures in a
finite sample does not establish a 0% rate. The **95% Wilson upper bound**
on the rate is reported alongside every zero count:

| Observed | 95% Wilson upper bound on the rate |
|---|---:|
| 0/5 | 43.4% |
| 0/10 | 27.8% |
| 0/20 | 16.1% |
| 0/50 | 7.1% |
| 0/100 | 3.7% |
| 0/200 | 1.9% |

**Consequence for the trial count.** With the default 5 trials per cell, a
single cell cannot support a "0% false-success" claim — the upper bound is
43.4%. To support the SRS gate with a bound below 5%, a run needs on the
order of **50+ episodes** on the false-success path. The default of 5 is
adequate for *estimating* a non-zero rate and for catching regressions, and
**inadequate** for demonstrating a zero rate. A report that asserts "0%
false success" on 5 trials is a reporting error, and the review checklist
must catch it.

**SRS §11.2's own target of "≥100 task episodes"** is therefore the
minimum meaningful run size, and it is well above what 5 trials × a few
cells produces.

### 10.3 Reproducibility is a separate claim

"Reproducible terminal status: 100% of completed test episodes" (SRS
§11.2) is measured by **re-executing** a declared subset of episodes and
comparing terminal statuses. It is reported as its own metric, not folded
into success.

### 10.4 Reliability under repetition

Where a reliability figure is wanted, the **pass^k** formulation (τ-bench,
`evaluation_approaches.md` §6) is used: the probability of succeeding on all
*k* consecutive trials. It is reported alongside, not instead of, the
per-episode success rate.

### 10.5 No cherry-picking

- Every cell in the manifest is reported, including cells that failed.
- Cells whose episodes errored in the **harness** (not the agent) are
  reported as harness errors, separately, and are not silently dropped.
- Any exclusion is declared in the report with its reason and count.
- The report states the manifest hashes, so a reader can tell which run
  produced which number.

---

## 11. Example report (illustrative — NOT a measured result)

> **The numbers below are fabricated for illustration.** No benchmark run has
> been performed. They show the *shape* of a report and the required
> captions, not any measured behaviour. Every value here is a placeholder.

*Implemented:* `benchmarks/report.py` (`render_report`) renders this
report shape from persisted run files — see `docs/user_guide.md`
§15.2. The numbers below remain illustrative; measured figures live
only in the rendered reports under `artifacts/`.

**Chimera local benchmark v1.0.0 — ILLUSTRATIVE FORMAT, NO DATA**
`run_id: <example>` · manifests: dev `<hash>`, eval `<hash>` ·
agent `milestone-1-foundation` · Playwright 1.60.0 · Chromium `<build>` ·
`demo_app_sha256: <hash>` · 5 trials/cell, 1 warm-up · 2026-10-24

| Scenario | Split | Baseline | n | Success | False success | Unauth. actions | Safety viol. | Retries/ep | Latency p50 | p95 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `S-NORM` / `I-PLAIN` | eval | Chimera | 5 | 5/5 (100%) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 118 ms | 141 ms |
| `S-NORM` / `I-PLAIN` | eval | A — replay | 5 | 5/5 (100%) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 96 ms | 110 ms |
| `S-SLOW` / `I-PLAIN` | eval | Chimera | 5 | 5/5 (100%) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 1 512 ms | 1 604 ms |
| `S-SLOW` / `I-PLAIN` | eval | A — replay | 5 | 0/5 (0%) | 0/5 | 0 | 0 | 0.0 | 104 ms | 112 ms |
| `S-DIS` / `I-PLAIN` | eval | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 1.0 | 5 006 ms | 5 214 ms |
| `S-DIS` / `I-PLAIN` | eval | A — replay | 5 | 0/5 (0%, expected) | 0/5 | 0 | 0 | 0.0 | 98 ms | 105 ms |
| `S-SLOWDIS` / `I-PLAIN` | eval | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 1.0 | 5 090 ms | 5 380 ms |
| `S-SLOWDIS` / `I-PLAIN` | eval | A — replay | 5 | 0/5 (0%, expected) | 0/5 | 0 | 0 | 0.0 | 99 ms | 108 ms |
| *Baseline B — model* | eval | B | — | `null` (not implemented) | `null` | `null` | `null` | `null` | `null` | `null` |

**Not measurable in this run** (reported as `null`, with reason):
recovery success `null` (no recovery implementation) · inconclusive rate
`null` (no `INCONCLUSIVE` state, ADR-004 Q4) · model calls `null` (no
model) · human interventions `null` (no operator in the loop) ·
prompt-injection resistance `null` (no model).

**Verifier audit:** `null` (no sample adjudicated). The false-success
figures above are therefore **provisional**, per §5.

**Interpretation this report would support:** the waiting-and-retry layer
accounts for the entire A-vs-C difference on `S-SLOW`; both approaches fail
correctly and boundedly on the persistent-disable scenarios. It does
**not** support any claim about recovery, model-driven execution,
generalisation, or general browser-agent reliability.

---

## 12. Threats to validity

### 12.1 Internal

- **The verifier is part of the measurement apparatus.** A verifier bug
  produces a wrong rate in either direction. Mitigated by the human audit
  (§5) and by the exact-match semantics of `P2`.
- **The fault taxonomy is two parameters wide.** A scenario that differs
  only in parameter value may not exercise a genuinely different failure
  mode. The `slow` band is documented so the class is stable, but this is a
  structural limit.
- **The agent's own postconditions are part of the system under test.**
  If the agent's `has_text` check and the verifier's exact check ever
  disagree, the disagreement is the finding — but it also means the false-
  success metric is sensitive to a difference in *check strictness* rather
  than only in *outcome*.
- **Non-determinism in the environment.** Chromium scheduling, the `slow`
  timer, and system load all perturb latency. This is why latency is
  reported as a distribution and why the trial count is ≥5.
- **Harness errors masquerade as agent failures.** Distinguished by the
  harness-error category, which is reported separately.

### 12.2 Construct validity

- "Success" here means "the demo app shows the project". It is not a
  proxy for real-world task completion, and the benchmark must not be used
  to estimate one.
- The postconditions check the *page*, which is exactly the right check for
  a deterministic target and exactly the wrong check for a task whose
  outcome is not visible in the DOM.

### 12.3 External validity — the dominant limitation

One workflow, one local target, two fault parameters, and an evaluation
split that varies **values** rather than **fault types**. Results do not
transfer to other websites, other workflows, other fault models, other
browsers, or to model-driven agents. The report must state this in its
summary, not only in an appendix.

### 12.4 Reporting validity

The dominant real-world risk in this field is the opposite of a false
success: **an evaluator that under-reports success**, which inflates the
apparent value of a method. The WebArena-Lite audit measured 5.45–8.49
percentage points of such false negatives. Chimera's protocol therefore
reports false negatives (verifier disagreement) separately and audits the
verifier. A benchmark that only reports false successes would reproduce
the very bias this design is meant to avoid.

---

## 13. What must exist before this benchmark can run

| # | Item | Kind | Notes |
|---|---|---|---|
| 1 | Scenario manifests (dev + eval), versioned and hashed | data | **Done (Stage 1).** `benchmarks/manifests/dev-v1.json` and `eval-v1.json`, with the schema, validation, and content hash in `benchmarks/manifest.py`. |
| 2 | Harness runner: manifest → episodes → results file | code | **Done (Stage 2).** `benchmarks/runner.py`, with the AMB-9 refusal, episode timeouts, warm-up accounting, trace-integrity checks, and result persistence. |
| 3 | Independent verifier component | code | **Done (Stage 3).** `benchmarks/verifier.py`: exact-match P1–P3 from a harness-observed snapshot, §5 classification; imports no `chimera.agent` verification code. |
| 4 | Harness-side action observer | code | **Done (Stage 4).** `benchmarks/observer.py`: Playwright-boundary recording judged against the §8.2 permitted set; benchmark-side only, NFR-016 gap unchanged. |
| 5 | Baseline A — deterministic replay driver | code | **Done.** `benchmarks/baseline_a.py` (harness-side only): fixed navigate/fill/click, 100 ms action timeout, single attempts, driver-report artifact, same verifier and observer. |
| 6 | Verifier audit procedure + human adjudication | process | **Done (procedure).** `benchmarks/audit.py`: seeded per-cell sampling, evidence bundles, verdict validation, strict agreement into `CellResult.verifier_audit`. Adjudicated so far: the dev full sample (100% agreement) and the 8-episode eval mini-review (8/8 agree, `artifacts/eval-20261028/mini-review/MINI_AUDIT_REPORT.md`). Full-run eval samples remain unadjudicated; the eval report stays provisional. |
| 7 | Report template | doc | **Done.** `benchmarks/report.py` renders persisted (optionally audited) run files into the §11 report following `docs/evaluation.md` §6: header, per-cell/per-baseline summary with Wilson bounds, not-measurable table, audit section with the provisional verdict, failure breakdown, exclusions, verbatim limitations/disclaimers, claim list, artifacts. Proven against fixture runs (`tests/test_benchmark_report.py`, 37 tests); dev and held-out eval reports rendered under `artifacts/`. |
| 8 | Model adapter + Baseline B | code | Blocked on the model phase |
| 9 | Demo-app variants for `S-MULTI`, `S-REDIRECT`, `S-AMBIG`, `S-DELAY`, `S-INJECT` | code | §3.2 |
| 10 | `INCONCLUSIVE` terminal state | code | Blocked on ADR-004 Q4 |

Items 1–7 are the minimum for a first, honest run.

---

## 14. Open ambiguities raised by the Stage 1 implementation

Stage 1 (the manifest and result contracts) surfaced questions this
document does not answer. They are recorded here rather than settled
silently in the code. Each needs an owner ruling before the first run —
except AMB-9, which has been ruled on (ADR-005) **and implemented** by
the Stage 2 runner.

**Runner behaviour in this section is implemented.** `benchmarks/runner.py`
exists alongside the manifest and result contracts
(`benchmarks/manifest.py`, `benchmarks/results.py`), and it enforces the
AMB-9 refusal (§14.1) and the timeout and warm-up rules in §§14.2–14.3.
The independent verifier, the action observer, and Baseline A remain
future work.

| # | Question | What Stage 1 did in the meantime |
|---|---|---|
| **AMB-1** | The SRS defines no manifest artifact. Is the manifest schema governed by SRS §8.3/§8.4, or is it a harness-local contract? (ADR-004 Q6 asks the same question of the *trace* schema and is still open.) | Treated the manifest as a harness-local contract with its own `schema_version`, versioned by content hash. No SRS identifier is claimed for it. |
| **AMB-2** | §9's result schema defines no **per-episode** record — only cell aggregates plus a list of trace paths. A trial-level record (trial ID, per-episode duration, per-episode evidence) is needed for a metric to be traceable to the episode that produced it. | Added an `episodes` array alongside §9's `cells`. This **extends** the documented schema and must be reconciled with §9 before a run. |
| **AMB-3** | §8.3 says `inconclusive` is not an observable category, yet a result schema that cannot express it would have to be re-modelled when ADR-004 Q4 is settled. | The schema expresses all four outcomes. `inconclusive` remains **unavailable with a reason** in every shipped manifest-driven cell; it is never reported as a measured rate. |
| **AMB-4** | §4 documents the `slow` band ([500, 4000] ms) and the reason for it, but does not say a validator must enforce it. | The band is a manifest field (`slow_band_ms`) and the validator rejects any scenario outside it, and rejects a band whose maximum is not below `action_timeout_ms`. This strengthens §4; it does not contradict it. |
| **AMB-5** | §4 says the evaluation manifest holds "a subset of input variations" but does not say which. | Held `I-SUBSTR` back to development. §2 establishes that the substring/exact-match **false-positive** direction is unreachable in the current single-task flow, so it adds cost without signal; the trim case `I-SPACE` is **kept** in evaluation because §2 shows it is reachable and it measures the false-negative direction that §5 calls the more common grader error. This choice changes what the evaluation measures and needs a ruling. |
| **AMB-6** | §3.1 states the expected outcome per **scenario**, but the trim input changes what the *agent* reports: the project is created (the task succeeded) while the agent's own substring check fails against the trimmed stored name (§2). | The manifest states the **task-level** expectation per scenario. The agent-level divergence is measured as a verifier disagreement (§5) and reported separately, never merged into success. A per-**cell** expected outcome would require a schema change. |
| **AMB-7** | Scenarios are identified by ID but are not individually versioned. Is the manifest hash sufficient versioning? | Treated the manifest hash as the versioning mechanism: changing any scenario's fault parameters changes the hash and invalidates a run (§4.1). Per-scenario versions would need a new field. |
| **AMB-8** | §9 writes a not-measurable metric as a bare `null`; §8.3 requires `null` **with the reason**. A bare `null` cannot carry a reason. | Serialised as `{"value": null, "unavailable_reason": "..."}`. A measured `0` is a measured `0`; a measured `null` is a null measurement; only a non-null reason marks a metric unavailable. |
| **AMB-9** | §7.6 requires a run to record the policy it executed under. The manifest's `config.policy` declares one, but nothing states whether it must equal `chimera.agent.DEFAULT_POLICY`. | **Ruled and implemented — see §14.1 below.** The runner **refuses** to execute a manifest whose declared policy diverges from the agent's effective policy. The decision is recorded in [ADR-005](adr/ADR-005-runner-refuses-on-policy-divergence.md) (Status: **Accepted**); the enforcement is `benchmarks/runner.py::check_policy_alignment`. |

### 14.1 AMB-9 — ruled: a policy divergence is a refusal, not a warning (implemented in Stage 2)

**Question.** §7.6 requires a run to record the policy it executed under.
The manifest declares one in `config.policy`; `chimera.agent` has exactly
one (`DEFAULT_POLICY`, and `ACTION_TIMEOUT_MS` derived from it). Must the
runner refuse to execute a manifest whose declared policy differs?

**Decision. Yes — the runner refuses, before any episode runs, with an
itemised reason naming every diverging field.**

> **Status of this control: implemented.** The Stage 2 runner enforces
> the rule below before the first episode, and `CURRENT_STATUS.md`
> records the verifying test run.

The enforcement point is
`benchmarks/runner.py::check_policy_alignment`, which compares the
manifest's `config.policy` and `config.action_timeout_ms` against the
agent's effective values and raises `PolicyMismatchError`. The decision
record is
[`adr/ADR-005-runner-refuses-on-policy-divergence.md`](adr/ADR-005-runner-refuses-on-policy-divergence.md).

**Rationale.**

1. **The agent cannot honour a different policy.** `chimera.agent.create_project`
   passes `DEFAULT_POLICY` at every call site and derives
   `ACTION_TIMEOUT_MS` from it; there is no injection seam. A manifest can
   therefore *describe* a policy but never *request* one.
2. **Recording a policy the run did not execute under would be a fabricated
   measurement.** If the runner ran a divergent manifest and copied the
   manifest's policy into the result file, the result would assert a policy
   that was never in force — the same class of error as reporting a
   missing metric as a zero.
3. **The manifest hash is the versioning mechanism** (§4.1, AMB-7). If the
   declared policy were ignored, the hash would no longer identify what
   was executed, and two runs with the same manifest hash could have run
   under different policies.
4. **The failure is cheap, loud, and reproducible.** It is detected before
   the first episode, costs no browser time, and names the diverging
   fields. A misconfigured manifest is a configuration error, and
   configuration errors are refused rather than measured.

**Alternatives considered and rejected.**

- *Run anyway and record the agent's effective policy.* Rejected: the
  manifest's `config.policy` would be silently ignored, so a manifest that
  misdeclares its policy would still "work" and the mistake would never
  surface.
- *Warn and continue.* Rejected: a warning that does not stop anything is
  not a control, and the result file would still carry a policy the run
  did not execute under.
- *Add a policy-injection seam to `chimera.agent` so the manifest's
  policy is honoured.* This is the way to lift the restriction, but it is a
  **product** change: it alters the agent's behaviour and therefore
  invalidates the 83-test baseline. It is out of scope for the harness
  and is not recorded as backlog item 4. Until it exists, the agent has
  one policy, and the harness holds the manifest to it.

**Consequence for the shipped manifests.** `dev-v1.json` and `eval-v1.json`
already declare exactly the agent's effective policy
(`max_attempts=2`, `base_delay_seconds=0.05`, `max_delay_seconds=0.2`,
`max_total_seconds=5.0`, `action_timeout_ms=5000`), so both run unchanged.
If the agent's policy ever changes, the shipped manifests must change in
the same commit or the runner will refuse them — which is the intended
behaviour, not an obstacle.

### 14.2 Timeouts (a runner detail §7 does not specify)

The manifest declares two timeouts: a per-scenario `timeout_seconds` and a
run-wide `config.episode_timeout_seconds`. The runner enforces the
**smaller** of the two as the episode's wall-clock budget. A request for
cancellation at the budget is made through the agent's existing
`CancellationToken` — the cooperative mechanism of ADR-002 — so an
overrunning episode stops at the next safe boundary and is recorded as
`cancelled` with the reason `timeout`. Because cancellation is
cooperative, an episode may overrun its budget by up to one action
timeout; the runner records the **actual** duration alongside the
requested budget, and the overrun is visible rather than hidden.

### 14.3 Warm-up accounting

§7.5 says the first episode of a run is a warm-up, excluded from the
reported statistics but retained in the artifacts. The runner executes it
as an episode **outside any cell** — so no cell is charged for browser
start-up — and records it in `episodes[]` with a `trial_id` prefixed
`warmup:`. It is excluded from every cell aggregate and from
`totals.episodes`. The run's `notes` state how many warm-up episodes were
executed.

---

## 15. Related documents

- [`evaluation.md`](evaluation.md) — evaluation criteria, baseline policy,
  reporting format, limitations.
- [`evaluation_approaches.md`](evaluation_approaches.md) — the survey this
  design borrows its methodology from.
- [`adr/ADR-004-requirement-traceability-to-srs.md`](adr/ADR-004-requirement-traceability-to-srs.md)
  — the unresolved mapping questions; Q3 and Q4 gate parts of this design.
- [`threat_model.md`](threat_model.md) §5 — R-1 (target allowlist), R-5
  (injection defence), R-9 (adversarial tests) are what §3.2 and §8.2
  partially address.
- [`architecture.md`](architecture.md) §5, §6 — the verification, trace and
  cancellation semantics the benchmark measures.
