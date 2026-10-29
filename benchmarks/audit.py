"""Verifier audit procedure (benchmark harness).

The independent verifier is itself fallible, so before any rate is
published a human must adjudicate a random sample of the run's
episodes and the agreement rate must be reported alongside the results
(``docs/benchmark_design.md`` §5). Below 95% agreement the run's rates
are **provisional** and the disagreement cases are published.

This module implements the procedure's mechanical half. The human
half — looking at the evidence and judging the verifier right or
wrong — stays a human act; nothing here adjudicates. The flow is:

1. :func:`plan_audit` draws a seeded sample per cell from a persisted
   run file and writes an **audit plan** naming, for each sampled
   episode, the evidence bundle the human must inspect.
2. The human inspects the bundles and records one verdict per sampled
   episode in the plan file (their own P1–P3 booleans, or
   ``unauditable`` with a reason).
3. :func:`apply_audit` validates the verdicts, computes agreement,
   and writes a new run file with ``CellResult.verifier_audit``
   filled in.

Authority and deliberately narrow scope
---------------------------------------
Design §5 (human-adjudicated sample, 95% provisional rule), §9 (the
per-cell ``verifier_audit`` shape), §11 (unaudited figures are
provisional), §13 item 6 (the item is a *process*), evaluation.md
§6.1 item 4 (the report carries size, rate, provisionality) and §8.3
(the audit mitigates verifier risk; it does not eliminate it).

What this module does NOT do: it sets no sample size of its own (the
human chooses and the plan records it); it never treats missing
evidence as agreement (incomplete bundles are skipped with reasons,
and skips are counted in the audit note); it copies no snapshot
contents into the plan (references and digests only — the human reads
the artifacts themselves); it does not label runs provisional (that
wording belongs to the report stage — but :func:`is_provisional`
gives the rule its single implementation); and it leaves the
per-episode ``VerificationEvidence.audit`` slot alone, whose
semantics the design never defines.

Sampling rule
-------------
Per cell, over measured (non-warm-up) episodes: order candidates by
``sha256(seed : trial_id)`` — a seeded random permutation that is
reproducible from persisted information on any Python version —
and take the first ``sample_size`` episodes whose evidence bundles
are complete. Skipped episodes and their reasons are recorded in the
plan; requesting more than exist fails closed. The default seed is
``f"{run_id}:{cell_key}"``; an explicit seed override is recorded
when used.

Agreement rule
--------------
Agreement is strict per-check equality between the verifier's P1–P3
booleans and the human's: the audit checks the verifier's *decisions*
(evaluation.md §2), and a check-level mismatch is a disagreement even
when both sides' conjunctions coincide. This is the conservative
reading — it can only lower agreement toward provisionality, never
raise it.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from benchmarks.manifest import Manifest, load_manifest
from benchmarks.results import (
    CellResult,
    EpisodeResult,
    ResultValidationError,
    RunResult,
    VerificationEvidence,
    VerifierAudit,
)

#: Audit-plan file schema identifier.
PLAN_SCHEMA = "chimera-audit-plan/1"

#: Filename suffix for audit-plan artifacts.
PLAN_SUFFIX = ".audit-plan.json"

#: Design §5: agreement below this rate makes reported rates provisional.
AGREEMENT_THRESHOLD = 0.95


class AuditError(ValueError):
    """The audit cannot proceed honestly; nothing is written."""


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------


def cell_key(scenario_id: str, input_id: str, baseline: str,
             fault_params: Mapping[str, Any]) -> str:
    """The stable per-cell identity used for seed derivation.

    Fault params are part of the key: one scenario/input pair can
    carry several fault variants (eval-v1's S-SLOW has five), and
    each variant is its own cell with its own sample. Without the
    variant in the key, colliding cells would overwrite each other
    in the plan and share one sample.
    """
    faults = ",".join(f"{name}={fault_params[name]}"
                      for name in sorted(fault_params))
    return f"{scenario_id}|{input_id}|{baseline}|{faults}"


def default_seed(run_id: str, key: str) -> str:
    """The reproducible default seed, derivable from the run file alone."""
    return f"{run_id}:{key}"


def draw_order(trial_ids: List[str], seed: str) -> List[str]:
    """The seeded permutation of candidates (hash ordering).

    Sorting by ``sha256(seed : trial_id)`` is a uniform random
    permutation for sampling purposes, and unlike ``random.shuffle``
    its output does not depend on Python-version RNG internals.
    """
    keyed = [
        (hashlib.sha256(f"{seed}:{trial_id}".encode("utf-8")).hexdigest(),
         trial_id)
        for trial_id in trial_ids
    ]
    keyed.sort(key=lambda pair: pair[0])
    return [trial_id for _, trial_id in keyed]


def is_provisional(agreement_rate: Optional[float]) -> bool:
    """Whether the §5 provisional rule fires.

    Unaudited (``None``) rates are provisional, per the §11 example;
    audited rates below :data:`AGREEMENT_THRESHOLD` are provisional.
    """
    return agreement_rate is None or agreement_rate < AGREEMENT_THRESHOLD


# ---------------------------------------------------------------------------
# Evidence bundles
# ---------------------------------------------------------------------------


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@dataclass(frozen=True)
class EvidenceBundle:
    """The per-episode evidence a human needs to check the verdict.

    ``expected_stored_name`` comes from the manifest (the run file does
    not carry it). ``trace_path`` is the trace for Chimera episodes or
    the driver report for replay episodes. ``snapshot_path`` and
    ``actions_path`` follow the artifact-layout convention (siblings
    of the trace artifact). Digests let the human confirm they are
    looking at the bytes the plan was drawn against. Observer evidence
    is listed for completeness but plays no part in adjudication,
    which concerns only the verifier's P1–P3 decisions.
    """

    trial_id: str
    run_id: str
    manifest_id: str
    scenario_id: str
    input_id: str
    baseline: str
    expected_stored_name: str
    agent_terminal_status: str
    outcome: str
    trace_path: str
    snapshot_path: str
    actions_path: str
    verifier_checks: Mapping[str, bool]
    digests: Mapping[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trial_id": self.trial_id,
            "run_id": self.run_id,
            "manifest_id": self.manifest_id,
            "scenario_id": self.scenario_id,
            "input_id": self.input_id,
            "baseline": self.baseline,
            "expected_stored_name": self.expected_stored_name,
            "agent_terminal_status": self.agent_terminal_status,
            "outcome": self.outcome,
            "trace_path": self.trace_path,
            "snapshot_path": self.snapshot_path,
            "actions_path": self.actions_path,
            "verifier_checks": dict(self.verifier_checks),
            "digests": dict(self.digests),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EvidenceBundle":
        try:
            checks = dict(data["verifier_checks"])
            digests = dict(data.get("digests", {}))
            return cls(
                trial_id=str(data["trial_id"]),
                run_id=str(data["run_id"]),
                manifest_id=str(data["manifest_id"]),
                scenario_id=str(data["scenario_id"]),
                input_id=str(data["input_id"]),
                baseline=str(data["baseline"]),
                expected_stored_name=str(data["expected_stored_name"]),
                agent_terminal_status=str(data["agent_terminal_status"]),
                outcome=str(data["outcome"]),
                trace_path=str(data["trace_path"]),
                snapshot_path=str(data["snapshot_path"]),
                actions_path=str(data["actions_path"]),
                verifier_checks={k: bool(v) for k, v in checks.items()},
                digests={k: str(v) for k, v in digests.items()},
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise AuditError(f"malformed evidence bundle: {exc}") from exc


def _sibling_path(trace_path: str, run_id: str, suffix: str) -> Path:
    """The artifact-layout convention: per-run files share a directory."""
    return Path(trace_path).parent / f"{run_id}{suffix}"


def build_bundle(episode: EpisodeResult, manifest: Manifest
                 ) -> Tuple[Optional[EvidenceBundle], Optional[str]]:
    """Assemble an episode's bundle, or return ``(None, reason)``.

    Reasons cover every way a bundle can be incomplete: missing
    manifest input, unavailable verifier evidence, a missing trace
    artifact, a snapshot reference that does not resolve to the
    expected file, and unreadable bytes. Callers record the reason;
    they never adjudicate the episode.
    """
    try:
        scenario = manifest.scenario(episode.scenario_id)
    except KeyError:
        return None, (f"scenario {episode.scenario_id!r} is not in "
                      f"manifest {manifest.manifest_id!r}")
    expected: Optional[str] = None
    for task_input in scenario.inputs:
        if task_input.id == episode.input_id:
            expected = task_input.expected_stored_name
    if expected is None:
        return None, (f"input {episode.input_id!r} of scenario "
                      f"{episode.scenario_id!r} is not in manifest "
                      f"{manifest.manifest_id!r}")
    if episode.verification.status != VerificationEvidence.VERIFIED:
        return None, ("no verifier verdict to audit: "
                      f"{episode.verification.unavailable_reason}")
    if not episode.trace_artifact:
        return None, "episode has no trace artifact path"
    trace_path = Path(episode.trace_artifact)
    if not trace_path.is_file():
        return None, f"trace artifact missing: {episode.trace_artifact}"
    snapshot_path = _sibling_path(
        episode.trace_artifact, episode.run_id, ".snapshot.json")
    if not snapshot_path.is_file():
        return None, f"state snapshot missing: {snapshot_path}"
    # The verifier's evidence references must point at the same
    # snapshot file the bundle names; otherwise the human and the
    # verifier would be looking at different bytes.
    refs = {c.evidence_reference.rsplit("#", 1)[0]
            for c in episode.verification.checks if c.evidence_reference}
    refs.discard("")
    if len(refs) != 1 or next(iter(refs)) != str(snapshot_path):
        return None, ("snapshot reference mismatch: the verifier's "
                      f"evidence references {sorted(refs)} do not resolve "
                      f"to {snapshot_path}")
    actions_path = _sibling_path(
        episode.trace_artifact, episode.run_id, ".actions.json")
    try:
        digests = {
            "trace": _sha256_file(trace_path),
            "snapshot": _sha256_file(snapshot_path),
        }
        if actions_path.is_file():
            digests["actions"] = _sha256_file(actions_path)
    except OSError as exc:
        return None, f"evidence bytes unreadable: {exc}"
    return EvidenceBundle(
        trial_id=episode.trial_id,
        run_id=episode.run_id,
        manifest_id=episode.manifest_id,
        scenario_id=episode.scenario_id,
        input_id=episode.input_id,
        baseline=episode.baseline,
        expected_stored_name=expected,
        agent_terminal_status=episode.agent_terminal_status,
        outcome=episode.outcome.value,
        trace_path=str(trace_path),
        snapshot_path=str(snapshot_path),
        actions_path=str(actions_path),
        verifier_checks={c.postcondition_id: c.satisfied
                         for c in episode.verification.checks},
        digests=digests,
    ), None


# ---------------------------------------------------------------------------
# Audit plans
# ---------------------------------------------------------------------------


def _now_utc_iso() -> str:
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


@dataclass
class CellSample:
    """One cell's draw: sampled bundles, skips, and human verdicts."""

    scenario_id: str
    input_id: str
    baseline: str
    seed: str
    sampled: List[EvidenceBundle] = field(default_factory=list)
    skipped: List[Dict[str, str]] = field(default_factory=list)
    verdicts: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "input_id": self.input_id,
            "baseline": self.baseline,
            "seed": self.seed,
            "sampled": [b.to_dict() for b in self.sampled],
            "skipped": [dict(s) for s in self.skipped],
            "verdicts": {k: _verdict_to_json(v) for k, v in self.verdicts.items()},
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CellSample":
        try:
            return cls(
                scenario_id=str(data["scenario_id"]),
                input_id=str(data["input_id"]),
                baseline=str(data["baseline"]),
                seed=str(data["seed"]),
                sampled=[EvidenceBundle.from_dict(b)
                         for b in data.get("sampled", [])],
                skipped=[{"trial_id": str(s["trial_id"]),
                          "reason": str(s["reason"])}
                         for s in data.get("skipped", [])],
                verdicts={str(k): _verdict_from_json(v)
                          for k, v in data.get("verdicts", {}).items()},
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise AuditError(f"malformed cell sample: {exc}") from exc


@dataclass(frozen=True)
class HumanVerdict:
    """One episode's adjudication: the human's own P1–P3 booleans."""

    checks: Mapping[str, bool]
    note: str = ""

    def agrees_with(self, verifier_checks: Mapping[str, bool]) -> bool:
        """Strict per-check equality (see the module docstring)."""
        if set(self.checks) != set(verifier_checks):
            return False
        return all(self.checks[k] == verifier_checks[k] for k in self.checks)


def _verdict_to_json(verdict: Any) -> Any:
    if isinstance(verdict, tuple):
        tag, payload = verdict
        if tag == "unauditable":
            return {"verdict": "unauditable", "reason": str(payload)}
        raise AuditError(f"cannot serialize verdict {verdict!r}")
    if isinstance(verdict, HumanVerdict):
        return {"checks": dict(verdict.checks), "note": verdict.note}
    raise AuditError(f"cannot serialize verdict {verdict!r}")


def _verdict_from_json(data: Any) -> Any:
    """Parse one human verdict, failing closed on any malformation.

    Returns a :class:`HumanVerdict`, or ``("unauditable", reason)``.
    """
    if not isinstance(data, dict):
        raise AuditError(f"verdict must be an object, got {data!r}")
    if data.get("verdict") == "unauditable":
        reason = data.get("reason", "")
        if not isinstance(reason, str) or not reason.strip():
            raise AuditError(
                "unauditable verdicts need a non-empty reason")
        return ("unauditable", reason)
    checks = data.get("checks")
    if not isinstance(checks, dict) or not checks:
        raise AuditError(
            f"verdict must carry a non-empty checks object, got {data!r}")
    parsed: Dict[str, bool] = {}
    for key, value in checks.items():
        if not isinstance(value, bool):
            raise AuditError(
                f"verdict check {key!r} must be a boolean, got {value!r}")
        parsed[str(key)] = value
    note = data.get("note", "")
    if not isinstance(note, str):
        raise AuditError(f"verdict note must be a string, got {note!r}")
    return HumanVerdict(checks=parsed, note=note)


@dataclass
class AuditPlan:
    """The persisted plan: per-cell samples plus human verdicts."""

    schema: str
    run_id: str
    manifest_id: str
    manifest_sha256: str
    sample_size: int
    auditor: str
    created_at: str
    cells: Dict[str, CellSample] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": self.schema,
            "run_id": self.run_id,
            "manifest_id": self.manifest_id,
            "manifest_sha256": self.manifest_sha256,
            "sample_size": self.sample_size,
            "auditor": self.auditor,
            "created_at": self.created_at,
            "cells": {k: v.to_dict() for k, v in self.cells.items()},
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True,
                           ensure_ascii=False, indent=2) + "\n"

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AuditPlan":
        if not isinstance(data, Mapping):
            raise AuditError(
                f"audit plan must be an object, got {type(data).__name__}")
        if data.get("schema") != PLAN_SCHEMA:
            raise AuditError(
                f"audit plan schema is {data.get('schema')!r}, expected "
                f"{PLAN_SCHEMA!r}")
        try:
            size = data["sample_size"]
            if isinstance(size, bool) or not isinstance(size, int) \
                    or size < 0:
                raise AuditError(
                    f"audit plan sample_size must be an integer >= 0, "
                    f"got {size!r}")
            return cls(
                schema=PLAN_SCHEMA,
                run_id=str(data["run_id"]),
                manifest_id=str(data["manifest_id"]),
                manifest_sha256=str(data["manifest_sha256"]),
                sample_size=size,
                auditor=str(data.get("auditor", "")),
                created_at=str(data.get("created_at", "")),
                cells={str(k): CellSample.from_dict(v)
                       for k, v in data.get("cells", {}).items()},
            )
        except KeyError as exc:
            raise AuditError(f"audit plan is missing {exc}") from exc

    @classmethod
    def from_json(cls, raw: str) -> "AuditPlan":
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AuditError(
                f"audit plan is not valid JSON: {exc}") from exc
        return cls.from_dict(data)


def _cell_episodes(run: RunResult, cell: CellResult) -> List[EpisodeResult]:
    """A cell's measured episodes in execution order (warm-ups excluded).

    Episodes carry no fault tag, so the mapping is positional: the
    runner persists episodes grouped by cell in manifest order, and
    each cell owns exactly its recorded ``trials`` episodes. The
    slice is integrity-checked against the cell's
    scenario/input/baseline — an inconsistent run file fails closed
    instead of sampling another cell's episodes.
    """
    measured = [e for e in run.episodes
                if not e.trial_id.startswith("warmup:")]
    cursor = 0
    for candidate in run.cells:
        owned = measured[cursor:cursor + candidate.trials]
        if candidate == cell:
            for episode in owned:
                if (episode.scenario_id, episode.input_id,
                        episode.baseline) != (cell.scenario_id,
                                              cell.input_id, cell.baseline):
                    raise AuditError(
                        f"cell {cell_key(cell.scenario_id, cell.input_id, cell.baseline, cell.fault_params)}: "
                        f"episode {episode.trial_id} does not belong to "
                        "this cell; the run file's episode order is "
                        "inconsistent")
            return list(owned)
        cursor += candidate.trials
    raise AuditError("cell not found in the run file")


def _load_plan_inputs(run_path: Path, manifest_path: Path
                      ) -> Tuple[RunResult, Manifest]:
    """Load the run and manifest a plan is drawn against (fail closed)."""
    try:
        run = RunResult.from_dict(json.loads(Path(run_path).read_text(
            encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ResultValidationError) as exc:
        raise AuditError(f"cannot load run file {run_path}: {exc}") from exc
    try:
        manifest = load_manifest(Path(manifest_path))
    except Exception as exc:  # noqa: BLE001 — manifest errors fail the plan
        raise AuditError(
            f"cannot load manifest {manifest_path}: {exc}") from exc
    if manifest.manifest_id != run.manifest_id \
            or manifest.sha256() != run.manifest_sha256:
        raise AuditError(
            f"manifest {manifest_path} ({manifest.manifest_id}) does not "
            f"match the run's manifest ({run.manifest_id}); dev and eval "
            "evidence must never be mixed")
    return run, manifest


def _draw_cell_sample(cell: CellResult, run: RunResult, manifest: Manifest,
                      key: str, cell_seed: str, sample_size: int
                      ) -> CellSample:
    """Draw one cell's sample: first-N-auditable in seeded draw order."""
    episodes = _cell_episodes(run, cell)
    order = draw_order([e.trial_id for e in episodes], cell_seed)
    by_trial = {e.trial_id: e for e in episodes}
    sample = CellSample(scenario_id=cell.scenario_id,
                        input_id=cell.input_id, baseline=cell.baseline,
                        seed=cell_seed)
    for trial_id in order:
        if len(sample.sampled) >= sample_size:
            break
        bundle, reason = build_bundle(by_trial[trial_id], manifest)
        if bundle is None:
            sample.skipped.append(
                {"trial_id": trial_id, "reason": reason or "unknown"})
        else:
            sample.sampled.append(bundle)
    if len(sample.sampled) < sample_size:
        raise AuditError(
            f"cell {key}: only {len(sample.sampled)} of {sample_size} "
            f"requested episodes are auditable "
            f"({len(sample.skipped)} skipped: "
            + "; ".join(s["reason"] for s in sample.skipped) + ")")
    return sample


def _write_plan(plan: AuditPlan, output_path: Path) -> AuditPlan:
    """Persist a plan atomically (temp file + rename)."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    tmp.write_text(plan.to_json(), encoding="utf-8")
    tmp.replace(out)
    return plan


def plan_audit(
    run_path: Path,
    manifest_path: Path,
    sample_size: int,
    output_path: Path,
    *,
    seed: Optional[str] = None,
    auditor: str = "",
) -> AuditPlan:
    """Draw the per-cell audit sample and write the plan file.

    ``sample_size`` is the human's choice of episodes per cell and is
    recorded, not defaulted. ``seed`` overrides the reproducible
    default seed per cell (recorded when used). Every cell with fewer
    auditable episodes than requested fails the whole plan — the
    shortfall is a finding, not something to silently cap.
    """
    if isinstance(sample_size, bool) or not isinstance(sample_size, int) \
            or sample_size < 0:
        raise AuditError(
            f"sample_size must be an integer >= 0, got {sample_size!r}")
    run, manifest = _load_plan_inputs(run_path, manifest_path)
    plan = AuditPlan(
        schema=PLAN_SCHEMA, run_id=run.run_id,
        manifest_id=manifest.manifest_id,
        manifest_sha256=manifest.sha256(),
        sample_size=sample_size, auditor=auditor,
        created_at=_now_utc_iso(), cells={},
    )
    for cell in run.cells:
        key = cell_key(cell.scenario_id, cell.input_id, cell.baseline,
                       cell.fault_params)
        cell_seed = seed if seed is not None else default_seed(run.run_id, key)
        plan.cells[key] = _draw_cell_sample(
            cell, run, manifest, key, cell_seed, sample_size)
    return _write_plan(plan, Path(output_path))


def plan_targeted_audit(
    run_path: Path,
    manifest_path: Path,
    targets: Sequence[str],
    sample_size: int,
    output_path: Path,
    *,
    seed: Optional[str] = None,
    auditor: str = "",
) -> AuditPlan:
    """Draw audit samples for SELECTED cells only; write the plan file.

    ``targets`` names the run cells to sample, by fault-aware
    :func:`cell_key`. Every other cell is recorded with an empty
    sample (no episodes, no verdicts, no skips), so the plan still
    covers every run cell exactly — :func:`apply_audit` requires
    exact coverage — while untargeted cells keep ``verifier_audit``
    as ``None`` and are reported as unaudited, never as agreement.
    ``sample_size`` is the per-targeted-cell draw (the human's
    choice, recorded); ``seed`` overrides the reproducible default
    seed on targeted cells only (recorded when used). Unknown
    target keys, an empty target list, and shortfalls fail closed.
    """
    if isinstance(sample_size, bool) or not isinstance(sample_size, int) \
            or sample_size < 1:
        raise AuditError(
            "targeted sample_size must be an integer >= 1, "
            f"got {sample_size!r}")
    run, manifest = _load_plan_inputs(run_path, manifest_path)
    want = set(targets)
    if not want:
        raise AuditError("targeted audit needs at least one target cell")
    have = {cell_key(c.scenario_id, c.input_id, c.baseline, c.fault_params)
            for c in run.cells}
    unknown = sorted(want - have)
    if unknown:
        raise AuditError(
            f"target cells are not in run {run.run_id!r}: {unknown}")
    plan = AuditPlan(
        schema=PLAN_SCHEMA, run_id=run.run_id,
        manifest_id=manifest.manifest_id,
        manifest_sha256=manifest.sha256(),
        sample_size=sample_size, auditor=auditor,
        created_at=_now_utc_iso(), cells={},
    )
    for cell in run.cells:
        key = cell_key(cell.scenario_id, cell.input_id, cell.baseline,
                       cell.fault_params)
        if key in want:
            cell_seed = (seed if seed is not None
                         else default_seed(run.run_id, key))
            plan.cells[key] = _draw_cell_sample(
                cell, run, manifest, key, cell_seed, sample_size)
        else:
            plan.cells[key] = CellSample(
                scenario_id=cell.scenario_id, input_id=cell.input_id,
                baseline=cell.baseline,
                seed=default_seed(run.run_id, key))
    return _write_plan(plan, Path(output_path))


def load_plan(path: Path) -> AuditPlan:
    """Load an audit plan (possibly with human verdicts filled in)."""
    try:
        return AuditPlan.from_json(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise AuditError(f"cannot load audit plan {path}: {exc}") from exc


# ---------------------------------------------------------------------------
# Applying verdicts
# ---------------------------------------------------------------------------


def _check_bundle_freshness(bundle: EvidenceBundle) -> None:
    """Refuse bundles whose bytes changed since the plan was drawn."""
    for kind, path in (("trace", bundle.trace_path),
                       ("snapshot", bundle.snapshot_path)):
        try:
            current = _sha256_file(Path(path))
        except OSError as exc:
            raise AuditError(
                f"episode {bundle.trial_id}: {kind} evidence {path} is "
                f"unreadable at apply time: {exc}")
        if bundle.digests.get(kind) != current:
            raise AuditError(
                f"episode {bundle.trial_id}: {kind} evidence {path} changed "
                "since the plan was drawn; refusing to apply verdicts "
                "recorded against different bytes")


def apply_audit(run_path: Path, plan_path: Path, output_path: Path
                ) -> RunResult:
    """Validate human verdicts and write an audited copy of the run.

    Every sampled episode needs exactly one verdict; malformed,
    missing, or extra verdicts fail the whole application. Agreement
    is strict per-check equality; human-``unauditable`` episodes are
    excluded from the fraction. Cells whose sample adjudicates to
    zero episodes keep ``verifier_audit`` as ``None`` (no sample
    adjudicated, per the §11 example). Evidence bytes are
    re-hashed: verdicts recorded against changed bytes are refused.
    The input run file is never modified; the audited copy goes to
    ``output_path``.
    """
    try:
        raw_run = json.loads(Path(run_path).read_text(encoding="utf-8"))
        run = RunResult.from_dict(raw_run)
    except (OSError, json.JSONDecodeError, ResultValidationError) as exc:
        raise AuditError(f"cannot load run file {run_path}: {exc}") from exc
    plan = load_plan(Path(plan_path))
    if plan.run_id != run.run_id:
        raise AuditError(
            f"audit plan targets run {plan.run_id!r}, run file is "
            f"{run.run_id!r}")
    if plan.manifest_id != run.manifest_id \
            or plan.manifest_sha256 != run.manifest_sha256:
        raise AuditError(
            "audit plan manifest "
            f"({plan.manifest_id}) does not match the run's manifest "
            f"({run.manifest_id})")
    expected_keys = {cell_key(c.scenario_id, c.input_id, c.baseline,
                              c.fault_params)
                     for c in run.cells}
    if set(plan.cells) != expected_keys:
        raise AuditError(
            "audit plan cells do not match the run's cells: plan has "
            f"{sorted(plan.cells)}, run has {sorted(expected_keys)}")

    new_cells: List[CellResult] = []
    for cell in run.cells:
        key = cell_key(cell.scenario_id, cell.input_id, cell.baseline,
                       cell.fault_params)
        sample = plan.cells[key]
        sampled_ids = [b.trial_id for b in sample.sampled]
        if set(sample.verdicts) != set(sampled_ids):
            missing = sorted(set(sampled_ids) - set(sample.verdicts))
            extra = sorted(set(sample.verdicts) - set(sampled_ids))
            raise AuditError(
                f"cell {key}: verdicts must cover exactly the sampled "
                f"episodes (missing={missing}, extra={extra})")
        by_trial = {b.trial_id: b for b in sample.sampled}
        agreed = 0
        adjudicated = 0
        unauditable = 0
        for trial_id in sampled_ids:
            bundle = by_trial[trial_id]
            _check_bundle_freshness(bundle)
            verdict = sample.verdicts[trial_id]
            if isinstance(verdict, tuple):
                unauditable += 1
                continue
            if set(verdict.checks) != set(bundle.verifier_checks):
                raise AuditError(
                    f"cell {key}, episode {trial_id}: verdict checks "
                    f"{sorted(verdict.checks)} do not match the verifier's "
                    f"checks {sorted(bundle.verifier_checks)}; a partial "
                    "verdict cannot adjudicate the episode")
            adjudicated += 1
            if verdict.agrees_with(bundle.verifier_checks):
                agreed += 1
        if adjudicated == 0:
            audit = None
        else:
            skips = len(sample.skipped)
            note = (f"{adjudicated} of {len(sampled_ids)} sampled episodes "
                    f"adjudicated")
            if unauditable:
                note += f"; {unauditable} unauditable by the human"
            if skips:
                note += f"; {skips} skipped for incomplete evidence"
            note += (f"; seed {sample.seed!r}; auditor "
                     f"{plan.auditor or 'unrecorded'}")
            audit = VerifierAudit(
                sampled=adjudicated, agreed=agreed,
                agreement_rate=agreed / adjudicated, note=note)
        new_cells.append(dataclasses.replace(cell, verifier_audit=audit))

    audited = dataclasses.replace(run, cells=tuple(new_cells))
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_suffix(output_path.suffix + ".tmp")
    tmp.write_text(audited.to_json(), encoding="utf-8")
    tmp.replace(output_path)
    return audited


__all__ = [
    "AGREEMENT_THRESHOLD",
    "PLAN_SCHEMA",
    "PLAN_SUFFIX",
    "AuditError",
    "AuditPlan",
    "CellSample",
    "EvidenceBundle",
    "HumanVerdict",
    "apply_audit",
    "build_bundle",
    "cell_key",
    "default_seed",
    "draw_order",
    "is_provisional",
    "load_plan",
    "plan_audit",
    "plan_targeted_audit",
]
