"""Tests for the SauceDemo adapter (no browser; synthetic states)."""

import pytest

from adapters import saucedemo as adapter


def test_approved_url_guard():
    assert adapter.assert_approved_url(
        "https://www.saucedemo.com/cart.html")
    assert adapter.assert_approved_url("https://www.saucedemo.com/")
    # Query/fragment on an approved page is the same page: allowed.
    assert adapter.assert_approved_url(
        "https://www.saucedemo.com/cart.html?x=1#frag")
    for bad in ("https://evil.com/",
                "https://www.saucedemo.com.evil.com/",
                "https://www.saucedemo.com/admin",
                "http://www.saucedemo.com/",
                "",
                None):
        with pytest.raises(adapter.UnapprovedURLError):
            adapter.assert_approved_url(bad)


def _stages(**states):
    return [{"stage": name, "url": "https://www.saucedemo.com/x",
             "captured_at": "t", "state": state}
            for name, state in states.items()]


def _expected(**kw):
    base = {"username": "standard_user",
            "items": ["Sauce Labs Backpack", "Sauce Labs Bike Light"],
            "sort": "lohi", "checkout_case": "complete"}
    base.update(kw)
    return base


def _full_states():
    return {
        "login": {"logged_in": True, "error": None},
        "inventory": {"count": 2, "sort_value": "lohi", "items": [
            {"name": "Sauce Labs Bike Light", "price": "$9.99"},
            {"name": "Sauce Labs Backpack", "price": "$29.99"}]},
        "cart": {"badge": "2", "reached": True, "items": [
            {"name": "Sauce Labs Backpack", "qty": "1",
             "price": "$29.99"},
            {"name": "Sauce Labs Bike Light", "qty": "1",
             "price": "$9.99"}]},
        "info": {"accepted": True, "error": None},
        "overview": {"items": ["Sauce Labs Backpack"], "total": "Total: $x"},
        "complete": {"confirmation_visible": True,
                     "confirmation_text": adapter.COMPLETE_HEADER,
                     "detail": "dispatched"},
    }


def test_verify_success_and_sort():
    report = adapter.verify_sauce_order(
        {"url": "x"}, _stages(**_full_states()), _expected())
    assert report["status"] == "verified"
    assert [c["check_id"] for c in report["checks"]] == [
        "S1", "S2", "S3", "S4", "S5"]
    assert all(c["satisfied"] is True for c in report["checks"])
    # Wrong order fails S2 only.
    states = _full_states()
    states["inventory"]["items"] = list(reversed(
        states["inventory"]["items"]))
    report = adapter.verify_sauce_order({}, _stages(**states), _expected())
    by_id = {c["check_id"]: c for c in report["checks"]}
    assert by_id["S2"]["satisfied"] is False
    assert by_id["S1"]["satisfied"] is True
    # No sorting requested: S2 omitted, not faked.
    report = adapter.verify_sauce_order(
        {}, _stages(**_full_states()), _expected(sort="none"))
    assert [c["check_id"] for c in report["checks"]] == [
        "S1", "S3", "S4", "S5"]


def test_verify_failures_are_verified_not_missing():
    states = {"login": {"logged_in": False,
                        "error": "Epic sadface: locked out"}}
    report = adapter.verify_sauce_order(
        {}, _stages(**states), _expected())
    assert report["status"] == "verified"
    by_id = {c["check_id"]: c for c in report["checks"]}
    assert by_id["S1"]["satisfied"] is False
    assert "locked out" in by_id["S1"]["detail"]
    assert by_id["S3"]["satisfied"] is False  # cart never reached
    # Empty cart that stays empty matches honestly.
    states = _full_states()
    states["cart"] = {"badge": None, "reached": True, "items": []}
    report = adapter.verify_sauce_order(
        {}, _stages(**states), _expected(items=[]))
    by_id = {c["check_id"]: c for c in report["checks"]}
    assert by_id["S3"]["satisfied"] is True
    # No evidence at all: unavailable, never a verdict.
    report = adapter.verify_sauce_order(None, [], _expected())
    assert report == {"status": "unavailable", "checks": []}


def test_stages_file_round_trip(tmp_path):
    stages = _stages(**_full_states())
    path = adapter.write_stages(tmp_path, "r1", stages)
    assert adapter.read_stages_file(path) == stages
    assert adapter.read_stages_file(None) == []
    assert adapter.read_stages_file(str(tmp_path / "nope.json")) == []
    assert adapter.stages_for_trace(str(tmp_path / "r1.json")) == stages
    assert adapter.stages_for_trace(
        str(tmp_path / "r1.replay.json")) == stages
    assert adapter.stages_for_trace(None) == []


def test_stage_state_readers_with_fake_page():
    class Locator:
        def __init__(self, texts=(), first_text=None, count=0,
                     visible=True, value=None):
            self._texts = list(texts)
            self._first = first_text
            self._count = count
            self._visible = visible
            self._value = value

        def count(self):
            return self._count

        def all_text_contents(self):
            return list(self._texts)

        @property
        def first(self):
            return self

        def text_content(self):
            return self._first

        def is_visible(self):
            return self._visible

        def input_value(self):
            return self._value

    class Page:
        def __init__(self, mapping):
            self._mapping = mapping

        def locator(self, selector):
            return self._mapping.get(selector, Locator())

    page = Page({
        adapter.SEL_INVENTORY_LIST: Locator(count=1),
        adapter.SEL_LOGIN_ERROR: Locator(),
        adapter.SEL_ITEM_NAME: Locator(
            texts=["B", "A"], count=2),
        adapter.SEL_ITEM_PRICE: Locator(
            texts=["$9.99", "$29.99"], count=2),
        adapter.SEL_SORT: Locator(count=1, value="lohi"),
        adapter.SEL_CART_BADGE: Locator(count=1, first_text="2"),
        f"{adapter.SEL_CART_ITEM} {adapter.SEL_ITEM_NAME}": Locator(
            texts=["A", "B"], count=2),
        f"{adapter.SEL_CART_ITEM} {adapter.SEL_CART_QTY}": Locator(
            texts=["1", "1"], count=2),
        f"{adapter.SEL_CART_ITEM} {adapter.SEL_ITEM_PRICE}": Locator(
            texts=["$29.99", "$9.99"], count=2),
        adapter.SEL_CART_LIST: Locator(count=1),
        adapter.SEL_TOTAL: Locator(count=1, first_text="Total: $40"),
        adapter.SEL_COMPLETE_HEADER: Locator(
            count=1, first_text=adapter.COMPLETE_HEADER),
        adapter.SEL_COMPLETE_TEXT: Locator(count=1, first_text="pony"),
    })
    assert adapter.read_login_state(page) == {"logged_in": True,
                                              "error": None}
    inv = adapter.read_inventory_state(page)
    assert inv["count"] == 2 and inv["sort_value"] == "lohi"
    cart = adapter.read_cart_state(page)
    assert cart["badge"] == "2" and len(cart["items"]) == 2
    assert cart["reached"] is True
    assert adapter.read_info_state(page) == {"accepted": True,
                                             "error": None}
    assert adapter.read_complete_state(page)[
        "confirmation_visible"] is True
    snap = adapter.capture_end_snapshot(page)
    assert snap["confirmation_text"] == adapter.COMPLETE_HEADER


def _cart_lines(*names):
    return [{"name": n, "qty": "1", "price": "$1"} for n in names]


def test_cart_gate():
    full = {"reached": True, "badge": "2",
            "items": _cart_lines("Sauce Labs Backpack",
                                 "Sauce Labs Bike Light")}
    slugs = ["sauce-labs-backpack", "sauce-labs-bike-light"]
    assert adapter.cart_gate(full, slugs) is None
    # Unknown slugs are caller errors.
    gate = adapter.cart_gate(full, ["nope"])
    assert gate["kind"] == "unknown-slugs"
    # Empty or missing lines refuse checkout.
    assert adapter.cart_gate(
        {"reached": True, "items": []}, slugs)["kind"] == "empty"
    assert adapter.cart_gate(
        {"reached": True, "items": None}, slugs)["kind"] == "empty"
    # Wrong items or quantities refuse checkout.
    gate = adapter.cart_gate(
        {"reached": True, "items": _cart_lines("Sauce Labs Onesie")},
        slugs)
    assert gate["kind"] == "mismatch"
    bad_qty = {"reached": True, "items": [
        {"name": "Sauce Labs Backpack", "qty": "2", "price": "$1"}]}
    assert adapter.cart_gate(
        bad_qty, ["sauce-labs-backpack"])["kind"] == "mismatch"


def _stress_expected(**kw):
    base = {"username": "standard_user",
            "added": ["Sauce Labs Backpack", "Sauce Labs Bike Light"],
            "remaining": ["Sauce Labs Bike Light"],
            "sort": "az"}
    base.update(kw)
    return base


def _stress_states():
    states = _full_states()
    states["login"] = {"logged_in": True, "error": None, "login_ms": 120}
    states["inventory"]["images"] = [
        {"name": "Sauce Labs Backpack", "src": "/assets/a.jpg"},
        {"name": "Sauce Labs Bike Light", "src": "/assets/b.jpg"}]
    states["inventory"]["items"] = [
        {"name": "Sauce Labs Backpack", "price": "$29.99"},
        {"name": "Sauce Labs Bike Light", "price": "$9.99"}]
    states["inventory"]["sort_value"] = "az"
    states["cart_after_remove"] = {
        "badge": "1", "reached": True, "items": [
            {"name": "Sauce Labs Bike Light", "qty": "1",
             "price": "$9.99"}]}
    return states


def test_verify_stress_success():
    verdict = adapter.verify_stress_order(
        {"confirmation_visible": True}, _stages(**_stress_states()),
        _stress_expected())
    assert verdict["status"] == "verified"
    by_id = {c["check_id"]: c for c in verdict["checks"]}
    assert [c["check_id"] for c in verdict["checks"]] == [
        "T1", "T2", "T3", "T4", "T5", "T6"]
    assert all(c["satisfied"] for c in verdict["checks"])
    assert "120ms" in by_id["T1"]["detail"]


def test_verify_stress_problem_user_shape():
    states = _stress_states()
    states["inventory"]["images"] = [
        {"name": "Sauce Labs Backpack", "src": "/assets/sl-404-x.jpg"},
        {"name": "Sauce Labs Bike Light", "src": "/assets/sl-404-x.jpg"}]
    states["inventory"]["items"] = [
        {"name": "Sauce Labs Backpack", "price": "$29.99"},
        {"name": "Sauce Labs Bike Light", "price": "$9.99"}]
    states["info"] = {"accepted": False,
                      "error": "Error: Last Name is required"}
    states["complete"] = {"confirmation_visible": False,
                          "confirmation_text": None, "detail": None}
    verdict = adapter.verify_stress_order(
        {"confirmation_visible": False},
        _stages(**states), _stress_expected(sort="za"))
    by_id = {c["check_id"]: c for c in verdict["checks"]}
    assert verdict["status"] == "verified"
    assert by_id["T1"]["satisfied"] is True
    assert by_id["T2"]["satisfied"] is False
    assert "sl-404" in by_id["T2"]["detail"]
    assert by_id["T3"]["satisfied"] is False  # order never changed
    assert by_id["T4"]["satisfied"] is True
    assert by_id["T5"]["satisfied"] is True
    assert by_id["T6"]["satisfied"] is False
    assert "Last Name is required" in by_id["T6"]["detail"]


def test_verify_stress_omissions_and_unavailable():
    verdict = adapter.verify_stress_order(
        {"confirmation_visible": True}, _stages(**_stress_states()),
        _stress_expected(sort="none", remaining=None))
    assert [c["check_id"] for c in verdict["checks"]] == [
        "T1", "T2", "T4", "T6"]
    assert adapter.verify_stress_order(None, [], {}) == {
        "status": "unavailable", "checks": []}


def test_inventory_images_reader():
    from tests.fake_saucedemo import FakeSaucePage

    page = FakeSaucePage()
    page.goto(adapter.APPROVED_ORIGIN + adapter.INVENTORY_PATH)
    images = adapter.read_inventory_images(page)
    assert len(images) == 6
    assert len({i["src"] for i in images}) == 6
    bad = FakeSaucePage(images_404=True)
    bad.goto(adapter.APPROVED_ORIGIN + adapter.INVENTORY_PATH)
    images = adapter.read_inventory_images(bad)
    assert {i["src"] for i in images} == {"/assets/sl-404-fake.jpg"}
