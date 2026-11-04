"""Tests for the fill-contact-form workflow (fake browsers only).

Covers the real agent + replay functions through a simulated contact
page, the executor dispatch, and the submission-case mutations. No
Chromium is launched here; live runs happen in the e2e validation.
"""

import json
import re
import time
from pathlib import Path

from benchmarks.baseline_a import run_contact_replay
from chimera.agent import contact_entry_text, submit_contact_form
from workbench.executor import Executor, _run_spec
from workbench.store import Store


class ContactFakeLocator:
    def __init__(self, page, kind, value, has_text=None):
        self._page = page
        self._kind = kind
        self._value = value
        self._has_text = has_text

    def fill(self, value, timeout=None):
        self._page.calls.append(("fill", self._value, value))
        self._page.fields[self._value] = value

    def click(self, timeout=None):
        self._page.calls.append(("click", self._value))
        self._page.submit()

    def is_visible(self):
        if self._has_text is not None:
            return any(self._has_text in item
                       for item in self._page.items)
        return self._page.visible

    def all_text_contents(self):
        return list(self._page.items)

    def wait_for(self, state=None, timeout=None):
        if state == "visible" and not self.is_visible():
            raise TimeoutError(f"waiting for {self._value!r} visible")


class ContactFakePage:
    """Simulates demo_app/contact.html validation and rendering."""

    def __init__(self, broken=False):
        self.calls = []
        self.fields = {}
        self.visible = False
        self.items = []
        self.error = None
        self.broken = broken

    def goto(self, url, **kw):
        self.calls.append(("goto", url))

    def get_by_label(self, label):
        return ContactFakeLocator(self, "label", label)

    def get_by_role(self, role, name=None):
        return ContactFakeLocator(self, "role", name)

    def locator(self, selector, has_text=None):
        return ContactFakeLocator(self, "css", selector,
                                  has_text=has_text)

    def screenshot(self, path=None, **kwargs):
        Path(path).write_bytes(b"fake-png")
        return b"fake-png"

    def submit(self):
        if self.broken:
            return
        name = self.fields.get("Full Name", "").strip()
        email = self.fields.get("Email", "").strip()
        subject = self.fields.get("Subject", "").strip()
        message = self.fields.get("Message", "").strip()
        if not name:
            self.error = "Full name is required."
            return
        if not email:
            self.error = "Email is required."
            return
        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
            self.error = "Email address is invalid."
            return
        if not message:
            self.error = "Message is required."
            return
        self.items.append(f"{name} <{email}> [{subject}] {message}")
        self.visible = True


class FakeContext:
    def __init__(self, page):
        self._page = page

    def new_page(self):
        return self._page

    def close(self):
        pass


class FakeBrowser:
    def __init__(self, page):
        self._page = page

    def new_context(self):
        return FakeContext(self._page)

    def close(self):
        pass


class FakePlaywright:
    def __init__(self, page):
        self._page = page

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    @property
    def chromium(self):
        page = self._page

        class Launcher:
            def launch(self, headless=True):
                return FakeBrowser(page)

        return Launcher()


def test_contact_entry_text_trims():
    assert contact_entry_text(" Ann ", "a@b.co", "", "Hi") == \
        "Ann <a@b.co> [] Hi"


def test_run_spec_mutations():
    base = {"full_name": "Ann", "email": "ann@x.co", "subject": "S",
            "message": "M", "submission_case": "complete",
            "scenario": "normal"}
    spec = _run_spec("fill-contact-form", base, 0, False)
    assert spec["submitted"]["message"] == "M"
    assert spec["expected"] == "Ann <ann@x.co> [S] M"
    assert spec["label"] == "Ann"
    missing = _run_spec("fill-contact-form",
                        {**base, "submission_case": "missing-message"},
                        0, False)
    assert missing["submitted"]["message"] == ""
    assert missing["expected"] == "Ann <ann@x.co> [S] "
    broken = _run_spec("fill-contact-form",
                       {**base, "submission_case": "invalid-email"},
                       0, False)
    assert broken["submitted"]["email"] == "not-an-email"
    project = _run_spec("create-project", {"project_name": "P"}, 0, False)
    assert project["expected"] == "P"


def test_submit_contact_form_success(tmp_path, monkeypatch):
    import playwright.sync_api
    page = ContactFakePage()
    monkeypatch.setattr(playwright.sync_api, "sync_playwright",
                        lambda: FakePlaywright(page))
    result = submit_contact_form(
        "Ann Lee", "ann@example.com", "Hello", "Nice site",
        trace_dir=tmp_path)
    assert result["status"] == "succeeded"
    assert result["success"] is True
    trace = json.loads(Path(result["trace_path"]).read_text())
    kinds = [e.get("action_type") for e in trace["events"]
             if e.get("action_type")]
    # Each action emits an attempted + a succeeded event.
    assert kinds.count("fill") == 8
    assert kinds.count("click") == 2
    assert kinds.count("navigate") == 2
    # No submitted values leak into run-started evidence.
    first = trace["events"][0]["evidence_references"]
    assert not any("ann@example.com" in ref for ref in first)


def test_submit_contact_form_invalid_email_fails(tmp_path, monkeypatch):
    import playwright.sync_api
    page = ContactFakePage()
    monkeypatch.setattr(playwright.sync_api, "sync_playwright",
                        lambda: FakePlaywright(page))
    result = submit_contact_form(
        "Ann Lee", "not-an-email", "Hello", "Nice site",
        trace_dir=tmp_path)
    assert result["status"] == "failed"
    assert result["success"] is False
    assert page.error == "Email address is invalid."
    assert page.items == []


def test_run_contact_replay_success_and_cancel(tmp_path):
    from benchmarks.observer import RecordingPage
    from chimera.safety import CancellationToken

    page = ContactFakePage()
    holder = {}

    def factory():
        browser = FakeBrowser(page)
        context = browser.new_context()
        holder["browser"] = browser
        return browser, context, RecordingPage(
            page, __import__("benchmarks.observer",
                             fromlist=["ActionLog"]).ActionLog(
                run_id="r"))

    outcome = run_contact_replay(
        name="Ann", email="ann@x.co", subject="S", message="M",
        url="http://contact/", trace_dir=tmp_path,
        page_factory=factory, run_id="r1")
    assert outcome.terminal_status == "succeeded"
    assert outcome.snapshot is not None
    assert outcome.snapshot["items"] == ["Ann <ann@x.co> [S] M"]
    assert outcome.snapshot["confirmation_visible"] is True
    assert len(outcome.action_log["records"]) >= 6

    token = CancellationToken()
    token.request("stop now")
    outcome2 = run_contact_replay(
        name="Ann", email="ann@x.co", subject="S", message="M",
        url="http://contact/", trace_dir=tmp_path, token=token,
        page_factory=factory, run_id="r2")
    assert outcome2.terminal_status == "cancelled"


def _wait_terminal(store, exec_id, timeout=10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        record = store.get_execution(exec_id)
        if record and record["status"] not in ("queued", "running"):
            return record
        time.sleep(0.05)
    raise AssertionError(f"{exec_id} never finished")


def test_executor_contact_chimera_success(tmp_path, monkeypatch):
    store = Store(tmp_path / "w.db")
    try:
        def fake_submit(name, email, subject, message, url=None,
                        trace_dir=None, cancel=None, observe=None,
                        browser_factory=None):
            browser, context, wrapped = browser_factory(object())
            wrapped.goto(url)
            for label, value in (("Full Name", name), ("Email", email),
                                 ("Subject", subject), ("Message", message)):
                wrapped.get_by_label(label).fill(value)
            wrapped.get_by_role("button", name="Send Message").click()
            observation = observe(wrapped) if observe else None
            trace_path = Path(trace_dir) / "agent.json"
            trace_path.parent.mkdir(parents=True, exist_ok=True)
            trace_path.write_text(json.dumps({"run_id": "r",
                                              "events": []}))
            context.close()
            browser.close()
            return {"success": True, "status": "succeeded",
                    "project_name": name, "error": None,
                    "trace_path": str(trace_path), "run_id": "r",
                    "observation": observation}

        monkeypatch.setattr("workbench.executor.submit_contact_form",
                            fake_submit)

        from benchmarks.observer import RecordingPage
        from workbench.executor import _ShotOnClose

        def contact_factory(log, shot_path):
            def factory(pw):
                page = ContactFakePage()
                browser = FakeBrowser(page)
                context = browser.new_context()
                shot = _ShotOnClose(context, page, shot_path)
                factory.holder["shot"] = shot
                return browser, shot, RecordingPage(page, log)
            factory.holder = {}
            return factory

        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=contact_factory)
        exec_id = ex.submit("fill-contact-form", "chimera", {
            "full_name": "Ann Lee", "email": "ann@example.com",
            "subject": "Hello", "message": "Nice site",
            "submission_case": "complete", "scenario": "normal"})
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "succeeded"
        assert record["verdict"] == "verified-success"
        assert record["workflow_id"] == "fill-contact-form"
        assert record["project_name"] == "Ann Lee"
        assert all(c["satisfied"] == 1 for c in record["checks"])
        kinds = [a["action_type"] for a in record["actions"]]
        assert kinds.count("fill") == 4
        assert record["progress"]["submitted"]["email"] == "ann@example.com"
    finally:
        store.close()


def test_executor_contact_baseline_missing_message(tmp_path, monkeypatch):
    from benchmarks.baseline_a import ReplayOutcome
    store = Store(tmp_path / "w.db")
    try:
        seen = {}

        def fake_replay(*, name, email, subject, message, url,
                        trace_dir, token=None, page_factory=None,
                        run_id=None, action_timeout_ms=None):
            seen.update(message=message)
            browser, context, wrapped = page_factory()
            wrapped.goto(url)
            context.close()
            browser.close()
            report_path = Path(trace_dir) / f"{run_id}.replay.json"
            report_path.write_text(json.dumps(
                {"schema": "x", "run_id": run_id,
                 "terminal_status": "succeeded", "steps": [],
                 "started_at": "t", "completed_at": "t"}))
            return ReplayOutcome(
                run_id=run_id, terminal_status="succeeded",
                report_path=str(report_path),
                snapshot={"confirmation_visible": False, "items": []},
                snapshot_ref=None, observation_error=None,
                action_log={}, error=None)

        monkeypatch.setattr("workbench.executor.run_contact_replay",
                            fake_replay)
        from tests.test_workbench_executor import (
            _fake_baseline_factory)
        ex = Executor(store, tmp_path / "wb",
                      baseline_factory=_fake_baseline_factory)
        exec_id = ex.submit("fill-contact-form", "baseline-a", {
            "full_name": "Ann", "email": "ann@x.co", "subject": "S",
            "message": "M", "submission_case": "missing-message",
            "scenario": "normal"})
        record = _wait_terminal(store, exec_id)
        assert seen["message"] == ""
        # Driver claims success, but nothing verifiable was submitted.
        assert record["verdict"] == "verified-failure"
        assert record["progress"]["submitted"]["message"] == ""
    finally:
        store.close()
