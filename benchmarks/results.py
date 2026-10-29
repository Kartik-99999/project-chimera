"""Benchmark result schema and serialisation.

Stage 1 of the Chimera benchmark harness. This module defines the
*contract* for a benchmark result: what an episode's outcome was, what
evidence supports it, and — for every metric that could not be
measured — **why**.

Authority
---------
``docs/benchmark_design.md`` §5 (independent verification and the
false-success mechanism), §7 (trial protocol), §8 (metrics, including
the "measurable now" and "measurable only after future work" split),
and §9 (the result schema).

Two rules from the design shape this module:

**A missing metric is not a zero.** §8.3 requires metrics that are
blocked on future components to be reported as ``null`` with a reason,
"**never** as ``0``". :class:`Metric` makes that structural: a metric
is either *measured* (with a value, possibly ``0``) or *unavailable*
(with a reason). There is no way to express "we did not measure this"
as ``0``.

**The agent's own report is not evidence.** §5 requires the
agent-reported outcome to be read from the persisted trace artifact's
``terminal_status``, not from a return value in the same process. The
episode record therefore carries both ``agent_terminal_status`` (what
the agent said) and a separate :class:`VerificationEvidence` (what an
independent component observed), so the false-success set is
computable without either one standing in for the other.

Open ambiguities raised by this module are recorded in
``docs/benchmark_design.md`` §15.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

#: Schema version emitted by this module.
RESULT_SCHEMA_VERSION = 1

#: Supported result schema versions.
SUPPORTED_RESULT_SCHEMA_VERSIONS: Tuple[int, ...] = (1,)

#: The value of ``RunResult.status`` for a design illustration.
STATUS_PROPOSED = "proposed"

#: The value of ``RunResult.status`` for an actual run.
STATUS_MEASURED = "measured"


class ResultValidationError(ValueError):
    """Raised when a result document is internally inconsistent."""

    def __init__(self, issues: Sequence[str]) -> None:
        self.issues: Tuple[str, ...] = tuple(issues)
        super().__init__(f"invalid benchmark result ({len(self.issues)} issue(s)): " + "; ".join(self.issues))


class EpisodeOutcome(str, Enum):
    """The terminal outcome of one episode.

    ``INCONCLUSIVE`` is representable but **not currently observable**:
    a verification timeout is reported by the agent as ``failed``, so
    the category has no denominator (design §8.3, ADR-004 Q4). It is
    in the schema so that a run does not have to be re-modelled when
    the state exists — not because it can be measured today.
    """

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INCONCLUSIVE = "inconclusive"


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Metric:
    """A measured value, or an explicit statement that it is unavailable.

    The two states are discriminated by the **value** of
    ``unavailable_reason``, never by whether a key is present:

    * ``unavailable_reason`` is ``None`` — the metric was **measured**.
      ``value`` is whatever was observed, and may be ``0``, or even
      ``None`` when the measurement itself is null.
    * ``unavailable_reason`` is a non-empty string — the metric was
      **not** measurable, and this says why. ``value`` must be ``None``.

    The serialised form always carries both keys, so the discriminator
    has to read the reason's value. A missing metric is therefore never
    a zero and never a bare null: the null of an unavailable metric
    always travels with its reason, and a null ``value`` on its own
    means "measured, and the measurement is null".
    """

    value: Any = None
    unavailable_reason: Optional[str] = None

    def __post_init__(self) -> None:
        if self.unavailable_reason is not None:
            if not self.unavailable_reason.strip():
                raise ResultValidationError(["unavailable_reason must be a non-empty string"])
            if self.value is not None:
                raise ResultValidationError(
                    ["an unavailable metric must not also carry a value"]
                )

    @classmethod
    def measured(cls, value: Any = None) -> "Metric":
        """A metric that was observed, with a value (possibly ``0`` or ``None``)."""
        return cls(value=value, unavailable_reason=None)

    @classmethod
    def unavailable(cls, reason: str) -> "Metric":
        """A metric that could not be observed, and why."""
        return cls(value=None, unavailable_reason=reason)

    @property
    def is_available(self) -> bool:
        """Whether the metric was measured.

        Driven by the reason, not by the value: a measured metric whose
        value happens to be ``None`` was still measured.
        """
        return self.unavailable_reason is None

    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value, "unavailable_reason": self.unavailable_reason}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Metric":
        # The discriminator is the reason's value. The serialised form
        # always contains both keys, so key presence says nothing.
        reason = data.get("unavailable_reason")
        if reason is not None:
            return cls.unavailable(reason)
        if "value" not in data:
            raise ResultValidationError(
                ["metric must carry either a 'value' or a non-null 'unavailable_reason'"]
            )
        return cls.measured(data["value"])


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PostconditionCheck:
    """The independent verifier's verdict on one postcondition."""

    postcondition_id: str
    satisfied: bool
    evidence_reference: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "postcondition_id": self.postcondition_id,
            "satisfied": self.satisfied,
            "evidence_reference": self.evidence_reference,
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PostconditionCheck":
        return cls(
            postcondition_id=data["postcondition_id"],
            satisfied=bool(data["satisfied"]),
            evidence_reference=data.get("evidence_reference", ""),
            detail=data.get("detail", ""),
        )


@dataclass(frozen=True)
class VerifierAudit:
    """The human-audited sample of the verifier's own decisions.

    ``docs/benchmark_design.md`` §5: the verifier is fallible, so a
    human adjudicates a random sample and the agreement rate is
    reported. Below 95% agreement the run's rates are *provisional*.
    """

    sampled: int
    agreed: int
    agreement_rate: Optional[float] = None
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sampled": self.sampled,
            "agreed": self.agreed,
            "agreement_rate": self.agreement_rate,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "VerifierAudit":
        return cls(
            sampled=int(data["sampled"]),
            agreed=int(data["agreed"]),
            agreement_rate=data.get("agreement_rate"),
            note=data.get("note", ""),
        )


@dataclass(frozen=True)
class VerificationEvidence:
    """What an independent component observed about the final page state.

    ``status`` is ``verified`` when the verifier ran, or ``unavailable``
    with a reason when it did not — which is the case today, because
    the verifier is a later stage. ``all_satisfied`` is the conjunction
    of the checks, and is what the false-success formula consumes
    (design §5).
    """

    status: str
    all_satisfied: Optional[bool] = None
    checks: Tuple[PostconditionCheck, ...] = ()
    verifier_version: str = ""
    audit: Optional[VerifierAudit] = None
    unavailable_reason: Optional[str] = None

    VERIFIED = "verified"
    UNAVAILABLE = "unavailable"

    def __post_init__(self) -> None:
        issues: List[str] = []
        if self.status not in (self.VERIFIED, self.UNAVAILABLE):
            issues.append(
                f"verification status {self.status!r} must be "
                f"{self.VERIFIED!r} or {self.UNAVAILABLE!r}"
            )
        if self.status == self.VERIFIED:
            if self.all_satisfied is None:
                issues.append("verified evidence requires all_satisfied")
            if self.unavailable_reason is not None:
                issues.append("verified evidence must not carry an unavailable_reason")
        else:
            if not (self.unavailable_reason or "").strip():
                issues.append("unavailable evidence requires a non-empty unavailable_reason")
            if self.all_satisfied is not None:
                issues.append("unavailable evidence must not carry all_satisfied")
        if issues:
            raise ResultValidationError(issues)

    @classmethod
    def not_yet_verified(cls, reason: str) -> "VerificationEvidence":
        """Evidence that does not exist yet, and why."""
        return cls(status=cls.UNAVAILABLE, unavailable_reason=reason)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "all_satisfied": self.all_satisfied,
            "checks": [c.to_dict() for c in self.checks],
            "verifier_version": self.verifier_version,
            "audit": self.audit.to_dict() if self.audit else None,
            "unavailable_reason": self.unavailable_reason,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "VerificationEvidence":
        audit = data.get("audit")
        return cls(
            status=data["status"],
            all_satisfied=data.get("all_satisfied"),
            checks=tuple(PostconditionCheck.from_dict(c) for c in data.get("checks", ())),
            verifier_version=data.get("verifier_version", ""),
            audit=VerifierAudit.from_dict(audit) if audit else None,
            unavailable_reason=data.get("unavailable_reason"),
        )


# ---------------------------------------------------------------------------
# Episode
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EpisodeResult:
    """One trial of one cell.

    ``trial_id`` identifies the trial within the run; ``run_id`` is the
    agent's own run identifier, which is also the stem of the trace
    artifact filename. Both are kept so a result can be joined back to
    the trace that produced it.
    """

    trial_id: str
    run_id: str
    scenario_id: str
    input_id: str
    baseline: str
    manifest_id: str
    manifest_version: str
    manifest_schema_version: int
    outcome: EpisodeOutcome
    agent_terminal_status: str
    started_at: str
    completed_at: str
    duration_ms: int
    trace_artifact: Optional[str] = None
    verification: VerificationEvidence = field(
        default_factory=lambda: VerificationEvidence.not_yet_verified("not recorded")
    )
    safety_violations: Metric = field(default_factory=lambda: Metric.unavailable("not recorded"))
    unauthorized_actions: Metric = field(
        default_factory=lambda: Metric.unavailable("not recorded")
    )
    retries: Metric = field(default_factory=lambda: Metric.unavailable("not recorded"))
    actions_executed: Metric = field(default_factory=lambda: Metric.unavailable("not recorded"))
    failure_category: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trial_id": self.trial_id,
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "input_id": self.input_id,
            "baseline": self.baseline,
            "manifest_id": self.manifest_id,
            "manifest_version": self.manifest_version,
            "manifest_schema_version": self.manifest_schema_version,
            "outcome": self.outcome.value,
            "agent_terminal_status": self.agent_terminal_status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "trace_artifact": self.trace_artifact,
            "verification": self.verification.to_dict(),
            "safety_violations": self.safety_violations.to_dict(),
            "unauthorized_actions": self.unauthorized_actions.to_dict(),
            "retries": self.retries.to_dict(),
            "actions_executed": self.actions_executed.to_dict(),
            "failure_category": self.failure_category,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EpisodeResult":
        return cls(
            trial_id=data["trial_id"],
            run_id=data["run_id"],
            scenario_id=data["scenario_id"],
            input_id=data["input_id"],
            baseline=data["baseline"],
            manifest_id=data["manifest_id"],
            manifest_version=data["manifest_version"],
            manifest_schema_version=int(data["manifest_schema_version"]),
            outcome=EpisodeOutcome(data["outcome"]),
            agent_terminal_status=data["agent_terminal_status"],
            started_at=data["started_at"],
            completed_at=data["completed_at"],
            duration_ms=int(data["duration_ms"]),
            trace_artifact=data.get("trace_artifact"),
            verification=VerificationEvidence.from_dict(data["verification"]),
            safety_violations=Metric.from_dict(data["safety_violations"]),
            unauthorized_actions=Metric.from_dict(data["unauthorized_actions"]),
            retries=Metric.from_dict(data["retries"]),
            actions_executed=Metric.from_dict(data["actions_executed"]),
            failure_category=data.get("failure_category"),
            error=data.get("error"),
        )


# ---------------------------------------------------------------------------
# Cell and run
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CellResult:
    """The aggregate over one cell's episodes.

    Every count is a :class:`Metric`, so a count that could not be
    produced carries its reason instead of appearing as ``0``. This is
    the shape of ``docs/benchmark_design.md`` §9's ``cells`` entry,
    with the "not measurable" fields given explicit reasons.
    """

    scenario_id: str
    input_id: str
    baseline: str
    fault_params: Mapping[str, Any]
    trials: int
    outcomes: Mapping[str, Metric]
    independent_verification: Mapping[str, Metric]
    false_successes: Metric
    verifier_disagreements: Metric
    unauthorized_actions: Metric
    safety_violations: Metric
    retries: Metric
    actions: Metric
    latency_ms: Mapping[str, Metric]
    model_calls: Metric
    model_cost_usd: Metric
    human_interventions: Metric
    failure_categories: Mapping[str, int]
    trace_artifacts: Tuple[str, ...]
    verifier_audit: Optional[VerifierAudit] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "input_id": self.input_id,
            "baseline": self.baseline,
            "fault_params": dict(self.fault_params),
            "trials": self.trials,
            "outcomes": {k: v.to_dict() for k, v in self.outcomes.items()},
            "independent_verification": {
                k: v.to_dict() for k, v in self.independent_verification.items()
            },
            "false_successes": self.false_successes.to_dict(),
            "verifier_disagreements": self.verifier_disagreements.to_dict(),
            "unauthorized_actions": self.unauthorized_actions.to_dict(),
            "safety_violations": self.safety_violations.to_dict(),
            "retries": self.retries.to_dict(),
            "actions": self.actions.to_dict(),
            "latency_ms": {k: v.to_dict() for k, v in self.latency_ms.items()},
            "model_calls": self.model_calls.to_dict(),
            "model_cost_usd": self.model_cost_usd.to_dict(),
            "human_interventions": self.human_interventions.to_dict(),
            "failure_categories": dict(self.failure_categories),
            "trace_artifacts": list(self.trace_artifacts),
            "verifier_audit": self.verifier_audit.to_dict() if self.verifier_audit else None,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CellResult":
        audit = data.get("verifier_audit")
        return cls(
            scenario_id=data["scenario_id"],
            input_id=data["input_id"],
            baseline=data["baseline"],
            fault_params=dict(data.get("fault_params", {})),
            trials=int(data["trials"]),
            outcomes={k: Metric.from_dict(v) for k, v in data.get("outcomes", {}).items()},
            independent_verification={
                k: Metric.from_dict(v) for k, v in data.get("independent_verification", {}).items()
            },
            false_successes=Metric.from_dict(data["false_successes"]),
            verifier_disagreements=Metric.from_dict(data["verifier_disagreements"]),
            unauthorized_actions=Metric.from_dict(data["unauthorized_actions"]),
            safety_violations=Metric.from_dict(data["safety_violations"]),
            retries=Metric.from_dict(data["retries"]),
            actions=Metric.from_dict(data["actions"]),
            latency_ms={k: Metric.from_dict(v) for k, v in data.get("latency_ms", {}).items()},
            model_calls=Metric.from_dict(data["model_calls"]),
            model_cost_usd=Metric.from_dict(data["model_cost_usd"]),
            human_interventions=Metric.from_dict(data["human_interventions"]),
            failure_categories=dict(data.get("failure_categories", {})),
            trace_artifacts=tuple(data.get("trace_artifacts", ())),
            verifier_audit=VerifierAudit.from_dict(audit) if audit else None,
        )


@dataclass(frozen=True)
class EnvironmentInfo:
    """The environment a run was executed in (design §7.6, §9).

    Every field is required to be present and non-empty, because a
    result whose environment is unknown cannot be reproduced.
    """

    python_version: str
    playwright_version: str
    browser: str
    browser_build: str
    platform: str
    demo_app_sha256: str
    dev_manifest_sha256: str
    eval_manifest_sha256: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "python_version": self.python_version,
            "playwright_version": self.playwright_version,
            "browser": self.browser,
            "browser_build": self.browser_build,
            "platform": self.platform,
            "demo_app_sha256": self.demo_app_sha256,
            "dev_manifest_sha256": self.dev_manifest_sha256,
            "eval_manifest_sha256": self.eval_manifest_sha256,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EnvironmentInfo":
        return cls(
            python_version=data["python_version"],
            playwright_version=data["playwright_version"],
            browser=data["browser"],
            browser_build=data["browser_build"],
            platform=data["platform"],
            demo_app_sha256=data["demo_app_sha256"],
            dev_manifest_sha256=data["dev_manifest_sha256"],
            eval_manifest_sha256=data["eval_manifest_sha256"],
        )


@dataclass(frozen=True)
class RunTotals:
    """Run-level totals (``docs/benchmark_design.md`` §9).

    ``false_success_rate`` is unavailable when its denominator is zero —
    a rate with no denominator is not ``0``.
    """

    episodes: int
    by_baseline: Mapping[str, int]
    false_success_rate: Metric
    unauthorized_actions: Metric

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episodes": self.episodes,
            "by_baseline": dict(self.by_baseline),
            "false_success_rate": self.false_success_rate.to_dict(),
            "unauthorized_actions": self.unauthorized_actions.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RunTotals":
        return cls(
            episodes=int(data["episodes"]),
            by_baseline=dict(data.get("by_baseline", {})),
            false_success_rate=Metric.from_dict(data["false_success_rate"]),
            unauthorized_actions=Metric.from_dict(data["unauthorized_actions"]),
        )


@dataclass(frozen=True)
class RunResult:
    """One benchmark run: the file described in ``docs/benchmark_design.md`` §9.

    ``status`` is ``proposed`` for a design illustration and ``measured``
    only for an actual run. ``episodes`` is the per-episode record the
    design's §9 example does not spell out; see
    ``docs/benchmark_design.md`` §15 for that ambiguity.
    """

    schema_version: int
    benchmark_id: str
    benchmark_version: str
    run_id: str
    started_at: str
    completed_at: str
    status: str
    agent_version: str
    srs_mapping: str
    manifest_id: str
    manifest_version: str
    manifest_schema_version: int
    manifest_sha256: str
    environment: EnvironmentInfo
    config: Mapping[str, Any]
    cells: Tuple[CellResult, ...]
    episodes: Tuple[EpisodeResult, ...]
    totals: RunTotals
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "benchmark_id": self.benchmark_id,
            "benchmark_version": self.benchmark_version,
            "run_id": self.run_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "agent_version": self.agent_version,
            "srs_mapping": self.srs_mapping,
            "manifest_id": self.manifest_id,
            "manifest_version": self.manifest_version,
            "manifest_schema_version": self.manifest_schema_version,
            "manifest_sha256": self.manifest_sha256,
            "environment": self.environment.to_dict(),
            "config": dict(self.config),
            "cells": [c.to_dict() for c in self.cells],
            "episodes": [e.to_dict() for e in self.episodes],
            "totals": self.totals.to_dict(),
            "notes": self.notes,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False) + "\n"

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RunResult":
        if int(data["schema_version"]) not in SUPPORTED_RESULT_SCHEMA_VERSIONS:
            raise ResultValidationError(
                [
                    f"unsupported result schema_version {data['schema_version']!r}; "
                    f"supported: {list(SUPPORTED_RESULT_SCHEMA_VERSIONS)}"
                ]
            )
        if data["status"] not in (STATUS_PROPOSED, STATUS_MEASURED):
            raise ResultValidationError(
                [f"status {data['status']!r} must be {STATUS_PROPOSED!r} or {STATUS_MEASURED!r}"]
            )
        return cls(
            schema_version=int(data["schema_version"]),
            benchmark_id=data["benchmark_id"],
            benchmark_version=data["benchmark_version"],
            run_id=data["run_id"],
            started_at=data["started_at"],
            completed_at=data["completed_at"],
            status=data["status"],
            agent_version=data["agent_version"],
            srs_mapping=data["srs_mapping"],
            manifest_id=data["manifest_id"],
            manifest_version=data["manifest_version"],
            manifest_schema_version=int(data["manifest_schema_version"]),
            manifest_sha256=data["manifest_sha256"],
            environment=EnvironmentInfo.from_dict(data["environment"]),
            config=dict(data["config"]),
            cells=tuple(CellResult.from_dict(c) for c in data.get("cells", ())),
            episodes=tuple(EpisodeResult.from_dict(e) for e in data.get("episodes", ())),
            totals=RunTotals.from_dict(data["totals"]),
            notes=data.get("notes", ""),
        )


def false_success_set(episodes: Sequence[EpisodeResult]) -> Tuple[EpisodeResult, ...]:
    """The episodes that are false successes.

    ``docs/benchmark_design.md`` §5::

        false_success := (agent reported "succeeded") AND NOT (P1 AND P2 AND P3)

    The agent's report comes from the trace's ``terminal_status``; the
    postconditions come from the independent verifier. An episode whose
    verification evidence is unavailable is **not** a false success and
    **not** a success — it is simply unclassified, and is excluded.
    """
    flagged: List[EpisodeResult] = []
    for episode in episodes:
        if episode.agent_terminal_status != "succeeded":
            continue
        evidence = episode.verification
        if evidence.status != VerificationEvidence.VERIFIED:
            continue
        if evidence.all_satisfied is False:
            flagged.append(episode)
    return tuple(flagged)
