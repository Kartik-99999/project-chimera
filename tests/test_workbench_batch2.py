"""Tests for batch-2 read-only workflows (scripted fakes).

BBC headlines and GitHub profile run end to end against the fakes
in tests/fake_lookup.py with the real Executor, so no test touches
the live web.
"""

import time

import pytest

from adapters import bbc as bbc
from adapters import github as github
from benchmarks.observer import ActionPolicy
from tests.fake_lookup import (
    FakeBbcPage,
    FakeGithubPage,
    _StubBrowser,
    _StubContext,
)
from workbench.executor import Executor, _run_spec
from workbench.store import Store
from workbench.workflows import (
    BBC_HEADLINES,
    GITHUB_PROFILE,
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


# ---------------------------------------------------------------------------
# BBC headlines
# ---------------------------------------------------------------------------

def _bbc_params(**overrides):
    base = {"section": "news"}
    base.update(overrides)
    return base


def test_registry_lists_bbc_chimera_only():
    assert get_workflow("bbc-headlines") is BBC_HEADLINES
    assert BBC_HEADLINES.origin == "external"
    assert BBC_HEADLINES.drivers == ("chimera",)
    assert "bbc-headlines" in [w.workflow_id for w in list_workflows()]


def test_bbc_params_validate():
    cleaned = BBC_HEADLINES.validate(_bbc_params())
    assert cleaned["section"] == "news"
    assert BBC_HEADLINES.validate(_bbc_params(section="business"))[
        "section"] == "business"
    with pytest.raises(WorkflowValidationError):
        BBC_HEADLINES.validate(_bbc_params(section="sport"))
    with pytest.raises(WorkflowValidationError):
        _run_spec("bbc-headlines", _bbc_params(section="sport"))


def test_bbc_baseline_rejected(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb")
        with pytest.raises(WorkflowValidationError):
            ex.submit("bbc-headlines", "baseline-a", _bbc_params())
    finally:
        store.close()


def test_bbc_run_spec():
    spec = _run_spec("bbc-headlines", _bbc_params(section="business"))
    assert spec["verify"] == "bbc"
    assert spec["expected"] == {"section": "business"}
    assert spec["url"] == bbc.section_url("business")
    assert isinstance(spec["policy"], ActionPolicy)


def test_bbc_url_guard():
    assert bbc.assert_approved_url("https://www.bbc.com/")
    assert bbc.assert_approved_url(bbc.section_url("news"))
    assert bbc.assert_approved_url("https://www.bbc.com/news/")
    for bad in ("https://evil.com/",
                "https://www.bbc.com/sport",
                "https://www.bbc.com/news/world",
                "http://www.bbc.com/",
                "",
                None):
        with pytest.raises(bbc.UnapprovedURLError):
            bbc.assert_approved_url(bad)
    with pytest.raises(ValueError):
        bbc.section_url("sport")


def test_bbc_policy_allows_sections_denies_sport():
    from workbench.executor import _bbc_policy

    policy = _bbc_policy()
    for url in (bbc.HOME_URL, bbc.section_url("news"),
                bbc.section_url("technology")):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "allowed", url
    for url in ("https://www.bbc.com/sport",
                "https://www.bbc.com/news/world",
                "https://evil.com/"):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "denied", url


def _bbc_stages(**states):
    return [{"stage": name, "url": "https://www.bbc.com/news",
             "captured_at": "t", "state": state}
            for name, state in states.items()]


def test_bbc_verify_success():
    report = bbc.verify_bbc_headlines(
        {"url": "x"}, _bbc_stages(
            section={"url": "https://www.bbc.com/news",
                     "heading": "News", "count": 47,
                     "headlines": ["One thing happened",
                                   "Another thing happened"]}),
        {"section": "news"})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("BB1", True), ("BB2", True)]


def test_bbc_verify_failures():
    report = bbc.verify_bbc_headlines(
        {"url": "x"}, _bbc_stages(
            section={"url": "https://www.bbc.com/news",
                     "heading": "Something else", "count": 5,
                     "headlines": ["One thing happened"]}),
        {"section": "news"})
    assert [c["satisfied"] for c in report["checks"]] == [False, False]
    report = bbc.verify_bbc_headlines(
        {"url": "x"}, _bbc_stages(
            section={"url": "https://www.bbc.com/news",
                     "heading": "News", "count": 0, "headlines": []}),
        {"section": "news"})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("BB1", True), ("BB2", False)]
    assert bbc.verify_bbc_headlines(
        None, [], {"section": "news"})["status"] == "unavailable"


def test_bbc_end_to_end_success(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(FakeBbcPage()))
        exec_id = ex.submit("bbc-headlines", "chimera", _bbc_params())
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "succeeded"
        assert record["verdict"] == "verified-success"
        assert [c["check_id"] for c in record["checks"]] == ["BB1", "BB2"]
        stages = bbc.stages_for_trace(record["trace_path"])
        assert [s["stage"] for s in stages] == ["section"]
        assert len(stages[0]["state"]["headlines"]) == 3
    finally:
        store.close()


def test_bbc_end_to_end_empty_front(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(FakeBbcPage(empty=True)))
        exec_id = ex.submit("bbc-headlines", "chimera", _bbc_params())
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "failed"
        assert record["verdict"] == "verified-failure"
        assert "recorded no headlines" in (record["error"] or "")
    finally:
        store.close()


# ---------------------------------------------------------------------------
# GitHub profile
# ---------------------------------------------------------------------------

def _github_params(**overrides):
    base = {"username": "torvalds"}
    base.update(overrides)
    return base


def test_registry_lists_github_chimera_only():
    assert get_workflow("github-profile") is GITHUB_PROFILE
    assert GITHUB_PROFILE.origin == "external"
    assert GITHUB_PROFILE.drivers == ("chimera",)
    assert "github-profile" in [w.workflow_id for w in list_workflows()]


def test_github_params_validate():
    cleaned = GITHUB_PROFILE.validate(_github_params())
    assert cleaned["username"] == "torvalds"
    with pytest.raises(WorkflowValidationError):
        GITHUB_PROFILE.validate(_github_params(username="  "))
    with pytest.raises(WorkflowValidationError):
        GITHUB_PROFILE.validate(_github_params(username="x" * 40))
    with pytest.raises(WorkflowValidationError):
        _run_spec("github-profile", _github_params(username="-bad"))
    with pytest.raises(WorkflowValidationError):
        _run_spec("github-profile", _github_params(username="login"))


def test_github_baseline_rejected(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb")
        with pytest.raises(WorkflowValidationError):
            ex.submit("github-profile", "baseline-a", _github_params())
    finally:
        store.close()


def test_github_run_spec():
    spec = _run_spec("github-profile",
                     _github_params(username="octocat"))
    assert spec["verify"] == "github"
    assert spec["expected"] == {"username": "octocat"}
    assert spec["url"] == github.profile_url("octocat")
    assert isinstance(spec["policy"], ActionPolicy)


def test_github_url_guard():
    assert github.assert_approved_url("https://github.com/")
    assert github.assert_approved_url(github.profile_url("torvalds"))
    for bad in ("https://evil.com/",
                "https://github.com/login",
                "https://github.com/torvalds/linux",
                "http://github.com/",
                "",
                None):
        with pytest.raises(github.UnapprovedURLError):
            github.assert_approved_url(bad)
    with pytest.raises(ValueError):
        github.profile_url("-bad")
    with pytest.raises(ValueError):
        github.profile_url("login")


def test_github_policy_allows_profile_denies_login():
    from workbench.executor import _github_policy

    policy = _github_policy()
    for url in (github.HOME_URL, github.profile_url("torvalds"),
                "https://github.com/logins"):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "allowed", url
    for url in ("https://github.com/login",
                "https://github.com/login/",
                "https://github.com/torvalds/linux",
                "https://evil.com/"):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "denied", url


def _github_stages(**states):
    return [{"stage": name, "url": "https://github.com/torvalds",
             "captured_at": "t", "state": state}
            for name, state in states.items()]


def test_github_verify_success():
    report = github.verify_github_profile(
        {"url": "x"}, _github_stages(
            profile={"url": "https://github.com/torvalds",
                     "nickname": "torvalds", "name": "Linus Torvalds"}),
        {"username": "torvalds"})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("GH1", True), ("GH2", True)]


def test_github_verify_failures():
    report = github.verify_github_profile(
        {"url": "x"}, _github_stages(
            profile={"url": "https://github.com/qqqzzz",
                     "nickname": "", "name": ""}),
        {"username": "qqqzzz"})
    assert [c["satisfied"] for c in report["checks"]] == [False, False]
    report = github.verify_github_profile(
        {"url": "x"}, _github_stages(
            profile={"url": "https://github.com/torvalds",
                     "nickname": "torvalds", "name": ""}),
        {"username": "torvalds"})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("GH1", True), ("GH2", False)]
    assert github.verify_github_profile(
        None, [], {"username": "x"})["status"] == "unavailable"


def test_github_end_to_end_success(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(FakeGithubPage()))
        exec_id = ex.submit("github-profile", "chimera", _github_params())
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "succeeded"
        assert record["verdict"] == "verified-success"
        assert [c["check_id"] for c in record["checks"]] == ["GH1", "GH2"]
        stages = github.stages_for_trace(record["trace_path"])
        assert [s["stage"] for s in stages] == ["profile"]
    finally:
        store.close()


def test_github_end_to_end_missing_user(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(
                          FakeGithubPage(missing=True)))
        exec_id = ex.submit("github-profile", "chimera",
                            _github_params(username="qqqzzz"))
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "failed"
        assert record["verdict"] == "verified-failure"
        assert "no GitHub profile" in (record["error"] or "")
    finally:
        store.close()
