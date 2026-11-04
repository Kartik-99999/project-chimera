"""Tests for the flipkart-add-to-cart workbench workflow (fake market).

Adapter guards and F-check verdicts are pure unit tests; the driver
runs end to end against the scripted fake with the real Executor,
so no test touches the live marketplace.
"""

import json
import time
from pathlib import Path

import pytest

from adapters import flipkart as adapter
from benchmarks.observer import ActionPolicy
from tests.fake_flipkart import (
    FakeFlipBrowser,
    FakeFlipContext,
    FakeFlipPage,
)
from workbench.executor import Executor, _run_spec
from workbench.store import Store
from workbench.workflows import (
    FLIPKART_ADD_TO_CART,
    WorkflowValidationError,
    get_workflow,
    list_workflows,
)


def _params(**overrides):
    base = {"query": "yonex badminton", "pick": 1}
    base.update(overrides)
    return base


def _flip_chimera_factory(page):
    from benchmarks.observer import RecordingPage
    from workbench.executor import _ShotOnClose

    def make(log, shot_path):
        def factory(pw):
            browser = FakeFlipBrowser()
            context = FakeFlipContext()
            shot = _ShotOnClose(context, page, shot_path)
            factory.holder["shot"] = shot
            return browser, shot, RecordingPage(page, log)

        factory.holder = {}
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


def test_registry_lists_flipkart_chimera_only_with_external_origin():
    assert get_workflow("flipkart-add-to-cart") is FLIPKART_ADD_TO_CART
    assert FLIPKART_ADD_TO_CART.origin == "external"
    assert FLIPKART_ADD_TO_CART.drivers == ("chimera",)
    assert "flipkart-add-to-cart" in [w.workflow_id for w in list_workflows()]


def test_flipkart_params_validate():
    cleaned = FLIPKART_ADD_TO_CART.validate(_params())
    assert (cleaned["query"], cleaned["pick"]) == ("yonex badminton", 1)
    with pytest.raises(WorkflowValidationError):
        FLIPKART_ADD_TO_CART.validate(_params(query="  "))
    with pytest.raises(WorkflowValidationError):
        FLIPKART_ADD_TO_CART.validate(_params(query="x" * 81))
    with pytest.raises(WorkflowValidationError):
        FLIPKART_ADD_TO_CART.validate(_params(pick=0))
    with pytest.raises(WorkflowValidationError):
        FLIPKART_ADD_TO_CART.validate(_params(pick=6))


def test_baseline_driver_rejected(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb")
        with pytest.raises(WorkflowValidationError):
            ex.submit("flipkart-add-to-cart", "baseline-a", _params())
    finally:
        store.close()


def test_run_spec_builds_flipkart():
    spec = _run_spec("flipkart-add-to-cart", _params(query="q", pick=2))
    assert spec["verify"] == "flipkart"
    assert spec["expected"] == {"query": "q", "pick": 2}
    assert spec["submitted"] == {"query": "q", "pick": 2}
    assert spec["url"] == adapter.HOME_URL
    assert spec["snapshot_page"] is adapter.capture_end_snapshot
    policy = spec["policy"]
    assert isinstance(policy, ActionPolicy)
    assert adapter.HOME_URL in policy.permitted_urls
    assert adapter.VIEWCART_URL in policy.permitted_urls


def test_approved_url_guard():
    assert adapter.assert_approved_url("https://www.flipkart.com/")
    assert adapter.assert_approved_url(
        "https://www.flipkart.com/search?q=yonex")
    assert adapter.assert_approved_url(
        "https://www.flipkart.com/some-slug/p/itmFAKE0001?pid=X")
    assert adapter.assert_approved_url(
        "https://www.flipkart.com/viewcart?marketplace=FLIPKART")
    for bad in ("https://evil.com/",
                "https://www.flipkart.com.evil.com/",
                "https://www.flipkart.com/checkout/init",
                "https://www.flipkart.com/order/123",
                "https://www.flipkart.com/account/login",
                "https://www.flipkart.com/p/itmFAKE0001",
                "http://www.flipkart.com/",
                "",
                None):
        with pytest.raises(adapter.UnapprovedURLError):
            adapter.assert_approved_url(bad)


def test_policy_allows_pages_denies_checkout():
    from workbench.executor import _flipkart_policy

    policy = _flipkart_policy()
    allowed = [
        adapter.HOME_URL,
        adapter.search_url("yonex badminton"),
        "https://www.flipkart.com/a-b/p/itmX?pid=Y",
        adapter.VIEWCART_URL,
    ]
    for url in allowed:
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "allowed", url
    for url in ("https://www.flipkart.com/checkout/init",
                "https://www.flipkart.com/a-b/p/itmX/extra",
                "https://evil.com/"):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "denied", url


def _stages(**states):
    return [{"stage": name, "url": "https://www.flipkart.com/x",
             "captured_at": "t", "state": state}
            for name, state in states.items()]


def _full_states():
    href = "/yonex-gr/p/itmFAKE0001?pid=X"
    title = "YONEX GR 303i Black, Red Strung Badminton Racquet"
    return {
        "search": {"count": 3, "results": [
            {"title": title, "href": href},
            {"title": "Other result here", "href": "/o/p/itm2"}]},
        "product": {"url": adapter.APPROVED_ORIGIN + href,
                    "title": title + " - Buy Online | Flipkart.com",
                    "add_visible": True, "added": True},
        "cart": {"badge": "1", "reached": True, "items": [
            {"name": title + " (Pack of: 1)", "qty": "1"}],
            "total": "₹599", "empty": False},
    }


def test_verify_success():
    report = adapter.verify_flipkart_cart(
        {"url": "x"}, _stages(**_full_states()), {"query": "q", "pick": 1})
    assert report["status"] == "verified"
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("F1", True), ("F2", True), ("F3", True)]


def test_verify_pick_out_of_range():
    report = adapter.verify_flipkart_cart(
        {"url": "x"}, _stages(**_full_states()), {"query": "q", "pick": 5})
    assert [c["satisfied"] for c in report["checks"]] == [False, False, False]


def test_verify_empty_cart_and_wrong_item():
    states = _full_states()
    states["cart"] = {"badge": "0", "reached": True, "items": [],
                      "total": None, "empty": True}
    report = adapter.verify_flipkart_cart(
        {"url": "x"}, _stages(**states), {"query": "q", "pick": 1})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("F1", True), ("F2", True), ("F3", False)]
    states["cart"]["items"] = [{"name": "A completely different product",
                                "qty": "1"}]
    states["cart"]["empty"] = False
    report = adapter.verify_flipkart_cart(
        {"url": "x"}, _stages(**states), {"query": "q", "pick": 1})
    assert report["checks"][2] == {
        "check_id": "F3", "satisfied": False,
        "detail": report["checks"][2]["detail"]}
    assert "not the picked" in report["checks"][2]["detail"]


def test_search_reader_skips_badges_and_prices():
    rows = [
        ("Bestseller", "/yonex-gr/p/itm1?pid=X"),
        ("YONEX GR 303i Black, Red Strung Badminton Racquet",
         "/yonex-gr/p/itm1?pid=X"),
        ("₹589₹1,04943% off", "/yonex-gr/p/itm1?pid=X"),
        ("YONEX Astrox Attack 9 White Strung Badminton Racquet",
         "/yonex-astrox/p/itm2?pid=Y"),
    ]

    class _StubLink:
        def __init__(self, title, href):
            self._title, self._href = title, href

        def get_attribute(self, name, **kwargs):
            return self._href if name == "href" else None

        def text_content(self, **kwargs):
            return self._title

    class _StubLinks:
        def count(self):
            return len(rows)

        def nth(self, i):
            title, href = rows[i]
            return _StubLink(title, href)

    class _StubPage:
        def locator(self, selector):
            assert selector == adapter.SEL_RESULT_LINK
            return _StubLinks()

    state = adapter.read_search_state(_StubPage())
    assert state["count"] == 4
    assert [r["title"] for r in state["results"]] == [
        "YONEX GR 303i Black, Red Strung Badminton Racquet",
        "YONEX Astrox Attack 9 White Strung Badminton Racquet"]


def test_verify_unavailable_without_evidence():
    assert adapter.verify_flipkart_cart(None, [], {"pick": 1}) == {
        "status": "unavailable", "checks": []}


def test_chimera_flipkart_end_to_end(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(
            store, tmp_path / "wb",
            chimera_factory=_flip_chimera_factory(FakeFlipPage()))
        exec_id = ex.submit("flipkart-add-to-cart", "chimera", _params())
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "succeeded"
        assert record["verdict"] == "verified-success"
        assert record["origin"] == "external"
        assert [c["check_id"] for c in record["checks"]] == ["F1", "F2", "F3"]
        assert all(c["satisfied"] == 1 for c in record["checks"])
        kinds = [a["action_type"] for a in record["actions"]]
        assert "navigate" in kinds and "fill" in kinds and "click" in kinds
        assert record["screenshot_path"] is not None
        assert Path(record["screenshot_path"]).read_bytes() == b"fake-png"
        assert record["snapshot_path"] is not None
        stages_path = adapter.stages_path_for_trace(record["trace_path"])
        stages = adapter.read_stages_file(stages_path)
        assert [s["stage"] for s in stages] == [
            "search", "product", "product", "cart"]
        # Every observed action judged allowed: no denied, no unknown.
        judged = json.loads(Path(record["actions_path"]).read_text(
            encoding="utf-8"))
        decisions = {r["policy"] for r in judged["records"]}
        assert decisions == {"allowed"}, decisions
        assert record["progress"]["params"] == _params()
    finally:
        store.close()


def test_close_browser_runs_on_calling_thread_and_notes_errors(tmp_path):
    """_close_browser must close inline and record failures, never raise.

    Closing on a helper thread breaks Playwright's thread affinity
    ("Cannot switch to a different thread") and kills the final
    screenshot, so the old timeout-abandonment contract is gone: both
    closes run here, both are attempted, and errors land in the
    sidecar. A wedged close is bounded by the executor's run
    watchdog instead.
    """
    import threading

    import chimera.agent as agent

    main_ident = threading.get_ident()
    idents = []

    class _Closes:
        def close(self):
            idents.append(threading.get_ident())

    agent._close_browser(_Closes(), _Closes(), tmp_path, "clean-run")
    assert idents == [main_ident, main_ident]
    assert list(tmp_path.glob("*.teardown.json")) == []

    class _Fails:
        def close(self):
            raise RuntimeError("boom")

    # Must not raise; both failures recorded.
    agent._close_browser(_Fails(), _Fails(), tmp_path, "bad-run")
    sidecar = json.loads((tmp_path / "bad-run.teardown.json")
                         .read_text(encoding="utf-8"))
    assert len(sidecar["notes"]) == 2
    assert "context close failed: RuntimeError: boom" in sidecar["notes"][0]
    assert "browser close failed: RuntimeError: boom" in sidecar["notes"][1]


def test_boot_reaps_orphaned_runs(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        stuck = store.create_execution({
            "workflow_id": "flipkart-add-to-cart", "driver": "chimera",
            "scenario_id": "flipkart:add-to-cart", "status": "running",
            "verdict": "pending"})
        done = store.create_execution({
            "workflow_id": "create-project", "driver": "chimera",
            "scenario_id": "normal", "status": "succeeded",
            "verdict": "verified-success"})
        Executor(store, tmp_path / "wb")
        record = store.get_execution(stuck)
        assert record["status"] == "failed"
        assert record["verdict"] == "insufficient-evidence"
        assert "restarted" in (record["error"] or "")
        assert store.get_execution(done)["status"] == "succeeded"
    finally:
        store.close()


def test_readers_bound_single_element_reads():
    seen = []

    class _StrictLink:
        def get_attribute(self, name, **kwargs):
            assert "timeout" in kwargs, "get_attribute needs a timeout"
            seen.append(("attr", kwargs["timeout"]))
            return "/yonex-gr/p/itm1?pid=X"

        def text_content(self, **kwargs):
            assert "timeout" in kwargs, "text_content needs a timeout"
            seen.append(("text", kwargs["timeout"]))
            return "YONEX GR 303i Black, Red Strung Badminton Racquet"

    class _StrictLinks:
        def count(self):
            return 1

        def nth(self, i):
            return _StrictLink()

    class _StrictPage:
        def locator(self, selector):
            if selector == adapter.SEL_RESULT_LINK:
                return _StrictLinks()

            class _Empty:
                def count(self):
                    return 0

                def all_text_contents(self):
                    return []

                def text_content(self, **kwargs):
                    return ""

            return _Empty()

        def title(self, **kwargs):
            assert "timeout" in kwargs, "title needs a timeout"
            return "t"

    state = adapter.read_search_state(_StrictPage())
    assert len(state["results"]) == 1
    assert seen and all(v == adapter.READ_TIMEOUT_MS for _, v in seen)


@pytest.mark.parametrize("mode", ["no_results", "add_fails", "wrong_item"])
def test_flipkart_failures_are_verified_not_missing(tmp_path, mode):
    page = FakeFlipPage(**{mode: True})
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_flip_chimera_factory(page))
        exec_id = ex.submit("flipkart-add-to-cart", "chimera", _params())
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "failed"
        assert record["verdict"] == "verified-failure"
        by_id = {c["check_id"]: c["satisfied"] for c in record["checks"]}
        if mode == "no_results":
            assert by_id == {"F1": 0, "F2": 0, "F3": 0}
        elif mode == "add_fails":
            assert by_id == {"F1": 1, "F2": 0, "F3": 0}
        else:
            assert by_id == {"F1": 1, "F2": 1, "F3": 0}
    finally:
        store.close()


def test_same_product_ignores_site_ellipsis():
    full = ("Yonex Astrox Lite 27i Badminton Racquet "
            "(G4, 77 Grams, 30 lbs Tension)")
    assert adapter._same_product(
        "Yonex Astrox Lite 27i Badminton Racquet (G4, 77 Grams, ...",
        full)
    assert adapter._same_product(
        "Yonex Astrox Lite 27i Badminton Racquet (G4, 77 Grams…",
        full)
    assert adapter._same_product(full, full)
    assert not adapter._same_product(
        "Yonex Astrox Lite 27i Badminton Racquet", "Wilson Pro Staff")
    assert not adapter._same_product("", full)
