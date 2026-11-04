"""Tests for Baseline B (Muse Spark agent loop, no network/browser).

The model is scripted through ``FakeTransport`` and the page through a
scripted fake, so the loop, the action validation, the refusal paths,
and the trace/sidecar evidence are all exercised without a key.
"""

import json
from pathlib import Path
from types import SimpleNamespace

from benchmarks import baseline_b
from benchmarks.baseline_b import (
    MODEL_BASELINE_ID,
    model_executor,
    run_model,
    snapshot_elements,
    validate_action,
)
from chimera.llm import FakeTransport, MetaModelClient, completion_body


URL = "file:///demo/index.html?test=1"


def _client(*actions):
    """A model client scripted to emit the given action objects."""
    bodies = [completion_body(json.dumps(a)) for a in actions]
    return MetaModelClient(api_key="fake-key-for-tests",
                           transport=FakeTransport(bodies))


class _Row:
    def __init__(self, name="", value=None, fail=None):
        self._name = name
        self._value = value
        self._fail = fail
        self.filled = []
        self.clicked = 0

    def is_visible(self):
        return True

    def get_attribute(self, attr):
        if attr == "aria-label":
            return self._name or None
        return None

    def text_content(self, timeout=None):
        return self._name

    def input_value(self, timeout=None):
        if self._value is None:
            raise RuntimeError("not a field")
        return self._value

    def fill(self, value, timeout=None):
        if self._fail:
            raise RuntimeError(self._fail)
        self.filled.append(value)

    def click(self, timeout=None):
        if self._fail:
            raise RuntimeError(self._fail)
        self.clicked += 1


class _Rows:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return list(self._rows)

    def inner_text(self, timeout=None):
        return ""


class _Page:
    def __init__(self, rows):
        self._rows = rows
        self.url = URL
        self.gotos = []
        self.waits = []

    def locator(self, selector):
        return _Rows(self._rows)

    def goto(self, url, timeout=None):
        self.gotos.append(url)
        self.url = url

    def title(self):
        return "fake demo"

    def wait_for_timeout(self, ms):
        self.waits.append(ms)


class _Ctx:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class _Browser:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def _factory(rows):
    holder = {}

    def make(pw):
        page = _Page(rows)
        holder["page"] = page
        holder["ctx"] = _Ctx()
        holder["browser"] = _Browser()
        return holder["browser"], holder["ctx"], page

    make.holder = holder
    return make


def _rows():
    return [_Row(name="Project Name", value=""),
            _Row(name="Create Project")]


# -- validation (pure unit) ------------------------------------------------


def test_validate_action_accepts_the_allowlist():
    elements = [{"index": 0, "name": "a"}, {"index": 1, "name": "b"}]
    assert validate_action({"action": "click", "index": 1}, elements,
                           URL)[0] == "click"
    kind, params, _ = validate_action(
        {"action": "fill", "index": 0, "value": "x"}, elements, URL)
    assert (kind, params) == ("fill", {"index": 0, "value": "x"})
    assert validate_action({"action": "wait", "ms": 500}, elements,
                           URL)[0] == "wait"
    assert validate_action({"action": "navigate", "url": URL}, elements,
                           URL)[0] == "navigate"
    kind, params, _ = validate_action(
        {"action": "done", "claim": "success"}, elements, URL)
    assert (kind, params) == ("done", {"claim": "success"})


def test_validate_action_refuses_everything_else():
    elements = [{"index": 0, "name": "a"}]
    bad = [
        "click",
        {"action": "click", "index": 7},
        {"action": "click", "index": True},
        {"action": "fill", "index": 0},
        {"action": "fill", "index": 0, "value": "x" * 501},
        {"action": "wait", "ms": 99999},
        {"action": "navigate", "url": "https://evil.example/"},
        {"action": "navigate", "url": URL + "/../../etc/passwd"},
        {"action": "done", "claim": "maybe"},
        {"action": "delete"},
        {},
    ]
    for action in bad:
        kind, _, error = validate_action(action, elements, URL)
        assert kind is None and error, action


def test_snapshot_elements_indexes_visible_controls():
    page = _Page(_rows())
    elements, locators = snapshot_elements(page)
    assert [e["index"] for e in elements] == [0, 1]
    assert elements[0]["name"] == "Project Name"
    assert len(locators) == 2


# -- the loop ---------------------------------------------------------------


def test_run_model_happy_path_writes_trace_and_sidecar(tmp_path):
    client = _client(
        {"action": "fill", "index": 0, "value": "Acme",
         "reason": "enter the name"},
        {"action": "click", "index": 1, "reason": "create it"},
        {"action": "done", "claim": "success", "reason": "listed"},
    )
    factory = _factory(_rows())
    outcome = run_model(project_name="Acme", url=URL,
                        trace_dir=tmp_path, browser_factory=factory,
                        client=client)
    assert outcome.terminal_status == "succeeded"
    assert outcome.error is None
    assert outcome.model_calls == 3
    assert outcome.blocked_attempts == 0
    page = factory.holder["page"]
    assert page.gotos[0] == URL
    trace = json.loads(Path(outcome.trace_path).read_text(
        encoding="utf-8"))
    assert trace["terminal_status"] == "succeeded"
    attempted = [e["action_type"] for e in trace["events"]
                 if e["event_type"] == "action_attempted"]
    assert attempted == ["navigate", "fill", "click"]
    sidecar = json.loads(Path(outcome.model_report_path).read_text(
        encoding="utf-8"))
    assert sidecar["baseline"] == MODEL_BASELINE_ID
    assert len(sidecar["calls"]) == 3
    assert sidecar["calls"][0]["executed"] == "fill"
    assert factory.holder["ctx"].closed
    assert factory.holder["browser"].closed


def test_run_model_blocks_off_page_navigate(tmp_path):
    evil = "https://evil.example/steal"
    client = _client(*[{"action": "navigate", "url": evil,
                        "reason": "exfiltrate"}] * 3)
    factory = _factory(_rows())
    outcome = run_model(project_name="Acme", url=URL,
                        trace_dir=tmp_path, browser_factory=factory,
                        client=client)
    assert outcome.terminal_status == "failed"
    assert outcome.blocked_attempts == 3
    page = factory.holder["page"]
    assert evil not in page.gotos
    assert page.url == URL


def test_run_model_recovers_from_non_json(tmp_path):
    transport = FakeTransport([
        completion_body("I will now fill the form…"),
        completion_body(json.dumps({"action": "fill", "index": 0,
                                    "value": "Acme"})),
        completion_body(json.dumps({"action": "click", "index": 1})),
        completion_body(json.dumps({"action": "done",
                                    "claim": "success"})),
    ])
    client = MetaModelClient(api_key="fake", transport=transport)
    outcome = run_model(
        project_name="Acme", url=URL, trace_dir=tmp_path,
        browser_factory=_factory(_rows()), client=client)
    assert outcome.terminal_status == "succeeded"
    assert outcome.model_calls == 4


def test_run_model_done_failure_is_honest_failure(tmp_path):
    client = _client({"action": "done", "claim": "failure",
                      "reason": "button disabled"})
    outcome = run_model(
        project_name="Acme", url=URL, trace_dir=tmp_path,
        browser_factory=_factory(_rows()), client=client)
    assert outcome.terminal_status == "failed"
    assert "gave up" in (outcome.error or "")


def test_run_model_step_budget_exhaustion(tmp_path):
    client = _client(*[{"action": "wait", "ms": 10}] * 5)
    outcome = run_model(
        project_name="Acme", url=URL, trace_dir=tmp_path,
        browser_factory=_factory(_rows()), client=client,
        max_steps=2)
    assert outcome.terminal_status == "failed"
    assert "budget exhausted" in (outcome.error or "")
    assert outcome.model_calls == 2


def test_run_model_reports_model_errors(tmp_path):
    from chimera.llm import TransportError

    transport = FakeTransport([TransportError("boom")] * 9)
    client = MetaModelClient(api_key="fake", transport=transport,
                             max_retries=0, sleep=lambda s: None)
    outcome = run_model(
        project_name="Acme", url=URL, trace_dir=tmp_path,
        browser_factory=_factory(_rows()), client=client)
    assert outcome.terminal_status == "failed"
    assert "unreachable" in (outcome.error or "")


# -- executor seam ----------------------------------------------------------


def test_model_executor_returns_judged_execution(tmp_path):
    client = _client({"action": "done", "claim": "failure",
                      "reason": "nothing to do"})
    execution = model_executor(
        scenario=SimpleNamespace(id="S-NORM"),
        task_input=SimpleNamespace(project_name="Acme"),
        fault=SimpleNamespace(slow_ms=0, disabled=False),
        trace_dir=tmp_path, token=None, timeout_seconds=60.0,
        client=client, browser_factory=_factory(_rows()))
    assert execution.trace_path is not None
    assert Path(execution.trace_path).is_file()
    assert execution.reported_status == "failed"
    assert execution.episode_url.startswith("file://")
    assert isinstance(execution.action_log, dict)


def test_runner_accepts_baseline_b_dispatch(tmp_path):
    from benchmarks.manifest import load_manifest
    from benchmarks.runner import Runner, SUPPORTED_BASELINES

    assert MODEL_BASELINE_ID in SUPPORTED_BASELINES
    manifest = load_manifest(
        Path("benchmarks/manifests/dev-v1.json"))
    runner = Runner(manifest, output_path=tmp_path / "r.json",
                    trace_dir=tmp_path / "t",
                    baseline=MODEL_BASELINE_ID,
                    run_id="baseline-b-dispatch")
    assert runner.executor is baseline_b.model_executor
    assert runner.baseline == MODEL_BASELINE_ID


def test_model_manifest_loads_aligned_and_sized():
    from benchmarks.manifest import load_manifest
    from benchmarks.runner import check_policy_alignment

    manifest = load_manifest(
        Path("benchmarks/manifests/model-v1.json"))
    check_policy_alignment(manifest)
    assert manifest.manifest_id == "model-v1"
    assert len(manifest.cells(MODEL_BASELINE_ID)) == 6
    assert manifest.total_episodes(MODEL_BASELINE_ID) == 30
    assert manifest.sha256() == (
        "0336a1ded94d025ec432bf25da964615e34a8c953fa7c6e4b727bffa76588698"
    )
