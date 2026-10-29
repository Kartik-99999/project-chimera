# Evaluation Approaches for Browser Agents — Survey

Companion to [`evaluation.md`](evaluation.md) (Chimera's evaluation criteria)
and [`benchmark_design.md`](benchmark_design.md) (the proposed initial
benchmark). This document surveys what the field measures, so that Chimera's
benchmark borrows established methodology instead of inventing its own.

**Survey date:** 2026-10-24. **Method:** the arXiv API (`export.arxiv.org`)
and the official benchmark site `webarena.dev` were queried directly; every
entry below was retrieved and its title, authors, date and abstract read in
the session that wrote this file. General web search returned no usable
results, so **this survey is arXiv- and official-site-centric**; it is
likely to under-represent non-published industry benchmarks and any work
published only as a technical report or blog post. Leaderboard numbers
quoted here are those stated **in the papers themselves**, not live
leaderboard values as of the survey date.

---

## 1. Taxonomy

Seven families of approach, each answering a different question.

| # | Family | Question it answers | Representative works |
|---|---|---|---|
| A | Realistic self-hosted environments | Can the agent do real work in a faithful site? | WebArena, VisualWebArena, WorkArena, TheAgentCompany, OSWorld |
| B | Demonstration datasets | Can it generalise to unseen sites from human traces? | Mind2Web, WebLINX |
| C | Synthetic task suites | Can it execute fine-grained UI actions reliably? | MiniWoB++, WebShop |
| D | LLM-as-judge / open-ended scoring | Can it handle tasks with no exact checker? | WebVoyager; *A Survey on LLM-as-a-Judge* |
| E | Reliability under repetition | Is success consistent, not just occasional? | τ-bench (`pass^k`) |
| F | Safety and adversarial evaluation | Does it resist injected instructions and unauthorised actions? | AgentDojo, AgentHarm, Agent-SafetyBench, TRAP, BrowseSafe |
| G | Evaluation-methodology hygiene | Is the benchmark itself sound? | ABC checklist, WebArena-Lite human audit, statistical diagnosis of web agents |

---

## 2. Family A — Realistic self-hosted environments

**WebArena** — Shuyan Zhou, Frank F. Xu, Hao Zhu, Xuhui Zhou, Robert Lo,
Abishek Sridhar, Xianyi Cheng, Tianyue Ou, Yonatan Bisk, Daniel Fried, Uri
Alon, Graham Neubig. *WebArena: A Realistic Web Environment for Building
Autonomous Agents.* arXiv:2307.13854, v1 2023-07-25 (v4 current).
<https://arxiv.org/abs/2307.13854> · Official site:
<https://webarena.dev/> (now "WebArena-x", a suite covering WebArena,
WebArena-Infinity, VisualWebArena and TheAgentCompany; WebArena published at
NeurIPS 2024, Oral).

- **Measures:** end-to-end task success on long-horizon tasks over working
  self-hosted sites (e-commerce, forum, git, CMS, map, encyclopedia),
  scored by **functional correctness** — the final state of the environment
  is checked programmatically, not by asking a model.
- **Strengths:** reproducible and self-hosted; state-based checkers make the
  grader independent of the agent's own reasoning; the reference point for
  almost every later web-agent paper.
- **Limitations:** heavy infrastructure; task authoring and per-task
  checkers are expensive; the environment is a *simulation* of the web, and
  its failure modes are not the real web's.
- **Reported results:** best GPT-4-based agent **14.41%** end-to-end task
  success vs. a human **78.24%** — the paper's own framing is that leading
  models were "far from dependable" on realistic web tasks.
- **Relevance to Chimera:** high, as a *method* model. WebArena's
  state-checker grading is exactly the "independently verified
  postcondition" discipline Chimera must adopt for its false-success
  metric. Its scale is out of reach for the current milestone, and Chimera's
  single-workflow, local-target benchmark must not be presented as a
  WebArena equivalent.

**VisualWebArena** — Jing Yu Koh et al. *VisualWebArena: Evaluating
Multimodal Agents on Realistic Visual Web Tasks.* arXiv:2401.13649, v1
2024-01-24. <https://arxiv.org/abs/2401.13649>. Adds the visual
(ARIA-tree + screenshot) observation mode that text-only agents lack.
Relevant to Chimera only if a future observer consumes rendered pixels
rather than the accessibility tree.

**WorkArena** — Alexandre Drouin, Maxime Gasse, Massimo Caccia, Issam H.
Laradji, Manuel Del Verme, Tom Marty, Léo Boisvert, Megh Thakkar, Quentin
Cappart, David Vazquez, Nicolas Chapados, Alexandre Lacoste. *WorkArena: How
Capable Are Web Agents at Solving Common Knowledge Work Tasks?*
arXiv:2403.07718, v1 2024-03-12 (v5 2024-07-23).
<https://arxiv.org/abs/2403.07718>. **33 tasks** on a real ServiceNow
instance. Relevant to Chimera as a second source of the *enterprise task*
formulation; noted for its controlled, resettable instance — the property
Chimera's demo app already has.

**TheAgentCompany** — Frank F. Xu et al. *TheAgentCompany: Benchmarking LLM
Agents on Consequential Real World Tasks.* arXiv:2412.14161, v1 2024-12-18.
<https://arxiv.org/abs/2412.14161>. A simulated software company with
checkpoint-based partial credit. Relevant to Chimera for **partial-credit /
checkpoint evaluation** — the closest published analogue to "did the run
reach a known intermediate state", which is what Chimera's per-postcondition
verification already produces.

**OSWorld** — Tianbao Xie et al. *OSWorld: Benchmarking Multimodal Agents for
Open-Ended Tasks in Real Computer Environments.* arXiv:2404.07972, v1
2024-04-11. <https://arxiv.org/abs/2404.07972>. Full-desktop rather than
browser-only; included for the *cross-environment* generality argument, not
for its task set.

---

## 3. Family B — Demonstration datasets

**Mind2Web** — Xiang Deng, Yu Gu, Boyuan Zheng, Shijie Chen, Samuel Stevens,
Boshi Wang, Huan Sun, Yu Su. *Mind2Web: Towards a Generalist Agent for the
Web.* arXiv:2306.06070, v1 2023-06-09 (v3 2023-12-09).
<https://arxiv.org/abs/2306.06070>. **2,000+ open-ended tasks across 137
websites and 31 domains**, with human-recorded action sequences.

- **Measures:** step-level and task-level success; **cross-domain
  generalisation** to sites and domains unseen in training.
- **Strengths:** the reference dataset for generalisation claims; provides
  ground-truth action sequences usable for a *replay* baseline.
- **Limitations:** recordings are of a human, so "correct" is one
  plausible path, not the only one; static snapshots of live sites drift;
  step-level metrics reward path-matching rather than outcome.
- **Relevance to Chimera:** this is where Chimera is weakest. Chimera has
  **one** hard-coded workflow against **one** local target and therefore
  **no cross-site or cross-domain generalisation claim it is entitled to
  make**. Chimera's benchmark must report robustness to *parameter
  variation*, and must never be described as a generalisation benchmark.

**WebLINX** — Xing Han Lù et al. *WebLINX: Real-World Website Navigation with
Multi-Turn Dialogue.* arXiv:2402.05930, v1 2024-02-08.
<https://arxiv.org/abs/2402.05930>. Conversational navigation over live
websites with expert demonstrations. Relevant to the future conversational
UI (SRS §13), not to the current benchmark.

---

## 4. Family C — Synthetic task suites

**MiniWoB++** — Peter C. Humphreys et al. *A data-driven approach for
learning to control computers.* arXiv:2202.08137, v1 2022-02-16.
<https://arxiv.org/abs/2202.08137>. The synthetic mini-web task suite whose
tasks each have a **programmatic success predicate** (state of one or two
DOM elements).

- **Measures:** fine-grained UI-action competence; cheap, parallel,
  deterministic, resettable.
- **Strengths:** the closest published analogue to Chimera's setting — a
  controlled, fault-injectable, deterministically-checked page. The
  failure-recovery literature built on it (e.g. *SteP: Stacked LLM Policies
  for Web Actions*, Paloma Sodhi et al., arXiv:2310.03720, v1 2023-10-05) is
  the most transferable prior art to Chimera's fault scenarios.
- **Limitations:** synthetic pages are simpler than real sites; a high score
  says little about the open web.
- **Relevance to Chimera:** **the highest of any benchmark surveyed.** It
  is the precedent for "small, controlled, fault-injected, programmatically
  scored" evaluation — which is exactly what Chimera's demo application
  provides. The lesson to copy is the *predicates*, not the scale.

**WebShop** — Shunyu Yao et al. *WebShop: Towards Scalable Real-World Web
Interaction with Grounded Language Agents.* arXiv:2207.01206, v1 2022-07-04.
<https://arxiv.org/abs/2207.01206>. Simulated store; scoring compares the
final cart/order state against the goal. Reports **29%** task success for
the best model vs. **59%** for a human expert — a useful calibration point
for how far a scripted-or-LLM agent is from a person on even a constrained
shopping task.

---

## 5. Family D — LLM-as-judge and open-ended scoring

**WebVoyager** — Hongliang He et al. *WebVoyager: Building an End-to-End
Web Agent with Large Multimodal Models.* arXiv:2401.13919, v1 2024-01-25.
<https://arxiv.org/abs/2401.13919>. Evaluated on 15 real-world websites,
judged by an LLM using a task-specific rubric rather than a state checker.

**A Survey on LLM-as-a-Judge** — Jiawei Gu et al. *A Survey on LLM-as-a-Judge.*
arXiv:2411.15594, v1 2024-11-23. <https://arxiv.org/abs/2411.15594>. The
reference survey for judge reliability, bias, and cost.

- **Strengths:** scales to open-ended tasks with no exact checker; cheap.
- **Limitations:** the judge is a model, so judge error becomes benchmark
  error; position/verbosity bias is documented; results are not
  reproducible without fixing the judge, its prompt and its model version.
- **Relevance to Chimera:** **use only where no deterministic checker
  exists.** Chimera's postconditions are all deterministically checkable, so
  Chimera's benchmark should use programmatic checkers and reserve a judge
  for a documented fallback — and, if a judge is ever used, record the
  judge model, version and prompt, and report human-audited agreement on a
  sample. Note that the WebArena-Lite audit (Family G) found automatic
  grading *understated* success by 5.45–8.49 percentage points, i.e. judge
  and checker error is real in both directions.

---

## 6. Family E — Reliability under repetition

**τ-bench** — Shunyu Yao, Noah Shinn, Pedram Razavi, Karthik Narasimhan.
*τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World
Domains.* arXiv:2406.12045, v1 2024-06-17.
<https://arxiv.org/abs/2406.12045>. Introduces **pass^k** — the probability
of succeeding on *all k* consecutive trials — to separate "works
sometimes" from "works reliably". Evaluation compares the **final database
state** against the annotated desired state. Reports GPT-4o function-calling
agents below 50% task success, with retail **pass^8 below 25%**.

- **Why it matters for Chimera:** a single-episode success rate is a
  weak and easily inflated statistic. `pass^k` is the published precedent
  for the **repeated-trial protocol** Chimera's benchmark needs, and its
  "final state vs. desired state" check is the same independent-verification
  pattern Chimera requires for its false-success metric.
- **Limitation / caution:** the ABC checklist (§7) reports that τ-bench
  "counts empty responses as successful" — a concrete example of a grader
  bug inflating scores. Treat any imported metric definition as needing its
  own audit.

---

## 7. Family F — Safety and adversarial evaluation

**AgentDojo** — Edoardo Debenedetti et al. *AgentDojo: A Dynamic Environment
to Evaluate Prompt Injection Attacks and Defenses for LLM Agents.*
arXiv:2406.13352, v1 2024-06-19. <https://arxiv.org/abs/2406.13352>.

**AgentHarm** — Maksym Andriushchenko et al. *AgentHarm: A Benchmark for
Measuring Harmfulness of LLM Agents.* arXiv:2410.09024, v1 2024-10-11.
<https://arxiv.org/abs/2410.09024>.

**Agent-SafetyBench** — Zhexin Zhang et al. *Agent-SafetyBench: Evaluating
the Safety of LLM Agents.* arXiv:2412.14470, v1 2024-12-19.
<https://arxiv.org/abs/2412.14470>. 349 interactive settings and 2,000
cases organised around eight risk types and ten recurring failure patterns.

**It's a TRAP!** — Karolina Korgul et al. *It's a TRAP! Task-Redirecting Agent
Persuasion Benchmark for Web Agents.* arXiv:2512.23128, v1 2025-12-29.
<https://arxiv.org/abs/2512.23128>. Measures task *diversion* — the page
persuading the agent to do something else — across six frontier models, with
**25% average susceptibility** and high sensitivity to small contextual
changes.

**BrowseSafe** — Kaiyuan Zhang et al. *BrowseSafe: Understanding and
Preventing Prompt Injection Within AI Browser Agents.* arXiv:2511.20597, v1
2025-11-25. <https://arxiv.org/abs/2511.20597>. Notably, its benchmark
targets **consequential browser actions** rather than altered generated
text — the same distinction Chimera's threat model draws between "the text
changed" and "the action changed".

- **Relevance to Chimera:** directly relevant to the residual risks in
  [`threat_model.md`](threat_model.md) §5 — R-2 (authorization for
  consequential actions), R-5 (prompt-injection defence) and R-9
  (adversarial tests). Two design points to adopt: (i) measure safety on
  **outcomes** (did an unauthorised action occur?) rather than on
  token-level defences; (ii) report a *task-diversion* rate distinct from
  an injection *success* rate, since a page can divert the agent without
  injecting text.

---

## 8. Family G — Evaluation-methodology hygiene

**Establishing Best Practices for Building Rigorous Agentic Benchmarks** —
Yuxuan Zhu, Tengjun Jin, Yada Pruksachatkun, Andy Zhang, Shu Liu, Sasha Cui,
Sayash Kapoor, Shayne Longpre, Kevin Meng, Rebecca Weiss, Fazl Barez, Rahul
Gupta, Jwala Dhamala, Jacob Merizian, Mario Giulianelli, Harry Coppock, Cozmin
Ududec, Jasjeet Sekhon, Jacob Steinhardt, Antony Kellermann, Sarah
Schwettmann, Matei Zaharia, Ion Stoica, Percy Liang, Daniel Kang.
arXiv:2507.02825, v1 2025-07-03. <https://arxiv.org/abs/2507.02825>.
Proposes the **Agentic Benchmark Checklist (ABC)**, and reports that flaws
in task construction or reward design can cause "under- or overestimation of
agents' performance by up to 100% in relative terms"; applied to CVE-Bench
it "reduces the performance overestimation by 33%".

**Auditing Web Agent Evaluation on WebArena-Lite: Human Review of Outcomes
and Trajectories** — Chengguang Gan, Zimeng He, Yoshihiro Tsujii, Ken-ichiro
Kobayashi, Hiroki Itoh, Kotaro Funakoshi. arXiv:2610.01491, v1 2026-10-01.
<https://arxiv.org/abs/2610.01491>. Human review of **all 165** WebArena
Lite tasks across six configurations, with trajectory-level error analysis.

- **Measured findings relevant to Chimera:** human review recovered
  **5.45–8.49 percentage points** of success that the automatic evaluator
  had wrongly rejected, across four GPT-5.5 configurations; the analysis of
  102 failed trajectories identified recurring patterns (scrolling loops,
  unfinished exploration, premature responses, invalid actions, incomplete
  form workflows); and the authors conclude that **endpoint scores alone do
  not fully characterise web-agent behaviour**. The abstract reports **no
  count or rate of false successes** (tasks that scored as successes but
  were not) — so this paper supplies no basis for any claim that published
  browser-agent performance was *overstated*; the quantified error it
  establishes runs in the opposite direction.
- **Direct implications for Chimera's design:**
  1. A benchmark must have a **human-audited** component, or at minimum a
     documented audit of a sample. Chimera's benchmark therefore specifies
     a human-adjudicated subset.
  2. **Trajectory-level analysis** is required, not just the terminal
     state. Chimera's trace artifacts already contain the full trajectory,
     so this is achievable at low cost.
  3. A grader can be wrong in **both** directions. Chimera's false-success
     metric must be computed by an independent verifier and the verifier
     itself must be audited.
  4. Failure trajectories should be **categorised** (scrolling loops,
     unfinished exploration, premature response, invalid action, incomplete
     form workflow), not merely counted.

**How to Train Your LLM Web Agent: A Statistical Diagnosis** — Dheeraj
Vattikonda et al. arXiv:2507.04103, v1 2025-07-05.
<https://arxiv.org/abs/2507.04103>. Evaluates WorkArena and MiniWoB++ with
an explicit statistical treatment; relevant to choosing trial counts and
reporting variance rather than bare point estimates.

---

## 9. What this survey implies for Chimera's benchmark

Directly transferable practices, with their source:

1. **Check the final environment state, not the agent's narration.**
   (WebArena, τ-bench, TheAgentCompany.) → Chimera's false-success metric
   must be computed by a verifier that does not share the agent's code path.
2. **Score against known desired state, per checkpoint/postcondition.**
   (TheAgentCompany, WebShop.) → report per-postcondition success, not only
   task-level success.
3. **Repeat trials and report a reliability statistic, not one episode.**
   (τ-bench `pass^k`; statistical diagnosis.) → fixed trial count, reported
   n, and a confidence bound for every rate — including zero-failure rates.
4. **Prefer programmatic checkers; use a judge only as a documented
   fallback, and audit the judge.** (WebArena vs. WebVoyager; the LLM-as-a-
   Judge survey; the WebArena-Lite audit.)
5. **Measure safety as an outcome rate on consequential actions**, and
   separate *task diversion* from *injection success*. (TRAP, BrowseSafe,
   Agent-SafetyBench.)
6. **Analyse trajectories, not just endpoints, and categorise failures.**
   (WebArena-Lite audit.)
7. **Audit the benchmark itself against a checklist before trusting a
   number.** (ABC checklist.)
8. **Declare split discipline and sample sizes in advance.** (ABC;
   SRS §11.2's own requirement that targets "must be reported with sample
   sizes and scenario definitions".)

Practices that do **not** transfer, and must not be imitated:

- Scale. WebArena's 812-task, six-site environment and Mind2Web's 2,000
  tasks across 137 sites are not reachable for Chimera's current
  implementation, and a 100-episode local benchmark must not be described
  as being in the same class.
- Leaderboard framing. Chimera has one workflow; there is no leaderboard,
  and no cross-system comparison is possible until a second system is
  implemented.

---

## 10. Limits of this survey

- **Source coverage is arXiv-centric** (plus the official `webarena.dev`
  site). General web search was unavailable in this session, so industry
  benchmarks published only as engineering blogs, and any 2026 work not on
  arXiv, are likely missing.
- **Only the abstract and metadata of each paper were read**, not the full
  text. Task counts, checker implementations and metric definitions were
  taken from the abstracts; where an abstract did not state a detail (for
  example WebArena's per-site task breakdown and the exact fuzzy-matcher
  implementation), this survey says so rather than filling the gap.
- **Leaderboard numbers are the papers' own reported figures at
  publication**, not current standings.
- The taxonomy in §1 is this survey's own organisation of the literature,
  not a classification any source uses.

---

## 11. Sources

All URLs verified 2026-10-24 via the arXiv API or the official site.

1. Zhou, S., Xu, F. F., Zhu, H., Zhou, X., Lo, R., Sridhar, A., Cheng, X., Ou, T., Bisk, Y., Fried, D., Alon, U., Neubig, G. — *WebArena: A Realistic Web Environment for Building Autonomous Agents.* arXiv:2307.13854, v1 2023-07-25. <https://arxiv.org/abs/2307.13854> · <https://webarena.dev/>
2. Koh, J. Y. et al. — *VisualWebArena: Evaluating Multimodal Agents on Realistic Visual Web Tasks.* arXiv:2401.13649, v1 2024-01-24. <https://arxiv.org/abs/2401.13649>
3. Drouin, A., Gasse, M., Caccia, M., Laradji, I. H., Del Verme, M., Marty, T., Boisvert, L., Thakkar, M., Cappart, Q., Vazquez, D., Chapados, N., Lacoste, A. — *WorkArena: How Capable Are Web Agents at Solving Common Knowledge Work Tasks?* arXiv:2403.07718, v1 2024-03-12. <https://arxiv.org/abs/2403.07718>
4. Le Sellier De Chezelles, T. et al. — *The BrowserGym Ecosystem for Web Agent Research.* arXiv:2412.05467, v1 2024-12-06. <https://arxiv.org/abs/2412.05467>
5. Xu, F. F. et al. — *TheAgentCompany: Benchmarking LLM Agents on Consequential Real World Tasks.* arXiv:2412.14161, v1 2024-12-18. <https://arxiv.org/abs/2412.14161>
6. Xie, T. et al. — *OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments.* arXiv:2404.07972, v1 2024-04-11. <https://arxiv.org/abs/2404.07972>
7. Deng, X., Gu, Y., Zheng, B., Chen, S., Stevens, S., Wang, B., Sun, H., Su, Y. — *Mind2Web: Towards a Generalist Agent for the Web.* arXiv:2306.06070, v1 2023-06-09. <https://arxiv.org/abs/2306.06070>
8. Lù, X. H. et al. — *WebLINX: Real-World Website Navigation with Multi-Turn Dialogue.* arXiv:2402.05930, v1 2024-02-08. <https://arxiv.org/abs/2402.05930>
9. Humphreys, P. C. et al. — *A data-driven approach for learning to control computers.* (MiniWoB++.) arXiv:2202.08137, v1 2022-02-16. <https://arxiv.org/abs/2202.08137>
10. Yao, S. et al. — *WebShop: Towards Scalable Real-World Web Interaction with Grounded Language Agents.* arXiv:2207.01206, v1 2022-07-04. <https://arxiv.org/abs/2207.01206>
11. He, H. et al. — *WebVoyager: Building an End-to-End Web Agent with Large Multimodal Models.* arXiv:2401.13919, v1 2024-01-25. <https://arxiv.org/abs/2401.13919>
12. Gu, J. et al. — *A Survey on LLM-as-a-Judge.* arXiv:2411.15594, v1 2024-11-23. <https://arxiv.org/abs/2411.15594>
13. Yao, S., Shinn, N., Razavi, P., Narasimhan, K. — *τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains.* arXiv:2406.12045, v1 2024-06-17. <https://arxiv.org/abs/2406.12045>
14. Debenedetti, E. et al. — *AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents.* arXiv:2406.13352, v1 2024-06-19. <https://arxiv.org/abs/2406.13352>
15. Andriushchenko, M. et al. — *AgentHarm: A Benchmark for Measuring Harmfulness of LLM Agents.* arXiv:2410.09024, v1 2024-10-11. <https://arxiv.org/abs/2410.09024>
16. Zhang, Z. et al. — *Agent-SafetyBench: Evaluating the Safety of LLM Agents.* arXiv:2412.14470, v1 2024-12-19. <https://arxiv.org/abs/2412.14470>
17. Korgul, K. et al. — *It's a TRAP! Task-Redirecting Agent Persuasion Benchmark for Web Agents.* arXiv:2512.23128, v1 2025-12-29. <https://arxiv.org/abs/2512.23128>
18. Zhang, K. et al. — *BrowseSafe: Understanding and Preventing Prompt Injection Within AI Browser Agents.* arXiv:2511.20597, v1 2025-11-25. <https://arxiv.org/abs/2511.20597>
19. Zhu, Y. et al. — *Establishing Best Practices for Building Rigorous Agentic Benchmarks.* arXiv:2507.02825, v1 2025-07-03. <https://arxiv.org/abs/2507.02825>
20. Gan, C., He, Z., Tsujii, Y., Kobayashi, K., Itoh, H., Funakoshi, K. — *Auditing Web Agent Evaluation on WebArena-Lite: Human Review of Outcomes and Trajectories.* arXiv:2610.01491, v1 2026-10-01. <https://arxiv.org/abs/2610.01491>
21. Vattikonda, D. et al. — *How to Train Your LLM Web Agent: A Statistical Diagnosis.* arXiv:2507.04103, v1 2025-07-05. <https://arxiv.org/abs/2507.04103>
22. Sodhi, P. et al. — *SteP: Stacked LLM Policies for Web Actions.* arXiv:2310.03720, v1 2023-10-05. <https://arxiv.org/abs/2310.03720>

---

## 12. Related documents

- [`evaluation.md`](evaluation.md) — Chimera's evaluation criteria, metrics,
  baselines, reporting format and limitations.
- [`benchmark_design.md`](benchmark_design.md) — the proposed initial
  benchmark: scenarios, protocol, result schema, example report.
- [`threat_model.md`](threat_model.md) — the safety threats the benchmark
  must measure (R-2, R-5, R-9 in §5).
- [`adr/ADR-004-requirement-traceability-to-srs.md`](adr/ADR-004-requirement-traceability-to-srs.md)
  — the six unresolved requirement-mapping questions, three of which bear
  directly on what the benchmark can measure.
