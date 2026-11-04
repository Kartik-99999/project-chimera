"""Tests for the user-session pilot workflows (scripted fakes).

Stack Overflow search and Amazon price check run end to end
against the fakes in tests/fake_lookup.py with the real
Executor, so no test touches the live web.
"""

import time

import pytest

from adapters import stackoverflow as so
from adapters import amazon as amazon
from benchmarks.observer import ActionPolicy
from tests.fake_lookup import (
    FakeAmazonPage,
    FakeSoPage,
    _StubBrowser,
    _StubContext,
)
from workbench.executor import Executor, _run_spec
from workbench.store import Store
from workbench.workflows import (
    AMAZON_PRICE,
    SO_SEARCH,
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
# Stack Overflow search
# ---------------------------------------------------------------------------

def _so_params(**overrides):
    base = {"query": "playwright python click"}
    base.update(overrides)
    return base


def test_registry_lists_so_user_session():
    assert get_workflow("stackoverflow-search") is SO_SEARCH
    assert SO_SEARCH.origin == "external"
    assert SO_SEARCH.drivers == ("chimera",)
    assert SO_SEARCH.sessions == ("clean", "user")
    assert "stackoverflow-search" in [
        w.workflow_id for w in list_workflows()]


def test_so_params_validate():
    cleaned = SO_SEARCH.validate(_so_params())
    assert cleaned["query"] == "playwright python click"
    with pytest.raises(WorkflowValidationError):
        SO_SEARCH.validate(_so_params(query="  "))
    with pytest.raises(WorkflowValidationError):
        SO_SEARCH.validate(_so_params(query="x" * 101))
    with pytest.raises(WorkflowValidationError):
        _run_spec("stackoverflow-search", _so_params(query="  "))


def test_so_baseline_rejected(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb")
        with pytest.raises(WorkflowValidationError):
            ex.submit("stackoverflow-search", "baseline-a", _so_params())
    finally:
        store.close()


def test_so_run_spec():
    spec = _run_spec("stackoverflow-search",
                     _so_params(query="pytest fixture"))
    assert spec["verify"] == "so"
    assert spec["expected"] == {"query": "pytest fixture"}
    assert spec["url"] == so.search_url("pytest fixture")
    assert isinstance(spec["policy"], ActionPolicy)


def test_so_url_guard():
    assert so.assert_approved_url("https://stackoverflow.com/")
    assert so.assert_approved_url(so.search_url("pytest"))
    for bad in ("https://evil.com/",
                "https://stackoverflow.com/search",
                "https://stackoverflow.com/search?q=",
                "https://stackoverflow.com/questions/123/x",
                "http://stackoverflow.com/",
                "",
                None):
        with pytest.raises(so.UnapprovedURLError):
            so.assert_approved_url(bad)
    with pytest.raises(ValueError):
        so.search_url("  ")


def test_so_policy_allows_search_denies_questions():
    from workbench.executor import _so_policy

    policy = _so_policy()
    for url in (so.HOME_URL, so.search_url("pytest")):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "allowed", url
    for url in ("https://stackoverflow.com/questions/123/x",
                "https://evil.com/"):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "denied", url


def _so_stages(**states):
    return [{"stage": name, "url": "https://stackoverflow.com/search?q=x",
             "captured_at": "t", "state": state}
            for name, state in states.items()]


def test_so_verify_success():
    report = so.verify_so_search(
        {"url": "x"}, _so_stages(
            search={"url": "https://stackoverflow.com/search?q=pytest",
                    "gate": False, "count": 3,
                    "titles": ["How do fixtures work?",
                               "Fake fixture scope"]}),
        {"query": "pytest"})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("SO1", True), ("SO2", True)]


def test_so_verify_failures():
    report = so.verify_so_search(
        {"url": "x"}, _so_stages(
            search={"url": "https://stackoverflow.com/search?q=qqqzzz",
                    "gate": False, "count": 0, "titles": []}),
        {"query": "qqqzzz"})
    assert [c["satisfied"] for c in report["checks"]] == [False, False]
    report = so.verify_so_search(
        {"url": "x"}, _so_stages(
            search={"url": "https://stackoverflow.com/search?q=x",
                    "gate": False, "count": 2, "titles": []}),
        {"query": "x"})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("SO1", True), ("SO2", False)]
    assert so.verify_so_search(
        None, [], {"query": "x"})["status"] == "unavailable"


def test_so_verify_gate_diagnosed():
    report = so.verify_so_search(
        {"url": "x"}, _so_stages(
            search={"url": "https://stackoverflow.com/search?q=x",
                    "gate": True, "count": 0, "titles": []}),
        {"query": "x"})
    assert report["status"] == "verified"
    assert [c["satisfied"] for c in report["checks"]] == [False, False]
    assert "bot gate" in report["checks"][0]["detail"]
    assert "sessions login" in report["checks"][0]["detail"]


def test_so_end_to_end_success(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(FakeSoPage()))
        exec_id = ex.submit("stackoverflow-search", "chimera", _so_params())
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "succeeded"
        assert record["verdict"] == "verified-success"
        assert record["session"] == "clean"
        assert [c["check_id"] for c in record["checks"]] == ["SO1", "SO2"]
        stages = so.stages_for_trace(record["trace_path"])
        assert [s["stage"] for s in stages] == ["search"]
        assert len(stages[0]["state"]["titles"]) == 3
    finally:
        store.close()


def test_so_end_to_end_gate(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(FakeSoPage(gate=True)))
        exec_id = ex.submit("stackoverflow-search", "chimera", _so_params())
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "failed"
        assert record["verdict"] == "verified-failure"
        assert "bot gate" in (record["error"] or "")
        assert "bot gate" in record["checks"][0]["detail"]
    finally:
        store.close()


# ---------------------------------------------------------------------------
# Amazon price check
# ---------------------------------------------------------------------------

def _amazon_params(**overrides):
    base = {"query": "kindle", "pick": 1}
    base.update(overrides)
    return base


def test_registry_lists_amazon_user_session():
    assert get_workflow("amazon-price-check") is AMAZON_PRICE
    assert AMAZON_PRICE.origin == "external"
    assert AMAZON_PRICE.drivers == ("chimera",)
    assert AMAZON_PRICE.sessions == ("clean", "user")
    assert "amazon-price-check" in [
        w.workflow_id for w in list_workflows()]


def test_amazon_params_validate():
    cleaned = AMAZON_PRICE.validate(_amazon_params())
    assert (cleaned["query"], cleaned["pick"]) == ("kindle", 1)
    with pytest.raises(WorkflowValidationError):
        AMAZON_PRICE.validate(_amazon_params(query="  "))
    with pytest.raises(WorkflowValidationError):
        AMAZON_PRICE.validate(_amazon_params(pick=0))
    with pytest.raises(WorkflowValidationError):
        AMAZON_PRICE.validate(_amazon_params(pick=6))


def test_amazon_baseline_rejected(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb")
        with pytest.raises(WorkflowValidationError):
            ex.submit("amazon-price-check", "baseline-a", _amazon_params())
    finally:
        store.close()


def test_amazon_run_spec():
    spec = _run_spec("amazon-price-check",
                     _amazon_params(query="q", pick=2))
    assert spec["verify"] == "amazon"
    assert spec["expected"] == {"query": "q", "pick": 2}
    assert spec["url"] == amazon.HOME_URL
    assert isinstance(spec["policy"], ActionPolicy)
    with pytest.raises(WorkflowValidationError):
        _run_spec("amazon-price-check", _amazon_params(query="  "))


def test_amazon_url_guard():
    assert amazon.assert_approved_url("https://www.amazon.com/")
    assert amazon.assert_approved_url(amazon.search_url("kindle"))
    assert amazon.assert_approved_url(
        "https://www.amazon.com/dp/B012345678/")
    assert amazon.assert_approved_url(
        "https://www.amazon.com/dp/B012345678/Some-Product-Name/")
    assert amazon.assert_approved_url(
        "https://www.amazon.com/Kindle-E-reader-6-Display/dp/B0H964FWGK/"
        "ref=sr_1_1")
    assert amazon.assert_approved_url(
        "https://www.amazon.com/gp/product/B012345678/")
    assert amazon.assert_approved_url(
        "https://www.amazon.com/gp/slredirect/picassoRedirect.html")
    for bad in ("https://evil.com/",
                "https://www.amazon.com/gp/cart/view.html",
                "https://www.amazon.com/gp/buy/spc/handlers/x",
                "https://www.amazon.com/ap/signin",
                "https://www.amazon.com/dp/abc",
                "https://www.amazon.com/s",
                "http://www.amazon.com/",
                "",
                None):
        with pytest.raises(amazon.UnapprovedURLError):
            amazon.assert_approved_url(bad)
    with pytest.raises(ValueError):
        amazon.search_url("  ")


def test_amazon_policy_denies_cart_and_login():
    from workbench.executor import _amazon_policy

    policy = _amazon_policy()
    for url in (amazon.HOME_URL, amazon.search_url("kindle"),
                "https://www.amazon.com/dp/B012345678/",
                "https://www.amazon.com/Kindle-E-reader-6-Display/dp/"
                "B0H964FWGK/ref=sr_1_1",
                "https://www.amazon.com/gp/slredirect/picassoRedirect.html"):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "allowed", url
    for url in ("https://www.amazon.com/gp/cart/view.html",
                "https://www.amazon.com/gp/buy/spc/handlers/x",
                "https://www.amazon.com/ap/signin",
                "https://evil.com/"):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "denied", url


def _amazon_stages(**states):
    return [{"stage": name, "url": "https://www.amazon.com/x",
             "captured_at": "t", "state": state}
            for name, state in states.items()]


def test_amazon_verify_success():
    report = amazon.verify_amazon_price(
        {"url": "x"}, _amazon_stages(
            search={"gate": False, "count": 3, "results": [
                {"name": "Fake Kindle", "href": "/dp/B012345678/"}]},
            product={"url": "https://www.amazon.com/dp/B012345678/",
                     "gate": False, "name": "Fake Kindle",
                     "price": "$129.99"}),
        {"query": "kindle", "pick": 1})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("AM1", True), ("AM2", True)]


def test_amazon_verify_failures():
    report = amazon.verify_amazon_price(
        {"url": "x"}, _amazon_stages(
            search={"gate": False, "count": 0, "results": []},
            product={"url": "", "gate": False, "name": "",
                     "price": ""}),
        {"query": "q", "pick": 1})
    assert [c["satisfied"] for c in report["checks"]] == [False, False]
    report = amazon.verify_amazon_price(
        {"url": "x"}, _amazon_stages(
            search={"gate": False, "count": 3, "results": [
                {"name": "Fake Kindle", "href": "/dp/B012345678/"}]},
            product={"url": "https://www.amazon.com/dp/B012345678/",
                     "gate": False, "name": "Something Else",
                     "price": "$9.99"}),
        {"query": "kindle", "pick": 1})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("AM1", True), ("AM2", False)]
    assert amazon.verify_amazon_price(
        None, [], {"pick": 1})["status"] == "unavailable"


def test_amazon_verify_gate_diagnosed():
    report = amazon.verify_amazon_price(
        {"url": "x"}, _amazon_stages(
            search={"gate": True, "count": 0, "results": []},
            product={"url": "", "gate": False, "name": "",
                     "price": ""}),
        {"query": "kindle", "pick": 1})
    assert report["status"] == "verified"
    assert [c["satisfied"] for c in report["checks"]] == [False, False]
    assert "bot gate" in report["checks"][0]["detail"]
    assert "sessions login" in report["checks"][0]["detail"]


def test_amazon_end_to_end_success(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(FakeAmazonPage()))
        exec_id = ex.submit("amazon-price-check", "chimera",
                            _amazon_params(pick=2))
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "succeeded"
        assert record["verdict"] == "verified-success"
        assert record["session"] == "clean"
        assert [c["check_id"] for c in record["checks"]] == ["AM1", "AM2"]
        stages = amazon.stages_for_trace(record["trace_path"])
        assert [s["stage"] for s in stages] == ["search", "product"]
        assert stages[1]["state"]["price"] == "$129.99"
    finally:
        store.close()


def test_amazon_end_to_end_pick_out_of_range(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(FakeAmazonPage()))
        exec_id = ex.submit("amazon-price-check", "chimera",
                            _amazon_params(pick=5))
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "failed"
        assert record["verdict"] == "verified-failure"
        assert "cannot pick #5" in (record["error"] or "")
    finally:
        store.close()


def test_amazon_dog_page_reads_as_gate():
    page = FakeAmazonPage(dog=True)
    page.goto("https://www.amazon.com/s?k=kindle")
    state = amazon.read_search_state(page)
    assert state["gate"] is True
    assert state["count"] == 0
    page = FakeAmazonPage()
    page.goto("https://www.amazon.com/s?k=kindle")
    assert amazon.read_search_state(page)["gate"] is False


def test_amazon_search_pairs_row_link_with_joined_title():
    # Live rows carry brand + title as separate h2 spans with the
    # product anchors outside the h2: each row must pair its own
    # first /dp/ link with its joined spans (regression: the old
    # page-wide `h2 a` selector matched nothing live).
    page = FakeAmazonPage()
    page.goto("https://www.amazon.com/s?k=kindle")
    state = amazon.read_search_state(page)
    assert state["gate"] is False
    assert state["count"] == 3
    assert state["results"][0] == {
        "name": "FakeBrand Fake Kindle E-reader WiFi 16GB",
        "href": "/dp/B012345678/"}
    assert state["results"][1]["name"] == \
        "FakeBrand Fake Echo Dot 5th Gen"
    assert state["results"][2]["href"].endswith("picassoRedirect.html")


def test_amazon_verify_accepts_listing_head_of_title():
    # Listing titles may be truncated heads of the product-page
    # title; containment still verifies, a different product fails.
    report = amazon.verify_amazon_price(
        {"url": "x"}, _amazon_stages(
            search={"gate": False, "count": 3, "results": [
                {"name": "FakeBrand Fake Kindle E-reader",
                 "href": "/dp/B012345678/"}]},
            product={"url": "https://www.amazon.com/dp/B012345678/",
                     "gate": False,
                     "name": "FakeBrand Fake Kindle E-reader WiFi 16GB",
                     "price": "$129.99"}),
        {"query": "kindle", "pick": 1})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("AM1", True), ("AM2", True)]
    report = amazon.verify_amazon_price(
        {"url": "x"}, _amazon_stages(
            search={"gate": False, "count": 3, "results": [
                {"name": "FakeBrand Fake Kindle E-reader",
                 "href": "/dp/B012345678/"}]},
            product={"url": "https://www.amazon.com/dp/B012345678/",
                     "gate": False, "name": "Unrelated Toaster Oven",
                     "price": "$129.99"}),
        {"query": "kindle", "pick": 1})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("AM1", True), ("AM2", False)]


def test_amazon_end_to_end_gate(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(
                          FakeAmazonPage(gate=True)))
        exec_id = ex.submit("amazon-price-check", "chimera",
                            _amazon_params())
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "failed"
        assert record["verdict"] == "verified-failure"
        assert "bot gate" in (record["error"] or "")
        assert "bot gate" in record["checks"][0]["detail"]
    finally:
        store.close()
