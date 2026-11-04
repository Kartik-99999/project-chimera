# Errata — held-out evaluation `eval-20261028`

Added 2026-11-04. The files in this folder are **frozen evidence** and are
not edited: `report.md`, `run-chimera.json`, `run-baseline-a.json`, the audit
plans, traces and the mini-review packet stay byte-for-byte as they were
produced on 2026-10-28. This note corrects statements inside them that later
evidence showed to be wrong or out of date. Every figure below was recomputed
from the run files in this folder (warm-ups excluded).

## E1 — A stated prediction was falsified: the padded name did not cause a false failure

`docs/benchmark_design.md` (§2.2, "Why `P2` is exact-match", lines ~103–106)
predicted that the padded input `I-SPACE` (`"  Alpha  "`) would make the agent
report a **false negative**: the app stores the trimmed name, so the agent's
substring check for the untrimmed text should fail.

That did not happen. In every cell where success was possible the agent
succeeded on `I-SPACE` and the verifier agreed:

| Run | `I-SPACE` S-NORM | `I-SPACE` S-SLOW | Verifier disagreements |
|---|---|---|---|
| `eval-20261028-chimera` | 5/5 | 25/25 | 0 |
| `dev-20261028-chimera` | 5/5 | 5/5 | 0 |

The likely mechanism is that Playwright's `has_text` normalises whitespace
before matching, so the padded string matched the stored trimmed name. The
prediction was a design-time risk statement, not a measured result; it is
recorded here as **falsified**.

## E2 — Retries never fired

The reports and several docs attribute the Chimera-vs-replay difference to
"waiting + retry + verification". The retry layer contributed nothing in
these runs: the `retries` metric is **0 in all 180 measured Chimera episodes**
here (and in all 80 dev episodes — 260 in total). A single action's timeout
(5000 ms) already uses the whole time budget, and repeating a `fill` is
refused as a blind retry.

The S-SLOW gap (Chimera 75/75 vs replay 0/75) is explained by the per-action
**time budget** (5000 ms vs 100 ms), not by retries or a capability
difference: in the matched-budget experiment
(`experiments/matched-budget-v1/REPORT.md`) replay given the same 5000 ms
budget agreed with Chimera on **20/20** matched pairs, with 0 retries in
every arm.

## E3 — Stale lines in the frozen `report.md` "Limitations" section

`report.md` lines ~744–770 reproduce `docs/evaluation.md` §8 as it stood
before the run. Three statements there are wrong for this run:

| Report says | Correct for this run |
|---|---|
| "Roughly 10–30 episodes per run at the default trial count" | **180** measured episodes per run (36 cells × 5 trials), plus 1 warm-up |
| "Only Baseline A is specified; B is unavailable" | Baseline A is **implemented** (`benchmarks/baseline_a.py`) and is the second run in this folder. A model-driven Baseline B now exists (Muse Spark), but it was run on a separate manifest, `model-v1`, never on `eval-v1`. |
| "happy path ≈0.12 s" | Measured S-NORM median duration is **348 ms** (Chimera) and **336 ms** (replay) |

Likewise the "Disclaimers" line "Baseline A compares fixed-step replay
against Chimera's waiting, retry, and verification layers" should be read
with E2: at a matched budget the comparison isolates the time budget only.

## E4 — Stale `notes` field in the run files

`run-chimera.json` and `run-baseline-a.json` both carry
`notes: "… Baselines A/B are not implemented, so the metrics gated on them
are unavailable with reasons."` That string is runner boilerplate written
before Baseline A existed. Baseline A **was** implemented and run (it is
`run-baseline-a.json`). The metrics the note refers to are still reported as
`null` with a reason, which is correct for a single-driver run file.

## E5 — Other facts a reader should know

- **False-success denominator.** A false success requires a *claimed*
  success. Chimera claimed success in **90** of its 180 measured held-out
  episodes and the verifier refuted **0** of them (95% Wilson upper bound
  **4.1%**). Pooling all 520 episodes across both drivers and both splits
  (0/520, ≤0.7%) mixes populations the design says must not be pooled and
  counts episodes in which no success was claimed; do not quote it.
- **Failure categories were never set.** "Uncategorized agent failures: 255"
  (`report.md` §Failure breakdown) means the runner never assigns
  `failure_category`; it is not a finding about the failures.
- **Browser build not recorded.** Every run file says
  `browser_build: "unknown"`.
- **Audit provenance.** The 8-episode mini-audit (`mini-review/`) was
  adjudicated by the author. The answer key sits in the same folder as the
  blinded packet. The full held-out audit (`artifacts/audit-full-v1/`) is
  not complete, so held-out figures remain **provisional**.
