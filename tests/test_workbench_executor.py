"""Tests for the workbench executor with fake browsers (no Chromium).

Fakes drive the same hooks the real drivers use (browser_factory /
page_factory / observe), so wiring, verification, screenshots,
cancellation, and persistence are all exercised without launching
a browser.
"""

import json
import threading
import time
from pathlib import Path

import pytest

from benchmarks.baseline_a import ReplayOutcome
from workbench.executor import Executor, classify_failure
from workbench.store import Store
from workbench.workflows import WorkflowValidationError


class FakeLocator:
    def __init__(self, page, kind, value):
        self._page = page
        self._kind = kind
        self._value = value

    def fill(self, value, timeout=None):
        self._page.calls.append(("fill", self._value, value))
        self._page.pending = value

    def click(self, timeout=None):
        self._page.calls.append(("click", self._value))
        # Simulate the demo app: submit stores the name, shows confirm.
        if not self._page.broken:
            self._page.items = [self._page.pending]
            self._page.visible = True

    def is_visible(self):
        return self._page.visible

    def all_text_contents(self):
        return list(self._page.items)


class FakePage:
    def __init__(self, visible=False, items=(), broken=False):
        self.calls = []
        self.visible = visible
        self.items = list(items)
        self.pending = ""
        self.broken = broken
        self.shot_paths = []

    def goto(self, url, **kw):
        self.calls.append(("goto", url))

    def get_by_label(self, label):
        return FakeLocator(self, "label", label)

    def get_by_role(self, role, name=None):
        return FakeLocator(self, "role", name)

    def locator(self, selector):
        return FakeLocator(self, "css", selector)

    def screenshot(self, path=None, **kwargs):
        self.shot_paths.append(str(path))
        Path(path).write_bytes(b"fake-png")
        return b"fake-png"


class FakeContext:
    def __init__(self, page):
        self._page = page
        self.closed = False

    def new_page(self):
        return self._page

    def close(self):
        self.closed = True


class FakeBrowser:
    def __init__(self, page):
        self._page = page
        self.closed = False

    def new_context(self):
        return FakeContext(self._page)

    def close(self):
        self.closed = True


def _fake_chimera_factory(log, shot_path):
    from benchmarks.observer import RecordingPage
    from workbench.executor import _ShotOnClose

    def factory(pw):
        page = FakePage()
        browser = FakeBrowser(page)
        context = browser.new_context()
        shot = _ShotOnClose(context, page, shot_path)
        factory.holder["shot"] = shot
        return browser, shot, RecordingPage(page, log)

    factory.holder = {}
    return factory


def _fake_baseline_factory(log, shot_path, holder):
    from benchmarks.observer import RecordingPage
    from workbench.executor import _ShotOnClose

    def factory():
        page = FakePage()
        browser = FakeBrowser(page)
        context = browser.new_context()
        shot = _ShotOnClose(context, page, shot_path)
        holder.update(shot=shot, browser=browser)
        return browser, shot, RecordingPage(page, log)

    return factory


def _wait_terminal(store, exec_id, timeout=10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        record = store.get_execution(exec_id)
        if record and record["status"] not in ("queued", "running"):
            return record
        time.sleep(0.05)
    raise AssertionError(f"{exec_id} never finished")


def test_chimera_success_end_to_end(tmp_path, monkeypatch):
    store = Store(tmp_path / "w.db")
    try:
        def fake_create_project(name, url=None, trace_dir=None,
                                cancel=None, observe=None,
                                browser_factory=None):
            browser, context, wrapped = browser_factory(object())
            wrapped.goto(url)
            wrapped.get_by_label("Project Name").fill(name)
            wrapped.get_by_role("button", name="Create Project").click()
            observation = observe(wrapped) if observe else None
            trace_dir = Path(trace_dir)
            trace_dir.mkdir(parents=True, exist_ok=True)
            trace_path = trace_dir / "agent-run.json"
            trace_path.write_text(json.dumps({
                "run_id": "agent-run", "events": [
                    {"sequence_number": 1, "timestamp": None,
                     "event_type": "run_started", "action_type": None},
                    {"sequence_number": 2,
                     "timestamp": "2026-10-30T10:00:01.000Z",
                     "event_type": "action", "action_type": "navigate",
                     "action_outcome": "ok",
                     "evidence_references": ["target=demo-url"]},
                ]}), encoding="utf-8")
            context.close()
            browser.close()
            return {"success": True, "status": "succeeded",
                    "project_name": name, "error": None,
                    "trace_path": str(trace_path), "run_id": "agent-run",
                    "observation": observation}

        monkeypatch.setattr("workbench.executor.create_project",
                            fake_create_project)
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_chimera_factory)
        exec_id = ex.submit("create-project", "chimera",
                            {"project_name": "Acme",
                             "scenario": "normal"})
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "succeeded"
        assert record["verdict"] == "verified-success"
        assert record["duration_ms"] is not None
        assert [c["check_id"] for c in record["checks"]] == ["P1", "P2", "P3"]
        assert all(c["satisfied"] == 1 for c in record["checks"])
        kinds = [a["action_type"] for a in record["actions"]]
        assert kinds[:3] == ["navigate", "fill", "click"]
        assert all(a["outcome"] == "ok" for a in record["actions"])
        assert record["screenshot_path"] is not None
        assert Path(record["screenshot_path"]).read_bytes() == b"fake-png"
        assert record["snapshot_path"] is not None
        assert record["failure_category"] is None
        assert record["progress"]["phase"] == "done"
    finally:
        store.close()


def test_baseline_failure_verdict_and_log_file(tmp_path, monkeypatch):
    store = Store(tmp_path / "w.db")
    try:
        def fake_run_replay(*, project_name, url, trace_dir, token=None,
                            page_factory=None, run_id=None,
                            action_timeout_ms=None):
            assert action_timeout_ms == 500
            browser, context, wrapped = page_factory()
            wrapped.goto(url)
            context.close()
            browser.close()
            trace_dir = Path(trace_dir)
            report_path = trace_dir / f"{run_id}.replay.json"
            report_path.write_text(json.dumps({
                "schema": "x", "run_id": run_id,
                "terminal_status": "failed", "steps": [],
                "started_at": "t", "completed_at": "t"}),
                encoding="utf-8")
            actions_path = trace_dir / f"{run_id}.actions.json"
            actions_path.write_text(json.dumps({
                "run_id": run_id, "attached": True, "complete": True,
                "records": [{"seq": 0, "action_type": "navigate",
                             "target": {"url": url},
                             "target_summary": "demo-url",
                             "outcome": "error", "policy": "allowed",
                             "policy_reason": "", "error_type": "TimeoutError",
                             "elapsed_ms": 500}]}),
                encoding="utf-8")
            return ReplayOutcome(
                run_id=run_id, terminal_status="failed",
                report_path=str(report_path), snapshot=None,
                snapshot_ref=None,
                observation_error="page closed before snapshot",
                action_log={}, error="TimeoutError: fill timed out")

        monkeypatch.setattr("workbench.executor.run_replay",
                            fake_run_replay)
        ex = Executor(store, tmp_path / "wb",
                      baseline_factory=_fake_baseline_factory)
        exec_id = ex.submit("create-project", "baseline-a",
                            {"project_name": "Acme", "scenario": "slow",
                             "slow_ms": 100, "action_timeout_ms": 500})
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "failed"
        # No snapshot -> checks unavailable -> never a success verdict.
        assert record["verdict"] == "insufficient-evidence"
        assert record["error_type"] == "TimeoutError"
        assert record["failure_category"] == "timeout"
        assert record["actions"][0]["error_type"] == "TimeoutError"
        assert record["retries"] == 1
    finally:
        store.close()


def test_cancel_and_validation(tmp_path, monkeypatch):
    store = Store(tmp_path / "w.db")
    try:
        entered = threading.Event()
        release = threading.Event()

        def blocking_create_project(*a, **k):
            entered.set()
            assert release.wait(timeout=10)
            return {"success": False, "status": "cancelled",
                    "project_name": "x", "error": "RunCancelledError: user",
                    "trace_path": None, "run_id": "r"}

        monkeypatch.setattr("workbench.executor.create_project",
                            blocking_create_project)
        ex = Executor(store, tmp_path / "wb")
        exec_id = ex.submit("create-project", "chimera",
                            {"project_name": "x", "scenario": "normal"})
        assert entered.wait(timeout=10)
        assert ex.cancel(exec_id) is True
        assert ex.cancel("missing") is False
        release.set()
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "cancelled"
        assert record["verdict"] == "insufficient-evidence"
        with pytest.raises(WorkflowValidationError):
            ex.submit("create-project", "chimera",
                      {"project_name": "x", "scenario": "normal",
                       "action_timeout_ms": 100})
        with pytest.raises(WorkflowValidationError):
            ex.submit("nope", "chimera", {})
        with pytest.raises(WorkflowValidationError):
            ex.submit("create-project", "hal", {"project_name": "x"})
    finally:
        store.close()


def test_classify_failure():
    assert classify_failure(None) is None
    assert classify_failure("TimeoutError") == "timeout"
    assert classify_failure("RetryBudgetExhaustedError") == "retry-exhausted"
    assert classify_failure("RunCancelledError") == "cancelled"
    assert classify_failure("SomeNewError") == "action-error"


class _WedgingPage(FakePage):
    release = threading.Event()

    def goto(self, url, **kw):
        self.calls.append(("goto", url))
        assert type(self).release.wait(timeout=30)


def _wedging_chimera_factory(log, shot_path):
    from benchmarks.observer import RecordingPage
    from workbench.executor import _ShotOnClose

    def factory(pw):
        page = _WedgingPage()
        browser = FakeBrowser(page)
        context = browser.new_context()
        shot = _ShotOnClose(context, page, shot_path)
        factory.holder["shot"] = shot
        return browser, shot, RecordingPage(page, log)

    factory.holder = {}
    return factory


def test_run_timeout_marks_wedged_run_and_refuses_late_writes(tmp_path):
    _WedgingPage.release.clear()
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_wedging_chimera_factory,
                      run_timeout_s=0.3)
        exec_id = ex.submit("create-project", "chimera",
                            {"project_name": "Acme", "scenario": "normal"})
        record = _wait_terminal(store, exec_id, timeout=15)
        assert record["status"] == "failed"
        assert record["verdict"] == "insufficient-evidence"
        assert record["failure_category"] == "run-timeout"
        assert "wall-clock budget" in (record["error"] or "")
        # Release the wedged worker; its late finish must not
        # overwrite the timeout verdict.
        _WedgingPage.release.set()
        deadline = time.time() + 15
        while ex.running() and time.time() < deadline:
            time.sleep(0.05)
        assert not ex.running()
        record = store.get_execution(exec_id)
        assert record["status"] == "failed"
        assert record["verdict"] == "insufficient-evidence"
        assert record["failure_category"] == "run-timeout"
    finally:
        _WedgingPage.release.set()
        store.close()


def test_concurrent_runs_bounded_by_worker_slots(tmp_path, monkeypatch):
    """Only max_workers runs hold browsers; the rest stay queued."""
    store = Store(tmp_path / "w.db")
    try:
        def fake_create_project(name, url=None, trace_dir=None,
                                cancel=None, observe=None,
                                browser_factory=None):
            browser, context, wrapped = browser_factory(object())
            wrapped.goto(url)
            wrapped.get_by_label("Project Name").fill(name)
            wrapped.get_by_role("button", name="Create Project").click()
            observation = observe(wrapped) if observe else None
            trace_dir = Path(trace_dir)
            trace_dir.mkdir(parents=True, exist_ok=True)
            trace_path = trace_dir / "agent-run.json"
            trace_path.write_text(json.dumps({
                "run_id": "agent-run", "events": [
                    {"sequence_number": 1, "timestamp": None,
                     "event_type": "run_started", "action_type": None},
                    {"sequence_number": 2,
                     "timestamp": "2026-10-30T10:00:01.000Z",
                     "event_type": "action", "action_type": "navigate",
                     "action_outcome": "ok",
                     "evidence_references": ["target=demo-url"]},
                ]}), encoding="utf-8")
            context.close()
            browser.close()
            return {"success": True, "status": "succeeded",
                    "project_name": name, "error": None,
                    "trace_path": str(trace_path), "run_id": "agent-run",
                    "observation": observation}

        monkeypatch.setattr("workbench.executor.create_project",
                            fake_create_project)
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_chimera_factory,
                      max_workers=1)
        ex._run_slots.acquire()  # hold the only slot: run must queue
        try:
            exec_id = ex.submit("create-project", "chimera",
                                {"project_name": "Queued",
                                 "scenario": "normal"})
            time.sleep(0.5)
            assert store.get_execution(exec_id)["status"] == "queued"
        finally:
            ex._run_slots.release()
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "succeeded"
    finally:
        store.close()
