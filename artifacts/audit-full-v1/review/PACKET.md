# Full audit review packet — eval-20261028 + matched-budget v1 (184 episodes)

Created: 2026-10-30T09:29:01.796+00:00 · schema `chimera-mini-review-packet/1` · 184 episodes.
This packet is a read-only view of frozen evidence plus empty decision slots. All judgments live in `decisions.json`, recorded only by a human reviewer.

Manifest: `benchmarks/manifests/eval-v1.json` (eval-v1, sha256 `b23580c8c07c3528a33f10f25780138cd58455a1f334c48e4fd889125c038cf5` — verified against the frozen file at packet build).

Manifest: `benchmarks/manifests/eval-v1.json` (eval-v1, sha256 `b23580c8c07c3528a33f10f25780138cd58455a1f334c48e4fd889125c038cf5` — verified against the frozen file at packet build).

Manifest: `experiments/matched-budget-v1/manifest-mb-v1.json` (mb-v1, sha256 `1b246fbd0d93442710a482eabd5384b4ff147d8722b70023b5bc3940b574fd98` — verified against the frozen file at packet build).

Manifest: `experiments/matched-budget-v1/manifest-mb-v1.json` (mb-v1, sha256 `1b246fbd0d93442710a482eabd5384b4ff147d8722b70023b5bc3940b574fd98` — verified against the frozen file at packet build).

Manifest: `experiments/matched-budget-v1/manifest-mb-v1.json` (mb-v1, sha256 `1b246fbd0d93442710a482eabd5384b4ff147d8722b70023b5bc3940b574fd98` — verified against the frozen file at packet build).

Manifest: `experiments/matched-budget-v1/manifest-mb-v1.json` (mb-v1, sha256 `1b246fbd0d93442710a482eabd5384b4ff147d8722b70023b5bc3940b574fd98` — verified against the frozen file at packet build).

Manifest: `experiments/matched-budget-v1/manifest-mb-v1.json` (mb-v1, sha256 `1b246fbd0d93442710a482eabd5384b4ff147d8722b70023b5bc3940b574fd98` — verified against the frozen file at packet build).

Populations (separate denominators — never pooled):

- **primary evaluation (eval-20261028)** — run `eval-20261028-chimera` · 72 episodes
- **primary evaluation (eval-20261028)** — run `eval-20261028-baseline-a` · 72 episodes
- **matched-budget follow-up (mb-v1)** — run `main-mb-v1-chimera` · 8 episodes
- **matched-budget follow-up (mb-v1)** — run `main-mb-v1-replay-100` · 8 episodes
- **matched-budget follow-up (mb-v1)** — run `main-mb-v1-replay-1000` · 8 episodes
- **matched-budget follow-up (mb-v1)** — run `main-mb-v1-replay-2500` · 8 episodes
- **matched-budget follow-up (mb-v1)** — run `main-mb-v1-replay-5000` · 8 episodes

## Task and postconditions (benchmark_design §2)

Create a project with a given name. The agent must navigate to the target, fill the name, click "Create Project", and satisfy the postconditions.

- **P1** — Confirmation is visible: `#confirmation` is visible (judge: Is confirmation_visible true in the snapshot?)
- **P2** — The project appears in the list, exactly once: exactly one `#project-list li` whose `textContent` equals the expected trimmed name (judge: Does items contain exactly one entry whose text equals the expected stored name?)
- **P3** — The list contains no unexpected entries: the count of `#project-list li` equals 1 (judge: Does items contain exactly one entry?)

P4 (list empty before the agent's click) is harness-only context; the audit judges the verifier's P1–P3.

Recorded outcomes and verifier checks are masked during initial assessment in the review queue. Blinding is partial: trace structure differs between the Chimera driver (event trace) and Baseline A (replay report), so a knowledgeable reviewer may infer the driver from the evidence shape.

## Selection

1. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0001` — S-NORM/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-NORM|I-PLAIN|chimera|disabled=False,slow_ms=0`
2. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0004` — S-NORM/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-NORM|I-PLAIN|chimera|disabled=False,slow_ms=0`
3. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0006` — S-NORM/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-NORM|I-SPACE|chimera|disabled=False,slow_ms=0`
4. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0008` — S-NORM/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-NORM|I-SPACE|chimera|disabled=False,slow_ms=0`
5. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0011` — S-NORM/I-UNICODE · baseline `chimera` · expected 'Проект — Ünïcode ✓' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-NORM|I-UNICODE|chimera|disabled=False,slow_ms=0`
6. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0014` — S-NORM/I-UNICODE · baseline `chimera` · expected 'Проект — Ünïcode ✓' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-NORM|I-UNICODE|chimera|disabled=False,slow_ms=0`
7. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0017` — S-SLOW/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-PLAIN|chimera|disabled=False,slow_ms=800`
8. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0020` — S-SLOW/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-PLAIN|chimera|disabled=False,slow_ms=800`
9. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0021` — S-SLOW/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-SPACE|chimera|disabled=False,slow_ms=800`
10. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0023` — S-SLOW/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-SPACE|chimera|disabled=False,slow_ms=800`
11. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0027` — S-SLOW/I-UNICODE · baseline `chimera` · expected 'Проект — Ünïcode ✓' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-UNICODE|chimera|disabled=False,slow_ms=800`
12. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0029` — S-SLOW/I-UNICODE · baseline `chimera` · expected 'Проект — Ünïcode ✓' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-UNICODE|chimera|disabled=False,slow_ms=800`
13. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0033` — S-SLOW/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-PLAIN|chimera|disabled=False,slow_ms=1350`
14. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0034` — S-SLOW/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-PLAIN|chimera|disabled=False,slow_ms=1350`
15. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0039` — S-SLOW/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-SPACE|chimera|disabled=False,slow_ms=1350`
16. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0040` — S-SLOW/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-SPACE|chimera|disabled=False,slow_ms=1350`
17. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0041` — S-SLOW/I-UNICODE · baseline `chimera` · expected 'Проект — Ünïcode ✓' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-UNICODE|chimera|disabled=False,slow_ms=1350`
18. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0043` — S-SLOW/I-UNICODE · baseline `chimera` · expected 'Проект — Ünïcode ✓' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-UNICODE|chimera|disabled=False,slow_ms=1350`
19. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0049` — S-SLOW/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-PLAIN|chimera|disabled=False,slow_ms=2100`
20. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0050` — S-SLOW/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-PLAIN|chimera|disabled=False,slow_ms=2100`
21. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0051` — S-SLOW/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-SPACE|chimera|disabled=False,slow_ms=2100`
22. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0055` — S-SLOW/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-SPACE|chimera|disabled=False,slow_ms=2100`
23. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0057` — S-SLOW/I-UNICODE · baseline `chimera` · expected 'Проект — Ünïcode ✓' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-UNICODE|chimera|disabled=False,slow_ms=2100`
24. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0059` — S-SLOW/I-UNICODE · baseline `chimera` · expected 'Проект — Ünïcode ✓' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-UNICODE|chimera|disabled=False,slow_ms=2100`
25. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0063` — S-SLOW/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-PLAIN|chimera|disabled=False,slow_ms=3000`
26. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0065` — S-SLOW/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-PLAIN|chimera|disabled=False,slow_ms=3000`
27. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0066` — S-SLOW/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-SPACE|chimera|disabled=False,slow_ms=3000`
28. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0069` — S-SLOW/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-SPACE|chimera|disabled=False,slow_ms=3000`
29. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0072` — S-SLOW/I-UNICODE · baseline `chimera` · expected 'Проект — Ünïcode ✓' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-UNICODE|chimera|disabled=False,slow_ms=3000`
30. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0074` — S-SLOW/I-UNICODE · baseline `chimera` · expected 'Проект — Ünïcode ✓' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-UNICODE|chimera|disabled=False,slow_ms=3000`
31. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0077` — S-SLOW/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-PLAIN|chimera|disabled=False,slow_ms=3900`
32. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0078` — S-SLOW/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-PLAIN|chimera|disabled=False,slow_ms=3900`
33. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0081` — S-SLOW/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-SPACE|chimera|disabled=False,slow_ms=3900`
34. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0082` — S-SLOW/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-SPACE|chimera|disabled=False,slow_ms=3900`
35. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0087` — S-SLOW/I-UNICODE · baseline `chimera` · expected 'Проект — Ünïcode ✓' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-UNICODE|chimera|disabled=False,slow_ms=3900`
36. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0090` — S-SLOW/I-UNICODE · baseline `chimera` · expected 'Проект — Ünïcode ✓' · recorded `succeeded` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOW|I-UNICODE|chimera|disabled=False,slow_ms=3900`
37. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0091` — S-DIS/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-DIS|I-PLAIN|chimera|disabled=True,slow_ms=0`
38. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0093` — S-DIS/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-DIS|I-PLAIN|chimera|disabled=True,slow_ms=0`
39. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0098` — S-DIS/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-DIS|I-SPACE|chimera|disabled=True,slow_ms=0`
40. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0100` — S-DIS/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-DIS|I-SPACE|chimera|disabled=True,slow_ms=0`
41. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0101` — S-DIS/I-UNICODE · baseline `chimera` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-DIS|I-UNICODE|chimera|disabled=True,slow_ms=0`
42. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0103` — S-DIS/I-UNICODE · baseline `chimera` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-DIS|I-UNICODE|chimera|disabled=True,slow_ms=0`
43. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0106` — S-SLOWDIS/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|chimera|disabled=True,slow_ms=800`
44. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0107` — S-SLOWDIS/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|chimera|disabled=True,slow_ms=800`
45. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0111` — S-SLOWDIS/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-SPACE|chimera|disabled=True,slow_ms=800`
46. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0115` — S-SLOWDIS/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-SPACE|chimera|disabled=True,slow_ms=800`
47. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0118` — S-SLOWDIS/I-UNICODE · baseline `chimera` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-UNICODE|chimera|disabled=True,slow_ms=800`
48. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0119` — S-SLOWDIS/I-UNICODE · baseline `chimera` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-UNICODE|chimera|disabled=True,slow_ms=800`
49. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0122` — S-SLOWDIS/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|chimera|disabled=True,slow_ms=1350`
50. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0123` — S-SLOWDIS/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|chimera|disabled=True,slow_ms=1350`
51. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0127` — S-SLOWDIS/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-SPACE|chimera|disabled=True,slow_ms=1350`
52. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0129` — S-SLOWDIS/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-SPACE|chimera|disabled=True,slow_ms=1350`
53. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0131` — S-SLOWDIS/I-UNICODE · baseline `chimera` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-UNICODE|chimera|disabled=True,slow_ms=1350`
54. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0133` — S-SLOWDIS/I-UNICODE · baseline `chimera` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-UNICODE|chimera|disabled=True,slow_ms=1350`
55. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0136` — S-SLOWDIS/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|chimera|disabled=True,slow_ms=2100`
56. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0138` — S-SLOWDIS/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|chimera|disabled=True,slow_ms=2100`
57. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0142` — S-SLOWDIS/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-SPACE|chimera|disabled=True,slow_ms=2100`
58. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0145` — S-SLOWDIS/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-SPACE|chimera|disabled=True,slow_ms=2100`
59. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0146` — S-SLOWDIS/I-UNICODE · baseline `chimera` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-UNICODE|chimera|disabled=True,slow_ms=2100`
60. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0147` — S-SLOWDIS/I-UNICODE · baseline `chimera` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-UNICODE|chimera|disabled=True,slow_ms=2100`
61. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0153` — S-SLOWDIS/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|chimera|disabled=True,slow_ms=3000`
62. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0154` — S-SLOWDIS/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|chimera|disabled=True,slow_ms=3000`
63. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0156` — S-SLOWDIS/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-SPACE|chimera|disabled=True,slow_ms=3000`
64. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0160` — S-SLOWDIS/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-SPACE|chimera|disabled=True,slow_ms=3000`
65. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0161` — S-SLOWDIS/I-UNICODE · baseline `chimera` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-UNICODE|chimera|disabled=True,slow_ms=3000`
66. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0165` — S-SLOWDIS/I-UNICODE · baseline `chimera` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-UNICODE|chimera|disabled=True,slow_ms=3000`
67. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0167` — S-SLOWDIS/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|chimera|disabled=True,slow_ms=3900`
68. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0170` — S-SLOWDIS/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|chimera|disabled=True,slow_ms=3900`
69. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0172` — S-SLOWDIS/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-SPACE|chimera|disabled=True,slow_ms=3900`
70. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0175` — S-SLOWDIS/I-SPACE · baseline `chimera` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-SPACE|chimera|disabled=True,slow_ms=3900`
71. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0176` — S-SLOWDIS/I-UNICODE · baseline `chimera` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-UNICODE|chimera|disabled=True,slow_ms=3900`
72. [primary evaluation (eval-20261028) · Driver B] `eval-20261028-chimera::trial-0179` — S-SLOWDIS/I-UNICODE · baseline `chimera` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-chimera.audit-plan.json` cell `S-SLOWDIS|I-UNICODE|chimera|disabled=True,slow_ms=3900`
73. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0003` — S-NORM/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `succeeded` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-NORM|I-PLAIN|baseline-a|disabled=False,slow_ms=0`
74. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0005` — S-NORM/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `succeeded` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-NORM|I-PLAIN|baseline-a|disabled=False,slow_ms=0`
75. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0007` — S-NORM/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `succeeded` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-NORM|I-SPACE|baseline-a|disabled=False,slow_ms=0`
76. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0009` — S-NORM/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `succeeded` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-NORM|I-SPACE|baseline-a|disabled=False,slow_ms=0`
77. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0011` — S-NORM/I-UNICODE · baseline `baseline-a` · expected 'Проект — Ünïcode ✓' · recorded `succeeded` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-NORM|I-UNICODE|baseline-a|disabled=False,slow_ms=0`
78. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0013` — S-NORM/I-UNICODE · baseline `baseline-a` · expected 'Проект — Ünïcode ✓' · recorded `succeeded` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-NORM|I-UNICODE|baseline-a|disabled=False,slow_ms=0`
79. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0016` — S-SLOW/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-PLAIN|baseline-a|disabled=False,slow_ms=800`
80. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0017` — S-SLOW/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-PLAIN|baseline-a|disabled=False,slow_ms=800`
81. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0021` — S-SLOW/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-SPACE|baseline-a|disabled=False,slow_ms=800`
82. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0024` — S-SLOW/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-SPACE|baseline-a|disabled=False,slow_ms=800`
83. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0027` — S-SLOW/I-UNICODE · baseline `baseline-a` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-UNICODE|baseline-a|disabled=False,slow_ms=800`
84. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0029` — S-SLOW/I-UNICODE · baseline `baseline-a` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-UNICODE|baseline-a|disabled=False,slow_ms=800`
85. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0032` — S-SLOW/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-PLAIN|baseline-a|disabled=False,slow_ms=1350`
86. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0035` — S-SLOW/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-PLAIN|baseline-a|disabled=False,slow_ms=1350`
87. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0036` — S-SLOW/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-SPACE|baseline-a|disabled=False,slow_ms=1350`
88. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0037` — S-SLOW/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-SPACE|baseline-a|disabled=False,slow_ms=1350`
89. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0041` — S-SLOW/I-UNICODE · baseline `baseline-a` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-UNICODE|baseline-a|disabled=False,slow_ms=1350`
90. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0042` — S-SLOW/I-UNICODE · baseline `baseline-a` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-UNICODE|baseline-a|disabled=False,slow_ms=1350`
91. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0046` — S-SLOW/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-PLAIN|baseline-a|disabled=False,slow_ms=2100`
92. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0050` — S-SLOW/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-PLAIN|baseline-a|disabled=False,slow_ms=2100`
93. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0051` — S-SLOW/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-SPACE|baseline-a|disabled=False,slow_ms=2100`
94. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0052` — S-SLOW/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-SPACE|baseline-a|disabled=False,slow_ms=2100`
95. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0059` — S-SLOW/I-UNICODE · baseline `baseline-a` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-UNICODE|baseline-a|disabled=False,slow_ms=2100`
96. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0060` — S-SLOW/I-UNICODE · baseline `baseline-a` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-UNICODE|baseline-a|disabled=False,slow_ms=2100`
97. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0061` — S-SLOW/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-PLAIN|baseline-a|disabled=False,slow_ms=3000`
98. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0063` — S-SLOW/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-PLAIN|baseline-a|disabled=False,slow_ms=3000`
99. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0069` — S-SLOW/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-SPACE|baseline-a|disabled=False,slow_ms=3000`
100. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0070` — S-SLOW/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-SPACE|baseline-a|disabled=False,slow_ms=3000`
101. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0071` — S-SLOW/I-UNICODE · baseline `baseline-a` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-UNICODE|baseline-a|disabled=False,slow_ms=3000`
102. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0073` — S-SLOW/I-UNICODE · baseline `baseline-a` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-UNICODE|baseline-a|disabled=False,slow_ms=3000`
103. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0076` — S-SLOW/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-PLAIN|baseline-a|disabled=False,slow_ms=3900`
104. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0078` — S-SLOW/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-PLAIN|baseline-a|disabled=False,slow_ms=3900`
105. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0084` — S-SLOW/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-SPACE|baseline-a|disabled=False,slow_ms=3900`
106. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0085` — S-SLOW/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-SPACE|baseline-a|disabled=False,slow_ms=3900`
107. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0086` — S-SLOW/I-UNICODE · baseline `baseline-a` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-UNICODE|baseline-a|disabled=False,slow_ms=3900`
108. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0090` — S-SLOW/I-UNICODE · baseline `baseline-a` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOW|I-UNICODE|baseline-a|disabled=False,slow_ms=3900`
109. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0093` — S-DIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-DIS|I-PLAIN|baseline-a|disabled=True,slow_ms=0`
110. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0094` — S-DIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-DIS|I-PLAIN|baseline-a|disabled=True,slow_ms=0`
111. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0098` — S-DIS/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-DIS|I-SPACE|baseline-a|disabled=True,slow_ms=0`
112. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0100` — S-DIS/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-DIS|I-SPACE|baseline-a|disabled=True,slow_ms=0`
113. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0102` — S-DIS/I-UNICODE · baseline `baseline-a` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-DIS|I-UNICODE|baseline-a|disabled=True,slow_ms=0`
114. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0104` — S-DIS/I-UNICODE · baseline `baseline-a` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-DIS|I-UNICODE|baseline-a|disabled=True,slow_ms=0`
115. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0107` — S-SLOWDIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|baseline-a|disabled=True,slow_ms=800`
116. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0108` — S-SLOWDIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|baseline-a|disabled=True,slow_ms=800`
117. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0111` — S-SLOWDIS/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-SPACE|baseline-a|disabled=True,slow_ms=800`
118. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0115` — S-SLOWDIS/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-SPACE|baseline-a|disabled=True,slow_ms=800`
119. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0116` — S-SLOWDIS/I-UNICODE · baseline `baseline-a` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-UNICODE|baseline-a|disabled=True,slow_ms=800`
120. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0119` — S-SLOWDIS/I-UNICODE · baseline `baseline-a` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-UNICODE|baseline-a|disabled=True,slow_ms=800`
121. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0122` — S-SLOWDIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|baseline-a|disabled=True,slow_ms=1350`
122. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0125` — S-SLOWDIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|baseline-a|disabled=True,slow_ms=1350`
123. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0126` — S-SLOWDIS/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-SPACE|baseline-a|disabled=True,slow_ms=1350`
124. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0127` — S-SLOWDIS/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-SPACE|baseline-a|disabled=True,slow_ms=1350`
125. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0131` — S-SLOWDIS/I-UNICODE · baseline `baseline-a` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-UNICODE|baseline-a|disabled=True,slow_ms=1350`
126. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0133` — S-SLOWDIS/I-UNICODE · baseline `baseline-a` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-UNICODE|baseline-a|disabled=True,slow_ms=1350`
127. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0137` — S-SLOWDIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|baseline-a|disabled=True,slow_ms=2100`
128. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0140` — S-SLOWDIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|baseline-a|disabled=True,slow_ms=2100`
129. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0143` — S-SLOWDIS/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-SPACE|baseline-a|disabled=True,slow_ms=2100`
130. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0145` — S-SLOWDIS/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-SPACE|baseline-a|disabled=True,slow_ms=2100`
131. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0147` — S-SLOWDIS/I-UNICODE · baseline `baseline-a` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-UNICODE|baseline-a|disabled=True,slow_ms=2100`
132. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0148` — S-SLOWDIS/I-UNICODE · baseline `baseline-a` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-UNICODE|baseline-a|disabled=True,slow_ms=2100`
133. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0154` — S-SLOWDIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|baseline-a|disabled=True,slow_ms=3000`
134. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0155` — S-SLOWDIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|baseline-a|disabled=True,slow_ms=3000`
135. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0156` — S-SLOWDIS/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-SPACE|baseline-a|disabled=True,slow_ms=3000`
136. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0159` — S-SLOWDIS/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-SPACE|baseline-a|disabled=True,slow_ms=3000`
137. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0164` — S-SLOWDIS/I-UNICODE · baseline `baseline-a` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-UNICODE|baseline-a|disabled=True,slow_ms=3000`
138. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0165` — S-SLOWDIS/I-UNICODE · baseline `baseline-a` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-UNICODE|baseline-a|disabled=True,slow_ms=3000`
139. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0167` — S-SLOWDIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|baseline-a|disabled=True,slow_ms=3900`
140. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0169` — S-SLOWDIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|baseline-a|disabled=True,slow_ms=3900`
141. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0171` — S-SLOWDIS/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-SPACE|baseline-a|disabled=True,slow_ms=3900`
142. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0173` — S-SLOWDIS/I-SPACE · baseline `baseline-a` · expected 'Padded Name' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-SPACE|baseline-a|disabled=True,slow_ms=3900`
143. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0176` — S-SLOWDIS/I-UNICODE · baseline `baseline-a` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-UNICODE|baseline-a|disabled=True,slow_ms=3900`
144. [primary evaluation (eval-20261028) · Driver F] `eval-20261028-baseline-a::trial-0177` — S-SLOWDIS/I-UNICODE · baseline `baseline-a` · expected 'Проект — Ünïcode ✓' · recorded `failed` · plan `artifacts/eval-20261028/run-baseline-a.audit-plan.json` cell `S-SLOWDIS|I-UNICODE|baseline-a|disabled=True,slow_ms=3900`
145. [matched-budget follow-up (mb-v1) · Driver C] `main-mb-v1-chimera::trial-0003` — S-NORM/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `succeeded` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-chimera.audit-plan.json` cell `S-NORM|I-PLAIN|chimera|disabled=False,slow_ms=0`
146. [matched-budget follow-up (mb-v1) · Driver C] `main-mb-v1-chimera::trial-0004` — S-NORM/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `succeeded` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-chimera.audit-plan.json` cell `S-NORM|I-PLAIN|chimera|disabled=False,slow_ms=0`
147. [matched-budget follow-up (mb-v1) · Driver C] `main-mb-v1-chimera::trial-0006` — S-SLOW/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `succeeded` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-chimera.audit-plan.json` cell `S-SLOW|I-PLAIN|chimera|disabled=False,slow_ms=2100`
148. [matched-budget follow-up (mb-v1) · Driver C] `main-mb-v1-chimera::trial-0007` — S-SLOW/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `succeeded` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-chimera.audit-plan.json` cell `S-SLOW|I-PLAIN|chimera|disabled=False,slow_ms=2100`
149. [matched-budget follow-up (mb-v1) · Driver C] `main-mb-v1-chimera::trial-0013` — S-DIS/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `failed` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-chimera.audit-plan.json` cell `S-DIS|I-PLAIN|chimera|disabled=True,slow_ms=0`
150. [matched-budget follow-up (mb-v1) · Driver C] `main-mb-v1-chimera::trial-0015` — S-DIS/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `failed` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-chimera.audit-plan.json` cell `S-DIS|I-PLAIN|chimera|disabled=True,slow_ms=0`
151. [matched-budget follow-up (mb-v1) · Driver C] `main-mb-v1-chimera::trial-0019` — S-SLOWDIS/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `failed` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-chimera.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|chimera|disabled=True,slow_ms=2100`
152. [matched-budget follow-up (mb-v1) · Driver C] `main-mb-v1-chimera::trial-0020` — S-SLOWDIS/I-PLAIN · baseline `chimera` · expected 'Benchmark Project' · recorded `failed` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-chimera.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|chimera|disabled=True,slow_ms=2100`
153. [matched-budget follow-up (mb-v1) · Driver G] `main-mb-v1-replay-100::trial-0002` — S-NORM/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `succeeded` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-100.audit-plan.json` cell `S-NORM|I-PLAIN|baseline-a|disabled=False,slow_ms=0`
154. [matched-budget follow-up (mb-v1) · Driver G] `main-mb-v1-replay-100::trial-0003` — S-NORM/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `succeeded` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-100.audit-plan.json` cell `S-NORM|I-PLAIN|baseline-a|disabled=False,slow_ms=0`
155. [matched-budget follow-up (mb-v1) · Driver G] `main-mb-v1-replay-100::trial-0007` — S-SLOW/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-100.audit-plan.json` cell `S-SLOW|I-PLAIN|baseline-a|disabled=False,slow_ms=2100`
156. [matched-budget follow-up (mb-v1) · Driver G] `main-mb-v1-replay-100::trial-0009` — S-SLOW/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-100.audit-plan.json` cell `S-SLOW|I-PLAIN|baseline-a|disabled=False,slow_ms=2100`
157. [matched-budget follow-up (mb-v1) · Driver G] `main-mb-v1-replay-100::trial-0011` — S-DIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-100.audit-plan.json` cell `S-DIS|I-PLAIN|baseline-a|disabled=True,slow_ms=0`
158. [matched-budget follow-up (mb-v1) · Driver G] `main-mb-v1-replay-100::trial-0014` — S-DIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-100.audit-plan.json` cell `S-DIS|I-PLAIN|baseline-a|disabled=True,slow_ms=0`
159. [matched-budget follow-up (mb-v1) · Driver G] `main-mb-v1-replay-100::trial-0016` — S-SLOWDIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-100.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|baseline-a|disabled=True,slow_ms=2100`
160. [matched-budget follow-up (mb-v1) · Driver G] `main-mb-v1-replay-100::trial-0018` — S-SLOWDIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-100.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|baseline-a|disabled=True,slow_ms=2100`
161. [matched-budget follow-up (mb-v1) · Driver A] `main-mb-v1-replay-1000::trial-0003` — S-NORM/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `succeeded` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-1000.audit-plan.json` cell `S-NORM|I-PLAIN|baseline-a|disabled=False,slow_ms=0`
162. [matched-budget follow-up (mb-v1) · Driver A] `main-mb-v1-replay-1000::trial-0004` — S-NORM/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `succeeded` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-1000.audit-plan.json` cell `S-NORM|I-PLAIN|baseline-a|disabled=False,slow_ms=0`
163. [matched-budget follow-up (mb-v1) · Driver A] `main-mb-v1-replay-1000::trial-0006` — S-SLOW/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-1000.audit-plan.json` cell `S-SLOW|I-PLAIN|baseline-a|disabled=False,slow_ms=2100`
164. [matched-budget follow-up (mb-v1) · Driver A] `main-mb-v1-replay-1000::trial-0009` — S-SLOW/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-1000.audit-plan.json` cell `S-SLOW|I-PLAIN|baseline-a|disabled=False,slow_ms=2100`
165. [matched-budget follow-up (mb-v1) · Driver A] `main-mb-v1-replay-1000::trial-0013` — S-DIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-1000.audit-plan.json` cell `S-DIS|I-PLAIN|baseline-a|disabled=True,slow_ms=0`
166. [matched-budget follow-up (mb-v1) · Driver A] `main-mb-v1-replay-1000::trial-0015` — S-DIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-1000.audit-plan.json` cell `S-DIS|I-PLAIN|baseline-a|disabled=True,slow_ms=0`
167. [matched-budget follow-up (mb-v1) · Driver A] `main-mb-v1-replay-1000::trial-0016` — S-SLOWDIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-1000.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|baseline-a|disabled=True,slow_ms=2100`
168. [matched-budget follow-up (mb-v1) · Driver A] `main-mb-v1-replay-1000::trial-0017` — S-SLOWDIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-1000.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|baseline-a|disabled=True,slow_ms=2100`
169. [matched-budget follow-up (mb-v1) · Driver E] `main-mb-v1-replay-2500::trial-0003` — S-NORM/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `succeeded` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-2500.audit-plan.json` cell `S-NORM|I-PLAIN|baseline-a|disabled=False,slow_ms=0`
170. [matched-budget follow-up (mb-v1) · Driver E] `main-mb-v1-replay-2500::trial-0004` — S-NORM/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `succeeded` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-2500.audit-plan.json` cell `S-NORM|I-PLAIN|baseline-a|disabled=False,slow_ms=0`
171. [matched-budget follow-up (mb-v1) · Driver E] `main-mb-v1-replay-2500::trial-0006` — S-SLOW/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `succeeded` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-2500.audit-plan.json` cell `S-SLOW|I-PLAIN|baseline-a|disabled=False,slow_ms=2100`
172. [matched-budget follow-up (mb-v1) · Driver E] `main-mb-v1-replay-2500::trial-0007` — S-SLOW/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `succeeded` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-2500.audit-plan.json` cell `S-SLOW|I-PLAIN|baseline-a|disabled=False,slow_ms=2100`
173. [matched-budget follow-up (mb-v1) · Driver E] `main-mb-v1-replay-2500::trial-0012` — S-DIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-2500.audit-plan.json` cell `S-DIS|I-PLAIN|baseline-a|disabled=True,slow_ms=0`
174. [matched-budget follow-up (mb-v1) · Driver E] `main-mb-v1-replay-2500::trial-0014` — S-DIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-2500.audit-plan.json` cell `S-DIS|I-PLAIN|baseline-a|disabled=True,slow_ms=0`
175. [matched-budget follow-up (mb-v1) · Driver E] `main-mb-v1-replay-2500::trial-0017` — S-SLOWDIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-2500.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|baseline-a|disabled=True,slow_ms=2100`
176. [matched-budget follow-up (mb-v1) · Driver E] `main-mb-v1-replay-2500::trial-0019` — S-SLOWDIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-2500.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|baseline-a|disabled=True,slow_ms=2100`
177. [matched-budget follow-up (mb-v1) · Driver D] `main-mb-v1-replay-5000::trial-0003` — S-NORM/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `succeeded` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-5000.audit-plan.json` cell `S-NORM|I-PLAIN|baseline-a|disabled=False,slow_ms=0`
178. [matched-budget follow-up (mb-v1) · Driver D] `main-mb-v1-replay-5000::trial-0004` — S-NORM/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `succeeded` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-5000.audit-plan.json` cell `S-NORM|I-PLAIN|baseline-a|disabled=False,slow_ms=0`
179. [matched-budget follow-up (mb-v1) · Driver D] `main-mb-v1-replay-5000::trial-0008` — S-SLOW/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `succeeded` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-5000.audit-plan.json` cell `S-SLOW|I-PLAIN|baseline-a|disabled=False,slow_ms=2100`
180. [matched-budget follow-up (mb-v1) · Driver D] `main-mb-v1-replay-5000::trial-0010` — S-SLOW/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `succeeded` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-5000.audit-plan.json` cell `S-SLOW|I-PLAIN|baseline-a|disabled=False,slow_ms=2100`
181. [matched-budget follow-up (mb-v1) · Driver D] `main-mb-v1-replay-5000::trial-0011` — S-DIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-5000.audit-plan.json` cell `S-DIS|I-PLAIN|baseline-a|disabled=True,slow_ms=0`
182. [matched-budget follow-up (mb-v1) · Driver D] `main-mb-v1-replay-5000::trial-0014` — S-DIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-5000.audit-plan.json` cell `S-DIS|I-PLAIN|baseline-a|disabled=True,slow_ms=0`
183. [matched-budget follow-up (mb-v1) · Driver D] `main-mb-v1-replay-5000::trial-0017` — S-SLOWDIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-5000.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|baseline-a|disabled=True,slow_ms=2100`
184. [matched-budget follow-up (mb-v1) · Driver D] `main-mb-v1-replay-5000::trial-0020` — S-SLOWDIS/I-PLAIN · baseline `baseline-a` · expected 'Benchmark Project' · recorded `failed` · plan `experiments/matched-budget-v1/audit-plans/mb-v1-replay-5000.audit-plan.json` cell `S-SLOWDIS|I-PLAIN|baseline-a|disabled=True,slow_ms=2100`

## Episodes

### `eval-20261028-chimera::trial-0001`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-NORM / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/449dd1c8-4cce-4a74-90a3-ef08a0fe9d28.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/449dd1c8-4cce-4a74-90a3-ef08a0fe9d28.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/449dd1c8-4cce-4a74-90a3-ef08a0fe9d28.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `artifacts/eval-20261028/traces-chimera/449dd1c8-4cce-4a74-90a3-ef08a0fe9d28.json` (2973 bytes, sha256 `c0e1001d50ac…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/449dd1c8-4cce-4a74-90a3-ef08a0fe9d28.snapshot.json` (156 bytes, sha256 `358de60233a9…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/449dd1c8-4cce-4a74-90a3-ef08a0fe9d28.actions.json` (2284 bytes, sha256 `ed40ca69f883…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0004`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-NORM / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/3094b314-db6c-46fc-ae67-a20ae7c027ca.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/3094b314-db6c-46fc-ae67-a20ae7c027ca.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/3094b314-db6c-46fc-ae67-a20ae7c027ca.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `artifacts/eval-20261028/traces-chimera/3094b314-db6c-46fc-ae67-a20ae7c027ca.json` (2973 bytes, sha256 `0e22373d68fe…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/3094b314-db6c-46fc-ae67-a20ae7c027ca.snapshot.json` (156 bytes, sha256 `5fc9b80d4e97…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/3094b314-db6c-46fc-ae67-a20ae7c027ca.actions.json` (2284 bytes, sha256 `652317547f89…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0006`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-NORM / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/391c7849-f7a5-4d27-b69f-5f933b3e8ac1.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/391c7849-f7a5-4d27-b69f-5f933b3e8ac1.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/391c7849-f7a5-4d27-b69f-5f933b3e8ac1.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Padded Name"]
- trace: `artifacts/eval-20261028/traces-chimera/391c7849-f7a5-4d27-b69f-5f933b3e8ac1.json` (2971 bytes, sha256 `e3f22addec8c…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/391c7849-f7a5-4d27-b69f-5f933b3e8ac1.snapshot.json` (150 bytes, sha256 `dcacee610fc6…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/391c7849-f7a5-4d27-b69f-5f933b3e8ac1.actions.json` (2284 bytes, sha256 `8b11825a2902…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0008`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-NORM / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/25084547-4d58-47fb-abcd-fe076af17a87.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/25084547-4d58-47fb-abcd-fe076af17a87.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/25084547-4d58-47fb-abcd-fe076af17a87.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Padded Name"]
- trace: `artifacts/eval-20261028/traces-chimera/25084547-4d58-47fb-abcd-fe076af17a87.json` (2971 bytes, sha256 `56ab2417ce4f…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/25084547-4d58-47fb-abcd-fe076af17a87.snapshot.json` (150 bytes, sha256 `fc5ec7b6a3ff…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/25084547-4d58-47fb-abcd-fe076af17a87.actions.json` (2284 bytes, sha256 `e79a40c52757…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0011`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-NORM / I-UNICODE / chimera · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/e0ca1dc7-a2b8-45f3-94e7-aacdce841d03.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/e0ca1dc7-a2b8-45f3-94e7-aacdce841d03.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/e0ca1dc7-a2b8-45f3-94e7-aacdce841d03.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Проект — Ünïcode ✓"]
- trace: `artifacts/eval-20261028/traces-chimera/e0ca1dc7-a2b8-45f3-94e7-aacdce841d03.json` (3024 bytes, sha256 `3a292634f393…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/e0ca1dc7-a2b8-45f3-94e7-aacdce841d03.snapshot.json` (169 bytes, sha256 `c6dd89f4e977…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/e0ca1dc7-a2b8-45f3-94e7-aacdce841d03.actions.json` (2284 bytes, sha256 `7f169ba9c8b3…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0014`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-NORM / I-UNICODE / chimera · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/ed680e8a-8652-4131-ab19-e347a1934b64.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/ed680e8a-8652-4131-ab19-e347a1934b64.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/ed680e8a-8652-4131-ab19-e347a1934b64.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Проект — Ünïcode ✓"]
- trace: `artifacts/eval-20261028/traces-chimera/ed680e8a-8652-4131-ab19-e347a1934b64.json` (3024 bytes, sha256 `39af79e7de36…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/ed680e8a-8652-4131-ab19-e347a1934b64.snapshot.json` (169 bytes, sha256 `6df58948a9e3…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/ed680e8a-8652-4131-ab19-e347a1934b64.actions.json` (2284 bytes, sha256 `0255afb3fbf9…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0017`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/196468a1-451d-4fac-9e7e-35807f1e52eb.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/196468a1-451d-4fac-9e7e-35807f1e52eb.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/196468a1-451d-4fac-9e7e-35807f1e52eb.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `artifacts/eval-20261028/traces-chimera/196468a1-451d-4fac-9e7e-35807f1e52eb.json` (2982 bytes, sha256 `62bf63e5ce51…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/196468a1-451d-4fac-9e7e-35807f1e52eb.snapshot.json` (156 bytes, sha256 `610eb94e9f05…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/196468a1-451d-4fac-9e7e-35807f1e52eb.actions.json` (2317 bytes, sha256 `a16e8793a370…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0020`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/5c875c32-d262-48c6-8820-46b087090885.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/5c875c32-d262-48c6-8820-46b087090885.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/5c875c32-d262-48c6-8820-46b087090885.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `artifacts/eval-20261028/traces-chimera/5c875c32-d262-48c6-8820-46b087090885.json` (2982 bytes, sha256 `13e82370f694…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/5c875c32-d262-48c6-8820-46b087090885.snapshot.json` (156 bytes, sha256 `b955f6d61fad…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/5c875c32-d262-48c6-8820-46b087090885.actions.json` (2317 bytes, sha256 `05e47e76e230…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0021`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/e1bebe4b-f16c-4596-b772-a39416187ec3.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/e1bebe4b-f16c-4596-b772-a39416187ec3.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/e1bebe4b-f16c-4596-b772-a39416187ec3.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Padded Name"]
- trace: `artifacts/eval-20261028/traces-chimera/e1bebe4b-f16c-4596-b772-a39416187ec3.json` (2980 bytes, sha256 `d9b58a32fe07…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/e1bebe4b-f16c-4596-b772-a39416187ec3.snapshot.json` (150 bytes, sha256 `55d391777710…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/e1bebe4b-f16c-4596-b772-a39416187ec3.actions.json` (2317 bytes, sha256 `218778ff2a59…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0023`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/33777254-cf75-4cc4-a348-c27c622d9aad.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/33777254-cf75-4cc4-a348-c27c622d9aad.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/33777254-cf75-4cc4-a348-c27c622d9aad.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Padded Name"]
- trace: `artifacts/eval-20261028/traces-chimera/33777254-cf75-4cc4-a348-c27c622d9aad.json` (2980 bytes, sha256 `f529d8604118…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/33777254-cf75-4cc4-a348-c27c622d9aad.snapshot.json` (150 bytes, sha256 `fd4498c0be92…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/33777254-cf75-4cc4-a348-c27c622d9aad.actions.json` (2317 bytes, sha256 `45ae6222a16d…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0027`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-UNICODE / chimera · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/505a0e0a-db81-4c18-a67c-5d3b3abf73a1.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/505a0e0a-db81-4c18-a67c-5d3b3abf73a1.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/505a0e0a-db81-4c18-a67c-5d3b3abf73a1.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Проект — Ünïcode ✓"]
- trace: `artifacts/eval-20261028/traces-chimera/505a0e0a-db81-4c18-a67c-5d3b3abf73a1.json` (3033 bytes, sha256 `3211d83c97a0…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/505a0e0a-db81-4c18-a67c-5d3b3abf73a1.snapshot.json` (169 bytes, sha256 `91c752e53923…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/505a0e0a-db81-4c18-a67c-5d3b3abf73a1.actions.json` (2317 bytes, sha256 `526c1df22ae0…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0029`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-UNICODE / chimera · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/5f4b5297-d15b-46a5-8f88-94e9a8e2df69.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/5f4b5297-d15b-46a5-8f88-94e9a8e2df69.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/5f4b5297-d15b-46a5-8f88-94e9a8e2df69.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Проект — Ünïcode ✓"]
- trace: `artifacts/eval-20261028/traces-chimera/5f4b5297-d15b-46a5-8f88-94e9a8e2df69.json` (3033 bytes, sha256 `9fed7008a4e9…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/5f4b5297-d15b-46a5-8f88-94e9a8e2df69.snapshot.json` (169 bytes, sha256 `63061747467a…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/5f4b5297-d15b-46a5-8f88-94e9a8e2df69.actions.json` (2317 bytes, sha256 `63102c493bb1…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0033`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/7452ef59-3a50-4a36-8120-d2ddb460a26e.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/7452ef59-3a50-4a36-8120-d2ddb460a26e.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/7452ef59-3a50-4a36-8120-d2ddb460a26e.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `artifacts/eval-20261028/traces-chimera/7452ef59-3a50-4a36-8120-d2ddb460a26e.json` (2983 bytes, sha256 `ef18b0cfad2c…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/7452ef59-3a50-4a36-8120-d2ddb460a26e.snapshot.json` (156 bytes, sha256 `f884f1685eba…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/7452ef59-3a50-4a36-8120-d2ddb460a26e.actions.json` (2320 bytes, sha256 `46b5743b82f1…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0034`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/f0351701-656b-464e-9e33-13c7c5e1bd99.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/f0351701-656b-464e-9e33-13c7c5e1bd99.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/f0351701-656b-464e-9e33-13c7c5e1bd99.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `artifacts/eval-20261028/traces-chimera/f0351701-656b-464e-9e33-13c7c5e1bd99.json` (2983 bytes, sha256 `b9a41324ec17…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/f0351701-656b-464e-9e33-13c7c5e1bd99.snapshot.json` (156 bytes, sha256 `b802db11bea4…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/f0351701-656b-464e-9e33-13c7c5e1bd99.actions.json` (2320 bytes, sha256 `b1743f321afe…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0039`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/563bd3ca-c81c-4f2a-aa2e-d662574b0630.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/563bd3ca-c81c-4f2a-aa2e-d662574b0630.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/563bd3ca-c81c-4f2a-aa2e-d662574b0630.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Padded Name"]
- trace: `artifacts/eval-20261028/traces-chimera/563bd3ca-c81c-4f2a-aa2e-d662574b0630.json` (2981 bytes, sha256 `c86ea9c28159…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/563bd3ca-c81c-4f2a-aa2e-d662574b0630.snapshot.json` (150 bytes, sha256 `138f210cdcf1…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/563bd3ca-c81c-4f2a-aa2e-d662574b0630.actions.json` (2320 bytes, sha256 `ce90f7ae5775…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0040`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/72f9b032-32e4-4ce1-a437-ebd3203bea21.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/72f9b032-32e4-4ce1-a437-ebd3203bea21.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/72f9b032-32e4-4ce1-a437-ebd3203bea21.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Padded Name"]
- trace: `artifacts/eval-20261028/traces-chimera/72f9b032-32e4-4ce1-a437-ebd3203bea21.json` (2981 bytes, sha256 `3c39b4240b9d…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/72f9b032-32e4-4ce1-a437-ebd3203bea21.snapshot.json` (150 bytes, sha256 `f5b2ae79df7f…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/72f9b032-32e4-4ce1-a437-ebd3203bea21.actions.json` (2320 bytes, sha256 `4d6adb768d93…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0041`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-UNICODE / chimera · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/98160735-1b96-45f4-8619-e37d1179096e.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/98160735-1b96-45f4-8619-e37d1179096e.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/98160735-1b96-45f4-8619-e37d1179096e.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Проект — Ünïcode ✓"]
- trace: `artifacts/eval-20261028/traces-chimera/98160735-1b96-45f4-8619-e37d1179096e.json` (3034 bytes, sha256 `19ada2695424…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/98160735-1b96-45f4-8619-e37d1179096e.snapshot.json` (169 bytes, sha256 `6c51cfddb72a…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/98160735-1b96-45f4-8619-e37d1179096e.actions.json` (2320 bytes, sha256 `a64c17b7140c…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0043`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-UNICODE / chimera · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/6bf177f7-7dd8-47f5-a121-ce64f92010cf.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/6bf177f7-7dd8-47f5-a121-ce64f92010cf.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/6bf177f7-7dd8-47f5-a121-ce64f92010cf.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Проект — Ünïcode ✓"]
- trace: `artifacts/eval-20261028/traces-chimera/6bf177f7-7dd8-47f5-a121-ce64f92010cf.json` (3034 bytes, sha256 `902b370e212c…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/6bf177f7-7dd8-47f5-a121-ce64f92010cf.snapshot.json` (169 bytes, sha256 `08466ba3fc57…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/6bf177f7-7dd8-47f5-a121-ce64f92010cf.actions.json` (2320 bytes, sha256 `1c5e2c2275eb…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0049`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/88966295-b674-4fd2-9423-592fc31437e4.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/88966295-b674-4fd2-9423-592fc31437e4.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/88966295-b674-4fd2-9423-592fc31437e4.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `artifacts/eval-20261028/traces-chimera/88966295-b674-4fd2-9423-592fc31437e4.json` (2983 bytes, sha256 `d9f07881a41e…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/88966295-b674-4fd2-9423-592fc31437e4.snapshot.json` (156 bytes, sha256 `3f3fb67e5a6f…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/88966295-b674-4fd2-9423-592fc31437e4.actions.json` (2320 bytes, sha256 `f4f8374a84a0…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0050`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/ef3cacc3-981d-4e7f-b319-f86a3eccc63f.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/ef3cacc3-981d-4e7f-b319-f86a3eccc63f.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/ef3cacc3-981d-4e7f-b319-f86a3eccc63f.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `artifacts/eval-20261028/traces-chimera/ef3cacc3-981d-4e7f-b319-f86a3eccc63f.json` (2983 bytes, sha256 `bc7c1425b41a…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/ef3cacc3-981d-4e7f-b319-f86a3eccc63f.snapshot.json` (156 bytes, sha256 `70f09dd0bc86…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/ef3cacc3-981d-4e7f-b319-f86a3eccc63f.actions.json` (2320 bytes, sha256 `39e1317d7c6d…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0051`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/ffb591b4-d4a8-43e5-9567-2004ff35431b.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/ffb591b4-d4a8-43e5-9567-2004ff35431b.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/ffb591b4-d4a8-43e5-9567-2004ff35431b.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Padded Name"]
- trace: `artifacts/eval-20261028/traces-chimera/ffb591b4-d4a8-43e5-9567-2004ff35431b.json` (2981 bytes, sha256 `fb423221dd01…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/ffb591b4-d4a8-43e5-9567-2004ff35431b.snapshot.json` (150 bytes, sha256 `bdfe0aeded3a…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/ffb591b4-d4a8-43e5-9567-2004ff35431b.actions.json` (2320 bytes, sha256 `282a922a083d…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0055`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/be95d9fb-aaf7-4aab-a1c8-1e2b45e2d56b.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/be95d9fb-aaf7-4aab-a1c8-1e2b45e2d56b.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/be95d9fb-aaf7-4aab-a1c8-1e2b45e2d56b.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Padded Name"]
- trace: `artifacts/eval-20261028/traces-chimera/be95d9fb-aaf7-4aab-a1c8-1e2b45e2d56b.json` (2981 bytes, sha256 `fa822659fb11…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/be95d9fb-aaf7-4aab-a1c8-1e2b45e2d56b.snapshot.json` (150 bytes, sha256 `2279e2c9d9fe…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/be95d9fb-aaf7-4aab-a1c8-1e2b45e2d56b.actions.json` (2320 bytes, sha256 `9f8eb3b1f826…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0057`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-UNICODE / chimera · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/a10cdf45-02d5-448b-8e4b-0968ce626d4b.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/a10cdf45-02d5-448b-8e4b-0968ce626d4b.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/a10cdf45-02d5-448b-8e4b-0968ce626d4b.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Проект — Ünïcode ✓"]
- trace: `artifacts/eval-20261028/traces-chimera/a10cdf45-02d5-448b-8e4b-0968ce626d4b.json` (3034 bytes, sha256 `04b87d9ac457…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/a10cdf45-02d5-448b-8e4b-0968ce626d4b.snapshot.json` (169 bytes, sha256 `1abe507d982c…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/a10cdf45-02d5-448b-8e4b-0968ce626d4b.actions.json` (2320 bytes, sha256 `2b8f877b4385…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0059`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-UNICODE / chimera · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/0101cfc0-78cd-4775-96bc-625636eb2fca.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/0101cfc0-78cd-4775-96bc-625636eb2fca.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/0101cfc0-78cd-4775-96bc-625636eb2fca.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Проект — Ünïcode ✓"]
- trace: `artifacts/eval-20261028/traces-chimera/0101cfc0-78cd-4775-96bc-625636eb2fca.json` (3034 bytes, sha256 `3f24e7989004…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/0101cfc0-78cd-4775-96bc-625636eb2fca.snapshot.json` (169 bytes, sha256 `fafa6a701804…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/0101cfc0-78cd-4775-96bc-625636eb2fca.actions.json` (2320 bytes, sha256 `26979cfc291f…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0063`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/aa2efd5e-45a8-4918-9926-a4fec020ef09.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/aa2efd5e-45a8-4918-9926-a4fec020ef09.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/aa2efd5e-45a8-4918-9926-a4fec020ef09.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `artifacts/eval-20261028/traces-chimera/aa2efd5e-45a8-4918-9926-a4fec020ef09.json` (2983 bytes, sha256 `ee6d5533b7a4…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/aa2efd5e-45a8-4918-9926-a4fec020ef09.snapshot.json` (156 bytes, sha256 `0ab5544cab7b…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/aa2efd5e-45a8-4918-9926-a4fec020ef09.actions.json` (2320 bytes, sha256 `83c33e58c876…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0065`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/9b746fec-9b83-4e66-80d5-b259be36d69d.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/9b746fec-9b83-4e66-80d5-b259be36d69d.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/9b746fec-9b83-4e66-80d5-b259be36d69d.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `artifacts/eval-20261028/traces-chimera/9b746fec-9b83-4e66-80d5-b259be36d69d.json` (2983 bytes, sha256 `4a65b49706fa…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/9b746fec-9b83-4e66-80d5-b259be36d69d.snapshot.json` (156 bytes, sha256 `8b5cbd805fbd…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/9b746fec-9b83-4e66-80d5-b259be36d69d.actions.json` (2320 bytes, sha256 `fb853835d314…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0066`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/d5c3f8c9-1435-414f-90c1-832e1865d063.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/d5c3f8c9-1435-414f-90c1-832e1865d063.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/d5c3f8c9-1435-414f-90c1-832e1865d063.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Padded Name"]
- trace: `artifacts/eval-20261028/traces-chimera/d5c3f8c9-1435-414f-90c1-832e1865d063.json` (2981 bytes, sha256 `47f2280cb544…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/d5c3f8c9-1435-414f-90c1-832e1865d063.snapshot.json` (150 bytes, sha256 `4b6a2657f073…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/d5c3f8c9-1435-414f-90c1-832e1865d063.actions.json` (2320 bytes, sha256 `f3fecb3dc0a5…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0069`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/ed9760c9-6f64-487d-8c53-7442adce3212.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/ed9760c9-6f64-487d-8c53-7442adce3212.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/ed9760c9-6f64-487d-8c53-7442adce3212.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Padded Name"]
- trace: `artifacts/eval-20261028/traces-chimera/ed9760c9-6f64-487d-8c53-7442adce3212.json` (2981 bytes, sha256 `baadebd581c7…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/ed9760c9-6f64-487d-8c53-7442adce3212.snapshot.json` (150 bytes, sha256 `35af39fb3ec8…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/ed9760c9-6f64-487d-8c53-7442adce3212.actions.json` (2320 bytes, sha256 `766610199fe9…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0072`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-UNICODE / chimera · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/638e8981-f87f-42d8-8c07-3b1bf90a857a.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/638e8981-f87f-42d8-8c07-3b1bf90a857a.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/638e8981-f87f-42d8-8c07-3b1bf90a857a.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Проект — Ünïcode ✓"]
- trace: `artifacts/eval-20261028/traces-chimera/638e8981-f87f-42d8-8c07-3b1bf90a857a.json` (3034 bytes, sha256 `9a161f427af3…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/638e8981-f87f-42d8-8c07-3b1bf90a857a.snapshot.json` (169 bytes, sha256 `784584ef777c…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/638e8981-f87f-42d8-8c07-3b1bf90a857a.actions.json` (2320 bytes, sha256 `fc84263e317b…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0074`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-UNICODE / chimera · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/093af616-a20b-4f0b-af11-d22fef595840.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/093af616-a20b-4f0b-af11-d22fef595840.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/093af616-a20b-4f0b-af11-d22fef595840.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Проект — Ünïcode ✓"]
- trace: `artifacts/eval-20261028/traces-chimera/093af616-a20b-4f0b-af11-d22fef595840.json` (3034 bytes, sha256 `c426e1d3e687…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/093af616-a20b-4f0b-af11-d22fef595840.snapshot.json` (169 bytes, sha256 `f5c6d2c7e286…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/093af616-a20b-4f0b-af11-d22fef595840.actions.json` (2320 bytes, sha256 `ae32e371dce7…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0077`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/5821b25f-4bf9-49df-8977-8c882213a360.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/5821b25f-4bf9-49df-8977-8c882213a360.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/5821b25f-4bf9-49df-8977-8c882213a360.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `artifacts/eval-20261028/traces-chimera/5821b25f-4bf9-49df-8977-8c882213a360.json` (2983 bytes, sha256 `3c7218599567…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/5821b25f-4bf9-49df-8977-8c882213a360.snapshot.json` (156 bytes, sha256 `3c2b830a0ded…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/5821b25f-4bf9-49df-8977-8c882213a360.actions.json` (2320 bytes, sha256 `e917a5580f78…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0078`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/e4d6b39f-8381-4ea5-99c1-c55e6e8c7ef0.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/e4d6b39f-8381-4ea5-99c1-c55e6e8c7ef0.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/e4d6b39f-8381-4ea5-99c1-c55e6e8c7ef0.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `artifacts/eval-20261028/traces-chimera/e4d6b39f-8381-4ea5-99c1-c55e6e8c7ef0.json` (2983 bytes, sha256 `5e3d974aef06…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/e4d6b39f-8381-4ea5-99c1-c55e6e8c7ef0.snapshot.json` (156 bytes, sha256 `05551e40453a…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/e4d6b39f-8381-4ea5-99c1-c55e6e8c7ef0.actions.json` (2320 bytes, sha256 `a15098e6ad4f…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0081`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/d3195113-0973-4c04-b1cb-7cb8b8b27be1.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/d3195113-0973-4c04-b1cb-7cb8b8b27be1.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/d3195113-0973-4c04-b1cb-7cb8b8b27be1.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Padded Name"]
- trace: `artifacts/eval-20261028/traces-chimera/d3195113-0973-4c04-b1cb-7cb8b8b27be1.json` (2981 bytes, sha256 `f5c5b5bd98ca…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/d3195113-0973-4c04-b1cb-7cb8b8b27be1.snapshot.json` (150 bytes, sha256 `319a08dfa2ce…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/d3195113-0973-4c04-b1cb-7cb8b8b27be1.actions.json` (2320 bytes, sha256 `ee1571bac31f…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0082`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/b6ae0743-b74b-4a67-a56d-4b0f49ee8bfe.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/b6ae0743-b74b-4a67-a56d-4b0f49ee8bfe.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/b6ae0743-b74b-4a67-a56d-4b0f49ee8bfe.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Padded Name"]
- trace: `artifacts/eval-20261028/traces-chimera/b6ae0743-b74b-4a67-a56d-4b0f49ee8bfe.json` (2981 bytes, sha256 `e9c3cd6a54a2…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/b6ae0743-b74b-4a67-a56d-4b0f49ee8bfe.snapshot.json` (150 bytes, sha256 `3f54efaabf91…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/b6ae0743-b74b-4a67-a56d-4b0f49ee8bfe.actions.json` (2320 bytes, sha256 `b86393b2988b…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0087`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-UNICODE / chimera · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/58417b50-c7d4-4e57-ac72-72fbd59bf441.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/58417b50-c7d4-4e57-ac72-72fbd59bf441.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/58417b50-c7d4-4e57-ac72-72fbd59bf441.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Проект — Ünïcode ✓"]
- trace: `artifacts/eval-20261028/traces-chimera/58417b50-c7d4-4e57-ac72-72fbd59bf441.json` (3034 bytes, sha256 `05a5c010d443…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/58417b50-c7d4-4e57-ac72-72fbd59bf441.snapshot.json` (169 bytes, sha256 `8582ee6418b8…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/58417b50-c7d4-4e57-ac72-72fbd59bf441.actions.json` (2320 bytes, sha256 `e2086d1345c2…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0090`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-UNICODE / chimera · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-chimera/224063ad-e95e-4d1b-837a-aa111cbf808d.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/224063ad-e95e-4d1b-837a-aa111cbf808d.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/224063ad-e95e-4d1b-837a-aa111cbf808d.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Проект — Ünïcode ✓"]
- trace: `artifacts/eval-20261028/traces-chimera/224063ad-e95e-4d1b-837a-aa111cbf808d.json` (3034 bytes, sha256 `5d6c19577930…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/224063ad-e95e-4d1b-837a-aa111cbf808d.snapshot.json` (169 bytes, sha256 `5f26f16fcba4…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/224063ad-e95e-4d1b-837a-aa111cbf808d.actions.json` (2320 bytes, sha256 `a9caba09c73a…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `eval-20261028-chimera::trial-0091`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-DIS / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/4bb74591-1788-470d-ad1d-3f79c0109027.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/4bb74591-1788-470d-ad1d-3f79c0109027.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/4bb74591-1788-470d-ad1d-3f79c0109027.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/4bb74591-1788-470d-ad1d-3f79c0109027.json` (3918 bytes, sha256 `0f5d43e22b57…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/4bb74591-1788-470d-ad1d-3f79c0109027.snapshot.json` (138 bytes, sha256 `370927fa0fa8…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/4bb74591-1788-470d-ad1d-3f79c0109027.actions.json` (1731 bytes, sha256 `357e16a33531…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/4bb74591-1788-470d-ad1d-3f79c0109027.png` (present)

### `eval-20261028-chimera::trial-0093`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-DIS / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/e75b7100-9785-4518-8069-825126825dc2.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/e75b7100-9785-4518-8069-825126825dc2.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/e75b7100-9785-4518-8069-825126825dc2.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/e75b7100-9785-4518-8069-825126825dc2.json` (3918 bytes, sha256 `f2ab4e8c80fa…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/e75b7100-9785-4518-8069-825126825dc2.snapshot.json` (138 bytes, sha256 `2b5d2ee3024b…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/e75b7100-9785-4518-8069-825126825dc2.actions.json` (1731 bytes, sha256 `ed57adfcfc62…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/e75b7100-9785-4518-8069-825126825dc2.png` (present)

### `eval-20261028-chimera::trial-0098`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-DIS / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/ce403f69-3c76-4578-9072-f5c3d94c2347.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/ce403f69-3c76-4578-9072-f5c3d94c2347.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/ce403f69-3c76-4578-9072-f5c3d94c2347.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/ce403f69-3c76-4578-9072-f5c3d94c2347.json` (3912 bytes, sha256 `3116b77b69da…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/ce403f69-3c76-4578-9072-f5c3d94c2347.snapshot.json` (138 bytes, sha256 `8f85bbb39209…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/ce403f69-3c76-4578-9072-f5c3d94c2347.actions.json` (1731 bytes, sha256 `0ba43f50e755…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/ce403f69-3c76-4578-9072-f5c3d94c2347.png` (present)

### `eval-20261028-chimera::trial-0100`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
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

### `eval-20261028-chimera::trial-0101`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-DIS / I-UNICODE / chimera · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/c82c4aa8-45d8-4e11-af70-19ba85796732.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/c82c4aa8-45d8-4e11-af70-19ba85796732.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/c82c4aa8-45d8-4e11-af70-19ba85796732.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/c82c4aa8-45d8-4e11-af70-19ba85796732.json` (4071 bytes, sha256 `51a6348ddf3e…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/c82c4aa8-45d8-4e11-af70-19ba85796732.snapshot.json` (138 bytes, sha256 `e43c59a991a1…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/c82c4aa8-45d8-4e11-af70-19ba85796732.actions.json` (1731 bytes, sha256 `9dc56c101ee8…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/c82c4aa8-45d8-4e11-af70-19ba85796732.png` (present)

### `eval-20261028-chimera::trial-0103`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-DIS / I-UNICODE / chimera · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/e4aa350a-f7bd-43c0-8410-63c0d0cfc12a.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/e4aa350a-f7bd-43c0-8410-63c0d0cfc12a.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/e4aa350a-f7bd-43c0-8410-63c0d0cfc12a.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/e4aa350a-f7bd-43c0-8410-63c0d0cfc12a.json` (4071 bytes, sha256 `6ef61e5757dc…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/e4aa350a-f7bd-43c0-8410-63c0d0cfc12a.snapshot.json` (138 bytes, sha256 `81a407c6c96f…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/e4aa350a-f7bd-43c0-8410-63c0d0cfc12a.actions.json` (1731 bytes, sha256 `15714dba0dcf…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/e4aa350a-f7bd-43c0-8410-63c0d0cfc12a.png` (present)

### `eval-20261028-chimera::trial-0106`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/8c05c538-adc7-43ed-843e-0906d86f4341.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/8c05c538-adc7-43ed-843e-0906d86f4341.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/8c05c538-adc7-43ed-843e-0906d86f4341.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/8c05c538-adc7-43ed-843e-0906d86f4341.json` (3927 bytes, sha256 `d5fedfc3f94c…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/8c05c538-adc7-43ed-843e-0906d86f4341.snapshot.json` (138 bytes, sha256 `6fc29c854af2…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/8c05c538-adc7-43ed-843e-0906d86f4341.actions.json` (1758 bytes, sha256 `5e104ba0841f…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/8c05c538-adc7-43ed-843e-0906d86f4341.png` (present)

### `eval-20261028-chimera::trial-0107`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/3c5ab3b5-7896-40b3-8e49-a5d62ce105a5.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/3c5ab3b5-7896-40b3-8e49-a5d62ce105a5.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/3c5ab3b5-7896-40b3-8e49-a5d62ce105a5.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/3c5ab3b5-7896-40b3-8e49-a5d62ce105a5.json` (3927 bytes, sha256 `db5a2b3a398b…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/3c5ab3b5-7896-40b3-8e49-a5d62ce105a5.snapshot.json` (138 bytes, sha256 `5866fd3c0bae…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/3c5ab3b5-7896-40b3-8e49-a5d62ce105a5.actions.json` (1758 bytes, sha256 `7944fd3c7e6b…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/3c5ab3b5-7896-40b3-8e49-a5d62ce105a5.png` (present)

### `eval-20261028-chimera::trial-0111`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/f1580323-39ae-4194-b82e-eb8e63b4e2a8.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/f1580323-39ae-4194-b82e-eb8e63b4e2a8.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/f1580323-39ae-4194-b82e-eb8e63b4e2a8.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/f1580323-39ae-4194-b82e-eb8e63b4e2a8.json` (3921 bytes, sha256 `657bb995e302…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/f1580323-39ae-4194-b82e-eb8e63b4e2a8.snapshot.json` (138 bytes, sha256 `45ef02d64203…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/f1580323-39ae-4194-b82e-eb8e63b4e2a8.actions.json` (1758 bytes, sha256 `5bcb55014e37…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/f1580323-39ae-4194-b82e-eb8e63b4e2a8.png` (present)

### `eval-20261028-chimera::trial-0115`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/58fd4a9a-806c-4ad4-bdca-ebf07435a88a.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/58fd4a9a-806c-4ad4-bdca-ebf07435a88a.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/58fd4a9a-806c-4ad4-bdca-ebf07435a88a.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/58fd4a9a-806c-4ad4-bdca-ebf07435a88a.json` (3921 bytes, sha256 `c93573cca888…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/58fd4a9a-806c-4ad4-bdca-ebf07435a88a.snapshot.json` (138 bytes, sha256 `fd2b6c9dc51c…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/58fd4a9a-806c-4ad4-bdca-ebf07435a88a.actions.json` (1758 bytes, sha256 `561a8631a745…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/58fd4a9a-806c-4ad4-bdca-ebf07435a88a.png` (present)

### `eval-20261028-chimera::trial-0118`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-UNICODE / chimera · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/b78d25e1-caa4-48c7-89f2-59ec3720d0ae.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/b78d25e1-caa4-48c7-89f2-59ec3720d0ae.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/b78d25e1-caa4-48c7-89f2-59ec3720d0ae.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/b78d25e1-caa4-48c7-89f2-59ec3720d0ae.json` (4080 bytes, sha256 `e3291cc67407…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/b78d25e1-caa4-48c7-89f2-59ec3720d0ae.snapshot.json` (138 bytes, sha256 `5c27f77df95c…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/b78d25e1-caa4-48c7-89f2-59ec3720d0ae.actions.json` (1758 bytes, sha256 `b42e56d423d0…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/b78d25e1-caa4-48c7-89f2-59ec3720d0ae.png` (present)

### `eval-20261028-chimera::trial-0119`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-UNICODE / chimera · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/a9895f6e-d045-483d-a920-7fc53d73c8ec.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/a9895f6e-d045-483d-a920-7fc53d73c8ec.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/a9895f6e-d045-483d-a920-7fc53d73c8ec.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/a9895f6e-d045-483d-a920-7fc53d73c8ec.json` (4080 bytes, sha256 `7f490aabfe05…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/a9895f6e-d045-483d-a920-7fc53d73c8ec.snapshot.json` (138 bytes, sha256 `896d5dc92e80…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/a9895f6e-d045-483d-a920-7fc53d73c8ec.actions.json` (1758 bytes, sha256 `f5eb224aacd0…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/a9895f6e-d045-483d-a920-7fc53d73c8ec.png` (present)

### `eval-20261028-chimera::trial-0122`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/36e27b0b-3f43-4817-8c24-4a7438dc044b.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/36e27b0b-3f43-4817-8c24-4a7438dc044b.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/36e27b0b-3f43-4817-8c24-4a7438dc044b.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/36e27b0b-3f43-4817-8c24-4a7438dc044b.json` (3928 bytes, sha256 `2d1d644bbf42…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/36e27b0b-3f43-4817-8c24-4a7438dc044b.snapshot.json` (138 bytes, sha256 `398882674e58…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/36e27b0b-3f43-4817-8c24-4a7438dc044b.actions.json` (1761 bytes, sha256 `a70956a2b16f…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/36e27b0b-3f43-4817-8c24-4a7438dc044b.png` (present)

### `eval-20261028-chimera::trial-0123`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/ff67c88b-768d-4165-984e-05a2242973cc.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/ff67c88b-768d-4165-984e-05a2242973cc.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/ff67c88b-768d-4165-984e-05a2242973cc.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/ff67c88b-768d-4165-984e-05a2242973cc.json` (3928 bytes, sha256 `ef9926077e01…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/ff67c88b-768d-4165-984e-05a2242973cc.snapshot.json` (138 bytes, sha256 `e9d7ea8f2dcb…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/ff67c88b-768d-4165-984e-05a2242973cc.actions.json` (1761 bytes, sha256 `2da595cb7fc8…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/ff67c88b-768d-4165-984e-05a2242973cc.png` (present)

### `eval-20261028-chimera::trial-0127`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/2ebbf3d4-75c2-41c3-9ce5-e4f7ce61c586.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/2ebbf3d4-75c2-41c3-9ce5-e4f7ce61c586.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/2ebbf3d4-75c2-41c3-9ce5-e4f7ce61c586.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/2ebbf3d4-75c2-41c3-9ce5-e4f7ce61c586.json` (3922 bytes, sha256 `2d02df92df77…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/2ebbf3d4-75c2-41c3-9ce5-e4f7ce61c586.snapshot.json` (138 bytes, sha256 `831d3bd4bfc6…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/2ebbf3d4-75c2-41c3-9ce5-e4f7ce61c586.actions.json` (1761 bytes, sha256 `1032e4020f67…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/2ebbf3d4-75c2-41c3-9ce5-e4f7ce61c586.png` (present)

### `eval-20261028-chimera::trial-0129`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/106e1722-f097-44ce-a19d-5e2811c15b9a.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/106e1722-f097-44ce-a19d-5e2811c15b9a.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/106e1722-f097-44ce-a19d-5e2811c15b9a.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/106e1722-f097-44ce-a19d-5e2811c15b9a.json` (3922 bytes, sha256 `5363ae757958…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/106e1722-f097-44ce-a19d-5e2811c15b9a.snapshot.json` (138 bytes, sha256 `7e073cff7340…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/106e1722-f097-44ce-a19d-5e2811c15b9a.actions.json` (1761 bytes, sha256 `3fa5d62afa43…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/106e1722-f097-44ce-a19d-5e2811c15b9a.png` (present)

### `eval-20261028-chimera::trial-0131`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-UNICODE / chimera · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/b70bf19a-6eef-4ff3-93e6-f2bb6cab4c69.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/b70bf19a-6eef-4ff3-93e6-f2bb6cab4c69.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/b70bf19a-6eef-4ff3-93e6-f2bb6cab4c69.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/b70bf19a-6eef-4ff3-93e6-f2bb6cab4c69.json` (4081 bytes, sha256 `06503115083b…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/b70bf19a-6eef-4ff3-93e6-f2bb6cab4c69.snapshot.json` (138 bytes, sha256 `48feeb16f182…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/b70bf19a-6eef-4ff3-93e6-f2bb6cab4c69.actions.json` (1761 bytes, sha256 `a13108cfb9f0…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/b70bf19a-6eef-4ff3-93e6-f2bb6cab4c69.png` (present)

### `eval-20261028-chimera::trial-0133`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-UNICODE / chimera · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/4825292d-89ad-478c-bc88-43fee0dfb593.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/4825292d-89ad-478c-bc88-43fee0dfb593.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/4825292d-89ad-478c-bc88-43fee0dfb593.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/4825292d-89ad-478c-bc88-43fee0dfb593.json` (4081 bytes, sha256 `303693b23ea2…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/4825292d-89ad-478c-bc88-43fee0dfb593.snapshot.json` (138 bytes, sha256 `889e2ace397c…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/4825292d-89ad-478c-bc88-43fee0dfb593.actions.json` (1761 bytes, sha256 `f3de93921195…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/4825292d-89ad-478c-bc88-43fee0dfb593.png` (present)

### `eval-20261028-chimera::trial-0136`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/33f28145-42eb-4eb5-9d40-a07ee0a34b15.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/33f28145-42eb-4eb5-9d40-a07ee0a34b15.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/33f28145-42eb-4eb5-9d40-a07ee0a34b15.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/33f28145-42eb-4eb5-9d40-a07ee0a34b15.json` (3928 bytes, sha256 `002f1c62790a…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/33f28145-42eb-4eb5-9d40-a07ee0a34b15.snapshot.json` (138 bytes, sha256 `49ea60d19347…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/33f28145-42eb-4eb5-9d40-a07ee0a34b15.actions.json` (1761 bytes, sha256 `f6b4175926b3…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/33f28145-42eb-4eb5-9d40-a07ee0a34b15.png` (present)

### `eval-20261028-chimera::trial-0138`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/ad63c6e0-349b-4969-bd28-6f383c2a1332.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/ad63c6e0-349b-4969-bd28-6f383c2a1332.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/ad63c6e0-349b-4969-bd28-6f383c2a1332.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/ad63c6e0-349b-4969-bd28-6f383c2a1332.json` (3928 bytes, sha256 `acc1966db50d…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/ad63c6e0-349b-4969-bd28-6f383c2a1332.snapshot.json` (138 bytes, sha256 `e789fc193bd6…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/ad63c6e0-349b-4969-bd28-6f383c2a1332.actions.json` (1761 bytes, sha256 `1d7472bcdad1…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/ad63c6e0-349b-4969-bd28-6f383c2a1332.png` (present)

### `eval-20261028-chimera::trial-0142`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
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

### `eval-20261028-chimera::trial-0145`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/aa567fb3-066c-4250-a65c-dd106415a53f.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/aa567fb3-066c-4250-a65c-dd106415a53f.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/aa567fb3-066c-4250-a65c-dd106415a53f.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/aa567fb3-066c-4250-a65c-dd106415a53f.json` (3922 bytes, sha256 `918a46d760aa…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/aa567fb3-066c-4250-a65c-dd106415a53f.snapshot.json` (138 bytes, sha256 `dbdb490d5d4c…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/aa567fb3-066c-4250-a65c-dd106415a53f.actions.json` (1761 bytes, sha256 `6da93ed1d0c9…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/aa567fb3-066c-4250-a65c-dd106415a53f.png` (present)

### `eval-20261028-chimera::trial-0146`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-UNICODE / chimera · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/1c74d1ee-be66-4607-886b-945ac3411873.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/1c74d1ee-be66-4607-886b-945ac3411873.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/1c74d1ee-be66-4607-886b-945ac3411873.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/1c74d1ee-be66-4607-886b-945ac3411873.json` (4081 bytes, sha256 `8ea6cab41f86…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/1c74d1ee-be66-4607-886b-945ac3411873.snapshot.json` (138 bytes, sha256 `0366d595d802…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/1c74d1ee-be66-4607-886b-945ac3411873.actions.json` (1761 bytes, sha256 `94946bae88f5…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/1c74d1ee-be66-4607-886b-945ac3411873.png` (present)

### `eval-20261028-chimera::trial-0147`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-UNICODE / chimera · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/4a1b887b-7800-48b2-b4df-bc6201c28836.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/4a1b887b-7800-48b2-b4df-bc6201c28836.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/4a1b887b-7800-48b2-b4df-bc6201c28836.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/4a1b887b-7800-48b2-b4df-bc6201c28836.json` (4081 bytes, sha256 `4cb5cffa9ada…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/4a1b887b-7800-48b2-b4df-bc6201c28836.snapshot.json` (138 bytes, sha256 `11e9809fa9d6…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/4a1b887b-7800-48b2-b4df-bc6201c28836.actions.json` (1761 bytes, sha256 `f4f6e6f57b1b…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/4a1b887b-7800-48b2-b4df-bc6201c28836.png` (present)

### `eval-20261028-chimera::trial-0153`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/c0c41847-dbe2-4c48-8ded-7d52a16a6b6f.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/c0c41847-dbe2-4c48-8ded-7d52a16a6b6f.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/c0c41847-dbe2-4c48-8ded-7d52a16a6b6f.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/c0c41847-dbe2-4c48-8ded-7d52a16a6b6f.json` (3928 bytes, sha256 `37d42c850a21…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/c0c41847-dbe2-4c48-8ded-7d52a16a6b6f.snapshot.json` (138 bytes, sha256 `e22d8921e153…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/c0c41847-dbe2-4c48-8ded-7d52a16a6b6f.actions.json` (1761 bytes, sha256 `c5eea3097cad…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/c0c41847-dbe2-4c48-8ded-7d52a16a6b6f.png` (present)

### `eval-20261028-chimera::trial-0154`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/60e27849-3263-4345-88fa-28f7411104a6.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/60e27849-3263-4345-88fa-28f7411104a6.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/60e27849-3263-4345-88fa-28f7411104a6.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/60e27849-3263-4345-88fa-28f7411104a6.json` (3928 bytes, sha256 `fcd5adc8d3fb…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/60e27849-3263-4345-88fa-28f7411104a6.snapshot.json` (138 bytes, sha256 `8640f9ff6e76…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/60e27849-3263-4345-88fa-28f7411104a6.actions.json` (1761 bytes, sha256 `79e4a28addd8…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/60e27849-3263-4345-88fa-28f7411104a6.png` (present)

### `eval-20261028-chimera::trial-0156`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/2604a02f-aa7d-4e00-ab64-f8b986a0cd2a.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/2604a02f-aa7d-4e00-ab64-f8b986a0cd2a.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/2604a02f-aa7d-4e00-ab64-f8b986a0cd2a.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/2604a02f-aa7d-4e00-ab64-f8b986a0cd2a.json` (3922 bytes, sha256 `c0461678a418…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/2604a02f-aa7d-4e00-ab64-f8b986a0cd2a.snapshot.json` (138 bytes, sha256 `60fcadb751a6…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/2604a02f-aa7d-4e00-ab64-f8b986a0cd2a.actions.json` (1761 bytes, sha256 `70f63dfa8580…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/2604a02f-aa7d-4e00-ab64-f8b986a0cd2a.png` (present)

### `eval-20261028-chimera::trial-0160`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/9adfd349-8638-4af4-b0a6-92df25ed8302.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/9adfd349-8638-4af4-b0a6-92df25ed8302.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/9adfd349-8638-4af4-b0a6-92df25ed8302.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/9adfd349-8638-4af4-b0a6-92df25ed8302.json` (3922 bytes, sha256 `58485e59a9e9…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/9adfd349-8638-4af4-b0a6-92df25ed8302.snapshot.json` (138 bytes, sha256 `b3470ce3c2c7…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/9adfd349-8638-4af4-b0a6-92df25ed8302.actions.json` (1761 bytes, sha256 `4508be1b755c…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/9adfd349-8638-4af4-b0a6-92df25ed8302.png` (present)

### `eval-20261028-chimera::trial-0161`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-UNICODE / chimera · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/a2e0bf13-efd9-48f4-adb9-a501a922eb8a.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/a2e0bf13-efd9-48f4-adb9-a501a922eb8a.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/a2e0bf13-efd9-48f4-adb9-a501a922eb8a.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/a2e0bf13-efd9-48f4-adb9-a501a922eb8a.json` (4081 bytes, sha256 `d172b1f7bc29…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/a2e0bf13-efd9-48f4-adb9-a501a922eb8a.snapshot.json` (138 bytes, sha256 `4802c71dbcf6…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/a2e0bf13-efd9-48f4-adb9-a501a922eb8a.actions.json` (1761 bytes, sha256 `aca5983b72ea…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/a2e0bf13-efd9-48f4-adb9-a501a922eb8a.png` (present)

### `eval-20261028-chimera::trial-0165`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-UNICODE / chimera · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/4cde7cf6-81e5-41d2-89dd-9ce666744fdf.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/4cde7cf6-81e5-41d2-89dd-9ce666744fdf.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/4cde7cf6-81e5-41d2-89dd-9ce666744fdf.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/4cde7cf6-81e5-41d2-89dd-9ce666744fdf.json` (4081 bytes, sha256 `880b8dd59b00…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/4cde7cf6-81e5-41d2-89dd-9ce666744fdf.snapshot.json` (138 bytes, sha256 `a40946615e19…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/4cde7cf6-81e5-41d2-89dd-9ce666744fdf.actions.json` (1761 bytes, sha256 `b75c1ecc4ff5…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/4cde7cf6-81e5-41d2-89dd-9ce666744fdf.png` (present)

### `eval-20261028-chimera::trial-0167`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/1cbdbb49-e6e8-435d-9d5b-9cd3e020ba02.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/1cbdbb49-e6e8-435d-9d5b-9cd3e020ba02.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/1cbdbb49-e6e8-435d-9d5b-9cd3e020ba02.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/1cbdbb49-e6e8-435d-9d5b-9cd3e020ba02.json` (3928 bytes, sha256 `c1c5758a7fb2…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/1cbdbb49-e6e8-435d-9d5b-9cd3e020ba02.snapshot.json` (138 bytes, sha256 `95fc77d7ff8d…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/1cbdbb49-e6e8-435d-9d5b-9cd3e020ba02.actions.json` (1761 bytes, sha256 `9eae0a9aa1b0…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/1cbdbb49-e6e8-435d-9d5b-9cd3e020ba02.png` (present)

### `eval-20261028-chimera::trial-0170`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/c1412559-b255-4d3b-87e7-6c6144a07ae7.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/c1412559-b255-4d3b-87e7-6c6144a07ae7.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/c1412559-b255-4d3b-87e7-6c6144a07ae7.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/c1412559-b255-4d3b-87e7-6c6144a07ae7.json` (3928 bytes, sha256 `f70c9925eabf…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/c1412559-b255-4d3b-87e7-6c6144a07ae7.snapshot.json` (138 bytes, sha256 `59ed88fb6901…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/c1412559-b255-4d3b-87e7-6c6144a07ae7.actions.json` (1761 bytes, sha256 `7c78ece2d3df…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/c1412559-b255-4d3b-87e7-6c6144a07ae7.png` (present)

### `eval-20261028-chimera::trial-0172`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/a619bc7e-c94f-4e91-99dd-a7ba5a666b2d.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/a619bc7e-c94f-4e91-99dd-a7ba5a666b2d.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/a619bc7e-c94f-4e91-99dd-a7ba5a666b2d.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/a619bc7e-c94f-4e91-99dd-a7ba5a666b2d.json` (3922 bytes, sha256 `e40fcc1a2888…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/a619bc7e-c94f-4e91-99dd-a7ba5a666b2d.snapshot.json` (138 bytes, sha256 `01ef8747f16c…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/a619bc7e-c94f-4e91-99dd-a7ba5a666b2d.actions.json` (1761 bytes, sha256 `a13c568149bc…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/a619bc7e-c94f-4e91-99dd-a7ba5a666b2d.png` (present)

### `eval-20261028-chimera::trial-0175`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-SPACE / chimera · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/9f8027d2-279f-49cc-903a-4b2ec85914b5.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/9f8027d2-279f-49cc-903a-4b2ec85914b5.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/9f8027d2-279f-49cc-903a-4b2ec85914b5.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/9f8027d2-279f-49cc-903a-4b2ec85914b5.json` (3922 bytes, sha256 `ff9ecc7276dd…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/9f8027d2-279f-49cc-903a-4b2ec85914b5.snapshot.json` (138 bytes, sha256 `5a016f05c07e…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/9f8027d2-279f-49cc-903a-4b2ec85914b5.actions.json` (1761 bytes, sha256 `53bdc14979e6…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/9f8027d2-279f-49cc-903a-4b2ec85914b5.png` (present)

### `eval-20261028-chimera::trial-0176`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-UNICODE / chimera · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/49b8ee20-5da4-4e3c-b0ee-8bd6b375c8b3.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/49b8ee20-5da4-4e3c-b0ee-8bd6b375c8b3.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/49b8ee20-5da4-4e3c-b0ee-8bd6b375c8b3.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/49b8ee20-5da4-4e3c-b0ee-8bd6b375c8b3.json` (4081 bytes, sha256 `f60b90ef43e8…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/49b8ee20-5da4-4e3c-b0ee-8bd6b375c8b3.snapshot.json` (138 bytes, sha256 `108859c710c5…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/49b8ee20-5da4-4e3c-b0ee-8bd6b375c8b3.actions.json` (1761 bytes, sha256 `0c9a0ebf5feb…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/49b8ee20-5da4-4e3c-b0ee-8bd6b375c8b3.png` (present)

### `eval-20261028-chimera::trial-0179`

- Population: primary evaluation (eval-20261028) · Driver B · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-UNICODE / chimera · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-chimera/fda8daa7-5403-4bcb-8de1-3385903feb3c.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-chimera/fda8daa7-5403-4bcb-8de1-3385903feb3c.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-chimera/fda8daa7-5403-4bcb-8de1-3385903feb3c.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-chimera/fda8daa7-5403-4bcb-8de1-3385903feb3c.json` (4081 bytes, sha256 `f0fc261e9db5…`, verified)
- snapshot: `artifacts/eval-20261028/traces-chimera/fda8daa7-5403-4bcb-8de1-3385903feb3c.snapshot.json` (138 bytes, sha256 `b4a5ffaf0c84…`, verified)
- actions: `artifacts/eval-20261028/traces-chimera/fda8daa7-5403-4bcb-8de1-3385903feb3c.actions.json` (1761 bytes, sha256 `e7946c8e8afa…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/fda8daa7-5403-4bcb-8de1-3385903feb3c.png` (present)

### `eval-20261028-baseline-a::trial-0003`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-NORM / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/0c2e8c01-2fd5-43a3-aa83-e86b60eeb1b3.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/0c2e8c01-2fd5-43a3-aa83-e86b60eeb1b3.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/0c2e8c01-2fd5-43a3-aa83-e86b60eeb1b3.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 3 steps · 5 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `artifacts/eval-20261028/traces-baseline-a/0c2e8c01-2fd5-43a3-aa83-e86b60eeb1b3.replay.json` (560 bytes, sha256 `0592185d4273…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/0c2e8c01-2fd5-43a3-aa83-e86b60eeb1b3.snapshot.json` (156 bytes, sha256 `eaf58298b037…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/0c2e8c01-2fd5-43a3-aa83-e86b60eeb1b3.actions.json` (1708 bytes, sha256 `166517dbb93d…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0005`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-NORM / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/c207af31-eb95-4820-ac62-4a32bf11bcec.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/c207af31-eb95-4820-ac62-4a32bf11bcec.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/c207af31-eb95-4820-ac62-4a32bf11bcec.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 3 steps · 5 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `artifacts/eval-20261028/traces-baseline-a/c207af31-eb95-4820-ac62-4a32bf11bcec.replay.json` (560 bytes, sha256 `531c53dcc619…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/c207af31-eb95-4820-ac62-4a32bf11bcec.snapshot.json` (156 bytes, sha256 `1e23b680f6cb…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/c207af31-eb95-4820-ac62-4a32bf11bcec.actions.json` (1708 bytes, sha256 `86a01029cd2b…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0007`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-NORM / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/10ea31c6-41d6-4ef5-baf7-f9b45ff749f3.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/10ea31c6-41d6-4ef5-baf7-f9b45ff749f3.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/10ea31c6-41d6-4ef5-baf7-f9b45ff749f3.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 3 steps · 5 observed actions · snapshot confirmation_visible=true items=["Padded Name"]
- trace: `artifacts/eval-20261028/traces-baseline-a/10ea31c6-41d6-4ef5-baf7-f9b45ff749f3.replay.json` (560 bytes, sha256 `6559199b20b9…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/10ea31c6-41d6-4ef5-baf7-f9b45ff749f3.snapshot.json` (150 bytes, sha256 `7b6df03d6abb…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/10ea31c6-41d6-4ef5-baf7-f9b45ff749f3.actions.json` (1708 bytes, sha256 `45e382b2acbd…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0009`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-NORM / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/4606f72f-1e04-42e0-a694-f982366943d5.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/4606f72f-1e04-42e0-a694-f982366943d5.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/4606f72f-1e04-42e0-a694-f982366943d5.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 3 steps · 5 observed actions · snapshot confirmation_visible=true items=["Padded Name"]
- trace: `artifacts/eval-20261028/traces-baseline-a/4606f72f-1e04-42e0-a694-f982366943d5.replay.json` (560 bytes, sha256 `b4f18476f11c…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/4606f72f-1e04-42e0-a694-f982366943d5.snapshot.json` (150 bytes, sha256 `4f0f420f4354…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/4606f72f-1e04-42e0-a694-f982366943d5.actions.json` (1708 bytes, sha256 `806bf26bef41…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0011`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-NORM / I-UNICODE / baseline-a · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/1543fc77-078f-4474-9508-f569218c63bc.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/1543fc77-078f-4474-9508-f569218c63bc.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/1543fc77-078f-4474-9508-f569218c63bc.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 3 steps · 5 observed actions · snapshot confirmation_visible=true items=["Проект — Ünïcode ✓"]
- trace: `artifacts/eval-20261028/traces-baseline-a/1543fc77-078f-4474-9508-f569218c63bc.replay.json` (560 bytes, sha256 `4ebe300ae1a5…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/1543fc77-078f-4474-9508-f569218c63bc.snapshot.json` (169 bytes, sha256 `989a334e1081…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/1543fc77-078f-4474-9508-f569218c63bc.actions.json` (1708 bytes, sha256 `18617e13b8d5…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0013`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-NORM / I-UNICODE / baseline-a · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/21bee0e2-9c07-4663-b73b-bf86c5d2d450.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/21bee0e2-9c07-4663-b73b-bf86c5d2d450.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/21bee0e2-9c07-4663-b73b-bf86c5d2d450.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 3 steps · 5 observed actions · snapshot confirmation_visible=true items=["Проект — Ünïcode ✓"]
- trace: `artifacts/eval-20261028/traces-baseline-a/21bee0e2-9c07-4663-b73b-bf86c5d2d450.replay.json` (560 bytes, sha256 `c554cea91bb2…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/21bee0e2-9c07-4663-b73b-bf86c5d2d450.snapshot.json` (169 bytes, sha256 `5972ae0ced6e…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/21bee0e2-9c07-4663-b73b-bf86c5d2d450.actions.json` (1708 bytes, sha256 `5ca392040922…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0016`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/57c7763a-a2f7-4663-ac85-18e8778f61e3.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/57c7763a-a2f7-4663-ac85-18e8778f61e3.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/57c7763a-a2f7-4663-ac85-18e8778f61e3.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/57c7763a-a2f7-4663-ac85-18e8778f61e3.replay.json` (484 bytes, sha256 `3c42c337c6c2…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/57c7763a-a2f7-4663-ac85-18e8778f61e3.snapshot.json` (138 bytes, sha256 `9e5c31635b69…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/57c7763a-a2f7-4663-ac85-18e8778f61e3.actions.json` (1437 bytes, sha256 `0e2b882d36c8…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0017`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/850040ea-3a9e-4fef-8c6a-94b4d8c0378b.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/850040ea-3a9e-4fef-8c6a-94b4d8c0378b.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/850040ea-3a9e-4fef-8c6a-94b4d8c0378b.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/850040ea-3a9e-4fef-8c6a-94b4d8c0378b.replay.json` (484 bytes, sha256 `b13ab72754b9…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/850040ea-3a9e-4fef-8c6a-94b4d8c0378b.snapshot.json` (138 bytes, sha256 `0a042c74c0b9…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/850040ea-3a9e-4fef-8c6a-94b4d8c0378b.actions.json` (1437 bytes, sha256 `ad5086791fe2…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0021`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("  Padded Name  ")
  - attempting fill action
 …`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/7448b361-dac8-4969-a8da-58425ec5b90c.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/7448b361-dac8-4969-a8da-58425ec5b90c.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/7448b361-dac8-4969-a8da-58425ec5b90c.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/7448b361-dac8-4969-a8da-58425ec5b90c.replay.json` (484 bytes, sha256 `03807e4fa633…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/7448b361-dac8-4969-a8da-58425ec5b90c.snapshot.json` (138 bytes, sha256 `52a6b4a1d5a5…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/7448b361-dac8-4969-a8da-58425ec5b90c.actions.json` (1437 bytes, sha256 `dcb12bca3994…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0024`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("  Padded Name  ")
  - attempting fill action
 …`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/93033cf6-5b5c-42fa-b48f-00f797dd2ef6.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/93033cf6-5b5c-42fa-b48f-00f797dd2ef6.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/93033cf6-5b5c-42fa-b48f-00f797dd2ef6.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/93033cf6-5b5c-42fa-b48f-00f797dd2ef6.replay.json` (484 bytes, sha256 `b9c70d7bc201…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/93033cf6-5b5c-42fa-b48f-00f797dd2ef6.snapshot.json` (138 bytes, sha256 `ec64f87fb5f1…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/93033cf6-5b5c-42fa-b48f-00f797dd2ef6.actions.json` (1437 bytes, sha256 `f96d4f544cfe…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0027`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-UNICODE / baseline-a · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Проект — Ünïcode ✓")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/328db666-0da8-4891-995b-d485ef0bb0f4.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/328db666-0da8-4891-995b-d485ef0bb0f4.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/328db666-0da8-4891-995b-d485ef0bb0f4.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/328db666-0da8-4891-995b-d485ef0bb0f4.replay.json` (484 bytes, sha256 `5e760337e6ec…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/328db666-0da8-4891-995b-d485ef0bb0f4.snapshot.json` (138 bytes, sha256 `d1a3d1f11f8f…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/328db666-0da8-4891-995b-d485ef0bb0f4.actions.json` (1437 bytes, sha256 `efcce84220d5…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0029`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-UNICODE / baseline-a · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Проект — Ünïcode ✓")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/02640753-5cde-48b4-8638-f91a5e549493.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/02640753-5cde-48b4-8638-f91a5e549493.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/02640753-5cde-48b4-8638-f91a5e549493.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/02640753-5cde-48b4-8638-f91a5e549493.replay.json` (484 bytes, sha256 `f4a109970b26…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/02640753-5cde-48b4-8638-f91a5e549493.snapshot.json` (138 bytes, sha256 `6c59ed77abce…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/02640753-5cde-48b4-8638-f91a5e549493.actions.json` (1437 bytes, sha256 `42fe8968511a…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0032`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/87cf9a3c-e12a-4616-bf29-ad881e40cb83.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/87cf9a3c-e12a-4616-bf29-ad881e40cb83.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/87cf9a3c-e12a-4616-bf29-ad881e40cb83.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/87cf9a3c-e12a-4616-bf29-ad881e40cb83.replay.json` (485 bytes, sha256 `df74e8891675…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/87cf9a3c-e12a-4616-bf29-ad881e40cb83.snapshot.json` (138 bytes, sha256 `2be14632bc6e…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/87cf9a3c-e12a-4616-bf29-ad881e40cb83.actions.json` (1440 bytes, sha256 `536cee906657…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0035`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/e1359c74-9a28-4740-8cd2-5056365f660b.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/e1359c74-9a28-4740-8cd2-5056365f660b.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/e1359c74-9a28-4740-8cd2-5056365f660b.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/e1359c74-9a28-4740-8cd2-5056365f660b.replay.json` (485 bytes, sha256 `1958d69ab69e…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/e1359c74-9a28-4740-8cd2-5056365f660b.snapshot.json` (138 bytes, sha256 `f85018162a73…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/e1359c74-9a28-4740-8cd2-5056365f660b.actions.json` (1440 bytes, sha256 `e0e475ff707a…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0036`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("  Padded Name  ")
  - attempting fill action
 …`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/63d8e0a0-f3bb-4058-a4b3-22714a81691c.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/63d8e0a0-f3bb-4058-a4b3-22714a81691c.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/63d8e0a0-f3bb-4058-a4b3-22714a81691c.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/63d8e0a0-f3bb-4058-a4b3-22714a81691c.replay.json` (485 bytes, sha256 `8556eed435cc…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/63d8e0a0-f3bb-4058-a4b3-22714a81691c.snapshot.json` (138 bytes, sha256 `9a9ea5d7dd83…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/63d8e0a0-f3bb-4058-a4b3-22714a81691c.actions.json` (1440 bytes, sha256 `320ec42b55c8…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0037`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("  Padded Name  ")
  - attempting fill action
 …`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/d5bbed64-8ed3-4bb5-a525-eadaf79a49db.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/d5bbed64-8ed3-4bb5-a525-eadaf79a49db.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/d5bbed64-8ed3-4bb5-a525-eadaf79a49db.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/d5bbed64-8ed3-4bb5-a525-eadaf79a49db.replay.json` (485 bytes, sha256 `9637513d0363…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/d5bbed64-8ed3-4bb5-a525-eadaf79a49db.snapshot.json` (138 bytes, sha256 `ed319520dac9…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/d5bbed64-8ed3-4bb5-a525-eadaf79a49db.actions.json` (1440 bytes, sha256 `267517bac095…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0041`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-UNICODE / baseline-a · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Проект — Ünïcode ✓")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/f9b2d09d-281e-4785-9606-3ac3898a8ecd.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/f9b2d09d-281e-4785-9606-3ac3898a8ecd.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/f9b2d09d-281e-4785-9606-3ac3898a8ecd.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/f9b2d09d-281e-4785-9606-3ac3898a8ecd.replay.json` (485 bytes, sha256 `f04715129de1…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/f9b2d09d-281e-4785-9606-3ac3898a8ecd.snapshot.json` (138 bytes, sha256 `a5a9ed7cb391…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/f9b2d09d-281e-4785-9606-3ac3898a8ecd.actions.json` (1440 bytes, sha256 `7e6db1065fc4…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0042`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-UNICODE / baseline-a · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Проект — Ünïcode ✓")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/2d2e1e1d-439b-4649-b767-46326467075d.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/2d2e1e1d-439b-4649-b767-46326467075d.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/2d2e1e1d-439b-4649-b767-46326467075d.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/2d2e1e1d-439b-4649-b767-46326467075d.replay.json` (485 bytes, sha256 `c71feec29b2b…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/2d2e1e1d-439b-4649-b767-46326467075d.snapshot.json` (138 bytes, sha256 `6ac24aeeaac3…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/2d2e1e1d-439b-4649-b767-46326467075d.actions.json` (1440 bytes, sha256 `ce9e5300fd75…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0046`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/89ea7ef1-280c-4399-bf9d-8ea272848b40.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/89ea7ef1-280c-4399-bf9d-8ea272848b40.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/89ea7ef1-280c-4399-bf9d-8ea272848b40.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/89ea7ef1-280c-4399-bf9d-8ea272848b40.replay.json` (485 bytes, sha256 `d9a6e891a9a2…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/89ea7ef1-280c-4399-bf9d-8ea272848b40.snapshot.json` (138 bytes, sha256 `5212da755330…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/89ea7ef1-280c-4399-bf9d-8ea272848b40.actions.json` (1440 bytes, sha256 `019a3fbc9d95…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0050`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/320ee232-abea-49ad-8ba1-4871d7eb4a50.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/320ee232-abea-49ad-8ba1-4871d7eb4a50.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/320ee232-abea-49ad-8ba1-4871d7eb4a50.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/320ee232-abea-49ad-8ba1-4871d7eb4a50.replay.json` (485 bytes, sha256 `060d1456efa8…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/320ee232-abea-49ad-8ba1-4871d7eb4a50.snapshot.json` (138 bytes, sha256 `85b26d92fee5…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/320ee232-abea-49ad-8ba1-4871d7eb4a50.actions.json` (1440 bytes, sha256 `dcdee2ccacac…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0051`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("  Padded Name  ")
  - attempting fill action
 …`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/78452480-471c-43cf-8d50-98fc54384cc8.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/78452480-471c-43cf-8d50-98fc54384cc8.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/78452480-471c-43cf-8d50-98fc54384cc8.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/78452480-471c-43cf-8d50-98fc54384cc8.replay.json` (485 bytes, sha256 `f78f8180b570…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/78452480-471c-43cf-8d50-98fc54384cc8.snapshot.json` (138 bytes, sha256 `c7312fc92f17…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/78452480-471c-43cf-8d50-98fc54384cc8.actions.json` (1440 bytes, sha256 `adad1dcd438d…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0052`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
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
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0059`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-UNICODE / baseline-a · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Проект — Ünïcode ✓")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/30610e12-7096-41ef-bdde-f08c0a951bac.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/30610e12-7096-41ef-bdde-f08c0a951bac.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/30610e12-7096-41ef-bdde-f08c0a951bac.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/30610e12-7096-41ef-bdde-f08c0a951bac.replay.json` (485 bytes, sha256 `bc8411e6b83c…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/30610e12-7096-41ef-bdde-f08c0a951bac.snapshot.json` (138 bytes, sha256 `fc553d7f8d2a…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/30610e12-7096-41ef-bdde-f08c0a951bac.actions.json` (1440 bytes, sha256 `16634b32ca21…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0060`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-UNICODE / baseline-a · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Проект — Ünïcode ✓")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/f4fea0ca-24fe-4b16-b4a9-8aade6eafb1d.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/f4fea0ca-24fe-4b16-b4a9-8aade6eafb1d.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/f4fea0ca-24fe-4b16-b4a9-8aade6eafb1d.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/f4fea0ca-24fe-4b16-b4a9-8aade6eafb1d.replay.json` (485 bytes, sha256 `24255c02f87d…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/f4fea0ca-24fe-4b16-b4a9-8aade6eafb1d.snapshot.json` (138 bytes, sha256 `c20c13efd0aa…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/f4fea0ca-24fe-4b16-b4a9-8aade6eafb1d.actions.json` (1440 bytes, sha256 `3205af52a5c1…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0061`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/2ea32651-d02d-47a9-8aca-ebb2f522507c.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/2ea32651-d02d-47a9-8aca-ebb2f522507c.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/2ea32651-d02d-47a9-8aca-ebb2f522507c.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/2ea32651-d02d-47a9-8aca-ebb2f522507c.replay.json` (485 bytes, sha256 `d19143bd237f…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/2ea32651-d02d-47a9-8aca-ebb2f522507c.snapshot.json` (138 bytes, sha256 `12a0e3fb670d…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/2ea32651-d02d-47a9-8aca-ebb2f522507c.actions.json` (1440 bytes, sha256 `45edd970923f…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0063`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/d7506be2-9629-474f-b574-8f2d2fd7bd76.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/d7506be2-9629-474f-b574-8f2d2fd7bd76.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/d7506be2-9629-474f-b574-8f2d2fd7bd76.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/d7506be2-9629-474f-b574-8f2d2fd7bd76.replay.json` (485 bytes, sha256 `8f8ff47784a9…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/d7506be2-9629-474f-b574-8f2d2fd7bd76.snapshot.json` (138 bytes, sha256 `52a9f716e8bc…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/d7506be2-9629-474f-b574-8f2d2fd7bd76.actions.json` (1440 bytes, sha256 `6d93d71cee00…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0069`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("  Padded Name  ")
  - attempting fill action
 …`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/023b46fa-b692-4c3f-bbed-adb9cdbb35c6.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/023b46fa-b692-4c3f-bbed-adb9cdbb35c6.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/023b46fa-b692-4c3f-bbed-adb9cdbb35c6.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/023b46fa-b692-4c3f-bbed-adb9cdbb35c6.replay.json` (485 bytes, sha256 `f70814e077c1…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/023b46fa-b692-4c3f-bbed-adb9cdbb35c6.snapshot.json` (138 bytes, sha256 `12e64c9f1465…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/023b46fa-b692-4c3f-bbed-adb9cdbb35c6.actions.json` (1440 bytes, sha256 `7b62f3ec371e…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0070`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("  Padded Name  ")
  - attempting fill action
 …`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/a614409e-842b-4323-98f7-e222a5379ad7.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/a614409e-842b-4323-98f7-e222a5379ad7.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/a614409e-842b-4323-98f7-e222a5379ad7.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/a614409e-842b-4323-98f7-e222a5379ad7.replay.json` (485 bytes, sha256 `8eb7bdd2e720…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/a614409e-842b-4323-98f7-e222a5379ad7.snapshot.json` (138 bytes, sha256 `c5f2a6f2af61…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/a614409e-842b-4323-98f7-e222a5379ad7.actions.json` (1440 bytes, sha256 `897893c07d6e…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0071`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-UNICODE / baseline-a · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Проект — Ünïcode ✓")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/4db72e66-4f91-49ae-84db-56a6e291b1d3.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/4db72e66-4f91-49ae-84db-56a6e291b1d3.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/4db72e66-4f91-49ae-84db-56a6e291b1d3.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/4db72e66-4f91-49ae-84db-56a6e291b1d3.replay.json` (485 bytes, sha256 `1e35e57c5651…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/4db72e66-4f91-49ae-84db-56a6e291b1d3.snapshot.json` (138 bytes, sha256 `da8afad19b5b…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/4db72e66-4f91-49ae-84db-56a6e291b1d3.actions.json` (1440 bytes, sha256 `b07ec493e04b…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0073`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-UNICODE / baseline-a · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Проект — Ünïcode ✓")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/5a4ab056-d930-4a32-97c9-013f9c400710.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/5a4ab056-d930-4a32-97c9-013f9c400710.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/5a4ab056-d930-4a32-97c9-013f9c400710.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/5a4ab056-d930-4a32-97c9-013f9c400710.replay.json` (485 bytes, sha256 `a3297779035f…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/5a4ab056-d930-4a32-97c9-013f9c400710.snapshot.json` (138 bytes, sha256 `2270b2e51545…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/5a4ab056-d930-4a32-97c9-013f9c400710.actions.json` (1440 bytes, sha256 `4d91d0a075ff…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0076`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/19fedd5a-4e11-4147-a0cb-843720870695.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/19fedd5a-4e11-4147-a0cb-843720870695.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/19fedd5a-4e11-4147-a0cb-843720870695.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/19fedd5a-4e11-4147-a0cb-843720870695.replay.json` (485 bytes, sha256 `955bdb7e2919…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/19fedd5a-4e11-4147-a0cb-843720870695.snapshot.json` (138 bytes, sha256 `89b9f90a8455…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/19fedd5a-4e11-4147-a0cb-843720870695.actions.json` (1440 bytes, sha256 `0e8420985712…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0078`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/692276e2-ea1e-4d22-90bc-6aca4077bfd6.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/692276e2-ea1e-4d22-90bc-6aca4077bfd6.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/692276e2-ea1e-4d22-90bc-6aca4077bfd6.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/692276e2-ea1e-4d22-90bc-6aca4077bfd6.replay.json` (485 bytes, sha256 `a2d2443d82cd…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/692276e2-ea1e-4d22-90bc-6aca4077bfd6.snapshot.json` (138 bytes, sha256 `75701dc3a229…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/692276e2-ea1e-4d22-90bc-6aca4077bfd6.actions.json` (1440 bytes, sha256 `b22c52b3a02d…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0084`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("  Padded Name  ")
  - attempting fill action
 …`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/a1eec0a0-89c0-4ad6-b62d-4723f9556d9b.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/a1eec0a0-89c0-4ad6-b62d-4723f9556d9b.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/a1eec0a0-89c0-4ad6-b62d-4723f9556d9b.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/a1eec0a0-89c0-4ad6-b62d-4723f9556d9b.replay.json` (485 bytes, sha256 `10034a9d3107…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/a1eec0a0-89c0-4ad6-b62d-4723f9556d9b.snapshot.json` (138 bytes, sha256 `372ba219ea44…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/a1eec0a0-89c0-4ad6-b62d-4723f9556d9b.actions.json` (1440 bytes, sha256 `86a2fd1d1a9b…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0085`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("  Padded Name  ")
  - attempting fill action
 …`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/428de1e6-719f-46e0-8ffc-bde8bf5bffc8.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/428de1e6-719f-46e0-8ffc-bde8bf5bffc8.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/428de1e6-719f-46e0-8ffc-bde8bf5bffc8.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/428de1e6-719f-46e0-8ffc-bde8bf5bffc8.replay.json` (485 bytes, sha256 `517b9302dcdf…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/428de1e6-719f-46e0-8ffc-bde8bf5bffc8.snapshot.json` (138 bytes, sha256 `0d1ac58afeb2…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/428de1e6-719f-46e0-8ffc-bde8bf5bffc8.actions.json` (1440 bytes, sha256 `aa906c75104e…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0086`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-UNICODE / baseline-a · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Проект — Ünïcode ✓")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/6992dc18-3c77-456f-815c-52f171948b9f.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/6992dc18-3c77-456f-815c-52f171948b9f.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/6992dc18-3c77-456f-815c-52f171948b9f.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/6992dc18-3c77-456f-815c-52f171948b9f.replay.json` (485 bytes, sha256 `9500d38711f5…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/6992dc18-3c77-456f-815c-52f171948b9f.snapshot.json` (138 bytes, sha256 `06b8595d9629…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/6992dc18-3c77-456f-815c-52f171948b9f.actions.json` (1440 bytes, sha256 `04feef9d54a2…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0090`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOW / I-UNICODE / baseline-a · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Проект — Ünïcode ✓")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/f549119c-e6cd-491e-9e60-aa03524652ab.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/f549119c-e6cd-491e-9e60-aa03524652ab.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/f549119c-e6cd-491e-9e60-aa03524652ab.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/f549119c-e6cd-491e-9e60-aa03524652ab.replay.json` (485 bytes, sha256 `a648f599d9f5…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/f549119c-e6cd-491e-9e60-aa03524652ab.snapshot.json` (138 bytes, sha256 `0b6801bfe944…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/f549119c-e6cd-491e-9e60-aa03524652ab.actions.json` (1440 bytes, sha256 `20bf756e5056…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0093`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-DIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/96ccc285-e02a-45c9-8c88-71eaaa1132c3.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/96ccc285-e02a-45c9-8c88-71eaaa1132c3.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/96ccc285-e02a-45c9-8c88-71eaaa1132c3.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/96ccc285-e02a-45c9-8c88-71eaaa1132c3.replay.json` (486 bytes, sha256 `abc9c4186208…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/96ccc285-e02a-45c9-8c88-71eaaa1132c3.snapshot.json` (138 bytes, sha256 `7420ac6bc9b4…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/96ccc285-e02a-45c9-8c88-71eaaa1132c3.actions.json` (1443 bytes, sha256 `922b9b9ea042…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0094`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-DIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/b4bef28a-6c5e-4f22-9d7d-fad5a88afc15.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/b4bef28a-6c5e-4f22-9d7d-fad5a88afc15.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/b4bef28a-6c5e-4f22-9d7d-fad5a88afc15.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/b4bef28a-6c5e-4f22-9d7d-fad5a88afc15.replay.json` (486 bytes, sha256 `84fae4b8cbc6…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/b4bef28a-6c5e-4f22-9d7d-fad5a88afc15.snapshot.json` (138 bytes, sha256 `3b6162e85133…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/b4bef28a-6c5e-4f22-9d7d-fad5a88afc15.actions.json` (1443 bytes, sha256 `99a9daba0a84…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0098`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
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
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0100`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-DIS / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("  Padded Name  ")
  - attempting fill action
 …`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/6d0b1c63-6e01-4e1f-8917-b81491b34219.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/6d0b1c63-6e01-4e1f-8917-b81491b34219.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/6d0b1c63-6e01-4e1f-8917-b81491b34219.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/6d0b1c63-6e01-4e1f-8917-b81491b34219.replay.json` (486 bytes, sha256 `79c8e3d73cc6…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/6d0b1c63-6e01-4e1f-8917-b81491b34219.snapshot.json` (138 bytes, sha256 `d6a61f6fd517…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/6d0b1c63-6e01-4e1f-8917-b81491b34219.actions.json` (1443 bytes, sha256 `8d3f03a772b8…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0102`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-DIS / I-UNICODE / baseline-a · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Проект — Ünïcode ✓")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/b03fd3df-4e47-433e-be1a-a4c12b094af5.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/b03fd3df-4e47-433e-be1a-a4c12b094af5.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/b03fd3df-4e47-433e-be1a-a4c12b094af5.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/b03fd3df-4e47-433e-be1a-a4c12b094af5.replay.json` (486 bytes, sha256 `d9e18c15a3a6…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/b03fd3df-4e47-433e-be1a-a4c12b094af5.snapshot.json` (138 bytes, sha256 `02257e4798bc…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/b03fd3df-4e47-433e-be1a-a4c12b094af5.actions.json` (1443 bytes, sha256 `fac35be4b590…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0104`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-DIS / I-UNICODE / baseline-a · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Проект — Ünïcode ✓")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/123cf125-64c5-4d5a-8457-968a2457eb84.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/123cf125-64c5-4d5a-8457-968a2457eb84.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/123cf125-64c5-4d5a-8457-968a2457eb84.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/123cf125-64c5-4d5a-8457-968a2457eb84.replay.json` (486 bytes, sha256 `7e8bd5604199…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/123cf125-64c5-4d5a-8457-968a2457eb84.snapshot.json` (138 bytes, sha256 `286979a4ad0d…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/123cf125-64c5-4d5a-8457-968a2457eb84.actions.json` (1443 bytes, sha256 `6cb33d6b74f9…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0107`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/2c7d0f54-be21-4bba-8d02-2797d207fb04.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/2c7d0f54-be21-4bba-8d02-2797d207fb04.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/2c7d0f54-be21-4bba-8d02-2797d207fb04.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/2c7d0f54-be21-4bba-8d02-2797d207fb04.replay.json` (495 bytes, sha256 `d69cb6cb02e8…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/2c7d0f54-be21-4bba-8d02-2797d207fb04.snapshot.json` (138 bytes, sha256 `96bed0a76944…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/2c7d0f54-be21-4bba-8d02-2797d207fb04.actions.json` (1470 bytes, sha256 `70d98233dc3d…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0108`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/7f27e4b0-d50f-4704-9936-7d6c95ab34fa.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/7f27e4b0-d50f-4704-9936-7d6c95ab34fa.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/7f27e4b0-d50f-4704-9936-7d6c95ab34fa.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/7f27e4b0-d50f-4704-9936-7d6c95ab34fa.replay.json` (495 bytes, sha256 `022477411991…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/7f27e4b0-d50f-4704-9936-7d6c95ab34fa.snapshot.json` (138 bytes, sha256 `aa71bd5cbfc6…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/7f27e4b0-d50f-4704-9936-7d6c95ab34fa.actions.json` (1470 bytes, sha256 `49dac576680d…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0111`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("  Padded Name  ")
  - attempting fill action
 …`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/b1c01a70-cc80-4e3a-8028-77a180c09ea6.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/b1c01a70-cc80-4e3a-8028-77a180c09ea6.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/b1c01a70-cc80-4e3a-8028-77a180c09ea6.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/b1c01a70-cc80-4e3a-8028-77a180c09ea6.replay.json` (495 bytes, sha256 `a1b610b906e9…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/b1c01a70-cc80-4e3a-8028-77a180c09ea6.snapshot.json` (138 bytes, sha256 `e1029103a608…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/b1c01a70-cc80-4e3a-8028-77a180c09ea6.actions.json` (1470 bytes, sha256 `8a30e869fd8c…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0115`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("  Padded Name  ")
  - attempting fill action
 …`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/1b39fe14-0e89-4e4d-808a-628723a6f4f3.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/1b39fe14-0e89-4e4d-808a-628723a6f4f3.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/1b39fe14-0e89-4e4d-808a-628723a6f4f3.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/1b39fe14-0e89-4e4d-808a-628723a6f4f3.replay.json` (495 bytes, sha256 `0e3156d98cdd…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/1b39fe14-0e89-4e4d-808a-628723a6f4f3.snapshot.json` (138 bytes, sha256 `63a1da10ac9c…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/1b39fe14-0e89-4e4d-808a-628723a6f4f3.actions.json` (1470 bytes, sha256 `b7f68f45fb42…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0116`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-UNICODE / baseline-a · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Проект — Ünïcode ✓")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/c1200b02-a6a8-487e-a0a4-b8c7bcb4e198.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/c1200b02-a6a8-487e-a0a4-b8c7bcb4e198.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/c1200b02-a6a8-487e-a0a4-b8c7bcb4e198.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/c1200b02-a6a8-487e-a0a4-b8c7bcb4e198.replay.json` (495 bytes, sha256 `10114750618a…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/c1200b02-a6a8-487e-a0a4-b8c7bcb4e198.snapshot.json` (138 bytes, sha256 `f68dafaa9f1e…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/c1200b02-a6a8-487e-a0a4-b8c7bcb4e198.actions.json` (1470 bytes, sha256 `1e35dca60928…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0119`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-UNICODE / baseline-a · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Проект — Ünïcode ✓")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/1ad38226-4ef6-4d31-bcc4-3dff443a68e9.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/1ad38226-4ef6-4d31-bcc4-3dff443a68e9.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/1ad38226-4ef6-4d31-bcc4-3dff443a68e9.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/1ad38226-4ef6-4d31-bcc4-3dff443a68e9.replay.json` (495 bytes, sha256 `a9bc97d23b88…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/1ad38226-4ef6-4d31-bcc4-3dff443a68e9.snapshot.json` (138 bytes, sha256 `69c6d9c822f2…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/1ad38226-4ef6-4d31-bcc4-3dff443a68e9.actions.json` (1470 bytes, sha256 `18b46088f680…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0122`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/b251d0eb-8ad9-47d2-bf09-963796ad6247.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/b251d0eb-8ad9-47d2-bf09-963796ad6247.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/b251d0eb-8ad9-47d2-bf09-963796ad6247.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/b251d0eb-8ad9-47d2-bf09-963796ad6247.replay.json` (496 bytes, sha256 `1b629bb26357…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/b251d0eb-8ad9-47d2-bf09-963796ad6247.snapshot.json` (138 bytes, sha256 `67840c49b9b1…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/b251d0eb-8ad9-47d2-bf09-963796ad6247.actions.json` (1473 bytes, sha256 `acdbd06158b5…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0125`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/aef93e11-3e00-4982-9748-31ca20a7d777.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/aef93e11-3e00-4982-9748-31ca20a7d777.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/aef93e11-3e00-4982-9748-31ca20a7d777.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/aef93e11-3e00-4982-9748-31ca20a7d777.replay.json` (496 bytes, sha256 `4d6e108edffe…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/aef93e11-3e00-4982-9748-31ca20a7d777.snapshot.json` (138 bytes, sha256 `4fd45e9f7c00…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/aef93e11-3e00-4982-9748-31ca20a7d777.actions.json` (1473 bytes, sha256 `cb4ce25f9420…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0126`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("  Padded Name  ")
  - attempting fill action
 …`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/3a80969d-70c2-4d68-a68e-80e5743be255.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/3a80969d-70c2-4d68-a68e-80e5743be255.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/3a80969d-70c2-4d68-a68e-80e5743be255.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/3a80969d-70c2-4d68-a68e-80e5743be255.replay.json` (496 bytes, sha256 `effcff88c1cd…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/3a80969d-70c2-4d68-a68e-80e5743be255.snapshot.json` (138 bytes, sha256 `c88fa311e186…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/3a80969d-70c2-4d68-a68e-80e5743be255.actions.json` (1473 bytes, sha256 `5c59830293c5…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0127`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("  Padded Name  ")
  - attempting fill action
 …`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/814bc21e-5f6f-4717-bda1-95ae119e3cd4.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/814bc21e-5f6f-4717-bda1-95ae119e3cd4.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/814bc21e-5f6f-4717-bda1-95ae119e3cd4.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/814bc21e-5f6f-4717-bda1-95ae119e3cd4.replay.json` (496 bytes, sha256 `32e93078b71a…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/814bc21e-5f6f-4717-bda1-95ae119e3cd4.snapshot.json` (138 bytes, sha256 `df58c157a080…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/814bc21e-5f6f-4717-bda1-95ae119e3cd4.actions.json` (1473 bytes, sha256 `0b2990b5954e…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0131`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-UNICODE / baseline-a · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Проект — Ünïcode ✓")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/b44d01e3-d266-4ebe-8d33-e55731de36f5.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/b44d01e3-d266-4ebe-8d33-e55731de36f5.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/b44d01e3-d266-4ebe-8d33-e55731de36f5.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/b44d01e3-d266-4ebe-8d33-e55731de36f5.replay.json` (496 bytes, sha256 `8f41a35b965f…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/b44d01e3-d266-4ebe-8d33-e55731de36f5.snapshot.json` (138 bytes, sha256 `3bd74280e52b…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/b44d01e3-d266-4ebe-8d33-e55731de36f5.actions.json` (1473 bytes, sha256 `2c177dacd0a6…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0133`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-UNICODE / baseline-a · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Проект — Ünïcode ✓")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/b6c488d1-0fe9-4cee-a439-4624a2e2e4b9.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/b6c488d1-0fe9-4cee-a439-4624a2e2e4b9.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/b6c488d1-0fe9-4cee-a439-4624a2e2e4b9.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/b6c488d1-0fe9-4cee-a439-4624a2e2e4b9.replay.json` (496 bytes, sha256 `2012b6fe893f…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/b6c488d1-0fe9-4cee-a439-4624a2e2e4b9.snapshot.json` (138 bytes, sha256 `7418046601ed…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/b6c488d1-0fe9-4cee-a439-4624a2e2e4b9.actions.json` (1473 bytes, sha256 `9f2acc256d24…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0137`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/6a5f5f30-0d86-432f-a8ac-7d25ff2d2a1b.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/6a5f5f30-0d86-432f-a8ac-7d25ff2d2a1b.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/6a5f5f30-0d86-432f-a8ac-7d25ff2d2a1b.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/6a5f5f30-0d86-432f-a8ac-7d25ff2d2a1b.replay.json` (496 bytes, sha256 `f62f2e24371d…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/6a5f5f30-0d86-432f-a8ac-7d25ff2d2a1b.snapshot.json` (138 bytes, sha256 `f94b60cad7e0…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/6a5f5f30-0d86-432f-a8ac-7d25ff2d2a1b.actions.json` (1473 bytes, sha256 `7b85fc214e86…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0140`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/1105aad3-2db8-4050-a326-dc3d991b9578.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/1105aad3-2db8-4050-a326-dc3d991b9578.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/1105aad3-2db8-4050-a326-dc3d991b9578.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/1105aad3-2db8-4050-a326-dc3d991b9578.replay.json` (496 bytes, sha256 `71780e33b48f…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/1105aad3-2db8-4050-a326-dc3d991b9578.snapshot.json` (138 bytes, sha256 `c7a134f927ba…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/1105aad3-2db8-4050-a326-dc3d991b9578.actions.json` (1473 bytes, sha256 `54ee6c42ef5b…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0143`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
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
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0145`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("  Padded Name  ")
  - attempting fill action
 …`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/0fd0047f-9e7e-4097-8ee2-659de4675be4.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/0fd0047f-9e7e-4097-8ee2-659de4675be4.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/0fd0047f-9e7e-4097-8ee2-659de4675be4.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/0fd0047f-9e7e-4097-8ee2-659de4675be4.replay.json` (496 bytes, sha256 `4ce3c58559c7…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/0fd0047f-9e7e-4097-8ee2-659de4675be4.snapshot.json` (138 bytes, sha256 `96ec55e3c7ce…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/0fd0047f-9e7e-4097-8ee2-659de4675be4.actions.json` (1473 bytes, sha256 `e3b1542b9220…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0147`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-UNICODE / baseline-a · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Проект — Ünïcode ✓")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/e62b13c4-bd7d-4549-b403-5316857f39dc.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/e62b13c4-bd7d-4549-b403-5316857f39dc.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/e62b13c4-bd7d-4549-b403-5316857f39dc.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/e62b13c4-bd7d-4549-b403-5316857f39dc.replay.json` (496 bytes, sha256 `062932802470…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/e62b13c4-bd7d-4549-b403-5316857f39dc.snapshot.json` (138 bytes, sha256 `fdc848c9809c…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/e62b13c4-bd7d-4549-b403-5316857f39dc.actions.json` (1473 bytes, sha256 `1c50fe2d52a9…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0148`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-UNICODE / baseline-a · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Проект — Ünïcode ✓")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/87e97efe-bded-4745-b42d-c66392733c9d.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/87e97efe-bded-4745-b42d-c66392733c9d.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/87e97efe-bded-4745-b42d-c66392733c9d.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/87e97efe-bded-4745-b42d-c66392733c9d.replay.json` (496 bytes, sha256 `708b38ffd088…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/87e97efe-bded-4745-b42d-c66392733c9d.snapshot.json` (138 bytes, sha256 `4ce0278d739a…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/87e97efe-bded-4745-b42d-c66392733c9d.actions.json` (1473 bytes, sha256 `7f10eba9d48a…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0154`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/76f6e2b0-0cc2-4958-9531-b8cc3fb70136.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/76f6e2b0-0cc2-4958-9531-b8cc3fb70136.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/76f6e2b0-0cc2-4958-9531-b8cc3fb70136.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/76f6e2b0-0cc2-4958-9531-b8cc3fb70136.replay.json` (496 bytes, sha256 `03c92b569661…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/76f6e2b0-0cc2-4958-9531-b8cc3fb70136.snapshot.json` (138 bytes, sha256 `4779df100bad…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/76f6e2b0-0cc2-4958-9531-b8cc3fb70136.actions.json` (1473 bytes, sha256 `109dd01c71b4…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0155`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/342398a5-8e76-4084-afb6-8b63d43adc54.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/342398a5-8e76-4084-afb6-8b63d43adc54.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/342398a5-8e76-4084-afb6-8b63d43adc54.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/342398a5-8e76-4084-afb6-8b63d43adc54.replay.json` (496 bytes, sha256 `b9a1ce47b3d0…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/342398a5-8e76-4084-afb6-8b63d43adc54.snapshot.json` (138 bytes, sha256 `d346f95577a8…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/342398a5-8e76-4084-afb6-8b63d43adc54.actions.json` (1473 bytes, sha256 `d5dde577c080…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0156`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("  Padded Name  ")
  - attempting fill action
 …`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/ae164c21-17ad-434e-b304-6a568aad574f.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/ae164c21-17ad-434e-b304-6a568aad574f.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/ae164c21-17ad-434e-b304-6a568aad574f.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/ae164c21-17ad-434e-b304-6a568aad574f.replay.json` (496 bytes, sha256 `d944f9b7d1e6…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/ae164c21-17ad-434e-b304-6a568aad574f.snapshot.json` (138 bytes, sha256 `0fbe2a5a3c38…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/ae164c21-17ad-434e-b304-6a568aad574f.actions.json` (1473 bytes, sha256 `f4d4e2e68242…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0159`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("  Padded Name  ")
  - attempting fill action
 …`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/1fa62c6b-f196-4cc9-b963-712baf2dce9e.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/1fa62c6b-f196-4cc9-b963-712baf2dce9e.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/1fa62c6b-f196-4cc9-b963-712baf2dce9e.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/1fa62c6b-f196-4cc9-b963-712baf2dce9e.replay.json` (496 bytes, sha256 `b116c7d610b3…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/1fa62c6b-f196-4cc9-b963-712baf2dce9e.snapshot.json` (138 bytes, sha256 `9d5e26004be6…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/1fa62c6b-f196-4cc9-b963-712baf2dce9e.actions.json` (1473 bytes, sha256 `f70bb4e868b2…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0164`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-UNICODE / baseline-a · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Проект — Ünïcode ✓")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/95abfcac-4280-40a8-96e1-ce67ea25ebd7.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/95abfcac-4280-40a8-96e1-ce67ea25ebd7.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/95abfcac-4280-40a8-96e1-ce67ea25ebd7.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/95abfcac-4280-40a8-96e1-ce67ea25ebd7.replay.json` (496 bytes, sha256 `d16aab9e1fe4…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/95abfcac-4280-40a8-96e1-ce67ea25ebd7.snapshot.json` (138 bytes, sha256 `9e1ac31df046…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/95abfcac-4280-40a8-96e1-ce67ea25ebd7.actions.json` (1473 bytes, sha256 `3e71e6c6fa6f…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0165`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-UNICODE / baseline-a · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Проект — Ünïcode ✓")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/ff0c774b-dff6-4af4-8af1-563dc40beb8e.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/ff0c774b-dff6-4af4-8af1-563dc40beb8e.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/ff0c774b-dff6-4af4-8af1-563dc40beb8e.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/ff0c774b-dff6-4af4-8af1-563dc40beb8e.replay.json` (496 bytes, sha256 `3a57d5d11e02…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/ff0c774b-dff6-4af4-8af1-563dc40beb8e.snapshot.json` (138 bytes, sha256 `bad9fd85bfe8…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/ff0c774b-dff6-4af4-8af1-563dc40beb8e.actions.json` (1473 bytes, sha256 `837c91601d79…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0167`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/abf6f0ba-e199-47bf-a5ba-aedf9bf7ea54.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/abf6f0ba-e199-47bf-a5ba-aedf9bf7ea54.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/abf6f0ba-e199-47bf-a5ba-aedf9bf7ea54.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/abf6f0ba-e199-47bf-a5ba-aedf9bf7ea54.replay.json` (496 bytes, sha256 `550a2e4e73e8…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/abf6f0ba-e199-47bf-a5ba-aedf9bf7ea54.snapshot.json` (138 bytes, sha256 `3b01fa4251ab…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/abf6f0ba-e199-47bf-a5ba-aedf9bf7ea54.actions.json` (1473 bytes, sha256 `1fbd5fe8da25…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0169`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/b14d1f53-7db5-4a87-a2e8-8d8da2a1e46a.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/b14d1f53-7db5-4a87-a2e8-8d8da2a1e46a.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/b14d1f53-7db5-4a87-a2e8-8d8da2a1e46a.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/b14d1f53-7db5-4a87-a2e8-8d8da2a1e46a.replay.json` (496 bytes, sha256 `03bd55a2c28c…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/b14d1f53-7db5-4a87-a2e8-8d8da2a1e46a.snapshot.json` (138 bytes, sha256 `8d163509da23…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/b14d1f53-7db5-4a87-a2e8-8d8da2a1e46a.actions.json` (1473 bytes, sha256 `d21f8099838c…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0171`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("  Padded Name  ")
  - attempting fill action
 …`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/54068f0e-d350-4d16-86a2-226685cb9562.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/54068f0e-d350-4d16-86a2-226685cb9562.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/54068f0e-d350-4d16-86a2-226685cb9562.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/54068f0e-d350-4d16-86a2-226685cb9562.replay.json` (496 bytes, sha256 `a92db9ef0ef6…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/54068f0e-d350-4d16-86a2-226685cb9562.snapshot.json` (138 bytes, sha256 `78c49acbeabd…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/54068f0e-d350-4d16-86a2-226685cb9562.actions.json` (1473 bytes, sha256 `4019e7cb68a9…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0173`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-SPACE / baseline-a · expected stored name: 'Padded Name'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("  Padded Name  ")
  - attempting fill action
 …`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/858cfbd8-83d9-4819-a596-7a66711a3d51.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Padded Name' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/858cfbd8-83d9-4819-a596-7a66711a3d51.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/858cfbd8-83d9-4819-a596-7a66711a3d51.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/858cfbd8-83d9-4819-a596-7a66711a3d51.replay.json` (496 bytes, sha256 `33a85279f89c…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/858cfbd8-83d9-4819-a596-7a66711a3d51.snapshot.json` (138 bytes, sha256 `a9b46d80c203…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/858cfbd8-83d9-4819-a596-7a66711a3d51.actions.json` (1473 bytes, sha256 `d3fd5d21eaac…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0176`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-UNICODE / baseline-a · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Проект — Ünïcode ✓")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/f7ba3405-f614-4dfe-b181-8056f62e395c.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/f7ba3405-f614-4dfe-b181-8056f62e395c.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/f7ba3405-f614-4dfe-b181-8056f62e395c.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/f7ba3405-f614-4dfe-b181-8056f62e395c.replay.json` (496 bytes, sha256 `e4ff101cdaff…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/f7ba3405-f614-4dfe-b181-8056f62e395c.snapshot.json` (138 bytes, sha256 `25c25d60695c…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/f7ba3405-f614-4dfe-b181-8056f62e395c.actions.json` (1473 bytes, sha256 `3d298a39a44e…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `eval-20261028-baseline-a::trial-0177`

- Population: primary evaluation (eval-20261028) · Driver F · manifest `benchmarks/manifests/eval-v1.json` (`eval-v1`)
- Condition: S-SLOWDIS / I-UNICODE / baseline-a · expected stored name: 'Проект — Ünïcode ✓'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Проект — Ünïcode ✓")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/5bf12381-c4e8-4378-9f5c-5af860aecb75.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Проект — Ünïcode ✓' (exact match)", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/5bf12381-c4e8-4378-9f5c-5af860aecb75.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "artifacts/eval-20261028/traces-baseline-a/5bf12381-c4e8-4378-9f5c-5af860aecb75.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `artifacts/eval-20261028/traces-baseline-a/5bf12381-c4e8-4378-9f5c-5af860aecb75.replay.json` (496 bytes, sha256 `873b8a67e5af…`, verified)
- snapshot: `artifacts/eval-20261028/traces-baseline-a/5bf12381-c4e8-4378-9f5c-5af860aecb75.snapshot.json` (138 bytes, sha256 `80accd8eb60f…`, verified)
- actions: `artifacts/eval-20261028/traces-baseline-a/5bf12381-c4e8-4378-9f5c-5af860aecb75.actions.json` (1473 bytes, sha256 `cb2460d278ab…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-chimera::trial-0003`

- Population: matched-budget follow-up (mb-v1) · Driver C · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-NORM / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/3e2ada23-8013-4951-be3e-d5636732ed30.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/3e2ada23-8013-4951-be3e-d5636732ed30.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/3e2ada23-8013-4951-be3e-d5636732ed30.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/3e2ada23-8013-4951-be3e-d5636732ed30.json` (2973 bytes, sha256 `50c970dd3c6d…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/3e2ada23-8013-4951-be3e-d5636732ed30.snapshot.json` (156 bytes, sha256 `614375c6cb56…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/3e2ada23-8013-4951-be3e-d5636732ed30.actions.json` (2284 bytes, sha256 `498567db1c2f…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `main-mb-v1-chimera::trial-0004`

- Population: matched-budget follow-up (mb-v1) · Driver C · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-NORM / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/1c3ef8b0-293f-4641-8773-8b60200fe238.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/1c3ef8b0-293f-4641-8773-8b60200fe238.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/1c3ef8b0-293f-4641-8773-8b60200fe238.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/1c3ef8b0-293f-4641-8773-8b60200fe238.json` (2973 bytes, sha256 `055145da57e9…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/1c3ef8b0-293f-4641-8773-8b60200fe238.snapshot.json` (156 bytes, sha256 `9fe9d31706e3…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/1c3ef8b0-293f-4641-8773-8b60200fe238.actions.json` (2284 bytes, sha256 `1d35b97f18d7…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `main-mb-v1-chimera::trial-0006`

- Population: matched-budget follow-up (mb-v1) · Driver C · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-SLOW / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/b4a100da-b966-4e9c-861a-66869a1b455f.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/b4a100da-b966-4e9c-861a-66869a1b455f.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/b4a100da-b966-4e9c-861a-66869a1b455f.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/b4a100da-b966-4e9c-861a-66869a1b455f.json` (2983 bytes, sha256 `a128ababe9ee…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/b4a100da-b966-4e9c-861a-66869a1b455f.snapshot.json` (156 bytes, sha256 `3269e4c7ddf6…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/b4a100da-b966-4e9c-861a-66869a1b455f.actions.json` (2320 bytes, sha256 `da2d8610f324…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `main-mb-v1-chimera::trial-0007`

- Population: matched-budget follow-up (mb-v1) · Driver C · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-SLOW / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/46b99f0f-05ea-4333-9c45-73deb999bf2d.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/46b99f0f-05ea-4333-9c45-73deb999bf2d.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/46b99f0f-05ea-4333-9c45-73deb999bf2d.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 10 steps · 7 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/46b99f0f-05ea-4333-9c45-73deb999bf2d.json` (2983 bytes, sha256 `6dfc5e9aca7d…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/46b99f0f-05ea-4333-9c45-73deb999bf2d.snapshot.json` (156 bytes, sha256 `ea006ab27cfe…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/46b99f0f-05ea-4333-9c45-73deb999bf2d.actions.json` (2320 bytes, sha256 `3eba0aed07e4…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)

### `main-mb-v1-chimera::trial-0013`

- Population: matched-budget follow-up (mb-v1) · Driver C · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-DIS / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/c8f1cac4-1dc6-4e51-af71-e80530ad536b.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/c8f1cac4-1dc6-4e51-af71-e80530ad536b.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/c8f1cac4-1dc6-4e51-af71-e80530ad536b.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/c8f1cac4-1dc6-4e51-af71-e80530ad536b.json` (3918 bytes, sha256 `e3972482a4e9…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/c8f1cac4-1dc6-4e51-af71-e80530ad536b.snapshot.json` (138 bytes, sha256 `ffb13601621e…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/c8f1cac4-1dc6-4e51-af71-e80530ad536b.actions.json` (1731 bytes, sha256 `66d7e891db65…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/c8f1cac4-1dc6-4e51-af71-e80530ad536b.png` (present)

### `main-mb-v1-chimera::trial-0015`

- Population: matched-budget follow-up (mb-v1) · Driver C · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-DIS / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/d21a2810-edcc-4866-b6a3-b8f456723f37.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/d21a2810-edcc-4866-b6a3-b8f456723f37.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/d21a2810-edcc-4866-b6a3-b8f456723f37.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/d21a2810-edcc-4866-b6a3-b8f456723f37.json` (3918 bytes, sha256 `544d610d850a…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/d21a2810-edcc-4866-b6a3-b8f456723f37.snapshot.json` (138 bytes, sha256 `831121acf717…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/d21a2810-edcc-4866-b6a3-b8f456723f37.actions.json` (1731 bytes, sha256 `1dc70e246664…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/d21a2810-edcc-4866-b6a3-b8f456723f37.png` (present)

### `main-mb-v1-chimera::trial-0019`

- Population: matched-budget follow-up (mb-v1) · Driver C · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-SLOWDIS / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/b974eb70-ba6c-4e4b-98d9-bcfd819a6ef6.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/b974eb70-ba6c-4e4b-98d9-bcfd819a6ef6.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/b974eb70-ba6c-4e4b-98d9-bcfd819a6ef6.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/b974eb70-ba6c-4e4b-98d9-bcfd819a6ef6.json` (3928 bytes, sha256 `c6a8b94fc34f…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/b974eb70-ba6c-4e4b-98d9-bcfd819a6ef6.snapshot.json` (138 bytes, sha256 `eb12729eb119…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/b974eb70-ba6c-4e4b-98d9-bcfd819a6ef6.actions.json` (1761 bytes, sha256 `1e9f228aa6bd…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/b974eb70-ba6c-4e4b-98d9-bcfd819a6ef6.png` (present)

### `main-mb-v1-chimera::trial-0020`

- Population: matched-budget follow-up (mb-v1) · Driver C · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-SLOWDIS / I-PLAIN / chimera · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `RetryBudgetExhaustedError: Action 'fill' failed after 2 attempt(s) (caused by TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-la…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/895cb5d9-f414-4246-b0f1-56102eee8a80.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/895cb5d9-f414-4246-b0f1-56102eee8a80.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/895cb5d9-f414-4246-b0f1-56102eee8a80.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `trace` · 6 steps · 5 observed actions · snapshot confirmation_visible=false items=[]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/895cb5d9-f414-4246-b0f1-56102eee8a80.json` (3928 bytes, sha256 `2445e44e0cd1…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/895cb5d9-f414-4246-b0f1-56102eee8a80.snapshot.json` (138 bytes, sha256 `a0ad571d3bfe…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-chimera/895cb5d9-f414-4246-b0f1-56102eee8a80.actions.json` (1761 bytes, sha256 `f0bb747e281c…`, verified)
- Screenshots: `/Users/kartikbhardwaj/project-chimera/data/screenshots/895cb5d9-f414-4246-b0f1-56102eee8a80.png` (present)

### `main-mb-v1-replay-100::trial-0002`

- Population: matched-budget follow-up (mb-v1) · Driver G · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-NORM / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/c363de47-c18f-438a-8296-84e63546602e.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/c363de47-c18f-438a-8296-84e63546602e.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/c363de47-c18f-438a-8296-84e63546602e.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 3 steps · 5 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/c363de47-c18f-438a-8296-84e63546602e.replay.json` (560 bytes, sha256 `5f773b8bef74…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/c363de47-c18f-438a-8296-84e63546602e.snapshot.json` (156 bytes, sha256 `5ab6c979fe75…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/c363de47-c18f-438a-8296-84e63546602e.actions.json` (1713 bytes, sha256 `a67923d042f3…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-100::trial-0003`

- Population: matched-budget follow-up (mb-v1) · Driver G · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-NORM / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/784d481c-0c5d-4602-819e-c29d52f56fa7.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/784d481c-0c5d-4602-819e-c29d52f56fa7.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/784d481c-0c5d-4602-819e-c29d52f56fa7.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 3 steps · 5 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/784d481c-0c5d-4602-819e-c29d52f56fa7.replay.json` (560 bytes, sha256 `0612ce622261…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/784d481c-0c5d-4602-819e-c29d52f56fa7.snapshot.json` (156 bytes, sha256 `eed5fec83179…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/784d481c-0c5d-4602-819e-c29d52f56fa7.actions.json` (1708 bytes, sha256 `8a4172d6c1ca…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-100::trial-0007`

- Population: matched-budget follow-up (mb-v1) · Driver G · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-SLOW / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/153de099-f6d4-4c3c-8a71-5119b0b2e928.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/153de099-f6d4-4c3c-8a71-5119b0b2e928.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/153de099-f6d4-4c3c-8a71-5119b0b2e928.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/153de099-f6d4-4c3c-8a71-5119b0b2e928.replay.json` (485 bytes, sha256 `ffe756ce1acd…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/153de099-f6d4-4c3c-8a71-5119b0b2e928.snapshot.json` (138 bytes, sha256 `0196ec9c2031…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/153de099-f6d4-4c3c-8a71-5119b0b2e928.actions.json` (1440 bytes, sha256 `6accae8f614f…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-100::trial-0009`

- Population: matched-budget follow-up (mb-v1) · Driver G · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-SLOW / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/0db54f67-1333-4537-8472-6b2eede4df79.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/0db54f67-1333-4537-8472-6b2eede4df79.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/0db54f67-1333-4537-8472-6b2eede4df79.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/0db54f67-1333-4537-8472-6b2eede4df79.replay.json` (485 bytes, sha256 `7f1d0bdfb781…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/0db54f67-1333-4537-8472-6b2eede4df79.snapshot.json` (138 bytes, sha256 `ac00cf6319b8…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/0db54f67-1333-4537-8472-6b2eede4df79.actions.json` (1440 bytes, sha256 `6a134c801a13…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-100::trial-0011`

- Population: matched-budget follow-up (mb-v1) · Driver G · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-DIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/df1604e0-5aa5-41b4-b861-372a305317a8.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/df1604e0-5aa5-41b4-b861-372a305317a8.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/df1604e0-5aa5-41b4-b861-372a305317a8.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/df1604e0-5aa5-41b4-b861-372a305317a8.replay.json` (486 bytes, sha256 `d13cd3f665f7…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/df1604e0-5aa5-41b4-b861-372a305317a8.snapshot.json` (138 bytes, sha256 `b3c8686ffd2a…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/df1604e0-5aa5-41b4-b861-372a305317a8.actions.json` (1443 bytes, sha256 `ac0830dd9587…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-100::trial-0014`

- Population: matched-budget follow-up (mb-v1) · Driver G · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-DIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/357bb2ab-684d-40c6-b91b-5a4a6fcbad11.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/357bb2ab-684d-40c6-b91b-5a4a6fcbad11.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/357bb2ab-684d-40c6-b91b-5a4a6fcbad11.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/357bb2ab-684d-40c6-b91b-5a4a6fcbad11.replay.json` (486 bytes, sha256 `40d3d2d3163b…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/357bb2ab-684d-40c6-b91b-5a4a6fcbad11.snapshot.json` (138 bytes, sha256 `2d59a7004066…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/357bb2ab-684d-40c6-b91b-5a4a6fcbad11.actions.json` (1443 bytes, sha256 `4c288ec41048…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-100::trial-0016`

- Population: matched-budget follow-up (mb-v1) · Driver G · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-SLOWDIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/c69322f3-24a3-4024-8f24-dcca745c5511.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/c69322f3-24a3-4024-8f24-dcca745c5511.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/c69322f3-24a3-4024-8f24-dcca745c5511.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/c69322f3-24a3-4024-8f24-dcca745c5511.replay.json` (496 bytes, sha256 `a860e1081f4e…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/c69322f3-24a3-4024-8f24-dcca745c5511.snapshot.json` (138 bytes, sha256 `9f170b128e48…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/c69322f3-24a3-4024-8f24-dcca745c5511.actions.json` (1473 bytes, sha256 `5b549f8d6070…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-100::trial-0018`

- Population: matched-budget follow-up (mb-v1) · Driver G · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-SLOWDIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 100ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill action…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/7f20e605-cdb1-47fd-a4b4-2c6c777090cf.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/7f20e605-cdb1-47fd-a4b4-2c6c777090cf.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/7f20e605-cdb1-47fd-a4b4-2c6c777090cf.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/7f20e605-cdb1-47fd-a4b4-2c6c777090cf.replay.json` (496 bytes, sha256 `fe6267d0940b…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/7f20e605-cdb1-47fd-a4b4-2c6c777090cf.snapshot.json` (138 bytes, sha256 `36490b7e0e74…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-100/7f20e605-cdb1-47fd-a4b4-2c6c777090cf.actions.json` (1473 bytes, sha256 `b49a3dd33ff5…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-1000::trial-0003`

- Population: matched-budget follow-up (mb-v1) · Driver A · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-NORM / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/28a8e12a-8f79-4b8b-8f9c-874d05ac4778.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/28a8e12a-8f79-4b8b-8f9c-874d05ac4778.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/28a8e12a-8f79-4b8b-8f9c-874d05ac4778.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 3 steps · 5 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/28a8e12a-8f79-4b8b-8f9c-874d05ac4778.replay.json` (560 bytes, sha256 `c4f45c6e138c…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/28a8e12a-8f79-4b8b-8f9c-874d05ac4778.snapshot.json` (156 bytes, sha256 `47a39f5c5113…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/28a8e12a-8f79-4b8b-8f9c-874d05ac4778.actions.json` (1708 bytes, sha256 `2c16dfb69203…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-1000::trial-0004`

- Population: matched-budget follow-up (mb-v1) · Driver A · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-NORM / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/83e3ff9d-c60c-4644-920d-ebe637b95387.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/83e3ff9d-c60c-4644-920d-ebe637b95387.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/83e3ff9d-c60c-4644-920d-ebe637b95387.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 3 steps · 5 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/83e3ff9d-c60c-4644-920d-ebe637b95387.replay.json` (560 bytes, sha256 `32065fca5192…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/83e3ff9d-c60c-4644-920d-ebe637b95387.snapshot.json` (156 bytes, sha256 `33e26eef4912…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/83e3ff9d-c60c-4644-920d-ebe637b95387.actions.json` (1708 bytes, sha256 `afd81a2f7ea2…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-1000::trial-0006`

- Population: matched-budget follow-up (mb-v1) · Driver A · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-SLOW / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 1000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/625ac7ec-153c-4c0c-ae54-f829dd2d8467.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/625ac7ec-153c-4c0c-ae54-f829dd2d8467.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/625ac7ec-153c-4c0c-ae54-f829dd2d8467.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/625ac7ec-153c-4c0c-ae54-f829dd2d8467.replay.json` (485 bytes, sha256 `5a7e71c47313…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/625ac7ec-153c-4c0c-ae54-f829dd2d8467.snapshot.json` (138 bytes, sha256 `32b09324ba25…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/625ac7ec-153c-4c0c-ae54-f829dd2d8467.actions.json` (1443 bytes, sha256 `95abb64946e0…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-1000::trial-0009`

- Population: matched-budget follow-up (mb-v1) · Driver A · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-SLOW / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 1000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/50aff475-9f29-4127-9754-81a687bab293.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/50aff475-9f29-4127-9754-81a687bab293.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/50aff475-9f29-4127-9754-81a687bab293.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/50aff475-9f29-4127-9754-81a687bab293.replay.json` (485 bytes, sha256 `7b1ac22eb9e8…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/50aff475-9f29-4127-9754-81a687bab293.snapshot.json` (138 bytes, sha256 `015bf33fdfe0…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/50aff475-9f29-4127-9754-81a687bab293.actions.json` (1443 bytes, sha256 `e8d249009bfc…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-1000::trial-0013`

- Population: matched-budget follow-up (mb-v1) · Driver A · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-DIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 1000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/192af011-4f17-47ed-9ec2-f47566377c2e.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/192af011-4f17-47ed-9ec2-f47566377c2e.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/192af011-4f17-47ed-9ec2-f47566377c2e.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/192af011-4f17-47ed-9ec2-f47566377c2e.replay.json` (486 bytes, sha256 `b13bf82e4292…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/192af011-4f17-47ed-9ec2-f47566377c2e.snapshot.json` (138 bytes, sha256 `29dd7383f883…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/192af011-4f17-47ed-9ec2-f47566377c2e.actions.json` (1446 bytes, sha256 `4929ea475073…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-1000::trial-0015`

- Population: matched-budget follow-up (mb-v1) · Driver A · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-DIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 1000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/4d56431e-c2a4-4ed9-9c37-41d4d6763df1.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/4d56431e-c2a4-4ed9-9c37-41d4d6763df1.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/4d56431e-c2a4-4ed9-9c37-41d4d6763df1.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/4d56431e-c2a4-4ed9-9c37-41d4d6763df1.replay.json` (486 bytes, sha256 `28b1b82c7434…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/4d56431e-c2a4-4ed9-9c37-41d4d6763df1.snapshot.json` (138 bytes, sha256 `985ce5278a28…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/4d56431e-c2a4-4ed9-9c37-41d4d6763df1.actions.json` (1446 bytes, sha256 `66e9db8727a3…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-1000::trial-0016`

- Population: matched-budget follow-up (mb-v1) · Driver A · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-SLOWDIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 1000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/873320bd-5539-402a-8e16-5478d4d39c46.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/873320bd-5539-402a-8e16-5478d4d39c46.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/873320bd-5539-402a-8e16-5478d4d39c46.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/873320bd-5539-402a-8e16-5478d4d39c46.replay.json` (496 bytes, sha256 `3f5382b9cc09…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/873320bd-5539-402a-8e16-5478d4d39c46.snapshot.json` (138 bytes, sha256 `fc974897b749…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/873320bd-5539-402a-8e16-5478d4d39c46.actions.json` (1476 bytes, sha256 `36403ac4d2a9…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-1000::trial-0017`

- Population: matched-budget follow-up (mb-v1) · Driver A · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-SLOWDIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 1000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/5a16b46d-9b50-443a-a8c9-aa506dfc6118.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/5a16b46d-9b50-443a-a8c9-aa506dfc6118.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/5a16b46d-9b50-443a-a8c9-aa506dfc6118.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/5a16b46d-9b50-443a-a8c9-aa506dfc6118.replay.json` (496 bytes, sha256 `76370a4b9a87…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/5a16b46d-9b50-443a-a8c9-aa506dfc6118.snapshot.json` (138 bytes, sha256 `bdc4de3353db…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-1000/5a16b46d-9b50-443a-a8c9-aa506dfc6118.actions.json` (1476 bytes, sha256 `1f1b9b3456d9…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-2500::trial-0003`

- Population: matched-budget follow-up (mb-v1) · Driver E · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-NORM / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/490d0bfb-c55b-466e-bbd8-57943dfb1773.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/490d0bfb-c55b-466e-bbd8-57943dfb1773.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/490d0bfb-c55b-466e-bbd8-57943dfb1773.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 3 steps · 5 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/490d0bfb-c55b-466e-bbd8-57943dfb1773.replay.json` (560 bytes, sha256 `293f2e82329c…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/490d0bfb-c55b-466e-bbd8-57943dfb1773.snapshot.json` (156 bytes, sha256 `0511c61027da…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/490d0bfb-c55b-466e-bbd8-57943dfb1773.actions.json` (1708 bytes, sha256 `3e5f348ec8a2…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-2500::trial-0004`

- Population: matched-budget follow-up (mb-v1) · Driver E · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-NORM / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/fda6b6d8-1958-4a9d-9bcb-029dfb3ac687.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/fda6b6d8-1958-4a9d-9bcb-029dfb3ac687.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/fda6b6d8-1958-4a9d-9bcb-029dfb3ac687.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 3 steps · 5 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/fda6b6d8-1958-4a9d-9bcb-029dfb3ac687.replay.json` (560 bytes, sha256 `0d598bbcef34…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/fda6b6d8-1958-4a9d-9bcb-029dfb3ac687.snapshot.json` (156 bytes, sha256 `c1cca7570c39…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/fda6b6d8-1958-4a9d-9bcb-029dfb3ac687.actions.json` (1708 bytes, sha256 `8ad56310cb41…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-2500::trial-0006`

- Population: matched-budget follow-up (mb-v1) · Driver E · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-SLOW / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/85abc0d2-8ebc-412a-8284-b12114c0babb.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/85abc0d2-8ebc-412a-8284-b12114c0babb.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/85abc0d2-8ebc-412a-8284-b12114c0babb.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 3 steps · 5 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/85abc0d2-8ebc-412a-8284-b12114c0babb.replay.json` (570 bytes, sha256 `358e938c1133…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/85abc0d2-8ebc-412a-8284-b12114c0babb.snapshot.json` (156 bytes, sha256 `60bdff3fa16d…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/85abc0d2-8ebc-412a-8284-b12114c0babb.actions.json` (1742 bytes, sha256 `817aac91e0b0…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-2500::trial-0007`

- Population: matched-budget follow-up (mb-v1) · Driver E · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-SLOW / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/50fb12fd-4b2d-4eae-800b-bc085008d109.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/50fb12fd-4b2d-4eae-800b-bc085008d109.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/50fb12fd-4b2d-4eae-800b-bc085008d109.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 3 steps · 5 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/50fb12fd-4b2d-4eae-800b-bc085008d109.replay.json` (570 bytes, sha256 `e97e2171427b…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/50fb12fd-4b2d-4eae-800b-bc085008d109.snapshot.json` (156 bytes, sha256 `1faffc1cc5bb…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/50fb12fd-4b2d-4eae-800b-bc085008d109.actions.json` (1742 bytes, sha256 `b89d6af34098…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-2500::trial-0012`

- Population: matched-budget follow-up (mb-v1) · Driver E · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-DIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 2500ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/8835da2a-f27d-4607-8b76-f28dc4ef86a4.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/8835da2a-f27d-4607-8b76-f28dc4ef86a4.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/8835da2a-f27d-4607-8b76-f28dc4ef86a4.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/8835da2a-f27d-4607-8b76-f28dc4ef86a4.replay.json` (486 bytes, sha256 `332adaf91fed…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/8835da2a-f27d-4607-8b76-f28dc4ef86a4.snapshot.json` (138 bytes, sha256 `dc7d9d1cc573…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/8835da2a-f27d-4607-8b76-f28dc4ef86a4.actions.json` (1446 bytes, sha256 `f0617b64f72f…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-2500::trial-0014`

- Population: matched-budget follow-up (mb-v1) · Driver E · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-DIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 2500ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/69639934-494b-4d68-bc9b-8e65ede956f7.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/69639934-494b-4d68-bc9b-8e65ede956f7.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/69639934-494b-4d68-bc9b-8e65ede956f7.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/69639934-494b-4d68-bc9b-8e65ede956f7.replay.json` (486 bytes, sha256 `baaf0abacd09…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/69639934-494b-4d68-bc9b-8e65ede956f7.snapshot.json` (138 bytes, sha256 `a11144994d84…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/69639934-494b-4d68-bc9b-8e65ede956f7.actions.json` (1446 bytes, sha256 `a68b3fd84354…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-2500::trial-0017`

- Population: matched-budget follow-up (mb-v1) · Driver E · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-SLOWDIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 2500ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/0f186ee0-5292-4a38-8c8e-75ad71b89f16.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/0f186ee0-5292-4a38-8c8e-75ad71b89f16.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/0f186ee0-5292-4a38-8c8e-75ad71b89f16.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/0f186ee0-5292-4a38-8c8e-75ad71b89f16.replay.json` (496 bytes, sha256 `0054d643513f…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/0f186ee0-5292-4a38-8c8e-75ad71b89f16.snapshot.json` (138 bytes, sha256 `e92c7c797207…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/0f186ee0-5292-4a38-8c8e-75ad71b89f16.actions.json` (1476 bytes, sha256 `fcd50aeec8ff…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-2500::trial-0019`

- Population: matched-budget follow-up (mb-v1) · Driver E · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-SLOWDIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 2500ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/30263ce3-75a3-4928-a9e5-c4ee486b6d14.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/30263ce3-75a3-4928-a9e5-c4ee486b6d14.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/30263ce3-75a3-4928-a9e5-c4ee486b6d14.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/30263ce3-75a3-4928-a9e5-c4ee486b6d14.replay.json` (496 bytes, sha256 `39bf47edb5bc…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/30263ce3-75a3-4928-a9e5-c4ee486b6d14.snapshot.json` (138 bytes, sha256 `a27555cf4d81…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-2500/30263ce3-75a3-4928-a9e5-c4ee486b6d14.actions.json` (1476 bytes, sha256 `2612b756309b…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-5000::trial-0003`

- Population: matched-budget follow-up (mb-v1) · Driver D · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-NORM / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/8298dbec-1fb8-4260-87eb-e3e59f125564.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/8298dbec-1fb8-4260-87eb-e3e59f125564.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/8298dbec-1fb8-4260-87eb-e3e59f125564.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 3 steps · 5 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/8298dbec-1fb8-4260-87eb-e3e59f125564.replay.json` (560 bytes, sha256 `cf494d4ec432…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/8298dbec-1fb8-4260-87eb-e3e59f125564.snapshot.json` (156 bytes, sha256 `1b65d08c3e88…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/8298dbec-1fb8-4260-87eb-e3e59f125564.actions.json` (1708 bytes, sha256 `c381d5cacce6…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-5000::trial-0004`

- Population: matched-budget follow-up (mb-v1) · Driver D · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-NORM / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/5737a38c-7c57-4cb0-a983-3655df2939cc.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/5737a38c-7c57-4cb0-a983-3655df2939cc.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/5737a38c-7c57-4cb0-a983-3655df2939cc.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 3 steps · 5 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/5737a38c-7c57-4cb0-a983-3655df2939cc.replay.json` (560 bytes, sha256 `3fd9774bfa78…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/5737a38c-7c57-4cb0-a983-3655df2939cc.snapshot.json` (156 bytes, sha256 `3f3f843eb95c…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/5737a38c-7c57-4cb0-a983-3655df2939cc.actions.json` (1708 bytes, sha256 `e1a087b73609…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-5000::trial-0008`

- Population: matched-budget follow-up (mb-v1) · Driver D · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-SLOW / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/3355415f-eb09-45cb-90e7-5464adc2fa99.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/3355415f-eb09-45cb-90e7-5464adc2fa99.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/3355415f-eb09-45cb-90e7-5464adc2fa99.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 3 steps · 5 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/3355415f-eb09-45cb-90e7-5464adc2fa99.replay.json` (570 bytes, sha256 `df36526dd7e1…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/3355415f-eb09-45cb-90e7-5464adc2fa99.snapshot.json` (156 bytes, sha256 `dd3cd68c31a0…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/3355415f-eb09-45cb-90e7-5464adc2fa99.actions.json` (1742 bytes, sha256 `ae130a95793f…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-5000::trial-0010`

- Population: matched-budget follow-up (mb-v1) · Driver D · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-SLOW / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `succeeded` · agent said `succeeded` · error: `—`
- Verifier: status `verified`, all_satisfied=true, checks `[{"detail": "confirmation_visible=True", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/1567030a-39f7-431f-8d4d-4e2c7639d778.snapshot.json#P1", "postcondition_id": "P1", "satisfied": true}, {"detail": "1 of 1 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/1567030a-39f7-431f-8d4d-4e2c7639d778.snapshot.json#P2", "postcondition_id": "P2", "satisfied": true}, {"detail": "project-list count=1, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/1567030a-39f7-431f-8d4d-4e2c7639d778.snapshot.json#P3", "postcondition_id": "P3", "satisfied": true}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 3 steps · 5 observed actions · snapshot confirmation_visible=true items=["Benchmark Project"]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/1567030a-39f7-431f-8d4d-4e2c7639d778.replay.json` (570 bytes, sha256 `ef6a7cdc9156…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/1567030a-39f7-431f-8d4d-4e2c7639d778.snapshot.json` (156 bytes, sha256 `172fb18ac783…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/1567030a-39f7-431f-8d4d-4e2c7639d778.actions.json` (1742 bytes, sha256 `f5381066a747…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-5000::trial-0011`

- Population: matched-budget follow-up (mb-v1) · Driver D · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-DIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/caa7b477-9e78-476c-8b7a-c2e58347a491.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/caa7b477-9e78-476c-8b7a-c2e58347a491.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/caa7b477-9e78-476c-8b7a-c2e58347a491.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/caa7b477-9e78-476c-8b7a-c2e58347a491.replay.json` (486 bytes, sha256 `0176dccda826…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/caa7b477-9e78-476c-8b7a-c2e58347a491.snapshot.json` (138 bytes, sha256 `c99cd5965666…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/caa7b477-9e78-476c-8b7a-c2e58347a491.actions.json` (1446 bytes, sha256 `0bf7121127b6…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-5000::trial-0014`

- Population: matched-budget follow-up (mb-v1) · Driver D · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-DIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/8642c19e-0b2e-4a93-abf9-0526825230cc.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/8642c19e-0b2e-4a93-abf9-0526825230cc.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/8642c19e-0b2e-4a93-abf9-0526825230cc.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/8642c19e-0b2e-4a93-abf9-0526825230cc.replay.json` (486 bytes, sha256 `f0b256985af1…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/8642c19e-0b2e-4a93-abf9-0526825230cc.snapshot.json` (138 bytes, sha256 `7eac7a228a61…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/8642c19e-0b2e-4a93-abf9-0526825230cc.actions.json` (1446 bytes, sha256 `6e41a4fd9aa5…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-5000::trial-0017`

- Population: matched-budget follow-up (mb-v1) · Driver D · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-SLOWDIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/993d3482-c1da-498b-9ddf-1e6d625f0ca5.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/993d3482-c1da-498b-9ddf-1e6d625f0ca5.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/993d3482-c1da-498b-9ddf-1e6d625f0ca5.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/993d3482-c1da-498b-9ddf-1e6d625f0ca5.replay.json` (496 bytes, sha256 `bd155e3c7755…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/993d3482-c1da-498b-9ddf-1e6d625f0ca5.snapshot.json` (138 bytes, sha256 `eaa291e432bf…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/993d3482-c1da-498b-9ddf-1e6d625f0ca5.actions.json` (1476 bytes, sha256 `392080ea03a2…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

### `main-mb-v1-replay-5000::trial-0020`

- Population: matched-budget follow-up (mb-v1) · Driver D · manifest `experiments/matched-budget-v1/manifest-mb-v1.json` (`mb-v1`)
- Condition: S-SLOWDIS / I-PLAIN / baseline-a · expected stored name: 'Benchmark Project'
- Recorded outcome: `failed` · agent said `failed` · error: `TimeoutError: Locator.fill: Timeout 5000ms exceeded.
Call log:
  - waiting for get_by_label("Project Name")
    - locator resolved to <input disabled type="text" required="" id="project-name" name="project-name" aria-label="Project Name"/>
    - fill("Benchmark Project")
  - attempting fill actio…`
- Verifier: status `verified`, all_satisfied=false, checks `[{"detail": "confirmation_visible=False", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/60888520-4799-4a7e-8da6-1453e5939573.snapshot.json#P1", "postcondition_id": "P1", "satisfied": false}, {"detail": "0 of 0 items equal 'Benchmark Project' (exact match)", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/60888520-4799-4a7e-8da6-1453e5939573.snapshot.json#P2", "postcondition_id": "P2", "satisfied": false}, {"detail": "project-list count=0, expected 1", "evidence_reference": "/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/60888520-4799-4a7e-8da6-1453e5939573.snapshot.json#P3", "postcondition_id": "P3", "satisfied": false}]` (independent-verifier-1.0)
- Evidence kind: `replay` · 2 steps · 4 observed actions · snapshot confirmation_visible=false items=[]
- trace: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/60888520-4799-4a7e-8da6-1453e5939573.replay.json` (496 bytes, sha256 `37278e6c1a5f…`, verified)
- snapshot: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/60888520-4799-4a7e-8da6-1453e5939573.snapshot.json` (138 bytes, sha256 `e2f833b2e7fb…`, verified)
- actions: `/Users/kartikbhardwaj/project-chimera/experiments/matched-budget-v1/runs/traces-main-mb-v1-replay-5000/60888520-4799-4a7e-8da6-1453e5939573.actions.json` (1476 bytes, sha256 `13bc9cb131dc…`, verified)
- Screenshots: none attached
- Gap: no screenshots attached (expected: the harness captures one only on action failure)
- Gap: step report carries step indexes only — no timestamps or trace sequence numbers

## Review protocol

1. Assess each episode blinded (driver identity, recorded outcome, and verifier checks masked): record your own true/false judgment for P1, P2, and P3 from the postconditions and the evidence above — never from success strings or the verifier's status.
2. If the evidence cannot support a judgment, mark the episode unauditable with an explicit reason tied to specific observations.
3. Reveal the recorded verdict only after saving your own decision.
4. Export `decisions.json` and validate it with `tools/mini_review.py validate --dir <packet-dir>`.
5. Apply validated decisions to the audit plans with `tools/mini_review.py apply-verdicts --packet <packet-dir>` (dry-run first; `--write` only after review is complete).

Populations stay separate: agreement is computed per population and per run, never pooled across experiments. The 95% provisional rule (user guide §15.1 step 4) applies per population once its required sample is fully adjudicated.
