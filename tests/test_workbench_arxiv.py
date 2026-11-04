"""Tests for the arXiv paper-search workflow (scripted fakes).

Runs end to end against FakeArxivPage in tests/fake_lookup.py with
the real Executor, so no test touches the live web.
"""

import time

import pytest

from adapters import arxiv as arxiv
from benchmarks.observer import ActionPolicy
from tests.fake_lookup import (
    FakeArxivPage,
    _StubBrowser,
    _StubContext,
)
from workbench.executor import Executor, _run_spec
from workbench.store import Store
from workbench.workflows import (
    ARXIV_SEARCH,
    WorkflowValidationError,
    get_workflow,
    list_workflows,
)


def _fake_factory(page):
    def make(log, shot_path):
        from benchmarks.observer import RecordingPage
        from workbench.executor import _ShotOnClose

        def factory(pw):
            shot = _ShotOnClose(_StubContext(), page, shot_path)
            return _StubBrowser(), shot, RecordingPage(page, log)

        return factory

    return make


def _wait_terminal(store, exec_id, timeout=30.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        record = store.get_execution(exec_id)
        if record and record["status"] not in ("queued", "running"):
            return record
        time.sleep(0.05)
    raise AssertionError(f"{exec_id} never finished")


def _arxiv_params(**overrides):
    base = {"query": "transformer"}
    base.update(overrides)
    return base


def test_registry_lists_arxiv_chimera_only():
    assert get_workflow("arxiv-search") is ARXIV_SEARCH
    assert ARXIV_SEARCH.origin == "external"
    assert ARXIV_SEARCH.drivers == ("chimera",)
    assert "arxiv-search" in [w.workflow_id for w in list_workflows()]


def test_arxiv_params_validate():
    cleaned = ARXIV_SEARCH.validate(_arxiv_params())
    assert cleaned["query"] == "transformer"
    with pytest.raises(WorkflowValidationError):
        ARXIV_SEARCH.validate(_arxiv_params(query="  "))
    with pytest.raises(WorkflowValidationError):
        ARXIV_SEARCH.validate(_arxiv_params(query="x" * 101))
    with pytest.raises(WorkflowValidationError):
        _run_spec("arxiv-search", _arxiv_params(query="  "))


def test_arxiv_baseline_rejected(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb")
        with pytest.raises(WorkflowValidationError):
            ex.submit("arxiv-search", "baseline-a", _arxiv_params())
    finally:
        store.close()


def test_arxiv_run_spec():
    spec = _run_spec("arxiv-search", _arxiv_params(query="diffusion"))
    assert spec["verify"] == "arxiv"
    assert spec["expected"] == {"query": "diffusion"}
    assert spec["url"] == arxiv.search_url("diffusion")
    assert isinstance(spec["policy"], ActionPolicy)


def test_arxiv_url_guard():
    assert arxiv.assert_approved_url("https://arxiv.org/")
    assert arxiv.assert_approved_url(arxiv.search_url("transformer"))
    for bad in ("https://evil.com/",
                "https://arxiv.org/search/",
                "https://arxiv.org/search/?query=",
                "https://arxiv.org/abs/1706.03762",
                "http://arxiv.org/",
                "",
                None):
        with pytest.raises(arxiv.UnapprovedURLError):
            arxiv.assert_approved_url(bad)
    with pytest.raises(ValueError):
        arxiv.search_url("  ")


def test_arxiv_policy_allows_search_denies_abs():
    from workbench.executor import _arxiv_policy

    policy = _arxiv_policy()
    for url in (arxiv.HOME_URL, arxiv.search_url("transformer")):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "allowed", url
    for url in ("https://arxiv.org/abs/1706.03762",
                "https://evil.com/"):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "denied", url


def _arxiv_stages(**states):
    return [{"stage": name, "url": "https://arxiv.org/search/?query=x",
             "captured_at": "t", "state": state}
            for name, state in states.items()]


def test_arxiv_verify_success():
    report = arxiv.verify_arxiv_search(
        {"url": "x"}, _arxiv_stages(
            search={"url": "https://arxiv.org/search/?query=transformer",
                    "summary": "Showing 1–50 of 183,731 results",
                    "count": 50,
                    "titles": ["Attention Is All You Need",
                               "Fake Transformers"]}),
        {"query": "transformer"})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("AX1", True), ("AX2", True)]


def test_arxiv_verify_failures():
    report = arxiv.verify_arxiv_search(
        {"url": "x"}, _arxiv_stages(
            search={"url": "https://arxiv.org/search/?query=qqqzzz",
                    "summary": "Search", "count": 0, "titles": []}),
        {"query": "qqqzzz"})
    assert [c["satisfied"] for c in report["checks"]] == [False, False]
    report = arxiv.verify_arxiv_search(
        {"url": "x"}, _arxiv_stages(
            search={"url": "https://arxiv.org/search/?query=x",
                    "summary": "Showing results", "count": 5,
                    "titles": []}),
        {"query": "x"})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("AX1", True), ("AX2", False)]
    assert arxiv.verify_arxiv_search(
        None, [], {"query": "x"})["status"] == "unavailable"


def test_arxiv_end_to_end_success(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(FakeArxivPage()))
        exec_id = ex.submit("arxiv-search", "chimera", _arxiv_params())
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "succeeded"
        assert record["verdict"] == "verified-success"
        assert [c["check_id"] for c in record["checks"]] == ["AX1", "AX2"]
        stages = arxiv.stages_for_trace(record["trace_path"])
        assert [s["stage"] for s in stages] == ["search"]
        assert len(stages[0]["state"]["titles"]) == 3
    finally:
        store.close()


def test_arxiv_end_to_end_no_matches(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(
                          FakeArxivPage(empty=True)))
        exec_id = ex.submit("arxiv-search", "chimera",
                            _arxiv_params(query="qqqzzz"))
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "failed"
        assert record["verdict"] == "verified-failure"
        assert "returned no papers" in (record["error"] or "")
    finally:
        store.close()
