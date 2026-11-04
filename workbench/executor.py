"""Real browser execution for workbench runs.

One execution = one worker thread driving real Chromium through either
the Chimera agent (:func:`chimera.agent.create_project`) or the
Baseline A replay driver (:func:`benchmarks.baseline_a.run_replay`),
both pointed at the bundled Demo Task Manager. Independent action
observation (``benchmarks.observer``) feeds the live monitor; the
independent verifier (``benchmarks.verifier``) judges P1–P3 from a
snapshot captured before teardown. Nothing here is simulated: phases,
durations, errors, and screenshots all come from the live run.

Progress is cooperative: a monitor thread samples the shared action
log while the driver runs, and cancellation flows through
:class:`chimera.safety.CancellationToken` at safe boundaries.
"""

from __future__ import annotations

import json
import threading
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional

from adapters import saucedemo as sauce_adapter
from adapters import flipkart as flipkart_adapter
from adapters import wikipedia as wiki_adapter
from adapters import wiktionary as wikt_adapter
from adapters import pypi as pypi_adapter
from adapters import bbc as bbc_adapter
from adapters import github as github_adapter
from adapters import crates as crates_adapter
from adapters import weather as weather_adapter
from adapters import github_search as gsearch_adapter
from adapters import steam as steam_adapter
from adapters import arxiv as arxiv_adapter
from adapters import stackoverflow as so_adapter
from adapters import amazon as amazon_adapter
from workbench import sessions as session_module
from benchmarks.baseline_a import (
    run_contact_replay,
    run_replay,
    run_saucedemo_replay,
    run_saucedemo_stress_replay,
)
from benchmarks.observer import (
    ActionLog,
    ActionPolicy,
    RecordingPage,
    episode_policy,
    judge_log,
)
from benchmarks.verifier import (
    CONTACT_LIST_SELECTOR,
    PROJECT_LIST_SELECTOR,
    capture_page_state,
    verify_postconditions,
)
from chimera.agent import (
    contact_entry_text,
    create_project,
    get_contact_url_with_faults,
    get_demo_url_with_faults,
    run_amazon_price,
    run_arxiv_search,
    run_bbc_headlines,
    run_bbc_weather,
    run_crates_lookup,
    run_flipkart_add_to_cart,
    run_github_profile,
    run_github_search,
    run_steam_price,
    run_saucedemo_order,
    run_so_search,
    run_pypi_lookup,
    run_wikipedia_lookup,
    run_wiktionary_lookup,
    submit_contact_form,
)
from chimera.safety import CancellationToken
from workbench.store import Store, utcnow
from workbench.workflows import (
    SCENARIO_FAULTS,
    WorkflowValidationError,
    get_workflow,
)

CHIMERA_ACTION_TIMEOUT_MS = 5000  # fixed agent default; not overridable

#: Wall-clock budget for one run. Hostile pages can stall even
#: timeout-bearing protocol calls indefinitely (observed: a text
#: read with timeout=8000 wedged ~16 min on an Amazon gate page),
#: so the monitor enforces this outer bound: past it the run is
#: marked timed-out honestly and the wedged worker is abandoned
#: (daemon thread; dies with the server process).
RUN_TIMEOUT_S = 600.0

# error_type -> failure_category taxonomy for analytics.
_FAILURE_TOKENS = (
    ("timeout", "timeout"),
    ("retrybudgetexhausted", "retry-exhausted"),
    ("blindretryrefused", "retry-exhausted"),
    ("cancelled", "cancelled"),
    ("tracewrite", "missing-evidence"),
    ("snapshot", "missing-evidence"),
    ("targetclosed", "browser-error"),
)


def classify_failure(error_type: Optional[str]) -> Optional[str]:
    if not error_type:
        return None
    lowered = error_type.lower()
    for token, category in _FAILURE_TOKENS:
        if token in lowered:
            return category
    return "action-error"


def _screenshot_name(exec_id: str) -> str:
    return f"{exec_id}.png"


class _ShotOnClose:
    """Context wrapper that screenshots final state before closing.

    Both drivers close the context exactly once during teardown; the
    screenshot therefore shows the page the verdict was judged from.
    Any capture failure is recorded, never fatal.
    """

    def __init__(self, context: Any, page: Any, path: Path):
        self._context = context
        self._page = page
        self._path = path
        self.error: Optional[str] = None
        self.taken = False

    def close(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            # Explicit timeout: a wedged page must not stall teardown.
            self._page.screenshot(path=str(self._path), timeout=8000)
            self.taken = True
        except Exception as exc:  # noqa: BLE001 — evidence best-effort
            self.error = f"{type(exc).__name__}: {exc}"
        finally:
            self._context.close()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._context, name)


def real_chimera_factory(log: ActionLog, shot_path: Path) -> Callable:
    """Browser factory for the agent hook: real Chromium + recorder."""

    def factory(playwright: Any) -> tuple:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        raw_page = context.new_page()
        page = RecordingPage(raw_page, log)
        holder["shot"] = _ShotOnClose(context, raw_page, shot_path)
        return browser, holder["shot"], page

    holder: Dict[str, Any] = {}
    factory.holder = holder  # type: ignore[attr-defined]
    return factory


def real_baseline_factory(log: ActionLog, shot_path: Path,
                          holder: Dict[str, Any]) -> Callable:
    """Page factory for the replay hook: real Chromium + recorder."""

    def factory() -> tuple:
        from playwright.sync_api import sync_playwright
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        raw_page = context.new_page()
        holder.update(shot=_ShotOnClose(context, raw_page, shot_path),
                      playwright=playwright, browser=browser)
        return browser, holder["shot"], RecordingPage(raw_page, log)

    return factory


class Executor:
    """Runs workbench executions on worker threads."""

    def __init__(self, store: Store, root: Path | str,
                 chimera_factory: Optional[Callable] = None,
                 baseline_factory: Optional[Callable] = None,
                 run_timeout_s: float = RUN_TIMEOUT_S,
                 max_workers: int = 2):
        self._store = store
        self._root = Path(root)
        self._traces = self._root / "traces"
        self._shots = self._root / "screenshots"
        self._traces.mkdir(parents=True, exist_ok=True)
        self._shots.mkdir(parents=True, exist_ok=True)
        self.shots_dir = self._shots
        self._chimera_factory = chimera_factory or real_chimera_factory
        self._custom_chimera_factory = chimera_factory is not None
        self._baseline_factory = baseline_factory or real_baseline_factory
        self._run_timeout_s = run_timeout_s
        self._run_slots = threading.Semaphore(max(1, max_workers))
        self._timed_out: set = set()
        self._tokens: Dict[str, CancellationToken] = {}
        self._lock = threading.Lock()
        self._reap_orphaned_runs()

    def _reap_orphaned_runs(self) -> int:
        """Fail runs left behind by a dead server.

        No run thread survives a restart, so any execution still
        marked queued/running belongs to a previous process. It is
        marked failed with insufficient evidence (outcome genuinely
        unknown) instead of lingering as a zombie. Single-owner DB
        assumed, same as campaigns.recover().
        """
        count = 0
        page = 1
        while True:
            index = self._store.list_executions(
                filters={"status": ["queued", "running"]},
                sort="+created_at", page=page, page_size=200)
            rows = index.get("rows", [])
            if not rows:
                break
            for row in rows:
                try:
                    progress = {"phase": "aborted",
                                "started_at": utcnow()}
                    self._store.update_execution(row["id"], {
                        "status": "failed",
                        "verdict": "insufficient-evidence",
                        "completed_at": utcnow(),
                        "error": ("server restarted before the run "
                                  "finished; outcome unknown"),
                        "error_type": "ServerRestart",
                        "progress_json": json.dumps(progress),
                    })
                    count += 1
                except Exception:  # noqa: BLE001 — one bad row skips
                    continue
            if len(rows) < 200:
                break
            page += 1
        return count

    # -- public API ---------------------------------------------------

    def submit(self, workflow_id: str, driver: str,
             params: Mapping[str, Any],
             campaign_id: Optional[str] = None,
             trial_seq: Optional[int] = None,
             trial_kind: Optional[str] = None,
             profile: Optional[str] = None,
             sequence_id: Optional[str] = None,
             step_seq: Optional[int] = None) -> str:
        if workflow_id.startswith("studio:"):
            if profile:
                raise WorkflowValidationError(
                    "studio workflows run on clean sessions only")
            return self._submit_studio(
                workflow_id[len("studio:"):], driver, params or {},
                campaign_id, trial_seq, trial_kind,
                sequence_id, step_seq)
        workflow = get_workflow(workflow_id)
        if driver not in workflow.drivers:
            raise WorkflowValidationError(
                f"driver {driver!r} is not supported for {workflow_id!r}")
        session_factory = None
        if profile:
            if "user" not in workflow.sessions:
                raise WorkflowValidationError(
                    f"{workflow_id!r} does not support user sessions")
            session_factory = session_module.profile_browser_factory(profile)
            session_label = f"user:{session_module.check_profile_name(profile)}"
        else:
            session_label = "clean"
        cleaned = workflow.validate(params or {})
        timeout_override = int(cleaned.get("action_timeout_ms") or 0)
        if driver == "chimera" and timeout_override:
            raise WorkflowValidationError(
                "Chimera uses its fixed 5 s per-action timeout; the "
                "override applies to Baseline A only")
        spec = _run_spec(workflow_id, cleaned)
        spec["session_factory"] = session_factory
        if "scenario" in cleaned:
            faults = SCENARIO_FAULTS[cleaned["scenario"]]
            slow_ms = (cleaned["slow_ms"] if faults["slow_ms"] is None
                       else faults["slow_ms"])
            disabled = faults["disabled"]
            scenario_id = _scenario_id(cleaned["scenario"])
            progress_params = {**cleaned, "slow_ms": slow_ms,
                               "disabled": disabled}
        else:
            # Workflows without page-condition scenarios (e.g. the
            # external store) carry their own fixed target and id.
            slow_ms, disabled = 0, False
            scenario_id = spec["scenario_id"]
            progress_params = dict(cleaned)
        exec_id = self._store.create_execution({
            "workflow_id": workflow_id,
            "driver": driver,
            "origin": workflow.origin,
            "session": session_label,
            "scenario_id": scenario_id,
            "trial_kind": trial_kind or "adhoc",
            "campaign_id": campaign_id,
            "trial_seq": trial_seq,
            "sequence_id": sequence_id,
            "step_seq": step_seq,
            "project_name": spec["label"],
            "status": "queued",
            "progress_json": json.dumps({
                "phase": "queued", "started_at": utcnow(),
                "actions_seen": 0,
                "params": progress_params,
            }),
        })
        token = CancellationToken()
        with self._lock:
            self._tokens[exec_id] = token
        thread = threading.Thread(
            target=self._run,
            args=(exec_id, workflow_id, driver, spec, slow_ms,
                  disabled, timeout_override, token,
                  progress_params),
            name=f"workbench-{exec_id[:8]}",
            daemon=True,
        )
        thread.start()
        return exec_id

    def _submit_studio(self, studio_id: str, driver: str,
                       params: Mapping[str, Any],
                       campaign_id: Optional[str],
                       trial_seq: Optional[int],
                       trial_kind: Optional[str],
                       sequence_id: Optional[str] = None,
                       step_seq: Optional[int] = None) -> str:
        from workbench import studio as studio_module

        if driver not in ("chimera", "baseline-a"):
            raise WorkflowValidationError(
                f"driver {driver!r} is not supported for studio workflows")
        if not isinstance(params, Mapping):
            raise WorkflowValidationError("studio params must be an object")
        variables = params.get("variables") or {}
        if not isinstance(variables, Mapping):
            raise WorkflowValidationError(
                "studio variables must be an object")
        record = self._store.get_studio_workflow(studio_id)
        if record is None:
            raise WorkflowValidationError(
                f"unknown studio workflow {studio_id!r}")
        version = params.get("version")
        if version is not None:
            try:
                version = int(version)
            except (TypeError, ValueError):
                raise WorkflowValidationError(
                    "studio version must be a whole number") from None
            record = self._store.get_studio_workflow(studio_id, version)
        definition = (record or {}).get("definition")
        if definition is None:
            raise WorkflowValidationError(
                "studio workflow has no saved version yet")
        definition = {**definition,
                      "environment": record["environment"],
                      "env_params": record.get("env_params") or {}}
        problems = studio_module.validate_definition(definition)
        if problems:
            raise WorkflowValidationError(
                f"studio definition invalid: "
                f"{problems[0]['message']}")
        try:
            values = studio_module.resolve_variables(
                definition, dict(variables))
        except studio_module.StudioError as exc:
            raise WorkflowValidationError(str(exc)) from None
        secrets = studio_module.secret_values(definition, values)
        shown = {k: (studio_module.REDACTED if v in secrets else v)
                 for k, v in values.items()}
        environment = definition["environment"]
        origin = "external" if environment == "saucedemo" else "local"
        scenario_id = (f"studio:{environment}:v{record['version']}")
        cleaned_params = {"workflow_name": record["name"],
                          "version": record["version"],
                          "variables": shown}
        spec = {
            "label": record["name"],
            "expected": {"steps": [
                {"key": s.get("key", f"s{i}"), "order": i,
                 "type": s.get("type"), "label": s.get("label", "")}
                for i, s in enumerate(
                    definition.get("steps", []), start=1)]},
            "submitted": {"variables": shown,
                          "version": record["version"]},
            "scenario_id": scenario_id,
            "verify": "studio",
            "policy": studio_module.build_policy(definition),
            "snapshot_page": studio_module.capture_end_state,
            "url": "",
            "chimera": (
                lambda url, token, observe, factory, trace_dir,
                _d=definition, _v=dict(values): (
                    studio_module.run_studio_chimera(
                        definition=_d, variables=_v,
                        trace_dir=trace_dir, token=token,
                        observe=observe, browser_factory=factory,
                        screenshots_dir=self._shots))),
            "baseline": (
                lambda url, token, factory, exec_id, timeout_override,
                trace_dir, _d=definition, _v=dict(values): (
                    studio_module.run_studio_replay(
                        definition=_d, variables=_v,
                        trace_dir=trace_dir, token=token,
                        page_factory=factory, run_id=exec_id,
                        screenshots_dir=self._shots))),
        }
        exec_id = self._store.create_execution({
            "workflow_id": studio_module.studio_workflow_id(studio_id),
            "driver": driver,
            "origin": origin,
            "scenario_id": scenario_id,
            "trial_kind": trial_kind or "adhoc",
            "campaign_id": campaign_id,
            "trial_seq": trial_seq,
            "sequence_id": sequence_id,
            "step_seq": step_seq,
            "project_name": spec["label"],
            "status": "queued",
            "progress_json": json.dumps({
                "phase": "queued", "started_at": utcnow(),
                "actions_seen": 0,
                "params": cleaned_params,
            }),
        })
        token = CancellationToken()
        with self._lock:
            self._tokens[exec_id] = token
        thread = threading.Thread(
            target=self._run,
            args=(exec_id, studio_module.studio_workflow_id(studio_id),
                  driver, spec, 0, False, 0, token, cleaned_params),
            name=f"workbench-{exec_id[:8]}",
            daemon=True,
        )
        thread.start()
        return exec_id

    def cancel(self, exec_id: str) -> bool:
        with self._lock:
            token = self._tokens.get(exec_id)
        record = self._store.get_execution(exec_id)
        if record is None or token is None:
            return False
        if record["status"] not in ("queued", "running"):
            return False
        token.request(f"user cancelled execution {exec_id}")
        return True

    def running(self) -> List[str]:
        with self._lock:
            return list(self._tokens)

    # -- worker -------------------------------------------------------

    def _run(self, exec_id: str, workflow_id: str, driver: str,
             spec: Dict[str, Any], slow_ms: int, disabled: bool,
             timeout_override: int, token: CancellationToken,
             progress_params: Optional[Dict[str, Any]] = None) -> None:
        started = time.monotonic()
        log = ActionLog(run_id=exec_id)
        progress = {"phase": "launching", "started_at": utcnow(),
                    "actions_seen": 0, "submitted": spec.get("submitted"),
                    "params": progress_params or {}}
        stop = threading.Event()
        monitor = threading.Thread(
            target=self._monitor,
            args=(exec_id, log, progress, stop, token, started,
                  self._run_timeout_s),
            name=f"workbench-mon-{exec_id[:8]}", daemon=True)
        # Process-wide bound on concurrently running browsers: extra
        # submits wait here with status "queued" instead of each
        # launching a Chromium.
        self._run_slots.acquire()
        try:
            if token.is_cancelled():
                self._store.update_execution(exec_id, {
                    "status": "cancelled",
                    "verdict": "insufficient-evidence",
                    "completed_at": utcnow(),
                    "duration_ms": int(
                        (time.monotonic() - started) * 1000),
                    "error": ("cancelled while queued: "
                              f"{token.reason or 'run cancelled'}"),
                    "error_type": "RunCancelledError",
                    "failure_category": "cancelled",
                    "progress_json": json.dumps(
                        {**progress, "phase": "done"}),
                })
                return
            self._store.update_execution(
                exec_id, {"status": "running",
                          "progress_json": json.dumps(progress)})
            monitor.start()
            target = spec["url"]
            url = (target(slow_ms=slow_ms, disabled=disabled)
                   if callable(target) else target)
            shot_path = self._shots / _screenshot_name(exec_id)
            if driver == "chimera":
                outcome = self._run_chimera(
                    spec, url, log, shot_path, token, progress)
            else:
                outcome = self._run_baseline(
                    exec_id, spec, url, log, shot_path, token,
                    timeout_override, progress)
            self._finish(exec_id, outcome, started, progress, log, url,
                         spec)
        except Exception as exc:  # noqa: BLE001 — executor must not die
            if not self._is_timed_out(exec_id):
                self._store.update_execution(exec_id, {
                    "status": "error",
                    "verdict": "insufficient-evidence",
                    "completed_at": utcnow(),
                    "duration_ms": int((time.monotonic() - started) * 1000),
                    "error": f"executor failure: {exc}",
                    "error_type": type(exc).__name__,
                    "failure_category": "executor-error",
                    "progress_json": json.dumps(
                        {**progress, "phase": "error"}),
                })
        finally:
            self._run_slots.release()
            stop.set()
            if monitor.is_alive():
                monitor.join(timeout=2)
            with self._lock:
                self._tokens.pop(exec_id, None)

    def _is_timed_out(self, exec_id: str) -> bool:
        with self._lock:
            return exec_id in self._timed_out

    def _monitor(self, exec_id: str, log: ActionLog, progress: Dict,
                 stop: threading.Event, token: CancellationToken,
                 started: float, run_timeout_s: float) -> None:
        while not stop.wait(0.3):
            try:
                seen = len(log.records)
            except Exception:  # noqa: BLE001 — monitor must not die
                continue
            if seen != progress.get("actions_seen"):
                progress["actions_seen"] = seen
                try:
                    self._store.update_execution(
                        exec_id, {"progress_json": json.dumps(progress)})
                except Exception:  # noqa: BLE001
                    pass
            if time.monotonic() - started <= run_timeout_s:
                continue
            # Outer wall-clock bound: hostile pages can stall even
            # timeout-bearing calls, so the row must finish here. A
            # cooperative run aborts via the token; a wedged worker
            # stays parked (daemon) and its late writes are refused.
            try:
                token.request(
                    f"run exceeded {run_timeout_s:g}s wall-clock budget")
            except Exception:  # noqa: BLE001 — monitor must not die
                pass
            try:
                record = self._store.get_execution(exec_id)
                if record is not None and record["status"] in (
                        "queued", "running"):
                    with self._lock:
                        self._timed_out.add(exec_id)
                    self._store.update_execution(exec_id, {
                        "status": "failed",
                        "verdict": "insufficient-evidence",
                        "completed_at": utcnow(),
                        "duration_ms": int(
                            (time.monotonic() - started) * 1000),
                        "error": "run exceeded "
                                 f"{run_timeout_s:g}s wall-clock budget; "
                                 "worker abandoned",
                        "error_type": "RunTimeoutError",
                        "failure_category": "run-timeout",
                        "progress_json": json.dumps(
                            {**progress, "phase": "timeout"}),
                    })
            except Exception:  # noqa: BLE001 — monitor must not die
                pass
            stop.set()
            return

    def _run_chimera(self, spec: Dict[str, Any], url: str,
                     log: ActionLog, shot_path: Path,
                     token: CancellationToken,
                     progress: Dict) -> Dict[str, Any]:
        # A run-level user profile wins over the default factory; an
        # explicitly injected factory (tests) always wins over both.
        maker = self._chimera_factory
        if spec.get("session_factory") is not None \
                and not self._custom_chimera_factory:
            maker = spec["session_factory"]
        factory = maker(log, shot_path)
        snapshot_page = spec["snapshot_page"]

        def observe(page: Any) -> Dict[str, Any]:
            progress["phase"] = "verifying"
            snapshot = snapshot_page(page)
            return {"snapshot": snapshot}

        progress["phase"] = "running"
        result = spec["chimera"](
            url=url, token=token, observe=observe, factory=factory,
            trace_dir=self._traces)
        holder = getattr(factory, "holder", {})
        shot = holder.get("shot")
        return {
            "driver": "chimera",
            "agent_run_id": result.get("run_id"),
            "status": result.get("status", "failed"),
            "error": result.get("error"),
            "trace_path": result.get("trace_path"),
            "observation": result.get("observation"),
            "observation_error": result.get("observation_error"),
            "shot_taken": bool(shot and shot.taken),
            "shot_error": shot.error if shot else None,
        }

    def _run_baseline(self, exec_id: str, spec: Dict[str, Any], url: str,
                      log: ActionLog, shot_path: Path,
                      token: CancellationToken, timeout_override: int,
                      progress: Dict) -> Dict[str, Any]:
        holder: Dict[str, Any] = {}
        factory = self._baseline_factory(log, shot_path, holder)

        progress["phase"] = "running"
        try:
            outcome = spec["baseline"](
                url=url, token=token, factory=factory, exec_id=exec_id,
                timeout_override=timeout_override,
                trace_dir=self._traces)
        finally:
            browser = holder.get("browser")
            playwright = holder.get("playwright")
            if browser is not None:
                try:
                    browser.close()
                except Exception:  # noqa: BLE001 — teardown best-effort
                    pass
            if playwright is not None:
                try:
                    playwright.stop()
                except Exception:  # noqa: BLE001
                    pass
        return {
            "driver": "baseline-a",
            "agent_run_id": outcome.run_id,
            "status": outcome.terminal_status,
            "error": outcome.error,
            "trace_path": outcome.report_path,
            "observation": ({"snapshot": outcome.snapshot}
                            if outcome.snapshot else None),
            "observation_error": outcome.observation_error,
            "shot_taken": bool(holder.get("shot")
                               and holder["shot"].taken),
            "shot_error": (holder["shot"].error
                           if holder.get("shot") else None),
        }

    def _finish(self, exec_id: str, outcome: Dict[str, Any],
                started: float, progress: Dict, log: ActionLog,
                url: str, spec: Dict[str, Any]) -> None:
        if self._is_timed_out(exec_id):
            return
        duration_ms = int((time.monotonic() - started) * 1000)
        # The agent records its observer log in memory only; judge and
        # persist it here (the replay driver writes its own).
        judged = None
        if log.records and outcome.get("driver") == "chimera":
            try:
                judged = judge_log(
                    log, spec.get("policy") or episode_policy(url))
                actions_path = self._traces / f"{exec_id}.actions.json"
                actions_path.write_text(judged.to_json(), encoding="utf-8")
                actions_path = str(actions_path)
            except Exception:  # noqa: BLE001 — evidence best-effort
                actions_path = None
        else:
            actions_path = None
        trace_path = outcome.get("trace_path")

        # Independent verification from the pre-teardown snapshot.
        observation = outcome.get("observation") or {}
        snapshot = observation.get("snapshot")
        agent_run_id = outcome.get("agent_run_id") or exec_id
        if isinstance(snapshot, dict):
            snapshot = {**snapshot, "run_id": agent_run_id,
                        "captured_at": snapshot.get("captured_at")
                        or utcnow()}
            snap_path = self._traces / f"{exec_id}.snapshot.json"
            snap_path.write_text(json.dumps(snapshot, indent=2),
                                 encoding="utf-8")
            snapshot_ref = str(snap_path)
        else:
            snap_path = None
            snapshot_ref = f"workbench:{exec_id}:snapshot"
        if spec.get("verify") in ("sauce", "sauce-stress", "flipkart",
                                  "wiki", "wikt", "pypi", "bbc",
                                  "github", "crates", "weather",
                                  "gsearch", "steam", "arxiv", "so",
                                  "amazon"):
            if spec.get("verify") == "sauce-stress":
                judge = sauce_adapter.verify_stress_order
                stages = sauce_adapter.stages_for_trace(trace_path)
            elif spec.get("verify") == "flipkart":
                judge = flipkart_adapter.verify_flipkart_cart
                stages = flipkart_adapter.stages_for_trace(trace_path)
            elif spec.get("verify") == "wiki":
                judge = wiki_adapter.verify_wikipedia_lookup
                stages = wiki_adapter.stages_for_trace(trace_path)
            elif spec.get("verify") == "wikt":
                judge = wikt_adapter.verify_wiktionary_lookup
                stages = wikt_adapter.stages_for_trace(trace_path)
            elif spec.get("verify") == "pypi":
                judge = pypi_adapter.verify_pypi_lookup
                stages = pypi_adapter.stages_for_trace(trace_path)
            elif spec.get("verify") == "bbc":
                judge = bbc_adapter.verify_bbc_headlines
                stages = bbc_adapter.stages_for_trace(trace_path)
            elif spec.get("verify") == "github":
                judge = github_adapter.verify_github_profile
                stages = github_adapter.stages_for_trace(trace_path)
            elif spec.get("verify") == "crates":
                judge = crates_adapter.verify_crates_lookup
                stages = crates_adapter.stages_for_trace(trace_path)
            elif spec.get("verify") == "weather":
                judge = weather_adapter.verify_bbc_weather
                stages = weather_adapter.stages_for_trace(trace_path)
            elif spec.get("verify") == "gsearch":
                judge = gsearch_adapter.verify_github_search
                stages = gsearch_adapter.stages_for_trace(trace_path)
            elif spec.get("verify") == "steam":
                judge = steam_adapter.verify_steam_price
                stages = steam_adapter.stages_for_trace(trace_path)
            elif spec.get("verify") == "arxiv":
                judge = arxiv_adapter.verify_arxiv_search
                stages = arxiv_adapter.stages_for_trace(trace_path)
            elif spec.get("verify") == "so":
                judge = so_adapter.verify_so_search
                stages = so_adapter.stages_for_trace(trace_path)
            elif spec.get("verify") == "amazon":
                judge = amazon_adapter.verify_amazon_price
                stages = amazon_adapter.stages_for_trace(trace_path)
            else:
                judge = sauce_adapter.verify_sauce_order
                stages = sauce_adapter.stages_for_trace(trace_path)
            sauce = judge(
                snapshot if isinstance(snapshot, dict) else None,
                stages,
                spec["expected"])
            status, checks = sauce["status"], sauce["checks"]
            all_satisfied = bool(checks) and all(
                c.get("satisfied") is True for c in checks)
        elif spec.get("verify") == "studio":
            from workbench import studio as studio_module

            studio_verdict = studio_module.verify_studio_run(
                snapshot if isinstance(snapshot, dict) else None,
                studio_module.steps_for_trace(trace_path),
                spec["expected"])
            status, checks = (studio_verdict["status"],
                              studio_verdict["checks"])
            all_satisfied = bool(checks) and all(
                c.get("satisfied") is True for c in checks)
        else:
            evidence = verify_postconditions(
                snapshot=snapshot,
                expected_stored_name=spec["expected"],
                snapshot_ref=snapshot_ref, run_id=agent_run_id,
                observation_error=outcome.get("observation_error"))
            status = evidence.status
            checks = [{"check_id": c.postcondition_id,
                       "satisfied": c.satisfied, "detail": c.detail}
                      for c in evidence.checks] if evidence.checks else []
            all_satisfied = evidence.all_satisfied
        self._store.replace_verification(exec_id, checks)

        if status == "verified" and all_satisfied:
            verdict = "verified-success"
        elif status == "verified":
            verdict = "verified-failure"
        else:
            verdict = "insufficient-evidence"

        # Actions: in-memory judged log first, sibling log file
        # second, trace-event fallback last.
        if judged is not None and judged.records:
            actions = [{
                "seq": r.seq,
                "action_type": r.action_type,
                "target_summary": r.target_summary,
                "outcome": r.outcome,
                "elapsed_ms": r.elapsed_ms,
                "error_type": r.error_type,
            } for r in judged.records]
        else:
            actions, found_path = self._collect_actions(
                exec_id, outcome, trace_path)
            if found_path is not None:
                actions_path = found_path
        if actions:
            self._store.replace_actions(exec_id, actions)

        error = outcome.get("error")
        error_type = _error_type(error)
        status = outcome.get("status", "failed")
        if status not in ("succeeded", "failed", "cancelled"):
            status = "failed"

        shot = self._shots / _screenshot_name(exec_id)
        self._store.update_execution(exec_id, {
            "status": status,
            "verdict": verdict,
            "completed_at": utcnow(),
            "duration_ms": duration_ms,
            "stage_timings_json": _stage_timings(spec, trace_path),
            "error": error,
            "error_type": error_type,
            "failure_category": (classify_failure(error_type)
                                 if status != "succeeded" else None),
            "retries": _count_errors(actions),
            "actions_count": len(actions) if actions else None,
            "trace_path": trace_path,
            "snapshot_path": str(snap_path) if snap_path else None,
            "screenshot_path": str(shot) if shot.is_file() else None,
            "actions_path": actions_path,
            "progress_json": json.dumps({**progress, "phase": "done"}),
        })

    def _collect_actions(self, exec_id: str, outcome: Dict[str, Any],
                         trace_path: Optional[str]
                         ) -> tuple[List[Dict[str, Any]], Optional[str]]:
        # A judged action log next to the trace/report wins when present.
        if trace_path:
            stem = str(trace_path)
            if stem.endswith(".replay.json"):
                stem = stem[: -len(".replay.json")]
            elif stem.endswith(".json"):
                stem = stem[: -len(".json")]
            candidate = Path(stem + ".actions.json")
            if candidate.is_file():
                try:
                    doc = json.loads(candidate.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    doc = None
                if doc is not None:
                    rows = [{
                        "seq": r.get("seq", i),
                        "action_type": r.get("action_type", "?"),
                        "target_summary": r.get("target_summary"),
                        "outcome": r.get("outcome", "ok"),
                        "elapsed_ms": r.get("elapsed_ms"),
                        "error_type": r.get("error_type"),
                    } for i, r in enumerate(doc.get("records", []))]
                    return rows, str(candidate)
        # Otherwise parse the agent trace events.
        if trace_path:
            try:
                doc = json.loads(Path(trace_path).read_text(
                    encoding="utf-8"))
            except (OSError, ValueError):
                return [], None
            rows = []
            prev_ts: Optional[float] = None
            for event in doc.get("events", []):
                action = event.get("action_type")
                if not action:
                    continue
                ts = event.get("timestamp")
                stamp = _parse_ts(ts)
                elapsed = (int((stamp - prev_ts) * 1000)
                           if stamp and prev_ts else None)
                if stamp:
                    prev_ts = stamp
                err = event.get("error_details")
                rows.append({
                    "seq": event.get("sequence_number", len(rows)),
                    "ts": ts,
                    "action_type": action,
                    "target_summary": _summarize_event(event),
                    "outcome": ("error"
                                if event.get("action_outcome") == "failure"
                                else "ok"),
                    "elapsed_ms": elapsed,
                    "error_type": (_error_type(err) if err else None),
                })
            return rows, None
        return [], None


def _scenario_id(scenario: str) -> str:
    return {"normal": "S-NORM", "slow": "S-SLOW",
            "disabled": "S-DIS",
            "slow-disabled": "S-SLOWDIS"}[scenario]


def _sauce_policy() -> ActionPolicy:
    """Observer policy for the external store's approved controls."""
    return ActionPolicy(
        permitted_urls=sauce_adapter.SAUCE_URLS,
        permitted_fill_targets=sauce_adapter.SAUCE_FILL_TARGETS,
        permitted_click_targets=sauce_adapter.SAUCE_CLICK_TARGETS,
        permitted_select_targets=sauce_adapter.SAUCE_SELECT_TARGETS,
    )


def _flipkart_policy() -> ActionPolicy:
    """Observer policy for the Flipkart marketplace's approved pages.

    Search and product URLs carry the live query and catalog IDs,
    so they are permitted by origin+path prefix; the adapter's
    fail-closed URL guard (no checkout, account, or off-origin
    page) is what keeps the driver on the three approved pages.
    """
    origin = flipkart_adapter.APPROVED_ORIGIN
    return ActionPolicy(
        permitted_urls=(flipkart_adapter.HOME_URL,
                        flipkart_adapter.VIEWCART_URL),
        permitted_url_prefixes=(
            f"{origin}{flipkart_adapter.SEARCH_PATH}",
        ),
        permitted_url_patterns=(
            origin + r"/[^/]+/p/[^/?#]+(?=$|[?#])",
        ),
        permitted_fill_targets=flipkart_adapter.FLIPKART_FILL_TARGETS,
        permitted_click_targets=flipkart_adapter.FLIPKART_CLICK_TARGETS,
    )


def _wiki_policy() -> ActionPolicy:
    """Observer policy for Wikipedia's search box and article pages."""
    origin = wiki_adapter.APPROVED_ORIGIN
    return ActionPolicy(
        permitted_urls=(wiki_adapter.HOME_URL,),
        permitted_url_prefixes=(
            f"{origin}{wiki_adapter.SEARCH_PREFIX}",
        ),
        permitted_url_patterns=(
            origin + r"/wiki/[^/:?#]+(?=$|[?#])",
        ),
        permitted_fill_targets=wiki_adapter.WIKI_FILL_TARGETS,
        permitted_click_targets=wiki_adapter.WIKI_CLICK_TARGETS,
    )


def _wikt_policy() -> ActionPolicy:
    """Observer policy for Wiktionary's read-only entry pages."""
    origin = wikt_adapter.APPROVED_ORIGIN
    return ActionPolicy(
        permitted_urls=(wikt_adapter.HOME_URL,),
        permitted_url_prefixes=(),
        permitted_url_patterns=(
            origin + r"/wiki/[^/:?#]+(?=$|[?#])",
        ),
        permitted_fill_targets=wikt_adapter.WIKT_FILL_TARGETS,
        permitted_click_targets=wikt_adapter.WIKT_CLICK_TARGETS,
    )


def _pypi_policy() -> ActionPolicy:
    """Observer policy for PyPI's read-only project pages."""
    origin = pypi_adapter.APPROVED_ORIGIN
    return ActionPolicy(
        permitted_urls=(pypi_adapter.HOME_URL,),
        permitted_url_prefixes=(),
        permitted_url_patterns=(
            origin + r"/project/[^/?#]+/?(?=$|[?#])",
        ),
        permitted_fill_targets=pypi_adapter.PYPI_FILL_TARGETS,
        permitted_click_targets=pypi_adapter.PYPI_CLICK_TARGETS,
    )


def _bbc_policy() -> ActionPolicy:
    """Observer policy for the BBC's read-only section fronts."""
    origin = bbc_adapter.APPROVED_ORIGIN
    return ActionPolicy(
        permitted_urls=(bbc_adapter.HOME_URL,),
        permitted_url_prefixes=(),
        permitted_url_patterns=(
            origin + r"/(news|business|technology)/?(?=$|[?#])",
        ),
        permitted_fill_targets=bbc_adapter.BBC_FILL_TARGETS,
        permitted_click_targets=bbc_adapter.BBC_CLICK_TARGETS,
    )


def _github_policy() -> ActionPolicy:
    """Observer policy for GitHub's read-only public profiles."""
    origin = github_adapter.APPROVED_ORIGIN
    reserved = github_adapter.RESERVED_ALTERNATION
    return ActionPolicy(
        permitted_urls=(github_adapter.HOME_URL,),
        permitted_url_prefixes=(),
        permitted_url_patterns=(
            origin + r"/(?!" + reserved + r"/?(?=$|[?#]))"
            r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?/?(?=$|[?#])",
        ),
        permitted_fill_targets=github_adapter.GITHUB_FILL_TARGETS,
        permitted_click_targets=github_adapter.GITHUB_CLICK_TARGETS,
    )


def _crates_policy() -> ActionPolicy:
    """Observer policy for crates.io's read-only crate pages."""
    origin = crates_adapter.APPROVED_ORIGIN
    return ActionPolicy(
        permitted_urls=(crates_adapter.HOME_URL,),
        permitted_url_prefixes=(),
        permitted_url_patterns=(
            origin + r"/crates/[^/?#]+/?(?=$|[?#])",
        ),
        permitted_fill_targets=crates_adapter.CRATES_FILL_TARGETS,
        permitted_click_targets=crates_adapter.CRATES_CLICK_TARGETS,
    )


def _weather_policy() -> ActionPolicy:
    """Observer policy for BBC Weather's read-only city pages."""
    origin = weather_adapter.APPROVED_ORIGIN
    return ActionPolicy(
        permitted_urls=(weather_adapter.HOME_URL,),
        permitted_url_prefixes=(),
        permitted_url_patterns=(
            origin + r"/weather/\d+/?(?=$|[?#])",
        ),
        permitted_fill_targets=weather_adapter.WEATHER_FILL_TARGETS,
        permitted_click_targets=weather_adapter.WEATHER_CLICK_TARGETS,
    )


def _gsearch_policy() -> ActionPolicy:
    """Observer policy for GitHub's repository search page."""
    origin = gsearch_adapter.APPROVED_ORIGIN
    return ActionPolicy(
        permitted_urls=(gsearch_adapter.HOME_URL,),
        permitted_url_prefixes=(
            f"{origin}{gsearch_adapter.SEARCH_PATH}?",
        ),
        permitted_url_patterns=(),
        permitted_fill_targets=gsearch_adapter.GSEARCH_FILL_TARGETS,
        permitted_click_targets=gsearch_adapter.GSEARCH_CLICK_TARGETS,
    )


def _steam_policy() -> ActionPolicy:
    """Observer policy for the Steam store's search and game pages."""
    origin = steam_adapter.APPROVED_ORIGIN
    return ActionPolicy(
        permitted_urls=(steam_adapter.HOME_URL,),
        permitted_url_prefixes=(
            f"{origin}{steam_adapter.SEARCH_PATH}",
        ),
        permitted_url_patterns=(
            origin + r"/app/\d+(/[^?#]*)?(?=$|[?#])",
        ),
        permitted_fill_targets=steam_adapter.STEAM_FILL_TARGETS,
        permitted_click_targets=steam_adapter.STEAM_CLICK_TARGETS,
    )


def _arxiv_policy() -> ActionPolicy:
    """Observer policy for arXiv's paper search page."""
    origin = arxiv_adapter.APPROVED_ORIGIN
    return ActionPolicy(
        permitted_urls=(arxiv_adapter.HOME_URL,),
        permitted_url_prefixes=(
            f"{origin}{arxiv_adapter.SEARCH_PATH}?",
        ),
        permitted_url_patterns=(),
        permitted_fill_targets=arxiv_adapter.ARXIV_FILL_TARGETS,
        permitted_click_targets=arxiv_adapter.ARXIV_CLICK_TARGETS,
    )


def _so_policy() -> ActionPolicy:
    """Observer policy for Stack Overflow's question search page."""
    origin = so_adapter.APPROVED_ORIGIN
    return ActionPolicy(
        permitted_urls=(so_adapter.HOME_URL,),
        permitted_url_prefixes=(
            f"{origin}{so_adapter.SEARCH_PATH}?",
        ),
        permitted_url_patterns=(),
        permitted_fill_targets=so_adapter.SO_FILL_TARGETS,
        permitted_click_targets=so_adapter.SO_CLICK_TARGETS,
    )


def _amazon_policy() -> ActionPolicy:
    """Observer policy for Amazon's search and product pages.

    Deliberately narrow: search plus product pages only. Cart,
    checkout, account, and login paths match nothing here, so any
    navigation toward them is denied and recorded.
    """
    origin = amazon_adapter.APPROVED_ORIGIN
    return ActionPolicy(
        permitted_urls=(amazon_adapter.HOME_URL,),
        permitted_url_prefixes=(
            f"{origin}{amazon_adapter.SEARCH_PATH}?",
        ),
        permitted_url_patterns=(
            origin + r"/([^/]+/)?dp/[A-Z0-9]{10}(/[^?#]*)?(?=$|[?#])",
            origin + r"/gp/product/[A-Z0-9]{10}(/[^?#]*)?(?=$|[?#])",
            origin + r"/gp/slredirect/[^?#]+(?=$|[?#])",
        ),
        permitted_fill_targets=amazon_adapter.AMAZON_FILL_TARGETS,
        permitted_click_targets=amazon_adapter.AMAZON_CLICK_TARGETS,
    )


def _run_spec(workflow_id: str, cleaned: Mapping[str, Any],
              slow_ms: int = 0, disabled: bool = False) -> Dict[str, Any]:
    """Build the per-run execution spec: URL, drivers, expected value.

    Driver callables look their targets up as module globals at call
    time so tests can substitute fakes. ``submitted`` records exactly
    what the driver will type (after submission-case mutation);
    ``expected`` is the entry text the verifier matches exactly (a
    dict of order expectations for the external store).
    ``snapshot_page`` reads the pre-teardown state for the verifier;
    ``policy`` judges the agent's action log (replay drivers judge
    their own). ``slow_ms``/``disabled`` are accepted for
    backwards compatibility and ignored: faulted URLs are built in
    :meth:`Executor._run` from the ``url`` callable.
    """
    if workflow_id == "create-project":
        name = cleaned["project_name"]
        return {
            "label": name,
            "expected": name,
            "submitted": {"project_name": name},
            "items_selector": PROJECT_LIST_SELECTOR,
            "snapshot_page": (lambda page: capture_page_state(
                page, PROJECT_LIST_SELECTOR)),
            "url": get_demo_url_with_faults,
            "chimera": lambda url, token, observe, factory, trace_dir: (
                create_project(name, url=url, trace_dir=trace_dir,
                               cancel=token, observe=observe,
                               browser_factory=factory)),
            "baseline": lambda url, token, factory, exec_id, timeout_override, trace_dir: (
                run_replay(project_name=name, url=url,
                           trace_dir=trace_dir, token=token,
                           page_factory=factory, run_id=exec_id,
                           action_timeout_ms=(timeout_override or None))),
        }
    if workflow_id == "fill-contact-form":
        case = cleaned["submission_case"]
        submitted = {
            "name": cleaned["full_name"],
            "email": cleaned["email"],
            "subject": cleaned["subject"],
            "message": cleaned["message"],
        }
        if case == "missing-message":
            submitted["message"] = ""
        elif case == "invalid-email":
            submitted["email"] = "not-an-email"
        return {
            "label": cleaned["full_name"],
            "expected": contact_entry_text(
                submitted["name"], submitted["email"],
                submitted["subject"], submitted["message"]),
            "submitted": submitted,
            "items_selector": CONTACT_LIST_SELECTOR,
            "snapshot_page": (lambda page: capture_page_state(
                page, CONTACT_LIST_SELECTOR)),
            "url": get_contact_url_with_faults,
            "chimera": lambda url, token, observe, factory, trace_dir: (
                submit_contact_form(
                    submitted["name"], submitted["email"],
                    submitted["subject"], submitted["message"],
                    url=url, trace_dir=trace_dir, cancel=token,
                    observe=observe, browser_factory=factory)),
            "baseline": lambda url, token, factory, exec_id, timeout_override, trace_dir: (
                run_contact_replay(
                    name=submitted["name"], email=submitted["email"],
                    subject=submitted["subject"],
                    message=submitted["message"], url=url,
                    trace_dir=trace_dir, token=token,
                    page_factory=factory, run_id=exec_id,
                    action_timeout_ms=(timeout_override or None))),
        }
    if workflow_id == "saucedemo-order":
        login_case = cleaned["login_case"]
        cart_preset = cleaned["cart_preset"]
        checkout_case = cleaned["checkout_case"]
        user = {"standard": "standard_user",
                "locked-out": "locked_out_user",
                "wrong-password": "standard_user"}[login_case]
        password = ("wrong-password"
                    if login_case == "wrong-password"
                    else sauce_adapter.DEFAULT_PASSWORD)
        slugs = list(sauce_adapter.CART_PRESETS[cart_preset])
        sort = cleaned["sort"]
        info = {"firstName": cleaned["first_name"],
                "lastName": cleaned["last_name"],
                "postalCode": cleaned["postal_code"]}
        if checkout_case == "missing-postal":
            info["postalCode"] = ""
        elif checkout_case == "blank-info":
            info = {"firstName": "", "lastName": "", "postalCode": ""}
        names = [sauce_adapter.CATALOG[s]["name"] for s in slugs]
        order = {"user": user, "password": password, "items": slugs,
                 "sort": sort, "info": info}
        expected = {"username": user, "items": names, "sort": sort,
                    "login_case": login_case,
                    "checkout_case": checkout_case}
        submitted = {"user": user, "items": slugs, "sort": sort,
                     "info": info}
        return {
            "label": f"sauce-order:{user}:{cart_preset}",
            "expected": expected,
            "submitted": submitted,
            "scenario_id": (f"sauce:{login_case}/{cart_preset}/"
                            f"{checkout_case}"),
            "verify": "sauce",
            "policy": _sauce_policy(),
            "snapshot_page": sauce_adapter.capture_end_snapshot,
            "url": sauce_adapter.LOGIN_URL,
            "chimera": lambda url, token, observe, factory, trace_dir: (
                run_saucedemo_order(
                    user, password, slugs, sort,
                    info["firstName"], info["lastName"],
                    info["postalCode"], url=url, trace_dir=trace_dir,
                    cancel=token, observe=observe,
                    browser_factory=factory)),
            "baseline": lambda url, token, factory, exec_id, timeout_override, trace_dir: (
                run_saucedemo_replay(
                    order=order, expected=expected,
                    trace_dir=trace_dir, token=token,
                    page_factory=factory, run_id=exec_id,
                    action_timeout_ms=(timeout_override or None))),
        }
    if workflow_id == "saucedemo-stress":
        account = cleaned["account"]
        user = {"standard": "standard_user",
                "glitch": "performance_glitch_user",
                "problem": "problem_user"}[account]
        cart_preset = cleaned["cart_preset"]
        slugs = list(sauce_adapter.CART_PRESETS[cart_preset])
        sort = cleaned["sort"]
        remove_slug = (slugs[-1]
                       if cleaned["remove_item"] == "last-added" and slugs
                       else None)
        info = {"firstName": cleaned["first_name"],
                "lastName": cleaned["last_name"],
                "postalCode": cleaned["postal_code"]}
        names = [sauce_adapter.CATALOG[s]["name"] for s in slugs]
        remaining = (None if remove_slug is None else
                     [sauce_adapter.CATALOG[s]["name"] for s in slugs
                      if s != remove_slug])
        order = {"user": user, "password": sauce_adapter.DEFAULT_PASSWORD,
                 "items": slugs, "remove": remove_slug, "sort": sort,
                 "info": info}
        expected = {"username": user, "added": names,
                    "remaining": remaining, "sort": sort,
                    "account": account}
        submitted = {"user": user, "items": slugs, "remove": remove_slug,
                     "sort": sort, "info": info}
        settle_ms = int(cleaned["settle_timeout_ms"])
        remove_tag = "remove" if remove_slug is not None else "keep"
        return {
            "label": f"sauce-stress:{user}:{cart_preset}",
            "expected": expected,
            "submitted": submitted,
            "scenario_id": (f"sauce-stress:{account}/{cart_preset}/"
                            f"{sort}/{remove_tag}"),
            "verify": "sauce-stress",
            "policy": _sauce_policy(),
            "snapshot_page": sauce_adapter.capture_end_snapshot,
            "url": sauce_adapter.LOGIN_URL,
            "chimera": lambda url, token, observe, factory, trace_dir: (
                run_saucedemo_order(
                    user, sauce_adapter.DEFAULT_PASSWORD, slugs, sort,
                    info["firstName"], info["lastName"],
                    info["postalCode"], url=url, trace_dir=trace_dir,
                    cancel=token, observe=observe,
                    browser_factory=factory, remove_slug=remove_slug,
                    flow_label="sauce-stress")),
            "baseline": lambda url, token, factory, exec_id, timeout_override, trace_dir: (
                run_saucedemo_stress_replay(
                    order=order, expected=expected,
                    trace_dir=trace_dir, token=token,
                    page_factory=factory, run_id=exec_id,
                    action_timeout_ms=(timeout_override or None),
                    settle_timeout_ms=settle_ms)),
        }
    if workflow_id == "flipkart-add-to-cart":
        query = cleaned["query"]
        pick = int(cleaned["pick"])
        expected = {"query": query, "pick": pick}
        submitted = {"query": query, "pick": pick}
        return {
            "label": f"flipkart:{query}#{pick}",
            "expected": expected,
            "submitted": submitted,
            "scenario_id": f"flipkart:add-to-cart",
            "verify": "flipkart",
            "policy": _flipkart_policy(),
            "snapshot_page": flipkart_adapter.capture_end_snapshot,
            "url": flipkart_adapter.HOME_URL,
            "chimera": lambda url, token, observe, factory, trace_dir: (
                run_flipkart_add_to_cart(
                    query, pick, url=url, trace_dir=trace_dir,
                    cancel=token, observe=observe,
                    browser_factory=factory)),
            "baseline": _chimera_only_no_baseline("flipkart-add-to-cart"),
        }
    if workflow_id == "wikipedia-article-lookup":
        query = cleaned["query"]
        pick = int(cleaned["pick"])
        expected = {"query": query, "pick": pick}
        submitted = {"query": query, "pick": pick}
        return {
            "label": f"wikipedia:{query}#{pick}",
            "expected": expected,
            "submitted": submitted,
            "scenario_id": "wikipedia:lookup",
            "verify": "wiki",
            "policy": _wiki_policy(),
            "snapshot_page": wiki_adapter.capture_end_snapshot,
            "url": wiki_adapter.HOME_URL,
            "chimera": lambda url, token, observe, factory, trace_dir: (
                run_wikipedia_lookup(
                    query, pick, url=url, trace_dir=trace_dir,
                    cancel=token, observe=observe,
                    browser_factory=factory)),
            "baseline": _chimera_only_no_baseline("wikipedia-article-lookup"),
        }
    if workflow_id == "wiktionary-word-lookup":
        word = cleaned["word"]
        try:
            target = wikt_adapter.entry_url(word)
        except ValueError as exc:
            raise WorkflowValidationError(str(exc)) from exc
        expected = {"word": word}
        submitted = {"word": word}
        return {
            "label": f"wiktionary:{word}",
            "expected": expected,
            "submitted": submitted,
            "scenario_id": "wiktionary:lookup",
            "verify": "wikt",
            "policy": _wikt_policy(),
            "snapshot_page": wikt_adapter.capture_end_snapshot,
            "url": target,
            "chimera": lambda url, token, observe, factory, trace_dir: (
                run_wiktionary_lookup(
                    word, url=url, trace_dir=trace_dir,
                    cancel=token, observe=observe,
                    browser_factory=factory)),
            "baseline": _chimera_only_no_baseline("wiktionary-word-lookup"),
        }
    if workflow_id == "pypi-package-lookup":
        package = cleaned["package"]
        try:
            target = pypi_adapter.project_url(package)
        except ValueError as exc:
            raise WorkflowValidationError(str(exc)) from exc
        expected = {"package": package}
        submitted = {"package": package}
        return {
            "label": f"pypi:{package}",
            "expected": expected,
            "submitted": submitted,
            "scenario_id": "pypi:lookup",
            "verify": "pypi",
            "policy": _pypi_policy(),
            "snapshot_page": pypi_adapter.capture_end_snapshot,
            "url": target,
            "chimera": lambda url, token, observe, factory, trace_dir: (
                run_pypi_lookup(
                    package, url=url, trace_dir=trace_dir,
                    cancel=token, observe=observe,
                    browser_factory=factory)),
            "baseline": _chimera_only_no_baseline("pypi-package-lookup"),
        }
    if workflow_id == "bbc-headlines":
        section = cleaned["section"]
        try:
            target = bbc_adapter.section_url(section)
        except ValueError as exc:
            raise WorkflowValidationError(str(exc)) from exc
        expected = {"section": section}
        submitted = {"section": section}
        return {
            "label": f"bbc:{section}",
            "expected": expected,
            "submitted": submitted,
            "scenario_id": "bbc:headlines",
            "verify": "bbc",
            "policy": _bbc_policy(),
            "snapshot_page": bbc_adapter.capture_end_snapshot,
            "url": target,
            "chimera": lambda url, token, observe, factory, trace_dir: (
                run_bbc_headlines(
                    section, url=url, trace_dir=trace_dir,
                    cancel=token, observe=observe,
                    browser_factory=factory)),
            "baseline": _chimera_only_no_baseline("bbc-headlines"),
        }
    if workflow_id == "github-profile":
        username = cleaned["username"]
        try:
            target = github_adapter.profile_url(username)
        except ValueError as exc:
            raise WorkflowValidationError(str(exc)) from exc
        expected = {"username": username}
        submitted = {"username": username}
        return {
            "label": f"github:{username}",
            "expected": expected,
            "submitted": submitted,
            "scenario_id": "github:profile",
            "verify": "github",
            "policy": _github_policy(),
            "snapshot_page": github_adapter.capture_end_snapshot,
            "url": target,
            "chimera": lambda url, token, observe, factory, trace_dir: (
                run_github_profile(
                    username, url=url, trace_dir=trace_dir,
                    cancel=token, observe=observe,
                    browser_factory=factory)),
            "baseline": _chimera_only_no_baseline("github-profile"),
        }
    if workflow_id == "crates-lookup":
        crate = cleaned["crate"]
        try:
            target = crates_adapter.crate_url(crate)
        except ValueError as exc:
            raise WorkflowValidationError(str(exc)) from exc
        expected = {"crate": crate}
        submitted = {"crate": crate}
        return {
            "label": f"crates:{crate}",
            "expected": expected,
            "submitted": submitted,
            "scenario_id": "crates:lookup",
            "verify": "crates",
            "policy": _crates_policy(),
            "snapshot_page": crates_adapter.capture_end_snapshot,
            "url": target,
            "chimera": lambda url, token, observe, factory, trace_dir: (
                run_crates_lookup(
                    crate, url=url, trace_dir=trace_dir,
                    cancel=token, observe=observe,
                    browser_factory=factory)),
            "baseline": _chimera_only_no_baseline("crates-lookup"),
        }
    if workflow_id == "bbc-weather":
        city = cleaned["city"]
        try:
            target = weather_adapter.city_url(city)
        except ValueError as exc:
            raise WorkflowValidationError(str(exc)) from exc
        expected = {"city": city}
        submitted = {"city": city}
        return {
            "label": f"weather:{city}",
            "expected": expected,
            "submitted": submitted,
            "scenario_id": "bbc:weather",
            "verify": "weather",
            "policy": _weather_policy(),
            "snapshot_page": weather_adapter.capture_end_snapshot,
            "url": target,
            "chimera": lambda url, token, observe, factory, trace_dir: (
                run_bbc_weather(
                    city, url=url, trace_dir=trace_dir,
                    cancel=token, observe=observe,
                    browser_factory=factory)),
            "baseline": _chimera_only_no_baseline("bbc-weather"),
        }
    if workflow_id == "github-search":
        query = cleaned["query"]
        try:
            target = gsearch_adapter.search_url(query)
        except ValueError as exc:
            raise WorkflowValidationError(str(exc)) from exc
        expected = {"query": query}
        submitted = {"query": query}
        return {
            "label": f"ghsearch:{query}",
            "expected": expected,
            "submitted": submitted,
            "scenario_id": "github:search",
            "verify": "gsearch",
            "policy": _gsearch_policy(),
            "snapshot_page": gsearch_adapter.capture_end_snapshot,
            "url": target,
            "chimera": lambda url, token, observe, factory, trace_dir: (
                run_github_search(
                    query, url=url, trace_dir=trace_dir,
                    cancel=token, observe=observe,
                    browser_factory=factory)),
            "baseline": _chimera_only_no_baseline("github-search"),
        }
    if workflow_id == "steam-price-check":
        query = cleaned["query"]
        pick = int(cleaned["pick"])
        try:
            steam_adapter.search_url(query)
        except ValueError as exc:
            raise WorkflowValidationError(str(exc)) from exc
        expected = {"query": query, "pick": pick}
        submitted = {"query": query, "pick": pick}
        return {
            "label": f"steam:{query}#{pick}",
            "expected": expected,
            "submitted": submitted,
            "scenario_id": "steam:price",
            "verify": "steam",
            "policy": _steam_policy(),
            "snapshot_page": steam_adapter.capture_end_snapshot,
            "url": steam_adapter.HOME_URL,
            "chimera": lambda url, token, observe, factory, trace_dir: (
                run_steam_price(
                    query, pick, url=url, trace_dir=trace_dir,
                    cancel=token, observe=observe,
                    browser_factory=factory)),
            "baseline": _chimera_only_no_baseline("steam-price-check"),
        }
    if workflow_id == "arxiv-search":
        query = cleaned["query"]
        try:
            target = arxiv_adapter.search_url(query)
        except ValueError as exc:
            raise WorkflowValidationError(str(exc)) from exc
        expected = {"query": query}
        submitted = {"query": query}
        return {
            "label": f"arxiv:{query}",
            "expected": expected,
            "submitted": submitted,
            "scenario_id": "arxiv:search",
            "verify": "arxiv",
            "policy": _arxiv_policy(),
            "snapshot_page": arxiv_adapter.capture_end_snapshot,
            "url": target,
            "chimera": lambda url, token, observe, factory, trace_dir: (
                run_arxiv_search(
                    query, url=url, trace_dir=trace_dir,
                    cancel=token, observe=observe,
                    browser_factory=factory)),
            "baseline": _chimera_only_no_baseline("arxiv-search"),
        }
    if workflow_id == "stackoverflow-search":
        query = cleaned["query"]
        try:
            target = so_adapter.search_url(query)
        except ValueError as exc:
            raise WorkflowValidationError(str(exc)) from exc
        expected = {"query": query}
        submitted = {"query": query}
        return {
            "label": f"so:{query}",
            "expected": expected,
            "submitted": submitted,
            "scenario_id": "so:search",
            "verify": "so",
            "policy": _so_policy(),
            "snapshot_page": so_adapter.capture_end_snapshot,
            "url": target,
            "chimera": lambda url, token, observe, factory, trace_dir: (
                run_so_search(
                    query, url=url, trace_dir=trace_dir,
                    cancel=token, observe=observe,
                    browser_factory=factory)),
            "baseline": _chimera_only_no_baseline("stackoverflow-search"),
        }
    if workflow_id == "amazon-price-check":
        query = cleaned["query"]
        pick = int(cleaned["pick"])
        try:
            amazon_adapter.search_url(query)
        except ValueError as exc:
            raise WorkflowValidationError(str(exc)) from exc
        expected = {"query": query, "pick": pick}
        submitted = {"query": query, "pick": pick}
        return {
            "label": f"amazon:{query}#{pick}",
            "expected": expected,
            "submitted": submitted,
            "scenario_id": "amazon:price",
            "verify": "amazon",
            "policy": _amazon_policy(),
            "snapshot_page": amazon_adapter.capture_end_snapshot,
            "url": amazon_adapter.HOME_URL,
            "chimera": lambda url, token, observe, factory, trace_dir: (
                run_amazon_price(
                    query, pick, url=url, trace_dir=trace_dir,
                    cancel=token, observe=observe,
                    browser_factory=factory)),
            "baseline": _chimera_only_no_baseline("amazon-price-check"),
        }
    raise WorkflowValidationError(f"unsupported workflow {workflow_id!r}")


def _chimera_only_no_baseline(workflow_id: str = "this workflow"):
    """Chimera-only workflows share one baseline stub (unreachable)."""
    def _raise(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError(f"{workflow_id} has no baseline-a driver")
    return _raise


def _stage_timings(spec: Dict[str, Any],
                   trace_path: Optional[str]) -> Optional[str]:
    """Per-stage offsets/durations from the sauce stages file.

    Returns a JSON document (or None for non-sauce runs and missing
    stage evidence). Offsets count from the first captured stage;
    each duration runs until the next capture; the final stage has
    no measured end, so its duration is null — never zero.
    """
    if spec.get("verify") not in ("sauce", "sauce-stress", "flipkart",
                                  "wiki", "wikt", "pypi", "bbc",
                                  "github", "crates", "weather",
                                  "gsearch", "steam", "arxiv", "so",
                                  "amazon"):
        return None
    try:
        verify = spec.get("verify")
        helper = (flipkart_adapter.stages_for_trace
                  if verify == "flipkart"
                  else wiki_adapter.stages_for_trace
                  if verify == "wiki"
                  else wikt_adapter.stages_for_trace
                  if verify == "wikt"
                  else pypi_adapter.stages_for_trace
                  if verify == "pypi"
                  else bbc_adapter.stages_for_trace
                  if verify == "bbc"
                  else github_adapter.stages_for_trace
                  if verify == "github"
                  else crates_adapter.stages_for_trace
                  if verify == "crates"
                  else weather_adapter.stages_for_trace
                  if verify == "weather"
                  else gsearch_adapter.stages_for_trace
                  if verify == "gsearch"
                  else steam_adapter.stages_for_trace
                  if verify == "steam"
                  else arxiv_adapter.stages_for_trace
                  if verify == "arxiv"
                  else so_adapter.stages_for_trace
                  if verify == "so"
                  else amazon_adapter.stages_for_trace
                  if verify == "amazon"
                  else sauce_adapter.stages_for_trace)
        stages = helper(trace_path)
    except Exception:  # noqa: BLE001 — evidence best-effort
        return None
    if not stages:
        return None
    names = [s.get("stage", "?") if isinstance(s, dict) else "?"
             for s in stages]
    stamps = [_parse_ts(s.get("captured_at")) if isinstance(s, dict)
              else None for s in stages]
    if any(t is None for t in stamps):
        return json.dumps({
            "stages": [{"stage": name, "offset_ms": None,
                        "duration_ms": None} for name in names],
            "unavailable_reason":
                "stage timestamps missing or unparseable",
        })
    assert stamps[0] is not None
    base = stamps[0]
    out = []
    for i, name in enumerate(names):
        start = stamps[i]
        assert start is not None
        nxt = stamps[i + 1] if i + 1 < len(stamps) else None
        out.append({
            "stage": name,
            "offset_ms": int((start - base) * 1000),
            "duration_ms": (int((nxt - start) * 1000)
                            if nxt is not None else None),
        })
    return json.dumps({"stages": out})


def _error_type(error: Any) -> Optional[str]:
    if not error:
        return None
    text = error if isinstance(error, str) else json.dumps(error)
    head = text.split(":", 1)[0].strip()
    return head.split(".")[-1] or None


def _count_errors(actions: List[Dict[str, Any]]) -> Optional[int]:
    if not actions:
        return None
    return sum(1 for a in actions if a.get("outcome") == "error")


def _parse_ts(value: Any) -> Optional[float]:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _summarize_event(event: Mapping[str, Any]) -> Optional[str]:
    refs = event.get("evidence_references") or []
    for ref in refs:
        if isinstance(ref, str) and ref.startswith("target="):
            return ref[len("target="):][:160]
    err = event.get("error_details")
    if isinstance(err, str) and err:
        return err[:160]
    return event.get("event_type")
