"""Tests for ordered multi-workflow sequences.

Covers: spec validation, deterministic step order, full runs to
completion, stop-on-failure (verified-failure and executor errors),
run-all mode, pause/resume/cancel, the one-browser guard shared
with campaigns, persistence across runner instances, the store
migration, and the sequence HTTP API.
"""

import json
import threading
import time
import urllib.error
import urllib.request

import pytest

from workbench.executor import Executor
from workbench.sequences import (
    SequenceError,
    SequenceRunner,
    build_steps,
    validate_spec,
)
from workbench.server import WorkbenchState, create_server
from workbench.store import Store


def _chain_spec(**overrides):
    base = {
        "name": "morning chain",
        "steps": [
            {"label": "wiki", "workflow_id": "wikipedia-article-lookup",
             "params": {"query": "badminton"}},
            {"label": "pypi", "workflow_id": "pypi-package-lookup",
             "params": {"package": "playwright"}},
            {"label": "project", "workflow_id": "create-project",
             "params": {"project_name": "Chain File"}},
        ],
        "pacing_ms": 0,
    }
    base.update(overrides)
    return base


def test_validate_spec_accepts_multi_workflow_chain():
    spec = validate_spec(_chain_spec())
    assert spec["total_steps"] == 3
    assert [s["workflow_id"] for s in spec["steps"]] == [
        "wikipedia-article-lookup", "pypi-package-lookup", "create-project"]
    # Driver defaults to chimera; workflow defaults fill the rest.
    assert spec["steps"][0]["driver"] == "chimera"
    assert spec["steps"][0]["params"]["pick"] == 1
    assert spec["stop_on_failure"] is True


def test_validate_spec_rejects_bad_specs():
    with pytest.raises(SequenceError):
        validate_spec(_chain_spec(name="  "))
    with pytest.raises(SequenceError):
        validate_spec(_chain_spec(steps=[]))
    with pytest.raises(SequenceError):
        validate_spec(_chain_spec(steps=[{"label": "x"}]))
    with pytest.raises(SequenceError):
        validate_spec(_chain_spec(steps=[
            {"label": "x", "workflow_id": "nope"}]))
    with pytest.raises(SequenceError):
        validate_spec(_chain_spec(steps=[
            {"label": "x", "workflow_id": "third-party-sites"}]))
    with pytest.raises(SequenceError):
        validate_spec(_chain_spec(steps=[
            {"label": "x", "workflow_id": "pypi-package-lookup",
             "driver": "watson"}]))
    with pytest.raises(SequenceError):
        validate_spec(_chain_spec(steps=[
            {"label": "x", "workflow_id": "bbc-headlines",
             "params": {"section": "sports"}}]))
    with pytest.raises(SequenceError):
        validate_spec(_chain_spec(pacing_ms=-1))
    with pytest.raises(SequenceError):
        validate_spec(_chain_spec(stop_on_failure="yes"))
    with pytest.raises(SequenceError):
        validate_spec(_chain_spec(steps=[
            {"label": f"s{i}", "workflow_id": "bbc-headlines"}
            for i in range(101)]))


def test_build_steps_numbers_in_run_order():
    steps = build_steps(validate_spec(_chain_spec()))
    assert [s["step_seq"] for s in steps] == [1, 2, 3]
    assert steps[2]["label"] == "project"


class ScriptedExecutor:
    """Fake executor completing steps instantly per script."""

    def __init__(self, store, script):
        self._store = store
        self._script = list(script)
        self.submitted = []
        self.cancelled = []

    def submit(self, workflow_id, driver, params, campaign_id=None,
               trial_seq=None, trial_kind=None, sequence_id=None,
               step_seq=None):
        self.submitted.append((workflow_id, step_seq))
        status, verdict = self._script.pop(0) if self._script else (
            "succeeded", "verified-success")
        exec_id = self._store.create_execution({
            "workflow_id": workflow_id, "driver": driver,
            "scenario_id": "seq:x", "trial_kind": trial_kind,
            "sequence_id": sequence_id, "step_seq": step_seq,
            "status": status, "verdict": verdict,
            "duration_ms": 100,
        })
        return exec_id

    def cancel(self, exec_id):
        self.cancelled.append(exec_id)
        return True


def _wait_status(store, sequence_id, statuses, timeout=15.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        sequence = store.get_sequence(sequence_id)
        if sequence["status"] in statuses:
            return sequence
        time.sleep(0.05)
    raise AssertionError(f"sequence stuck in {sequence['status']}")


def test_full_run_completes_steps_in_order(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        fake = ScriptedExecutor(store, [])
        runner = SequenceRunner(store, fake)
        sequence_id = runner.create(_chain_spec())
        runner.start(sequence_id)
        done = _wait_status(store, sequence_id, ("completed",))
        assert done["finished_steps"] == 3
        assert fake.submitted == [
            ("wikipedia-article-lookup", 1),
            ("pypi-package-lookup", 2),
            ("create-project", 3),
        ]
        rows = store.list_executions(
            filters={"sequence_id": sequence_id})["rows"]
        assert sorted(r["step_seq"] for r in rows) == [1, 2, 3]
        assert all(r["trial_kind"] == "sequence" for r in rows)
    finally:
        store.close()


def test_verified_failure_halts_chain_by_default(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        fake = ScriptedExecutor(store, [
            ("succeeded", "verified-success"),
            ("failed", "verified-failure"),
            ("succeeded", "verified-success"),
        ])
        runner = SequenceRunner(store, fake)
        sequence_id = runner.create(_chain_spec())
        runner.start(sequence_id)
        failed = _wait_status(store, sequence_id, ("failed",))
        assert failed["finished_steps"] == 2
        assert "step 2 (pypi)" in failed["stop_reason"]
        # Step 3 never started.
        assert [s[1] for s in fake.submitted] == [1, 2]
    finally:
        store.close()


def test_executor_error_halts_chain(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        fake = ScriptedExecutor(store, [("error", "pending")])
        runner = SequenceRunner(store, fake)
        sequence_id = runner.create(_chain_spec())
        runner.start(sequence_id)
        failed = _wait_status(store, sequence_id, ("failed",))
        assert failed["finished_steps"] == 1
        assert len(fake.submitted) == 1
    finally:
        store.close()


def test_run_all_mode_finishes_despite_failures(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        fake = ScriptedExecutor(store, [
            ("failed", "verified-failure"),
            ("succeeded", "verified-success"),
            ("failed", "verified-failure"),
        ])
        runner = SequenceRunner(store, fake)
        sequence_id = runner.create(
            _chain_spec(stop_on_failure=False))
        runner.start(sequence_id)
        done = _wait_status(store, sequence_id, ("completed",))
        assert done["finished_steps"] == 3
        assert len(fake.submitted) == 3
    finally:
        store.close()


class BlockingExecutor(ScriptedExecutor):
    """Steps stay running until finish()/cancel() flips the record."""

    def __init__(self, store):
        super().__init__(store, [])

    def submit(self, workflow_id, driver, params, campaign_id=None,
               trial_seq=None, trial_kind=None, sequence_id=None,
               step_seq=None):
        exec_id = self._store.create_execution({
            "workflow_id": workflow_id, "driver": driver,
            "scenario_id": "seq:x", "trial_kind": trial_kind,
            "sequence_id": sequence_id, "step_seq": step_seq,
            "status": "running", "verdict": "pending",
        })
        self.submitted.append((workflow_id, step_seq))
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
        raise AssertionError("step never submitted")


def test_pause_waits_for_live_step_then_resume_finishes(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        fake = BlockingExecutor(store)
        runner = SequenceRunner(store, fake)
        sequence_id = runner.create(_chain_spec())
        runner.start(sequence_id)
        fake.wait_submitted(1)
        runner.pause(sequence_id)
        assert store.get_sequence(sequence_id)["status"] == "paused"
        fake.finish()
        deadline = time.time() + 10
        while (store.get_sequence(sequence_id)["finished_steps"] < 1
               and time.time() < deadline):
            time.sleep(0.05)
        paused = store.get_sequence(sequence_id)
        assert paused["finished_steps"] == 1
        assert paused["status"] == "paused"
        # A fresh runner instance resumes from the database.
        runner2 = SequenceRunner(store, fake)
        runner2.resume(sequence_id)
        for _ in range(2):
            fake.wait_submitted(len(fake.submitted) + 1)
            fake.finish()
        done = _wait_status(store, sequence_id, ("completed",))
        assert done["finished_steps"] == 3
    finally:
        store.close()


def test_cancel_stops_sequence_and_step(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        fake = BlockingExecutor(store)
        runner = SequenceRunner(store, fake)
        sequence_id = runner.create(_chain_spec())
        runner.start(sequence_id)
        fake.wait_submitted(1)
        runner.cancel(sequence_id)
        cancelled = store.get_sequence(sequence_id)
        assert cancelled["status"] == "cancelled"
        assert fake.cancelled
    finally:
        store.close()


def test_one_browser_guard_spans_campaigns_and_sequences(tmp_path):
    from workbench.campaigns import CampaignRunner

    store = Store(tmp_path / "w.db")
    try:
        blocking = BlockingExecutor(store)
        seq_runner = SequenceRunner(store, blocking)
        camp_runner = CampaignRunner(store, blocking)
        sequence_id = seq_runner.create(_chain_spec())
        seq_runner.start(sequence_id)
        blocking.wait_submitted(1)
        campaign_id = camp_runner.create({
            "name": "x", "workflow_id": "create-project",
            "drivers": ["chimera"],
            "conditions": [{"label": "a",
                            "params": {"project_name": "G"}}],
            "repetitions": 1, "pacing_ms": 0,
            "stop_after_consecutive_errors": 5,
        })
        with pytest.raises(Exception, match="already running"):
            camp_runner.start(campaign_id)
        seq_runner.cancel(sequence_id)
        camp_runner.start(campaign_id)
        blocking.wait_submitted(2)
        sequence_id2 = seq_runner.create(_chain_spec())
        with pytest.raises(Exception, match="already running"):
            seq_runner.start(sequence_id2)
    finally:
        store.close()


def test_recover_pauses_orphaned_running_sequence(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        runner = SequenceRunner(store, ScriptedExecutor(store, []))
        sequence_id = runner.create(_chain_spec())
        store.update_sequence(sequence_id, {"status": "running"})
        assert runner.recover() == 1
        paused = store.get_sequence(sequence_id)
        assert paused["status"] == "paused"
        assert "resume to continue" in paused["stop_reason"]
    finally:
        store.close()


def test_store_migrates_legacy_executions_table(tmp_path):
    import sqlite3

    fresh = Store(tmp_path / "fresh.db")
    ddl = fresh._conn.execute(
        "SELECT sql FROM sqlite_master WHERE name='executions'").fetchone()[0]
    fresh.close()
    legacy_ddl = "\n".join(
        line for line in ddl.splitlines()
        if "sequence_id" not in line and "step_seq" not in line)
    path = tmp_path / "legacy.db"
    conn = sqlite3.connect(str(path))
    conn.execute(legacy_ddl)
    conn.execute("INSERT INTO executions (id, created_at, source, "
                 "workflow_id, driver, scenario_id, trial_kind, status, "
                 "verdict) VALUES ('e1', '2026-11-01T00:00:00', "
                 "'workbench', 'create-project', 'chimera', 'demo:x', "
                 "'adhoc', 'succeeded', 'verified-success')")
    conn.commit()
    conn.close()
    store = Store(path)
    try:
        cols = [r[1] for r in store._conn.execute(
            "PRAGMA table_info(executions)").fetchall()]
        assert "sequence_id" in cols
        assert "step_seq" in cols
        tables = [r[0] for r in store._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")]
        assert "sequences" in tables
        assert store.get_execution("e1")["workflow_id"] == "create-project"
    finally:
        store.close()


def test_sequence_api_end_to_end(tmp_path):
    store = Store(tmp_path / "w.db")
    runner = SequenceRunner(
        store, ScriptedExecutor(store, [("succeeded",
                                         "verified-success")] * 2))
    state = WorkbenchState(tmp_path, store=store,
                           executor=Executor(store, tmp_path / "wb"),
                           sequences=runner)
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

        status, body = call("POST", "/sequences", _chain_spec())
        assert status == 201
        sequence_id = body["id"]
        status, body = call("GET", "/sequences")
        assert status == 200
        assert [s["id"] for s in body["sequences"]] == [sequence_id]
        status, _ = call("POST", f"/sequences/{sequence_id}/start")
        assert status == 200
        done = _wait_status(store, sequence_id, ("completed",))
        assert done["finished_steps"] == 3
        status, body = call("GET", f"/sequences/{sequence_id}")
        assert status == 200
        assert body["sequence"]["status"] == "completed"
        assert body["sequence"]["step_counts"] == {"succeeded": 3}
        try:
            call("GET", "/sequences/nope")
        except urllib.error.HTTPError as exc:
            assert exc.code == 404
        else:
            raise AssertionError("unknown sequence did not 404")
    finally:
        httpd.shutdown()
        store.close()
