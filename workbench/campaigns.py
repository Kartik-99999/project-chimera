"""Repeatable browser-execution campaigns over registered workflows.

A campaign is a validated spec (workflow, drivers, labelled
conditions, repetitions) plus a sequential runner: one browser at a
time, fresh contexts per trial (the executor launches a new
browser per execution), configurable pacing, and a stop-on-error
safeguard. Pause/resume/cancel are persisted in the database, so a
new runner on the same database can resume an interrupted
campaign. Every trial is a real execution — nothing is simulated.

Only infrastructure failures (execution ``status == 'error'``)
feed the stop-on-error counter. ``verified-failure`` verdicts
are legitimate trial outcomes and never stop a campaign.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Dict, List, Mapping, Optional

from workbench.store import Store, utcnow
from workbench.workflows import WorkflowValidationError, get_workflow

TRIAL_KIND = "campaign"

#: Hard ceiling on trials per campaign (protects public sites).
MAX_TRIALS = 2000

TERMINAL_STATUSES = ("succeeded", "failed", "cancelled", "error")


class CampaignError(WorkflowValidationError):
    """Campaign spec or transition invalid."""


def validate_config(raw: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate a campaign spec; return the cleaned config."""
    if not isinstance(raw, Mapping):
        raise CampaignError("campaign spec must be an object")
    name = raw.get("name")
    if not isinstance(name, str) or not name.strip():
        raise CampaignError("campaign name is required")
    if len(name.strip()) > 120:
        raise CampaignError("campaign name must be at most 120 characters")
    try:
        workflow = get_workflow(raw.get("workflow_id", ""))
    except WorkflowValidationError as exc:
        raise CampaignError(str(exc)) from None
    drivers = raw.get("drivers")
    if not isinstance(drivers, list) or not drivers:
        raise CampaignError("at least one driver is required")
    seen_drivers = []
    for driver in drivers:
        if driver not in workflow.drivers:
            raise CampaignError(
                f"driver {driver!r} is not supported for "
                f"{workflow.workflow_id!r}")
        if driver not in seen_drivers:
            seen_drivers.append(driver)
    conditions = raw.get("conditions")
    if not isinstance(conditions, list) or not conditions:
        raise CampaignError("at least one condition is required")
    cleaned_conditions = []
    labels = set()
    for index, condition in enumerate(conditions):
        if not isinstance(condition, Mapping):
            raise CampaignError(f"condition {index} must be an object")
        label = condition.get("label")
        if not isinstance(label, str) or not label.strip():
            raise CampaignError(f"condition {index} needs a label")
        if label.strip() in labels:
            raise CampaignError(
                f"duplicate condition label {label.strip()!r}")
        labels.add(label.strip())
        params = condition.get("params") or {}
        if not isinstance(params, Mapping):
            raise CampaignError(
                f"condition {label.strip()!r} params must be an object")
        try:
            cleaned = workflow.validate(params)
        except WorkflowValidationError as exc:
            raise CampaignError(
                f"condition {label.strip()!r}: {exc}") from None
        cleaned_conditions.append({"label": label.strip(),
                                   "params": cleaned})
    repetitions = raw.get("repetitions", 1)
    if (isinstance(repetitions, bool)
            or not isinstance(repetitions, int)
            or not 1 <= repetitions <= 500):
        raise CampaignError("repetitions must be 1..500")
    pacing_ms = raw.get("pacing_ms", 2000)
    if (isinstance(pacing_ms, bool) or not isinstance(pacing_ms, int)
            or not 0 <= pacing_ms <= 120000):
        raise CampaignError("pacing_ms must be 0..120000")
    stop_after = raw.get("stop_after_consecutive_errors", 5)
    if (isinstance(stop_after, bool) or not isinstance(stop_after, int)
            or not 1 <= stop_after <= 100):
        raise CampaignError("stop_after_consecutive_errors must be 1..100")
    total = repetitions * len(seen_drivers) * len(cleaned_conditions)
    if total > MAX_TRIALS:
        raise CampaignError(
            f"{total} trials exceeds the {MAX_TRIALS}-trial ceiling")
    return {
        "name": name.strip(),
        "workflow_id": workflow.workflow_id,
        "drivers": seen_drivers,
        "conditions": cleaned_conditions,
        "repetitions": repetitions,
        "pacing_ms": pacing_ms,
        "stop_after_consecutive_errors": stop_after,
        "total_trials": total,
    }


def build_trials(config: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Deterministic trial order: repetition, driver, condition."""
    trials = []
    seq = 0
    for rep in range(1, int(config["repetitions"]) + 1):
        for driver in config["drivers"]:
            for condition in config["conditions"]:
                seq += 1
                trials.append({
                    "trial_seq": seq,
                    "repetition": rep,
                    "driver": driver,
                    "condition_label": condition["label"],
                    "params": condition["params"],
                })
    return trials


def collect_versions() -> Dict[str, Any]:
    """Application + implementation versions for campaign records."""
    versions: Dict[str, Any] = {}
    try:
        from chimera.tracing import AGENT_VERSION
        versions["chimera_agent"] = AGENT_VERSION
    except Exception:  # noqa: BLE001 — version metadata best-effort
        versions["chimera_agent"] = None
    try:
        from adapters import saucedemo as sauce_adapter
        versions["saucedemo_adapter"] = {
            "origin": sauce_adapter.APPROVED_ORIGIN,
        }
    except Exception:  # noqa: BLE001
        versions["saucedemo_adapter"] = None
    try:
        from benchmarks.baseline_a import SAUCE_REPORT_SCHEMA
        versions["sauce_report_schema"] = SAUCE_REPORT_SCHEMA
    except Exception:  # noqa: BLE001
        versions["sauce_report_schema"] = None
    try:
        from benchmarks.baseline_a import REPORT_SCHEMA
        versions["baseline_report_schema"] = REPORT_SCHEMA
    except Exception:  # noqa: BLE001
        versions["baseline_report_schema"] = None
    return versions


class CampaignRunner:
    """Owns campaign worker threads; state lives in the database."""

    def __init__(self, store: Store, executor: Any,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        self._store = store
        self._executor = executor
        self._sleep = sleep
        self._lock = threading.Lock()
        self._threads: Dict[str, threading.Thread] = {}

    # -- lifecycle --------------------------------------------------------

    def create(self, raw_config: Mapping[str, Any]) -> str:
        import json

        config = validate_config(raw_config)
        return self._store.create_campaign({
            "name": config["name"],
            "workflow_id": config["workflow_id"],
            "config_json": json.dumps(config),
            "versions_json": json.dumps(collect_versions()),
            "status": "draft",
            "total_trials": config["total_trials"],
        })

    def start(self, campaign_id: str) -> Dict[str, Any]:
        with self._lock:
            campaign = self._require(campaign_id)
            if campaign["status"] not in ("draft", "paused"):
                raise CampaignError(
                    f"campaign is {campaign['status']}; only draft or "
                    f"paused campaigns can start")
            for other in self._store.list_campaigns():
                if (other["id"] != campaign_id
                        and other["status"] == "running"):
                    raise CampaignError(
                        "another campaign is already running; "
                        "concurrency is limited to one browser")
            for other in self._store.list_sequences():
                if other["status"] == "running":
                    raise CampaignError(
                        "a sequence is already running; "
                        "concurrency is limited to one browser")
            if campaign_id in self._threads and self._threads[
                    campaign_id].is_alive():
                raise CampaignError("campaign worker already running")
            fields: Dict[str, Any] = {"status": "running",
                                      "stop_reason": None, "error": None}
            if not campaign.get("started_at"):
                fields["started_at"] = utcnow()
            self._store.update_campaign(campaign_id, fields)
            thread = threading.Thread(
                target=self._run_campaign, args=(campaign_id,),
                name=f"campaign-{campaign_id[:8]}", daemon=True)
            self._threads[campaign_id] = thread
            thread.start()
            result = self._store.get_campaign(campaign_id)
            assert result is not None
            return result

    def pause(self, campaign_id: str) -> Dict[str, Any]:
        with self._lock:
            campaign = self._require(campaign_id)
            if campaign["status"] != "running":
                raise CampaignError(
                    f"campaign is {campaign['status']}; only a running "
                    f"campaign can pause")
            self._store.update_campaign(
                campaign_id, {"status": "paused",
                              "stop_reason": "paused by user"})
            result = self._store.get_campaign(campaign_id)
            assert result is not None
            return result

    def resume(self, campaign_id: str) -> Dict[str, Any]:
        with self._lock:
            campaign = self._require(campaign_id)
            if campaign["status"] != "paused":
                raise CampaignError(
                    f"campaign is {campaign['status']}; only a paused "
                    f"campaign can resume")
        return self.start(campaign_id)

    def cancel(self, campaign_id: str) -> Dict[str, Any]:
        with self._lock:
            campaign = self._require(campaign_id)
            if campaign["status"] not in ("running", "paused", "draft"):
                raise CampaignError(
                    f"campaign is {campaign['status']}; nothing to cancel")
            current = campaign.get("current_exec_id")
            self._store.update_campaign(
                campaign_id, {"status": "cancelled",
                              "completed_at": utcnow(),
                              "current_exec_id": None,
                              "stop_reason": "cancelled by user"})
        if current:
            try:
                self._executor.cancel(current)
            except Exception:  # noqa: BLE001 — cancel best-effort
                pass
        result = self._store.get_campaign(campaign_id)
        assert result is not None
        return result

    def recover(self) -> int:
        """Pause campaigns left 'running' by an unclean shutdown."""
        count = 0
        with self._lock:
            for campaign in self._store.list_campaigns():
                if campaign["status"] != "running":
                    continue
                thread = self._threads.get(campaign["id"])
                if thread is not None and thread.is_alive():
                    continue
                self._store.update_campaign(campaign["id"], {
                    "status": "paused",
                    "current_exec_id": None,
                    "stop_reason": "runner restarted; resume to continue",
                })
                count += 1
        return count

    def running(self) -> List[str]:
        with self._lock:
            return [cid for cid, thread in self._threads.items()
                    if thread.is_alive()]

    def _require(self, campaign_id: str) -> Dict[str, Any]:
        campaign = self._store.get_campaign(campaign_id)
        if campaign is None:
            raise CampaignError(f"unknown campaign {campaign_id!r}")
        return campaign

    # -- worker -----------------------------------------------------------

    def _run_campaign(self, campaign_id: str) -> None:
        import json

        try:
            campaign = self._store.get_campaign(campaign_id)
            assert campaign is not None
            config = campaign["config"]
            if not isinstance(config, dict):
                raise CampaignError("campaign config unreadable")
            trials = build_trials(config)
            pacing = float(config.get("pacing_ms", 0)) / 1000.0
            stop_after = int(
                config.get("stop_after_consecutive_errors", 5))
            consecutive = int(
                campaign.get("consecutive_errors", 0) or 0)
            while True:
                live = self._store.get_campaign(campaign_id)
                assert live is not None
                if live["status"] != "running":
                    return
                finished = int(live.get("finished_trials", 0) or 0)
                if finished >= len(trials):
                    self._store.update_campaign(campaign_id, {
                        "status": "completed",
                        "completed_at": utcnow(),
                        "current_exec_id": None})
                    return
                if finished > 0 and pacing > 0:
                    if not self._paced_wait(campaign_id, pacing):
                        return
                    live = self._store.get_campaign(campaign_id)
                    assert live is not None
                    if live["status"] != "running":
                        return
                    finished = int(live.get("finished_trials", 0) or 0)
                trial = trials[finished]
                try:
                    exec_id = self._executor.submit(
                        config["workflow_id"], trial["driver"],
                        trial["params"], campaign_id=campaign_id,
                        trial_seq=trial["trial_seq"],
                        trial_kind=TRIAL_KIND)
                except Exception as exc:  # noqa: BLE001 — config-level fault
                    self._store.update_campaign(campaign_id, {
                        "status": "failed",
                        "completed_at": utcnow(),
                        "current_exec_id": None,
                        "error": f"trial submit failed: {exc}"})
                    return
                self._store.update_campaign(
                    campaign_id, {"current_exec_id": exec_id})
                record = self._wait_terminal(exec_id)
                status = (record or {}).get("status", "error")
                consecutive = consecutive + 1 if status == "error" else 0
                self._store.update_campaign(campaign_id, {
                    "finished_trials": finished + 1,
                    "current_exec_id": None,
                    "consecutive_errors": consecutive,
                })
                if consecutive >= stop_after:
                    self._store.update_campaign(campaign_id, {
                        "status": "paused",
                        "stop_reason": (
                            f"stop-on-error: {consecutive} consecutive "
                            f"executor errors"),
                    })
                    return
        except Exception as exc:  # noqa: BLE001 — worker must not die silent
            try:
                self._store.update_campaign(campaign_id, {
                    "status": "failed",
                    "completed_at": utcnow(),
                    "current_exec_id": None,
                    "error": f"campaign worker failed: {exc}"})
            except Exception:  # noqa: BLE001
                pass
        finally:
            with self._lock:
                self._threads.pop(campaign_id, None)

    def _paced_wait(self, campaign_id: str, seconds: float) -> bool:
        """Sleep between trials; False when no longer running."""
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            campaign = self._store.get_campaign(campaign_id)
            if campaign is None or campaign["status"] != "running":
                return False
            self._sleep(min(0.2, max(0.0, deadline - time.monotonic())))
        campaign = self._store.get_campaign(campaign_id)
        return campaign is not None and campaign["status"] == "running"

    def _wait_terminal(self, exec_id: str,
                       timeout: float = 1800.0) -> Optional[Dict[str, Any]]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            record = self._store.get_execution(exec_id)
            if record is not None and record["status"] in TERMINAL_STATUSES:
                return record
            self._sleep(0.5)
        return self._store.get_execution(exec_id)
