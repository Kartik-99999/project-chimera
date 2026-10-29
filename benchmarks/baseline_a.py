"""Baseline A — deterministic replay driver (benchmark harness).

A scripted driver that performs the fixed steps — navigate, fill, click
— with fixed locators and **no** adaptive waiting, no retry, no fault
awareness, and no tracing. It is scored by the same independent
verifier as Chimera (``docs/benchmark_design.md`` §6).

Authority
---------
``docs/benchmark_design.md`` §6 (definition, purpose, and prediction)
and §6.1 (attribution: with only Baseline A available, the A-vs-C
difference is attributable to **waiting + retry + verification** and
to nothing else). SRS §11.3, via §6, requires the same scenarios with
comparable execution limits.

What "no waiting" means here
----------------------------
Fill and click run with a fixed, tiny Playwright timeout
(:data:`REPLAY_ACTION_TIMEOUT_MS`): they act on the controls'
instantaneous state instead of waiting for them to become ready. (Note
that Playwright ``timeout=0`` would mean the opposite — it disables
the timeout and waits indefinitely — so a small positive value is
required.) The value sits below the manifest slow band's 500 ms
minimum, so replay can never wait out a transient fault, yet tolerates
scheduling jitter on the instantly-ready normal path. On ``S-NORM``
the controls are already enabled, so replay succeeds; on ``S-SLOW``
the fill runs while the controls are still disabled and fails
immediately — the design's prediction (observed at the fill step,
which precedes click in the fixed order).
Navigation keeps the default load wait (loading a ``file://`` page is
not control-waiting).

Deliberate non-differences from Chimera episodes
------------------------------------------------
* Each episode gets its own browser and context (isolation parity).
* The cancellation token is checked between steps, so episode budgets
  stay enforceable and a timeout records ``cancelled`` as usual.
* The page is wrapped in the harness's :class:`RecordingPage`, so the
  same action observer judges replay episodes.
* A state snapshot is captured with the same
  :func:`capture_page_state` before teardown, so the same independent
  verifier scores replay episodes.

Deliberate differences
----------------------
* One attempt per step, no retries: measured retries are always 0.
* No postcondition waits, no screenshots, no Chimera trace events.
  Instead of a trace, each episode persists a minimal **driver
  report** (schema ``baseline-a-replay/1``): run ID, terminal status,
  the steps attempted with per-step outcomes, and timestamps. The
  runner reads the reported terminal from that persisted artifact —
  never from an in-memory return — and integrity-checks it the way
  it checks traces.

Harness artifact, not production code: this module must never be
added to ``chimera/``. It imports Playwright lazily (inside the run
function) so unit tests can drive it with fake pages.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from benchmarks.observer import (
    ActionLog,
    RecordingPage,
    actions_path_for,
    episode_policy,
    judge_log,
)
from benchmarks.verifier import (
    DOMSnapshot,
    SnapshotValidationError,
    capture_page_state,
    snapshot_path_for,
)

#: Baseline identifier recorded in cells, episodes, and run configs.
BASELINE_ID = "baseline-a"

#: Driver-report schema identifier.
REPORT_SCHEMA = "baseline-a-replay/1"

#: Filename suffix for driver-report artifacts.
REPLAY_SUFFIX = ".replay.json"

#: Fixed steps, in order. Each is attempted at most once per episode.
STEP_NAVIGATE = "navigate"
STEP_FILL = "fill"
STEP_CLICK = "click"
STEPS: Tuple[str, ...] = (STEP_NAVIGATE, STEP_FILL, STEP_CLICK)

#: Fixed per-action timeout for replay fill/click, in milliseconds.
#: Small enough to never wait out a transient fault (slow band starts
#: at 500 ms), large enough for the instantly-ready normal path.
REPLAY_ACTION_TIMEOUT_MS = 100

#: Terminal statuses a driver report may carry.
TERMINALS: Tuple[str, ...] = ("succeeded", "failed", "cancelled")


class DriverReportError(ValueError):
    """A Baseline A driver report is missing or fails validation."""


# ---------------------------------------------------------------------------
# Driver report schema
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReplayStep:
    """One fixed step as attempted: what, on which target, what happened."""

    step: str
    target: str
    outcome: str
    error_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "target": self.target,
            "outcome": self.outcome,
            "error_type": self.error_type,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ReplayStep":
        if not isinstance(data, Mapping):
            raise DriverReportError(
                f"replay step must be an object, got {type(data).__name__}")
        step = data.get("step")
        if step not in STEPS:
            raise DriverReportError(f"replay step {step!r} is not a fixed step")
        target = data.get("target")
        if not isinstance(target, str) or not target.strip():
            raise DriverReportError(
                f"replay step target must be a non-empty string, "
                f"got {target!r}")
        outcome = data.get("outcome")
        if outcome not in ("ok", "error"):
            raise DriverReportError(
                f"replay step outcome must be ok/error, got {outcome!r}")
        error_type = data.get("error_type")
        if error_type is not None and not isinstance(error_type, str):
            raise DriverReportError(
                f"replay step error_type must be a string, got {error_type!r}")
        return cls(step=step, target=target, outcome=outcome,
                   error_type=error_type)


@dataclass(frozen=True)
class DriverReport:
    """The persisted record of one replay episode.

    The runner treats this the way it treats a trace: the terminal
    status comes from this file, and any integrity failure aborts the
    run. Single-attempt order is structural — steps appear at most
    once, in fixed order.
    """

    schema: str
    run_id: str
    terminal_status: str
    steps: Tuple[ReplayStep, ...]
    started_at: str
    completed_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": self.schema,
            "run_id": self.run_id,
            "terminal_status": self.terminal_status,
            "steps": [s.to_dict() for s in self.steps],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "attempts_per_step": 1,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True,
                           ensure_ascii=False) + "\n"

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DriverReport":
        if not isinstance(data, Mapping):
            raise DriverReportError(
                f"driver report must be an object, got {type(data).__name__}")
        if data.get("schema") != REPORT_SCHEMA:
            raise DriverReportError(
                f"driver report schema is {data.get('schema')!r}, "
                f"expected {REPORT_SCHEMA!r}")
        run_id = data.get("run_id")
        if not isinstance(run_id, str) or not run_id.strip():
            raise DriverReportError(
                f"driver report run_id must be a non-empty string, "
                f"got {run_id!r}")
        terminal = data.get("terminal_status")
        if terminal not in TERMINALS:
            raise DriverReportError(
                f"driver report terminal_status is {terminal!r}, expected "
                f"one of {list(TERMINALS)}")
        raw_steps = data.get("steps")
        if not isinstance(raw_steps, list):
            raise DriverReportError(
                "driver report steps must be a list")
        if not raw_steps and terminal != "cancelled":
            raise DriverReportError(
                f"driver report terminal is {terminal!r} with no steps "
                "attempted: only a pre-start cancellation may attempt nothing")
        steps = tuple(ReplayStep.from_dict(s) for s in raw_steps)
        names = [s.step for s in steps]
        if len(set(names)) != len(names):
            raise DriverReportError(
                f"driver report repeats a step: {names!r} "
                "(Baseline A attempts each step at most once)")
        if names != [s for s in STEPS if s in names]:
            raise DriverReportError(
                f"driver report steps out of fixed order: {names!r}")
        for key in ("started_at", "completed_at"):
            if not isinstance(data.get(key), str):
                raise DriverReportError(
                    f"driver report {key} must be a string")
        return cls(schema=REPORT_SCHEMA, run_id=run_id,
                   terminal_status=terminal, steps=steps,
                   started_at=data["started_at"],
                   completed_at=data["completed_at"])

    @classmethod
    def from_json(cls, raw: str) -> "DriverReport":
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise DriverReportError(
                f"driver report is not valid JSON: {exc}") from exc
        return cls.from_dict(data)


def replay_path_for(trace_dir: Path, run_id: str) -> Path:
    """The driver-report artifact path for an episode's run."""
    return Path(trace_dir) / f"{run_id}{REPLAY_SUFFIX}"


def load_driver_report(path: Path, expected_run_id: str) -> DriverReport:
    """Load and integrity-check a driver report (fail closed)."""
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise DriverReportError(
            f"driver report unreadable for run {expected_run_id!r}: "
            f"{path}: {exc}") from exc
    try:
        report = DriverReport.from_json(raw)
    except DriverReportError as exc:
        raise DriverReportError(
            f"driver report corrupt for run {expected_run_id!r}: {exc}"
        ) from exc
    if report.run_id != expected_run_id:
        raise DriverReportError(
            f"driver report mismatch for run {expected_run_id!r}: artifact "
            f"belongs to run {report.run_id!r}")
    return report


# ---------------------------------------------------------------------------
# Replay driver
# ---------------------------------------------------------------------------


def _now_utc_iso() -> str:
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


@dataclass
class ReplayOutcome:
    """Everything one replay episode produced (in-memory carrier).

    The runner re-reads the terminal from the persisted report file;
    these fields carry the artifacts and evidence to persist or judge.
    """

    run_id: str
    terminal_status: str
    report_path: str
    snapshot: Optional[Dict[str, Any]]
    snapshot_ref: Optional[str]
    observation_error: Optional[str]
    action_log: Dict[str, Any]
    error: Optional[str]


def run_replay(
    *,
    project_name: str,
    url: str,
    trace_dir: Path,
    token: Any = None,
    page_factory: Optional[Callable[[], Tuple[Any, Any, Any]]] = None,
    run_id: Optional[str] = None,
) -> ReplayOutcome:
    """Run one Baseline A episode: navigate, fill, click — once each.

    ``page_factory`` replaces browser acquisition for tests
    (``() -> (browser, context, page)``); when omitted, a real Chromium
    is launched with its own context. ``token`` is an optional
    cancellation token checked between steps. Artifacts (driver
    report, snapshot, action log) are persisted under ``trace_dir``.
    """
    from chimera.safety import RunCancelledError

    run_id = run_id or str(uuid.uuid4())
    trace_dir = Path(trace_dir)
    trace_dir.mkdir(parents=True, exist_ok=True)
    started_at = _now_utc_iso()
    log = ActionLog(run_id=run_id)
    steps: List[ReplayStep] = []
    terminal = "succeeded"
    error: Optional[str] = None

    def _check_cancel() -> None:
        if token is not None:
            token.check()

    if page_factory is None:
        from playwright.sync_api import sync_playwright

        playwright_context = sync_playwright()
        playwright = playwright_context.__enter__()
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        raw_page = context.new_page()
        owned = True
    else:
        playwright_context = None
        playwright = None
        browser, context, raw_page = page_factory()
        owned = False
    page = RecordingPage(raw_page, log)

    def _attempt(step: str, target: str, func: Callable[[], Any]) -> bool:
        """Attempt one fixed step, exactly once. Returns True on success."""
        nonlocal terminal, error
        try:
            func()
        except Exception as exc:  # noqa: BLE001 — step failure is the outcome
            steps.append(ReplayStep(step=step, target=target,
                                    outcome="error",
                                    error_type=type(exc).__name__))
            terminal = "failed"
            error = f"{type(exc).__name__}: {exc}"
            return False
        steps.append(ReplayStep(step=step, target=target, outcome="ok"))
        return True

    try:
        _check_cancel()
        alive = _attempt(STEP_NAVIGATE, url, lambda: page.goto(url))
        if alive:
            _check_cancel()
            name_input = page.get_by_label("Project Name")
            alive = _attempt(
                STEP_FILL, 'label "Project Name"',
                lambda: name_input.fill(
                    project_name, timeout=REPLAY_ACTION_TIMEOUT_MS),
            )
        if alive:
            _check_cancel()
            create_button = page.get_by_role("button", name="Create Project")
            _attempt(STEP_CLICK, 'button "Create Project"',
                     lambda: create_button.click(
                         timeout=REPLAY_ACTION_TIMEOUT_MS))
    except RunCancelledError as exc:
        terminal = "cancelled"
        error = f"RunCancelledError: {exc}"
    finally:
        snapshot_dict: Optional[Dict[str, Any]] = None
        snapshot_ref: Optional[str] = None
        observation_error: Optional[str] = None
        try:
            observation = capture_page_state(page)
        except Exception as exc:  # noqa: BLE001 — reported, not fatal
            observation_error = f"{type(exc).__name__}: {exc}"
        else:
            try:
                candidate = dict(observation)
                candidate["run_id"] = run_id
                candidate.setdefault("captured_at", _now_utc_iso())
                snapshot = DOMSnapshot.from_dict(candidate)
            except SnapshotValidationError as exc:
                observation_error = f"state snapshot malformed: {exc}"
            else:
                snap_path = snapshot_path_for(trace_dir, run_id)
                snap_tmp = snap_path.with_suffix(snap_path.suffix + ".tmp")
                snap_tmp.write_text(snapshot.to_json(), encoding="utf-8")
                snap_tmp.replace(snap_path)
                snapshot_dict = snapshot.to_dict()
                snapshot_ref = str(snap_path)
        try:
            context.close()
        finally:
            browser.close()
            if owned and playwright_context is not None:
                playwright_context.__exit__(None, None, None)

    completed_at = _now_utc_iso()
    report = DriverReport(
        schema=REPORT_SCHEMA, run_id=run_id, terminal_status=terminal,
        steps=tuple(steps), started_at=started_at,
        completed_at=completed_at,
    )
    report_path = replay_path_for(trace_dir, run_id)
    report_tmp = report_path.with_suffix(report_path.suffix + ".tmp")
    report_tmp.write_text(report.to_json(), encoding="utf-8")
    report_tmp.replace(report_path)
    judged = judge_log(log, episode_policy(url))
    actions_path = actions_path_for(trace_dir, run_id)
    actions_tmp = actions_path.with_suffix(actions_path.suffix + ".tmp")
    actions_tmp.write_text(judged.to_json(), encoding="utf-8")
    actions_tmp.replace(actions_path)
    return ReplayOutcome(
        run_id=run_id, terminal_status=terminal,
        report_path=str(report_path), snapshot=snapshot_dict,
        snapshot_ref=snapshot_ref, observation_error=observation_error,
        action_log=judged.to_dict(), error=error,
    )


# ---------------------------------------------------------------------------
# Runner executor adapter
# ---------------------------------------------------------------------------


def replay_url(fault: Any) -> str:
    """The demo-app URL for a fault config, built harness-side.

    Deliberately not reused from ``chimera.agent``: Baseline A is a
    harness artifact and must not import the agent. Parity with the
    agent's URL builder is pinned by
    ``tests/test_baseline_a.py::test_replay_url_matches_agent_url``,
    so any drift fails loudly instead of running replay against a
    different page than Chimera.
    """
    from urllib.parse import urlencode

    demo_app = Path(__file__).resolve().parent.parent / "demo_app" / "index.html"
    params = fault.url_params()
    if not params:
        return f"file://{demo_app}"
    return f"file://{demo_app}?{urlencode(params)}"


def replay_executor(
    *,
    scenario: Any,
    task_input: Any,
    fault: Any,
    trace_dir: Path,
    token: Any,
    timeout_seconds: float,
) -> Any:
    """Execute one Baseline A episode (the runner's executor seam)."""
    from benchmarks.runner import EpisodeExecution

    del scenario, timeout_seconds  # fixed steps; budget enforced by the runner
    url = replay_url(fault)
    outcome = run_replay(
        project_name=task_input.project_name, url=url,
        trace_dir=Path(trace_dir), token=token,
    )
    return EpisodeExecution(
        run_id=outcome.run_id,
        trace_path=None,
        reported_status=outcome.terminal_status,
        error=outcome.error,
        state_snapshot=outcome.snapshot,
        snapshot_ref=outcome.snapshot_ref,
        observation_error=outcome.observation_error,
        episode_url=url,
        action_log=outcome.action_log,
        driver_report_path=outcome.report_path,
    )


__all__ = [
    "BASELINE_ID",
    "REPORT_SCHEMA",
    "REPLAY_ACTION_TIMEOUT_MS",
    "REPLAY_SUFFIX",
    "STEP_CLICK",
    "STEP_FILL",
    "STEP_NAVIGATE",
    "STEPS",
    "TERMINALS",
    "DriverReport",
    "DriverReportError",
    "ReplayOutcome",
    "ReplayStep",
    "load_driver_report",
    "replay_executor",
    "replay_path_for",
    "replay_url",
    "run_replay",
]
