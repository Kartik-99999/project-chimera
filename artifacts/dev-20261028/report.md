# chimera-local v1.0.0 — benchmark report

agent `milestone-1-foundation` · Playwright 1.60.0 · chromium `unknown` · Python 3.9.6 · macOS-27.2-arm64-arm-64bit
demo_app_sha256: `b20340c34d3b0c91ebbcf8ee723ab625f435f6f7fc7a6fbd495bd7771184dd47`
manifests: dev `54dc5bb6b5f4f9f810c37330b4ff69b604d0d491d23439563d6c7d34d31d9e28`, eval `b23580c8c07c3528a33f10f25780138cd58455a1f334c48e4fd889125c038cf5`

## Runs

| Run | Baseline | Manifest | Trials/cell | Warm-ups | Started | Completed |
|---|---|---|---|---|---|---|
| `dev-20261028-baseline-a` | baseline-a | `dev-v1` (`54dc5bb6b5f4…`) | 5 | 1 | 2026-10-28T11:30:05.870Z | 2026-10-28T11:30:35.308Z |
| `dev-20261028-chimera` | chimera | `dev-v1` (`54dc5bb6b5f4…`) | 5 | 1 | 2026-10-28T11:25:24.114Z | 2026-10-28T11:29:56.156Z |

---

## Summary by cell

| Scenario / input | Split | Baseline | n | Success | False success | Unauth. actions | Safety viol. | Retries/ep | Latency p50 | p95 | Harness errors |
|---|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| `S-DIS` / `I-PLAIN` | development | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 369 ms | 381 ms | 0 |
| `S-DIS` / `I-SPACE` | development | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 372 ms | 381 ms | 0 |
| `S-DIS` / `I-SUBSTR` | development | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 371 ms | 422 ms | 0 |
| `S-DIS` / `I-UNICODE` | development | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 368 ms | 380 ms | 0 |
| `S-NORM` / `I-PLAIN` | development | A — replay | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 315 ms | 352 ms | 0 |
| `S-NORM` / `I-SPACE` | development | A — replay | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 320 ms | 336 ms | 0 |
| `S-NORM` / `I-SUBSTR` | development | A — replay | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 319 ms | 335 ms | 0 |
| `S-NORM` / `I-UNICODE` | development | A — replay | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 319 ms | 324 ms | 0 |
| `S-SLOW` / `I-PLAIN` | development | A — replay | 5 | 0/5 (0%) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 375 ms | 387 ms | 0 |
| `S-SLOW` / `I-SPACE` | development | A — replay | 5 | 0/5 (0%) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 368 ms | 371 ms | 0 |
| `S-SLOW` / `I-SUBSTR` | development | A — replay | 5 | 0/5 (0%) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 372 ms | 396 ms | 0 |
| `S-SLOW` / `I-UNICODE` | development | A — replay | 5 | 0/5 (0%) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 375 ms | 379 ms | 0 |
| `S-SLOWDIS` / `I-PLAIN` | development | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 367 ms | 379 ms | 0 |
| `S-SLOWDIS` / `I-SPACE` | development | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 378 ms | 417 ms | 0 |
| `S-SLOWDIS` / `I-SUBSTR` | development | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 382 ms | 385 ms | 0 |
| `S-SLOWDIS` / `I-UNICODE` | development | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 379 ms | 393 ms | 0 |
| `S-DIS` / `I-PLAIN` | development | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5331 ms | 5336 ms | 0 |
| `S-DIS` / `I-SPACE` | development | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5316 ms | 5336 ms | 0 |
| `S-DIS` / `I-SUBSTR` | development | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5325 ms | 5333 ms | 0 |
| `S-DIS` / `I-UNICODE` | development | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5314 ms | 5333 ms | 0 |
| `S-NORM` / `I-PLAIN` | development | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 319 ms | 349 ms | 0 |
| `S-NORM` / `I-SPACE` | development | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 316 ms | 325 ms | 0 |
| `S-NORM` / `I-SUBSTR` | development | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 318 ms | 332 ms | 0 |
| `S-NORM` / `I-UNICODE` | development | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 331 ms | 334 ms | 0 |
| `S-SLOW` / `I-PLAIN` | development | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 2601 ms | 2618 ms | 0 |
| `S-SLOW` / `I-SPACE` | development | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 2589 ms | 2619 ms | 0 |
| `S-SLOW` / `I-SUBSTR` | development | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 2590 ms | 2593 ms | 0 |
| `S-SLOW` / `I-UNICODE` | development | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 2592 ms | 2609 ms | 0 |
| `S-SLOWDIS` / `I-PLAIN` | development | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5316 ms | 5332 ms | 0 |
| `S-SLOWDIS` / `I-SPACE` | development | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5340 ms | 5349 ms | 0 |
| `S-SLOWDIS` / `I-SUBSTR` | development | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5300 ms | 5316 ms | 0 |
| `S-SLOWDIS` / `I-UNICODE` | development | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5317 ms | 5335 ms | 0 |
| *Baseline B — model* | development | B | — | `null` (not implemented) | `null` | `null` | `null` | `null` | `null` | `null` | — |

---

## Not measurable in this report

Every `null` with its blocking reason:

| Scope | Where | Metric | Reason |
|---|---|---|---|
| cell | `S-DIS`/`I-PLAIN`/baseline-a@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-DIS`/`I-PLAIN`/baseline-a@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-PLAIN`/baseline-a@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-PLAIN`/baseline-a@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-DIS`/`I-PLAIN`/chimera@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-DIS`/`I-PLAIN`/chimera@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-PLAIN`/chimera@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-PLAIN`/chimera@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-DIS`/`I-SPACE`/baseline-a@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-DIS`/`I-SPACE`/baseline-a@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-SPACE`/baseline-a@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-SPACE`/baseline-a@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-DIS`/`I-SPACE`/chimera@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-DIS`/`I-SPACE`/chimera@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-SPACE`/chimera@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-SPACE`/chimera@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-DIS`/`I-SUBSTR`/baseline-a@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-DIS`/`I-SUBSTR`/baseline-a@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-SUBSTR`/baseline-a@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-SUBSTR`/baseline-a@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-DIS`/`I-SUBSTR`/chimera@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-DIS`/`I-SUBSTR`/chimera@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-SUBSTR`/chimera@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-SUBSTR`/chimera@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-DIS`/`I-UNICODE`/baseline-a@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-DIS`/`I-UNICODE`/baseline-a@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-UNICODE`/baseline-a@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-UNICODE`/baseline-a@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-DIS`/`I-UNICODE`/chimera@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-DIS`/`I-UNICODE`/chimera@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-UNICODE`/chimera@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-UNICODE`/chimera@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-NORM`/`I-PLAIN`/baseline-a@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-NORM`/`I-PLAIN`/baseline-a@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-PLAIN`/baseline-a@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-PLAIN`/baseline-a@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-NORM`/`I-PLAIN`/chimera@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-NORM`/`I-PLAIN`/chimera@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-PLAIN`/chimera@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-PLAIN`/chimera@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-NORM`/`I-SPACE`/baseline-a@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-NORM`/`I-SPACE`/baseline-a@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-SPACE`/baseline-a@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-SPACE`/baseline-a@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-NORM`/`I-SPACE`/chimera@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-NORM`/`I-SPACE`/chimera@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-SPACE`/chimera@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-SPACE`/chimera@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-NORM`/`I-SUBSTR`/baseline-a@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-NORM`/`I-SUBSTR`/baseline-a@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-SUBSTR`/baseline-a@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-SUBSTR`/baseline-a@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-NORM`/`I-SUBSTR`/chimera@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-NORM`/`I-SUBSTR`/chimera@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-SUBSTR`/chimera@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-SUBSTR`/chimera@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-NORM`/`I-UNICODE`/baseline-a@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-NORM`/`I-UNICODE`/baseline-a@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-UNICODE`/baseline-a@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-UNICODE`/baseline-a@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-NORM`/`I-UNICODE`/chimera@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-NORM`/`I-UNICODE`/chimera@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-UNICODE`/chimera@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-UNICODE`/chimera@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-PLAIN`/baseline-a@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-PLAIN`/baseline-a@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-PLAIN`/baseline-a@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-PLAIN`/baseline-a@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-PLAIN`/chimera@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-PLAIN`/chimera@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-PLAIN`/chimera@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-PLAIN`/chimera@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-SPACE`/baseline-a@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-SPACE`/baseline-a@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SPACE`/baseline-a@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SPACE`/baseline-a@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-SPACE`/chimera@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-SPACE`/chimera@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SPACE`/chimera@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SPACE`/chimera@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-SUBSTR`/baseline-a@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-SUBSTR`/baseline-a@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SUBSTR`/baseline-a@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SUBSTR`/baseline-a@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-SUBSTR`/chimera@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-SUBSTR`/chimera@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SUBSTR`/chimera@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SUBSTR`/chimera@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-UNICODE`/baseline-a@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-UNICODE`/baseline-a@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-UNICODE`/baseline-a@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-UNICODE`/baseline-a@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-UNICODE`/chimera@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-UNICODE`/chimera@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-UNICODE`/chimera@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-UNICODE`/chimera@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-PLAIN`/baseline-a@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-PLAIN`/baseline-a@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-PLAIN`/baseline-a@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-PLAIN`/baseline-a@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-PLAIN`/chimera@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-PLAIN`/chimera@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-PLAIN`/chimera@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-PLAIN`/chimera@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-SPACE`/baseline-a@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-SPACE`/baseline-a@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SPACE`/baseline-a@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SPACE`/baseline-a@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-SPACE`/chimera@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-SPACE`/chimera@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SPACE`/chimera@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SPACE`/chimera@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-SUBSTR`/baseline-a@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-SUBSTR`/baseline-a@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SUBSTR`/baseline-a@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SUBSTR`/baseline-a@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-SUBSTR`/chimera@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-SUBSTR`/chimera@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SUBSTR`/chimera@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SUBSTR`/chimera@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-UNICODE`/baseline-a@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-UNICODE`/baseline-a@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-UNICODE`/baseline-a@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-UNICODE`/baseline-a@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-UNICODE`/chimera@dev-2026 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-UNICODE`/chimera@dev-2026 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-UNICODE`/chimera@dev-2026 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-UNICODE`/chimera@dev-2026 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| run | totals@dev-2026 | `false_success_rate` | rate reporting with confidence bounds is a report-stage concern; per-cell false-success counts are measured |
| run | totals@dev-2026 | `false_success_rate` | rate reporting with confidence bounds is a report-stage concern; per-cell false-success counts are measured |

---

## Verifier audit

- `S-NORM`/`I-PLAIN`/baseline-a@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-NORM`/`I-SUBSTR`/baseline-a@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-NORM`/`I-SPACE`/baseline-a@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-NORM`/`I-UNICODE`/baseline-a@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-PLAIN`/baseline-a@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-SUBSTR`/baseline-a@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-SPACE`/baseline-a@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-UNICODE`/baseline-a@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-DIS`/`I-PLAIN`/baseline-a@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-DIS`/`I-SUBSTR`/baseline-a@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-DIS`/`I-SPACE`/baseline-a@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-DIS`/`I-UNICODE`/baseline-a@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-PLAIN`/baseline-a@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-SUBSTR`/baseline-a@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-SPACE`/baseline-a@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-UNICODE`/baseline-a@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-NORM`/`I-PLAIN`/chimera@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-NORM`/`I-SUBSTR`/chimera@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-NORM`/`I-SPACE`/chimera@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-NORM`/`I-UNICODE`/chimera@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-PLAIN`/chimera@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-SUBSTR`/chimera@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-SPACE`/chimera@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-UNICODE`/chimera@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-DIS`/`I-PLAIN`/chimera@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-DIS`/`I-SUBSTR`/chimera@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-DIS`/`I-SPACE`/chimera@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-DIS`/`I-UNICODE`/chimera@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-PLAIN`/chimera@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-SUBSTR`/chimera@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-SPACE`/chimera@dev-2026: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-UNICODE`/chimera@dev-2026: `null` (no sample adjudicated) — figures provisional.

**Verdict: PROVISIONAL** — at least one cell is unaudited or below 95% agreement.

---

## Failure breakdown

Uncategorized agent failures (`failure_category` null): 100
- `trial-0021` → artifacts/dev-20261028/traces-baseline-a/69bdd3fc-0832-44df-908e-5df227cc4a7d.replay.json
- `trial-0022` → artifacts/dev-20261028/traces-baseline-a/aa178969-0cec-479f-93c9-e842e8ccb948.replay.json
- `trial-0023` → artifacts/dev-20261028/traces-baseline-a/466101a4-1ca8-40db-9b95-8f4128e11372.replay.json
- `trial-0024` → artifacts/dev-20261028/traces-baseline-a/0cf39b37-c73e-4bfb-b14e-f818e23b20e7.replay.json
- `trial-0025` → artifacts/dev-20261028/traces-baseline-a/a8324fe4-c39e-4bfb-b554-b72ca9a6617e.replay.json
- `trial-0026` → artifacts/dev-20261028/traces-baseline-a/abfd4938-d4ec-455b-81ea-e584ea3cef65.replay.json
- `trial-0027` → artifacts/dev-20261028/traces-baseline-a/f0366c13-faae-4bb8-a247-39761cb62244.replay.json
- `trial-0028` → artifacts/dev-20261028/traces-baseline-a/e3c55514-944e-42e9-b2c8-fc6bf6730774.replay.json
- `trial-0029` → artifacts/dev-20261028/traces-baseline-a/78166440-80d7-4f19-b135-7c4e567d447d.replay.json
- `trial-0030` → artifacts/dev-20261028/traces-baseline-a/cd36f444-49a4-430b-a1fb-6f3958304d54.replay.json
- `trial-0031` → artifacts/dev-20261028/traces-baseline-a/ae841e2b-cf81-4f61-b7fc-d36b956bf075.replay.json
- `trial-0032` → artifacts/dev-20261028/traces-baseline-a/75214bdd-47a3-451c-9587-b0605f833206.replay.json
- `trial-0033` → artifacts/dev-20261028/traces-baseline-a/b0bdfed7-6536-4e58-93bb-89ca2153cc92.replay.json
- `trial-0034` → artifacts/dev-20261028/traces-baseline-a/13f4b02d-85e2-4de4-88c1-628d8780176c.replay.json
- `trial-0035` → artifacts/dev-20261028/traces-baseline-a/08d8a8c7-242f-4204-b8ec-8b22190bc598.replay.json
- `trial-0036` → artifacts/dev-20261028/traces-baseline-a/705ac57f-9d91-479a-8803-ea074112aad9.replay.json
- `trial-0037` → artifacts/dev-20261028/traces-baseline-a/60922677-979d-42ae-85d3-24a7b58b633d.replay.json
- `trial-0038` → artifacts/dev-20261028/traces-baseline-a/1fe0d612-a05b-4ed1-ad91-57aeef24291d.replay.json
- `trial-0039` → artifacts/dev-20261028/traces-baseline-a/0cbbe1e7-3955-4d59-8ef9-58bebcc26de5.replay.json
- `trial-0040` → artifacts/dev-20261028/traces-baseline-a/91abc8a8-d0e6-46f6-9d68-cb28a62353a7.replay.json
- `trial-0041` → artifacts/dev-20261028/traces-baseline-a/930b5bdf-2f7e-416e-99f2-771e24fa6f26.replay.json
- `trial-0041` → artifacts/dev-20261028/traces-chimera/ac52f51e-ac97-4297-92ac-0ddcdeeb6e28.json
- `trial-0042` → artifacts/dev-20261028/traces-baseline-a/e2392368-1d3c-4975-b75d-350b6b66f64b.replay.json
- `trial-0042` → artifacts/dev-20261028/traces-chimera/db241ba3-9cbf-4fc2-bf61-deeedf1133f2.json
- `trial-0043` → artifacts/dev-20261028/traces-baseline-a/da32f4bb-b319-4189-baca-0f66c27f8336.replay.json
- `trial-0043` → artifacts/dev-20261028/traces-chimera/5bfd74a4-7bbc-425b-bbec-fd541df833ef.json
- `trial-0044` → artifacts/dev-20261028/traces-baseline-a/4a06c777-aa73-41ac-9ccf-587434a740d1.replay.json
- `trial-0044` → artifacts/dev-20261028/traces-chimera/d18ed98f-7266-4c8d-b5be-8901b75d63c4.json
- `trial-0045` → artifacts/dev-20261028/traces-baseline-a/245fc5d8-a321-4bfd-a1f9-1df4a64575b2.replay.json
- `trial-0045` → artifacts/dev-20261028/traces-chimera/6419c0a3-39b5-49e4-888a-319706d4d87e.json
- `trial-0046` → artifacts/dev-20261028/traces-baseline-a/fd3649b6-0dd9-48a9-a406-4fb30785fc73.replay.json
- `trial-0046` → artifacts/dev-20261028/traces-chimera/bd29563e-2031-4af2-8c7d-48608363fdd3.json
- `trial-0047` → artifacts/dev-20261028/traces-baseline-a/88b6b6e9-ec68-4ea8-a14c-7d01df8421af.replay.json
- `trial-0047` → artifacts/dev-20261028/traces-chimera/4cc97bcf-8436-4fd1-a87f-ae42559d9b86.json
- `trial-0048` → artifacts/dev-20261028/traces-baseline-a/b1980e94-2cdc-4ee0-ac32-66cd8dba06da.replay.json
- `trial-0048` → artifacts/dev-20261028/traces-chimera/acb81584-b69b-4e09-ba25-5b1dc1eb8bc6.json
- `trial-0049` → artifacts/dev-20261028/traces-baseline-a/f2076d3b-e274-4de6-a0ed-415e6bc47628.replay.json
- `trial-0049` → artifacts/dev-20261028/traces-chimera/14d52fff-afd1-4e8e-a77d-b6e9c913c090.json
- `trial-0050` → artifacts/dev-20261028/traces-baseline-a/5a7e8d7d-f098-4763-99df-1698e4c40f25.replay.json
- `trial-0050` → artifacts/dev-20261028/traces-chimera/e853f3c1-5378-44b0-973b-575b2e2f7d63.json
- `trial-0051` → artifacts/dev-20261028/traces-baseline-a/5cbb863c-1529-4625-855e-251d77b5ac34.replay.json
- `trial-0051` → artifacts/dev-20261028/traces-chimera/f030e8b7-10f6-412e-af80-2d6151a72824.json
- `trial-0052` → artifacts/dev-20261028/traces-baseline-a/fea359be-6ecd-4686-b6ce-c7b13f36c54e.replay.json
- `trial-0052` → artifacts/dev-20261028/traces-chimera/1c0536af-2458-4751-91e6-e4c187e3d46b.json
- `trial-0053` → artifacts/dev-20261028/traces-baseline-a/98f01300-9756-4176-8671-eb4610f5789b.replay.json
- `trial-0053` → artifacts/dev-20261028/traces-chimera/76bf6fb3-8870-4eba-970f-5a8bb7a2d084.json
- `trial-0054` → artifacts/dev-20261028/traces-baseline-a/e074c157-d099-4e57-9168-25a89fa312f7.replay.json
- `trial-0054` → artifacts/dev-20261028/traces-chimera/242c11a4-787e-4e5a-9b7b-f9748d69024d.json
- `trial-0055` → artifacts/dev-20261028/traces-baseline-a/37b7f2e7-1a02-4c50-bb2f-e093b17b4fbb.replay.json
- `trial-0055` → artifacts/dev-20261028/traces-chimera/8248b358-ebc4-4c9e-8f7d-db4be546c069.json
- `trial-0056` → artifacts/dev-20261028/traces-baseline-a/8e63be6f-2555-4faf-89f6-14a3dcfb2ac4.replay.json
- `trial-0056` → artifacts/dev-20261028/traces-chimera/ddcb9367-5968-4479-b2c0-061d0fb215e2.json
- `trial-0057` → artifacts/dev-20261028/traces-baseline-a/fd816c57-062a-48c5-b905-999e6f448c74.replay.json
- `trial-0057` → artifacts/dev-20261028/traces-chimera/8eec1c3e-c33d-4f50-b588-b694c354c71b.json
- `trial-0058` → artifacts/dev-20261028/traces-baseline-a/087f8f38-b4ab-4cae-b48c-b1da3c20528b.replay.json
- `trial-0058` → artifacts/dev-20261028/traces-chimera/e6070603-36b1-4f40-a6ea-51a008188d51.json
- `trial-0059` → artifacts/dev-20261028/traces-baseline-a/840721cb-1b0e-45f8-9a82-5f114f348e41.replay.json
- `trial-0059` → artifacts/dev-20261028/traces-chimera/bd73ecdf-be88-4539-ae94-2db614853ed3.json
- `trial-0060` → artifacts/dev-20261028/traces-baseline-a/baf36d76-5c11-4bdc-956f-c880990a54af.replay.json
- `trial-0060` → artifacts/dev-20261028/traces-chimera/77f4b505-41b1-4498-8176-13007d44d606.json
- `trial-0061` → artifacts/dev-20261028/traces-baseline-a/de07318a-f835-46f3-bab1-01f3064362f6.replay.json
- `trial-0061` → artifacts/dev-20261028/traces-chimera/1aa0d3e6-cebd-40df-baca-f797e7fdecf1.json
- `trial-0062` → artifacts/dev-20261028/traces-baseline-a/5c28ad5f-355b-41af-b9c2-a21fc47c7323.replay.json
- `trial-0062` → artifacts/dev-20261028/traces-chimera/463a1bf0-26e9-41cb-9a35-0333b8a99f4b.json
- `trial-0063` → artifacts/dev-20261028/traces-baseline-a/c9e84360-a3db-440e-8d25-22bb4b5b3877.replay.json
- `trial-0063` → artifacts/dev-20261028/traces-chimera/15f4df46-927e-4ded-9017-9c736f64ca91.json
- `trial-0064` → artifacts/dev-20261028/traces-baseline-a/5974da10-8bd9-46bf-a4cf-72af1bafd317.replay.json
- `trial-0064` → artifacts/dev-20261028/traces-chimera/a44ff827-5b24-4aeb-900c-c7c0761b3578.json
- `trial-0065` → artifacts/dev-20261028/traces-baseline-a/ab80be72-94c3-4cf6-942b-7a7b88249aca.replay.json
- `trial-0065` → artifacts/dev-20261028/traces-chimera/4366345c-5d2c-4c81-a155-2156ab10363f.json
- `trial-0066` → artifacts/dev-20261028/traces-baseline-a/eb5d74f2-2315-45bc-a535-6f123a3ec944.replay.json
- `trial-0066` → artifacts/dev-20261028/traces-chimera/4e57d5ad-4309-4c4f-9fc5-a6f714710c4b.json
- `trial-0067` → artifacts/dev-20261028/traces-baseline-a/44e0ce0e-cb3d-4395-93e4-d71dca8c8169.replay.json
- `trial-0067` → artifacts/dev-20261028/traces-chimera/bd974f69-d63d-44ee-9a31-f33dc6f66559.json
- `trial-0068` → artifacts/dev-20261028/traces-baseline-a/d0ed2048-61f0-4130-b1e4-ff35852d5a5e.replay.json
- `trial-0068` → artifacts/dev-20261028/traces-chimera/3755ada1-2631-4e9e-98b7-587d3e413b53.json
- `trial-0069` → artifacts/dev-20261028/traces-baseline-a/418f1e67-56b6-4a4d-8da9-42cca7d8e7c2.replay.json
- `trial-0069` → artifacts/dev-20261028/traces-chimera/a0e238c1-38a5-4e4e-82ba-432fba3a57df.json
- `trial-0070` → artifacts/dev-20261028/traces-baseline-a/d4258fbd-b0f1-498c-86e2-a6e92fbd6eb5.replay.json
- `trial-0070` → artifacts/dev-20261028/traces-chimera/b3598566-6e84-464c-b9b8-a102123dc723.json
- `trial-0071` → artifacts/dev-20261028/traces-baseline-a/2539d770-e5fd-466d-9dc8-43e0c6eb8a25.replay.json
- `trial-0071` → artifacts/dev-20261028/traces-chimera/d586b947-ab3d-4814-8443-f5fcf58ee2a0.json
- `trial-0072` → artifacts/dev-20261028/traces-baseline-a/9985c09e-2e4e-48a3-a2d3-04865807a4b4.replay.json
- `trial-0072` → artifacts/dev-20261028/traces-chimera/4275f9b5-dbd9-4c4f-9596-7732aadc95a3.json
- `trial-0073` → artifacts/dev-20261028/traces-baseline-a/def537f9-30ad-46ba-94ab-f03d06ff713b.replay.json
- `trial-0073` → artifacts/dev-20261028/traces-chimera/a44a0b90-4f5d-460c-b7b9-85a9c27809e7.json
- `trial-0074` → artifacts/dev-20261028/traces-baseline-a/594daf9f-da8b-4fe5-a451-cb87ffa57504.replay.json
- `trial-0074` → artifacts/dev-20261028/traces-chimera/ac739be8-e426-4bc9-a966-dd7698fb71fd.json
- `trial-0075` → artifacts/dev-20261028/traces-baseline-a/60eb7e61-5659-4f8f-8423-42ea524294fd.replay.json
- `trial-0075` → artifacts/dev-20261028/traces-chimera/2e7d1ee1-a736-46e7-96e5-8ac4a5c7bdb0.json
- `trial-0076` → artifacts/dev-20261028/traces-baseline-a/2b3e7586-e2ab-4c2e-9c18-fb3ae7c7e4a4.replay.json
- `trial-0076` → artifacts/dev-20261028/traces-chimera/89d20f45-9911-4106-8645-247b5d3adf4f.json
- `trial-0077` → artifacts/dev-20261028/traces-baseline-a/6adacd32-4591-4bee-be4a-37a8b88095c3.replay.json
- `trial-0077` → artifacts/dev-20261028/traces-chimera/419c71c0-f524-456f-8e07-4f8610997f07.json
- `trial-0078` → artifacts/dev-20261028/traces-baseline-a/df1b6e09-6339-4798-a5ec-2d99478bbf2c.replay.json
- `trial-0078` → artifacts/dev-20261028/traces-chimera/25009c55-e6c3-40da-9978-7d976db776a9.json
- `trial-0079` → artifacts/dev-20261028/traces-baseline-a/96029e0a-eafd-4926-b22a-e1912f7efb29.replay.json
- `trial-0079` → artifacts/dev-20261028/traces-chimera/82fffc25-83a3-43f2-8647-1f2b217b957c.json
- `trial-0080` → artifacts/dev-20261028/traces-baseline-a/9192150c-9eab-4eb4-89a2-fed3714c4afb.replay.json
- `trial-0080` → artifacts/dev-20261028/traces-chimera/ec0528ba-9fcc-409b-b2e3-cc2c67b7b97d.json


---

## Exclusions

- Run `dev-20261028-baseline-a`: 1 warm-up episode(s) excluded from every aggregate (outside any cell, design §14.3).
- Run `dev-20261028-chimera`: 1 warm-up episode(s) excluded from every aggregate (outside any cell, design §14.3).


---

## Limitations

(Evaluation.md §6.1 cites “§7 of this document”; the limitations paragraph lives in §8 at this revision and is reproduced verbatim below.)

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

## Claim list

What this report supports:

- Success counts with denominators for 32 reported cell(s), as listed above.
- False-success counts with denominators and Wilson bounds for: `S-DIS`/`I-PLAIN`/baseline-a, `S-DIS`/`I-PLAIN`/chimera, `S-DIS`/`I-SPACE`/baseline-a, `S-DIS`/`I-SPACE`/chimera, `S-DIS`/`I-SUBSTR`/baseline-a, `S-DIS`/`I-SUBSTR`/chimera, `S-DIS`/`I-UNICODE`/baseline-a, `S-DIS`/`I-UNICODE`/chimera, `S-NORM`/`I-PLAIN`/baseline-a, `S-NORM`/`I-PLAIN`/chimera, `S-NORM`/`I-SPACE`/baseline-a, `S-NORM`/`I-SPACE`/chimera, `S-NORM`/`I-SUBSTR`/baseline-a, `S-NORM`/`I-SUBSTR`/chimera, `S-NORM`/`I-UNICODE`/baseline-a, `S-NORM`/`I-UNICODE`/chimera, `S-SLOWDIS`/`I-PLAIN`/baseline-a, `S-SLOWDIS`/`I-PLAIN`/chimera, `S-SLOWDIS`/`I-SPACE`/baseline-a, `S-SLOWDIS`/`I-SPACE`/chimera, `S-SLOWDIS`/`I-SUBSTR`/baseline-a, `S-SLOWDIS`/`I-SUBSTR`/chimera, `S-SLOWDIS`/`I-UNICODE`/baseline-a, `S-SLOWDIS`/`I-UNICODE`/chimera, `S-SLOW`/`I-PLAIN`/baseline-a, `S-SLOW`/`I-PLAIN`/chimera, `S-SLOW`/`I-SPACE`/baseline-a, `S-SLOW`/`I-SPACE`/chimera, `S-SLOW`/`I-SUBSTR`/baseline-a, `S-SLOW`/`I-SUBSTR`/chimera, `S-SLOW`/`I-UNICODE`/baseline-a, `S-SLOW`/`I-UNICODE`/chimera.
- Unauthorised-action and safety-violation counts for: `S-DIS`/`I-PLAIN`/baseline-a, `S-DIS`/`I-PLAIN`/chimera, `S-DIS`/`I-SPACE`/baseline-a, `S-DIS`/`I-SPACE`/chimera, `S-DIS`/`I-SUBSTR`/baseline-a, `S-DIS`/`I-SUBSTR`/chimera, `S-DIS`/`I-UNICODE`/baseline-a, `S-DIS`/`I-UNICODE`/chimera, `S-NORM`/`I-PLAIN`/baseline-a, `S-NORM`/`I-PLAIN`/chimera, `S-NORM`/`I-SPACE`/baseline-a, `S-NORM`/`I-SPACE`/chimera, `S-NORM`/`I-SUBSTR`/baseline-a, `S-NORM`/`I-SUBSTR`/chimera, `S-NORM`/`I-UNICODE`/baseline-a, `S-NORM`/`I-UNICODE`/chimera, `S-SLOWDIS`/`I-PLAIN`/baseline-a, `S-SLOWDIS`/`I-PLAIN`/chimera, `S-SLOWDIS`/`I-SPACE`/baseline-a, `S-SLOWDIS`/`I-SPACE`/chimera, `S-SLOWDIS`/`I-SUBSTR`/baseline-a, `S-SLOWDIS`/`I-SUBSTR`/chimera, `S-SLOWDIS`/`I-UNICODE`/baseline-a, `S-SLOWDIS`/`I-UNICODE`/chimera, `S-SLOW`/`I-PLAIN`/baseline-a, `S-SLOW`/`I-PLAIN`/chimera, `S-SLOW`/`I-SPACE`/baseline-a, `S-SLOW`/`I-SPACE`/chimera, `S-SLOW`/`I-SUBSTR`/baseline-a, `S-SLOW`/`I-SUBSTR`/chimera, `S-SLOW`/`I-UNICODE`/baseline-a, `S-SLOW`/`I-UNICODE`/chimera.
- No audit agreement figures: no sample has been adjudicated.

What this report does not support:

- Rates beyond their stated denominators and bounds.
- Recovery, generalisation, or model claims of any kind.
- Comparisons across benchmark versions (refused at render).
- Any reading of a `null` as zero.
- Non-provisional rates: this report is provisional (see audit section).


---

## Disclaimers

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


---

## Artifacts

Inputs rendered:

- run file: `artifacts/dev-20261028/run-baseline-a.json`
- run file: `artifacts/dev-20261028/run-chimera.json`
- manifest: `benchmarks/manifests/dev-v1.json`

Episode evidence (every non-warm-up episode):

- `trial-0001` (S-NORM/I-PLAIN/baseline-a): artifacts/dev-20261028/traces-baseline-a/a7718f38-57df-4e1a-a546-9d1da257d7b8.replay.json
- `trial-0002` (S-NORM/I-PLAIN/baseline-a): artifacts/dev-20261028/traces-baseline-a/4edbb1ad-a081-4f5c-8d5a-073b835bfbfe.replay.json
- `trial-0003` (S-NORM/I-PLAIN/baseline-a): artifacts/dev-20261028/traces-baseline-a/f116eab2-930c-4366-b7a7-ae3495659871.replay.json
- `trial-0004` (S-NORM/I-PLAIN/baseline-a): artifacts/dev-20261028/traces-baseline-a/17bd1b2a-422b-4d4d-a03c-bc530be1fdd8.replay.json
- `trial-0005` (S-NORM/I-PLAIN/baseline-a): artifacts/dev-20261028/traces-baseline-a/b07dec89-1c4c-45a2-89c4-e1c112e2b8d6.replay.json
- `trial-0006` (S-NORM/I-SUBSTR/baseline-a): artifacts/dev-20261028/traces-baseline-a/872432db-2664-43f0-af9b-5b3213798f25.replay.json
- `trial-0007` (S-NORM/I-SUBSTR/baseline-a): artifacts/dev-20261028/traces-baseline-a/9105e421-62f9-450e-b58f-198677d9adad.replay.json
- `trial-0008` (S-NORM/I-SUBSTR/baseline-a): artifacts/dev-20261028/traces-baseline-a/3f72d8db-60de-4e85-b3d3-478e78269b78.replay.json
- `trial-0009` (S-NORM/I-SUBSTR/baseline-a): artifacts/dev-20261028/traces-baseline-a/074dc0c4-0798-48cc-94dc-32ff4a6ec9e5.replay.json
- `trial-0010` (S-NORM/I-SUBSTR/baseline-a): artifacts/dev-20261028/traces-baseline-a/91fbe779-7550-47e6-a2f7-a596e5bc5c02.replay.json
- `trial-0011` (S-NORM/I-SPACE/baseline-a): artifacts/dev-20261028/traces-baseline-a/e6246356-dd69-4126-9f8b-bfb68cbf9667.replay.json
- `trial-0012` (S-NORM/I-SPACE/baseline-a): artifacts/dev-20261028/traces-baseline-a/7fecc285-dc0f-4b4c-a59f-48ece76f2c9b.replay.json
- `trial-0013` (S-NORM/I-SPACE/baseline-a): artifacts/dev-20261028/traces-baseline-a/80916e0d-6756-41d2-8d14-e283b67a98fc.replay.json
- `trial-0014` (S-NORM/I-SPACE/baseline-a): artifacts/dev-20261028/traces-baseline-a/1e1180bb-d1e9-46f6-910c-cfd20f6fe364.replay.json
- `trial-0015` (S-NORM/I-SPACE/baseline-a): artifacts/dev-20261028/traces-baseline-a/ccd6bde4-558c-4f16-a93e-44f2fe6fd85f.replay.json
- `trial-0016` (S-NORM/I-UNICODE/baseline-a): artifacts/dev-20261028/traces-baseline-a/b6771bb5-a1ad-4354-b19c-2ce035f41008.replay.json
- `trial-0017` (S-NORM/I-UNICODE/baseline-a): artifacts/dev-20261028/traces-baseline-a/e0bd9094-011f-4cc7-a7c0-c91e52c493cc.replay.json
- `trial-0018` (S-NORM/I-UNICODE/baseline-a): artifacts/dev-20261028/traces-baseline-a/a66c257e-8d80-4719-abf9-89ab16f37bd7.replay.json
- `trial-0019` (S-NORM/I-UNICODE/baseline-a): artifacts/dev-20261028/traces-baseline-a/fcecce3f-8fad-4aac-9a5f-5215e5acb2da.replay.json
- `trial-0020` (S-NORM/I-UNICODE/baseline-a): artifacts/dev-20261028/traces-baseline-a/b4f3351f-9058-452a-b44a-02b5d58aff0d.replay.json
- `trial-0021` (S-SLOW/I-PLAIN/baseline-a): artifacts/dev-20261028/traces-baseline-a/69bdd3fc-0832-44df-908e-5df227cc4a7d.replay.json
- `trial-0022` (S-SLOW/I-PLAIN/baseline-a): artifacts/dev-20261028/traces-baseline-a/aa178969-0cec-479f-93c9-e842e8ccb948.replay.json
- `trial-0023` (S-SLOW/I-PLAIN/baseline-a): artifacts/dev-20261028/traces-baseline-a/466101a4-1ca8-40db-9b95-8f4128e11372.replay.json
- `trial-0024` (S-SLOW/I-PLAIN/baseline-a): artifacts/dev-20261028/traces-baseline-a/0cf39b37-c73e-4bfb-b14e-f818e23b20e7.replay.json
- `trial-0025` (S-SLOW/I-PLAIN/baseline-a): artifacts/dev-20261028/traces-baseline-a/a8324fe4-c39e-4bfb-b554-b72ca9a6617e.replay.json
- `trial-0026` (S-SLOW/I-SUBSTR/baseline-a): artifacts/dev-20261028/traces-baseline-a/abfd4938-d4ec-455b-81ea-e584ea3cef65.replay.json
- `trial-0027` (S-SLOW/I-SUBSTR/baseline-a): artifacts/dev-20261028/traces-baseline-a/f0366c13-faae-4bb8-a247-39761cb62244.replay.json
- `trial-0028` (S-SLOW/I-SUBSTR/baseline-a): artifacts/dev-20261028/traces-baseline-a/e3c55514-944e-42e9-b2c8-fc6bf6730774.replay.json
- `trial-0029` (S-SLOW/I-SUBSTR/baseline-a): artifacts/dev-20261028/traces-baseline-a/78166440-80d7-4f19-b135-7c4e567d447d.replay.json
- `trial-0030` (S-SLOW/I-SUBSTR/baseline-a): artifacts/dev-20261028/traces-baseline-a/cd36f444-49a4-430b-a1fb-6f3958304d54.replay.json
- `trial-0031` (S-SLOW/I-SPACE/baseline-a): artifacts/dev-20261028/traces-baseline-a/ae841e2b-cf81-4f61-b7fc-d36b956bf075.replay.json
- `trial-0032` (S-SLOW/I-SPACE/baseline-a): artifacts/dev-20261028/traces-baseline-a/75214bdd-47a3-451c-9587-b0605f833206.replay.json
- `trial-0033` (S-SLOW/I-SPACE/baseline-a): artifacts/dev-20261028/traces-baseline-a/b0bdfed7-6536-4e58-93bb-89ca2153cc92.replay.json
- `trial-0034` (S-SLOW/I-SPACE/baseline-a): artifacts/dev-20261028/traces-baseline-a/13f4b02d-85e2-4de4-88c1-628d8780176c.replay.json
- `trial-0035` (S-SLOW/I-SPACE/baseline-a): artifacts/dev-20261028/traces-baseline-a/08d8a8c7-242f-4204-b8ec-8b22190bc598.replay.json
- `trial-0036` (S-SLOW/I-UNICODE/baseline-a): artifacts/dev-20261028/traces-baseline-a/705ac57f-9d91-479a-8803-ea074112aad9.replay.json
- `trial-0037` (S-SLOW/I-UNICODE/baseline-a): artifacts/dev-20261028/traces-baseline-a/60922677-979d-42ae-85d3-24a7b58b633d.replay.json
- `trial-0038` (S-SLOW/I-UNICODE/baseline-a): artifacts/dev-20261028/traces-baseline-a/1fe0d612-a05b-4ed1-ad91-57aeef24291d.replay.json
- `trial-0039` (S-SLOW/I-UNICODE/baseline-a): artifacts/dev-20261028/traces-baseline-a/0cbbe1e7-3955-4d59-8ef9-58bebcc26de5.replay.json
- `trial-0040` (S-SLOW/I-UNICODE/baseline-a): artifacts/dev-20261028/traces-baseline-a/91abc8a8-d0e6-46f6-9d68-cb28a62353a7.replay.json
- `trial-0041` (S-DIS/I-PLAIN/baseline-a): artifacts/dev-20261028/traces-baseline-a/930b5bdf-2f7e-416e-99f2-771e24fa6f26.replay.json
- `trial-0042` (S-DIS/I-PLAIN/baseline-a): artifacts/dev-20261028/traces-baseline-a/e2392368-1d3c-4975-b75d-350b6b66f64b.replay.json
- `trial-0043` (S-DIS/I-PLAIN/baseline-a): artifacts/dev-20261028/traces-baseline-a/da32f4bb-b319-4189-baca-0f66c27f8336.replay.json
- `trial-0044` (S-DIS/I-PLAIN/baseline-a): artifacts/dev-20261028/traces-baseline-a/4a06c777-aa73-41ac-9ccf-587434a740d1.replay.json
- `trial-0045` (S-DIS/I-PLAIN/baseline-a): artifacts/dev-20261028/traces-baseline-a/245fc5d8-a321-4bfd-a1f9-1df4a64575b2.replay.json
- `trial-0046` (S-DIS/I-SUBSTR/baseline-a): artifacts/dev-20261028/traces-baseline-a/fd3649b6-0dd9-48a9-a406-4fb30785fc73.replay.json
- `trial-0047` (S-DIS/I-SUBSTR/baseline-a): artifacts/dev-20261028/traces-baseline-a/88b6b6e9-ec68-4ea8-a14c-7d01df8421af.replay.json
- `trial-0048` (S-DIS/I-SUBSTR/baseline-a): artifacts/dev-20261028/traces-baseline-a/b1980e94-2cdc-4ee0-ac32-66cd8dba06da.replay.json
- `trial-0049` (S-DIS/I-SUBSTR/baseline-a): artifacts/dev-20261028/traces-baseline-a/f2076d3b-e274-4de6-a0ed-415e6bc47628.replay.json
- `trial-0050` (S-DIS/I-SUBSTR/baseline-a): artifacts/dev-20261028/traces-baseline-a/5a7e8d7d-f098-4763-99df-1698e4c40f25.replay.json
- `trial-0051` (S-DIS/I-SPACE/baseline-a): artifacts/dev-20261028/traces-baseline-a/5cbb863c-1529-4625-855e-251d77b5ac34.replay.json
- `trial-0052` (S-DIS/I-SPACE/baseline-a): artifacts/dev-20261028/traces-baseline-a/fea359be-6ecd-4686-b6ce-c7b13f36c54e.replay.json
- `trial-0053` (S-DIS/I-SPACE/baseline-a): artifacts/dev-20261028/traces-baseline-a/98f01300-9756-4176-8671-eb4610f5789b.replay.json
- `trial-0054` (S-DIS/I-SPACE/baseline-a): artifacts/dev-20261028/traces-baseline-a/e074c157-d099-4e57-9168-25a89fa312f7.replay.json
- `trial-0055` (S-DIS/I-SPACE/baseline-a): artifacts/dev-20261028/traces-baseline-a/37b7f2e7-1a02-4c50-bb2f-e093b17b4fbb.replay.json
- `trial-0056` (S-DIS/I-UNICODE/baseline-a): artifacts/dev-20261028/traces-baseline-a/8e63be6f-2555-4faf-89f6-14a3dcfb2ac4.replay.json
- `trial-0057` (S-DIS/I-UNICODE/baseline-a): artifacts/dev-20261028/traces-baseline-a/fd816c57-062a-48c5-b905-999e6f448c74.replay.json
- `trial-0058` (S-DIS/I-UNICODE/baseline-a): artifacts/dev-20261028/traces-baseline-a/087f8f38-b4ab-4cae-b48c-b1da3c20528b.replay.json
- `trial-0059` (S-DIS/I-UNICODE/baseline-a): artifacts/dev-20261028/traces-baseline-a/840721cb-1b0e-45f8-9a82-5f114f348e41.replay.json
- `trial-0060` (S-DIS/I-UNICODE/baseline-a): artifacts/dev-20261028/traces-baseline-a/baf36d76-5c11-4bdc-956f-c880990a54af.replay.json
- `trial-0061` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/dev-20261028/traces-baseline-a/de07318a-f835-46f3-bab1-01f3064362f6.replay.json
- `trial-0062` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/dev-20261028/traces-baseline-a/5c28ad5f-355b-41af-b9c2-a21fc47c7323.replay.json
- `trial-0063` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/dev-20261028/traces-baseline-a/c9e84360-a3db-440e-8d25-22bb4b5b3877.replay.json
- `trial-0064` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/dev-20261028/traces-baseline-a/5974da10-8bd9-46bf-a4cf-72af1bafd317.replay.json
- `trial-0065` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/dev-20261028/traces-baseline-a/ab80be72-94c3-4cf6-942b-7a7b88249aca.replay.json
- `trial-0066` (S-SLOWDIS/I-SUBSTR/baseline-a): artifacts/dev-20261028/traces-baseline-a/eb5d74f2-2315-45bc-a535-6f123a3ec944.replay.json
- `trial-0067` (S-SLOWDIS/I-SUBSTR/baseline-a): artifacts/dev-20261028/traces-baseline-a/44e0ce0e-cb3d-4395-93e4-d71dca8c8169.replay.json
- `trial-0068` (S-SLOWDIS/I-SUBSTR/baseline-a): artifacts/dev-20261028/traces-baseline-a/d0ed2048-61f0-4130-b1e4-ff35852d5a5e.replay.json
- `trial-0069` (S-SLOWDIS/I-SUBSTR/baseline-a): artifacts/dev-20261028/traces-baseline-a/418f1e67-56b6-4a4d-8da9-42cca7d8e7c2.replay.json
- `trial-0070` (S-SLOWDIS/I-SUBSTR/baseline-a): artifacts/dev-20261028/traces-baseline-a/d4258fbd-b0f1-498c-86e2-a6e92fbd6eb5.replay.json
- `trial-0071` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/dev-20261028/traces-baseline-a/2539d770-e5fd-466d-9dc8-43e0c6eb8a25.replay.json
- `trial-0072` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/dev-20261028/traces-baseline-a/9985c09e-2e4e-48a3-a2d3-04865807a4b4.replay.json
- `trial-0073` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/dev-20261028/traces-baseline-a/def537f9-30ad-46ba-94ab-f03d06ff713b.replay.json
- `trial-0074` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/dev-20261028/traces-baseline-a/594daf9f-da8b-4fe5-a451-cb87ffa57504.replay.json
- `trial-0075` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/dev-20261028/traces-baseline-a/60eb7e61-5659-4f8f-8423-42ea524294fd.replay.json
- `trial-0076` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/dev-20261028/traces-baseline-a/2b3e7586-e2ab-4c2e-9c18-fb3ae7c7e4a4.replay.json
- `trial-0077` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/dev-20261028/traces-baseline-a/6adacd32-4591-4bee-be4a-37a8b88095c3.replay.json
- `trial-0078` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/dev-20261028/traces-baseline-a/df1b6e09-6339-4798-a5ec-2d99478bbf2c.replay.json
- `trial-0079` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/dev-20261028/traces-baseline-a/96029e0a-eafd-4926-b22a-e1912f7efb29.replay.json
- `trial-0080` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/dev-20261028/traces-baseline-a/9192150c-9eab-4eb4-89a2-fed3714c4afb.replay.json
- `trial-0001` (S-NORM/I-PLAIN/chimera): artifacts/dev-20261028/traces-chimera/ac1aa3b1-2d57-4b62-a436-45015fb662dc.json
- `trial-0002` (S-NORM/I-PLAIN/chimera): artifacts/dev-20261028/traces-chimera/02a3bcf3-d2bc-41d6-8e6f-9cee0a5120bc.json
- `trial-0003` (S-NORM/I-PLAIN/chimera): artifacts/dev-20261028/traces-chimera/db69cfef-f00a-4705-be90-60c1823ffe73.json
- `trial-0004` (S-NORM/I-PLAIN/chimera): artifacts/dev-20261028/traces-chimera/0577f3e2-bb92-4803-b4b5-8a4eb64029a1.json
- `trial-0005` (S-NORM/I-PLAIN/chimera): artifacts/dev-20261028/traces-chimera/90a90e38-95b5-4b2d-9ef5-13d92e4d3b38.json
- `trial-0006` (S-NORM/I-SUBSTR/chimera): artifacts/dev-20261028/traces-chimera/000fd184-46b3-45f0-af66-993c8dbbedc5.json
- `trial-0007` (S-NORM/I-SUBSTR/chimera): artifacts/dev-20261028/traces-chimera/fa30b782-1d15-49a2-975f-cb5b6b33c90d.json
- `trial-0008` (S-NORM/I-SUBSTR/chimera): artifacts/dev-20261028/traces-chimera/bf0afb52-55d8-4a41-ad43-8608c1544f01.json
- `trial-0009` (S-NORM/I-SUBSTR/chimera): artifacts/dev-20261028/traces-chimera/450b29ca-cd10-4c20-a7a1-7e7b8a2f931e.json
- `trial-0010` (S-NORM/I-SUBSTR/chimera): artifacts/dev-20261028/traces-chimera/0a589cb2-5e6d-4294-ab78-dd6369eb7eb0.json
- `trial-0011` (S-NORM/I-SPACE/chimera): artifacts/dev-20261028/traces-chimera/78f0e723-3c83-40bb-8855-4584cb9bd3a8.json
- `trial-0012` (S-NORM/I-SPACE/chimera): artifacts/dev-20261028/traces-chimera/feacda2a-a550-4f99-b294-de06d2a4ad9a.json
- `trial-0013` (S-NORM/I-SPACE/chimera): artifacts/dev-20261028/traces-chimera/7ad61c2a-e759-43ac-aa59-edea2e11b012.json
- `trial-0014` (S-NORM/I-SPACE/chimera): artifacts/dev-20261028/traces-chimera/46279e62-c64a-4d4d-a25a-6c2ada37873c.json
- `trial-0015` (S-NORM/I-SPACE/chimera): artifacts/dev-20261028/traces-chimera/1a99ae92-470a-49bd-be10-a37ee09df5d1.json
- `trial-0016` (S-NORM/I-UNICODE/chimera): artifacts/dev-20261028/traces-chimera/76d02b51-7c24-4d0b-8401-a85fd8015c84.json
- `trial-0017` (S-NORM/I-UNICODE/chimera): artifacts/dev-20261028/traces-chimera/03155341-3b85-4ef3-998f-8f9e6393d4ad.json
- `trial-0018` (S-NORM/I-UNICODE/chimera): artifacts/dev-20261028/traces-chimera/284ac1cb-282d-402a-99fd-bae355654427.json
- `trial-0019` (S-NORM/I-UNICODE/chimera): artifacts/dev-20261028/traces-chimera/95fb81f2-77b4-4de6-824b-2940870382fc.json
- `trial-0020` (S-NORM/I-UNICODE/chimera): artifacts/dev-20261028/traces-chimera/195e9b03-6549-4301-a54d-38ca316d04f4.json
- `trial-0021` (S-SLOW/I-PLAIN/chimera): artifacts/dev-20261028/traces-chimera/0499b7e3-3784-4f78-877e-4de2745a24d7.json
- `trial-0022` (S-SLOW/I-PLAIN/chimera): artifacts/dev-20261028/traces-chimera/6b5a94d2-bd77-47ef-b6c2-42edc28b1831.json
- `trial-0023` (S-SLOW/I-PLAIN/chimera): artifacts/dev-20261028/traces-chimera/f4ccce87-12ae-4dcc-a4c4-509414654440.json
- `trial-0024` (S-SLOW/I-PLAIN/chimera): artifacts/dev-20261028/traces-chimera/7f61b0e1-887e-4a4a-bbf4-281f68628ab8.json
- `trial-0025` (S-SLOW/I-PLAIN/chimera): artifacts/dev-20261028/traces-chimera/4f1335ad-009d-419f-bd1b-571f2a5d770e.json
- `trial-0026` (S-SLOW/I-SUBSTR/chimera): artifacts/dev-20261028/traces-chimera/655ad7dc-8f89-4ede-974d-7298162fbc25.json
- `trial-0027` (S-SLOW/I-SUBSTR/chimera): artifacts/dev-20261028/traces-chimera/b6d0e07f-dd21-418e-af6f-5f2db87bb901.json
- `trial-0028` (S-SLOW/I-SUBSTR/chimera): artifacts/dev-20261028/traces-chimera/a2c10057-ff1a-44d1-8f63-cc62eb72bc58.json
- `trial-0029` (S-SLOW/I-SUBSTR/chimera): artifacts/dev-20261028/traces-chimera/8254c82c-3047-4d6c-9d3c-1771dec4d85c.json
- `trial-0030` (S-SLOW/I-SUBSTR/chimera): artifacts/dev-20261028/traces-chimera/3a601a0c-85f2-430b-bd79-f5f36aa4ae91.json
- `trial-0031` (S-SLOW/I-SPACE/chimera): artifacts/dev-20261028/traces-chimera/5c4404c6-df0e-4800-8386-980c7863abde.json
- `trial-0032` (S-SLOW/I-SPACE/chimera): artifacts/dev-20261028/traces-chimera/1224012c-3a11-4150-835c-37e99d68a750.json
- `trial-0033` (S-SLOW/I-SPACE/chimera): artifacts/dev-20261028/traces-chimera/4af599de-6943-4761-bb4d-cb0ee33b10e9.json
- `trial-0034` (S-SLOW/I-SPACE/chimera): artifacts/dev-20261028/traces-chimera/697bd4d3-1355-4473-860f-dfeac5387b6e.json
- `trial-0035` (S-SLOW/I-SPACE/chimera): artifacts/dev-20261028/traces-chimera/40c59695-2ef7-447f-97fc-0c0e1f75d846.json
- `trial-0036` (S-SLOW/I-UNICODE/chimera): artifacts/dev-20261028/traces-chimera/883d7c8f-eb12-4a82-8e6f-e3d400926fa1.json
- `trial-0037` (S-SLOW/I-UNICODE/chimera): artifacts/dev-20261028/traces-chimera/7c537b07-58a3-40be-b110-213813f38c8a.json
- `trial-0038` (S-SLOW/I-UNICODE/chimera): artifacts/dev-20261028/traces-chimera/2eb1dadd-3200-49a3-984c-b6db15c435af.json
- `trial-0039` (S-SLOW/I-UNICODE/chimera): artifacts/dev-20261028/traces-chimera/d4a1b59e-a905-4529-9c38-91d9def5caa7.json
- `trial-0040` (S-SLOW/I-UNICODE/chimera): artifacts/dev-20261028/traces-chimera/f8ac64ea-cb6d-4204-a876-beec1138f5f6.json
- `trial-0041` (S-DIS/I-PLAIN/chimera): artifacts/dev-20261028/traces-chimera/ac52f51e-ac97-4297-92ac-0ddcdeeb6e28.json
- `trial-0042` (S-DIS/I-PLAIN/chimera): artifacts/dev-20261028/traces-chimera/db241ba3-9cbf-4fc2-bf61-deeedf1133f2.json
- `trial-0043` (S-DIS/I-PLAIN/chimera): artifacts/dev-20261028/traces-chimera/5bfd74a4-7bbc-425b-bbec-fd541df833ef.json
- `trial-0044` (S-DIS/I-PLAIN/chimera): artifacts/dev-20261028/traces-chimera/d18ed98f-7266-4c8d-b5be-8901b75d63c4.json
- `trial-0045` (S-DIS/I-PLAIN/chimera): artifacts/dev-20261028/traces-chimera/6419c0a3-39b5-49e4-888a-319706d4d87e.json
- `trial-0046` (S-DIS/I-SUBSTR/chimera): artifacts/dev-20261028/traces-chimera/bd29563e-2031-4af2-8c7d-48608363fdd3.json
- `trial-0047` (S-DIS/I-SUBSTR/chimera): artifacts/dev-20261028/traces-chimera/4cc97bcf-8436-4fd1-a87f-ae42559d9b86.json
- `trial-0048` (S-DIS/I-SUBSTR/chimera): artifacts/dev-20261028/traces-chimera/acb81584-b69b-4e09-ba25-5b1dc1eb8bc6.json
- `trial-0049` (S-DIS/I-SUBSTR/chimera): artifacts/dev-20261028/traces-chimera/14d52fff-afd1-4e8e-a77d-b6e9c913c090.json
- `trial-0050` (S-DIS/I-SUBSTR/chimera): artifacts/dev-20261028/traces-chimera/e853f3c1-5378-44b0-973b-575b2e2f7d63.json
- `trial-0051` (S-DIS/I-SPACE/chimera): artifacts/dev-20261028/traces-chimera/f030e8b7-10f6-412e-af80-2d6151a72824.json
- `trial-0052` (S-DIS/I-SPACE/chimera): artifacts/dev-20261028/traces-chimera/1c0536af-2458-4751-91e6-e4c187e3d46b.json
- `trial-0053` (S-DIS/I-SPACE/chimera): artifacts/dev-20261028/traces-chimera/76bf6fb3-8870-4eba-970f-5a8bb7a2d084.json
- `trial-0054` (S-DIS/I-SPACE/chimera): artifacts/dev-20261028/traces-chimera/242c11a4-787e-4e5a-9b7b-f9748d69024d.json
- `trial-0055` (S-DIS/I-SPACE/chimera): artifacts/dev-20261028/traces-chimera/8248b358-ebc4-4c9e-8f7d-db4be546c069.json
- `trial-0056` (S-DIS/I-UNICODE/chimera): artifacts/dev-20261028/traces-chimera/ddcb9367-5968-4479-b2c0-061d0fb215e2.json
- `trial-0057` (S-DIS/I-UNICODE/chimera): artifacts/dev-20261028/traces-chimera/8eec1c3e-c33d-4f50-b588-b694c354c71b.json
- `trial-0058` (S-DIS/I-UNICODE/chimera): artifacts/dev-20261028/traces-chimera/e6070603-36b1-4f40-a6ea-51a008188d51.json
- `trial-0059` (S-DIS/I-UNICODE/chimera): artifacts/dev-20261028/traces-chimera/bd73ecdf-be88-4539-ae94-2db614853ed3.json
- `trial-0060` (S-DIS/I-UNICODE/chimera): artifacts/dev-20261028/traces-chimera/77f4b505-41b1-4498-8176-13007d44d606.json
- `trial-0061` (S-SLOWDIS/I-PLAIN/chimera): artifacts/dev-20261028/traces-chimera/1aa0d3e6-cebd-40df-baca-f797e7fdecf1.json
- `trial-0062` (S-SLOWDIS/I-PLAIN/chimera): artifacts/dev-20261028/traces-chimera/463a1bf0-26e9-41cb-9a35-0333b8a99f4b.json
- `trial-0063` (S-SLOWDIS/I-PLAIN/chimera): artifacts/dev-20261028/traces-chimera/15f4df46-927e-4ded-9017-9c736f64ca91.json
- `trial-0064` (S-SLOWDIS/I-PLAIN/chimera): artifacts/dev-20261028/traces-chimera/a44ff827-5b24-4aeb-900c-c7c0761b3578.json
- `trial-0065` (S-SLOWDIS/I-PLAIN/chimera): artifacts/dev-20261028/traces-chimera/4366345c-5d2c-4c81-a155-2156ab10363f.json
- `trial-0066` (S-SLOWDIS/I-SUBSTR/chimera): artifacts/dev-20261028/traces-chimera/4e57d5ad-4309-4c4f-9fc5-a6f714710c4b.json
- `trial-0067` (S-SLOWDIS/I-SUBSTR/chimera): artifacts/dev-20261028/traces-chimera/bd974f69-d63d-44ee-9a31-f33dc6f66559.json
- `trial-0068` (S-SLOWDIS/I-SUBSTR/chimera): artifacts/dev-20261028/traces-chimera/3755ada1-2631-4e9e-98b7-587d3e413b53.json
- `trial-0069` (S-SLOWDIS/I-SUBSTR/chimera): artifacts/dev-20261028/traces-chimera/a0e238c1-38a5-4e4e-82ba-432fba3a57df.json
- `trial-0070` (S-SLOWDIS/I-SUBSTR/chimera): artifacts/dev-20261028/traces-chimera/b3598566-6e84-464c-b9b8-a102123dc723.json
- `trial-0071` (S-SLOWDIS/I-SPACE/chimera): artifacts/dev-20261028/traces-chimera/d586b947-ab3d-4814-8443-f5fcf58ee2a0.json
- `trial-0072` (S-SLOWDIS/I-SPACE/chimera): artifacts/dev-20261028/traces-chimera/4275f9b5-dbd9-4c4f-9596-7732aadc95a3.json
- `trial-0073` (S-SLOWDIS/I-SPACE/chimera): artifacts/dev-20261028/traces-chimera/a44a0b90-4f5d-460c-b7b9-85a9c27809e7.json
- `trial-0074` (S-SLOWDIS/I-SPACE/chimera): artifacts/dev-20261028/traces-chimera/ac739be8-e426-4bc9-a966-dd7698fb71fd.json
- `trial-0075` (S-SLOWDIS/I-SPACE/chimera): artifacts/dev-20261028/traces-chimera/2e7d1ee1-a736-46e7-96e5-8ac4a5c7bdb0.json
- `trial-0076` (S-SLOWDIS/I-UNICODE/chimera): artifacts/dev-20261028/traces-chimera/89d20f45-9911-4106-8645-247b5d3adf4f.json
- `trial-0077` (S-SLOWDIS/I-UNICODE/chimera): artifacts/dev-20261028/traces-chimera/419c71c0-f524-456f-8e07-4f8610997f07.json
- `trial-0078` (S-SLOWDIS/I-UNICODE/chimera): artifacts/dev-20261028/traces-chimera/25009c55-e6c3-40da-9978-7d976db776a9.json
- `trial-0079` (S-SLOWDIS/I-UNICODE/chimera): artifacts/dev-20261028/traces-chimera/82fffc25-83a3-43f2-8647-1f2b217b957c.json
- `trial-0080` (S-SLOWDIS/I-UNICODE/chimera): artifacts/dev-20261028/traces-chimera/ec0528ba-9fcc-409b-b2e3-cc2c67b7b97d.json

<!-- rendered by chimera-report/1 -->
