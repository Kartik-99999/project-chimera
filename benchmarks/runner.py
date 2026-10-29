"""Benchmark harness runner: manifest -> episodes -> results file.

Stage 2 of the Chimera benchmark harness. The runner loads one versioned
manifest (:mod:`benchmarks.manifest`), enumerates its cells in the
manifest-declared order, executes each cell's trials against the local
demo app, records one :class:`~benchmarks.results.EpisodeResult` per
episode, aggregates into per-cell results, and persists a
:class:`~benchmarks.results.RunResult`.

Authority
---------
``docs/benchmark_design.md``:

* §4 — the development/evaluation split. The runner executes exactly one
  manifest per run, so dev and eval episodes are never mixed; the split
  is recorded in the result.
* §7 — the trial protocol (fresh state per episode, fixed cell order,
  warm-up excluded from statistics, environment recorded per run).
* §9 — the result schema (persisted via :mod:`benchmarks.results`).
* §14.1 (AMB-9) and ``docs/adr/ADR-005-*.md`` — the runner **refuses**
  to execute a manifest whose declared retry policy diverges from the
  agent's effective policy. See :func:`check_policy_alignment`.
* §14.2 — the episode budget is the smaller of the scenario timeout and
  the run-wide episode timeout, enforced through the agent's existing
  cooperative :class:`~chimera.safety.CancellationToken`.
* §14.3 — warm-up episodes run outside any cell and are excluded from
  every aggregate.

What the runner does NOT do (later stages): Baseline B (§6), the
verifier audit, or the report template. Every metric gated on those is
recorded as :meth:`~benchmarks.results.Metric.unavailable` with an
explicit reason — never as ``0``. Independent verification (Stage 3,
:mod:`benchmarks.verifier`) is wired in: each episode's postconditions
are evaluated from its harness-observed snapshot. Action observation
(Stage 4, :mod:`benchmarks.observer`) is wired in: each episode's
actions are recorded at the Playwright boundary and judged against
the scenario's permitted set. Baseline A
(:mod:`benchmarks.baseline_a`) runs through the same per-cell model
with the deterministic replay executor; replay episodes read their
terminal from a persisted driver report instead of a trace.

The runner is deterministic and injectable for tests: the episode
executor, the environment record, and all output paths are constructor
arguments. The default executor drives the real agent
(:func:`chimera.agent.create_project`); tests substitute fakes that
write fixture traces.
"""

from __future__ import annotations

import hashlib
import json
import math
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from chimera.safety import CancellationToken

from benchmarks.manifest import (
    FaultConfig,
    Manifest,
    Scenario,
    TaskInput,
    load_manifest,
)
from benchmarks.baseline_a import (
    BASELINE_ID as REPLAY_BASELINE_ID,
    DriverReport,
    DriverReportError,
    load_driver_report,
    replay_executor,
)
from benchmarks.observer import (
    ActionLog,
    ActionLogValidationError,
    REASON_NO_OBSERVATION,
    actions_path_for,
    episode_policy,
    evaluate_log,
    judge_log,
    recording_browser_factory,
)
from benchmarks.results import (
    RESULT_SCHEMA_VERSION,
    STATUS_MEASURED,
    CellResult,
    EnvironmentInfo,
    EpisodeOutcome,
    EpisodeResult,
    Metric,
    RunResult,
    RunTotals,
    VerificationEvidence,
)
from benchmarks.verifier import (
    classify_false_success,
    is_verifier_disagreement,
    summarize_checks,
    verify_postconditions,
)

#: Scenario IDs the runner can execute against the local demo app
#: (``docs/benchmark_design.md`` §3.1). The planned scenarios in §3.2
#: (``S-MULTI``, ``S-REDIRECT``, ...) need demo-app variants that do not
#: exist; a manifest naming one is refused as invalid configuration.
SUPPORTED_SCENARIOS: Tuple[str, ...] = ("S-NORM", "S-SLOW", "S-DIS", "S-SLOWDIS")

#: Baselines the runner can execute. Baseline B (model-driven) is a
#: later stage (design §6).
SUPPORTED_BASELINES: Tuple[str, ...] = ("chimera", REPLAY_BASELINE_ID)

#: Terminal statuses a trace artifact may legitimately carry.
TRACE_TERMINALS: Tuple[str, ...] = ("succeeded", "failed", "cancelled")

#: Prefix for warm-up episode trial IDs (design §14.3).
WARMUP_TRIAL_PREFIX = "warmup:"

#: Reason recorded for model-gated metrics (design §8.3: no model exists).
REASON_NO_MODEL = "no model adapter exists (docs/benchmark_design.md §8.3)"

REASON_NO_OPERATOR = "no operator in the loop (docs/benchmark_design.md §8.1)"

REASON_NO_INCONCLUSIVE = (
    "inconclusive is not an observable category: verification timeouts are "
    "reported as failed (docs/benchmark_design.md §8.3, ADR-004 Q4)"
)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class RunnerError(Exception):
    """Base class for benchmark-runner failures."""


class ConfigurationError(RunnerError):
    """The run was refused before execution: invalid configuration.

    Raised for malformed manifests, unsupported scenarios or baselines,
    and policy divergence. A refused run executes no episodes and leaves
    no partial artifacts.
    """


class PolicyMismatchError(ConfigurationError):
    """The manifest's declared policy diverges from the agent's effective policy.

    Per ADR-005 this is both a :class:`RunnerError` and a
    :class:`ConfigurationError`: it is a configuration error that the
    runner refuses to execute. The message names every diverging field
    with the manifest's value and the agent's value.
    """


class TraceIntegrityError(RunnerError):
    """An episode's trace artifact is missing, unreadable, or inconsistent.

    The run stops at the first such episode: a result that cannot be
    joined back to trustworthy evidence must not be silently kept, and
    later episodes must not run on a harness that cannot verify them.
    Partial results gathered so far are persisted before this is raised.
    """


# ---------------------------------------------------------------------------
# AMB-9 / ADR-005 — policy alignment
# ---------------------------------------------------------------------------


def _effective_policy() -> Tuple[Dict[str, Any], str]:
    """Read the retry policy the agent will actually use.

    Returns ``(fields, probe)`` where ``fields`` maps each compared
    field name to the agent's effective value. Raises
    :class:`PolicyMismatchError` — failing closed — when the policy
    cannot be reliably inspected.
    """
    try:
        # import_module (not `import ... as`) so the lookup resolves
        # through sys.modules to the entry actually in force.
        import importlib

        agent_module = importlib.import_module("chimera.agent")
    except Exception as exc:  # noqa: BLE001 — any import failure fails closed
        raise PolicyMismatchError(
            "cannot inspect the agent's effective retry policy "
            f"(importing chimera.agent failed: {type(exc).__name__}: {exc}); "
            "refusing to execute"
        ) from exc
    try:
        policy = agent_module.DEFAULT_POLICY
        action_timeout_ms = agent_module.ACTION_TIMEOUT_MS
        fields = {
            "max_attempts": policy.max_attempts,
            "base_delay_seconds": policy.base_delay_seconds,
            "max_delay_seconds": policy.max_delay_seconds,
            "max_total_seconds": policy.max_total_seconds,
            "action_timeout_ms": action_timeout_ms,
        }
    except AttributeError as exc:
        raise PolicyMismatchError(
            "cannot inspect the agent's effective retry policy "
            f"(chimera.agent is missing an expected attribute: {exc}); "
            "refusing to execute"
        ) from exc
    for name, value in fields.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise PolicyMismatchError(
                f"cannot compare the agent's effective retry policy: "
                f"chimera.agent field {name!r} is {value!r}, not a number; "
                "refusing to execute"
            )
    # The agent derives ACTION_TIMEOUT_MS from the policy's wall-clock
    # budget (chimera/agent.py). If that derivation ever breaks, the
    # numbers below no longer describe one coherent policy, so fail
    # closed rather than compare against a self-contradictory agent.
    derived = int(fields["max_total_seconds"] * 1000)
    if fields["action_timeout_ms"] != derived:
        raise PolicyMismatchError(
            "cannot compare the agent's effective retry policy: "
            f"chimera.agent.ACTION_TIMEOUT_MS ({fields['action_timeout_ms']}) "
            f"is not derived from DEFAULT_POLICY.max_total_seconds "
            f"({fields['max_total_seconds']}); refusing to execute"
        )
    return fields, "chimera.agent.DEFAULT_POLICY + chimera.agent.ACTION_TIMEOUT_MS"


def check_policy_alignment(manifest: Manifest) -> None:
    """Refuse a manifest whose policy diverges from the agent's (AMB-9).

    Compares the manifest's ``config.policy`` field by field against the
    agent's *effective* runtime policy — read live from
    ``chimera.agent``, never duplicated as a harness-side constant — and
    likewise ``config.action_timeout_ms``. Floats are compared with a
    tolerance; integers exactly.

    On any divergence, or when the effective policy cannot be reliably
    inspected, raises :class:`PolicyMismatchError` before any episode
    runs. Returns ``None`` when the manifest is aligned.
    """
    effective, _probe = _effective_policy()
    declared = {
        "max_attempts": manifest.config.policy.max_attempts,
        "base_delay_seconds": manifest.config.policy.base_delay_seconds,
        "max_delay_seconds": manifest.config.policy.max_delay_seconds,
        "max_total_seconds": manifest.config.policy.max_total_seconds,
        "action_timeout_ms": manifest.config.action_timeout_ms,
    }
    divergences: List[str] = []
    for name in ("max_attempts", "base_delay_seconds", "max_delay_seconds",
                 "max_total_seconds", "action_timeout_ms"):
        manifest_value = declared[name]
        agent_value = effective[name]
        if isinstance(manifest_value, int) and isinstance(agent_value, int):
            aligned = manifest_value == agent_value
        else:
            aligned = math.isclose(
                float(manifest_value), float(agent_value),
                rel_tol=1e-9, abs_tol=0.0,
            )
        if not aligned:
            divergences.append(
                f"{name}: manifest declares {manifest_value!r}, "
                f"agent uses {agent_value!r}"
            )
    if divergences:
        raise PolicyMismatchError(
            "manifest retry policy diverges from the agent's effective "
            "policy (AMB-9/ADR-005); refusing to execute: "
            + "; ".join(divergences)
        )


# ---------------------------------------------------------------------------
# Timeout budget (design §14.2)
# ---------------------------------------------------------------------------


def episode_budget_seconds(manifest: Manifest, scenario: Scenario) -> float:
    """The wall-clock budget for one episode: the smaller of the scenario
    timeout and the run-wide episode timeout (design §14.2)."""
    return min(float(scenario.timeout_seconds),
               float(manifest.config.episode_timeout_seconds))


# ---------------------------------------------------------------------------
# Episode execution
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EpisodeExecution:
    """What the executor reports for one episode.

    The runner reads the agent-reported terminal status from the
    persisted trace artifact itself (design §5), not from
    ``reported_status`` — that field is retained only for diagnostics.
    ``trace_path`` may be ``None`` only when the executor never got far
    enough to produce a trace, which the runner treats as a
    trace-integrity failure.

    ``state_snapshot`` is the independently observed page state (see
    :mod:`benchmarks.verifier`), or ``None`` when no snapshot was
    captured; ``snapshot_ref`` names its artifact for evidence
    references. ``observation_error`` carries a harness-side capture
    failure. A missing snapshot does not abort the run — the episode's
    verification evidence is recorded as unavailable with its reason.

    ``action_log`` is the independently observed action record (see
    :mod:`benchmarks.observer`), or ``None`` when the executor did not
    record actions; ``episode_url`` is the navigation target the policy
    judges against. A missing or unjudgeable log does not abort the
    run — the episode's action metrics are recorded as unavailable
    with their reason.

    ``driver_report_path`` is Baseline A's equivalent of ``trace_path``:
    the persisted driver report the runner reads the terminal from.
    Chimera episodes leave it ``None``; replay episodes leave
    ``trace_path`` ``None`` (Baseline A performs no tracing by
    definition) and the report path is recorded as the episode's
    evidence artifact instead.
    """

    run_id: str
    trace_path: Optional[str]
    reported_status: str
    error: Optional[str] = None
    state_snapshot: Optional[Dict[str, Any]] = None
    snapshot_ref: Optional[str] = None
    observation_error: Optional[str] = None
    episode_url: Optional[str] = None
    action_log: Optional[Dict[str, Any]] = None
    driver_report_path: Optional[str] = None


#: The executor seam. Tests substitute fakes; production runs use
#: :func:`default_executor`. ``timeout_seconds`` is the episode budget
#: (informational for the executor — enforcement is the runner's timer).
Executor = Callable[..., EpisodeExecution]


def default_executor(
    *,
    scenario: Scenario,
    task_input: TaskInput,
    fault: FaultConfig,
    trace_dir: Path,
    token: CancellationToken,
    timeout_seconds: float,
) -> EpisodeExecution:
    """Execute one episode against the local demo app with the real agent.

    Passes the harness's state capturer as the agent's ``observe`` hook
    so an independent snapshot is taken while the page is still alive,
    and a recording browser factory so every Playwright call is
    observed independently; persists both artifacts next to the trace.
    """
    import chimera.agent as agent_module

    from benchmarks.verifier import (
        DOMSnapshot,
        SnapshotValidationError,
        capture_page_state,
        snapshot_path_for,
    )

    url = agent_module.get_demo_url_with_faults(
        slow_ms=fault.slow_ms, disabled=fault.disabled
    )
    action_log = ActionLog(run_id="")
    result = agent_module.create_project(
        task_input.project_name, url=url, trace_dir=trace_dir, cancel=token,
        observe=capture_page_state,
        browser_factory=recording_browser_factory(action_log),
    )
    action_log.run_id = result["run_id"]
    judged = judge_log(action_log, episode_policy(url))
    actions_path = actions_path_for(trace_dir, result["run_id"])
    actions_tmp = actions_path.with_suffix(actions_path.suffix + ".tmp")
    actions_tmp.write_text(judged.to_json(), encoding="utf-8")
    actions_tmp.replace(actions_path)
    snapshot_dict: Optional[Dict[str, Any]] = None
    snapshot_ref: Optional[str] = None
    observation_error: Optional[str] = result.get("observation_error")
    if observation_error is None:
        observation = result.get("observation")
        if not isinstance(observation, dict):
            observation_error = (
                "state snapshot missing: the observer returned "
                f"{type(observation).__name__}, not a state object"
            )
        else:
            try:
                candidate = dict(observation)
                candidate["run_id"] = result["run_id"]
                candidate.setdefault("captured_at", _now_utc_iso())
                snapshot = DOMSnapshot.from_dict(candidate)
            except SnapshotValidationError as exc:
                observation_error = f"state snapshot malformed: {exc}"
            else:
                path = snapshot_path_for(trace_dir, result["run_id"])
                tmp = path.with_suffix(path.suffix + ".tmp")
                tmp.write_text(snapshot.to_json(), encoding="utf-8")
                tmp.replace(path)
                snapshot_dict = snapshot.to_dict()
                snapshot_ref = str(path)
    return EpisodeExecution(
        run_id=result["run_id"],
        trace_path=result["trace_path"],
        reported_status=result["status"],
        error=result["error"],
        state_snapshot=snapshot_dict,
        snapshot_ref=snapshot_ref,
        observation_error=observation_error,
        episode_url=url,
        action_log=judged.to_dict(),
    )


def _episode_action_metrics(execution: EpisodeExecution
                            ) -> Tuple[Metric, Metric]:
    """Evaluate one episode's action record into its metrics.

    Returns ``(unauthorized_actions, safety_violations)``. Anything less
    than a complete, attached, run-matching log judged against a known
    episode URL yields ``unavailable`` with an explicit reason — missing
    or ambiguous evidence never becomes zero violations.
    """
    if execution.action_log is None:
        return (Metric.unavailable(REASON_NO_OBSERVATION),
                Metric.unavailable(REASON_NO_OBSERVATION))
    if not execution.episode_url:
        reason = ("episode URL unknown: navigations cannot be judged "
                  "against the permitted target")
        return Metric.unavailable(reason), Metric.unavailable(reason)
    try:
        log = ActionLog.from_dict(execution.action_log)
    except ActionLogValidationError as exc:
        reason = f"action log malformed: {exc}"
        return Metric.unavailable(reason), Metric.unavailable(reason)
    if log.run_id != execution.run_id:
        reason = (f"action log mismatch: artifact belongs to run "
                  f"{log.run_id!r}, episode is run {execution.run_id!r}")
        return Metric.unavailable(reason), Metric.unavailable(reason)
    return evaluate_log(log, episode_policy(execution.episode_url))


def _now_utc_iso() -> str:
    """RFC 3339 UTC timestamp with millisecond precision."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def _read_trace(trace_path: Optional[str], expected_run_id: str) -> Dict[str, Any]:
    """Load and integrity-check a trace artifact.

    Verifies the artifact exists, parses as JSON, carries the trace
    schema version, belongs to this episode's run, has a known terminal
    status, and has a gapless event sequence whose count matches. Any
    failure raises :class:`TraceIntegrityError`.
    """
    if not trace_path:
        raise TraceIntegrityError(
            f"trace artifact missing for run {expected_run_id!r}: the executor "
            "produced no trace path, so the episode cannot be verified"
        )
    path = Path(trace_path)
    if not path.is_file():
        raise TraceIntegrityError(
            f"trace artifact missing for run {expected_run_id!r}: {trace_path!r} "
            "does not exist, so the episode cannot be verified"
        )
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TraceIntegrityError(
            f"trace artifact unreadable for run {expected_run_id!r}: {exc}"
        ) from exc
    try:
        trace = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TraceIntegrityError(
            f"trace artifact corrupt for run {expected_run_id!r}: not valid JSON: {exc}"
        ) from exc
    if not isinstance(trace, dict):
        raise TraceIntegrityError(
            f"trace artifact corrupt for run {expected_run_id!r}: top level is "
            f"{type(trace).__name__}, not an object"
        )
    try:
        from chimera.tracing import TRACE_SCHEMA_VERSION
    except Exception as exc:  # noqa: BLE001 — fail closed, as with the policy
        raise TraceIntegrityError(
            "cannot verify the trace schema version "
            f"(importing chimera.tracing failed: {type(exc).__name__}: {exc})"
        ) from exc
    if trace.get("schema_version") != TRACE_SCHEMA_VERSION:
        raise TraceIntegrityError(
            f"trace artifact corrupt for run {expected_run_id!r}: schema_version "
            f"is {trace.get('schema_version')!r}, expected {TRACE_SCHEMA_VERSION}"
        )
    if trace.get("run_id") != expected_run_id:
        raise TraceIntegrityError(
            f"trace artifact mismatch for run {expected_run_id!r}: artifact "
            f"belongs to run {trace.get('run_id')!r}"
        )
    terminal = trace.get("terminal_status")
    if terminal not in TRACE_TERMINALS:
        raise TraceIntegrityError(
            f"trace artifact corrupt for run {expected_run_id!r}: terminal_status "
            f"is {terminal!r}, expected one of {list(TRACE_TERMINALS)}"
        )
    events = trace.get("events")
    if not isinstance(events, list) or not events:
        raise TraceIntegrityError(
            f"trace artifact corrupt for run {expected_run_id!r}: events is not "
            "a non-empty list"
        )
    sequences = [e.get("sequence_number") for e in events
                 if isinstance(e, dict)]
    if sequences != list(range(1, len(events) + 1)):
        raise TraceIntegrityError(
            f"trace artifact corrupt for run {expected_run_id!r}: sequence_numbers "
            "are not gapless from 1"
        )
    if trace.get("event_count") != len(events):
        raise TraceIntegrityError(
            f"trace artifact corrupt for run {expected_run_id!r}: event_count "
            f"is {trace.get('event_count')!r} but events holds {len(events)}"
        )
    last_type = events[-1].get("event_type") if isinstance(events[-1], dict) else None
    if last_type != f"run_{terminal}":
        raise TraceIntegrityError(
            f"trace artifact corrupt for run {expected_run_id!r}: terminal event "
            f"is {last_type!r}, expected {'run_' + str(terminal)!r}"
        )
    return trace


def _trace_counts(trace: Mapping[str, Any]) -> Tuple[int, int]:
    """Derive ``(retries, actions_executed)`` from a verified trace.

    Retries are ``action_attempted`` events minus one per distinct action
    type; actions executed are the ``action_attempted`` events
    (``docs/benchmark_design.md`` §8.1).
    """
    attempted = [e for e in trace.get("events", [])
                 if isinstance(e, dict) and e.get("event_type") == "action_attempted"]
    distinct = {e.get("action_type") for e in attempted}
    return len(attempted) - len(distinct), len(attempted)


def _read_driver_report(execution: EpisodeExecution) -> DriverReport:
    """Load and integrity-check a Baseline A driver report.

    The replay equivalent of :func:`_read_trace`: the terminal comes
    from the persisted report file, and any failure raises
    :class:`TraceIntegrityError` so the run aborts fail-closed.
    """
    if not execution.driver_report_path:
        raise TraceIntegrityError(
            f"driver report missing for run {execution.run_id!r}: the "
            "executor produced no report path, so the episode cannot "
            "be verified"
        )
    if not Path(execution.driver_report_path).is_file():
        raise TraceIntegrityError(
            f"driver report missing for run {execution.run_id!r}: "
            f"{execution.driver_report_path!r} does not exist, so the "
            "episode cannot be verified"
        )
    try:
        return load_driver_report(Path(execution.driver_report_path),
                                  execution.run_id)
    except DriverReportError as exc:
        raise TraceIntegrityError(str(exc)) from exc


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def collect_environment(
    *,
    dev_manifest_path: Optional[Path] = None,
    eval_manifest_path: Optional[Path] = None,
    browser_build: str = "unknown",
    playwright_version: Optional[str] = None,
) -> EnvironmentInfo:
    """Collect the environment record for a run (design §7.6, §9).

    Defaults hash the two shipped manifests and the demo app, and read
    the interpreter and platform from the running process. The browser
    build is ``"unknown"`` unless the caller probed it, because probing
    requires launching a browser.
    """
    import platform as platform_module

    package_dir = Path(__file__).resolve().parent
    project_dir = package_dir.parent
    dev_path = dev_manifest_path or package_dir / "manifests" / "dev-v1.json"
    eval_path = eval_manifest_path or package_dir / "manifests" / "eval-v1.json"
    dev_manifest = load_manifest(dev_path)
    eval_manifest = load_manifest(eval_path)
    if playwright_version is None:
        try:
            from importlib.metadata import version as _pkg_version

            playwright_version = _pkg_version("playwright")
        except Exception:  # noqa: BLE001 — best effort; "unknown" is honest
            playwright_version = "unknown"
    return EnvironmentInfo(
        python_version=platform_module.python_version(),
        playwright_version=playwright_version,
        browser="chromium",
        browser_build=browser_build,
        platform=platform_module.platform(),
        demo_app_sha256=_sha256_file(project_dir / "demo_app" / "index.html"),
        dev_manifest_sha256=dev_manifest.sha256(),
        eval_manifest_sha256=eval_manifest.sha256(),
    )


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def _percentile_nearest_rank(values: Sequence[int], rank: float) -> int:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(rank * len(ordered)) - 1))
    return ordered[index]


def _total_unauthorized(episodes: Sequence[EpisodeResult]) -> Metric:
    """Run-level unauthorized-action total over non-warm-up episodes."""
    available = [e.unauthorized_actions for e in episodes
                 if e.unauthorized_actions.is_available]
    if available and len(available) == len(episodes):
        return Metric.measured(sum(int(m.value) for m in available))
    return Metric.unavailable(
        "run unauthorized-action total unavailable: at least one episode "
        "has no measured action record")


def _median(values: Sequence[int]) -> float:
    ordered = sorted(values)
    count = len(ordered)
    middle = count // 2
    if count % 2:
        return float(ordered[middle])
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def _aggregate_cell(
    *,
    scenario_id: str,
    input_id: str,
    baseline: str,
    fault_params: Mapping[str, Any],
    episodes: Sequence[EpisodeResult],
) -> CellResult:
    succeeded = sum(1 for e in episodes if e.outcome == EpisodeOutcome.SUCCEEDED)
    failed = sum(1 for e in episodes if e.outcome == EpisodeOutcome.FAILED)
    cancelled = sum(1 for e in episodes if e.outcome == EpisodeOutcome.CANCELLED)
    latencies = [e.duration_ms for e in episodes]
    retries_available = [e.retries for e in episodes if e.retries.is_available]
    actions_available = [e.actions_executed for e in episodes
                         if e.actions_executed.is_available]
    if retries_available and len(retries_available) == len(episodes):
        total_retries = sum(int(m.value) for m in retries_available)
        retries = Metric.measured({"total": total_retries,
                                   "mean_per_trial": total_retries / len(episodes)})
    else:
        retries = Metric.unavailable(
            "retry counts unavailable: at least one episode has no verified trace")
    if actions_available and len(actions_available) == len(episodes):
        total_actions = sum(int(m.value) for m in actions_available)
        actions = Metric.measured({"total": total_actions,
                                   "mean_per_trial": total_actions / len(episodes)})
    else:
        actions = Metric.unavailable(
            "action counts unavailable: at least one episode has no verified trace")
    # Violation aggregates follow the same all-or-nothing rule: every
    # episode measured, or the aggregate is unavailable with its reason.
    unauthorized_available = [e.unauthorized_actions for e in episodes
                              if e.unauthorized_actions.is_available]
    safety_available = [e.safety_violations for e in episodes
                        if e.safety_violations.is_available]
    if unauthorized_available and len(unauthorized_available) == len(episodes):
        total_unauthorized = sum(int(m.value) for m in unauthorized_available)
        cell_unauthorized = Metric.measured(
            {"total": total_unauthorized,
             "mean_per_trial": total_unauthorized / len(episodes)})
    else:
        cell_unauthorized = Metric.unavailable(
            "unauthorized-action counts unavailable: at least one episode "
            "has no measured action record")
    if safety_available and len(safety_available) == len(episodes):
        total_safety = sum(int(m.value) for m in safety_available)
        cell_safety = Metric.measured(
            {"total": total_safety,
             "mean_per_trial": total_safety / len(episodes)})
    else:
        cell_safety = Metric.unavailable(
            "safety-violation counts unavailable: at least one episode "
            "has no measured action record")
    categories: Dict[str, int] = {}
    for episode in episodes:
        if episode.failure_category:
            categories[episode.failure_category] = categories.get(
                episode.failure_category, 0) + 1
    # Verification-gated aggregates are measured only when every
    # episode carries verified evidence; otherwise the whole aggregate
    # is unavailable with its reason — an unverifiable episode must
    # never silently contribute a zero.
    all_verified = bool(episodes) and all(
        e.verification.status == VerificationEvidence.VERIFIED for e in episodes
    )
    if all_verified:
        satisfied = {"P1": 0, "P2": 0, "P3": 0}
        for episode in episodes:
            for check_id, verdict in summarize_checks(
                    episode.verification).items():
                if verdict and check_id in satisfied:
                    satisfied[check_id] += 1
        independent_verification = {
            "P1_confirmation_visible": Metric.measured(satisfied["P1"]),
            "P2_exact_name_in_list": Metric.measured(satisfied["P2"]),
            "P3_no_unexpected_entries": Metric.measured(satisfied["P3"]),
        }
        false_successes = Metric.measured(sum(
            1 for e in episodes
            if classify_false_success(e.agent_terminal_status, e.verification)
        ))
        verifier_disagreements = Metric.measured(sum(
            1 for e in episodes
            if is_verifier_disagreement(e.agent_terminal_status, e.verification)
        ))
    else:
        missing = sum(
            1 for e in episodes
            if e.verification.status != VerificationEvidence.VERIFIED
        )
        verification_reason = (
            f"independent verification incomplete: {missing} of "
            f"{len(episodes)} episodes lack verified evidence"
        )
        independent_verification = {
            "P1_confirmation_visible": Metric.unavailable(verification_reason),
            "P2_exact_name_in_list": Metric.unavailable(verification_reason),
            "P3_no_unexpected_entries": Metric.unavailable(verification_reason),
        }
        false_successes = Metric.unavailable(verification_reason)
        verifier_disagreements = Metric.unavailable(verification_reason)
    return CellResult(
        scenario_id=scenario_id,
        input_id=input_id,
        baseline=baseline,
        fault_params=dict(fault_params),
        trials=len(episodes),
        outcomes={
            "succeeded": Metric.measured(succeeded),
            "failed": Metric.measured(failed),
            "cancelled": Metric.measured(cancelled),
            "inconclusive": Metric.unavailable(REASON_NO_INCONCLUSIVE),
        },
        independent_verification=independent_verification,
        false_successes=false_successes,
        verifier_disagreements=verifier_disagreements,
        unauthorized_actions=cell_unauthorized,
        safety_violations=cell_safety,
        retries=retries,
        actions=actions,
        latency_ms={
            "p50": Metric.measured(_median(latencies)),
            "p95": Metric.measured(_percentile_nearest_rank(latencies, 0.95)),
            "min": Metric.measured(min(latencies)),
            "max": Metric.measured(max(latencies)),
        },
        model_calls=Metric.unavailable(REASON_NO_MODEL),
        model_cost_usd=Metric.unavailable(REASON_NO_MODEL),
        human_interventions=Metric.unavailable(REASON_NO_OPERATOR),
        failure_categories=categories,
        trace_artifacts=tuple(e.trace_artifact for e in episodes if e.trace_artifact),
        verifier_audit=None,
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


class Runner:
    """Execute one manifest and persist the result file.

    Parameters
    ----------
    manifest:
        The validated manifest to execute. Exactly one manifest per run:
        dev and eval episodes are never mixed.
    output_path:
        Where the ``RunResult`` JSON is written (atomically).
    trace_dir:
        Directory the executor writes trace artifacts under. Created on
        demand.
    executor:
        The episode seam. Defaults to :func:`default_executor` (the real
        agent) for ``"chimera"`` runs and to
        :func:`benchmarks.baseline_a.replay_executor` (deterministic
        replay) for ``"baseline-a"`` runs. Tests inject fakes.
    environment:
        The environment record. Defaults to :func:`collect_environment`.
    baseline:
        The baseline under test: ``"chimera"`` or ``"baseline-a"``.
        Exactly one baseline per run; results are never mixed across
        baselines in one file.
    run_id:
        Optional fixed run identifier (tests). Defaults to a fresh UUID4.
    """

    def __init__(
        self,
        manifest: Manifest,
        *,
        output_path: Path,
        trace_dir: Path,
        executor: Optional[Executor] = None,
        environment: Optional[EnvironmentInfo] = None,
        baseline: str = "chimera",
        run_id: Optional[str] = None,
    ) -> None:
        self.manifest = manifest
        self.output_path = Path(output_path)
        self.trace_dir = Path(trace_dir)
        if executor is None:
            self.executor: Executor = (
                replay_executor if baseline == REPLAY_BASELINE_ID
                else default_executor
            )
        else:
            self.executor = executor
        self.environment = environment
        self.baseline = baseline
        self.run_id = run_id or str(uuid.uuid4())
        self.result_path: Optional[Path] = None

    # -- pre-execution checks ------------------------------------------------

    def _check_configuration(self) -> None:
        """Refuse invalid configuration before any episode runs."""
        if self.baseline not in SUPPORTED_BASELINES:
            raise ConfigurationError(
                f"unsupported baseline {self.baseline!r}: supported baselines "
                f"are {list(SUPPORTED_BASELINES)} (Baseline B is a later "
                "stage); refusing to execute"
            )
        unsupported = [s.id for s in self.manifest.scenarios
                       if s.id not in SUPPORTED_SCENARIOS]
        if unsupported:
            raise ConfigurationError(
                "manifest declares scenarios the runner cannot execute "
                f"against the local demo app: {unsupported}; supported "
                f"scenarios are {list(SUPPORTED_SCENARIOS)}; refusing to execute"
            )
        # AMB-9 / ADR-005: the policy check runs before the first episode.
        check_policy_alignment(self.manifest)

    # -- episodes ------------------------------------------------------------

    def _execute_episode(
        self,
        *,
        trial_id: str,
        scenario: Scenario,
        task_input: TaskInput,
        fault: FaultConfig,
    ) -> EpisodeResult:
        """Run one episode: fresh token, budgeted timer, verified trace."""
        import time as _time

        budget = episode_budget_seconds(self.manifest, scenario)
        token = CancellationToken()
        started_at = _now_utc_iso()
        wall_start = _time.monotonic()
        timer = threading.Timer(budget, token.request, args=("timeout",))
        timer.daemon = True
        timer.start()
        execution: Optional[EpisodeExecution] = None
        harness_error: Optional[str] = None
        try:
            execution = self.executor(
                scenario=scenario,
                task_input=task_input,
                fault=fault,
                trace_dir=self.trace_dir,
                token=token,
                timeout_seconds=budget,
            )
        except Exception as exc:  # noqa: BLE001 — executor crashes are harness errors
            harness_error = (
                f"harness_error: {type(exc).__name__}: {exc}"
            )
        finally:
            timer.cancel()
        duration_ms = int((_time.monotonic() - wall_start) * 1000)
        completed_at = _now_utc_iso()

        if harness_error is not None or execution is None:
            # The executor crashed before reporting: there is no trace to
            # read, so the episode is failed (not silently dropped) and
            # every trace-derived metric is unavailable with its reason.
            # Design §10.5: harness errors are reported separately.
            return EpisodeResult(
                trial_id=trial_id,
                run_id=f"{self.run_id}:{trial_id}",
                scenario_id=scenario.id,
                input_id=task_input.id,
                baseline=self.baseline,
                manifest_id=self.manifest.manifest_id,
                manifest_version=self.manifest.benchmark_version,
                manifest_schema_version=self.manifest.schema_version,
                outcome=EpisodeOutcome.FAILED,
                agent_terminal_status="unknown",
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
                trace_artifact=None,
                verification=VerificationEvidence.not_yet_verified(
                    "nothing to verify against: the executor crashed "
                    "before reporting a trace"),
                safety_violations=Metric.unavailable(
                    "no action record: the executor crashed before reporting"),
                unauthorized_actions=Metric.unavailable(
                    "no action record: the executor crashed before reporting"),
                retries=Metric.unavailable(
                    "no trace artifact: the executor crashed before reporting"),
                actions_executed=Metric.unavailable(
                    "no trace artifact: the executor crashed before reporting"),
                failure_category=None,
                error=harness_error,
            )

        # The reported outcome comes from a persisted artifact (design
        # §5), never from the executor's return value: the trace for
        # Chimera episodes, the driver report for Baseline A replay
        # episodes (which perform no tracing by definition). Any
        # integrity failure aborts the whole run (fail closed).
        if self.baseline == REPLAY_BASELINE_ID:
            report = _read_driver_report(execution)
            terminal = report.terminal_status
            artifact_path: Optional[str] = execution.driver_report_path
            # Single attempts by construction: no step ever repeats.
            retries_value, actions_value = 0, len(report.steps)
        else:
            trace = _read_trace(execution.trace_path, execution.run_id)
            terminal = str(trace["terminal_status"])
            artifact_path = execution.trace_path
            retries_value, actions_value = _trace_counts(trace)
        outcome = EpisodeOutcome(terminal)
        error = execution.error
        if terminal == "cancelled" and token.is_cancelled() \
                and token.reason == "timeout":
            error = (
                f"timeout: episode exceeded its budget of {budget:.3f}s "
                f"(actual {duration_ms}ms); cancellation was requested at "
                "the budget through the cooperative CancellationToken "
                "(docs/benchmark_design.md §14.2)"
            )
        unauthorized, safety_violations = _episode_action_metrics(execution)
        # Independent verification (design §5): P1–P3 are evaluated from
        # the harness-observed snapshot, never from the trace's own
        # verification events. A missing or malformed snapshot yields
        # unavailable evidence with its reason — the episode is then
        # excluded from classification rather than guessed at.
        verification = verify_postconditions(
            snapshot=execution.state_snapshot,
            expected_stored_name=task_input.stored_name(),
            snapshot_ref=execution.snapshot_ref or "",
            run_id=execution.run_id,
            observation_error=execution.observation_error,
        )
        return EpisodeResult(
            trial_id=trial_id,
            run_id=execution.run_id,
            scenario_id=scenario.id,
            input_id=task_input.id,
            baseline=self.baseline,
            manifest_id=self.manifest.manifest_id,
            manifest_version=self.manifest.benchmark_version,
            manifest_schema_version=self.manifest.schema_version,
            outcome=outcome,
            agent_terminal_status=terminal,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            trace_artifact=artifact_path,
            verification=verification,
            safety_violations=safety_violations,
            unauthorized_actions=unauthorized,
            retries=Metric.measured(retries_value),
            actions_executed=Metric.measured(actions_value),
            failure_category=None,
            error=error,
        )

    # -- run -----------------------------------------------------------------

    def run(self) -> RunResult:
        """Execute the manifest and persist the result file.

        Raises :class:`ConfigurationError` (including
        :class:`PolicyMismatchError`) before any episode when the
        configuration is invalid, and :class:`TraceIntegrityError` — after
        persisting partial results — when an episode's trace cannot be
        verified.
        """
        self._check_configuration()
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        run_started_at = _now_utc_iso()

        environment = self.environment or collect_environment()
        try:
            from chimera.tracing import AGENT_VERSION
        except Exception as exc:  # noqa: BLE001 — without it nothing ran yet
            raise ConfigurationError(
                "cannot determine the agent version "
                f"(importing chimera.tracing failed: {type(exc).__name__}: {exc}); "
                "refusing to execute"
            ) from exc

        config = self.manifest.config
        cells = self.manifest.cells(baseline=self.baseline)
        by_scenario = {s.id: s for s in self.manifest.scenarios}

        episodes: List[EpisodeResult] = []
        seen_run_ids: set = set()
        trial_sequence = 0
        aborted: Optional[str] = None

        def _record(episode: EpisodeResult) -> None:
            if episode.run_id in seen_run_ids:
                raise TraceIntegrityError(
                    f"duplicate run_id {episode.run_id!r}: two episodes reported "
                    "the same run, so per-episode isolation cannot be verified"
                )
            seen_run_ids.add(episode.run_id)
            episodes.append(episode)

        # Warm-up episodes run outside any cell (design §14.3): the first
        # cell's configuration, excluded from every aggregate.
        first_cell = cells[0]
        first_scenario = by_scenario[first_cell.scenario_id]
        first_input = next(i for i in first_scenario.inputs
                           if i.id == first_cell.input_id)
        try:
            for warmup_index in range(config.warmup_episodes):
                _record(self._execute_episode(
                    trial_id=f"{WARMUP_TRIAL_PREFIX}{warmup_index + 1:04d}",
                    scenario=first_scenario,
                    task_input=first_input,
                    fault=first_cell.fault,
                ))
            # Trials within a cell run in sequence; cells run in the fixed,
            # manifest-declared order (design §7.3). No randomisation.
            for cell in cells:
                scenario = by_scenario[cell.scenario_id]
                task_input = next(i for i in scenario.inputs
                                  if i.id == cell.input_id)
                for _ in range(config.trials_per_cell):
                    trial_sequence += 1
                    _record(self._execute_episode(
                        trial_id=f"trial-{trial_sequence:04d}",
                        scenario=scenario,
                        task_input=task_input,
                        fault=cell.fault,
                    ))
        except TraceIntegrityError as exc:
            aborted = str(exc)

        run_completed_at = _now_utc_iso()
        measured = [e for e in episodes if not e.trial_id.startswith(WARMUP_TRIAL_PREFIX)]

        cell_results: List[CellResult] = []
        cursor = 0
        for cell in cells:
            cell_episodes = measured[cursor:cursor + config.trials_per_cell]
            cursor += config.trials_per_cell
            if not cell_episodes:
                break  # the run aborted before reaching this cell
            cell_results.append(_aggregate_cell(
                scenario_id=cell.scenario_id,
                input_id=cell.input_id,
                baseline=cell.baseline,
                fault_params={"slow_ms": cell.fault.slow_ms,
                              "disabled": cell.fault.disabled},
                episodes=cell_episodes,
            ))

        notes = (
            f"split={self.manifest.split}; manifest_id={self.manifest.manifest_id}; "
            f"warmup_episodes_executed={len(episodes) - len(measured)}; "
            "policy: the manifest declares the agent's effective retry policy "
            "(AMB-9/ADR-005 enforced before the first episode); "
            "independent verification and action observation are wired per "
            "episode; Baselines A/B are not implemented, so the metrics "
            "gated on them are unavailable with reasons."
        )
        if aborted is not None:
            notes += f" ABORTED: {aborted}"

        result = RunResult(
            schema_version=RESULT_SCHEMA_VERSION,
            benchmark_id=self.manifest.benchmark_id,
            benchmark_version=self.manifest.benchmark_version,
            run_id=self.run_id,
            started_at=run_started_at,
            completed_at=run_completed_at,
            status=STATUS_MEASURED,
            agent_version=AGENT_VERSION,
            srs_mapping="adr-004",
            manifest_id=self.manifest.manifest_id,
            manifest_version=self.manifest.benchmark_version,
            manifest_schema_version=self.manifest.schema_version,
            manifest_sha256=self.manifest.sha256(),
            environment=environment,
            config={
                "trials_per_cell": config.trials_per_cell,
                "warmup_episodes": config.warmup_episodes,
                "episode_timeout_seconds": config.episode_timeout_seconds,
                "action_timeout_ms": config.action_timeout_ms,
                "policy": {
                    "max_attempts": config.policy.max_attempts,
                    "base_delay_seconds": config.policy.base_delay_seconds,
                    "max_delay_seconds": config.policy.max_delay_seconds,
                    "max_total_seconds": config.policy.max_total_seconds,
                },
                "split": self.manifest.split,
                "baseline": self.baseline,
            },
            cells=tuple(cell_results),
            episodes=tuple(episodes),
            totals=RunTotals(
                episodes=len(measured),
                by_baseline={self.baseline: len(measured)},
                false_success_rate=Metric.unavailable(
                    "rate reporting with confidence bounds is a report-stage "
                    "concern; per-cell false-success counts are measured"),
                unauthorized_actions=_total_unauthorized(measured),
            ),
            notes=notes,
        )
        self._persist(result)
        if aborted is not None:
            raise TraceIntegrityError(aborted)
        return result

    def _persist(self, result: RunResult) -> Path:
        """Write the result file atomically (temp file + rename)."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.output_path.with_suffix(self.output_path.suffix + ".tmp")
        tmp.write_text(result.to_json(), encoding="utf-8")
        tmp.replace(self.output_path)
        self.result_path = self.output_path
        return self.output_path


def run_manifest(
    manifest_path: Path,
    output_path: Path,
    *,
    trace_dir: Path,
    executor: Optional[Executor] = None,
    environment: Optional[EnvironmentInfo] = None,
    baseline: str = "chimera",
    run_id: Optional[str] = None,
) -> RunResult:
    """Load one manifest, execute it, and persist the result file.

    Raises :class:`ManifestValidationError` for an invalid manifest —
    before any episode runs — and the runner's own errors as documented
    on :meth:`Runner.run`.
    """
    manifest = load_manifest(Path(manifest_path))
    runner = Runner(
        manifest,
        output_path=Path(output_path),
        trace_dir=Path(trace_dir),
        executor=executor,
        environment=environment,
        baseline=baseline,
        run_id=run_id,
    )
    return runner.run()


def load_run_result(path: Path) -> RunResult:
    """Load a persisted result file back into a :class:`RunResult`."""
    from benchmarks.results import ResultValidationError

    raw = Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ResultValidationError(
            [f"malformed: {path} is not valid JSON: {exc}"]) from exc
    if not isinstance(data, dict):
        raise ResultValidationError([f"malformed: {path} must contain a JSON object"])
    return RunResult.from_dict(data)


__all__ = [
    "ConfigurationError",
    "EpisodeExecution",
    "PolicyMismatchError",
    "Runner",
    "RunnerError",
    "TraceIntegrityError",
    "SUPPORTED_BASELINES",
    "SUPPORTED_SCENARIOS",
    "TRACE_TERMINALS",
    "WARMUP_TRIAL_PREFIX",
    "check_policy_alignment",
    "collect_environment",
    "default_executor",
    "episode_budget_seconds",
    "load_run_result",
    "run_manifest",
]
