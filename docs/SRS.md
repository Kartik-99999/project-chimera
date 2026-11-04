> **Provenance note (added 2026-11-04, not part of the original text):** this is the
> project requirements specification, copied verbatim from the author's original file
> dated **2026-10-17** (before the hackathon start). It is the document cited as
> "SRS §…" throughout the repository. It describes the long-term vision; what is
> actually implemented is stated in [`../README.md`](../README.md).

# PROJECT CHIMERA
## Software Requirements Specification (SRS)

**Version:** 1.0  
**Status:** Proposed baseline  
**Project type:** AI agent / intelligent automation / developer tooling  
**Development approach:** Research-driven, test-first, iterative engineering  
**Primary environment:** macOS on Apple Silicon  
**Primary implementation languages:** Python and TypeScript

---

# 1. Executive Summary

Project Chimera is an adaptive software operator that learns how to perform browser-based tasks from demonstrations, converts those demonstrations into reusable workflows, executes those workflows autonomously within a controlled environment, detects unexpected application states, recovers from failures, and verifies the resulting application state.

Unlike a conventional macro recorder, Chimera must distinguish between the intended outcome of a task and the sequence of actions used to achieve it.

For example, a recorded workflow might click a button labelled "Create Project." If the application later changes that button's position, layout, or label, Chimera should attempt to understand the current state and identify an appropriate action rather than blindly replaying old coordinates.

The system must also establish whether the project was actually created. A successful click is not proof of success.

### 1.1 Core proposition

Chimera combines five capabilities:

1. Learning reusable procedures from demonstrations.
2. Executing procedures through browser automation.
3. Adapting to unfamiliar inputs and changed interface states.
4. Recovering from errors using bounded, safety-aware strategies.
5. Verifying task completion using observable evidence.

### 1.2 Primary objective

Build a demonstrably reliable AI agent that can learn, execute, adapt, and verify browser workflows, with measurable performance on previously unseen task variations.

### 1.3 Definition of success

The project is successful when an independent evaluator can:

- Demonstrate a task to Chimera.
- Ask Chimera to repeat that task with different input data.
- Introduce a controlled interface change or execution failure.
- Observe Chimera detect the unexpected state.
- Inspect the agent's recovery decision and supporting evidence.
- Verify that the final application state satisfies the task's requirements.
- Reproduce the experiment and inspect the resulting metrics.

A visually impressive interface is important, but it is not sufficient evidence of technical success.

---

# 2. Problem Statement

Traditional browser automation systems are often built around fixed selectors, recorded clicks, scripts, or manually configured workflows.

These approaches can be effective in stable environments but become brittle when interfaces, input data, or application behavior change.

General-purpose AI agents offer more flexibility, but they introduce other challenges:

- Unreliable action selection.
- Excessive or repetitive retries.
- Difficulty distinguishing a failed action from a successful action with delayed feedback.
- Hallucinated application state.
- Inconsistent behavior across repeated runs.
- Poor reproducibility.
- Insufficient evidence for claimed task completion.
- Risks associated with granting agents unrestricted access to software.

Chimera addresses these challenges through a hybrid architecture combining deterministic automation, model-assisted reasoning, explicit workflow representations, application-state observation, bounded recovery, and independent verification.

The project will investigate whether these mechanisms improve reliability compared with simple replay and model-only execution.

---

# 3. Goals and Non-Goals

## 3.1 Primary goals

**G1 — Demonstration-based learning**

Capture a user's browser interactions and transform those demonstrations into reusable workflow definitions.

**G2 — Generalization**

Execute learned workflows with different input values and controlled variations in the application interface.

**G3 — Adaptive execution**

Use the current application state to choose actions instead of depending exclusively on historical coordinates or selectors.

**G4 — Verified completion**

Determine task success using explicit postconditions and observable application state.

**G5 — Failure recovery**

Recognize failed actions, diagnose recoverable errors, select alternative actions, and stop safely when recovery is inappropriate.

**G6 — Explainability and observability**

Record what the agent observed, what it intended to do, what action it took, why recovery was triggered, and what evidence established the final result.

**G7 — Reproducible evaluation**

Provide an evaluation harness for measuring success, generalization, recovery, execution cost, and reliability across repeated experiments.

**G8 — Professional presentation**

Provide an interactive dashboard that makes the agent's execution and learning process understandable to technical and nontechnical reviewers.

## 3.2 Non-goals for the initial release

The following are explicitly outside the initial release:

- Unrestricted control of the user's everyday browser or operating system.
- Autonomous access to personal email, banking, financial accounts, or production systems.
- Training a foundation model from scratch.
- Claiming that workflows improve model weights through online training.
- Unrestricted autonomous purchasing, deletion, publishing, or account modification.
- Supporting every website and browser from the beginning.
- Building a general desktop computer-use agent before browser workflows are reliable.
- Claiming universal autonomy based on a few successful demonstrations.

These capabilities may be considered later, subject to separate technical and safety evaluations.

---

# 4. Users and Use Cases

## 4.1 Primary user

A developer or technical operator who wants to automate repetitive browser-based work without manually programming every workflow.

## 4.2 Secondary users

- Researchers evaluating browser agents.
- QA engineers testing interface changes.
- Hackathon judges evaluating an AI system's technical depth.
- Developers inspecting execution traces and failure reports.

## 4.3 Core use cases

### UC-01: Demonstrate a task

The user opens a supported test application, performs a task, and records the interaction.

Example: create a project, enter its name and description, and submit the form.

Expected result: Chimera stores the demonstration as an inspectable sequence of observations and actions.

### UC-02: Compile a reusable workflow

Chimera analyzes the demonstration and creates a workflow containing action definitions, variable inputs, preconditions, postconditions, and recovery rules.

Expected result: the user can inspect and edit the generated workflow before executing it.

### UC-03: Execute a learned workflow

The user supplies new input values and requests execution.

Expected result: Chimera performs the task and verifies the final state.

### UC-04: Adapt to interface changes

The test application changes a button label, DOM structure, or element location.

Expected result: Chimera detects that the original interaction is no longer valid, reassesses the page, and chooses an allowed alternative when confidence and evidence justify doing so.

### UC-05: Recover from a failure

The application returns a validation error, times out, or fails to respond as expected.

Expected result: Chimera classifies the failure, selects an appropriate recovery strategy, and avoids repeating unsafe actions.

### UC-06: Verify task completion

The agent reaches what appears to be the final step.

Expected result: the verifier checks the actual application state against the workflow's postconditions before reporting success.

### UC-07: Inspect execution

The user opens a run and examines its timeline, screenshots, actions, errors, recovery decisions, and verification evidence.

Expected result: every consequential decision is traceable to recorded evidence or explicitly marked as a model-generated hypothesis.

### UC-08: Evaluate an agent version

The user runs a collection of tasks against a specific version of Chimera.

Expected result: the evaluation system produces comparable metrics and a report of successes, failures, regressions, and resource consumption.

---

# 5. Functional Requirements

Priority definitions:

- **P0:** Required for a credible first complete release.
- **P1:** Required for the high-quality research-oriented release.
- **P2:** Optional advanced capability.

## 5.1 Demonstration capture

**FR-001 — Start and stop recording (P0)**

The user must be able to start, pause, resume, and stop a recording session.

**FR-002 — Capture browser actions (P0)**

The system must capture supported interactions, including:

- Clicks.
- Text input.
- Form submission.
- Selection changes.
- Navigation.
- Relevant keyboard actions.
- Changes in observable application state.

**FR-003 — Capture semantic context (P0)**

Where available, recorded actions must include accessible names, roles, labels, locator information, URL, relevant DOM context, and the intended interaction.

**FR-004 — Avoid coordinate-only workflows (P0)**

The system must prefer semantic locators and DOM-backed interactions over fixed screen coordinates.

Coordinate-based actions must be treated as a fallback and must include additional checks.

**FR-005 — Store demonstration metadata (P0)**

Each demonstration must record its identifier, timestamps, initial state, ordered actions, observations, and completion status.

**FR-006 — Review recorded demonstrations (P0)**

The user must be able to inspect, replay, and discard a demonstration before turning it into a reusable workflow.

## 5.2 Workflow learning and compilation

**FR-007 — Generate workflow definitions (P0)**

Chimera must transform a demonstration into a structured workflow representation.

**FR-008 — Parameterize input values (P0)**

The system must identify candidate variable values, such as project names, descriptions, categories, and dates.

A user must be able to replace recorded values with named parameters.

**FR-009 — Define preconditions (P0)**

Every workflow must describe the initial conditions required for execution, including the relevant page or application state.

**FR-010 — Define postconditions (P0)**

Every workflow must specify observable conditions that must hold after completion.

Example: a project with the requested name exists in the project's list.

**FR-011 — Represent conditional steps (P1)**

Workflows must support branching based on observed conditions.

Example: if a confirmation dialog appears, handle it; otherwise, continue to the next verification step.

**FR-012 — Validate generated workflows (P0)**

The workflow compiler must reject invalid structures, missing required fields, unsupported actions, and malformed conditions.

**FR-013 — Version workflows (P1)**

Changes to a workflow must create versioned records so previous behavior can be reproduced.

**FR-014 — Human review (P0)**

Users must be able to inspect and approve a workflow before its first autonomous execution.

## 5.3 Planning and execution

**FR-015 — Interpret task requests (P0)**

The agent must convert a user request into a structured task objective and required inputs.

**FR-016 — Select a suitable workflow (P0)**

The system must identify whether an existing workflow can perform the requested task.

If no suitable workflow exists, it must request a demonstration or use an explicitly authorized planning mode.

**FR-017 — Observe before acting (P0)**

The execution engine must inspect the current state before performing consequential actions.

**FR-018 — Use deterministic browser primitives (P0)**

Playwright must execute approved browser operations using validated locators and bounded timeouts.

**FR-019 — Enforce action constraints (P0)**

Every proposed action must be checked against the workflow definition, action schema, execution policy, and current authorization.

**FR-020 — Detect stale assumptions (P0)**

The agent must recognize when a locator fails, a page changes unexpectedly, a modal appears, or the observed state contradicts the expected state.

**FR-021 — Support cancellation (P0)**

The user must be able to stop an active run. The system must stop scheduling further actions and handle browser cleanup safely.

**FR-022 — Limit execution resources (P0)**

Each run must have configurable limits on duration, number of actions, retries, and model calls.

## 5.4 Adaptive recovery

**FR-023 — Classify failures (P0)**

The system must classify common errors, including:

- Locator not found.
- Element not actionable.
- Navigation timeout.
- Unexpected page state.
- Form validation failure.
- Permission denial.
- Network or service failure.
- Ambiguous execution result.
- Verification failure.

**FR-024 — Diagnose failure context (P0)**

The recovery system must collect relevant evidence before asking a model to suggest an alternative.

**FR-025 — Generate alternative actions (P1)**

When a failure is recoverable, the planner may propose alternative locators or action sequences based on the current page state.

**FR-026 — Validate recovery proposals (P0)**

A proposed recovery must pass policy, schema, target-element, and risk checks before execution.

**FR-027 — Bound recovery attempts (P0)**

Recovery must have a configurable maximum number of attempts. Exhausting the limit must produce a clear failure report.

**FR-028 — Prevent blind retries (P0)**

The system must not repeat an action merely because a response was delayed.

Before retrying, it must check whether the intended effect already occurred.

**FR-029 — Preserve recovery history (P0)**

Every recovery attempt must record the original error, relevant observations, proposed alternative, decision, outcome, and verification result.

**FR-030 — Escalate unresolved failures (P0)**

When confidence is insufficient or an action is unsafe, Chimera must stop and request human intervention.

## 5.5 Independent verification

**FR-031 — Verify final state (P0)**

The verifier must assess task completion independently of the model's claim that it succeeded.

**FR-032 — Support multiple evidence types (P0)**

Evidence may include:

- DOM state.
- Accessible element properties.
- Visible confirmation messages.
- Application records.
- Read-only API responses in the controlled test environment.
- Relevant screenshots.
- Expected navigation or state transitions.

**FR-033 — Evaluate postconditions (P0)**

Each required postcondition must receive an explicit pass, fail, or inconclusive result.

**FR-034 — Prevent unsupported success claims (P0)**

If the required evidence is missing or contradictory, the run must not be marked successful.

**FR-035 — Detect ambiguous outcomes (P0)**

The system must distinguish a confirmed failure from an uncertain result, such as a form submission that may have succeeded despite a timeout.

**FR-036 — Produce a verification report (P0)**

The report must include the requested outcome, each postcondition, evidence references, final status, and unresolved uncertainties.

## 5.6 Memory and improvement

**FR-037 — Persist reusable workflows (P0)**

Approved workflows must remain available across application restarts.

**FR-038 — Store execution history (P0)**

The system must retain configurable run metadata, traces, and verification outcomes.

**FR-039 — Learn from failures (P1)**

The system may propose workflow improvements based on repeated failure patterns and verified recovery results.

**FR-040 — Require validation before promotion (P0)**

A modified workflow must pass relevant regression tests before becoming the active version.

**FR-041 — Separate evidence from inference (P0)**

Stored information must distinguish observed facts, model-generated hypotheses, user instructions, and verified conclusions.

**FR-042 — Support rollback (P1)**

Users must be able to restore a previously approved workflow version.

## 5.7 Dashboard and observability

**FR-043 — Overview dashboard (P0)**

Display recent runs, completion rates, failed runs, active executions, and evaluation summaries.

**FR-044 — Live execution timeline (P0)**

Display action progress, observation updates, errors, recovery attempts, and verification outcomes.

**FR-045 — Workflow graph (P1)**

Display workflow steps, branches, dependencies, and execution status.

**FR-046 — Evidence inspector (P0)**

Allow users to inspect screenshots, relevant DOM evidence, action arguments, and verification results.

**FR-047 — Run comparison (P1)**

Compare two runs of the same workflow to identify differences in execution path, errors, duration, and outcome.

**FR-048 — Evaluation reports (P0)**

Display benchmark results with denominators, task definitions, failure categories, and agent version information.

**FR-049 — Export results (P1)**

Allow users to export workflow definitions and machine-readable execution reports.

---

# 6. Non-Functional Requirements

## 6.1 Reliability

**NFR-001:** Every run must terminate in an explicit state: succeeded, failed, cancelled, or inconclusive.

**NFR-002:** Unhandled exceptions must not silently produce a successful result.

**NFR-003:** Retries must be bounded and recorded.

**NFR-004:** State-changing actions must be checked for possible duplicate effects before being repeated.

**NFR-005:** The system must preserve enough execution metadata to investigate failures after a run ends.

## 6.2 Performance

**NFR-006:** The dashboard should remain responsive during browser execution.

**NFR-007:** Local, deterministic actions should not require an LLM call when the required information is already available.

**NFR-008:** Model calls must have configurable timeouts and error handling.

**NFR-009:** Long-running tasks must report progress without blocking the user interface.

**NFR-010:** The application must record model latency, browser execution time, and total task duration separately.

No absolute end-to-end latency guarantee is required until a representative benchmark has been established.

## 6.3 Security

**NFR-011:** The default execution target must be a controlled test application.

**NFR-012:** Browser sessions must be isolated between test runs where practical.

**NFR-013:** Secrets must not be committed to source control or written into ordinary logs.

**NFR-014:** Browser content must be treated as untrusted input, not as an authoritative source of instructions.

**NFR-015:** The system must defend against prompt injection in page content.

**NFR-016:** The action executor must enforce an allowlist of permitted operations and targets.

**NFR-017:** Destructive or consequential actions must require explicit authorization.

**NFR-018:** The system must not automatically bypass authentication, access controls, CAPTCHAs, or other security mechanisms.

**NFR-019:** Screenshots and traces must avoid capturing unnecessary credentials or personal data.

**NFR-020:** The test environment must be resettable so failed experiments do not damage unrelated data.

## 6.4 Maintainability

**NFR-021:** Browser execution, workflow compilation, planning, verification, model access, and the user interface must be separate modules.

**NFR-022:** Model providers must be replaceable through a documented adapter interface.

**NFR-023:** Core workflow validation must not depend on a particular LLM provider.

**NFR-024:** All critical modules must have automated tests.

**NFR-025:** Configuration must be environment-based and documented.

**NFR-026:** The repository must include setup instructions, architecture documentation, troubleshooting guidance, and reproducible evaluation commands.

## 6.5 Portability

**NFR-027:** The project must support local development on macOS with Apple Silicon.

**NFR-028:** The application must not require a Claude subscription.

**NFR-029:** Model API access must be optional at the architectural level, although an LLM-backed execution mode requires a compatible model endpoint.

**NFR-030:** Core deterministic workflows and evaluation tests must run without a paid model API.

---

# 7. Proposed Technical Architecture

## 7.1 Frontend

**Technology:** React, TypeScript, Vite.

Responsibilities:

- Dashboard and run history.
- Workflow editor and graph.
- Live execution timeline.
- Evidence inspection.
- Verification reports.
- Benchmark comparisons.
- Human approval and cancellation controls.

A graph library may be selected after the first functional dashboard is established.

## 7.2 Backend

**Technology:** Python, FastAPI, Pydantic.

Responsibilities:

- Task and run management.
- Workflow storage and validation.
- Execution orchestration.
- Model adapter interfaces.
- Recovery policy.
- Verification engine.
- Audit events.
- Evaluation API.

Long-running executions should run in managed background tasks rather than blocking HTTP request handlers.

## 7.3 Browser execution

**Technology:** Playwright with Chromium.

Responsibilities:

- Launch isolated browser contexts.
- Record demonstrations.
- Observe the DOM and accessible state.
- Execute validated actions.
- Capture relevant screenshots and traces.
- Detect navigation and interaction failures.
- Expose browser observations to the planner.

## 7.4 Model adapter

The application must define a provider-independent interface for model requests.

Expected capabilities:

- Structured output generation.
- Task interpretation.
- Workflow compilation suggestions.
- Recovery proposals.
- Explanation generation.

Provider-specific capabilities must be detected rather than assumed.

Gemini chat can be used as a development assistant. It is not automatically a programmatic runtime endpoint. To run Chimera autonomously, configure an accessible model API or a compatible local model runtime.

## 7.5 Storage

**Initial technology:** SQLite.

Store:

- Workflows and versions.
- Demonstrations.
- Execution runs.
- Action events.
- Verification results.
- Evaluation experiments.
- Model and configuration metadata.

Store large screenshots and browser traces as filesystem artifacts, with database references and configurable retention.

## 7.6 Evaluation environment

Create a local web application containing representative workflows:

- Create and edit a project.
- Search and filter records.
- Complete a form with validation.
- Navigate multi-step forms.
- Recover from a stale or changed element.
- Handle delayed UI updates.
- Recognize duplicate submission risk.
- Stop safely when permissions are insufficient.

The environment must support controlled faults and repeatable initial states.

---

# 8. Core Data Model

## 8.1 Workflow

Fields:

- workflow_id
- name
- description
- version
- input_schema
- preconditions
- steps
- postconditions
- allowed_actions
- recovery_policy
- approval_status
- created_at
- updated_at

## 8.2 Workflow step

Fields:

- step_id
- step_type
- objective
- action_definition
- locator_strategy
- input_references
- preconditions
- expected_state_change
- postconditions
- timeout
- retry_policy

## 8.3 Execution run

Fields:

- run_id
- workflow_id
- workflow_version
- input_values
- agent_version
- model_provider
- model_identifier
- started_at
- completed_at
- status
- final_verification
- failure_category
- resource_metrics

## 8.4 Execution event

Fields:

- event_id
- run_id
- sequence_number
- event_type
- timestamp
- observed_state_reference
- action_proposal
- executed_action
- outcome
- error_details
- recovery_attempt
- evidence_references

## 8.5 Verification result

Fields:

- verification_id
- run_id
- postcondition_id
- status
- evidence_type
- evidence_reference
- evaluator
- explanation
- timestamp

The evaluator must distinguish deterministic checks from model-assisted judgments.

## 8.6 Evaluation experiment

Fields:

- experiment_id
- dataset_version
- agent_version
- workflow_version
- model_configuration
- scenario_ids
- run_count
- success_count
- recovery_count
- false_success_count
- duration_statistics
- cost_statistics
- failure_distribution

---

# 9. Execution State Machine

Each run must follow an explicit state machine.

1. **CREATED:** A task has been submitted.
2. **VALIDATING:** Inputs, workflow, and permissions are checked.
3. **OBSERVING:** The current browser state is collected.
4. **PLANNING:** The next permitted action is selected.
5. **EXECUTING:** The action is performed.
6. **CHECKING:** The expected state change is inspected.
7. **RECOVERING:** A bounded recovery strategy is being evaluated or executed.
8. **VERIFYING:** Final postconditions are evaluated.
9. **SUCCEEDED:** All mandatory postconditions are verified.
10. **FAILED:** The task cannot continue or a required condition failed.
11. **INCONCLUSIVE:** Evidence is insufficient to establish success or failure.
12. **CANCELLED:** The user or execution policy stopped the run.

State transitions must be validated by code.

The language model may propose actions, but it must not directly assign the run's terminal status.

---

# 10. Workflow Representation

Workflows should use a validated, versioned JSON representation rather than storing only a transcript of natural-language instructions.

A simplified example:

```json
{
  "workflow_id": "create-project",
  "version": 1,
  "name": "Create Project",
  "inputs": {
    "project_name": {
      "type": "string",
      "required": true
    }
  },
  "preconditions": [
    {
      "type": "page_origin",
      "value": "http://127.0.0.1"
    }
  ],
  "steps": [
    {
      "id": "fill-name",
      "action": "fill",
      "target": {
        "role": "textbox",
        "name": "Project name"
      },
      "value_from": "project_name"
    },
    {
      "id": "submit",
      "action": "click",
      "target": {
        "role": "button",
        "name": "Create Project"
      }
    }
  ],
  "postconditions": [
    {
      "id": "project-exists",
      "type": "record_exists",
      "field": "name",
      "value_from": "project_name"
    }
  ]
}
```

This is an illustrative schema, not the final implementation contract.

The production schema must define allowed action types, JSON validation, target restrictions, condition syntax, timeouts, retry rules, and verification semantics. Application-specific checks must be implemented against the controlled test environment.

---

# 11. Evaluation and Acceptance Criteria

A high-quality project must be evaluated empirically rather than judged solely on its demonstration.

The following targets are proposed initial release gates, not established performance claims.

## 11.1 Functional acceptance

- At least five representative workflows can be demonstrated, stored, and executed.
- Each workflow has explicit preconditions and postconditions.
- Inputs can be changed without rewriting the entire workflow.
- A controlled interface change triggers detection and either successful recovery or a safe failure.
- Failed verification cannot result in a successful terminal status.
- Runs can be inspected and reproduced.
- The user can cancel an execution.
- Critical actions and recovery decisions are recorded.

## 11.2 Proposed benchmark targets

**Initial benchmark:** At least 100 task episodes across a versioned collection of ordinary, changed-interface, and injected-failure scenarios. Increase the dataset as the system matures.

| Metric | Initial target |
|---|---:|
| Success on baseline workflows | ≥95% |
| Success on supported interface variations | ≥80% |
| Recovery success on designated recoverable failures | ≥70% |
| False-success rate | 0% on the release acceptance suite |
| Unauthorized destructive actions | 0 |
| Reproducible terminal status | 100% of completed test episodes |
| Critical regression tests passing | 100% |

These are engineering targets. They must be reported with sample sizes and scenario definitions. A result from a small, curated test set must not be presented as proof of general reliability.

## 11.3 Comparative evaluation

Compare at least three approaches:

**Baseline A — Deterministic replay**

Execute the recorded steps with fixed locators and no adaptive reasoning.

**Baseline B — Model-assisted execution**

Use a model to interpret the task and choose actions without a learned reusable workflow.

**Chimera — Learned workflow plus adaptive recovery and verification**

Use structured workflows, state observation, constrained recovery, and independent postcondition checks.

Evaluate each approach on the same scenarios, using comparable execution limits.

Measure:

- Task success rate.
- Generalization success.
- Recovery success.
- False-success rate.
- Actions per successful task.
- Median and percentile execution duration.
- Model calls and estimated model cost.
- Human intervention frequency.
- Failure categories.

The comparison should establish which improvements come from workflow learning, which come from recovery, and which come from verification.

---

# 12. Testing Strategy

## 12.1 Unit tests

Test:

- Workflow schema validation.
- State-machine transitions.
- Input parameter substitution.
- Locator construction.
- Action policy enforcement.
- Retry limits.
- Postcondition evaluation.
- Terminal-state assignment.
- Model response validation.

## 12.2 Integration tests

Test:

- Backend-to-browser execution.
- Browser-to-verifier state inspection.
- Database persistence.
- Model adapter failures.
- Timeout handling.
- Run cancellation.
- Artifact generation.
- Dashboard event updates.

## 12.3 End-to-end tests

Test complete user journeys:

- Record, compile, approve, execute, verify.
- Execute with new inputs.
- Recover from a changed interface.
- Handle a validation failure.
- Detect an already-completed action.
- Stop on a forbidden operation.
- Produce an inconclusive result when evidence is unavailable.

## 12.4 Adversarial tests

Test:

- Prompt-injection text embedded in page content.
- Unexpected redirects.
- Malformed model responses.
- Ambiguous button labels.
- Duplicate records.
- Delayed confirmations.
- Stale browser state.
- Missing permissions.
- Model timeouts and unavailable providers.

The system must fail safely when it cannot establish a permitted, valid next action.

---

# 13. User Interface Requirements

The interface should communicate the state of the agent, not merely decorate the automation.

## 13.1 Overview

Show:

- Recent executions.
- Success and failure counts.
- Recovery statistics.
- Evaluation trends.
- Active runs.
- Recent regressions.

## 13.2 Workflow studio

Provide:

- A visual representation of steps and branches.
- Editable input parameters.
- Preconditions and postconditions.
- Workflow versions.
- Approval status.
- Validation errors.

## 13.3 Live execution view

Provide:

- Current browser state or screenshot.
- Current step and execution status.
- Recent action history.
- Expected versus observed state changes.
- Recovery decisions.
- Verification progress.
- Cancellation controls.

## 13.4 Evidence and run inspector

Provide:

- Ordered event timeline.
- Action arguments.
- Relevant screenshots.
- Locator information.
- Error details.
- Verification evidence.
- Model latency and resource usage.
- Final outcome and unresolved uncertainties.

## 13.5 Evaluation studio

Provide:

- Dataset and agent-version selection.
- Repeatable benchmark execution.
- Baseline comparison.
- Failure-category breakdown.
- Metrics with denominators.
- Exportable experiment reports.

The visual style should be consistent and restrained. Real evidence and readable execution traces should take precedence over decorative animation.

---

# 14. Technology Decisions

## Required initial stack

- **Language:** Python for the backend and agent.
- **Backend:** FastAPI and Pydantic.
- **Browser:** Playwright with Chromium.
- **Frontend:** React, TypeScript, and Vite.
- **Storage:** SQLite initially.
- **Model integration:** A provider-independent adapter.
- **Local model option:** Ollama with a compatible tool-capable model.
- **Testing:** pytest and Playwright tests.
- **Version control:** Git and GitHub.
- **Development environment:** Antigravity, with Codex as an implementation and review assistant where available.
- **Optional visualization:** A graph library for workflow nodes and execution states.

## Model-access constraint

The project must not depend on a Claude subscription.

Gemini chat can be used as a development assistant. It is not automatically a programmatic runtime endpoint. To run Chimera autonomously, configure an accessible model API or a compatible local model runtime.

Before choosing the runtime model, verify the exact model identifier, API availability, quotas, pricing, structured-output support, and tool-calling behavior.

Keep the runtime model configurable so the system can use a compatible local model or an authorized hosted API.

## Infrastructure principle

Start with a modular monolith rather than microservices. Introduce additional infrastructure only when measurements show that the simpler architecture is insufficient.

---

# 15. Development Roadmap

The project has no fixed deadline. Each phase must satisfy its exit criteria before the next phase becomes the primary focus.

## Phase 0 — Research and specification

Deliverables:

- Reviewed requirements.
- Architecture decision records.
- Survey of browser-agent evaluation approaches.
- Threat model.
- Initial benchmark design.
- Repository and development setup.

Exit criterion: the core architecture, scope, evaluation criteria, and safety boundaries are documented.

## Phase 1 — Controlled test environment

Build a local application with deterministic workflows, test data, fault injection, and reset functionality.

Exit criterion: baseline tasks and injected failures can be reproduced reliably.

## Phase 2 — Browser execution engine

Implement Playwright execution, semantic locators, state observation, action validation, event recording, and cancellation.

Exit criterion: deterministic workflows execute and produce inspectable traces.

## Phase 3 — Independent verification

Implement preconditions, postconditions, evidence references, explicit terminal states, and inconclusive outcomes.

Exit criterion: the system never reports success when a mandatory postcondition fails or remains unverified in the acceptance suite.

## Phase 4 — Demonstration capture and workflow compilation

Implement recording, action normalization, parameterization, schema validation, workflow review, and versioning.

Exit criterion: a demonstrated workflow can be reused with new input values.

## Phase 5 — Adaptive planning and recovery

Add model-assisted action selection, interface-change detection, bounded recovery, failure classification, and safe escalation.

Exit criterion: Chimera can recover from defined interface changes while stopping safely on unsupported or unsafe situations.

## Phase 6 — Evaluation framework

Build a repeatable benchmark, baselines, metric calculation, experiment records, and regression tests.

Exit criterion: results are reproducible and the contribution of each major subsystem can be measured.

## Phase 7 — Professional dashboard

Build the workflow studio, live execution timeline, evidence inspector, and evaluation studio.

Exit criterion: a new user can understand a run and inspect its evidence without reading raw application logs.

## Phase 8 — Hardening and release

Complete adversarial testing, documentation, dependency review, clean-install validation, and a recorded demonstration.

Exit criterion: a fresh environment can reproduce the documented setup and evaluation procedure.

---

# 16. Repository Structure

A proposed initial layout:

```text
chimera/
├── apps/
│   ├── api/
│   └── web/
├── services/
│   ├── agent/
│   ├── browser/
│   ├── workflow_compiler/
│   ├── verifier/
│   ├── recovery/
│   ├── model_adapters/
│   └── evaluation/
├── packages/
│   ├── schemas/
│   └── shared_types/
├── testbed/
│   ├── web_app/
│   ├── scenarios/
│   ├── fault_injection/
│   └── fixtures/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── adversarial/
├── data/
│   └── .gitkeep
├── artifacts/
│   └── .gitkeep
├── docs/
│   ├── architecture.md
│   ├── threat_model.md
│   ├── evaluation.md
│   ├── adr/
│   └── user_guide.md
├── scripts/
├── .env.example
├── .gitignore
├── pyproject.toml
├── package.json
└── README.md
```

The exact package structure may change as implementation begins, but module responsibilities must remain explicit.

---

# 17. Required Project Deliverables

The final project must include:

1. A working browser-agent application.
2. A controlled demonstration website.
3. A demonstration recorder.
4. A validated workflow representation and compiler.
5. A reusable workflow execution engine.
6. A bounded recovery subsystem.
7. An independent verification engine.
8. Persistent workflow and execution history.
9. An interactive dashboard.
10. A reproducible benchmark and baseline implementations.
11. Automated unit, integration, end-to-end, and adversarial tests.
12. Architecture and security documentation.
13. Setup instructions and environment configuration.
14. A technical report documenting methodology, results, limitations, and failure cases.
15. A polished end-to-end demonstration showing learning, adaptation, recovery, and evidence-backed verification.

---

# 18. Release Acceptance Checklist

The project must not be considered complete until the following are satisfied:

- [ ] A fresh installation can run the application using the documented setup.
- [ ] A user can record and review a browser demonstration.
- [ ] A demonstration can be converted into a valid, reusable workflow.
- [ ] A workflow can execute with new parameter values.
- [ ] The agent can detect defined interface changes.
- [ ] Recovery attempts are constrained and auditable.
- [ ] The system detects ambiguous outcomes and avoids blind duplicate actions.
- [ ] Mandatory postconditions are checked independently of model claims.
- [ ] Failed or inconclusive runs cannot be presented as verified successes.
- [ ] Workflow versions and execution evidence are retained.
- [ ] The evaluation suite compares Chimera with appropriate baselines.
- [ ] Benchmark results are reproducible and reported honestly.
- [ ] Security and adversarial tests pass.
- [ ] The dashboard exposes execution evidence and failure details.
- [ ] Documentation includes known limitations and unsupported scenarios.

---

# 19. Research Contribution and Positioning

Chimera should not claim that browser automation, demonstration learning, agent memory, or recovery are individually new.

Its potential contribution is a rigorously evaluated combination of:

- Reusable workflow compilation from demonstrations.
- State-aware execution under controlled interface changes.
- Evidence-gated recovery and completion.
- Versioned learning from verified execution outcomes.
- Reproducible comparisons against simpler automation strategies.

The research question is:

**Does combining demonstration-derived workflows, constrained adaptive recovery, and independent verification improve the reliability and generalization of browser automation compared with deterministic replay and model-only execution?**

The answer must come from experimental results, not from the project's name, interface, or marketing.

---

# 20. Final Definition of Done

Project Chimera is complete when it is a working, documented, tested, and reproducibly evaluated software system—not merely a visual prototype.

A reviewer must be able to inspect its architecture, run its benchmark, observe an adaptive recovery scenario, examine the evidence for the final result, and identify the cases in which the system deliberately refuses to claim success.

The project should demonstrate three qualities simultaneously:

**Engineering quality:** modular architecture, automated testing, secure execution, and maintainable code.

**AI quality:** useful generalization, controlled planning, evidence-based recovery, and honest uncertainty.

**Product quality:** a polished interface that makes the agent's internal decisions and externally observable results understandable.

The final standard is not that Chimera never fails. It is that its failures are detectable, its recovery is controlled, its successes are verified, and its performance can be independently measured.
