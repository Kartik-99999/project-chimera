# Eval mini-review packet (8 episodes)

Created: 2026-10-29T16:01:31.836+00:00 · schema `chimera-mini-review-packet/1`.
This packet is a read-only view of frozen evidence plus empty decision slots. All judgments live in `decisions.json`, recorded only by a human reviewer.

Manifest: `benchmarks/manifests/eval-v1.json` (eval-v1, sha256 `b23580c8c07c3528a33f10f25780138cd58455a1f334c48e4fd889125c038cf5` — verified against the frozen file at packet build).

## Task and postconditions (benchmark_design §2)

Create a project with a given name. The agent must navigate to the target, fill the name, click "Create Project", and satisfy the postconditions.

- **P1** — Confirmation is visible: `#confirmation` is visible (judge: Is confirmation_visible true in the snapshot?)
- **P2** — The project appears in the list, exactly once: exactly one `#project-list li` whose `textContent` equals the expected trimmed name (judge: Does items contain exactly one entry whose text equals the expected stored name?)
- **P3** — The list contains no unexpected entries: the count of `#project-list li` equals 1 (judge: Does items contain exactly one entry?)

P4 (list empty before the agent's click) is harness-only context; the audit judges the verifier's P1–P3.

Recorded outcomes and verifier checks are masked during initial assessment in the review queue. Blinding is partial: trace structure differs between the Chimera driver (event trace) and Baseline A (replay report), so a knowledgeable reviewer may infer the driver from the evidence shape.

## Selection

1. `eval-20261028-baseline-a::trial-0009` — S-NORM/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `succeeded` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan-mini.json` cell `S-NORM|I-SPACE|baseline-a|disabled=False,slow_ms=0`
2. `eval-20261028-baseline-a::trial-0052` — S-SLOW/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan-mini.json` cell `S-SLOW|I-SPACE|baseline-a|disabled=False,slow_ms=2100`
3. `eval-20261028-baseline-a::trial-0098` — S-DIS/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan-mini.json` cell `S-DIS|I-SPACE|baseline-a|disabled=True,slow_ms=0`
4. `eval-20261028-baseline-a::trial-0143` — S-SLOWDIS/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan-mini.json` cell `S-SLOWDIS|I-SPACE|baseline-a|disabled=True,slow_ms=2100`
5. `eval-20261028-chimera::trial-0006` — S-NORM/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan-mini.json` cell `S-NORM|I-SPACE|chimera|disabled=False,slow_ms=0`
6. `eval-20261028-chimera::trial-0055` — S-SLOW/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan-mini.json` cell `S-SLOW|I-SPACE|chimera|disabled=False,slow_ms=2100`
7. `eval-20261028-chimera::trial-0100` — S-DIS/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan-mini.json` cell `S-DIS|I-SPACE|chimera|disabled=True,slow_ms=0`
8. `eval-20261028-chimera::trial-0142` — S-SLOWDIS/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan-mini.json` cell `S-SLOWDIS|I-SPACE|chimera|disabled=True,slow_ms=2100`

## Episodes

### `eval-20261028-baseline-a::trial-0009`

- Condition: S-NORM / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/4606f72f-1e04-42e0-a694-f982366943d5.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/4606f72f-1e04-42e0-a694-f982366943d5.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/4606f72f-1e04-42e0-a694-f982366943d5.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 3 steps · 5 observed actions · snapshot confirmation_visible=true items=["Padded Name"]
- trace: `artifacts/eval-20261028/traces-baseline-a/4606f72f-1e04-42e0-a694-f982366943d5.replay.json` (560 bytes, sha256 `b4f18476f11c…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/4606f72f-1e04-42e0-a694-f982366943d5.snapshot.json` (150 bytes, sha256 `4f0f420f4354…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/4606f72f-1e04-42e0-a694-f982366943d5.actions.json` (1708 bytes, sha256 `806bf26bef41…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: replay driver report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0052`

- Condition: S-SLOW / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("  Padded Name  ")
  - attempting fill action
 …`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/9d2ec184-2bf1-4af0-b587-52be948a3273.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/9d2ec184-2bf1-4af0-b587-52be948a3273.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/9d2ec184-2bf1-4af0-b587-52be948a3273.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/9d2ec184-2bf1-4af0-b587-52be948a3273.replay.json` (485 bytes, sha256 `061ca8b00e7a…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/9d2ec184-2bf1-4af0-b587-52be948a3273.snapshot.json` (138 bytes, sha256 `aba5d0029801…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/9d2ec184-2bf1-4af0-b587-52be948a3273.actions.json` (1440 bytes, sha256 `297d464143c7…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: replay driver report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0098`

- Condition: S-DIS / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("  Padded Name  ")
  - attempting fill action
 …`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/db822f37-1c14-4b1f-bda9-70b813f84a6f.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/db822f37-1c14-4b1f-bda9-70b813f84a6f.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/db822f37-1c14-4b1f-bda9-70b813f84a6f.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/db822f37-1c14-4b1f-bda9-70b813f84a6f.replay.json` (486 bytes, sha256 `a65a55e9a7cf…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/db822f37-1c14-4b1f-bda9-70b813f84a6f.snapshot.json` (138 bytes, sha256 `71bea270be27…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/db822f37-1c14-4b1f-bda9-70b813f84a6f.actions.json` (1443 bytes, sha256 `8a2a0ec33797…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: replay driver report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0143`

- Condition: S-SLOWDIS / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("  Padded Name  ")
  - attempting fill action
 …`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/62b89715-85fa-4232-a212-2ba3dadc7372.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/62b89715-85fa-4232-a212-2ba3dadc7372.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/62b89715-85fa-4232-a212-2ba3dadc7372.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/62b89715-85fa-4232-a212-2ba3dadc7372.replay.json` (496 bytes, sha256 `9185891fdae4…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/62b89715-85fa-4232-a212-2ba3dadc7372.snapshot.json` (138 bytes, sha256 `caea94761fe2…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/62b89715-85fa-4232-a212-2ba3dadc7372.actions.json` (1473 bytes, sha256 `f79965840a26…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: replay driver report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-chimera::trial-0006`

- Condition: S-NORM / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/391c7849-f7a5-4d27-b69f-5f933b3e8ac1.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/391c7849-f7a5-4d27-b69f-5f933b3e8ac1.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/391c7849-f7a5-4d27-b69f-5f933b3e8ac1.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Padded Name"]
- trace: `artifacts/eval-20261028/traces-chimera/391c7849-f7a5-4d27-b69f-5f933b3e8ac1.json` (2971 bytes, sha256 `e3f22addec8c…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/391c7849-f7a5-4d27-b69f-5f933b3e8ac1.snapshot.json` (150 bytes, sha256 `dcacee610fc6…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/391c7849-f7a5-4d27-b69f-5f933b3e8ac1.actions.json` (2284 bytes, sha256 `8b11825a2902…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0055`

- Condition: S-SLOW / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/be95d9fb-aaf7-4aab-a1c8-1e2b45e2d56b.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/be95d9fb-aaf7-4aab-a1c8-1e2b45e2d56b.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/be95d9fb-aaf7-4aab-a1c8-1e2b45e2d56b.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Padded Name"]
- trace: `artifacts/eval-20261028/traces-chimera/be95d9fb-aaf7-4aab-a1c8-1e2b45e2d56b.json` (2981 bytes, sha256 `fa822659fb11…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/be95d9fb-aaf7-4aab-a1c8-1e2b45e2d56b.snapshot.json` (150 bytes, sha256 `2279e2c9d9fe…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/be95d9fb-aaf7-4aab-a1c8-1e2b45e2d56b.actions.json` (2320 bytes, sha256 `9f8eb3b1f826…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0100`

- Condition: S-DIS / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/a763e65d-273f-47aa-a128-e188bebf55d7.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/a763e65d-273f-47aa-a128-e188bebf55d7.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/a763e65d-273f-47aa-a128-e188bebf55d7.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/a763e65d-273f-47aa-a128-e188bebf55d7.json` (3912 bytes, sha256 `4ae396ff820e…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/a763e65d-273f-47aa-a128-e188bebf55d7.snapshot.json` (138 bytes, sha256 `5faf55ab5b3c…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/a763e65d-273f-47aa-a128-e188bebf55d7.actions.json` (1731 bytes, sha256 `7d7dbbb2f560…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/a763e65d-273f-47aa-a128-e188bebf55d7.png` (present)

### `eval-20261028-chimera::trial-0142`

- Condition: S-SLOWDIS / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/3c91e2a3-e1b9-4db5-bf54-e509bcb38e45.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/3c91e2a3-e1b9-4db5-bf54-e509bcb38e45.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/3c91e2a3-e1b9-4db5-bf54-e509bcb38e45.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/3c91e2a3-e1b9-4db5-bf54-e509bcb38e45.json` (3922 bytes, sha256 `cf4ea88c7dcf…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/3c91e2a3-e1b9-4db5-bf54-e509bcb38e45.snapshot.json` (138 bytes, sha256 `08a594d9528a…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/3c91e2a3-e1b9-4db5-bf54-e509bcb38e45.actions.json` (1761 bytes, sha256 `f3009b8d8d8c…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/3c91e2a3-e1b9-4db5-bf54-e509bcb38e45.png` (present)

## Review protocol

1. Assess each episode blinded (recorded outcome and verifier checks masked): verified success, verified failure, or inconclusive — from the postconditions and the evidence above, never from success strings or the verifier's status.
2. Reveal the recorded verdict and judge agreement: agrees, disagrees, or undetermined.
3. Judge evidence sufficiency and record a reason tied to specific observations; describe missing evidence explicitly when a decision cannot be supported.
4. Export `decisions.json` and validate it with `tools/mini_review.py validate`.

Eight episodes describe only these eight episodes: agreement counts here support no reliability claim and the 95% provisional rule (user guide §15.1 step 4) applies to full audits, not to this mini-sample.
