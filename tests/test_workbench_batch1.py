"""Tests for batch-1 read-only lookup workflows (scripted fakes).

Wikipedia, Wiktionary, and PyPI lookups run end to end against the
fakes in tests/fake_lookup.py with the real Executor, so no test
touches the live web.
"""

import time

import pytest

from adapters import wikipedia as wiki
from adapters import wiktionary as wikt
from adapters import pypi as pypi
from benchmarks.observer import ActionPolicy
from tests.fake_lookup import (
    FakePypiPage,
    FakeWikiPage,
    FakeWiktPage,
    _StubBrowser,
    _StubContext,
)
from workbench.executor import Executor, _run_spec
from workbench.store import Store
from workbench.workflows import (
    PYPI_LOOKUP,
    WIKIPEDIA_LOOKUP,
    WIKTIONARY_LOOKUP,
    WorkflowValidationError,
    get_workflow,
    list_workflows,
)


def _wiki_params(**overrides):
    base = {"query": "badminton", "pick": 1}
    base.update(overrides)
    return base


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


def test_registry_lists_wikipedia_chimera_only():
    assert get_workflow("wikipedia-article-lookup") is WIKIPEDIA_LOOKUP
    assert WIKIPEDIA_LOOKUP.origin == "external"
    assert WIKIPEDIA_LOOKUP.drivers == ("chimera",)
    assert "wikipedia-article-lookup" in [
        w.workflow_id for w in list_workflows()]


def test_wiki_params_validate():
    cleaned = WIKIPEDIA_LOOKUP.validate(_wiki_params())
    assert (cleaned["query"], cleaned["pick"]) == ("badminton", 1)
    with pytest.raises(WorkflowValidationError):
        WIKIPEDIA_LOOKUP.validate(_wiki_params(query="  "))
    with pytest.raises(WorkflowValidationError):
        WIKIPEDIA_LOOKUP.validate(_wiki_params(pick=0))
    with pytest.raises(WorkflowValidationError):
        WIKIPEDIA_LOOKUP.validate(_wiki_params(pick=6))


def test_wiki_baseline_rejected(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb")
        with pytest.raises(WorkflowValidationError):
            ex.submit("wikipedia-article-lookup", "baseline-a",
                      _wiki_params())
    finally:
        store.close()


def test_wiki_run_spec():
    spec = _run_spec("wikipedia-article-lookup",
                     _wiki_params(query="q", pick=2))
    assert spec["verify"] == "wiki"
    assert spec["expected"] == {"query": "q", "pick": 2}
    assert spec["url"] == wiki.HOME_URL
    assert isinstance(spec["policy"], ActionPolicy)


def test_wiki_url_guard():
    assert wiki.assert_approved_url("https://en.wikipedia.org/")
    assert wiki.assert_approved_url(wiki.search_url("badminton"))
    assert wiki.assert_approved_url("https://en.wikipedia.org/wiki/Badminton")
    for bad in ("https://evil.com/",
                "https://en.wikipedia.org/wiki/Special:Search",
                "https://en.wikipedia.org/wiki/A/B",
                "https://en.wikipedia.org/w/index.php?title=Special:Edit",
                "http://en.wikipedia.org/",
                "",
                None):
        with pytest.raises(wiki.UnapprovedURLError):
            wiki.assert_approved_url(bad)


def test_wiki_policy_allows_pages_denies_special():
    from workbench.executor import _wiki_policy

    policy = _wiki_policy()
    for url in (wiki.HOME_URL, wiki.search_url("q"),
                "https://en.wikipedia.org/wiki/Badminton"):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "allowed", url
    for url in ("https://en.wikipedia.org/wiki/Special:Search",
                "https://evil.com/"):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "denied", url


def _wiki_stages(**states):
    return [{"stage": name, "url": "https://en.wikipedia.org/x",
             "captured_at": "t", "state": state}
            for name, state in states.items()]


def test_wiki_verify_results_path():
    report = wiki.verify_wikipedia_lookup(
        {"url": "x"}, _wiki_stages(
            search={"redirected": False, "count": 3, "results": [
                {"title": "Badminton", "href": "/wiki/Badminton"}]},
            article={"url": "https://en.wikipedia.org/wiki/Badminton",
                     "heading": "Badminton", "summary": "x" * 50}),
        {"query": "q", "pick": 1})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("WI1", True), ("WI2", True)]


def test_wiki_verify_redirect_path():
    report = wiki.verify_wikipedia_lookup(
        {"url": "x"}, _wiki_stages(
            search={"redirected": True, "count": 0, "results": []},
            article={"url": "https://en.wikipedia.org/wiki/Badminton",
                     "heading": "Badminton", "summary": "x" * 50}),
        {"query": "badminton", "pick": 1})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("WI1", True), ("WI2", True)]


def test_wiki_verify_failures():
    report = wiki.verify_wikipedia_lookup(
        {"url": "x"}, _wiki_stages(
            search={"redirected": False, "count": 0, "results": []},
            article={"url": "", "heading": "", "summary": ""}),
        {"query": "q", "pick": 1})
    assert [c["satisfied"] for c in report["checks"]] == [False, False]
    assert wiki.verify_wikipedia_lookup(
        None, [], {"pick": 1})["status"] == "unavailable"


def test_wiki_end_to_end_results_path(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(FakeWikiPage()))
        exec_id = ex.submit("wikipedia-article-lookup", "chimera",
                            _wiki_params())
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "succeeded"
        assert record["verdict"] == "verified-success"
        assert [c["check_id"] for c in record["checks"]] == ["WI1", "WI2"]
        stages = wiki.stages_for_trace(record["trace_path"])
        assert [s["stage"] for s in stages] == ["search", "article"]
    finally:
        store.close()


def test_wiki_end_to_end_redirect_path(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(
                          FakeWikiPage(redirect=True)))
        exec_id = ex.submit("wikipedia-article-lookup", "chimera",
                            _wiki_params())
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "succeeded"
        assert record["verdict"] == "verified-success"
    finally:
        store.close()


def test_wiki_redirect_rejects_pick(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(
                          FakeWikiPage(redirect=True)))
        exec_id = ex.submit("wikipedia-article-lookup", "chimera",
                            _wiki_params(pick=2))
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "failed"
        assert record["verdict"] == "verified-failure"
        assert "cannot pick #2" in (record["error"] or "")
    finally:
        store.close()


# ---------------------------------------------------------------------------
# Wiktionary word lookup
# ---------------------------------------------------------------------------

def _wikt_params(**overrides):
    base = {"word": "badminton"}
    base.update(overrides)
    return base


def test_registry_lists_wiktionary_chimera_only():
    assert get_workflow("wiktionary-word-lookup") is WIKTIONARY_LOOKUP
    assert WIKTIONARY_LOOKUP.origin == "external"
    assert WIKTIONARY_LOOKUP.drivers == ("chimera",)
    assert "wiktionary-word-lookup" in [
        w.workflow_id for w in list_workflows()]


def test_wikt_params_validate():
    cleaned = WIKTIONARY_LOOKUP.validate(_wikt_params())
    assert cleaned["word"] == "badminton"
    with pytest.raises(WorkflowValidationError):
        WIKTIONARY_LOOKUP.validate(_wikt_params(word="  "))
    with pytest.raises(WorkflowValidationError):
        WIKTIONARY_LOOKUP.validate(_wikt_params(word="x" * 41))
    with pytest.raises(WorkflowValidationError):
        _run_spec("wiktionary-word-lookup", _wikt_params(word="bad!minton"))


def test_wikt_baseline_rejected(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb")
        with pytest.raises(WorkflowValidationError):
            ex.submit("wiktionary-word-lookup", "baseline-a",
                      _wikt_params())
    finally:
        store.close()


def test_wikt_run_spec():
    spec = _run_spec("wiktionary-word-lookup",
                     _wikt_params(word="magnolia"))
    assert spec["verify"] == "wikt"
    assert spec["expected"] == {"word": "magnolia"}
    assert spec["url"] == wikt.entry_url("magnolia")
    assert isinstance(spec["policy"], ActionPolicy)


def test_wikt_url_guard():
    assert wikt.assert_approved_url("https://en.wiktionary.org/")
    assert wikt.assert_approved_url(wikt.entry_url("badminton"))
    for bad in ("https://evil.com/",
                "https://en.wiktionary.org/wiki/Special:Search",
                "https://en.wiktionary.org/wiki/A/B",
                "http://en.wiktionary.org/",
                "",
                None):
        with pytest.raises(wikt.UnapprovedURLError):
            wikt.assert_approved_url(bad)
    with pytest.raises(ValueError):
        wikt.entry_url("bad!minton")


def test_wikt_policy_allows_entry_denies_special():
    from workbench.executor import _wikt_policy

    policy = _wikt_policy()
    for url in (wikt.HOME_URL, wikt.entry_url("badminton")):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "allowed", url
    for url in ("https://en.wiktionary.org/wiki/Special:Search",
                "https://evil.com/"):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "denied", url


def _wikt_stages(**states):
    return [{"stage": name, "url": "https://en.wiktionary.org/x",
             "captured_at": "t", "state": state}
            for name, state in states.items()]


def test_wikt_verify_success():
    report = wikt.verify_wiktionary_lookup(
        {"url": "x"}, _wikt_stages(
            entry={"heading": "badminton", "missing": False,
                   "definitions": 3, "first_def": "a racquet sport"}),
        {"word": "badminton"})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("WX1", True), ("WX2", True)]


def test_wikt_verify_failures():
    report = wikt.verify_wiktionary_lookup(
        {"url": "x"}, _wikt_stages(
            entry={"heading": "qqqzzz", "missing": True,
                   "definitions": 0, "first_def": ""}),
        {"word": "qqqzzz"})
    assert [c["satisfied"] for c in report["checks"]] == [False, False]
    report = wikt.verify_wiktionary_lookup(
        {"url": "x"}, _wikt_stages(
            entry={"heading": "badminton", "missing": False,
                   "definitions": 0, "first_def": ""}),
        {"word": "badminton"})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("WX1", True), ("WX2", False)]
    assert wikt.verify_wiktionary_lookup(
        None, [], {"word": "x"})["status"] == "unavailable"


def test_wikt_end_to_end_success(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(FakeWiktPage()))
        exec_id = ex.submit("wiktionary-word-lookup", "chimera",
                            _wikt_params())
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "succeeded"
        assert record["verdict"] == "verified-success"
        assert [c["check_id"] for c in record["checks"]] == ["WX1", "WX2"]
        stages = wikt.stages_for_trace(record["trace_path"])
        assert [s["stage"] for s in stages] == ["entry"]
    finally:
        store.close()


def test_wikt_end_to_end_missing_word(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(
                          FakeWiktPage(missing=True)))
        exec_id = ex.submit("wiktionary-word-lookup", "chimera",
                            _wikt_params(word="qqqzzz"))
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "failed"
        assert record["verdict"] == "verified-failure"
        assert "no dictionary entry" in (record["error"] or "")
    finally:
        store.close()


# ---------------------------------------------------------------------------
# PyPI package lookup
# ---------------------------------------------------------------------------

def _pypi_params(**overrides):
    base = {"package": "playwright"}
    base.update(overrides)
    return base


def test_registry_lists_pypi_chimera_only():
    assert get_workflow("pypi-package-lookup") is PYPI_LOOKUP
    assert PYPI_LOOKUP.origin == "external"
    assert PYPI_LOOKUP.drivers == ("chimera",)
    assert "pypi-package-lookup" in [
        w.workflow_id for w in list_workflows()]


def test_pypi_params_validate():
    cleaned = PYPI_LOOKUP.validate(_pypi_params())
    assert cleaned["package"] == "playwright"
    with pytest.raises(WorkflowValidationError):
        PYPI_LOOKUP.validate(_pypi_params(package="  "))
    with pytest.raises(WorkflowValidationError):
        PYPI_LOOKUP.validate(_pypi_params(package="x" * 61))
    with pytest.raises(WorkflowValidationError):
        _run_spec("pypi-package-lookup", _pypi_params(package="a/b"))


def test_pypi_baseline_rejected(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb")
        with pytest.raises(WorkflowValidationError):
            ex.submit("pypi-package-lookup", "baseline-a",
                      _pypi_params())
    finally:
        store.close()


def test_pypi_run_spec():
    spec = _run_spec("pypi-package-lookup",
                     _pypi_params(package="requests"))
    assert spec["verify"] == "pypi"
    assert spec["expected"] == {"package": "requests"}
    assert spec["url"] == pypi.project_url("requests")
    assert isinstance(spec["policy"], ActionPolicy)


def test_pypi_url_guard():
    assert pypi.assert_approved_url("https://pypi.org/")
    assert pypi.assert_approved_url(pypi.project_url("playwright"))
    for bad in ("https://evil.com/",
                "https://pypi.org/project/a/b",
                "https://pypi.org/account/login/",
                "http://pypi.org/",
                "",
                None):
        with pytest.raises(pypi.UnapprovedURLError):
            pypi.assert_approved_url(bad)
    with pytest.raises(ValueError):
        pypi.project_url("a/b")


def test_pypi_policy_allows_project_denies_login():
    from workbench.executor import _pypi_policy

    policy = _pypi_policy()
    for url in (pypi.HOME_URL, pypi.project_url("playwright")):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "allowed", url
    for url in ("https://pypi.org/account/login/",
                "https://evil.com/"):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "denied", url


def _pypi_stages(**states):
    return [{"stage": name, "url": "https://pypi.org/x",
             "captured_at": "t", "state": state}
            for name, state in states.items()]


def test_pypi_verify_success():
    report = pypi.verify_pypi_lookup(
        {"url": "x"}, _pypi_stages(
            package={"name": "playwright", "version": "1.64.1",
                     "summary": "x" * 50}),
        {"package": "playwright"})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("PY1", True), ("PY2", True)]


def test_pypi_verify_failures():
    report = pypi.verify_pypi_lookup(
        {"url": "x"}, _pypi_stages(
            package={"name": "", "version": "", "summary": ""}),
        {"package": "qqqzzz"})
    assert [c["satisfied"] for c in report["checks"]] == [False, False]
    report = pypi.verify_pypi_lookup(
        {"url": "x"}, _pypi_stages(
            package={"name": "playwright", "version": "", "summary": ""}),
        {"package": "playwright"})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("PY1", True), ("PY2", False)]
    assert pypi.verify_pypi_lookup(
        None, [], {"package": "x"})["status"] == "unavailable"


def test_pypi_end_to_end_success(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(FakePypiPage()))
        exec_id = ex.submit("pypi-package-lookup", "chimera",
                            _pypi_params())
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "succeeded"
        assert record["verdict"] == "verified-success"
        assert [c["check_id"] for c in record["checks"]] == ["PY1", "PY2"]
        stages = pypi.stages_for_trace(record["trace_path"])
        assert [s["stage"] for s in stages] == ["package"]
    finally:
        store.close()


def test_pypi_end_to_end_challenge_page(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(
                          FakePypiPage(challenge=True)))
        exec_id = ex.submit("pypi-package-lookup", "chimera",
                            _pypi_params(package="qqqzzz"))
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "failed"
        assert record["verdict"] == "verified-failure"
        assert "no PyPI project" in (record["error"] or "")
    finally:
        store.close()
