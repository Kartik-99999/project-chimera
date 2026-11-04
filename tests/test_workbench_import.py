"""Tests for benchmark history import (synthetic run files + real ones)."""

import json
from pathlib import Path

from workbench.import_history import (
    default_run_files,
    import_paths,
    import_run_file,
)
from workbench.store import Store

ROOT = Path(__file__).resolve().parent.parent


def _run_file(tmp_path, name="run-x.json", episodes=None, **kw):
    doc = {"run_id": "run-1", "manifest_id": "test-v1",
           "episodes": episodes if episodes is not None else []}
    doc.update(kw)
    path = tmp_path / name
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def _episode(**kw):
    ep = {"trial_id": "trial-0001", "baseline": "chimera",
          "scenario_id": "S-NORM", "input_id": "I-PLAIN",
          "outcome": "succeeded", "duration_ms": 900,
          "started_at": "2026-10-28T10:00:00.000Z",
          "completed_at": "2026-10-28T10:00:01.000Z",
          "error": None, "failure_category": None,
          "retries": {"value": 1, "unavailable_reason": None},
          "actions_executed": {"value": 3, "unavailable_reason": None},
          "trace_artifact": None,
          "verification": {
              "status": "verified", "all_satisfied": True,
              "checks": [
                  {"postcondition_id": "P1", "satisfied": True,
                   "detail": "visible",
                   "evidence_reference": "snap.json#P1"},
                  {"postcondition_id": "P2", "satisfied": True,
                   "detail": "1 of 1", "evidence_reference": "snap.json#P2"},
              ]}}
    ep.update(kw)
    return ep


def test_import_round_trip_and_idempotent(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        path = _run_file(tmp_path, episodes=[
            _episode(),
            _episode(trial_id="warmup:0001", outcome="failed",
                     error="TimeoutError: click timed out",
                     verification={"status": "unavailable"}),
            "not-a-dict",
        ])
        first = import_run_file(store, path)
        assert first == {"imported": 2, "skipped": 1}
        second = import_run_file(store, path)
        assert second == {"imported": 0, "skipped": 3}
        measured = store.get_execution("bm:run-1:trial-0001")
        assert measured["source"] == "benchmark"
        assert measured["verdict"] == "verified-success"
        assert measured["trial_kind"] == "measured"
        assert measured["retries"] == 1
        assert measured["snapshot_path"] == "snap.json"
        assert [c["check_id"] for c in measured["checks"]] == ["P1", "P2"]
        warm = store.get_execution("bm:run-1:warmup:0001")
        assert warm["trial_kind"] == "warmup"
        assert warm["verdict"] == "insufficient-evidence"
        assert warm["error_type"] == "TimeoutError"
        assert warm["checks"] == []
    finally:
        store.close()


def test_import_actions_from_log_and_trace(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        trace = tmp_path / "ep1.json"
        trace.write_text(json.dumps({"events": [
            {"sequence_number": 1,
             "timestamp": "2026-10-28T10:00:00.000Z",
             "event_type": "action", "action_type": "navigate",
             "action_outcome": "ok"},
            {"sequence_number": 2,
             "timestamp": "2026-10-28T10:00:00.500Z",
             "event_type": "action", "action_type": "click",
             "action_outcome": "failure",
             "error_details": "TimeoutError: boom"},
        ]}), encoding="utf-8")
        log = tmp_path / "ep2.actions.json"
        log.write_text(json.dumps({"records": [
            {"seq": 0, "action_type": "navigate",
             "target_summary": "url", "outcome": "ok",
             "elapsed_ms": 40, "error_type": None}]}),
            encoding="utf-8")
        report = tmp_path / "ep2.replay.json"
        report.write_text("{}", encoding="utf-8")
        path = _run_file(tmp_path, episodes=[
            _episode(trial_id="t1", trace_artifact=str(trace)),
            _episode(trial_id="t2", trace_artifact=str(report)),
            _episode(trial_id="t3", trace_artifact=str(tmp_path / "gone.json")),
        ])
        assert import_run_file(store, path)["imported"] == 3
        rows = store.get_execution("bm:run-1:t1")["actions"]
        assert [a["action_type"] for a in rows] == ["navigate", "click"]
        assert rows[1]["elapsed_ms"] == 500
        assert rows[1]["error_type"] == "TimeoutError"
        rows2 = store.get_execution("bm:run-1:t2")["actions"]
        assert rows2[0]["elapsed_ms"] == 40
        assert store.get_execution("bm:run-1:t3")["actions"] == []
    finally:
        store.close()


def test_default_run_files_and_replay_drivers():
    files = default_run_files(ROOT)
    names = [f.name for f in files]
    assert "run-chimera.json" in names
    assert "main-mb-v1-replay-100.json" in names
    assert not [n for n in names
                if ".audited" in n or ".audit-plan" in n or ".config" in n]
    store = Store(":memory:")
    try:
        target = next(f for f in files
                      if f.name == "main-mb-v1-replay-100.json")
        result = import_run_file(store, target)
        assert result["imported"] > 0
        rows = store.list_executions(
            filters={"driver": "replay-100"}, page_size=5)["rows"]
        assert rows, "replay arm must keep its own driver label"
        assert all(r["source"] == "matched-budget" for r in rows)
        eval_file = next(f for f in files
                         if f.name == "run-chimera.json"
                         and "eval-20261028" in str(f))
        import_run_file(store, eval_file)
        eval_rows = store.list_executions(
            filters={"source": "benchmark"}, page_size=3)["rows"]
        assert eval_rows, "eval runs stay benchmark history"
        assert store.distinct("source") == ["benchmark", "matched-budget"]
    finally:
        store.close()


def test_legacy_matched_budget_rows_migrate(tmp_path):
    db = tmp_path / "w.db"
    store = Store(db)
    try:
        store.create_execution({
            "workflow_id": "create-project", "driver": "replay-100",
            "scenario_id": "S-NORM", "source": "benchmark",
            "source_ref": "mb-v1:main-mb-v1-replay-100.json:x"})
        store.create_execution({
            "workflow_id": "create-project", "driver": "chimera",
            "scenario_id": "S-NORM", "source": "benchmark",
            "source_ref": "eval-v1:run-chimera.json:y"})
    finally:
        store.close()
    reopened = Store(db)
    try:
        assert reopened.distinct("source") == ["benchmark",
                                               "matched-budget"]
        assert reopened.count({"source": "matched-budget"}) == 1
        assert reopened.count({"source": "benchmark"}) == 1
    finally:
        reopened.close()
