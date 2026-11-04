# Errata — development runs `dev-20261028`

Added 2026-11-04. The run files, audit plans, traces and both rendered
reports in this folder are **frozen evidence** and are not edited. This note
corrects statements inside them. The held-out errata
([`../eval-20261028/ERRATA.md`](../eval-20261028/ERRATA.md)) give the full
reasoning; this file lists what applies to the development split. Figures
were recomputed from the run files here (warm-ups excluded).

- **Padded-name prediction falsified.** `docs/benchmark_design.md`
  lines ~103–106 predicted that `I-SPACE` (`"  Alpha  "`) would cause a false
  failure. Chimera succeeded on `I-SPACE` 5/5 in S-NORM and 5/5 in S-SLOW,
  with 0 verifier disagreements.
- **Retries never fired.** The `retries` metric is 0 in all 80 measured
  Chimera episodes. The S-SLOW gap (Chimera 20/20 vs replay 0/20) comes from
  the 5000 ms vs 100 ms per-action budget; at a matched 5000 ms budget replay
  agreed with Chimera on 20/20 pairs
  (`experiments/matched-budget-v1/REPORT.md`).
- **Stale "Limitations" lines** in `report.md` and `report-audited.md`
  (lines ~349–375): there were **80** measured episodes per run (16 cells × 5
  trials), not "10–30"; Baseline A **is** implemented and is
  `run-baseline-a.json`; the measured S-NORM median is about **318 ms**, not
  "≈0.12 s".
- **Stale run-file note.** Both run files say "Baselines A/B are not
  implemented". Baseline A was implemented and run; the note is runner
  boilerplate from before it existed.
- **Audit provenance.** The audit plans' `auditor` field is empty. The
  64-episode dev audit (64/64 agree, verdict AUDITED) was adjudicated by the
  author. Auditors read the same harness snapshots the verifier reads, so the
  audit cannot detect a faulty snapshot.
- **False-success denominator.** Chimera claimed success in 40 of its 80
  dev episodes; the verifier refuted 0 (95% Wilson upper bound 8.8%).
