# Eval mini-audit report — 8-episode human adjudication

**Status:** complete. **Scope:** the 8 frozen mini-review episodes only.
This report adjudicates no run, changes no verdict file, and makes no
reliability claim. The held-out evaluation stays **provisional**.

## 1. Purpose, selection, methodology, provenance

**Purpose.** Independently check the independent verifier's P1–P3
decisions on a small, frozen, human-manageable sample of held-out
eval episodes: one episode per scenario per baseline.

**Frozen selection** (from `run-chimera.audit-plan-mini.json` and
`run-baseline-a.audit-plan-mini.json`; all `I-SPACE`, expected
stored name `"Padded Name"`):

| # | Episode key | Condition |
|---|-------------|-----------|
| 1 | `eval-20261028-baseline-a::trial-0009` | S-NORM |
| 2 | `eval-20261028-baseline-a::trial-0052` | S-SLOW, slow_ms=2100 |
| 3 | `eval-20261028-baseline-a::trial-0098` | S-DIS, disabled |
| 4 | `eval-20261028-baseline-a::trial-0143` | S-SLOWDIS, slow_ms=2100 + disabled |
| 5 | `eval-20261028-chimera::trial-0006` | S-NORM |
| 6 | `eval-20261028-chimera::trial-0055` | S-SLOW, slow_ms=2100 |
| 7 | `eval-20261028-chimera::trial-0100` | S-DIS, disabled |
| 8 | `eval-20261028-chimera::trial-0142` | S-SLOWDIS, slow_ms=2100 + disabled |

**Methodology.** Two-phase blinded protocol in the console
Mini-review queue (`#/review`), per
`READY_FOR_REVIEW.md`: Phase 1 — judge P1–P3 from the evidence
with recorded outcomes masked, record assessment / sufficiency /
reason (assessment `verified-success` ≡ reviewer finds P1∧P2∧P3
hold); Phase 2 — reveal recorded outcome and verifier checks,
record agreement. Timestamps prove the order
(`assessed_at < revealed_at` for all 8, verified below). No
reveal control exists before the assessment is saved; revisions
would append to a corrections history (none were needed).

**Provenance** (sha256, verified 2026-10-30; packet/payload hashes
match the `READY_FOR_REVIEW.md` record; `decisions.json` hash is
new because it now holds the 8 recorded decisions):

| File | sha256 |
|------|--------|
| `packet.json` | `881a5323aa72f508e97da23c6499a4d2bd20e174ac0132a20055301969251019` |
| `decisions.json` | `5c8259e213d34ec12c35de682ec085478c8b5bd960a82e7c2520075798cff362` |
| `reviewer-packet.json` | `a58e5fb07c661100a8a36de5baa16988c6463d37327c2558878783f291f667a4` |
| `answer-key.json` | `67d8cddbcfd0fa0e511da9883f7f914f154a3df31c5e7ba761df340cb1d788cd` |
| `evidence-bundle.zip` | `2be304c083e93c000b31e91c640d03b72a8758b9868a59836d48976aed79324c` |
| `benchmarks/manifests/eval-v1.json` (loader canonical) | `b23580c8c07c3528a33f10f25780138cd58455a1f334c48e4fd889125c038cf5` |

Reviewer: **Kartik**. Review window (UTC 2026-10-30):
first assessment 05:55:16, last reveal 06:21:41, decisions
exported 06:24:18. All 8 decisions `blinded: true`, no corrections.
`decisions.json` records `packet_sha256 881a5323…`, matching the
packet on disk — the judgments apply to exactly this packet.

## 2. Per-episode results

Recorded outcome / verifier P1–P3 come from `packet.json`
(verifier `independent-verifier-1.0`, all `status: verified`);
human columns come from `decisions.json`.

| # | Episode | Recorded | Verifier P1–P3 | Human assessment | Agreement | Evidence |
|---|---------|----------|----------------|------------------|-----------|----------|
| 1 | baseline-a trial-0009 (S-NORM) | succeeded | T,T,T | verified-success | agrees | sufficient |
| 2 | baseline-a trial-0052 (S-SLOW) | failed | F,F,F | verified-failure | agrees | sufficient |
| 3 | baseline-a trial-0098 (S-DIS) | failed | F,F,F | verified-failure | agrees | sufficient |
| 4 | baseline-a trial-0143 (S-SLOWDIS) | failed | F,F,F | verified-failure | agrees | sufficient |
| 5 | chimera trial-0006 (S-NORM) | succeeded | T,T,T | verified-success | agrees | sufficient |
| 6 | chimera trial-0055 (S-SLOW) | succeeded | T,T,T | verified-success | agrees | sufficient |
| 7 | chimera trial-0100 (S-DIS) | failed | F,F,F | verified-failure | agrees | sufficient |
| 8 | chimera trial-0142 (S-SLOWDIS) | failed | F,F,F | verified-failure | agrees | sufficient |

Human reasons (verbatim substance): successes were judged on
snapshots showing `confirmation_visible=true` with exactly one
list entry exactly equal to `"Padded Name"`; failures on
snapshots showing `confirmation_visible=false` with an empty
list, corroborated by failed-fill traces (Chimera) or replay
TimeoutErrors (Baseline A). Full reason strings are in
`decisions.json`; `missing_evidence` is empty for all 8.

## 3. Human vs verifier comparison

**8/8 agreement, 0 disagreements, 0 unauditable, 0 inconclusive.**
Every human assessment matches the verifier's conjunction, and
every recorded outcome matches the human assessment (no false
successes and no false failures in this sample — descriptive of
these 8 episodes only). Validator output:

```
Mini-review: 8/8 recorded · reviewer: Kartik
Status: COMPLETE — 8/8 human decisions recorded.
```

## 4. Condition-level observations (Baseline A vs Chimera)

One episode per cell — each row below describes a single
observed episode, not a condition rate:

| Condition | Baseline A (replay) | Chimera (agent) |
|-----------|---------------------|-----------------|
| S-NORM (no fault) | trial-0009 succeeded (315 ms) | trial-0006 succeeded (338 ms) |
| S-SLOW (slow_ms=2100) | trial-0052 **failed** — 100 ms fill timeout (378 ms) | trial-0055 **succeeded** — fill completed in ~2.5 s (2,608 ms) |
| S-DIS (disabled) | trial-0098 failed — fill timeout on disabled input (386 ms) | trial-0100 failed — retry budget exhausted on disabled input (5,346 ms) |
| S-SLOWDIS (slow+disabled) | trial-0143 failed — fill timeout on disabled input (369 ms) | trial-0142 failed — retry budget exhausted on disabled input (5,308 ms) |

## 5. The S-SLOW split

On the single sampled S-SLOW pair (I-SPACE, slow_ms=2100),
Chimera's trial-0055 succeeded while Baseline A's trial-0052
failed. Mechanism, as recorded in the evidence: the replay
driver's fixed 100 ms fill timeout expired while the input was
still slow to enable; the Chimera agent's fill took 2,517 ms and
completed, followed by `verification_passed` events and
`run_succeeded`. This matches the replay driver's documented
design (fixed tiny timeout, no waiting). It is one pair of
episodes: it illustrates the mechanism, it does not measure a
rate difference.

## 6. Disabled-input failures in both approaches

All four sampled disabled-input episodes failed in both drivers
(trials 0098/0143 replay; 0100/0142 Chimera), each with an empty
project list and hidden confirmation. Failure signatures differ
honestly by driver: replay reports a single 100 ms
`TimeoutError` at the fill step (~370–390 ms episodes); Chimera
reports `RetryBudgetExhaustedError` after 2 fill attempts against
the 5 s action timeout (~5.3 s episodes). Both terminals
(`failed`) are the correct report when success is impossible —
bounded failure, not a crash.

## 7. Sufficiency and agreement counts

- Agreement: **8/8 agree** (4 Baseline A, 4 Chimera).
- Sufficiency: **8/8 sufficient**; `missing_evidence` empty
  throughout.
- Validator: `tools/mini_review.py validate` → valid, COMPLETE
  (see §3); packet/digest freshness re-verified at validate time.

## 8. Evidence limitations

- **Screenshots:** 2 of 8 episodes carry failure screenshots
  (Chimera trials 0100, 0142 — the failures with trace evidence).
  The 3 successes carry none (the harness captures a screenshot
  only on action failure); the 3 replay failures carry none (the
  replay driver takes no screenshots by design). The reviewer
  judged all 8 sufficient on snapshot + trace/replay evidence.
- **Replay reports** carry step indexes only — no timestamps or
  trace sequence numbers — so Baseline A episodes support
  coarser timelines than Chimera event traces.
- **Blinding is partial:** run IDs stayed visible for lookup and
  trace shape differs by driver, so driver identity may have been
  inferable; masking enforced review order, not secrecy (see
  `READY_FOR_REVIEW.md`).

## 9. Disclosure

The reviewer reports **prior exposure to AI-assisted
recommendations** relating to this evaluation. This adjudication
therefore does not claim an AI-unassisted independent judgment;
its safeguard is procedural, not causal: blinded Phase-1
assessment with reasons tied to specific snapshot/trace
observations, timestamped before reveal, with the full evidence
preserved for re-review.

## 10. What this audit does not establish

**Eight selected episodes do not establish statistical
reliability or generalization.** Agreement counts (8/8) support
no reliability claim about the verifier; per-condition
observations (n=1 per cell) support no rate or comparison claim
about either driver; nothing here transfers to other inputs,
fault levels, or tasks. The 95% provisional rule (user guide
§15.1 step 4) applies to full audits, not to this sample. The
full-run eval audit samples remain unadjudicated and the
held-out eval report stays **provisional**.
