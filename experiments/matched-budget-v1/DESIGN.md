# Matched-budget experiment v1 — design

## Question

Does Chimera outperform Baseline A when both receive an equivalent
execution budget? The October 28 evaluation confounds driver logic
with budget: Chimera waits up to 5000 ms per action while replay
acts on a fixed 100 ms timeout.

## Budget anatomy (measured from the implementations)

| System | Per-action budget | Attempts | Verification waits | Episode cap |
|--------|-------------------|----------|--------------------|-------------|
| Chimera (`chimera/agent.py`, `DEFAULT_POLICY`) | 5000 ms Playwright timeout per fill/click/verify | max 2, but fill carries no `is_effect_achieved`, so a failed first attempt raises `BlindRetryRefusedError` — **effectively 1 attempt** (confirmed: S-DIS traces show attempted→failed→run_failed, ~5.3 s) | 2 × 5000 ms confirmation/list waits on the success path | 60 s runner episode timeout |
| Baseline A (`benchmarks/baseline_a.py`) | `REPLAY_ACTION_TIMEOUT_MS` = 100 ms (now overridable, default unchanged) | exactly 1, no retry, no waits | none — outcome judged by the harness verifier from the snapshot | same 60 s runner cap |

**Matched quantity:** the per-action Playwright timeout. The 5000 ms
arm equalizes the wall-clock budget each driver may spend per step.
What still differs by design (the treatment): Chimera's
verification waits, attempt structure, screenshots, and trace
shape; replay's fixed single pass. Outcomes for both arms are
judged symmetrically by the independent harness verifier (P1–P3).

## Arms (one runner invocation each, identical manifest)

| Arm | Baseline | Per-action budget | Measured episodes |
|-----|----------|-------------------|-------------------|
| mb-v1-chimera | chimera | 5000 ms (fixed) | 4 cells × 5 = 20 |
| mb-v1-replay-100 | baseline-a | 100 ms (Oct-28 replication) | 20 |
| mb-v1-replay-1000 | baseline-a | 1000 ms | 20 |
| mb-v1-replay-2500 | baseline-a | 2500 ms | 20 |
| mb-v1-replay-5000 | baseline-a | 5000 ms (**matched**) | 20 |

Plus 1 warm-up per run (first cell only, excluded from all
figures). Total: 105 executions, 100 measured.

## Conditions

4 scenarios × I-PLAIN × one fault variant:
S-NORM (slow 0), S-SLOW (slow 2100), S-DIS (disabled),
S-SLOWDIS (slow 2100 + disabled). Manifest `mb-v1`
(`split: development` — experimental work, explicitly not
held-out evaluation; policy block copied from eval-v1 so the
AMB-9 alignment check passes unmodified).

## Pairing

Pair = same cell + same measured-trial index across arms
(deterministic runner order). Primary comparison: chimera vs
replay-5000 (20 pairs). Secondary: replay budget–response curve.

## Hypotheses

- **H1 (budget explains the gap):** at matched 5000 ms budgets,
  replay-5000 ≈ chimera on every scenario, including S-SLOW —
  i.e. the Oct-28 S-SLOW gap (75/75 vs 0/75) was a budget
  artifact, not a capability gap.
- **H2 (step response):** replay S-SLOW success is a step
  function of budget around slow_ms=2100 (100/1000 fail,
  2500/5000 succeed); S-SLOWDIS stays 0/5 at every budget
  (disabled input is unresolvable by waiting).

## Sample size

n=5 measured trials per cell mirrors the benchmark cell
convention and keeps runtime feasible (~120 browser episodes,
≈15–30 min). Analysis is descriptive: k/n rates with Wilson
intervals, paired agreement/disagreement counts, and an exact
McNemar test on pooled matched pairs (justified: paired binary
outcomes; reported with the caveat that pooling across
scenarios mixes heterogeneous conditions). No generality claims.

## Pilot

`manifest-mb-v1-pilot.json`: S-SLOW only, 2 trials + 1 warm-up
per arm (15 executions). Must show before main runs: runner
plumbing works in the new directory, the env override changes
replay behavior (100 fails / 5000 succeeds on S-SLOW), no
harness errors, timing within estimate.

## Assumptions and confounds (see REPORT.md for full treatment)

1. Same-machine, headless Chromium, wall-clock timing —
   latencies comparable only within this experiment.
2. Single input (I-PLAIN): no input-variation coverage.
3. One slow value (2100 ms): the step location is probed, not
   mapped.
4. No human audit of these runs: outcomes rest on the
   machine verifier (P1–P3), whose Oct-28 agreement was
   dev 64/64 and mini-audit 8/8.
5. Chimera's two 5000 ms verification waits exist only on its
   success path; replay has no equivalent — residual,
   documented budget asymmetry on successes.
6. Trial order is fixed, not randomized; the single warm-up
   runs on the first cell (S-NORM) only, so later cells carry
   any order effects unmitigated.
