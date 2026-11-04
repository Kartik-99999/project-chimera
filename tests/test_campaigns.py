"""Tests for repeatable browser-execution campaigns.

Covers: spec validation, deterministic trial order, full runs to
completion, pause/resume/cancel, the stop-on-error safeguard (which
ignores legitimate verified-failure verdicts), the one-browser
concurrency guard, persistence across runner instances, stage
timings, and the campaign HTTP API.
"""

import json
import threading
import time
import urllib.request

import pytest

from workbench.campaigns import (
    CampaignError,
    CampaignRunner,
    build_trials,
    validate_config,
)
from workbench.executor import Executor
from workbench.server import WorkbenchState, create_server
from workbench.store import Store


def _sauce_spec(**overrides):
    base = {
        "name": "sauce smoke",
        "workflow_id": "saucedemo-order",
        "drivers": ["chimera", "baseline-a"],
        "conditions": [
            {"label": "success",
             "params": {"login_case": "standard",
                        "cart_preset": "backpack+bike-light",
                        "sort": "az", "checkout_case": "complete"}},
            {"label": "locked-out",
             "params": {"login_case": "locked-out"}},
        ],
        "repetitions": 2,
        "pacing_ms": 0,
        "stop_after_consecutive_errors": 3,
    }
    base.update(overrides)
    return base


def test_validate_config_accepts_balanced_sauce_campaign():
    config = validate_config(_sauce_spec())
    assert config["total_trials"] == 8
    assert config["conditions"][1]["params"]["login_case"] == "locked-out"
    # Workflow defaults fill the rest.
    assert config["conditions"][1]["params"]["sort"] == "az"


def test_validate_config_rejects_bad_specs():
    with pytest.raises(CampaignError):
        validate_config(_sauce_spec(name="  "))
    with pytest.raises(CampaignError):
        validate_config(_sauce_spec(workflow_id="nope"))
    with pytest.raises(CampaignError):
        validate_config(_sauce_spec(workflow_id="third-party-sites"))
    with pytest.raises(CampaignError):
        validate_config(_sauce_spec(drivers=[]))
    with pytest.raises(CampaignError):
        validate_config(_sauce_spec(drivers=["chimera", "watson"]))
    with pytest.raises(CampaignError):
        validate_config(_sauce_spec(conditions=[]))
    with pytest.raises(CampaignError):
        validate_config(_sauce_spec(conditions=[
            {"label": "x", "params": {}},
            {"label": "x", "params": {}}]))
    with pytest.raises(CampaignError):
        validate_config(_sauce_spec(conditions=[
            {"label": "x", "params": {"login_case": "root"}}]))
    with pytest.raises(CampaignError):
        validate_config(_sauce_spec(repetitions=0))
    with pytest.raises(CampaignError):
        validate_config(_sauce_spec(repetitions=500, conditions=[
            {"label": f"c{i}", "params": {}} for i in range(5)]))
    with pytest.raises(CampaignError):
        validate_config(_sauce_spec(pacing_ms=-1))
    with pytest.raises(CampaignError):
        validate_config(_sauce_spec(stop_after_consecutive_errors=0))


def test_build_trials_is_deterministic_and_balanced():
    config = validate_config(_sauce_spec())
    trials = build_trials(config)
    assert [t["trial_seq"] for t in trials] == list(range(1, 9))
    # Rep-major: rep 1 holds all driver/condition pairs first.
    assert [(t["repetition"], t["driver"], t["condition_label"])
            for t in trials[:4]] == [
        (1, "chimera", "success"), (1, "chimera", "locked-out"),
        (1, "baseline-a", "success"), (1, "baseline-a", "locked-out")]
    assert build_trials(config) == trials


class ScriptedExecutor:
    """Fake executor completing trials instantly per script."""

    def __init__(self, store, script):
        self._store = store
        self._script = list(script)
        self.submitted = []
        self.cancelled = []

    def submit(self, workflow_id, driver, params, campaign_id=None,
               trial_seq=None, trial_kind=None):
        self.submitted.append((driver, trial_seq, trial_kind,
                               campaign_id))
        status, verdict = self._script.pop(0) if self._script else (
            "succeeded", "verified-success")
        exec_id = self._store.create_execution({
            "workflow_id": workflow_id, "driver": driver,
            "scenario_id": "sauce:x", "trial_kind": trial_kind,
            "campaign_id": campaign_id, "trial_seq": trial_seq,
            "status": status, "verdict": verdict,
            "duration_ms": 100,
        })
        return exec_id

    def cancel(self, exec_id):
        self.cancelled.append(exec_id)
        return True


def _wait_status(store, campaign_id, statuses, timeout=15.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        campaign = store.get_campaign(campaign_id)
        if campaign["status"] in statuses:
            return campaign
        time.sleep(0.05)
    raise AssertionError(f"campaign stuck in {campaign['status']}")


def test_full_run_completes_and_labels_trials(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        runner = CampaignRunner(
            store, ScriptedExecutor(store, [("succeeded",
                                             "verified-success")] * 8))
        campaign_id = runner.create(_sauce_spec())
        record = store.get_campaign(campaign_id)
        assert record["status"] == "draft"
        assert record["total_trials"] == 8
        assert record["versions"]["chimera_agent"]
        runner.start(campaign_id)
        done = _wait_status(store, campaign_id, ("completed",))
        assert done["finished_trials"] == 8
        assert done["completed_at"]
        rows = store.list_executions(
            filters={"campaign_id": campaign_id},
            sort="trial_seq", page_size=100)["rows"]
        assert len(rows) == 8
        assert [r["trial_seq"] for r in rows] == list(range(1, 9))
        assert {r["trial_kind"] for r in rows} == {"campaign"}
        assert [r["driver"] for r in rows[:4]] == [
            "chimera", "chimera", "baseline-a", "baseline-a"]
    finally:
        store.close()


def test_verified_failures_do_not_trigger_stop_on_error(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        script = [("failed", "verified-failure")] * 8
        runner = CampaignRunner(store, ScriptedExecutor(store, script))
        campaign_id = runner.create(_sauce_spec())
        runner.start(campaign_id)
        done = _wait_status(store, campaign_id, ("completed",))
        assert done["finished_trials"] == 8
        assert done["consecutive_errors"] == 0
    finally:
        store.close()


def test_consecutive_executor_errors_pause_campaign(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        script = ([("succeeded", "verified-success")]
                  + [("error", "insufficient-evidence")] * 7)
        runner = CampaignRunner(store, ScriptedExecutor(store, script))
        campaign_id = runner.create(_sauce_spec())
        runner.start(campaign_id)
        paused = _wait_status(store, campaign_id, ("paused",))
        assert paused["finished_trials"] == 4
        assert "stop-on-error" in (paused["stop_reason"] or "")
        assert paused["consecutive_errors"] == 3
    finally:
        store.close()


class BlockingExecutor(ScriptedExecutor):
    """Trials stay running until finish()/cancel() flips the record."""

    def __init__(self, store):
        super().__init__(store, [])

    def submit(self, workflow_id, driver, params, campaign_id=None,
               trial_seq=None, trial_kind=None):
        exec_id = self._store.create_execution({
            "workflow_id": workflow_id, "driver": driver,
            "scenario_id": "sauce:x", "trial_kind": trial_kind,
            "campaign_id": campaign_id, "trial_seq": trial_seq,
            "status": "running", "verdict": "pending",
        })
        self.submitted.append((driver, trial_seq))
        return exec_id

    def cancel(self, exec_id):
        self.cancelled.append(exec_id)
        self._store.update_execution(
            exec_id, {"status": "cancelled",
                      "verdict": "insufficient-evidence"})
        return True

    def finish(self, status="succeeded", verdict="verified-success"):
        rows = self._store.list_executions(
            filters={"status": "running"}, page_size=1)["rows"]
        assert rows
        self._store.update_execution(
            rows[0]["id"], {"status": status, "verdict": verdict})

    def wait_submitted(self, count, timeout=10.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if len(self.submitted) >= count:
                return
            time.sleep(0.05)
        raise AssertionError("trial never submitted")


def test_pause_waits_for_live_trial_then_resume_finishes(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        fake = BlockingExecutor(store)
        runner = CampaignRunner(store, fake)
        campaign_id = runner.create(_sauce_spec(repetitions=1))
        runner.start(campaign_id)
        fake.wait_submitted(1)
        runner.pause(campaign_id)
        assert store.get_campaign(campaign_id)["status"] == "paused"
        fake.finish()
        deadline = time.time() + 10
        while (store.get_campaign(campaign_id)["finished_trials"] < 1
               and time.time() < deadline):
            time.sleep(0.05)
        paused = store.get_campaign(campaign_id)
        assert paused["finished_trials"] == 1
        assert paused["status"] == "paused"
        # A fresh runner instance resumes from the database.
        runner2 = CampaignRunner(store, fake)
        runner2.resume(campaign_id)
        for _ in range(3):
            fake.wait_submitted(len(fake.submitted) + 1)
            fake.finish()
        done = _wait_status(store, campaign_id, ("completed",))
        assert done["finished_trials"] == 4
    finally:
        store.close()


def test_cancel_stops_campaign_and_trial(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        fake = BlockingExecutor(store)
        runner = CampaignRunner(store, fake)
        campaign_id = runner.create(_sauce_spec())
        runner.start(campaign_id)
        fake.wait_submitted(1)
        deadline = time.time() + 10
        while (not store.get_campaign(campaign_id)["current_exec_id"]
               and time.time() < deadline):
            time.sleep(0.05)
        runner.cancel(campaign_id)
        cancelled = store.get_campaign(campaign_id)
        assert cancelled["status"] == "cancelled"
        assert cancelled["completed_at"]
        assert fake.cancelled
        with pytest.raises(CampaignError):
            runner.resume(campaign_id)
    finally:
        store.close()


def test_only_one_campaign_runs_at_a_time(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        fake = BlockingExecutor(store)
        runner = CampaignRunner(store, fake)
        first = runner.create(_sauce_spec(name="one"))
        second = runner.create(_sauce_spec(name="two"))
        runner.start(first)
        fake.wait_submitted(1)
        with pytest.raises(CampaignError):
            runner.start(second)
        runner.cancel(first)
    finally:
        store.close()


def test_recover_pauses_orphaned_running_campaign(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        runner = CampaignRunner(store, ScriptedExecutor(store, []))
        campaign_id = runner.create(_sauce_spec())
        store.update_campaign(
            campaign_id, {"status": "running",
                          "current_exec_id": "gone"})
        assert runner.recover() == 1
        paused = store.get_campaign(campaign_id)
        assert paused["status"] == "paused"
        assert paused["current_exec_id"] is None
        assert runner.recover() == 0
    finally:
        store.close()


def test_real_executor_records_stage_timings(tmp_path):
    from tests.fake_saucedemo import FakeSaucePage
    from tests.test_workbench_sauce import (
        _sauce_baseline_factory,
        _sauce_chimera_factory,
    )

    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(
            store, tmp_path / "wb",
            chimera_factory=_sauce_chimera_factory(FakeSaucePage()),
            baseline_factory=_sauce_baseline_factory(FakeSaucePage()))
        runner = CampaignRunner(store, ex)
        campaign_id = runner.create(_sauce_spec(
            drivers=["baseline-a"], repetitions=1,
            conditions=[{"label": "success", "params": {}}]))
        runner.start(campaign_id)
        done = _wait_status(store, campaign_id, ("completed",),
                            timeout=60)
        assert done["finished_trials"] == 1
        rows = store.list_executions(
            filters={"campaign_id": campaign_id})["rows"]
        record = store.get_execution(rows[0]["id"])
        timings = json.loads(record["stage_timings_json"])
        names = [s["stage"] for s in timings["stages"]]
        assert names == ["login", "inventory", "cart", "info",
                         "overview", "complete"]
        assert timings["stages"][0]["offset_ms"] == 0
        assert timings["stages"][-1]["duration_ms"] is None
        assert record["verdict"] == "verified-success"
    finally:
        store.close()


def _seed_paired_campaign(store):
    import json as _json

    campaign_id = store.create_campaign({
        "id": "camp-1", "name": "paired", "workflow_id": "saucedemo-order",
        "config_json": "{}", "status": "completed", "total_trials": 5,
        "finished_trials": 5,
    })
    trials = [
        # (seq, driver, scenario, verdict, duration, stage login ms)
        (1, "chimera", "sauce:a", "verified-success", 1000, 100),
        (2, "chimera", "sauce:b", "verified-failure", 2000, 200),
        (3, "baseline-a", "sauce:a", "verified-success", 1100, 150),
        (4, "baseline-a", "sauce:b", "verified-success", 2100, 250),
        (5, "chimera", "sauce:c", "verified-success", 1200, None),
    ]
    for seq, driver, scenario, verdict, duration, login_ms in trials:
        stages = None
        if login_ms is not None:
            stages = _json.dumps({"stages": [
                {"stage": "login", "offset_ms": 0,
                 "duration_ms": login_ms},
                {"stage": "cart", "offset_ms": login_ms,
                 "duration_ms": None}]})
        store.create_execution({
            "id": f"t{seq}", "workflow_id": "saucedemo-order",
            "driver": driver, "scenario_id": scenario,
            "trial_kind": "campaign", "campaign_id": campaign_id,
            "trial_seq": seq, "status": "succeeded"
            if verdict == "verified-success" else "failed",
            "verdict": verdict, "duration_ms": duration,
            "stage_timings_json": stages,
        })
    return campaign_id


def test_paired_outcomes_agreement_and_unpaired(tmp_path):
    from workbench import analytics

    store = Store(tmp_path / "w.db")
    try:
        campaign_id = _seed_paired_campaign(store)
        got = analytics.paired_outcomes(
            store, {"campaign_id": campaign_id})
        assert got["total_pairs"] == 3
        assert got["summary"] == {
            "both_success": 1, "chimera_only": 0,
            "baseline_only": 1, "both_failure": 0,
            "unknown": 0, "unpaired": 1}
        assert got["denominator"] == 2
        assert got["agreement"] == 0.5
        assert got["pairs_truncated"] is False
    finally:
        store.close()


def test_stage_durations_aggregates_and_missing(tmp_path):
    from workbench import analytics

    store = Store(tmp_path / "w.db")
    try:
        campaign_id = _seed_paired_campaign(store)
        got = analytics.stage_durations(
            store, {"campaign_id": campaign_id})
        assert got["rows_with_timings"] == 4
        assert got["rows_without_timings"] == 1
        by_key = {(s["stage"], s["driver"]): s
                  for s in got["stages"]}
        login = by_key[("login", "chimera")]
        assert login["n"] == 2
        assert login["avg_ms"] == 150.0
        assert login["p50"] == 100
        cart = by_key[("cart", "chimera")]
        assert cart["n"] == 0
        assert cart["missing_durations"] == 2
        assert cart["p50"] is None
    finally:
        store.close()


def test_campaign_trends_buckets_and_scope_guard(tmp_path):
    from workbench import analytics

    store = Store(tmp_path / "w.db")
    try:
        campaign_id = _seed_paired_campaign(store)
        scoped = analytics.campaign_trends(
            store, {"campaign_id": campaign_id})
        assert len(scoped["buckets"]) == 5
        assert scoped["buckets"][0]["lo"] == 1
        assert "reason" not in scoped
        unscoped = analytics.campaign_trends(store, {})
        assert unscoped["buckets"] == []
        assert "single campaign" in unscoped["reason"]
    finally:
        store.close()


def test_legacy_db_migrates_campaign_columns(tmp_path):
    import sqlite3

    from workbench.store import SCHEMA

    db_path = tmp_path / "legacy.db"
    legacy_schema = SCHEMA
    for ddl in ("    campaign_id TEXT,               -- campaign membership (NULL = standalone)\n",
                "    trial_seq INTEGER,              -- 1-based trial order within a campaign\n",
                "    stage_timings_json TEXT,        -- per-stage durations (JSON, nullable)\n"):
        assert ddl in legacy_schema, ddl
        legacy_schema = legacy_schema.replace(ddl, "")
    marker = "CREATE TABLE IF NOT EXISTS campaigns ("
    head, sep, tail = legacy_schema.partition(marker)
    assert sep
    end = tail.index(");")
    legacy_schema = head + tail[end + 2:]
    conn = sqlite3.connect(str(db_path))
    conn.executescript(legacy_schema)
    conn.execute(
        "INSERT INTO executions (id, created_at, source, workflow_id, "
        "driver, scenario_id, trial_kind, status, verdict) "
        "VALUES ('r1', 't', 'workbench', 'create-project', 'chimera', "
        "'S-NORM', 'adhoc', 'succeeded', 'verified-success')")
    conn.commit()
    conn.close()
    store = Store(db_path)
    try:
        record = store.get_execution("r1")
        assert record is not None
        assert record["campaign_id"] is None
        assert record["trial_seq"] is None
        assert store.get_campaign("nope") is None
        listed = store.list_campaigns()
        assert listed == []
    finally:
        store.close()


def test_campaign_api_end_to_end(tmp_path):
    store = Store(tmp_path / "w.db")
    runner = CampaignRunner(
        store, ScriptedExecutor(store, [("succeeded",
                                         "verified-success")] * 2))
    state = WorkbenchState(tmp_path, store=store,
                           executor=Executor(store, tmp_path / "wb"),
                           campaigns=runner)
    httpd = create_server(tmp_path, 0, state)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{httpd.server_address[1]}/api/workbench"

        def call(method, path, body=None):
            data = json.dumps(body).encode() if body is not None else None
            req = urllib.request.Request(
                base + path, data=data, method=method,
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req) as res:
                return res.status, json.loads(res.read().decode())

        status, body = call("POST", "/campaigns", _sauce_spec(
            drivers=["chimera"], repetitions=1,
            conditions=[{"label": "a", "params": {}},
                        {"label": "b", "params": {}}]))
        assert status == 201
        campaign_id = body["id"]
        status, body = call("GET", "/campaigns")
        assert status == 200
        assert [c["id"] for c in body["campaigns"]] == [campaign_id]
        status, _ = call("POST", f"/campaigns/{campaign_id}/start")
        assert status == 200
        done = _wait_status(store, campaign_id, ("completed",))
        assert done["finished_trials"] == 2
        status, body = call("GET", f"/campaigns/{campaign_id}")
        assert status == 200
        assert body["campaign"]["status"] == "completed"
        assert body["campaign"]["trial_counts"] == {"succeeded": 2}
    finally:
        httpd.shutdown()
        store.close()
