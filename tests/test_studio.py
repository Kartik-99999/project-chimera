"""Tests for Workflow Studio (no browser).

Covers: definition validation (every error code), variable
resolution and secret redaction, the evidence-based recovery
engine against a scripted fake page, the independent step
verifier, workflow persistence (save/clone/version), executor
end-to-end through both drivers, and analytics over seeded
studio rows.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

import pytest

from benchmarks.observer import RecordingPage
from workbench import studio
from workbench.executor import Executor, _ShotOnClose
from workbench.store import Store


# -- scripted fake page -------------------------------------------------


class FakeStudioLocator:
    def __init__(self, page: "FakeStudioPage", selector: str) -> None:
        self._page = page
        self._selector = selector

    @property
    def first(self) -> "FakeStudioLocator":
        return self

    def count(self) -> int:
        return len(self._page._texts(self._selector))

    def is_visible(self, **kwargs: Any) -> bool:
        return bool(self._page._texts(self._selector))

    def all_text_contents(self) -> List[str]:
        return list(self._page._texts(self._selector))

    def input_value(self) -> str:
        return self._page.values.get(self._selector, "")

    def fill(self, value: str, **kwargs: Any) -> None:
        if self._selector in self._page.fail_fills:
            raise RuntimeError("fake fill failure")
        self._page.values[self._selector] = value

    def click(self, **kwargs: Any) -> None:
        self._page.clicks.append(self._selector)
        if self._selector in self._page.fail_clicks:
            raise RuntimeError("fake click failure")
        if self._selector == "#create":
            self._page.created = True
            name = self._page.values.get("#name", "")
            self._page.texts["body"] = f"created {name}" if name else ""

    def select_option(self, value: Any, **kwargs: Any) -> None:
        self._page.values[self._selector] = str(value)


class FakeStudioPage:
    """Minimal page: form, create button, confirmation, list."""

    def __init__(self, fail_clicks: frozenset = frozenset(),
                 fail_fills: frozenset = frozenset()) -> None:
        self.url = ""
        self.values: Dict[str, str] = {}
        self.texts: Dict[str, str] = {"body": ""}
        self.created = False
        self.clicks: List[str] = []
        self.fail_clicks = fail_clicks
        self.fail_fills = fail_fills

    def _texts(self, selector: str) -> List[str]:
        if selector in ("#name", "#create"):
            return [""]
        if selector == "body":
            return [self.texts.get("body", "")]
        if selector == "#confirm":
            name = self.values.get("#name", "")
            return [f"created {name}"] if self.created and name else []
        if selector == "#items li":
            return ["created"] if self.created else []
        return []

    def locator(self, selector: str, **kwargs: Any) -> FakeStudioLocator:
        return FakeStudioLocator(self, selector)

    def goto(self, url: str, **kwargs: Any) -> None:
        self.url = url

    def title(self) -> str:
        return "fake"

    def screenshot(self, path: Any = None, **kwargs: Any) -> bytes:
        if path:
            Path(path).write_bytes(b"fake-png")
        return b"fake-png"


class FakeContext:
    def close(self) -> None:
        pass


class FakeBrowser:
    def close(self) -> None:
        pass


def _definition(**overrides: Any) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "environment": "demo",
        "variables": [
            {"name": "project", "label": "Project", "secret": False,
             "default": "Acme"},
        ],
        "steps": [
            {"key": "go", "type": "navigate", "label": "Open app",
             "url": "demo"},
            {"key": "fill", "type": "fill", "label": "Name it",
             "selector": "#name", "value": "{{project}}"},
            {"key": "create", "type": "click", "label": "Create",
             "selector": "#create",
             "effect": {"kind": "visible", "selector": "#confirm"}},
            {"key": "done", "type": "verify-text", "label": "Confirm",
             "text": "created {{project}}"},
        ],
    }
    base.update(overrides)
    return base


# -- validation ----------------------------------------------------------


def test_valid_definition_passes() -> None:
    assert studio.validate_definition(_definition()) == []


def test_validation_detects_each_problem() -> None:
    def codes(definition: Dict[str, Any]) -> set:
        return {e["code"]
                for e in studio.validate_definition(definition)}

    assert "bad-environment" in codes(_definition(environment="prod"))
    assert "no-steps" in codes(_definition(steps=[]))
    bad_type = _definition()
    bad_type["steps"][0]["type"] = "purchase"
    assert "bad-type" in codes(bad_type)
    dup = _definition()
    dup["steps"][1]["key"] = "go"
    assert "duplicate-key" in codes(dup)
    bad_sel = _definition()
    bad_sel["steps"][1]["selector"] = "((unclosed"
    assert "bad-selector" in codes(bad_sel)
    assert studio.check_selector("#project-list li") is None
    assert studio.check_selector("input[name='x']") is None
    assert studio.check_selector("a[href=\"y") is not None
    bad_timeout = _definition()
    bad_timeout["steps"][0]["timeout_ms"] = 5
    assert "bad-timeout" in codes(bad_timeout)
    bad_attempts = _definition()
    bad_attempts["steps"][1]["max_attempts"] = 9
    assert "bad-attempts" in codes(bad_attempts)
    unknown_var = _definition()
    unknown_var["steps"][1]["value"] = "{{missing}}"
    assert "unknown-variable" in codes(unknown_var)
    bad_url = _definition()
    bad_url["steps"][0]["url"] = "https://example.com/"
    assert "bad-url" in codes(bad_url)
    unreachable = _definition()
    unreachable["steps"].append(
        {"key": "tail", "type": "verify-state", "label": "End",
         "assertions": [{"kind": "visible", "selector": "#confirm"}]})
    unreachable["steps"].append(
        {"key": "late", "type": "capture", "label": "Late"})
    assert "unreachable-step" in codes(unreachable)
    contra_text = _definition(steps=[
        {"key": "a", "type": "verify-text", "label": "A",
         "text": "hello", "expect": "present"},
        {"key": "b", "type": "verify-text", "label": "B",
         "text": "hello", "expect": "absent"},
    ])
    assert "contradiction" in codes(contra_text)
    contra_count = _definition(steps=[
        {"key": "a", "type": "verify-count", "label": "A",
         "selector": "#items li", "op": "eq", "count": 1},
        {"key": "b", "type": "verify-count", "label": "B",
         "selector": "#items li", "op": "eq", "count": 2},
    ])
    assert "contradiction" in codes(contra_count)
    secret_default = _definition(variables=[
        {"name": "pw", "label": "PW", "secret": True, "default": "x"}])
    assert "bad-variable" in codes(secret_default)


def test_faulted_demo_url_resolution() -> None:
    plain = studio._resolve_navigate_url("demo", "demo", {})
    assert plain.startswith("file://") and "slow" not in plain
    faulted = studio._resolve_navigate_url(
        "demo", "demo", {"slow_ms": 500, "disabled": True})
    assert "slow=500" in faulted and "disabled=1" in faulted
    assert studio._resolve_navigate_url(
        "/inventory.html", "saucedemo", {}) == \
        "https://www.saucedemo.com/inventory.html"
    assert studio.validate_env_params({"slow_ms": -1}) != []
    assert studio.validate_env_params({"disabled": True}) == []


def test_rendered_navigate_url_revalidated_at_runtime() -> None:
    """A {{var}} navigate URL must be re-checked AFTER rendering.

    Regression (local file read / SSRF): validate-time _check_url
    accepts any URL starting with '{{', and _act used to goto() the
    rendered value unchecked for the demo environment — so a value
    like file:///etc/passwd opened arbitrary local files.
    """
    from chimera.agent import get_demo_url

    page = FakeStudioPage()
    step = {"key": "go", "type": "navigate", "url": "{{u}}"}
    for hostile in ("file:///etc/passwd",
                    "file:///etc/hosts?k=1",
                    "https://evil.example/",
                    "file:///tmp/x/../../etc/passwd"):
        with pytest.raises(studio.StudioStepError, match="bundled pages"):
            studio._act(page, step, {"url": hostile}, 1000, "demo")
        assert "passwd" not in page.url and "evil.example" not in page.url
    studio._act(page, step, {"url": "demo"}, 1000, "demo")
    assert page.url == get_demo_url()


# -- variables and secrets -----------------------------------------------


def test_resolve_variables_and_redaction() -> None:
    definition = _definition(variables=[
        {"name": "user", "label": "User", "secret": False,
         "default": "bob"},
        {"name": "pw", "label": "Password", "secret": True},
    ])
    with pytest.raises(studio.StudioError, match="missing value"):
        studio.resolve_variables(definition, {})
    values = studio.resolve_variables(definition, {"pw": "s3cret"})
    assert values == {"user": "bob", "pw": "s3cret"}
    secrets = studio.secret_values(definition, values)
    assert studio.redact("typed s3cret as bob", secrets) == \
        "typed *** as bob"
    assert studio.substitute("hi {{user}}", values) == "hi bob"


# -- recovery engine -------------------------------------------------------


def test_chimera_skips_action_when_effect_satisfied() -> None:
    page = FakeStudioPage()
    page.values["#name"] = "Acme"
    page.created = True  # effect already present
    step = {"key": "c", "type": "click", "label": "Create",
            "selector": "#create",
            "effect": {"kind": "visible", "selector": "#confirm"}}
    record = studio.run_step_chimera(page, step, 1, {}, [], "demo",
                                     None)
    assert record["satisfied"] is True
    assert record["attempts"][0].get("skipped") is True
    assert page.clicks == []  # never acted


def test_chimera_refuses_blind_retry_of_non_idempotent() -> None:
    page = FakeStudioPage(fail_clicks=frozenset({"#create"}))
    step = {"key": "c", "type": "click", "label": "Create",
            "selector": "#create", "max_attempts": 3}
    record = studio.run_step_chimera(page, step, 1, {}, [], "demo",
                                     None)
    assert record["satisfied"] is False
    assert "retry-refused" in record["detail"] \
        or record["attempts"][-1].get("retry_refused") is True
    assert page.clicks == ["#create"]  # exactly one attempt


def test_chimera_retries_idempotent_to_success() -> None:
    page = FakeStudioPage()
    calls = {"n": 0}
    real_fill = FakeStudioLocator.fill

    def flaky(self: FakeStudioLocator, value: str, **kwargs: Any) -> None:
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("transient")
        real_fill(self, value, **kwargs)

    FakeStudioLocator.fill = flaky  # type: ignore[assignment]
    try:
        step = {"key": "f", "type": "fill", "label": "Fill",
                "selector": "#name", "value": "Acme",
                "max_attempts": 3}
        record = studio.run_step_chimera(page, step, 1, {}, [], "demo",
                                         None)
    finally:
        FakeStudioLocator.fill = real_fill  # type: ignore[assignment]
    assert record["satisfied"] is True
    assert len(record["attempts"]) == 2


def test_chimera_recovers_via_effect_gate() -> None:
    page = FakeStudioPage()
    page.created = True  # effect true although no click yet
    step = {"key": "c", "type": "click", "label": "Create",
            "selector": "#create", "max_attempts": 3,
            "effect": {"kind": "count", "selector": "#items li",
                       "op": "eq", "count": 1}}
    record = studio.run_step_chimera(page, step, 1, {}, [], "demo",
                                     None)
    assert record["satisfied"] is True
    assert page.clicks == []


def test_precondition_blocks_entry() -> None:
    page = FakeStudioPage()
    step = {"key": "c", "type": "click", "label": "Create",
            "selector": "#create",
            "precondition": {"kind": "visible",
                             "selector": "#missing"}}
    record = studio.run_step_chimera(page, step, 1, {}, [], "demo",
                                     None)
    assert record["satisfied"] is False
    assert "precondition" in record["detail"]
    assert page.clicks == []


def test_replay_single_attempt_and_no_wait_poll() -> None:
    page = FakeStudioPage(fail_clicks=frozenset({"#create"}))
    step = {"key": "c", "type": "click", "label": "Create",
            "selector": "#create", "max_attempts": 3}
    record = studio.run_step_replay(page, step, 1, {}, [], "demo",
                                    None)
    assert record["satisfied"] is False
    assert len(record["attempts"]) == 1
    assert record["attempts"][0].get("retry_refused") is None
    wait = {"key": "w", "type": "wait", "label": "Wait",
            "condition": "visible", "selector": "#never",
            "timeout_ms": 500}
    started = time.monotonic()
    record = studio.run_step_replay(page, wait, 2, {}, [], "demo",
                                    None)
    assert record["satisfied"] is False
    assert time.monotonic() - started < 0.4  # no polling


def test_post_act_confirmation_polls_until_settled() -> None:
    page = FakeStudioPage()
    reads = {"n": 0}
    real_visible = studio._visible_of

    def delayed(selector_page: Any, selector: str) -> bool:
        if selector == "#confirm":
            reads["n"] += 1
            if reads["n"] >= 3:
                return True
            return False
        return real_visible(selector_page, selector)

    studio._visible_of = delayed  # type: ignore[assignment]
    try:
        step = {"key": "c", "type": "click", "label": "Create",
                "selector": "#create", "timeout_ms": 2000,
                "effect": {"kind": "visible", "selector": "#confirm"}}
        record = studio.run_step_chimera(page, step, 1, {}, [], "demo",
                                         None)
    finally:
        studio._visible_of = real_visible  # type: ignore[assignment]
    assert record["satisfied"] is True
    assert reads["n"] >= 3  # first reads missed, confirmation waited


def test_wait_timeout_reports_honestly() -> None:
    page = FakeStudioPage()
    wait = {"key": "w", "type": "wait", "label": "Wait",
            "condition": "visible", "selector": "#never",
            "timeout_ms": 300}
    record = studio.run_step_chimera(page, wait, 1, {}, [], "demo",
                                     None)
    assert record["satisfied"] is False
    assert "timed out" in record["detail"]


# -- verifier ---------------------------------------------------------------


def test_verify_studio_run_marks_missing_unavailable() -> None:
    expected = {"steps": [
        {"key": "a", "order": 1, "type": "navigate",
         "label": "Go"},
        {"key": "b", "order": 2, "type": "click", "label": "Do"},
    ]}
    got = studio.verify_studio_run(
        {"url": "x"},
        [{"order": 1, "type": "navigate", "status": "passed",
          "satisfied": True, "detail": "url=x"}],
        expected)
    assert got["status"] == "verified"
    assert [c["check_id"] for c in got["checks"]] == [
        "01-navigate", "02-click"]
    assert got["checks"][0]["satisfied"] is True
    assert got["checks"][1]["satisfied"] is None
    empty = studio.verify_studio_run(None, [], expected)
    assert empty["status"] == "unavailable"


# -- persistence ------------------------------------------------------------


def test_store_round_trip_clone_and_versions(tmp_path: Path) -> None:
    store = Store(tmp_path / "w.db")
    try:
        wid = store.create_studio_workflow(
            {"name": "Demo", "environment": "demo",
             "env_params": {"slow_ms": 0}})
        assert store.get_studio_workflow(wid)["definition"] is None
        assert store.save_studio_version(wid, _definition()) == 1
        assert store.save_studio_version(wid, _definition()) == 2
        record = store.get_studio_workflow(wid)
        assert record["version"] == 2
        assert record["versions"] == [1, 2]
        assert len(store.list_studio_workflows()) == 1
        clone = store.clone_studio_workflow(wid)
        cloned = store.get_studio_workflow(clone)
        assert cloned["name"] == "Demo (copy)"
        assert cloned["version"] == 1
        assert cloned["definition"]["steps"] == \
            record["definition"]["steps"]
    finally:
        store.close()


# -- executor end to end ------------------------------------------------------


def _chimera_factory(page: FakeStudioPage):
    def make(log, shot_path):
        def factory(pw):
            shot = _ShotOnClose(FakeContext(), page, shot_path)
            factory.holder["shot"] = shot
            return FakeBrowser(), shot, RecordingPage(page, log)

        factory.holder = {}
        return factory

    return make


def _baseline_factory(page: FakeStudioPage):
    def make(log, shot_path, holder):
        def factory():
            shot = _ShotOnClose(FakeContext(), page, shot_path)
            holder.update(shot=shot, browser=FakeBrowser())
            return FakeBrowser(), shot, RecordingPage(page, log)

        return factory

    return make


def _wait_terminal(store: Store, exec_id: str,
                   timeout: float = 30.0) -> Dict[str, Any]:
    deadline = time.time() + timeout
    while time.time() < deadline:
        record = store.get_execution(exec_id)
        if record and record["status"] not in ("queued", "running"):
            return record
        time.sleep(0.05)
    raise AssertionError(f"{exec_id} never finished")


def _seed(store: Store) -> str:
    wid = store.create_studio_workflow(
        {"name": "Demo create", "environment": "demo",
         "env_params": {}})
    store.save_studio_version(wid, _definition())
    return wid


def test_executor_runs_both_drivers(tmp_path: Path) -> None:
    store = Store(tmp_path / "w.db")
    try:
        wid = _seed(store)
        executor = Executor(
            store, tmp_path / "wb",
            chimera_factory=_chimera_factory(FakeStudioPage()),
            baseline_factory=_baseline_factory(FakeStudioPage()))
        for driver in ("chimera", "baseline-a"):
            exec_id = executor.submit(
                f"studio:{wid}", driver, {"variables": {}})
            record = _wait_terminal(store, exec_id)
            assert record["status"] == "succeeded", record
            assert record["verdict"] == "verified-success", record
            assert record["origin"] == "local"
            assert record["scenario_id"] == "studio:demo:v1"
            checks = {r["check_id"]: r["satisfied"] for r in store.query(
                "SELECT check_id, satisfied FROM verification "
                "WHERE exec_id=?", (exec_id,))}
            assert checks == {"01-navigate": 1, "02-fill": 1,
                              "03-click": 1, "04-verify-text": 1}
    finally:
        store.close()


def test_executor_rejects_unknown_workflow_and_missing_vars(
        tmp_path: Path) -> None:
    from workbench.workflows import WorkflowValidationError

    store = Store(tmp_path / "w.db")
    try:
        executor = Executor(store, tmp_path / "wb")
        with pytest.raises(WorkflowValidationError):
            executor.submit("studio:nope", "chimera", {"variables": {}})
        wid = store.create_studio_workflow(
            {"name": "Need secret", "environment": "demo",
             "env_params": {}})
        definition = _definition(variables=[
            {"name": "project", "label": "Project", "secret": False,
             "default": "Acme"},
            {"name": "token", "label": "Token", "secret": True}])
        store.save_studio_version(wid, definition)
        with pytest.raises(WorkflowValidationError, match="missing value"):
            executor.submit(f"studio:{wid}", "chimera",
                            {"variables": {}})
    finally:
        store.close()


def test_secrets_never_persisted(tmp_path: Path) -> None:
    store = Store(tmp_path / "w.db")
    try:
        wid = store.create_studio_workflow(
            {"name": "Login", "environment": "demo",
             "env_params": {}})
        definition = _definition(
            variables=[
                {"name": "user", "label": "User", "secret": False,
                 "default": "bob"},
                {"name": "pw", "label": "Password", "secret": True},
            ],
            steps=[
                {"key": "go", "type": "navigate", "label": "Open",
                 "url": "demo"},
                {"key": "pw", "type": "fill", "label": "Password",
                 "selector": "#name", "value": "{{pw}}"},
            ])
        store.save_studio_version(wid, definition)
        executor = Executor(
            store, tmp_path / "wb",
            chimera_factory=_chimera_factory(FakeStudioPage()),
            baseline_factory=_baseline_factory(FakeStudioPage()))
        exec_id = executor.submit(
            f"studio:{wid}", "chimera",
            {"variables": {"pw": "super-secret-pw"}})
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "succeeded"
        blob = json.dumps(record)
        assert "super-secret-pw" not in blob
        assert "***" in blob  # redacted placeholder recorded instead
        traces = tmp_path / "wb" / "traces"
        for path in traces.iterdir():
            assert "super-secret-pw" not in path.read_text()
    finally:
        store.close()


def test_failed_step_yields_verified_failure(tmp_path: Path) -> None:
    store = Store(tmp_path / "w.db")
    try:
        wid = store.create_studio_workflow(
            {"name": "Bad wait", "environment": "demo",
             "env_params": {}})
        definition = _definition(steps=[
            {"key": "go", "type": "navigate", "label": "Open",
             "url": "demo"},
            {"key": "w", "type": "wait", "label": "Never",
             "condition": "visible", "selector": "#never",
             "timeout_ms": 300},
        ])
        store.save_studio_version(wid, definition)
        executor = Executor(
            store, tmp_path / "wb",
            chimera_factory=_chimera_factory(FakeStudioPage()),
            baseline_factory=_baseline_factory(FakeStudioPage()))
        exec_id = executor.submit(f"studio:{wid}", "chimera",
                                  {"variables": {}})
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "failed"
        assert record["verdict"] == "verified-failure"
        assert "timed out" in (record["error"] or "")
    finally:
        store.close()


def test_studio_analytics_over_seeded_rows(tmp_path: Path) -> None:
    from workbench import analytics

    store = Store(tmp_path / "w.db")
    try:
        wid = "studio:abc123"
        store.create_execution({
            "id": "r1", "workflow_id": wid, "driver": "chimera",
            "origin": "local", "scenario_id": "studio:demo:v1",
            "trial_kind": "adhoc", "status": "succeeded",
            "verdict": "verified-success", "duration_ms": 900})
        store.replace_verification("r1", [
            {"check_id": "01-navigate", "satisfied": True,
             "detail": ""},
            {"check_id": "02-click", "satisfied": True, "detail": ""},
        ])
        store.create_execution({
            "id": "r2", "workflow_id": wid, "driver": "baseline-a",
            "origin": "local", "scenario_id": "studio:demo:v1",
            "trial_kind": "adhoc", "status": "failed",
            "verdict": "verified-failure", "duration_ms": 1500,
            "error": "StudioStepError[click]: timed out"})
        store.replace_verification("r2", [
            {"check_id": "01-navigate", "satisfied": True,
             "detail": ""},
            {"check_id": "02-click", "satisfied": False,
             "detail": "timed out"},
        ])
        got = analytics.verification_coverage(
            store, {"workflow_id": wid})
        by_id = {c["check_id"]: c for c in got["checks"]}
        assert by_id["01-navigate"]["satisfied"] == 2
        assert by_id["02-click"]["failed"] == 1
        duel = analytics.drivers(store, {"workflow_id": wid})
        assert {d["driver"] for d in duel["drivers"]} == {
            "chimera", "baseline-a"}
        lat = analytics.latency(store, {"workflow_id": wid})
        assert lat["overall"]["n"] == 2
    finally:
        store.close()
