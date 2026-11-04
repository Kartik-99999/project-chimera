# Project Chimera — Submission Snapshot

**Muse Spark proposes. Chimera proves.** Meta's Muse Spark acts in a
real browser; Chimera's deterministic, model-free referee (independent
P1–P3 verifier + action observer) judges every episode.

- **Demo video (94 s, captioned):**
  [chimera-baseline-b.mp4](https://github.com/Kartik-99999/project-chimera/releases/download/v1.0-demo/chimera-baseline-b.mp4)
- **Baseline B headline:** 30 measured episodes, 20 model claims,
  18 verified, **2 false successes caught** (upper 95% bound 30.1%).
  Method and evidence:
  [`experiments/model-baseline-v1/REPORT.md`](experiments/model-baseline-v1/REPORT.md).

Deterministic drivers + independent benchmark harness. Dev runs
complete and audited; held-out eval runs complete with a
**PROVISIONAL** report (human audit deferred). Primary frozen
evidence:
[`artifacts/eval-20261028/report.md`](artifacts/eval-20261028/report.md).

## Architecture and safety boundaries

- One hard-coded workflow — create a project in the bundled local demo
  app (`demo_app/index.html`, `file://` only, in-memory state). No
  model, no randomness, no network calls.
- `chimera/agent.py`: Playwright execution with per-action timeouts;
  every run gets its own browser process and `BrowserContext`
  (ADR-001); cancellation is cooperative at safe boundaries
  (ADR-002); a run whose trace write fails is reported failed, never
  successful (ADR-003).
- `chimera/safety.py`: type-level action allowlist (navigate/fill/
  click/wait/observe) + bounded retry with refusal of blind retries.
  URL/locator/target allowlists are **not** implemented (NFR-016 half
  met); the harness-side action observer detects violations but is
  not a product safeguard.
- The benchmark harness (`benchmarks/`) is strictly separated from
  the product (`chimera/`): it never drives the agent except through
  the documented runner/executor seam, and the verifier shares no
  verification code with the agent.

## Benchmark methodology and Baseline A comparison

- Design: [`docs/benchmark_design.md`](docs/benchmark_design.md);
  criteria: [`docs/evaluation.md`](docs/evaluation.md). Four fault
  scenarios (S-NORM, S-SLOW, S-DIS, S-SLOWDIS) × input variations,
  5 trials/cell, 1 warm-up/run (excluded), deterministic order,
  per-episode isolation, AMB-9/ADR-005 policy-alignment refusal.
- Dev split (`dev-v1`): 16 cells. Held-out eval split (`eval-v1`,
  content hash `b23580c8…cf5`, verified pre-run, never edited):
  36 cells with unseen slow values (800–3900 ms) and I-SUBSTR held
  out. Dev/eval evidence never mixed.
- Independent verifier checks exact-match P1–P3 from harness-captured
  snapshots (never the agent's own verdicts); zero false-success
  counts carry 95% Wilson upper bounds. Baseline A is fixed
  navigate/fill/click replay (100 ms actions, no waiting/retry) run
  through the same cells — it isolates the value of Chimera's
  waiting, retry, and verification layers, nothing more.
- Audit: seeded per-cell human adjudication, strict per-check
  agreement, 95% provisional rule intact. An 8-episode stratified
  eval mini-sample (one median cell per scenario per baseline) is
  adjudicated 8/8 agree (`artifacts/eval-20261028/mini-review/
  MINI_AUDIT_REPORT.md`) — eight episodes only, supporting no
  general-reliability claim; full-sample review still deferred.

## Observed results and test status

- Dev (`dev-20261028-*`, 81 episodes × 2 baselines): Chimera
  S-NORM 20/20, S-SLOW 20/20, persistent faults bounded 0/40;
  Baseline A S-NORM 20/20 only. Audit: 100% agreement, 32/32 cells —
  `artifacts/dev-20261028/report-audited.md` verdict **AUDITED**.
- Eval (`eval-20261028-*`, 181 episodes × 2 baselines): Chimera
  S-NORM 15/15, S-SLOW 75/75, S-DIS 0/15 and S-SLOWDIS 0/75 bounded
  as expected; Baseline A S-NORM 15/15, all fault cells 0. Zero
  measured false successes, zero unauthorized actions, zero harness
  errors. Verdict **PROVISIONAL** (0 full-sample eval verdicts
  recorded; the separate 8-episode mini-audit does not change
  the verdict).
- Baseline B (`model-b`, 2026-11-04, 30 measured episodes + 1
  warm-up): S-NORM 10 claims / 8 verified / 2 false successes
  (both padded-input duplicates the model over-claimed); S-SLOW
  10/10/0; S-DIS 0 claims, honest failures. 116 model calls,
  181,910 tokens; 0 unauthorised, 0 safety violations.
- Regression: **847 Python tests pass** (plus 88 JavaScript tests;
  browser tests need Chromium). Full evidence (traces, snapshots,
  action logs, driver reports, plans, per-episode model sidecars)
  preserved under `artifacts/` and `experiments/model-baseline-v1/
  runs/`.

## Reproduction instructions

From the project root, with the provisioned `.venv` (Chromium via
`docs/user_guide.md` §4.2; run outside any sandbox that blocks
browser launch):

```bash
.venv/bin/python -m pytest tests/ -q                           # 847 tests
.venv/bin/python -c "                                         # re-render (read-only)
from benchmarks.report import render_report
print(render_report(['artifacts/eval-20261028/run-chimera.json',
                     'artifacts/eval-20261028/run-baseline-a.json'],
                    manifest_paths=['benchmarks/manifests/eval-v1.json']))"
.venv/bin/python tools/audit_review.py \                        # deferred human review (8 episodes)
  artifacts/eval-20261028/run-chimera.audit-plan-mini.json \
  artifacts/eval-20261028/run-baseline-a.audit-plan-mini.json
```

Runs were executed with the documented
`benchmarks.runner.run_manifest(manifest_path, output_path,
trace_dir=…, baseline=…, run_id=…)` — no CLI flags exist and none
were invented. Do not re-run eval to "improve" figures; do not edit
runs, evidence, or `eval-v1.json`.

## Limitations

- Human audit pending: the eval report is provisional; agreement,
  disagreement cases, and any rate claim await adjudication.
- One local workflow against one local target; two fault parameters;
  the eval split varies values, not fault types.
- Baseline B is n=30 on one task with one prompt: the false-success
  detector is shown to fire, but no general model failure rate is
  claimed (upper 95% bound 30.1%). No USD cost recorded (no pricing
  data); no adversarial/prompt-injection scenario exists.
- Latencies are same-machine only; absolute values carry start-up
  overhead (see report §Latency).
- No recovery layer, no target allowlist, no `INCONCLUSIVE` state,
  not production-ready (see `docs/threat_model.md`).
- **No generalization claim is made.** Nothing here transfers to
  other sites, workflows, fault models, browsers, or model-driven
  agents.

## Provenance note

The deterministic harness, drivers, and frozen October evidence
predate this event (developed mid-to-late October 2026). Built
2026-11-03/04 for this submission: the Muse Spark integration
(`chimera/llm.py`, `benchmarks/baseline_b.py`), the measured
Baseline B run (2026-11-04), the security fixes, the demo video,
and this submission package.
