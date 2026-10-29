"""Benchmark manifest schema, parsing, validation, and content hashing.

Stage 1 of the Chimera benchmark harness. This module defines the
*contract* for a benchmark manifest — what a scenario is, what fault
configuration applies to it, which postconditions are expected, and
what limits the run. It contains no runner, no browser access, and no
agent code, and it imports nothing outside the standard library.

Authority
---------
``docs/benchmark_design.md``:

* §2 — target, task, and the postcondition set (``P1``–``P4``).
* §3 — the scenario catalogue (``S-NORM``, ``S-SLOW``, ``S-DIS``,
  ``S-SLOWDIS``) and the input variations (``I-PLAIN``, ``I-SUBSTR``,
  ``I-SPACE``, ``I-UNICODE``).
* §4 — the development/evaluation split, the ``slow`` band, and the
  discipline rules.
* §7 — the trial protocol (trials per cell, warm-up, fixed cell order).
* §9 — the result schema (the manifest's ``config`` block mirrors it).

Design notes
------------
**A scenario carries fault *variants*, not a single fault.** The
evaluation manifest carries five ``slow`` values (800, 1350, 2100,
3000, 3900 ms) for ``S-SLOW``. The benchmark's cell is therefore keyed
by *(scenario, fault variant, input, baseline)* — consistent with
``docs/benchmark_design.md`` §9, whose example cell names both
``scenario_id`` and ``fault_params``.

**The ``slow`` band is data, not prose.** §4 documents a band of
[500, 4000] ms and gives it a reason: a ``slow`` value above 4000 ms
would change the scenario's class, because it could no longer resolve
inside ``ACTION_TIMEOUT_MS`` (5000 ms). Encoding the band in the
manifest lets the validator *enforce* the invariant that prose can only
state.

**Cell order is derived, not random.** §7.3 requires cells to run in a
fixed, manifest-declared order. :meth:`Manifest.cells` produces that
order deterministically from the manifest's own ordering.

Open ambiguities raised by this module are recorded in
``docs/benchmark_design.md`` §15.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

#: Schema version emitted by this module.
MANIFEST_SCHEMA_VERSION = 1

#: Schema versions this module can parse. A manifest declaring anything
#: else is rejected rather than guessed at.
SUPPORTED_MANIFEST_SCHEMA_VERSIONS: Tuple[int, ...] = (1,)

#: The two splits defined in ``docs/benchmark_design.md`` §4.
VALID_SPLITS: Tuple[str, ...] = ("development", "evaluation")

#: The outcomes a scenario may *expect*. ``cancelled`` and
#: ``inconclusive`` are not expectable today — see §8.3 of the design
#: and ADR-004 Q4.
VALID_EXPECTED_OUTCOMES: Tuple[str, ...] = ("succeeded", "failed")

#: The baseline the manifest is written against. Baseline A and B are
#: separate stages (``docs/benchmark_design.md`` §6).
DEFAULT_BASELINE = "chimera"


class ManifestValidationError(ValueError):
    """Raised when a manifest is malformed or invalid.

    ``issues`` carries every problem found, so a caller can report all
    of them at once rather than one per run.
    """

    def __init__(self, issues: Sequence[str]) -> None:
        self.issues: Tuple[str, ...] = tuple(issues)
        detail = "; ".join(self.issues)
        super().__init__(f"invalid benchmark manifest ({len(self.issues)} issue(s)): {detail}")


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Postcondition:
    """One independently checkable condition on the final page state.

    ``kind`` names the check the independent verifier will perform
    (``docs/benchmark_design.md`` §2). ``verified_by`` records *who*
    grades it — the agent's own checks are not evidence (design §5), so
    every postcondition here names an independent verifier.
    """

    id: str
    kind: str
    description: str
    verified_by: str = "independent_verifier"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "description": self.description,
            "verified_by": self.verified_by,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Postcondition":
        return cls(
            id=data["id"],
            kind=data["kind"],
            description=data.get("description", ""),
            verified_by=data.get("verified_by", "independent_verifier"),
        )


@dataclass(frozen=True)
class FaultConfig:
    """A deterministic fault configuration for the demo app.

    Maps directly onto the two URL parameters the demo app reads
    (``docs/benchmark_design.md`` §2): ``slow`` in milliseconds and
    ``disabled``. The combination is persistent, because the demo app's
    slow timer re-enables the controls only when ``disabled`` is unset.
    """

    slow_ms: int = 0
    disabled: bool = False

    def url_params(self) -> Dict[str, str]:
        """The URL parameters this fault configuration corresponds to."""
        params: Dict[str, str] = {}
        if self.slow_ms:
            params["slow"] = str(self.slow_ms)
        if self.disabled:
            params["disabled"] = "1"
        return params

    def to_dict(self) -> Dict[str, Any]:
        return {"slow_ms": self.slow_ms, "disabled": self.disabled}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "FaultConfig":
        return cls(slow_ms=data.get("slow_ms", 0), disabled=bool(data.get("disabled", False)))


@dataclass(frozen=True)
class TaskInput:
    """A task input variation (``docs/benchmark_design.md`` §3.3).

    ``expected_stored_name`` is the text the demo app will store in the
    project list: the demo app assigns ``item.textContent =
    nameInput.value.trim()``, so a padded input is stored trimmed. It is
    stated explicitly rather than re-derived by the verifier, because
    postcondition ``P2`` is an equality check against exactly this
    value, and a verifier that re-implements the trim is a second
    place for the same rule to be got wrong.
    """

    id: str
    project_name: str
    expected_stored_name: Optional[str] = None

    def stored_name(self) -> str:
        """The text expected in the project list for this input."""
        return self.project_name if self.expected_stored_name is None else self.expected_stored_name

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "project_name": self.project_name,
            "expected_stored_name": self.expected_stored_name,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TaskInput":
        return cls(
            id=data["id"],
            project_name=data["project_name"],
            expected_stored_name=data.get("expected_stored_name"),
        )


@dataclass(frozen=True)
class Scenario:
    """One benchmark scenario.

    ``fault_variants`` may hold more than one configuration: the
    evaluation manifest gives ``S-SLOW`` five different ``slow`` values.
    ``expected_outcome`` is what a *correct* agent does — for the
    persistent-fault scenarios that is ``failed``, and a success there
    would be a bug indicator, not an achievement (design §3.1).
    """

    id: str
    description: str
    fault_variants: Tuple[FaultConfig, ...]
    expected_outcome: str
    timeout_seconds: float
    postconditions: Tuple[Postcondition, ...]
    preconditions: Tuple[Postcondition, ...] = ()
    inputs: Tuple[TaskInput, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "fault_variants": [f.to_dict() for f in self.fault_variants],
            "expected_outcome": self.expected_outcome,
            "timeout_seconds": self.timeout_seconds,
            "preconditions": [p.to_dict() for p in self.preconditions],
            "postconditions": [p.to_dict() for p in self.postconditions],
            "inputs": [i.to_dict() for i in self.inputs],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Scenario":
        return cls(
            id=data["id"],
            description=data.get("description", ""),
            fault_variants=tuple(FaultConfig.from_dict(f) for f in data.get("fault_variants", ())),
            expected_outcome=data["expected_outcome"],
            timeout_seconds=_require_number(data["timeout_seconds"], "scenario.timeout_seconds"),
            preconditions=tuple(
                Postcondition.from_dict(p) for p in data.get("preconditions", ())
            ),
            postconditions=tuple(
                Postcondition.from_dict(p) for p in data.get("postconditions", ())
            ),
            inputs=tuple(TaskInput.from_dict(i) for i in data.get("inputs", ())),
        )


@dataclass(frozen=True)
class RetryPolicyConfig:
    """The retry policy the run is executed under.

    Mirrors ``chimera.safety.RetryPolicy`` so a run records the policy
    it actually ran under, independently of the product's defaults
    (``docs/benchmark_design.md`` §7.6, §9).
    """

    max_attempts: int
    base_delay_seconds: float
    max_delay_seconds: float
    max_total_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_attempts": self.max_attempts,
            "base_delay_seconds": self.base_delay_seconds,
            "max_delay_seconds": self.max_delay_seconds,
            "max_total_seconds": self.max_total_seconds,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RetryPolicyConfig":
        return cls(
            max_attempts=_require_int(data["max_attempts"], "config.policy.max_attempts"),
            base_delay_seconds=_require_number(
                data["base_delay_seconds"], "config.policy.base_delay_seconds"
            ),
            max_delay_seconds=_require_number(
                data["max_delay_seconds"], "config.policy.max_delay_seconds"
            ),
            max_total_seconds=_require_number(
                data["max_total_seconds"], "config.policy.max_total_seconds"
            ),
        )


@dataclass(frozen=True)
class RunConfig:
    """Execution limits and counts for a run (``docs/benchmark_design.md`` §7)."""

    trials_per_cell: int
    warmup_episodes: int
    episode_timeout_seconds: float
    action_timeout_ms: int
    policy: RetryPolicyConfig

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trials_per_cell": self.trials_per_cell,
            "warmup_episodes": self.warmup_episodes,
            "episode_timeout_seconds": self.episode_timeout_seconds,
            "action_timeout_ms": self.action_timeout_ms,
            "policy": self.policy.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RunConfig":
        return cls(
            trials_per_cell=_require_int(data["trials_per_cell"], "config.trials_per_cell"),
            warmup_episodes=_require_int(data.get("warmup_episodes", 0), "config.warmup_episodes"),
            episode_timeout_seconds=_require_number(
                data["episode_timeout_seconds"], "config.episode_timeout_seconds"
            ),
            action_timeout_ms=_require_int(data["action_timeout_ms"], "config.action_timeout_ms"),
            policy=RetryPolicyConfig.from_dict(data["policy"]),
        )


@dataclass(frozen=True)
class SlowBand:
    """The permitted range of the ``slow`` fault parameter.

    Both manifests use [500, 4000] ms (design §4). The band is recorded
    per manifest so the validator can enforce that a scenario's class
    (transient and resolvable inside the action timeout) is stable.
    """

    min_ms: int
    max_ms: int

    def contains(self, slow_ms: int) -> bool:
        return self.min_ms <= slow_ms <= self.max_ms

    def to_dict(self) -> Dict[str, Any]:
        return {"min_ms": self.min_ms, "max_ms": self.max_ms}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SlowBand":
        return cls(
            min_ms=_require_int(data["min_ms"], "slow_band_ms.min_ms"),
            max_ms=_require_int(data["max_ms"], "slow_band_ms.max_ms"),
        )


@dataclass(frozen=True)
class Cell:
    """One execution cell: a scenario, a fault variant, and an input.

    ``trials`` episodes are run per cell (``docs/benchmark_design.md``
    §7.2). The baseline is part of the cell key so that Baseline A and
    Baseline C are reported side by side on the same cell.
    """

    scenario_id: str
    input_id: str
    fault: FaultConfig
    baseline: str = DEFAULT_BASELINE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "input_id": self.input_id,
            "baseline": self.baseline,
            "fault_params": self.fault.to_dict(),
        }


@dataclass(frozen=True)
class Manifest:
    """A versioned, content-hashed set of benchmark scenarios."""

    schema_version: int
    benchmark_id: str
    benchmark_version: str
    manifest_id: str
    split: str
    description: str
    slow_band_ms: SlowBand
    config: RunConfig
    scenarios: Tuple[Scenario, ...]

    # -- derived views ----------------------------------------------------

    def cells(self, baseline: str = DEFAULT_BASELINE) -> Tuple[Cell, ...]:
        """The manifest's cells, in the fixed manifest-declared order.

        The order is the manifest's own scenario order, then each
        scenario's fault-variant order, then its input order. It is
        deterministic and contains no randomness (design §7.3).
        """
        out: List[Cell] = []
        for scenario in self.scenarios:
            for fault in scenario.fault_variants:
                for task_input in scenario.inputs:
                    out.append(
                        Cell(
                            scenario_id=scenario.id,
                            input_id=task_input.id,
                            fault=fault,
                            baseline=baseline,
                        )
                    )
        return tuple(out)

    def total_episodes(self, baseline: str = DEFAULT_BASELINE) -> int:
        """Episodes the manifest implies, excluding the warm-up."""
        return len(self.cells(baseline)) * self.config.trials_per_cell

    def scenario(self, scenario_id: str) -> Scenario:
        for candidate in self.scenarios:
            if candidate.id == scenario_id:
                return candidate
        raise KeyError(scenario_id)

    # -- serialisation ----------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "benchmark_id": self.benchmark_id,
            "benchmark_version": self.benchmark_version,
            "manifest_id": self.manifest_id,
            "split": self.split,
            "description": self.description,
            "slow_band_ms": self.slow_band_ms.to_dict(),
            "config": self.config.to_dict(),
            "scenarios": [s.to_dict() for s in self.scenarios],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False) + "\n"

    def sha256(self) -> str:
        """The manifest's content hash.

        Computed over a canonical JSON encoding (sorted keys, no
        insignificant whitespace) so the hash is stable across
        serialisation choices and across platforms. The evaluation
        manifest is "frozen" by recording this hash before a run
        (design §4.1, §7.6).
        """
        canonical = json.dumps(
            self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Manifest":
        manifest = cls(
            schema_version=_require_int(data["schema_version"], "schema_version"),
            benchmark_id=_require_str(data["benchmark_id"], "benchmark_id"),
            benchmark_version=_require_str(
                data.get("benchmark_version", "0.0.0"), "benchmark_version"
            ),
            manifest_id=_require_str(data["manifest_id"], "manifest_id"),
            split=_require_str(data["split"], "split"),
            description=_require_str(data.get("description", ""), "description"),
            slow_band_ms=SlowBand.from_dict(data["slow_band_ms"]),
            config=RunConfig.from_dict(data["config"]),
            scenarios=tuple(Scenario.from_dict(s) for s in data["scenarios"]),
        )
        validate_manifest(manifest)
        return manifest


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


# -- typed extraction -------------------------------------------------------
#
# These run *before* any coercion. Without them, ``int(2.5)`` would
# silently turn an invalid trial count of 2.5 into a valid 2 and the
# manifest would be accepted.


def _require_int(value: Any, label: str) -> int:
    if not _is_int(value):
        raise ManifestValidationError(
            [f"malformed: {label} must be an integer, got {value!r}"]
        )
    return value


def _require_number(value: Any, label: str) -> float:
    if not _is_number(value):
        raise ManifestValidationError(
            [f"malformed: {label} must be a number, got {value!r}"]
        )
    return float(value)


def _require_str(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise ManifestValidationError(
            [f"malformed: {label} must be a string, got {value!r}"]
        )
    return value


def validate_manifest(manifest: Manifest) -> None:
    """Validate a manifest, raising :class:`ManifestValidationError`.

    Rejects malformed manifests, duplicate scenario IDs, invalid
    timeouts, and invalid trial counts, plus the internal-consistency
    rules the design implies (the ``slow`` band, the relationship
    between the band and the action timeout, and the relationship
    between a scenario's timeout and the episode timeout).
    """
    issues: List[str] = []

    # -- schema version ----------------------------------------------------
    if manifest.schema_version not in SUPPORTED_MANIFEST_SCHEMA_VERSIONS:
        issues.append(
            "malformed: unsupported schema_version "
            f"{manifest.schema_version!r}; supported: "
            f"{list(SUPPORTED_MANIFEST_SCHEMA_VERSIONS)}"
        )

    # -- identity ----------------------------------------------------------
    if not manifest.benchmark_id.strip():
        issues.append("malformed: benchmark_id must be a non-empty string")
    if not manifest.manifest_id.strip():
        issues.append("malformed: manifest_id must be a non-empty string")
    if manifest.split not in VALID_SPLITS:
        issues.append(
            f"invalid: split {manifest.split!r} must be one of {list(VALID_SPLITS)}"
        )

    # -- the slow band -----------------------------------------------------
    band = manifest.slow_band_ms
    if band.min_ms <= 0:
        issues.append(f"invalid: slow_band_ms.min_ms must be positive, got {band.min_ms}")
    if band.max_ms < band.min_ms:
        issues.append(
            f"invalid: slow_band_ms.max_ms ({band.max_ms}) must be >= "
            f"min_ms ({band.min_ms})"
        )

    # -- run config --------------------------------------------------------
    config = manifest.config
    if not _is_int(config.trials_per_cell) or config.trials_per_cell < 1:
        issues.append(
            f"invalid: config.trials_per_cell must be an integer >= 1, "
            f"got {config.trials_per_cell!r}"
        )
    if not _is_int(config.warmup_episodes) or config.warmup_episodes < 0:
        issues.append(
            f"invalid: config.warmup_episodes must be an integer >= 0, "
            f"got {config.warmup_episodes!r}"
        )
    if not _is_number(config.episode_timeout_seconds) or config.episode_timeout_seconds <= 0:
        issues.append(
            f"invalid: config.episode_timeout_seconds must be a positive number, "
            f"got {config.episode_timeout_seconds!r}"
        )
    if not _is_int(config.action_timeout_ms) or config.action_timeout_ms <= 0:
        issues.append(
            f"invalid: config.action_timeout_ms must be a positive integer, "
            f"got {config.action_timeout_ms!r}"
        )

    policy = config.policy
    if not _is_int(policy.max_attempts) or policy.max_attempts < 1:
        issues.append(
            f"invalid: config.policy.max_attempts must be an integer >= 1, "
            f"got {policy.max_attempts!r}"
        )
    if not _is_number(policy.base_delay_seconds) or policy.base_delay_seconds < 0:
        issues.append(
            f"invalid: config.policy.base_delay_seconds must be a number >= 0, "
            f"got {policy.base_delay_seconds!r}"
        )
    if not _is_number(policy.max_delay_seconds) or policy.max_delay_seconds < 0:
        issues.append(
            f"invalid: config.policy.max_delay_seconds must be a number >= 0, "
            f"got {policy.max_delay_seconds!r}"
        )
    if policy.max_delay_seconds < policy.base_delay_seconds:
        issues.append(
            f"invalid: config.policy.max_delay_seconds ({policy.max_delay_seconds}) "
            f"must be >= base_delay_seconds ({policy.base_delay_seconds})"
        )
    if not _is_number(policy.max_total_seconds) or policy.max_total_seconds <= 0:
        issues.append(
            f"invalid: config.policy.max_total_seconds must be a positive number, "
            f"got {policy.max_total_seconds!r}"
        )

    # The band exists so a slow scenario stays resolvable inside the
    # action timeout. A band that violates that is not a band, it is a
    # scenario-class change.
    if band.max_ms >= config.action_timeout_ms:
        issues.append(
            f"invalid: slow_band_ms.max_ms ({band.max_ms}) must be < "
            f"config.action_timeout_ms ({config.action_timeout_ms}), otherwise a "
            "slow scenario could no longer resolve inside the action timeout"
        )

    # -- scenarios ---------------------------------------------------------
    if not manifest.scenarios:
        issues.append("invalid: manifest must declare at least one scenario")

    seen_scenario_ids: Dict[str, int] = {}
    for index, scenario in enumerate(manifest.scenarios):
        label = f"scenarios[{index}]"
        if not scenario.id.strip():
            issues.append(f"malformed: {label}.id must be a non-empty string")
        if scenario.id in seen_scenario_ids:
            issues.append(
                f"invalid: duplicate scenario id {scenario.id!r} "
                f"(also at scenarios[{seen_scenario_ids[scenario.id]}])"
            )
        else:
            seen_scenario_ids[scenario.id] = index

        if scenario.expected_outcome not in VALID_EXPECTED_OUTCOMES:
            issues.append(
                f"invalid: {label} ({scenario.id!r}).expected_outcome "
                f"{scenario.expected_outcome!r} must be one of "
                f"{list(VALID_EXPECTED_OUTCOMES)}"
            )

        if not _is_number(scenario.timeout_seconds) or scenario.timeout_seconds <= 0:
            issues.append(
                f"invalid: {label} ({scenario.id!r}).timeout_seconds must be a "
                f"positive number, got {scenario.timeout_seconds!r}"
            )
        elif scenario.timeout_seconds > config.episode_timeout_seconds:
            issues.append(
                f"invalid: {label} ({scenario.id!r}).timeout_seconds "
                f"({scenario.timeout_seconds}) must be <= "
                f"config.episode_timeout_seconds ({config.episode_timeout_seconds})"
            )

        if not scenario.fault_variants:
            issues.append(f"invalid: {label} ({scenario.id!r}) must declare at least one fault variant")
        seen_faults: List[FaultConfig] = []
        for fault_index, fault in enumerate(scenario.fault_variants):
            fault_label = f"{label} ({scenario.id!r}).fault_variants[{fault_index}]"
            if not _is_int(fault.slow_ms) or fault.slow_ms < 0:
                issues.append(
                    f"invalid: {fault_label}.slow_ms must be an integer >= 0, "
                    f"got {fault.slow_ms!r}"
                )
            elif fault.slow_ms and not band.contains(fault.slow_ms):
                issues.append(
                    f"invalid: {fault_label}.slow_ms ({fault.slow_ms}) is outside the "
                    f"declared slow band [{band.min_ms}, {band.max_ms}]"
                )
            if not isinstance(fault.disabled, bool):
                issues.append(
                    f"invalid: {fault_label}.disabled must be a boolean, "
                    f"got {fault.disabled!r}"
                )
            if fault in seen_faults:
                issues.append(
                    f"invalid: {label} ({scenario.id!r}) repeats fault variant "
                    f"{fault.to_dict()}"
                )
            else:
                seen_faults.append(fault)

        if not scenario.inputs:
            issues.append(f"invalid: {label} ({scenario.id!r}) must declare at least one input")
        seen_input_ids: Dict[str, int] = {}
        for input_index, task_input in enumerate(scenario.inputs):
            input_label = f"{label} ({scenario.id!r}).inputs[{input_index}]"
            if not task_input.id.strip():
                issues.append(f"malformed: {input_label}.id must be a non-empty string")
            if task_input.id in seen_input_ids:
                issues.append(
                    f"invalid: {label} ({scenario.id!r}) repeats input id "
                    f"{task_input.id!r} (also at inputs[{seen_input_ids[task_input.id]}])"
                )
            else:
                seen_input_ids[task_input.id] = input_index
            if not task_input.project_name.strip():
                issues.append(
                    f"invalid: {input_label}.project_name must be a non-empty string"
                )
            if task_input.expected_stored_name is not None and not (
                isinstance(task_input.expected_stored_name, str)
                and task_input.expected_stored_name.strip()
            ):
                issues.append(
                    f"invalid: {input_label}.expected_stored_name must be a non-empty "
                    f"string or omitted, got {task_input.expected_stored_name!r}"
                )

        if not scenario.postconditions:
            issues.append(
                f"invalid: {label} ({scenario.id!r}) must declare at least one postcondition"
            )
        seen_pc_ids: Dict[str, int] = {}
        for pc_index, postcondition in enumerate(scenario.postconditions):
            pc_label = f"{label} ({scenario.id!r}).postconditions[{pc_index}]"
            if not postcondition.id.strip():
                issues.append(f"malformed: {pc_label}.id must be a non-empty string")
            if not postcondition.kind.strip():
                issues.append(f"malformed: {pc_label}.kind must be a non-empty string")
            if postcondition.id in seen_pc_ids:
                issues.append(
                    f"invalid: {label} ({scenario.id!r}) repeats postcondition id "
                    f"{postcondition.id!r}"
                )
            else:
                seen_pc_ids[postcondition.id] = pc_index

        seen_pre_ids: Dict[str, int] = {}
        for pc_index, precondition in enumerate(scenario.preconditions):
            pc_label = f"{label} ({scenario.id!r}).preconditions[{pc_index}]"
            if not precondition.id.strip():
                issues.append(f"malformed: {pc_label}.id must be a non-empty string")
            if precondition.id in seen_pre_ids:
                issues.append(
                    f"invalid: {label} ({scenario.id!r}) repeats precondition id "
                    f"{precondition.id!r}"
                )
            else:
                seen_pre_ids[precondition.id] = pc_index
            if precondition.id in seen_pc_ids:
                issues.append(
                    f"invalid: {label} ({scenario.id!r}) reuses postcondition id "
                    f"{precondition.id!r} as a precondition id"
                )

    if issues:
        raise ManifestValidationError(issues)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def parse_manifest(data: Mapping[str, Any]) -> Manifest:
    """Build and validate a :class:`Manifest` from a decoded JSON object.

    Structural problems (a missing key, a value of the wrong type) are
    reported as ``malformed:`` issues; semantic problems are reported as
    ``invalid:`` issues. Both raise :class:`ManifestValidationError`.
    """
    issues: List[str] = []
    required = {
        "schema_version": int,
        "benchmark_id": str,
        "manifest_id": str,
        "split": str,
        "slow_band_ms": dict,
        "config": dict,
        "scenarios": list,
    }
    for key, expected in required.items():
        if key not in data:
            issues.append(f"malformed: missing required key {key!r}")
        elif not isinstance(data[key], expected) or isinstance(data[key], bool):
            issues.append(
                f"malformed: {key!r} must be {expected.__name__}, "
                f"got {type(data[key]).__name__}"
            )
    if issues:
        raise ManifestValidationError(issues)

    try:
        return Manifest.from_dict(data)
    except ManifestValidationError:
        # Already a structured, typed rejection — keep its issue list.
        raise
    except KeyError as exc:
        raise ManifestValidationError([f"malformed: missing required key {exc.args[0]!r}"]) from exc
    except (TypeError, ValueError) as exc:
        raise ManifestValidationError([f"malformed: {exc}"]) from exc


def load_manifest(path: Path) -> Manifest:
    """Load, parse, and validate a manifest from a JSON file."""
    raw = Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ManifestValidationError([f"malformed: {path} is not valid JSON: {exc}"]) from exc
    if not isinstance(data, dict):
        raise ManifestValidationError([f"malformed: {path} must contain a JSON object"])
    return parse_manifest(data)
