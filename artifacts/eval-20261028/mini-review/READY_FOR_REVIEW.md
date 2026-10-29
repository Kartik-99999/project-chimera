# READY FOR REVIEW — eval mini-audit evidence bundle

Status: **prepared, 0/8 human decisions recorded — the audit is NOT
complete.** No human judgments exist in this directory; nothing here
adjudicates on its own.

## Frozen selection (do not alter)

Eight episodes from `run-chimera.audit-plan-mini.json` and
`run-baseline-a.audit-plan-mini.json`, one per scenario per baseline
(all `I-SPACE`, expected stored name `"Padded Name"`):

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

Manifest `benchmarks/manifests/eval-v1.json`, canonical sha256
`b23580c8c07c3528a33f10f25780138cd58455a1f334c48e4fd889125c038cf5`
(verified through the manifest loader at packet build; note this
is the loader's canonical hash, not a raw-bytes hash).

## Files in this directory

| File | sha256 | Purpose |
|------|--------|---------|
| `evidence-bundle.zip` | `2be304c8…` | 29 verified originals + `BUNDLE_MANIFEST.json` (24 trace/snapshot/action files, 2 failure screenshots, frozen manifest, both mini plans) |
| `packet.json` | `881a5323…` | Complete packet (evidence AND answers) — operator only |
| `reviewer-packet.json` | `a58e5fb0…` | Reviewer-safe packet (evidence, no answers) |
| `answer-key.json` | `67d8cddb…` | Recorded outcomes + verifier checks — withhold until locked |
| `PACKET.md` | `771d4634…` | Human-readable packet (contains answers) — operator only |
| `decisions.json` | `1f40ef6a…` | Human decisions store — currently all pending |

(Full hashes: see validation output below; verify with
`sha256sum -c` against your copy.)

## Distribution rules (independent review)

**Send the reviewer ONLY:**

- `reviewer-packet.json`
- the 24 trace/snapshot/action files and 2 screenshots, extracted
  from `evidence-bundle.zip` by their listed paths

**Withhold until all 8 initial decisions are locked:**

- `answer-key.json`, `packet.json`, `PACKET.md`
- both `*.audit-plan-mini.json` files (their `sampled` entries
  record outcomes and verifier checks)
- `decisions.json` and any prior assessment
- `artifacts/eval-20261028/mini-review.zip` (a Finder-made copy
  of packet + PACKET.md + decisions — contains answers; never
  send it to the reviewer pre-lock)

## Two-phase protocol (enforced in `#/review`)

1. **Phase 1 — blinded:** inspect the evidence and record the
   assessment (verified success / verified failure /
   inconclusive), sufficiency, reason, and any missing evidence.
   The assessment is the reviewer's overall P1–P3 judgment
   (verified success ≡ the reviewer finds P1∧P2∧P3 hold on the
   evidence). The Reveal control does not exist until the
   assessment is saved.
2. **Phase 2 — agreement:** reveal the recorded outcome and
   verifier checks, then record agrees / disagrees /
   undetermined. Revisions append to a corrections history.

**No cryptographic blinding is claimed.** The console is served
over static HTTP; anything served to the browser (including the
full packet backing `#/review`) is inspectable by a determined
reviewer. The in-app masking enforces review *order*, not
secrecy. True independence requires the distribution rules
above: reviewer works from the reviewer-safe packet + evidence
files only.

Blinding is also partial by evidence shape: run IDs stay visible
for lookup, and Chimera event traces vs Baseline A replay reports
differ structurally, so driver identity may be inferable. Judge
the postconditions, not the driver.

## Exact reviewer steps

```bash
cd /Users/kartikbhardwaj/project-chimera
.venv/bin/python -m http.server 8123
# open http://127.0.0.1:8123/research/#/review
```

1. Enter your reviewer name on the queue page.
2. Open episodes 1–8 in any order; assess blinded, reveal,
   complete. Status must reach 8/8 reviewed.
3. Export `decisions.json`; save it over
   `artifacts/eval-20261028/mini-review/decisions.json`.
4. Run `.venv/bin/python tools/mini_review.py validate` — it must
   report valid and COMPLETE. Anything else is not done.

## Validation performed (2026-10-29)

- `build-packet`: 8 episodes, 24/24 artifact digests + byte
  counts verify, plan↔run outcomes/checks agree, manifest
  canonical sha verified. (Prior run; packet bytes unchanged
  since — see hash above.)
- `build-bundle`: 29 files verified (24 artifacts + 2
  screenshots + manifest + 2 plans), deterministic zip
  (byte-reproducible; rebuilt twice identically in tests).
- `build-reviewer-packet`: reviewer packet contains zero
  answer-revealing keys (scan-enforced: no `recorded`,
  `verifier`, `decisions`, `verdicts`, `assessment`,
  `agreement`, `all_satisfied`, `satisfied`,
  `agent_terminal_status` at any depth); packet bytes proven
  unchanged across the split.
- `validate`: decisions file valid, **0/8 IN PROGRESS**;
  evidence freshness re-verified (frozen bytes match packet
  digests).
- Suites: `tests/test_mini_review.py` 9 passed; Node console
  suite 62 passed; console browser suite 30/30 green
  (unsandboxed), including the enforced two-phase review flow.
- Episode identifiers, manifest, and plan hashes re-confirmed
  unchanged; `decisions.json` pending and untouched by tooling.

## Limitations and gaps

- Successes carry no screenshots (the harness captures one
  only on action failure); the two failure screenshots are
  bundled and linked.
- Replay reports (Baseline A) carry step indexes only — no
  timestamps or trace sequence numbers.
- Eight episodes describe only themselves: agreement counts
  support no reliability claim; the 95% provisional rule
  (user guide §15.1 step 4) applies to full audits, not here.
- Boot fetch retries (one) cover transient static-server
  drops; persistent load failures still surface in the
  console footer and degrade views visibly.
