"""Reusable application adapter: SauceDemo (authorized practice store).

https://www.saucedemo.com/ is a public demo shop built for browser
automation practice. This adapter owns everything SauceDemo-specific:
the approved origin, page/selector constants, the test catalog,
duck-typed stage readers, the stages-file contract, and independent
order verification.

Layering: this package imports nothing from ``chimera``,
``benchmarks``, or ``workbench`` — all three layers may import it.
Only the standard library is used.

Stages-file contract (``<run>.stages.json`` next to the trace)::
    {"run_id": str, "stages": [
        {"stage": str, "url": str, "captured_at": str, "state": {...}}]}

Drivers append one entry per reached stage (login, inventory, cart,
info, overview, complete); the verifier judges the recorded states.
No real purchase exists to make: SauceDemo checkout is a demo flow
with no payment, and the adapter refuses any URL outside the
approved origin.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

APPROVED_ORIGIN = "https://www.saucedemo.com"

LOGIN_PATH = "/"
INVENTORY_PATH = "/inventory.html"
CART_PATH = "/cart.html"
INFO_PATH = "/checkout-step-one.html"
OVERVIEW_PATH = "/checkout-step-two.html"
COMPLETE_PATH = "/checkout-complete.html"

APPROVED_PATHS = (LOGIN_PATH, INVENTORY_PATH, CART_PATH, INFO_PATH,
                  OVERVIEW_PATH, COMPLETE_PATH)

LOGIN_URL = APPROVED_ORIGIN + LOGIN_PATH
SAUCE_URLS = tuple(APPROVED_ORIGIN + path for path in APPROVED_PATHS)

STAGES_SUFFIX = ".stages.json"

# Observed live against the site (names, prices, slugs). Prices are
# recorded as evidence, never asserted — only names drive matching.
CATALOG = {
    "sauce-labs-backpack": {"name": "Sauce Labs Backpack",
                            "price": "$29.99"},
    "sauce-labs-bike-light": {"name": "Sauce Labs Bike Light",
                              "price": "$9.99"},
    "sauce-labs-bolt-t-shirt": {"name": "Sauce Labs Bolt T-Shirt",
                                "price": "$15.99"},
    "sauce-labs-fleece-jacket": {"name": "Sauce Labs Fleece Jacket",
                                 "price": "$49.99"},
    "sauce-labs-onesie": {"name": "Sauce Labs Onesie", "price": "$7.99"},
    "test.allthethings()-t-shirt-(red)": {
        "name": "Test.allTheThings() T-Shirt (Red)",
        "price": "$15.99"},
}

CART_PRESETS = {
    "backpack+bike-light": ["sauce-labs-backpack",
                            "sauce-labs-bike-light"],
    "single-backpack": ["sauce-labs-backpack"],
    "empty-cart": [],
}

SORTS = {
    "az": "Name (A to Z)",
    "za": "Name (Z to A)",
    "lohi": "Price (low to high)",
    "hilo": "Price (high to low)",
    "none": "No sorting",
}

DOCUMENTED_USERS = ("standard_user", "locked_out_user")
DEFAULT_PASSWORD = "secret_sauce"

COMPLETE_HEADER = "Thank you for your order!"

# -- selectors (drivers must use these exact strings) ------------------

SEL_USERNAME = '[data-test="username"]'
SEL_PASSWORD = '[data-test="password"]'
SEL_LOGIN_BUTTON = '[data-test="login-button"]'
SEL_LOGIN_ERROR = '[data-test="error"]'
SEL_INVENTORY_LIST = ".inventory_list"
SEL_INVENTORY_ITEM = ".inventory_item"
SEL_ITEM_NAME = ".inventory_item_name"
SEL_ITEM_PRICE = ".inventory_item_price"
SEL_ITEM_IMG = ".inventory_item_img img"
SEL_SORT = ".product_sort_container"
SEL_CART_LINK = '[data-test="shopping-cart-link"]'
SEL_CART_BADGE = '[data-test="shopping-cart-badge"]'
SEL_CART_LIST = ".cart_list"
SEL_CART_ITEM = ".cart_item"
SEL_CART_QTY = ".cart_quantity"
SEL_CHECKOUT = '[data-test="checkout"]'
SEL_FIRST = '[data-test="firstName"]'
SEL_LAST = '[data-test="lastName"]'
SEL_POSTAL = '[data-test="postalCode"]'
SEL_CONTINUE = '[data-test="continue"]'
SEL_INFO_ERROR = '[data-test="error"]'
SEL_TOTAL = ".summary_total_label"
SEL_FINISH = '[data-test="finish"]'
SEL_COMPLETE_HEADER = '[data-test="complete-header"]'
SEL_COMPLETE_TEXT = '[data-test="complete-text"]'


def add_to_cart_selector(slug: str) -> str:
    return f'[data-test="add-to-cart-{slug}"]'


def remove_from_cart_selector(slug: str) -> str:
    return f'[data-test="remove-{slug}"]'


# Observer-policy targets (css constructions; value_length excluded).
SAUCE_FILL_TARGETS = (
    {"by": "css", "selector": SEL_USERNAME},
    {"by": "css", "selector": SEL_PASSWORD},
    {"by": "css", "selector": SEL_FIRST},
    {"by": "css", "selector": SEL_LAST},
    {"by": "css", "selector": SEL_POSTAL},
)

SAUCE_CLICK_TARGETS = (
    {"by": "css", "selector": SEL_LOGIN_BUTTON},
    {"by": "css", "selector": SEL_CART_LINK},
    {"by": "css", "selector": SEL_CHECKOUT},
    {"by": "css", "selector": SEL_CONTINUE},
    {"by": "css", "selector": SEL_FINISH},
    *({"by": "css", "selector": add_to_cart_selector(slug)}
      for slug in CATALOG),
    *({"by": "css", "selector": remove_from_cart_selector(slug)}
      for slug in CATALOG),
)

SAUCE_SELECT_TARGETS = (
    {"by": "css", "selector": SEL_SORT},
)


class UnapprovedURLError(ValueError):
    """A navigation target outside the approved SauceDemo origin."""


def assert_approved_url(url: str) -> str:
    """Fail closed unless the URL is the approved origin + path."""
    match = re.match(r"^(https://[^/]+)(/[^?#]*)?", url or "")
    if not match or match.group(1) != APPROVED_ORIGIN:
        raise UnapprovedURLError(
            f"refusing navigation outside {APPROVED_ORIGIN}: {url!r}")
    path = match.group(2) or "/"
    if path not in APPROVED_PATHS:
        raise UnapprovedURLError(
            f"refusing unapproved SauceDemo path: {url!r}")
    return url


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


# -- duck-typed stage readers (no Playwright import) --------------------

def _texts(page: Any, selector: str) -> Optional[List[str]]:
    if page.locator(selector).count() == 0:
        return None
    return list(page.locator(selector).all_text_contents())


def _text(page: Any, selector: str) -> Optional[str]:
    if page.locator(selector).count() == 0:
        return None
    return page.locator(selector).first.text_content()


def read_login_state(page: Any) -> Dict[str, Any]:
    return {
        "logged_in": page.locator(SEL_INVENTORY_LIST).count() > 0,
        "error": _text(page, SEL_LOGIN_ERROR),
    }


def read_inventory_images(page: Any) -> List[Dict[str, Any]]:
    """Product image sources in displayed order (name -> src).

    Each entry is best-effort: an unreadable image records a null
    src rather than failing the capture.
    """
    names = _texts(page, SEL_ITEM_NAME) or []
    try:
        locator = page.locator(SEL_ITEM_IMG)
        count = locator.count()
    except Exception:  # noqa: BLE001 — best-effort evidence
        return []
    out = []
    for index in range(min(len(names), count)):
        try:
            src = locator.nth(index).get_attribute("src")
        except Exception:  # noqa: BLE001 — best-effort evidence
            src = None
        out.append({"name": names[index], "src": src})
    return out


def read_inventory_state(page: Any) -> Dict[str, Any]:
    names = _texts(page, SEL_ITEM_NAME)
    prices = _texts(page, SEL_ITEM_PRICE)
    sort_value = None
    if page.locator(SEL_SORT).count() > 0:
        sort_value = page.locator(SEL_SORT).first.input_value()
    items = None
    if names is not None and prices is not None \
            and len(names) == len(prices):
        items = [{"name": name, "price": price}
                 for name, price in zip(names, prices)]
    return {"count": len(names) if names is not None else 0,
            "items": items, "sort_value": sort_value,
            "images": read_inventory_images(page)}


def read_cart_state(page: Any) -> Dict[str, Any]:
    names = _texts(page, f"{SEL_CART_ITEM} {SEL_ITEM_NAME}")
    quantities = _texts(page, f"{SEL_CART_ITEM} {SEL_CART_QTY}")
    prices = _texts(page, f"{SEL_CART_ITEM} {SEL_ITEM_PRICE}")
    badge = _text(page, SEL_CART_BADGE)
    items = None
    if names is not None and quantities is not None \
            and prices is not None \
            and len(names) == len(quantities) == len(prices):
        items = [{"name": name, "qty": qty, "price": price}
                 for name, qty, price in zip(names, quantities, prices)]
    return {"items": items, "badge": badge,
            "reached": page.locator(SEL_CART_LIST).count() > 0}


def read_info_state(page: Any) -> Dict[str, Any]:
    overview_here = page.locator(SEL_TOTAL).count() > 0
    return {
        "accepted": overview_here,
        "error": None if overview_here else _text(page, SEL_INFO_ERROR),
    }


def read_overview_state(page: Any) -> Dict[str, Any]:
    names = _texts(page, f"{SEL_CART_ITEM} {SEL_ITEM_NAME}")
    return {"items": names, "total": _text(page, SEL_TOTAL)}


def read_complete_state(page: Any) -> Dict[str, Any]:
    header = page.locator(SEL_COMPLETE_HEADER)
    return {
        "confirmation_visible": header.count() > 0
        and bool(header.first.is_visible()),
        "confirmation_text": _text(page, SEL_COMPLETE_HEADER),
        "detail": _text(page, SEL_COMPLETE_TEXT),
    }


STAGE_READERS = {
    "login": read_login_state,
    "inventory": read_inventory_state,
    "cart": read_cart_state,
    "cart_after_remove": read_cart_state,
    "info": read_info_state,
    "overview": read_overview_state,
    "complete": read_complete_state,
}


def wait_for_any(page: Any, selectors: List[str], timeout_ms: int,
                 poll_ms: int = 100) -> Optional[str]:
    """Return the first selector that becomes visible, else None.

    Read-only settle loop for post-click transitions (either the next
    page or an inline error appears). Plain visibility polling — not a
    retry of any action — bounded by ``timeout_ms``. Reads go through
    the page object, so a recording proxy observes them.
    """
    deadline = time.monotonic() + max(0, timeout_ms) / 1000
    while True:
        for selector in selectors:
            try:
                if page.locator(selector).first.is_visible():
                    return selector
            except Exception:  # noqa: BLE001 — a failed read is "not yet"
                continue
        if time.monotonic() >= deadline:
            return None
        time.sleep(max(0.01, poll_ms / 1000))


def capture_end_snapshot(page: Any) -> Dict[str, Any]:
    """Final pre-teardown state read (executor observe hook)."""
    try:
        url = page.url
    except Exception:  # noqa: BLE001 — duck-typed property
        url = ""
    snapshot = {"url": url if isinstance(url, str) else ""}
    snapshot.update(read_complete_state(page))
    return snapshot


# -- stages file --------------------------------------------------------

def stages_path_for(trace_dir: Path, run_id: str) -> Path:
    return Path(trace_dir) / f"{run_id}{STAGES_SUFFIX}"


def write_stages(trace_dir: Path, run_id: str,
                 stages: List[Dict[str, Any]]) -> str:
    path = stages_path_for(trace_dir, run_id)
    payload = {"run_id": run_id, "stages": stages}
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)
    return str(path)


def read_stages_file(path: Optional[str]) -> List[Dict[str, Any]]:
    if not path:
        return []
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    stages = doc.get("stages")
    return stages if isinstance(stages, list) else []


def stages_path_for_trace(trace_path: Optional[str]) -> Optional[str]:
    """Stages-file path next to a trace/report artifact, if derivable."""
    if not trace_path:
        return None
    stem = str(trace_path)
    if stem.endswith(".replay.json"):
        stem = stem[: -len(".replay.json")]
    elif stem.endswith(".json"):
        stem = stem[: -len(".json")]
    else:
        return None
    return stem + STAGES_SUFFIX


def stages_for_trace(trace_path: Optional[str]) -> List[Dict[str, Any]]:
    """Locate the stages file next to a trace/report artifact."""
    return read_stages_file(stages_path_for_trace(trace_path))


def stage_states(stages: List[Dict[str, Any]]) -> Dict[str, Dict]:
    """Latest captured state per stage name."""
    states: Dict[str, Dict] = {}
    for entry in stages:
        if isinstance(entry, dict) and isinstance(
                entry.get("state"), dict):
            states[entry.get("stage", "?")] = entry["state"]
    return states


# -- checkout gate ------------------------------------------------------

def cart_gate(cart_state: Mapping[str, Any],
              slugs: List[str]) -> Optional[Dict[str, str]]:
    """Refuse checkout unless the captured cart matches the intent.

    Returns ``None`` when checkout may proceed, else
    ``{"kind", "message"}`` with kind one of ``unknown-slugs``,
    ``empty``, or ``mismatch``. Both drivers gate on this so an
    empty or wrong cart fails at the cart stage instead of placing
    a wrong order.
    """
    unknown = [s for s in slugs if s not in CATALOG]
    if unknown:
        return {"kind": "unknown-slugs",
                "message": f"unknown catalog slugs: {unknown}"}
    lines = cart_state.get("items") or []
    observed = [i.get("name") for i in lines]
    if not observed:
        return {"kind": "empty",
                "message": "empty cart: refusing checkout with no items"}
    wanted = [CATALOG[s]["name"] for s in slugs]
    quantities_ok = all(i.get("qty") == "1" for i in lines)
    if sorted(observed) != sorted(wanted) or not quantities_ok:
        return {"kind": "mismatch",
                "message": (f"cart contents mismatch: observed {observed}, "
                            f"wanted {wanted}")}
    return None


# -- independent verification --------------------------------------------

def _check_sort(inventory: Mapping[str, Any], sort_mode: str,
                check_id: str) -> Dict[str, Any]:
    """Catalog order check shared by the order and stress flows."""
    items = inventory.get("items")
    if not isinstance(items, list) or not items:
        return {"check_id": check_id, "satisfied": False,
                "detail": "inventory not captured"}
    want = _expected_order(items, sort_mode)
    got = [i["name"] for i in items]
    if want is None:
        return {"check_id": check_id, "satisfied": False,
                "detail": "item price unparseable; order unverifiable"}
    match = got == want
    return {
        "check_id": check_id, "satisfied": match,
        "detail": (f"catalog in {sort_mode} order" if match else
                   f"order mismatch for {sort_mode}: {got[:3]}…"),
    }


def _check_images(inventory: Mapping[str, Any],
                  check_id: str) -> Dict[str, Any]:
    """Product image consistency: every product shows its own image.

    Satisfied when every captured product has a distinct,
    non-placeholder image source. A shared or placeholder source
    (e.g. the problem account's site-wide 404 image) fails with
    the observed sources quoted.
    """
    images = inventory.get("images")
    if not isinstance(images, list) or not images:
        return {"check_id": check_id, "satisfied": False,
                "detail": "no product images observed"}
    srcs = [i.get("src") if isinstance(i, dict) else None
            for i in images]
    if any(not s or not isinstance(s, str) for s in srcs):
        return {"check_id": check_id, "satisfied": False,
                "detail": "a product image source is missing"}
    placeholders = sorted({s for s in srcs if "404" in s})
    if placeholders:
        return {"check_id": check_id, "satisfied": False,
                "detail": ("placeholder image shown for "
                           f"{len(images)} products: {placeholders[0]}")}
    if len(set(srcs)) != len(srcs):
        return {"check_id": check_id, "satisfied": False,
                "detail": "products share image sources"}
    return {"check_id": check_id, "satisfied": True,
            "detail": f"{len(images)} distinct product images"}


def _check_cart_contents(cart: Mapping[str, Any],
                         want_items: List[str],
                         check_id: str) -> Dict[str, Any]:
    """Cart-lines check shared by the order and stress flows."""
    if cart.get("reached") is not True:
        return {"check_id": check_id, "satisfied": False,
                "detail": "cart page not reached"}
    lines = cart.get("items") if isinstance(
        cart.get("items"), list) else []
    got_items = [i["name"] for i in lines]
    quantities_ok = all(i.get("qty") == "1" for i in lines)
    match = sorted(got_items) == sorted(want_items) and quantities_ok
    return {
        "check_id": check_id, "satisfied": match,
        "detail": (f"cart holds {got_items or 'nothing'} "
                   f"(expected {want_items or 'nothing'})"),
    }

def _price(value: Any) -> Optional[float]:
    try:
        return float(str(value).replace("$", "").strip())
    except (TypeError, ValueError):
        return None


def _expected_order(items: List[Dict[str, Any]], sort: str
                    ) -> Optional[List[str]]:
    names = [i["name"] for i in items]
    if sort == "az":
        return sorted(names)
    if sort == "za":
        return sorted(names, reverse=True)
    prices = [_price(i.get("price")) for i in items]
    if any(p is None for p in prices):
        return None
    pairs = sorted(zip(prices, names), key=lambda p: (p[0], p[1]))
    ordered = [name for _, name in pairs]
    return ordered if sort == "lohi" else list(reversed(ordered))


def verify_sauce_order(snapshot: Optional[Dict[str, Any]],
                       stages: List[Dict[str, Any]],
                       expected: Mapping[str, Any]
                       ) -> Dict[str, Any]:
    """Judge a SauceDemo order from recorded stage states.

    ``expected`` carries ``items`` (names), ``sort`` mode, and
    ``checkout_case``. Returns ``{"status", "checks"}`` with S1–S5
    (S2 only when sorting was requested). ``unavailable`` only when
    no stage evidence exists at all — a failed login is a verified
    failure, not missing evidence.
    """
    states = stage_states(stages)
    if not states and not isinstance(snapshot, dict):
        return {"status": "unavailable", "checks": []}
    checks: List[Dict[str, Any]] = []

    login = states.get("login", {})
    logged_in = login.get("logged_in") is True
    checks.append({
        "check_id": "S1",
        "satisfied": logged_in,
        "detail": ("inventory reached as "
                   f"{expected.get('username', '?')}" if logged_in else
                   f"login failed: {login.get('error') or 'no inventory'}"),
    })

    inventory = states.get("inventory", {})
    sort_mode = expected.get("sort", "none")
    if sort_mode != "none":
        checks.append(_check_sort(inventory, sort_mode, "S2"))

    cart = states.get("cart", {})
    want_items = list(expected.get("items", []))
    checks.append(_check_cart_contents(cart, want_items, "S3"))

    info = states.get("info", {})
    accepted = info.get("accepted") is True
    checks.append({
        "check_id": "S4", "satisfied": accepted,
        "detail": ("checkout information accepted"
                   if accepted else
                   f"checkout blocked: {info.get('error') or 'no overview'}"),
    })

    complete = states.get("complete", {})
    header = complete.get("confirmation_text")
    done = complete.get("confirmation_visible") is True \
        and header == COMPLETE_HEADER
    checks.append({
        "check_id": "S5", "satisfied": done,
        "detail": (f"order confirmed: {header!r}" if done else
                   "no order confirmation"),
    })
    return {"status": "verified", "checks": checks}


def verify_stress_order(snapshot: Optional[Dict[str, Any]],
                        stages: List[Dict[str, Any]],
                        expected: Mapping[str, Any]
                        ) -> Dict[str, Any]:
    """Judge a stress flow (T1–T6) from captured stage states.

    ``expected`` carries ``username``, ``added`` (names added),
    ``remaining`` (names expected after the removal, or None when
    no removal was configured), and ``sort``. T3 is omitted when
    no sorting was requested; T5 is omitted when nothing was
    removed. T6 measures whether checkout completed — accounts
    the site itself blocks fail here with the site's own error
    quoted, which is a site defect, not missing evidence.
    """
    states = stage_states(stages)
    if not states and not isinstance(snapshot, dict):
        return {"status": "unavailable", "checks": []}
    checks: List[Dict[str, Any]] = []

    login = states.get("login", {})
    logged_in = login.get("logged_in") is True
    login_ms = login.get("login_ms")
    if logged_in:
        detail = (f"inventory in {login_ms}ms"
                  if isinstance(login_ms, int) and not isinstance(
                      login_ms, bool)
                  else "inventory reached (latency unmeasured)")
    else:
        detail = f"login failed: {login.get('error') or 'no inventory'}"
    checks.append({"check_id": "T1", "satisfied": logged_in,
                   "detail": detail})

    inventory = states.get("inventory", {})
    checks.append(_check_images(inventory, "T2"))

    sort_mode = expected.get("sort", "none")
    if sort_mode != "none":
        checks.append(_check_sort(inventory, sort_mode, "T3"))

    checks.append(_check_cart_contents(
        states.get("cart", {}), list(expected.get("added", [])), "T4"))

    remaining = expected.get("remaining")
    if remaining is not None:
        checks.append(_check_cart_contents(
            states.get("cart_after_remove", {}), list(remaining), "T5"))

    complete = states.get("complete", {})
    done = complete.get("confirmation_visible") is True
    header = complete.get("confirmation_text")
    if done:
        detail = f"order confirmed: {header!r}"
    else:
        info_error = states.get("info", {}).get("error")
        detail = (f"checkout rejected by site: {info_error}"
                  if info_error else "no order confirmation")
    checks.append({"check_id": "T6", "satisfied": done, "detail": detail})
    return {"status": "verified", "checks": checks}
