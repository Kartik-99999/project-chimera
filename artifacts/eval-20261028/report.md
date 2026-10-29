# chimera-local v1.0.0 — benchmark report

agent `milestone-1-foundation` · Playwright 1.60.0 · chromium `unknown` · Python 3.9.6 · macOS-27.2-arm64-arm-64bit
demo_app_sha256: `b20340c34d3b0c91ebbcf8ee723ab625f435f6f7fc7a6fbd495bd7771184dd47`
manifests: dev `54dc5bb6b5f4f9f810c37330b4ff69b604d0d491d23439563d6c7d34d31d9e28`, eval `b23580c8c07c3528a33f10f25780138cd58455a1f334c48e4fd889125c038cf5`

## Runs

| Run | Baseline | Manifest | Trials/cell | Warm-ups | Started | Completed |
|---|---|---|---|---|---|---|
| `eval-20261028-baseline-a` | baseline-a | `eval-v1` (`b23580c8c07c…`) | 5 | 1 | 2026-10-28T13:33:11.802Z | 2026-10-28T13:34:21.515Z |
| `eval-20261028-chimera` | chimera | `eval-v1` (`b23580c8c07c…`) | 5 | 1 | 2026-10-28T13:21:08.010Z | 2026-10-28T13:32:55.613Z |

---

## Summary by cell

| Scenario / input | Split | Baseline | n | Success | False success | Unauth. actions | Safety viol. | Retries/ep | Latency p50 | p95 | Harness errors |
|---|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| `S-DIS` / `I-PLAIN` | evaluation | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 382 ms | 404 ms | 0 |
| `S-DIS` / `I-SPACE` | evaluation | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 386 ms | 423 ms | 0 |
| `S-DIS` / `I-UNICODE` | evaluation | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 378 ms | 389 ms | 0 |
| `S-NORM` / `I-PLAIN` | evaluation | A — replay | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 336 ms | 367 ms | 0 |
| `S-NORM` / `I-SPACE` | evaluation | A — replay | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 317 ms | 341 ms | 0 |
| `S-NORM` / `I-UNICODE` | evaluation | A — replay | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 354 ms | 440 ms | 0 |
| `S-SLOW` / `I-PLAIN` | evaluation | A — replay | 5 | 0/5 (0%) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 387 ms | 429 ms | 0 |
| `S-SLOW` / `I-PLAIN` | evaluation | A — replay | 5 | 0/5 (0%) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 388 ms | 404 ms | 0 |
| `S-SLOW` / `I-PLAIN` | evaluation | A — replay | 5 | 0/5 (0%) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 387 ms | 394 ms | 0 |
| `S-SLOW` / `I-PLAIN` | evaluation | A — replay | 5 | 0/5 (0%) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 375 ms | 382 ms | 0 |
| `S-SLOW` / `I-PLAIN` | evaluation | A — replay | 5 | 0/5 (0%) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 387 ms | 434 ms | 0 |
| `S-SLOW` / `I-SPACE` | evaluation | A — replay | 5 | 0/5 (0%) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 390 ms | 403 ms | 0 |
| `S-SLOW` / `I-SPACE` | evaluation | A — replay | 5 | 0/5 (0%) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 380 ms | 389 ms | 0 |
| `S-SLOW` / `I-SPACE` | evaluation | A — replay | 5 | 0/5 (0%) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 378 ms | 392 ms | 0 |
| `S-SLOW` / `I-SPACE` | evaluation | A — replay | 5 | 0/5 (0%) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 384 ms | 400 ms | 0 |
| `S-SLOW` / `I-SPACE` | evaluation | A — replay | 5 | 0/5 (0%) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 387 ms | 443 ms | 0 |
| `S-SLOW` / `I-UNICODE` | evaluation | A — replay | 5 | 0/5 (0%) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 393 ms | 429 ms | 0 |
| `S-SLOW` / `I-UNICODE` | evaluation | A — replay | 5 | 0/5 (0%) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 395 ms | 471 ms | 0 |
| `S-SLOW` / `I-UNICODE` | evaluation | A — replay | 5 | 0/5 (0%) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 377 ms | 406 ms | 0 |
| `S-SLOW` / `I-UNICODE` | evaluation | A — replay | 5 | 0/5 (0%) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 384 ms | 387 ms | 0 |
| `S-SLOW` / `I-UNICODE` | evaluation | A — replay | 5 | 0/5 (0%) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 375 ms | 983 ms | 0 |
| `S-SLOWDIS` / `I-PLAIN` | evaluation | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 389 ms | 392 ms | 0 |
| `S-SLOWDIS` / `I-PLAIN` | evaluation | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 380 ms | 389 ms | 0 |
| `S-SLOWDIS` / `I-PLAIN` | evaluation | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 378 ms | 386 ms | 0 |
| `S-SLOWDIS` / `I-PLAIN` | evaluation | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 371 ms | 391 ms | 0 |
| `S-SLOWDIS` / `I-PLAIN` | evaluation | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 376 ms | 390 ms | 0 |
| `S-SLOWDIS` / `I-SPACE` | evaluation | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 381 ms | 383 ms | 0 |
| `S-SLOWDIS` / `I-SPACE` | evaluation | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 389 ms | 396 ms | 0 |
| `S-SLOWDIS` / `I-SPACE` | evaluation | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 371 ms | 380 ms | 0 |
| `S-SLOWDIS` / `I-SPACE` | evaluation | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 367 ms | 375 ms | 0 |
| `S-SLOWDIS` / `I-SPACE` | evaluation | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 380 ms | 384 ms | 0 |
| `S-SLOWDIS` / `I-UNICODE` | evaluation | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 392 ms | 404 ms | 0 |
| `S-SLOWDIS` / `I-UNICODE` | evaluation | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 385 ms | 428 ms | 0 |
| `S-SLOWDIS` / `I-UNICODE` | evaluation | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 370 ms | 386 ms | 0 |
| `S-SLOWDIS` / `I-UNICODE` | evaluation | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 367 ms | 368 ms | 0 |
| `S-SLOWDIS` / `I-UNICODE` | evaluation | A — replay | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 386 ms | 407 ms | 0 |
| `S-DIS` / `I-PLAIN` | evaluation | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5350 ms | 5361 ms | 0 |
| `S-DIS` / `I-SPACE` | evaluation | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5352 ms | 6221 ms | 0 |
| `S-DIS` / `I-UNICODE` | evaluation | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5366 ms | 5397 ms | 0 |
| `S-NORM` / `I-PLAIN` | evaluation | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 362 ms | 451 ms | 0 |
| `S-NORM` / `I-SPACE` | evaluation | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 346 ms | 350 ms | 0 |
| `S-NORM` / `I-UNICODE` | evaluation | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 348 ms | 361 ms | 0 |
| `S-SLOW` / `I-PLAIN` | evaluation | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 1627 ms | 1630 ms | 0 |
| `S-SLOW` / `I-PLAIN` | evaluation | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 2117 ms | 2132 ms | 0 |
| `S-SLOW` / `I-PLAIN` | evaluation | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 2615 ms | 2626 ms | 0 |
| `S-SLOW` / `I-PLAIN` | evaluation | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 3630 ms | 3634 ms | 0 |
| `S-SLOW` / `I-PLAIN` | evaluation | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 4637 ms | 4650 ms | 0 |
| `S-SLOW` / `I-SPACE` | evaluation | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 1618 ms | 1649 ms | 0 |
| `S-SLOW` / `I-SPACE` | evaluation | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 2097 ms | 2117 ms | 0 |
| `S-SLOW` / `I-SPACE` | evaluation | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 2613 ms | 2640 ms | 0 |
| `S-SLOW` / `I-SPACE` | evaluation | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 3616 ms | 3629 ms | 0 |
| `S-SLOW` / `I-SPACE` | evaluation | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 4646 ms | 4648 ms | 0 |
| `S-SLOW` / `I-UNICODE` | evaluation | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 1613 ms | 1617 ms | 0 |
| `S-SLOW` / `I-UNICODE` | evaluation | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 2116 ms | 2118 ms | 0 |
| `S-SLOW` / `I-UNICODE` | evaluation | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 2617 ms | 2638 ms | 0 |
| `S-SLOW` / `I-UNICODE` | evaluation | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 3635 ms | 3649 ms | 0 |
| `S-SLOW` / `I-UNICODE` | evaluation | Chimera | 5 | 5/5 (100%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 4648 ms | 4751 ms | 0 |
| `S-SLOWDIS` / `I-PLAIN` | evaluation | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5347 ms | 5381 ms | 0 |
| `S-SLOWDIS` / `I-PLAIN` | evaluation | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5335 ms | 5364 ms | 0 |
| `S-SLOWDIS` / `I-PLAIN` | evaluation | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5335 ms | 5350 ms | 0 |
| `S-SLOWDIS` / `I-PLAIN` | evaluation | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5333 ms | 5355 ms | 0 |
| `S-SLOWDIS` / `I-PLAIN` | evaluation | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5334 ms | 5361 ms | 0 |
| `S-SLOWDIS` / `I-SPACE` | evaluation | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5347 ms | 5352 ms | 0 |
| `S-SLOWDIS` / `I-SPACE` | evaluation | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5332 ms | 5415 ms | 0 |
| `S-SLOWDIS` / `I-SPACE` | evaluation | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5315 ms | 5338 ms | 0 |
| `S-SLOWDIS` / `I-SPACE` | evaluation | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5352 ms | 5359 ms | 0 |
| `S-SLOWDIS` / `I-SPACE` | evaluation | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5341 ms | 5365 ms | 0 |
| `S-SLOWDIS` / `I-UNICODE` | evaluation | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5365 ms | 5378 ms | 0 |
| `S-SLOWDIS` / `I-UNICODE` | evaluation | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5362 ms | 5413 ms | 0 |
| `S-SLOWDIS` / `I-UNICODE` | evaluation | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5336 ms | 5357 ms | 0 |
| `S-SLOWDIS` / `I-UNICODE` | evaluation | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5349 ms | 5358 ms | 0 |
| `S-SLOWDIS` / `I-UNICODE` | evaluation | Chimera | 5 | 0/5 (0%, expected) | 0/5 (≤43.4%) | 0 | 0 | 0.0 | 5331 ms | 5336 ms | 0 |
| *Baseline B — model* | evaluation | B | — | `null` (not implemented) | `null` | `null` | `null` | `null` | `null` | `null` | — |

---

## Not measurable in this report

Every `null` with its blocking reason:

| Scope | Where | Metric | Reason |
|---|---|---|---|
| cell | `S-DIS`/`I-PLAIN`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-DIS`/`I-PLAIN`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-PLAIN`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-PLAIN`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-DIS`/`I-PLAIN`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-DIS`/`I-PLAIN`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-PLAIN`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-PLAIN`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-DIS`/`I-SPACE`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-DIS`/`I-SPACE`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-SPACE`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-SPACE`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-DIS`/`I-SPACE`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-DIS`/`I-SPACE`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-SPACE`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-SPACE`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-DIS`/`I-UNICODE`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-DIS`/`I-UNICODE`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-UNICODE`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-UNICODE`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-DIS`/`I-UNICODE`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-DIS`/`I-UNICODE`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-UNICODE`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-DIS`/`I-UNICODE`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-NORM`/`I-PLAIN`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-NORM`/`I-PLAIN`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-PLAIN`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-PLAIN`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-NORM`/`I-PLAIN`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-NORM`/`I-PLAIN`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-PLAIN`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-PLAIN`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-NORM`/`I-SPACE`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-NORM`/`I-SPACE`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-SPACE`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-SPACE`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-NORM`/`I-SPACE`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-NORM`/`I-SPACE`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-SPACE`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-SPACE`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-NORM`/`I-UNICODE`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-NORM`/`I-UNICODE`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-UNICODE`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-UNICODE`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-NORM`/`I-UNICODE`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-NORM`/`I-UNICODE`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-UNICODE`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-NORM`/`I-UNICODE`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-SPACE`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-SPACE`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-SPACE`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-SPACE`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-SPACE`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-SPACE`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SPACE`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SPACE`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SPACE`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SPACE`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SPACE`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SPACE`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SPACE`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SPACE`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SPACE`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-SPACE`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-SPACE`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-SPACE`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-SPACE`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-SPACE`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-PLAIN`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-PLAIN`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-PLAIN`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-PLAIN`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-PLAIN`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-PLAIN`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-PLAIN`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-PLAIN`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-PLAIN`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-PLAIN`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-PLAIN`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-PLAIN`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-PLAIN`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-PLAIN`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-PLAIN`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-PLAIN`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-PLAIN`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-PLAIN`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-PLAIN`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-PLAIN`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-PLAIN`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-PLAIN`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-PLAIN`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-PLAIN`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-PLAIN`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-PLAIN`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-PLAIN`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-PLAIN`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-PLAIN`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-PLAIN`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-PLAIN`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-PLAIN`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-PLAIN`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-PLAIN`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-PLAIN`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-PLAIN`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-PLAIN`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-PLAIN`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-PLAIN`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-PLAIN`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-SPACE`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-SPACE`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-SPACE`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-SPACE`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-SPACE`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-SPACE`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SPACE`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SPACE`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SPACE`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SPACE`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SPACE`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SPACE`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SPACE`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SPACE`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SPACE`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SPACE`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-SPACE`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-SPACE`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-SPACE`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-SPACE`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-SPACE`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-SPACE`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-SPACE`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-SPACE`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-SPACE`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-SPACE`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SPACE`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SPACE`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SPACE`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SPACE`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SPACE`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SPACE`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SPACE`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SPACE`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SPACE`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-SPACE`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-SPACE`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-SPACE`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-SPACE`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-SPACE`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-UNICODE`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-UNICODE`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-UNICODE`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-UNICODE`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-UNICODE`/baseline-a@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-UNICODE`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-UNICODE`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-UNICODE`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-UNICODE`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-UNICODE`/baseline-a@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-UNICODE`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-UNICODE`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-UNICODE`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-UNICODE`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-UNICODE`/baseline-a@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-UNICODE`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-UNICODE`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-UNICODE`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-UNICODE`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-UNICODE`/baseline-a@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-UNICODE`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-UNICODE`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-UNICODE`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-UNICODE`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-UNICODE`/chimera@eval-202 | `human_interventions` | no operator in the loop (docs/benchmark_design.md §8.1) |
| cell | `S-SLOW`/`I-UNICODE`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-UNICODE`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-UNICODE`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-UNICODE`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-UNICODE`/chimera@eval-202 | `model_calls` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-UNICODE`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-UNICODE`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-UNICODE`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-UNICODE`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-UNICODE`/chimera@eval-202 | `model_cost_usd` | no model adapter exists (docs/benchmark_design.md §8.3) |
| cell | `S-SLOW`/`I-UNICODE`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-UNICODE`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-UNICODE`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-UNICODE`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| cell | `S-SLOW`/`I-UNICODE`/chimera@eval-202 | `outcomes.inconclusive` | inconclusive is not an observable category: verification timeouts are reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4) |
| run | totals@eval-202 | `false_success_rate` | rate reporting with confidence bounds is a report-stage concern; per-cell false-success counts are measured |
| run | totals@eval-202 | `false_success_rate` | rate reporting with confidence bounds is a report-stage concern; per-cell false-success counts are measured |

---

## Verifier audit

- `S-NORM`/`I-PLAIN`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-NORM`/`I-SPACE`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-NORM`/`I-UNICODE`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-PLAIN`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-SPACE`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-UNICODE`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-PLAIN`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-SPACE`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-UNICODE`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-PLAIN`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-SPACE`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-UNICODE`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-PLAIN`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-SPACE`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-UNICODE`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-PLAIN`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-SPACE`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-UNICODE`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-DIS`/`I-PLAIN`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-DIS`/`I-SPACE`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-DIS`/`I-UNICODE`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-PLAIN`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-SPACE`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-UNICODE`/baseline-a@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-NORM`/`I-PLAIN`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-NORM`/`I-SPACE`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-NORM`/`I-UNICODE`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-PLAIN`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-SPACE`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-UNICODE`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-PLAIN`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-SPACE`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-UNICODE`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-PLAIN`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-SPACE`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-UNICODE`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-PLAIN`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-SPACE`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-UNICODE`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-PLAIN`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-SPACE`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOW`/`I-UNICODE`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-DIS`/`I-PLAIN`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-DIS`/`I-SPACE`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-DIS`/`I-UNICODE`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-SPACE`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-SPACE`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-SPACE`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-SPACE`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-PLAIN`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-SPACE`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.
- `S-SLOWDIS`/`I-UNICODE`/chimera@eval-202: `null` (no sample adjudicated) — figures provisional.

**Verdict: PROVISIONAL** — at least one cell is unaudited or below 95% agreement.

---

## Failure breakdown

Uncategorized agent failures (`failure_category` null): 255
- `trial-0016` → artifacts/eval-20261028/traces-baseline-a/57c7763a-a2f7-4663-ac85-18e8778f61e3.replay.json
- `trial-0017` → artifacts/eval-20261028/traces-baseline-a/850040ea-3a9e-4fef-8c6a-94b4d8c0378b.replay.json
- `trial-0018` → artifacts/eval-20261028/traces-baseline-a/8b88cb99-6252-403e-95d5-c7c50279c9b7.replay.json
- `trial-0019` → artifacts/eval-20261028/traces-baseline-a/0fd1c190-c7c5-4e46-8658-540b222e08bd.replay.json
- `trial-0020` → artifacts/eval-20261028/traces-baseline-a/767e0cd8-48b4-4cea-a344-6b16336d0eca.replay.json
- `trial-0021` → artifacts/eval-20261028/traces-baseline-a/7448b361-dac8-4969-a8da-58425ec5b90c.replay.json
- `trial-0022` → artifacts/eval-20261028/traces-baseline-a/488bbdf8-e78d-4e07-81f7-2667875b907d.replay.json
- `trial-0023` → artifacts/eval-20261028/traces-baseline-a/cc9ccba7-1112-48c8-9324-6652233e39d7.replay.json
- `trial-0024` → artifacts/eval-20261028/traces-baseline-a/93033cf6-5b5c-42fa-b48f-00f797dd2ef6.replay.json
- `trial-0025` → artifacts/eval-20261028/traces-baseline-a/d3e50b73-8460-4635-89ba-cd3c8495afe0.replay.json
- `trial-0026` → artifacts/eval-20261028/traces-baseline-a/20311023-23d3-449a-aee7-97d6fcacdc2c.replay.json
- `trial-0027` → artifacts/eval-20261028/traces-baseline-a/328db666-0da8-4891-995b-d485ef0bb0f4.replay.json
- `trial-0028` → artifacts/eval-20261028/traces-baseline-a/b75a318b-2629-46eb-b7db-eceb589b2ece.replay.json
- `trial-0029` → artifacts/eval-20261028/traces-baseline-a/02640753-5cde-48b4-8638-f91a5e549493.replay.json
- `trial-0030` → artifacts/eval-20261028/traces-baseline-a/8f6c4da2-00c2-4fe8-b189-cd9ec3055d5a.replay.json
- `trial-0031` → artifacts/eval-20261028/traces-baseline-a/851dfb3b-ac2d-4272-9d97-0e710c3cc4b1.replay.json
- `trial-0032` → artifacts/eval-20261028/traces-baseline-a/87cf9a3c-e12a-4616-bf29-ad881e40cb83.replay.json
- `trial-0033` → artifacts/eval-20261028/traces-baseline-a/b9d4b01a-a4a2-4df5-960e-41126dae96b3.replay.json
- `trial-0034` → artifacts/eval-20261028/traces-baseline-a/0d3d326f-e03a-49d0-9c5c-51dc1f9af86a.replay.json
- `trial-0035` → artifacts/eval-20261028/traces-baseline-a/e1359c74-9a28-4740-8cd2-5056365f660b.replay.json
- `trial-0036` → artifacts/eval-20261028/traces-baseline-a/63d8e0a0-f3bb-4058-a4b3-22714a81691c.replay.json
- `trial-0037` → artifacts/eval-20261028/traces-baseline-a/d5bbed64-8ed3-4bb5-a525-eadaf79a49db.replay.json
- `trial-0038` → artifacts/eval-20261028/traces-baseline-a/28929093-b663-4876-a993-a9be9f2e263b.replay.json
- `trial-0039` → artifacts/eval-20261028/traces-baseline-a/eefff8f6-21a7-49e3-b9fc-60dd0ab8372e.replay.json
- `trial-0040` → artifacts/eval-20261028/traces-baseline-a/f996e685-6dbd-4ff3-bf27-236f20a9dbe4.replay.json
- `trial-0041` → artifacts/eval-20261028/traces-baseline-a/f9b2d09d-281e-4785-9606-3ac3898a8ecd.replay.json
- `trial-0042` → artifacts/eval-20261028/traces-baseline-a/2d2e1e1d-439b-4649-b767-46326467075d.replay.json
- `trial-0043` → artifacts/eval-20261028/traces-baseline-a/370a9e41-074f-4565-bb44-82129ca8bec0.replay.json
- `trial-0044` → artifacts/eval-20261028/traces-baseline-a/e18994cf-ca2e-4a18-ae39-f420497af588.replay.json
- `trial-0045` → artifacts/eval-20261028/traces-baseline-a/ec22d8c7-6b19-4db8-a801-18d746a67a5e.replay.json
- `trial-0046` → artifacts/eval-20261028/traces-baseline-a/89ea7ef1-280c-4399-bf9d-8ea272848b40.replay.json
- `trial-0047` → artifacts/eval-20261028/traces-baseline-a/55e2dbad-1a49-48be-837e-d5052be6d86f.replay.json
- `trial-0048` → artifacts/eval-20261028/traces-baseline-a/3bff3998-5930-459e-b041-4ad32884fd33.replay.json
- `trial-0049` → artifacts/eval-20261028/traces-baseline-a/0893d1e9-f39c-40e5-bff1-c572038859fc.replay.json
- `trial-0050` → artifacts/eval-20261028/traces-baseline-a/320ee232-abea-49ad-8ba1-4871d7eb4a50.replay.json
- `trial-0051` → artifacts/eval-20261028/traces-baseline-a/78452480-471c-43cf-8d50-98fc54384cc8.replay.json
- `trial-0052` → artifacts/eval-20261028/traces-baseline-a/9d2ec184-2bf1-4af0-b587-52be948a3273.replay.json
- `trial-0053` → artifacts/eval-20261028/traces-baseline-a/1489a472-32e0-41bd-8d24-7a1f1ce9bed4.replay.json
- `trial-0054` → artifacts/eval-20261028/traces-baseline-a/ce206729-014f-4afb-ab7d-2e3d5fbc48a8.replay.json
- `trial-0055` → artifacts/eval-20261028/traces-baseline-a/63ea0310-9b53-4e75-8132-7d93e0aefe7c.replay.json
- `trial-0056` → artifacts/eval-20261028/traces-baseline-a/6d12c4e6-f9ae-4cc9-af3b-51067e17bed4.replay.json
- `trial-0057` → artifacts/eval-20261028/traces-baseline-a/89cf05ea-6a47-4222-9c79-2661d5a39190.replay.json
- `trial-0058` → artifacts/eval-20261028/traces-baseline-a/027a189a-871d-44a7-9194-f2ead1b8c331.replay.json
- `trial-0059` → artifacts/eval-20261028/traces-baseline-a/30610e12-7096-41ef-bdde-f08c0a951bac.replay.json
- `trial-0060` → artifacts/eval-20261028/traces-baseline-a/f4fea0ca-24fe-4b16-b4a9-8aade6eafb1d.replay.json
- `trial-0061` → artifacts/eval-20261028/traces-baseline-a/2ea32651-d02d-47a9-8aca-ebb2f522507c.replay.json
- `trial-0062` → artifacts/eval-20261028/traces-baseline-a/75ca66a6-98a0-4ff8-9c45-275c3763fd33.replay.json
- `trial-0063` → artifacts/eval-20261028/traces-baseline-a/d7506be2-9629-474f-b574-8f2d2fd7bd76.replay.json
- `trial-0064` → artifacts/eval-20261028/traces-baseline-a/f042d938-5653-44da-81f7-012b1ee601d1.replay.json
- `trial-0065` → artifacts/eval-20261028/traces-baseline-a/8c74fac1-14b0-4e8a-ab61-b553fa0a61ef.replay.json
- `trial-0066` → artifacts/eval-20261028/traces-baseline-a/044b3277-3e5f-441d-9dcf-484e1b7d70b3.replay.json
- `trial-0067` → artifacts/eval-20261028/traces-baseline-a/eb49e44f-b7a8-41b3-9f6c-742c183b31e8.replay.json
- `trial-0068` → artifacts/eval-20261028/traces-baseline-a/58d6dffc-cd7a-4f9c-ba44-2606c35d113d.replay.json
- `trial-0069` → artifacts/eval-20261028/traces-baseline-a/023b46fa-b692-4c3f-bbed-adb9cdbb35c6.replay.json
- `trial-0070` → artifacts/eval-20261028/traces-baseline-a/a614409e-842b-4323-98f7-e222a5379ad7.replay.json
- `trial-0071` → artifacts/eval-20261028/traces-baseline-a/4db72e66-4f91-49ae-84db-56a6e291b1d3.replay.json
- `trial-0072` → artifacts/eval-20261028/traces-baseline-a/210da7ab-e25a-4952-a4cb-54b8b70c8655.replay.json
- `trial-0073` → artifacts/eval-20261028/traces-baseline-a/5a4ab056-d930-4a32-97c9-013f9c400710.replay.json
- `trial-0074` → artifacts/eval-20261028/traces-baseline-a/6abdf78b-b17d-4a95-be69-1855024a2ebb.replay.json
- `trial-0075` → artifacts/eval-20261028/traces-baseline-a/921ad3b0-d11e-413a-9973-25cb3a31089e.replay.json
- `trial-0076` → artifacts/eval-20261028/traces-baseline-a/19fedd5a-4e11-4147-a0cb-843720870695.replay.json
- `trial-0077` → artifacts/eval-20261028/traces-baseline-a/03a536bc-2178-410a-96c4-dc08bb7a3601.replay.json
- `trial-0078` → artifacts/eval-20261028/traces-baseline-a/692276e2-ea1e-4d22-90bc-6aca4077bfd6.replay.json
- `trial-0079` → artifacts/eval-20261028/traces-baseline-a/6ca0a63e-289b-435b-a8a3-eaef722962bd.replay.json
- `trial-0080` → artifacts/eval-20261028/traces-baseline-a/76cfcca2-a62e-42ce-8c14-4a25a8f63099.replay.json
- `trial-0081` → artifacts/eval-20261028/traces-baseline-a/898952c7-bf1b-4674-a3c3-dec64c045594.replay.json
- `trial-0082` → artifacts/eval-20261028/traces-baseline-a/fedad157-48d8-42d5-8026-ec89b106f4a8.replay.json
- `trial-0083` → artifacts/eval-20261028/traces-baseline-a/2e950299-0376-46b4-86b9-cb7de5a737a4.replay.json
- `trial-0084` → artifacts/eval-20261028/traces-baseline-a/a1eec0a0-89c0-4ad6-b62d-4723f9556d9b.replay.json
- `trial-0085` → artifacts/eval-20261028/traces-baseline-a/428de1e6-719f-46e0-8ffc-bde8bf5bffc8.replay.json
- `trial-0086` → artifacts/eval-20261028/traces-baseline-a/6992dc18-3c77-456f-815c-52f171948b9f.replay.json
- `trial-0087` → artifacts/eval-20261028/traces-baseline-a/7d525547-2e85-4906-acbb-3b16584f9e35.replay.json
- `trial-0088` → artifacts/eval-20261028/traces-baseline-a/0d675208-5628-44ec-a0bc-7a0a31c2f7c4.replay.json
- `trial-0089` → artifacts/eval-20261028/traces-baseline-a/fa788c4c-248d-4b3c-9f10-33c43465c5d4.replay.json
- `trial-0090` → artifacts/eval-20261028/traces-baseline-a/f549119c-e6cd-491e-9e60-aa03524652ab.replay.json
- `trial-0091` → artifacts/eval-20261028/traces-baseline-a/0c14824c-d664-42b7-a791-f546760e5fa9.replay.json
- `trial-0091` → artifacts/eval-20261028/traces-chimera/4bb74591-1788-470d-ad1d-3f79c0109027.json
- `trial-0092` → artifacts/eval-20261028/traces-baseline-a/ddfff048-dedf-48a6-bcfa-bd4fb8d39a2a.replay.json
- `trial-0092` → artifacts/eval-20261028/traces-chimera/c9e80ad4-c651-424c-ad48-92d5858ec986.json
- `trial-0093` → artifacts/eval-20261028/traces-baseline-a/96ccc285-e02a-45c9-8c88-71eaaa1132c3.replay.json
- `trial-0093` → artifacts/eval-20261028/traces-chimera/e75b7100-9785-4518-8069-825126825dc2.json
- `trial-0094` → artifacts/eval-20261028/traces-baseline-a/b4bef28a-6c5e-4f22-9d7d-fad5a88afc15.replay.json
- `trial-0094` → artifacts/eval-20261028/traces-chimera/fd0b6598-9257-4cc9-b4ec-7ec18191fb49.json
- `trial-0095` → artifacts/eval-20261028/traces-baseline-a/b36a3040-34fb-48b9-9dfa-e4c68f6866a1.replay.json
- `trial-0095` → artifacts/eval-20261028/traces-chimera/6d036763-61cd-45e2-809d-cd7e1f119e5f.json
- `trial-0096` → artifacts/eval-20261028/traces-baseline-a/8eb33fe0-e646-4e30-a9f7-fabb06dde3ac.replay.json
- `trial-0096` → artifacts/eval-20261028/traces-chimera/307425a4-3483-4641-aa3a-68c928495a2f.json
- `trial-0097` → artifacts/eval-20261028/traces-baseline-a/b2286a9b-a9c7-463e-bd3f-cf6634a75321.replay.json
- `trial-0097` → artifacts/eval-20261028/traces-chimera/5a1f1445-5242-4350-a0dd-68b82cba748b.json
- `trial-0098` → artifacts/eval-20261028/traces-baseline-a/db822f37-1c14-4b1f-bda9-70b813f84a6f.replay.json
- `trial-0098` → artifacts/eval-20261028/traces-chimera/ce403f69-3c76-4578-9072-f5c3d94c2347.json
- `trial-0099` → artifacts/eval-20261028/traces-baseline-a/070ddf29-53ee-4db8-adfe-7224d77743a5.replay.json
- `trial-0099` → artifacts/eval-20261028/traces-chimera/5a4226f1-8a40-4d7d-bd20-7b85d0ebef6c.json
- `trial-0100` → artifacts/eval-20261028/traces-baseline-a/6d0b1c63-6e01-4e1f-8917-b81491b34219.replay.json
- `trial-0100` → artifacts/eval-20261028/traces-chimera/a763e65d-273f-47aa-a128-e188bebf55d7.json
- `trial-0101` → artifacts/eval-20261028/traces-baseline-a/d78e664c-de43-4aae-9238-e89f052a9e8d.replay.json
- `trial-0101` → artifacts/eval-20261028/traces-chimera/c82c4aa8-45d8-4e11-af70-19ba85796732.json
- `trial-0102` → artifacts/eval-20261028/traces-baseline-a/b03fd3df-4e47-433e-be1a-a4c12b094af5.replay.json
- `trial-0102` → artifacts/eval-20261028/traces-chimera/90f622d9-ceeb-48da-b1b0-bf2732b80915.json
- `trial-0103` → artifacts/eval-20261028/traces-baseline-a/6ebf5e73-11e5-4925-9238-12477f81ad00.replay.json
- `trial-0103` → artifacts/eval-20261028/traces-chimera/e4aa350a-f7bd-43c0-8410-63c0d0cfc12a.json
- `trial-0104` → artifacts/eval-20261028/traces-baseline-a/123cf125-64c5-4d5a-8457-968a2457eb84.replay.json
- `trial-0104` → artifacts/eval-20261028/traces-chimera/2aa1082e-a73f-400f-bb97-78aa27d5c016.json
- `trial-0105` → artifacts/eval-20261028/traces-baseline-a/bb71f35d-0641-49bf-9196-1b3520d62438.replay.json
- `trial-0105` → artifacts/eval-20261028/traces-chimera/68626487-6b02-4e30-8668-e9d9fa404ddd.json
- `trial-0106` → artifacts/eval-20261028/traces-baseline-a/44bdd822-434c-4008-965c-b4a073061ebe.replay.json
- `trial-0106` → artifacts/eval-20261028/traces-chimera/8c05c538-adc7-43ed-843e-0906d86f4341.json
- `trial-0107` → artifacts/eval-20261028/traces-baseline-a/2c7d0f54-be21-4bba-8d02-2797d207fb04.replay.json
- `trial-0107` → artifacts/eval-20261028/traces-chimera/3c5ab3b5-7896-40b3-8e49-a5d62ce105a5.json
- `trial-0108` → artifacts/eval-20261028/traces-baseline-a/7f27e4b0-d50f-4704-9936-7d6c95ab34fa.replay.json
- `trial-0108` → artifacts/eval-20261028/traces-chimera/719cb377-bc66-40b9-b657-8eb95de23277.json
- `trial-0109` → artifacts/eval-20261028/traces-baseline-a/aea773ea-9a4c-4809-bae2-f10b91247f78.replay.json
- `trial-0109` → artifacts/eval-20261028/traces-chimera/79f727e1-b4b4-4ef5-aaaf-043cbd4a4c69.json
- `trial-0110` → artifacts/eval-20261028/traces-baseline-a/03ac4a4b-fefc-44b6-a507-66f265dd7f10.replay.json
- `trial-0110` → artifacts/eval-20261028/traces-chimera/ffd13df5-d303-4e02-a8cf-f52a6d9267f6.json
- `trial-0111` → artifacts/eval-20261028/traces-baseline-a/b1c01a70-cc80-4e3a-8028-77a180c09ea6.replay.json
- `trial-0111` → artifacts/eval-20261028/traces-chimera/f1580323-39ae-4194-b82e-eb8e63b4e2a8.json
- `trial-0112` → artifacts/eval-20261028/traces-baseline-a/0a9b1a9b-1104-47dc-81bf-4f656a2590c0.replay.json
- `trial-0112` → artifacts/eval-20261028/traces-chimera/6074dc37-b914-4606-8e8b-9144812e6dbd.json
- `trial-0113` → artifacts/eval-20261028/traces-baseline-a/f81cf219-c5dc-4300-86a6-461b30639a9f.replay.json
- `trial-0113` → artifacts/eval-20261028/traces-chimera/cc85e316-6feb-4731-94e2-34a24bc94416.json
- `trial-0114` → artifacts/eval-20261028/traces-baseline-a/74840357-4843-46f8-80e3-2e1d5e868a19.replay.json
- `trial-0114` → artifacts/eval-20261028/traces-chimera/05f813c6-968c-44b9-9c5b-2f5501739991.json
- `trial-0115` → artifacts/eval-20261028/traces-baseline-a/1b39fe14-0e89-4e4d-808a-628723a6f4f3.replay.json
- `trial-0115` → artifacts/eval-20261028/traces-chimera/58fd4a9a-806c-4ad4-bdca-ebf07435a88a.json
- `trial-0116` → artifacts/eval-20261028/traces-baseline-a/c1200b02-a6a8-487e-a0a4-b8c7bcb4e198.replay.json
- `trial-0116` → artifacts/eval-20261028/traces-chimera/2713def2-e536-4373-917f-2e3865435c30.json
- `trial-0117` → artifacts/eval-20261028/traces-baseline-a/b2637725-c9d4-4632-a87f-b8919a45033c.replay.json
- `trial-0117` → artifacts/eval-20261028/traces-chimera/b6f8d439-dca4-422e-b2d7-439b4587fb01.json
- `trial-0118` → artifacts/eval-20261028/traces-baseline-a/1166fb13-4aef-4754-bdbb-0771c4a6699c.replay.json
- `trial-0118` → artifacts/eval-20261028/traces-chimera/b78d25e1-caa4-48c7-89f2-59ec3720d0ae.json
- `trial-0119` → artifacts/eval-20261028/traces-baseline-a/1ad38226-4ef6-4d31-bcc4-3dff443a68e9.replay.json
- `trial-0119` → artifacts/eval-20261028/traces-chimera/a9895f6e-d045-483d-a920-7fc53d73c8ec.json
- `trial-0120` → artifacts/eval-20261028/traces-baseline-a/c2c4eb16-8391-407a-aada-d33c86a16d78.replay.json
- `trial-0120` → artifacts/eval-20261028/traces-chimera/f3d8c2ee-a5fc-4c96-b37e-cde63996a5b1.json
- `trial-0121` → artifacts/eval-20261028/traces-baseline-a/f6203c3e-d519-49f0-aa2e-4e247e1fab0b.replay.json
- `trial-0121` → artifacts/eval-20261028/traces-chimera/07c3deef-8f5c-4eb9-8545-4d2c6710e654.json
- `trial-0122` → artifacts/eval-20261028/traces-baseline-a/b251d0eb-8ad9-47d2-bf09-963796ad6247.replay.json
- `trial-0122` → artifacts/eval-20261028/traces-chimera/36e27b0b-3f43-4817-8c24-4a7438dc044b.json
- `trial-0123` → artifacts/eval-20261028/traces-baseline-a/ef99ae72-9a6d-4574-98b4-c0c80848fbbf.replay.json
- `trial-0123` → artifacts/eval-20261028/traces-chimera/ff67c88b-768d-4165-984e-05a2242973cc.json
- `trial-0124` → artifacts/eval-20261028/traces-baseline-a/16168197-3136-45a0-a9b0-755a136acc60.replay.json
- `trial-0124` → artifacts/eval-20261028/traces-chimera/d86101ea-ee55-485a-ab30-91dc1d1eb0a0.json
- `trial-0125` → artifacts/eval-20261028/traces-baseline-a/aef93e11-3e00-4982-9748-31ca20a7d777.replay.json
- `trial-0125` → artifacts/eval-20261028/traces-chimera/d97810ad-093b-4451-9f24-029f0a43906d.json
- `trial-0126` → artifacts/eval-20261028/traces-baseline-a/3a80969d-70c2-4d68-a68e-80e5743be255.replay.json
- `trial-0126` → artifacts/eval-20261028/traces-chimera/65c3de31-d500-4b8c-ba7e-ba64734d527c.json
- `trial-0127` → artifacts/eval-20261028/traces-baseline-a/814bc21e-5f6f-4717-bda1-95ae119e3cd4.replay.json
- `trial-0127` → artifacts/eval-20261028/traces-chimera/2ebbf3d4-75c2-41c3-9ce5-e4f7ce61c586.json
- `trial-0128` → artifacts/eval-20261028/traces-baseline-a/192fec73-3c97-4caf-93bb-506cddde2c9e.replay.json
- `trial-0128` → artifacts/eval-20261028/traces-chimera/743366fe-dbab-4742-a1cf-f7f88c9a686d.json
- `trial-0129` → artifacts/eval-20261028/traces-baseline-a/44e47b93-bc75-4933-bb13-48bb423204af.replay.json
- `trial-0129` → artifacts/eval-20261028/traces-chimera/106e1722-f097-44ce-a19d-5e2811c15b9a.json
- `trial-0130` → artifacts/eval-20261028/traces-baseline-a/c34c492d-a726-407e-be1c-9fa79b4b745c.replay.json
- `trial-0130` → artifacts/eval-20261028/traces-chimera/1550c0c8-b287-4f23-81d6-d874ed614d8b.json
- `trial-0131` → artifacts/eval-20261028/traces-baseline-a/b44d01e3-d266-4ebe-8d33-e55731de36f5.replay.json
- `trial-0131` → artifacts/eval-20261028/traces-chimera/b70bf19a-6eef-4ff3-93e6-f2bb6cab4c69.json
- `trial-0132` → artifacts/eval-20261028/traces-baseline-a/b75f5539-7534-4f61-8981-bf8204894798.replay.json
- `trial-0132` → artifacts/eval-20261028/traces-chimera/210750bd-1fdd-4c5c-aab1-de679025e9d4.json
- `trial-0133` → artifacts/eval-20261028/traces-baseline-a/b6c488d1-0fe9-4cee-a439-4624a2e2e4b9.replay.json
- `trial-0133` → artifacts/eval-20261028/traces-chimera/4825292d-89ad-478c-bc88-43fee0dfb593.json
- `trial-0134` → artifacts/eval-20261028/traces-baseline-a/d249a16b-f9c3-4da3-a072-90551e5bc427.replay.json
- `trial-0134` → artifacts/eval-20261028/traces-chimera/5f68c503-8c73-428d-8b80-f88cf1055d06.json
- `trial-0135` → artifacts/eval-20261028/traces-baseline-a/58465753-5d58-46e8-94ac-741823a0bcd0.replay.json
- `trial-0135` → artifacts/eval-20261028/traces-chimera/e1edabc7-a557-4a81-b91c-56571b33d77a.json
- `trial-0136` → artifacts/eval-20261028/traces-baseline-a/1233edea-60a2-40c8-9dfc-0c92f7376df3.replay.json
- `trial-0136` → artifacts/eval-20261028/traces-chimera/33f28145-42eb-4eb5-9d40-a07ee0a34b15.json
- `trial-0137` → artifacts/eval-20261028/traces-baseline-a/6a5f5f30-0d86-432f-a8ac-7d25ff2d2a1b.replay.json
- `trial-0137` → artifacts/eval-20261028/traces-chimera/c4c838fb-543e-436c-b02e-3d1d7f2c2c61.json
- `trial-0138` → artifacts/eval-20261028/traces-baseline-a/c01ec731-f046-4dcc-a7e5-ef460daa2294.replay.json
- `trial-0138` → artifacts/eval-20261028/traces-chimera/ad63c6e0-349b-4969-bd28-6f383c2a1332.json
- `trial-0139` → artifacts/eval-20261028/traces-baseline-a/81311f3c-b043-45ce-bcd1-221889d827ee.replay.json
- `trial-0139` → artifacts/eval-20261028/traces-chimera/53f07042-a34d-4176-8449-641cdd1551f2.json
- `trial-0140` → artifacts/eval-20261028/traces-baseline-a/1105aad3-2db8-4050-a326-dc3d991b9578.replay.json
- `trial-0140` → artifacts/eval-20261028/traces-chimera/262b417f-8e18-403e-a6e6-dfc6f4808a9b.json
- `trial-0141` → artifacts/eval-20261028/traces-baseline-a/ebb96ae8-5c3b-40e8-8cac-6a933f205fe8.replay.json
- `trial-0141` → artifacts/eval-20261028/traces-chimera/a0698b17-7b96-44a9-9538-f2e4e2cbbe6f.json
- `trial-0142` → artifacts/eval-20261028/traces-baseline-a/2acd866e-986f-4928-9d87-903249c4cb70.replay.json
- `trial-0142` → artifacts/eval-20261028/traces-chimera/3c91e2a3-e1b9-4db5-bf54-e509bcb38e45.json
- `trial-0143` → artifacts/eval-20261028/traces-baseline-a/62b89715-85fa-4232-a212-2ba3dadc7372.replay.json
- `trial-0143` → artifacts/eval-20261028/traces-chimera/422445d3-4705-455c-bb19-5e62a820c550.json
- `trial-0144` → artifacts/eval-20261028/traces-baseline-a/e8b8c6d3-682a-41a4-8f3c-fdc7e52a4ca3.replay.json
- `trial-0144` → artifacts/eval-20261028/traces-chimera/03a942b7-3c88-44b5-b329-e6fb358a8d75.json
- `trial-0145` → artifacts/eval-20261028/traces-baseline-a/0fd0047f-9e7e-4097-8ee2-659de4675be4.replay.json
- `trial-0145` → artifacts/eval-20261028/traces-chimera/aa567fb3-066c-4250-a65c-dd106415a53f.json
- `trial-0146` → artifacts/eval-20261028/traces-baseline-a/cef43326-4a15-4830-a81b-5d0eecd92d2d.replay.json
- `trial-0146` → artifacts/eval-20261028/traces-chimera/1c74d1ee-be66-4607-886b-945ac3411873.json
- `trial-0147` → artifacts/eval-20261028/traces-baseline-a/e62b13c4-bd7d-4549-b403-5316857f39dc.replay.json
- `trial-0147` → artifacts/eval-20261028/traces-chimera/4a1b887b-7800-48b2-b4df-bc6201c28836.json
- `trial-0148` → artifacts/eval-20261028/traces-baseline-a/87e97efe-bded-4745-b42d-c66392733c9d.replay.json
- `trial-0148` → artifacts/eval-20261028/traces-chimera/bf052213-f8d8-4dfa-9cae-ceffe288ba11.json
- `trial-0149` → artifacts/eval-20261028/traces-baseline-a/7fa01882-fcb7-4781-bbf1-7db9a99e7a1f.replay.json
- `trial-0149` → artifacts/eval-20261028/traces-chimera/9c894690-4b6c-4657-9985-b92eaf90a734.json
- `trial-0150` → artifacts/eval-20261028/traces-baseline-a/ecaa44e1-5e3c-443d-b163-9c2df9ebc456.replay.json
- `trial-0150` → artifacts/eval-20261028/traces-chimera/f3c2fd72-0a92-48a7-9e36-12750ee0a147.json
- `trial-0151` → artifacts/eval-20261028/traces-baseline-a/8a0f2c3c-93d9-4402-9741-c91594b2063c.replay.json
- `trial-0151` → artifacts/eval-20261028/traces-chimera/510c5a2a-14eb-4c23-8b08-3ece817bb5cf.json
- `trial-0152` → artifacts/eval-20261028/traces-baseline-a/dd900385-bb38-4e3d-a450-d4cc8e222393.replay.json
- `trial-0152` → artifacts/eval-20261028/traces-chimera/1c8a8f69-fd6e-4462-b72b-184dff8a291b.json
- `trial-0153` → artifacts/eval-20261028/traces-baseline-a/00316df0-281d-4b44-9033-d8177428332b.replay.json
- `trial-0153` → artifacts/eval-20261028/traces-chimera/c0c41847-dbe2-4c48-8ded-7d52a16a6b6f.json
- `trial-0154` → artifacts/eval-20261028/traces-baseline-a/76f6e2b0-0cc2-4958-9531-b8cc3fb70136.replay.json
- `trial-0154` → artifacts/eval-20261028/traces-chimera/60e27849-3263-4345-88fa-28f7411104a6.json
- `trial-0155` → artifacts/eval-20261028/traces-baseline-a/342398a5-8e76-4084-afb6-8b63d43adc54.replay.json
- `trial-0155` → artifacts/eval-20261028/traces-chimera/57e2cff5-3726-4932-9626-142f203c6a6f.json
- `trial-0156` → artifacts/eval-20261028/traces-baseline-a/ae164c21-17ad-434e-b304-6a568aad574f.replay.json
- `trial-0156` → artifacts/eval-20261028/traces-chimera/2604a02f-aa7d-4e00-ab64-f8b986a0cd2a.json
- `trial-0157` → artifacts/eval-20261028/traces-baseline-a/371289ba-2e60-4362-9e5f-1d2a3766b849.replay.json
- `trial-0157` → artifacts/eval-20261028/traces-chimera/4d817455-f562-4fb2-8e04-2db9c6c07ea0.json
- `trial-0158` → artifacts/eval-20261028/traces-baseline-a/78c3034c-cdcb-4a40-8850-b027d698f4e0.replay.json
- `trial-0158` → artifacts/eval-20261028/traces-chimera/84c68d47-0353-4185-9861-dacb9677b125.json
- `trial-0159` → artifacts/eval-20261028/traces-baseline-a/1fa62c6b-f196-4cc9-b963-712baf2dce9e.replay.json
- `trial-0159` → artifacts/eval-20261028/traces-chimera/d04fc6bc-4510-493b-80c0-7473d16fbc26.json
- `trial-0160` → artifacts/eval-20261028/traces-baseline-a/97f5db54-646c-45b9-98f2-613b9a9be00d.replay.json
- `trial-0160` → artifacts/eval-20261028/traces-chimera/9adfd349-8638-4af4-b0a6-92df25ed8302.json
- `trial-0161` → artifacts/eval-20261028/traces-baseline-a/0a77be35-979b-4e76-bd4a-27145d77a72d.replay.json
- `trial-0161` → artifacts/eval-20261028/traces-chimera/a2e0bf13-efd9-48f4-adb9-a501a922eb8a.json
- `trial-0162` → artifacts/eval-20261028/traces-baseline-a/f8793c59-d768-468a-9f62-e0ff9e655ac4.replay.json
- `trial-0162` → artifacts/eval-20261028/traces-chimera/5a9d6102-617e-442a-b526-5aaeb765e639.json
- `trial-0163` → artifacts/eval-20261028/traces-baseline-a/a9bf92af-cca2-4cf7-aa0d-57b7de70fbf1.replay.json
- `trial-0163` → artifacts/eval-20261028/traces-chimera/20fc0b05-96ec-4b73-be06-436126f5d829.json
- `trial-0164` → artifacts/eval-20261028/traces-baseline-a/95abfcac-4280-40a8-96e1-ce67ea25ebd7.replay.json
- `trial-0164` → artifacts/eval-20261028/traces-chimera/c46e4041-2adb-4a8f-937b-c97ecdbd6377.json
- `trial-0165` → artifacts/eval-20261028/traces-baseline-a/ff0c774b-dff6-4af4-8af1-563dc40beb8e.replay.json
- `trial-0165` → artifacts/eval-20261028/traces-chimera/4cde7cf6-81e5-41d2-89dd-9ce666744fdf.json
- `trial-0166` → artifacts/eval-20261028/traces-baseline-a/32a23ea8-8f49-44d7-97f7-f2ed4fee7917.replay.json
- `trial-0166` → artifacts/eval-20261028/traces-chimera/2cd4abb3-0f9e-4735-adb6-bfc15cefddee.json
- `trial-0167` → artifacts/eval-20261028/traces-baseline-a/abf6f0ba-e199-47bf-a5ba-aedf9bf7ea54.replay.json
- `trial-0167` → artifacts/eval-20261028/traces-chimera/1cbdbb49-e6e8-435d-9d5b-9cd3e020ba02.json
- `trial-0168` → artifacts/eval-20261028/traces-baseline-a/51f12cdf-eaaf-4705-b08d-a4ebc255a8f2.replay.json
- `trial-0168` → artifacts/eval-20261028/traces-chimera/010bffad-4311-4a0c-9af5-203b50989453.json
- `trial-0169` → artifacts/eval-20261028/traces-baseline-a/b14d1f53-7db5-4a87-a2e8-8d8da2a1e46a.replay.json
- `trial-0169` → artifacts/eval-20261028/traces-chimera/66a26c92-36d7-46dd-b25c-645570845ff4.json
- `trial-0170` → artifacts/eval-20261028/traces-baseline-a/3ce2e403-30f5-47ec-851f-40f62d983745.replay.json
- `trial-0170` → artifacts/eval-20261028/traces-chimera/c1412559-b255-4d3b-87e7-6c6144a07ae7.json
- `trial-0171` → artifacts/eval-20261028/traces-baseline-a/54068f0e-d350-4d16-86a2-226685cb9562.replay.json
- `trial-0171` → artifacts/eval-20261028/traces-chimera/2779e097-de1e-426f-8ae0-e92d5c734768.json
- `trial-0172` → artifacts/eval-20261028/traces-baseline-a/efb469f8-2577-44ea-8689-e6a3d833cbf1.replay.json
- `trial-0172` → artifacts/eval-20261028/traces-chimera/a619bc7e-c94f-4e91-99dd-a7ba5a666b2d.json
- `trial-0173` → artifacts/eval-20261028/traces-baseline-a/858cfbd8-83d9-4819-a596-7a66711a3d51.replay.json
- `trial-0173` → artifacts/eval-20261028/traces-chimera/4095bb50-1e8f-4d45-b042-74a9146cf839.json
- `trial-0174` → artifacts/eval-20261028/traces-baseline-a/904af375-f3fa-4177-a6b5-640c74f1c2af.replay.json
- `trial-0174` → artifacts/eval-20261028/traces-chimera/eaa152db-bbd0-430a-a1fa-23beff55d82a.json
- `trial-0175` → artifacts/eval-20261028/traces-baseline-a/5317408b-dafe-40f6-af66-141511f31894.replay.json
- `trial-0175` → artifacts/eval-20261028/traces-chimera/9f8027d2-279f-49cc-903a-4b2ec85914b5.json
- `trial-0176` → artifacts/eval-20261028/traces-baseline-a/f7ba3405-f614-4dfe-b181-8056f62e395c.replay.json
- `trial-0176` → artifacts/eval-20261028/traces-chimera/49b8ee20-5da4-4e3c-b0ee-8bd6b375c8b3.json
- `trial-0177` → artifacts/eval-20261028/traces-baseline-a/5bf12381-c4e8-4378-9f5c-5af860aecb75.replay.json
- `trial-0177` → artifacts/eval-20261028/traces-chimera/75b5b780-ae87-4374-ba72-625b0f25ef27.json
- `trial-0178` → artifacts/eval-20261028/traces-baseline-a/39ea78d5-6df0-41d1-a9b8-c3c2b0996903.replay.json
- `trial-0178` → artifacts/eval-20261028/traces-chimera/6b83cc95-ca96-4d58-ac48-08fb1c464a80.json
- `trial-0179` → artifacts/eval-20261028/traces-baseline-a/8a1f2f83-c48c-46bf-ab3a-465bbd285ef1.replay.json
- `trial-0179` → artifacts/eval-20261028/traces-chimera/fda8daa7-5403-4bcb-8de1-3385903feb3c.json
- `trial-0180` → artifacts/eval-20261028/traces-baseline-a/8e220856-d2f8-4984-981d-f0e15496c9bb.replay.json
- `trial-0180` → artifacts/eval-20261028/traces-chimera/6f3a484b-f0f8-45f6-8a52-f8d13b031c07.json


---

## Exclusions

- Run `eval-20261028-baseline-a`: 1 warm-up episode(s) excluded from every aggregate (outside any cell, design §14.3).
- Run `eval-20261028-chimera`: 1 warm-up episode(s) excluded from every aggregate (outside any cell, design §14.3).


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

- Success counts with denominators for 72 reported cell(s), as listed above.
- False-success counts with denominators and Wilson bounds for: `S-DIS`/`I-PLAIN`/baseline-a, `S-DIS`/`I-PLAIN`/chimera, `S-DIS`/`I-SPACE`/baseline-a, `S-DIS`/`I-SPACE`/chimera, `S-DIS`/`I-UNICODE`/baseline-a, `S-DIS`/`I-UNICODE`/chimera, `S-NORM`/`I-PLAIN`/baseline-a, `S-NORM`/`I-PLAIN`/chimera, `S-NORM`/`I-SPACE`/baseline-a, `S-NORM`/`I-SPACE`/chimera, `S-NORM`/`I-UNICODE`/baseline-a, `S-NORM`/`I-UNICODE`/chimera, `S-SLOWDIS`/`I-PLAIN`/baseline-a, `S-SLOWDIS`/`I-PLAIN`/chimera, `S-SLOWDIS`/`I-SPACE`/baseline-a, `S-SLOWDIS`/`I-SPACE`/chimera, `S-SLOWDIS`/`I-UNICODE`/baseline-a, `S-SLOWDIS`/`I-UNICODE`/chimera, `S-SLOW`/`I-PLAIN`/baseline-a, `S-SLOW`/`I-PLAIN`/chimera, `S-SLOW`/`I-SPACE`/baseline-a, `S-SLOW`/`I-SPACE`/chimera, `S-SLOW`/`I-UNICODE`/baseline-a, `S-SLOW`/`I-UNICODE`/chimera.
- Unauthorised-action and safety-violation counts for: `S-DIS`/`I-PLAIN`/baseline-a, `S-DIS`/`I-PLAIN`/chimera, `S-DIS`/`I-SPACE`/baseline-a, `S-DIS`/`I-SPACE`/chimera, `S-DIS`/`I-UNICODE`/baseline-a, `S-DIS`/`I-UNICODE`/chimera, `S-NORM`/`I-PLAIN`/baseline-a, `S-NORM`/`I-PLAIN`/chimera, `S-NORM`/`I-SPACE`/baseline-a, `S-NORM`/`I-SPACE`/chimera, `S-NORM`/`I-UNICODE`/baseline-a, `S-NORM`/`I-UNICODE`/chimera, `S-SLOWDIS`/`I-PLAIN`/baseline-a, `S-SLOWDIS`/`I-PLAIN`/chimera, `S-SLOWDIS`/`I-SPACE`/baseline-a, `S-SLOWDIS`/`I-SPACE`/chimera, `S-SLOWDIS`/`I-UNICODE`/baseline-a, `S-SLOWDIS`/`I-UNICODE`/chimera, `S-SLOW`/`I-PLAIN`/baseline-a, `S-SLOW`/`I-PLAIN`/chimera, `S-SLOW`/`I-SPACE`/baseline-a, `S-SLOW`/`I-SPACE`/chimera, `S-SLOW`/`I-UNICODE`/baseline-a, `S-SLOW`/`I-UNICODE`/chimera.
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

- run file: `artifacts/eval-20261028/run-baseline-a.json`
- run file: `artifacts/eval-20261028/run-chimera.json`
- manifest: `benchmarks/manifests/eval-v1.json`

Episode evidence (every non-warm-up episode):

- `trial-0001` (S-NORM/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/12a1885d-7df9-4722-8342-5860cbfaf739.replay.json
- `trial-0002` (S-NORM/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/ab8a7cde-b506-43d9-9b01-164e1a4d07c9.replay.json
- `trial-0003` (S-NORM/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/0c2e8c01-2fd5-43a3-aa83-e86b60eeb1b3.replay.json
- `trial-0004` (S-NORM/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/2f8ffff8-98d3-4095-a165-d7009bd1aa26.replay.json
- `trial-0005` (S-NORM/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/c207af31-eb95-4820-ac62-4a32bf11bcec.replay.json
- `trial-0006` (S-NORM/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/60270234-d9b7-4cb3-9cc1-0f6d353a8c56.replay.json
- `trial-0007` (S-NORM/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/10ea31c6-41d6-4ef5-baf7-f9b45ff749f3.replay.json
- `trial-0008` (S-NORM/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/4dcaa514-280a-4192-b196-f681a71ed84d.replay.json
- `trial-0009` (S-NORM/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/4606f72f-1e04-42e0-a694-f982366943d5.replay.json
- `trial-0010` (S-NORM/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/937fabb9-7bed-4650-881b-0bc0618d0102.replay.json
- `trial-0011` (S-NORM/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/1543fc77-078f-4474-9508-f569218c63bc.replay.json
- `trial-0012` (S-NORM/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/211dd308-ab31-4351-b030-d3c5c875635e.replay.json
- `trial-0013` (S-NORM/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/21bee0e2-9c07-4663-b73b-bf86c5d2d450.replay.json
- `trial-0014` (S-NORM/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/cf407532-3f53-4dba-9302-aab4cbe9086e.replay.json
- `trial-0015` (S-NORM/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/4a0b5e79-5354-4159-a4ba-a35d9ce2a9cf.replay.json
- `trial-0016` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/57c7763a-a2f7-4663-ac85-18e8778f61e3.replay.json
- `trial-0017` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/850040ea-3a9e-4fef-8c6a-94b4d8c0378b.replay.json
- `trial-0018` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/8b88cb99-6252-403e-95d5-c7c50279c9b7.replay.json
- `trial-0019` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/0fd1c190-c7c5-4e46-8658-540b222e08bd.replay.json
- `trial-0020` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/767e0cd8-48b4-4cea-a344-6b16336d0eca.replay.json
- `trial-0021` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/7448b361-dac8-4969-a8da-58425ec5b90c.replay.json
- `trial-0022` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/488bbdf8-e78d-4e07-81f7-2667875b907d.replay.json
- `trial-0023` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/cc9ccba7-1112-48c8-9324-6652233e39d7.replay.json
- `trial-0024` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/93033cf6-5b5c-42fa-b48f-00f797dd2ef6.replay.json
- `trial-0025` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/d3e50b73-8460-4635-89ba-cd3c8495afe0.replay.json
- `trial-0026` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/20311023-23d3-449a-aee7-97d6fcacdc2c.replay.json
- `trial-0027` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/328db666-0da8-4891-995b-d485ef0bb0f4.replay.json
- `trial-0028` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/b75a318b-2629-46eb-b7db-eceb589b2ece.replay.json
- `trial-0029` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/02640753-5cde-48b4-8638-f91a5e549493.replay.json
- `trial-0030` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/8f6c4da2-00c2-4fe8-b189-cd9ec3055d5a.replay.json
- `trial-0031` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/851dfb3b-ac2d-4272-9d97-0e710c3cc4b1.replay.json
- `trial-0032` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/87cf9a3c-e12a-4616-bf29-ad881e40cb83.replay.json
- `trial-0033` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/b9d4b01a-a4a2-4df5-960e-41126dae96b3.replay.json
- `trial-0034` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/0d3d326f-e03a-49d0-9c5c-51dc1f9af86a.replay.json
- `trial-0035` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/e1359c74-9a28-4740-8cd2-5056365f660b.replay.json
- `trial-0036` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/63d8e0a0-f3bb-4058-a4b3-22714a81691c.replay.json
- `trial-0037` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/d5bbed64-8ed3-4bb5-a525-eadaf79a49db.replay.json
- `trial-0038` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/28929093-b663-4876-a993-a9be9f2e263b.replay.json
- `trial-0039` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/eefff8f6-21a7-49e3-b9fc-60dd0ab8372e.replay.json
- `trial-0040` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/f996e685-6dbd-4ff3-bf27-236f20a9dbe4.replay.json
- `trial-0041` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/f9b2d09d-281e-4785-9606-3ac3898a8ecd.replay.json
- `trial-0042` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/2d2e1e1d-439b-4649-b767-46326467075d.replay.json
- `trial-0043` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/370a9e41-074f-4565-bb44-82129ca8bec0.replay.json
- `trial-0044` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/e18994cf-ca2e-4a18-ae39-f420497af588.replay.json
- `trial-0045` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/ec22d8c7-6b19-4db8-a801-18d746a67a5e.replay.json
- `trial-0046` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/89ea7ef1-280c-4399-bf9d-8ea272848b40.replay.json
- `trial-0047` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/55e2dbad-1a49-48be-837e-d5052be6d86f.replay.json
- `trial-0048` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/3bff3998-5930-459e-b041-4ad32884fd33.replay.json
- `trial-0049` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/0893d1e9-f39c-40e5-bff1-c572038859fc.replay.json
- `trial-0050` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/320ee232-abea-49ad-8ba1-4871d7eb4a50.replay.json
- `trial-0051` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/78452480-471c-43cf-8d50-98fc54384cc8.replay.json
- `trial-0052` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/9d2ec184-2bf1-4af0-b587-52be948a3273.replay.json
- `trial-0053` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/1489a472-32e0-41bd-8d24-7a1f1ce9bed4.replay.json
- `trial-0054` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/ce206729-014f-4afb-ab7d-2e3d5fbc48a8.replay.json
- `trial-0055` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/63ea0310-9b53-4e75-8132-7d93e0aefe7c.replay.json
- `trial-0056` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/6d12c4e6-f9ae-4cc9-af3b-51067e17bed4.replay.json
- `trial-0057` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/89cf05ea-6a47-4222-9c79-2661d5a39190.replay.json
- `trial-0058` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/027a189a-871d-44a7-9194-f2ead1b8c331.replay.json
- `trial-0059` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/30610e12-7096-41ef-bdde-f08c0a951bac.replay.json
- `trial-0060` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/f4fea0ca-24fe-4b16-b4a9-8aade6eafb1d.replay.json
- `trial-0061` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/2ea32651-d02d-47a9-8aca-ebb2f522507c.replay.json
- `trial-0062` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/75ca66a6-98a0-4ff8-9c45-275c3763fd33.replay.json
- `trial-0063` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/d7506be2-9629-474f-b574-8f2d2fd7bd76.replay.json
- `trial-0064` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/f042d938-5653-44da-81f7-012b1ee601d1.replay.json
- `trial-0065` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/8c74fac1-14b0-4e8a-ab61-b553fa0a61ef.replay.json
- `trial-0066` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/044b3277-3e5f-441d-9dcf-484e1b7d70b3.replay.json
- `trial-0067` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/eb49e44f-b7a8-41b3-9f6c-742c183b31e8.replay.json
- `trial-0068` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/58d6dffc-cd7a-4f9c-ba44-2606c35d113d.replay.json
- `trial-0069` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/023b46fa-b692-4c3f-bbed-adb9cdbb35c6.replay.json
- `trial-0070` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/a614409e-842b-4323-98f7-e222a5379ad7.replay.json
- `trial-0071` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/4db72e66-4f91-49ae-84db-56a6e291b1d3.replay.json
- `trial-0072` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/210da7ab-e25a-4952-a4cb-54b8b70c8655.replay.json
- `trial-0073` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/5a4ab056-d930-4a32-97c9-013f9c400710.replay.json
- `trial-0074` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/6abdf78b-b17d-4a95-be69-1855024a2ebb.replay.json
- `trial-0075` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/921ad3b0-d11e-413a-9973-25cb3a31089e.replay.json
- `trial-0076` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/19fedd5a-4e11-4147-a0cb-843720870695.replay.json
- `trial-0077` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/03a536bc-2178-410a-96c4-dc08bb7a3601.replay.json
- `trial-0078` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/692276e2-ea1e-4d22-90bc-6aca4077bfd6.replay.json
- `trial-0079` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/6ca0a63e-289b-435b-a8a3-eaef722962bd.replay.json
- `trial-0080` (S-SLOW/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/76cfcca2-a62e-42ce-8c14-4a25a8f63099.replay.json
- `trial-0081` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/898952c7-bf1b-4674-a3c3-dec64c045594.replay.json
- `trial-0082` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/fedad157-48d8-42d5-8026-ec89b106f4a8.replay.json
- `trial-0083` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/2e950299-0376-46b4-86b9-cb7de5a737a4.replay.json
- `trial-0084` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/a1eec0a0-89c0-4ad6-b62d-4723f9556d9b.replay.json
- `trial-0085` (S-SLOW/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/428de1e6-719f-46e0-8ffc-bde8bf5bffc8.replay.json
- `trial-0086` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/6992dc18-3c77-456f-815c-52f171948b9f.replay.json
- `trial-0087` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/7d525547-2e85-4906-acbb-3b16584f9e35.replay.json
- `trial-0088` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/0d675208-5628-44ec-a0bc-7a0a31c2f7c4.replay.json
- `trial-0089` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/fa788c4c-248d-4b3c-9f10-33c43465c5d4.replay.json
- `trial-0090` (S-SLOW/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/f549119c-e6cd-491e-9e60-aa03524652ab.replay.json
- `trial-0091` (S-DIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/0c14824c-d664-42b7-a791-f546760e5fa9.replay.json
- `trial-0092` (S-DIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/ddfff048-dedf-48a6-bcfa-bd4fb8d39a2a.replay.json
- `trial-0093` (S-DIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/96ccc285-e02a-45c9-8c88-71eaaa1132c3.replay.json
- `trial-0094` (S-DIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/b4bef28a-6c5e-4f22-9d7d-fad5a88afc15.replay.json
- `trial-0095` (S-DIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/b36a3040-34fb-48b9-9dfa-e4c68f6866a1.replay.json
- `trial-0096` (S-DIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/8eb33fe0-e646-4e30-a9f7-fabb06dde3ac.replay.json
- `trial-0097` (S-DIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/b2286a9b-a9c7-463e-bd3f-cf6634a75321.replay.json
- `trial-0098` (S-DIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/db822f37-1c14-4b1f-bda9-70b813f84a6f.replay.json
- `trial-0099` (S-DIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/070ddf29-53ee-4db8-adfe-7224d77743a5.replay.json
- `trial-0100` (S-DIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/6d0b1c63-6e01-4e1f-8917-b81491b34219.replay.json
- `trial-0101` (S-DIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/d78e664c-de43-4aae-9238-e89f052a9e8d.replay.json
- `trial-0102` (S-DIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/b03fd3df-4e47-433e-be1a-a4c12b094af5.replay.json
- `trial-0103` (S-DIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/6ebf5e73-11e5-4925-9238-12477f81ad00.replay.json
- `trial-0104` (S-DIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/123cf125-64c5-4d5a-8457-968a2457eb84.replay.json
- `trial-0105` (S-DIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/bb71f35d-0641-49bf-9196-1b3520d62438.replay.json
- `trial-0106` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/44bdd822-434c-4008-965c-b4a073061ebe.replay.json
- `trial-0107` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/2c7d0f54-be21-4bba-8d02-2797d207fb04.replay.json
- `trial-0108` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/7f27e4b0-d50f-4704-9936-7d6c95ab34fa.replay.json
- `trial-0109` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/aea773ea-9a4c-4809-bae2-f10b91247f78.replay.json
- `trial-0110` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/03ac4a4b-fefc-44b6-a507-66f265dd7f10.replay.json
- `trial-0111` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/b1c01a70-cc80-4e3a-8028-77a180c09ea6.replay.json
- `trial-0112` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/0a9b1a9b-1104-47dc-81bf-4f656a2590c0.replay.json
- `trial-0113` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/f81cf219-c5dc-4300-86a6-461b30639a9f.replay.json
- `trial-0114` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/74840357-4843-46f8-80e3-2e1d5e868a19.replay.json
- `trial-0115` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/1b39fe14-0e89-4e4d-808a-628723a6f4f3.replay.json
- `trial-0116` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/c1200b02-a6a8-487e-a0a4-b8c7bcb4e198.replay.json
- `trial-0117` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/b2637725-c9d4-4632-a87f-b8919a45033c.replay.json
- `trial-0118` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/1166fb13-4aef-4754-bdbb-0771c4a6699c.replay.json
- `trial-0119` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/1ad38226-4ef6-4d31-bcc4-3dff443a68e9.replay.json
- `trial-0120` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/c2c4eb16-8391-407a-aada-d33c86a16d78.replay.json
- `trial-0121` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/f6203c3e-d519-49f0-aa2e-4e247e1fab0b.replay.json
- `trial-0122` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/b251d0eb-8ad9-47d2-bf09-963796ad6247.replay.json
- `trial-0123` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/ef99ae72-9a6d-4574-98b4-c0c80848fbbf.replay.json
- `trial-0124` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/16168197-3136-45a0-a9b0-755a136acc60.replay.json
- `trial-0125` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/aef93e11-3e00-4982-9748-31ca20a7d777.replay.json
- `trial-0126` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/3a80969d-70c2-4d68-a68e-80e5743be255.replay.json
- `trial-0127` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/814bc21e-5f6f-4717-bda1-95ae119e3cd4.replay.json
- `trial-0128` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/192fec73-3c97-4caf-93bb-506cddde2c9e.replay.json
- `trial-0129` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/44e47b93-bc75-4933-bb13-48bb423204af.replay.json
- `trial-0130` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/c34c492d-a726-407e-be1c-9fa79b4b745c.replay.json
- `trial-0131` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/b44d01e3-d266-4ebe-8d33-e55731de36f5.replay.json
- `trial-0132` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/b75f5539-7534-4f61-8981-bf8204894798.replay.json
- `trial-0133` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/b6c488d1-0fe9-4cee-a439-4624a2e2e4b9.replay.json
- `trial-0134` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/d249a16b-f9c3-4da3-a072-90551e5bc427.replay.json
- `trial-0135` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/58465753-5d58-46e8-94ac-741823a0bcd0.replay.json
- `trial-0136` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/1233edea-60a2-40c8-9dfc-0c92f7376df3.replay.json
- `trial-0137` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/6a5f5f30-0d86-432f-a8ac-7d25ff2d2a1b.replay.json
- `trial-0138` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/c01ec731-f046-4dcc-a7e5-ef460daa2294.replay.json
- `trial-0139` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/81311f3c-b043-45ce-bcd1-221889d827ee.replay.json
- `trial-0140` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/1105aad3-2db8-4050-a326-dc3d991b9578.replay.json
- `trial-0141` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/ebb96ae8-5c3b-40e8-8cac-6a933f205fe8.replay.json
- `trial-0142` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/2acd866e-986f-4928-9d87-903249c4cb70.replay.json
- `trial-0143` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/62b89715-85fa-4232-a212-2ba3dadc7372.replay.json
- `trial-0144` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/e8b8c6d3-682a-41a4-8f3c-fdc7e52a4ca3.replay.json
- `trial-0145` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/0fd0047f-9e7e-4097-8ee2-659de4675be4.replay.json
- `trial-0146` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/cef43326-4a15-4830-a81b-5d0eecd92d2d.replay.json
- `trial-0147` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/e62b13c4-bd7d-4549-b403-5316857f39dc.replay.json
- `trial-0148` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/87e97efe-bded-4745-b42d-c66392733c9d.replay.json
- `trial-0149` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/7fa01882-fcb7-4781-bbf1-7db9a99e7a1f.replay.json
- `trial-0150` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/ecaa44e1-5e3c-443d-b163-9c2df9ebc456.replay.json
- `trial-0151` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/8a0f2c3c-93d9-4402-9741-c91594b2063c.replay.json
- `trial-0152` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/dd900385-bb38-4e3d-a450-d4cc8e222393.replay.json
- `trial-0153` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/00316df0-281d-4b44-9033-d8177428332b.replay.json
- `trial-0154` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/76f6e2b0-0cc2-4958-9531-b8cc3fb70136.replay.json
- `trial-0155` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/342398a5-8e76-4084-afb6-8b63d43adc54.replay.json
- `trial-0156` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/ae164c21-17ad-434e-b304-6a568aad574f.replay.json
- `trial-0157` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/371289ba-2e60-4362-9e5f-1d2a3766b849.replay.json
- `trial-0158` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/78c3034c-cdcb-4a40-8850-b027d698f4e0.replay.json
- `trial-0159` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/1fa62c6b-f196-4cc9-b963-712baf2dce9e.replay.json
- `trial-0160` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/97f5db54-646c-45b9-98f2-613b9a9be00d.replay.json
- `trial-0161` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/0a77be35-979b-4e76-bd4a-27145d77a72d.replay.json
- `trial-0162` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/f8793c59-d768-468a-9f62-e0ff9e655ac4.replay.json
- `trial-0163` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/a9bf92af-cca2-4cf7-aa0d-57b7de70fbf1.replay.json
- `trial-0164` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/95abfcac-4280-40a8-96e1-ce67ea25ebd7.replay.json
- `trial-0165` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/ff0c774b-dff6-4af4-8af1-563dc40beb8e.replay.json
- `trial-0166` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/32a23ea8-8f49-44d7-97f7-f2ed4fee7917.replay.json
- `trial-0167` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/abf6f0ba-e199-47bf-a5ba-aedf9bf7ea54.replay.json
- `trial-0168` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/51f12cdf-eaaf-4705-b08d-a4ebc255a8f2.replay.json
- `trial-0169` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/b14d1f53-7db5-4a87-a2e8-8d8da2a1e46a.replay.json
- `trial-0170` (S-SLOWDIS/I-PLAIN/baseline-a): artifacts/eval-20261028/traces-baseline-a/3ce2e403-30f5-47ec-851f-40f62d983745.replay.json
- `trial-0171` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/54068f0e-d350-4d16-86a2-226685cb9562.replay.json
- `trial-0172` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/efb469f8-2577-44ea-8689-e6a3d833cbf1.replay.json
- `trial-0173` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/858cfbd8-83d9-4819-a596-7a66711a3d51.replay.json
- `trial-0174` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/904af375-f3fa-4177-a6b5-640c74f1c2af.replay.json
- `trial-0175` (S-SLOWDIS/I-SPACE/baseline-a): artifacts/eval-20261028/traces-baseline-a/5317408b-dafe-40f6-af66-141511f31894.replay.json
- `trial-0176` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/f7ba3405-f614-4dfe-b181-8056f62e395c.replay.json
- `trial-0177` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/5bf12381-c4e8-4378-9f5c-5af860aecb75.replay.json
- `trial-0178` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/39ea78d5-6df0-41d1-a9b8-c3c2b0996903.replay.json
- `trial-0179` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/8a1f2f83-c48c-46bf-ab3a-465bbd285ef1.replay.json
- `trial-0180` (S-SLOWDIS/I-UNICODE/baseline-a): artifacts/eval-20261028/traces-baseline-a/8e220856-d2f8-4984-981d-f0e15496c9bb.replay.json
- `trial-0001` (S-NORM/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/449dd1c8-4cce-4a74-90a3-ef08a0fe9d28.json
- `trial-0002` (S-NORM/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/da014b26-3648-4795-a8a1-6f0810ea80bb.json
- `trial-0003` (S-NORM/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/47351c40-30d6-48f8-ac0b-d58ec8c38da8.json
- `trial-0004` (S-NORM/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/3094b314-db6c-46fc-ae67-a20ae7c027ca.json
- `trial-0005` (S-NORM/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/310e10cd-2398-47e1-b948-cf80fda4934c.json
- `trial-0006` (S-NORM/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/391c7849-f7a5-4d27-b69f-5f933b3e8ac1.json
- `trial-0007` (S-NORM/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/9be75697-3c6c-49f7-979a-b3a1ef392ea2.json
- `trial-0008` (S-NORM/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/25084547-4d58-47fb-abcd-fe076af17a87.json
- `trial-0009` (S-NORM/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/90b8f372-b812-423b-a2ff-db8504725e93.json
- `trial-0010` (S-NORM/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/6e5d4e49-dae5-4b4a-af5d-fce59460e404.json
- `trial-0011` (S-NORM/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/e0ca1dc7-a2b8-45f3-94e7-aacdce841d03.json
- `trial-0012` (S-NORM/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/bb7794f3-1a66-4ac3-bf20-1ab3cbf11092.json
- `trial-0013` (S-NORM/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/ce948062-a7bd-4392-a9a8-c484c05c9c11.json
- `trial-0014` (S-NORM/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/ed680e8a-8652-4131-ab19-e347a1934b64.json
- `trial-0015` (S-NORM/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/976bd78b-b4b8-49d6-9bd7-d7e543f8ee90.json
- `trial-0016` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/d350802c-34ac-477f-bdae-3aded89b2a5b.json
- `trial-0017` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/196468a1-451d-4fac-9e7e-35807f1e52eb.json
- `trial-0018` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/7905b6c1-e26f-499c-97b6-24d9cbce3949.json
- `trial-0019` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/3d5bd1c6-47d0-4f60-9c25-be7b2d0263dc.json
- `trial-0020` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/5c875c32-d262-48c6-8820-46b087090885.json
- `trial-0021` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/e1bebe4b-f16c-4596-b772-a39416187ec3.json
- `trial-0022` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/178592f7-cd9e-4561-a26d-dcafb811abb2.json
- `trial-0023` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/33777254-cf75-4cc4-a348-c27c622d9aad.json
- `trial-0024` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/7b0262f4-547c-45ab-9c77-2761a70b1d80.json
- `trial-0025` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/ca041e60-38fd-4e0f-a53c-4663a58f86de.json
- `trial-0026` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/b101e420-1046-48a4-adbe-f379e6e42040.json
- `trial-0027` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/505a0e0a-db81-4c18-a67c-5d3b3abf73a1.json
- `trial-0028` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/59647f6f-da4b-4434-87e7-12ac898ef24b.json
- `trial-0029` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/5f4b5297-d15b-46a5-8f88-94e9a8e2df69.json
- `trial-0030` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/8729bffe-aaae-48d9-942f-b175e0ef50ed.json
- `trial-0031` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/12c6c5d2-784c-4d2f-8520-d8ad9462975d.json
- `trial-0032` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/a8de7652-3dc5-40cb-b360-c43dfd26cc57.json
- `trial-0033` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/7452ef59-3a50-4a36-8120-d2ddb460a26e.json
- `trial-0034` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/f0351701-656b-464e-9e33-13c7c5e1bd99.json
- `trial-0035` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/8869d9fd-65b8-4221-aadb-1b1839f029a0.json
- `trial-0036` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/b5194017-6ce1-4e2d-aa2a-639e3cc8b18a.json
- `trial-0037` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/cb645720-2980-4c2e-98e7-d61e5be56281.json
- `trial-0038` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/cc2906e8-e986-4b25-958d-170038206be7.json
- `trial-0039` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/563bd3ca-c81c-4f2a-aa2e-d662574b0630.json
- `trial-0040` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/72f9b032-32e4-4ce1-a437-ebd3203bea21.json
- `trial-0041` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/98160735-1b96-45f4-8619-e37d1179096e.json
- `trial-0042` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/4dcd44a7-c82d-4d7f-9d10-e2079be2b4ed.json
- `trial-0043` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/6bf177f7-7dd8-47f5-a121-ce64f92010cf.json
- `trial-0044` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/c5fbf5c2-0834-4464-b3c0-ba5ce57c3213.json
- `trial-0045` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/3d040f5f-d6b6-4cf4-b244-9c30880d68c2.json
- `trial-0046` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/f2661dd5-3a88-4168-bcce-a5f2b0771e5f.json
- `trial-0047` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/bb17111d-9e1e-42f3-a537-83f4d0324d89.json
- `trial-0048` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/1878f7c6-8db3-4b6d-a49b-f373defab5a9.json
- `trial-0049` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/88966295-b674-4fd2-9423-592fc31437e4.json
- `trial-0050` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/ef3cacc3-981d-4e7f-b319-f86a3eccc63f.json
- `trial-0051` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/ffb591b4-d4a8-43e5-9567-2004ff35431b.json
- `trial-0052` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/d0da126b-75f0-4aba-9ea3-00499e16fedf.json
- `trial-0053` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/1f7d7bf3-f3a4-4f8c-9589-ff977a389fbc.json
- `trial-0054` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/13e13e9f-e47c-41de-b02d-7a440ef3dc2d.json
- `trial-0055` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/be95d9fb-aaf7-4aab-a1c8-1e2b45e2d56b.json
- `trial-0056` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/1434c250-fcc9-4873-9613-36daec3b6ae9.json
- `trial-0057` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/a10cdf45-02d5-448b-8e4b-0968ce626d4b.json
- `trial-0058` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/b2ef138c-e6ea-4e6c-b785-2b94a70fdbb7.json
- `trial-0059` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/0101cfc0-78cd-4775-96bc-625636eb2fca.json
- `trial-0060` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/6396eee6-2629-436a-86c2-b68cfd079ad4.json
- `trial-0061` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/519778e4-2e81-4acb-bb7f-343d7cf1c44b.json
- `trial-0062` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/36061b5e-79b3-4b16-8e68-91c2640c3e1c.json
- `trial-0063` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/aa2efd5e-45a8-4918-9926-a4fec020ef09.json
- `trial-0064` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/91aab1ff-7a51-4508-a086-314dab44e094.json
- `trial-0065` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/9b746fec-9b83-4e66-80d5-b259be36d69d.json
- `trial-0066` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/d5c3f8c9-1435-414f-90c1-832e1865d063.json
- `trial-0067` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/16e5c32a-e9f0-466c-b365-d628348d7eff.json
- `trial-0068` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/8a54aa61-b9a8-4708-9d80-8cc7fe4ce62c.json
- `trial-0069` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/ed9760c9-6f64-487d-8c53-7442adce3212.json
- `trial-0070` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/595c4215-1220-4afb-891f-3fb45f28a696.json
- `trial-0071` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/b6ef1467-74d2-47f8-8ae3-b78e0303edb1.json
- `trial-0072` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/638e8981-f87f-42d8-8c07-3b1bf90a857a.json
- `trial-0073` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/3418aadc-9e42-455c-9ec0-cc17e49590cd.json
- `trial-0074` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/093af616-a20b-4f0b-af11-d22fef595840.json
- `trial-0075` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/6fd38165-3db4-40f7-9ced-a8891c5e6878.json
- `trial-0076` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/30549452-acf3-42f1-8758-9c2fa59fd379.json
- `trial-0077` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/5821b25f-4bf9-49df-8977-8c882213a360.json
- `trial-0078` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/e4d6b39f-8381-4ea5-99c1-c55e6e8c7ef0.json
- `trial-0079` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/da0793ac-587f-43a1-bc55-7702ecc51d1f.json
- `trial-0080` (S-SLOW/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/4f6f6a59-21f0-49ca-98fa-c1845d5938ec.json
- `trial-0081` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/d3195113-0973-4c04-b1cb-7cb8b8b27be1.json
- `trial-0082` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/b6ae0743-b74b-4a67-a56d-4b0f49ee8bfe.json
- `trial-0083` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/411a0091-6c6a-4ab4-8739-e59d3eab0efd.json
- `trial-0084` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/87785f48-2b64-49f8-a353-e5067136c983.json
- `trial-0085` (S-SLOW/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/06ac89ec-532e-4c91-8711-aa5173bd19aa.json
- `trial-0086` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/6d05a938-4c95-412f-beb5-a46eb9cebc4d.json
- `trial-0087` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/58417b50-c7d4-4e57-ac72-72fbd59bf441.json
- `trial-0088` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/8456e3a1-46f9-4087-b02a-ab09f9593008.json
- `trial-0089` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/305f07ad-addb-4b5b-a7fc-6581f3b0c74b.json
- `trial-0090` (S-SLOW/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/224063ad-e95e-4d1b-837a-aa111cbf808d.json
- `trial-0091` (S-DIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/4bb74591-1788-470d-ad1d-3f79c0109027.json
- `trial-0092` (S-DIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/c9e80ad4-c651-424c-ad48-92d5858ec986.json
- `trial-0093` (S-DIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/e75b7100-9785-4518-8069-825126825dc2.json
- `trial-0094` (S-DIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/fd0b6598-9257-4cc9-b4ec-7ec18191fb49.json
- `trial-0095` (S-DIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/6d036763-61cd-45e2-809d-cd7e1f119e5f.json
- `trial-0096` (S-DIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/307425a4-3483-4641-aa3a-68c928495a2f.json
- `trial-0097` (S-DIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/5a1f1445-5242-4350-a0dd-68b82cba748b.json
- `trial-0098` (S-DIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/ce403f69-3c76-4578-9072-f5c3d94c2347.json
- `trial-0099` (S-DIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/5a4226f1-8a40-4d7d-bd20-7b85d0ebef6c.json
- `trial-0100` (S-DIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/a763e65d-273f-47aa-a128-e188bebf55d7.json
- `trial-0101` (S-DIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/c82c4aa8-45d8-4e11-af70-19ba85796732.json
- `trial-0102` (S-DIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/90f622d9-ceeb-48da-b1b0-bf2732b80915.json
- `trial-0103` (S-DIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/e4aa350a-f7bd-43c0-8410-63c0d0cfc12a.json
- `trial-0104` (S-DIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/2aa1082e-a73f-400f-bb97-78aa27d5c016.json
- `trial-0105` (S-DIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/68626487-6b02-4e30-8668-e9d9fa404ddd.json
- `trial-0106` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/8c05c538-adc7-43ed-843e-0906d86f4341.json
- `trial-0107` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/3c5ab3b5-7896-40b3-8e49-a5d62ce105a5.json
- `trial-0108` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/719cb377-bc66-40b9-b657-8eb95de23277.json
- `trial-0109` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/79f727e1-b4b4-4ef5-aaaf-043cbd4a4c69.json
- `trial-0110` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/ffd13df5-d303-4e02-a8cf-f52a6d9267f6.json
- `trial-0111` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/f1580323-39ae-4194-b82e-eb8e63b4e2a8.json
- `trial-0112` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/6074dc37-b914-4606-8e8b-9144812e6dbd.json
- `trial-0113` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/cc85e316-6feb-4731-94e2-34a24bc94416.json
- `trial-0114` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/05f813c6-968c-44b9-9c5b-2f5501739991.json
- `trial-0115` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/58fd4a9a-806c-4ad4-bdca-ebf07435a88a.json
- `trial-0116` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/2713def2-e536-4373-917f-2e3865435c30.json
- `trial-0117` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/b6f8d439-dca4-422e-b2d7-439b4587fb01.json
- `trial-0118` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/b78d25e1-caa4-48c7-89f2-59ec3720d0ae.json
- `trial-0119` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/a9895f6e-d045-483d-a920-7fc53d73c8ec.json
- `trial-0120` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/f3d8c2ee-a5fc-4c96-b37e-cde63996a5b1.json
- `trial-0121` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/07c3deef-8f5c-4eb9-8545-4d2c6710e654.json
- `trial-0122` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/36e27b0b-3f43-4817-8c24-4a7438dc044b.json
- `trial-0123` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/ff67c88b-768d-4165-984e-05a2242973cc.json
- `trial-0124` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/d86101ea-ee55-485a-ab30-91dc1d1eb0a0.json
- `trial-0125` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/d97810ad-093b-4451-9f24-029f0a43906d.json
- `trial-0126` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/65c3de31-d500-4b8c-ba7e-ba64734d527c.json
- `trial-0127` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/2ebbf3d4-75c2-41c3-9ce5-e4f7ce61c586.json
- `trial-0128` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/743366fe-dbab-4742-a1cf-f7f88c9a686d.json
- `trial-0129` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/106e1722-f097-44ce-a19d-5e2811c15b9a.json
- `trial-0130` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/1550c0c8-b287-4f23-81d6-d874ed614d8b.json
- `trial-0131` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/b70bf19a-6eef-4ff3-93e6-f2bb6cab4c69.json
- `trial-0132` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/210750bd-1fdd-4c5c-aab1-de679025e9d4.json
- `trial-0133` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/4825292d-89ad-478c-bc88-43fee0dfb593.json
- `trial-0134` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/5f68c503-8c73-428d-8b80-f88cf1055d06.json
- `trial-0135` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/e1edabc7-a557-4a81-b91c-56571b33d77a.json
- `trial-0136` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/33f28145-42eb-4eb5-9d40-a07ee0a34b15.json
- `trial-0137` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/c4c838fb-543e-436c-b02e-3d1d7f2c2c61.json
- `trial-0138` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/ad63c6e0-349b-4969-bd28-6f383c2a1332.json
- `trial-0139` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/53f07042-a34d-4176-8449-641cdd1551f2.json
- `trial-0140` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/262b417f-8e18-403e-a6e6-dfc6f4808a9b.json
- `trial-0141` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/a0698b17-7b96-44a9-9538-f2e4e2cbbe6f.json
- `trial-0142` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/3c91e2a3-e1b9-4db5-bf54-e509bcb38e45.json
- `trial-0143` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/422445d3-4705-455c-bb19-5e62a820c550.json
- `trial-0144` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/03a942b7-3c88-44b5-b329-e6fb358a8d75.json
- `trial-0145` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/aa567fb3-066c-4250-a65c-dd106415a53f.json
- `trial-0146` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/1c74d1ee-be66-4607-886b-945ac3411873.json
- `trial-0147` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/4a1b887b-7800-48b2-b4df-bc6201c28836.json
- `trial-0148` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/bf052213-f8d8-4dfa-9cae-ceffe288ba11.json
- `trial-0149` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/9c894690-4b6c-4657-9985-b92eaf90a734.json
- `trial-0150` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/f3c2fd72-0a92-48a7-9e36-12750ee0a147.json
- `trial-0151` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/510c5a2a-14eb-4c23-8b08-3ece817bb5cf.json
- `trial-0152` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/1c8a8f69-fd6e-4462-b72b-184dff8a291b.json
- `trial-0153` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/c0c41847-dbe2-4c48-8ded-7d52a16a6b6f.json
- `trial-0154` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/60e27849-3263-4345-88fa-28f7411104a6.json
- `trial-0155` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/57e2cff5-3726-4932-9626-142f203c6a6f.json
- `trial-0156` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/2604a02f-aa7d-4e00-ab64-f8b986a0cd2a.json
- `trial-0157` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/4d817455-f562-4fb2-8e04-2db9c6c07ea0.json
- `trial-0158` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/84c68d47-0353-4185-9861-dacb9677b125.json
- `trial-0159` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/d04fc6bc-4510-493b-80c0-7473d16fbc26.json
- `trial-0160` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/9adfd349-8638-4af4-b0a6-92df25ed8302.json
- `trial-0161` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/a2e0bf13-efd9-48f4-adb9-a501a922eb8a.json
- `trial-0162` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/5a9d6102-617e-442a-b526-5aaeb765e639.json
- `trial-0163` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/20fc0b05-96ec-4b73-be06-436126f5d829.json
- `trial-0164` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/c46e4041-2adb-4a8f-937b-c97ecdbd6377.json
- `trial-0165` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/4cde7cf6-81e5-41d2-89dd-9ce666744fdf.json
- `trial-0166` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/2cd4abb3-0f9e-4735-adb6-bfc15cefddee.json
- `trial-0167` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/1cbdbb49-e6e8-435d-9d5b-9cd3e020ba02.json
- `trial-0168` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/010bffad-4311-4a0c-9af5-203b50989453.json
- `trial-0169` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/66a26c92-36d7-46dd-b25c-645570845ff4.json
- `trial-0170` (S-SLOWDIS/I-PLAIN/chimera): artifacts/eval-20261028/traces-chimera/c1412559-b255-4d3b-87e7-6c6144a07ae7.json
- `trial-0171` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/2779e097-de1e-426f-8ae0-e92d5c734768.json
- `trial-0172` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/a619bc7e-c94f-4e91-99dd-a7ba5a666b2d.json
- `trial-0173` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/4095bb50-1e8f-4d45-b042-74a9146cf839.json
- `trial-0174` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/eaa152db-bbd0-430a-a1fa-23beff55d82a.json
- `trial-0175` (S-SLOWDIS/I-SPACE/chimera): artifacts/eval-20261028/traces-chimera/9f8027d2-279f-49cc-903a-4b2ec85914b5.json
- `trial-0176` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/49b8ee20-5da4-4e3c-b0ee-8bd6b375c8b3.json
- `trial-0177` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/75b5b780-ae87-4374-ba72-625b0f25ef27.json
- `trial-0178` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/6b83cc95-ca96-4d58-ac48-08fb1c464a80.json
- `trial-0179` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/fda8daa7-5403-4bcb-8de1-3385903feb3c.json
- `trial-0180` (S-SLOWDIS/I-UNICODE/chimera): artifacts/eval-20261028/traces-chimera/6f3a484b-f0f8-45f6-8a52-f8d13b031c07.json

<!-- rendered by chimera-report/1 -->
