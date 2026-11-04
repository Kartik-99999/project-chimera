"""Reusable application adapter: Flipkart add-to-cart (guest cart only).

https://www.flipkart.com/ is a live marketplace. This adapter owns
everything Flipkart-specific: the approved origin, the three
approved pages (home, search, product, cart-read), selector
constants observed live, duck-typed stage readers, the stages-file
contract, and independent cart verification.

Safety boundaries (fail closed):

- The driver never logs in, never checks out, and never buys. Only
  home (``/``), search (``/search``), product (``/<slug>/p/<id>``),
  and the cart page (``/viewcart``) are approved; every checkout,
  payment, order, or account path is refused.
- The guest cart belongs to a throwaway browser context that is
  closed at teardown. Nothing persists, nothing is purchased.

Layering: this package imports nothing from ``chimera``,
``benchmarks``, or ``workbench`` — all three layers may import it.
Only the standard library is used.

Stages-file contract (``<run>.stages.json`` next to the trace)::

    {"run_id": str, "stages": [
        {"stage": str, "url": str, "captured_at": str, "state": {...}}]}

The driver appends one entry per reached stage (search, product,
cart); the verifier judges the recorded states. Prices are
recorded as evidence, never asserted — only the picked product's
identity drives matching.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

APPROVED_ORIGIN = "https://www.flipkart.com"

HOME_PATH = "/"
SEARCH_PATH = "/search"
VIEWCART_PATH = "/viewcart"

HOME_URL = APPROVED_ORIGIN + HOME_PATH
VIEWCART_URL = APPROVED_ORIGIN + VIEWCART_PATH

# Product pages look like /<slug>/p/<item-id> with tracking query args.
PRODUCT_PATH_RE = re.compile(r"^/[^/]+/p/[^/]+$")

STAGES_SUFFIX = ".stages.json"

#: Bound for single-element reads (titles, hrefs, body text). Flipkart
#: re-renders under load; the Playwright 30 s default per call can
#: stretch a stage scan into minutes on a churning DOM.
READ_TIMEOUT_MS = 8000

# -- selectors (drivers must use these exact strings) ------------------
# Observed live. Flipkart's markup uses generated classes, so clicks
# anchor on stable attributes and innermost-text matches instead.

# Two inputs share the name (one hidden duplicate); :visible isolates the
# header search box.
SEL_SEARCH_INPUT = 'input[name="q"]:visible'
SEL_RESULT_LINK = 'a[href*="/p/"]'
SEL_ADD_TO_CART = 'div:has-text("Add to cart"):not(:has(div))'
SEL_GO_TO_CART = 'div:not(:has(*)):has-text("Go to cart")'
SEL_CART_LINK = 'a[href^="/viewcart"]'
SEL_MODAL_CANCEL = 'button:has-text("Cancel")'
SEL_CART_QTY = 'div:not(:has(*)):has-text("Qty:")'
SEL_TOTAL_LABEL = 'div:not(:has(*)):has-text("Total Amount")'
SEL_CART_LEAVES = 'div:not(:has(*))'

# Observer-policy targets (css constructions; value_length excluded).
FLIPKART_FILL_TARGETS = (
    {"by": "css", "selector": SEL_SEARCH_INPUT},
)

FLIPKART_CLICK_TARGETS = (
    {"by": "css", "selector": SEL_ADD_TO_CART},
    {"by": "css", "selector": SEL_MODAL_CANCEL},
)


class UnapprovedURLError(ValueError):
    """A navigation target outside the approved Flipkart pages."""


def assert_approved_url(url: str) -> str:
    """Fail closed unless the URL is an approved Flipkart page."""
    match = re.match(r"^(https://[^/]+)(/[^?#]*)?", url or "")
    if not match or match.group(1) != APPROVED_ORIGIN:
        raise UnapprovedURLError(
            f"refusing navigation outside {APPROVED_ORIGIN}: {url!r}")
    path = match.group(2) or "/"
    if path in (HOME_PATH, SEARCH_PATH, VIEWCART_PATH):
        return url
    if PRODUCT_PATH_RE.match(path):
        return url
    raise UnapprovedURLError(
        f"refusing unapproved Flipkart path: {url!r}")


def search_url(query: str) -> str:
    """Deterministic search URL for a validated query string."""
    from urllib.parse import quote_plus

    return f"{APPROVED_ORIGIN}{SEARCH_PATH}?q={quote_plus(query)}"


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


# -- duck-typed stage readers (no Playwright import) --------------------

def _texts(page: Any, selector: str) -> Optional[List[str]]:
    if page.locator(selector).count() == 0:
        return None
    return list(page.locator(selector).all_text_contents())


def _text(page: Any, selector: str) -> Optional[str]:
    texts = _texts(page, selector)
    return texts[0].strip() if texts and texts[0].strip() else None


def read_search_state(page: Any) -> Dict[str, Any]:
    """Search results: product titles and hrefs.

    Each product card carries several ``/p/`` anchors (badge, title,
    price); only anchors with a substantial title count as results,
    deduplicated by href so ``pick`` indexes products, not links.
    """
    links = page.locator(SEL_RESULT_LINK)
    count = links.count()
    results: List[Dict[str, str]] = []
    seen = set()
    for i in range(count):
        if len(results) >= 10:
            break
        try:
            link = links.nth(i)
            href = link.get_attribute("href", timeout=READ_TIMEOUT_MS) or ""
            title = (link.text_content(timeout=READ_TIMEOUT_MS)
                     or "").strip()
        except Exception:  # noqa: BLE001 — one bad row skips, not fails
            continue
        if "/p/" in href and len(title) >= 20 and href not in seen:
            seen.add(href)
            results.append({"title": title[:200], "href": href})
    return {"count": count, "results": results}


def read_product_state(page: Any) -> Dict[str, Any]:
    """Product page: title, price text, and cart-button state."""
    try:
        url = page.url
    except Exception:  # noqa: BLE001 — duck-typed property
        url = ""
    try:
        # NOTE: title() takes no timeout kwarg — pass none (an
        # immediate protocol read; the watchdog bounds the run).
        title = page.title() or ""
    except Exception:  # noqa: BLE001 — duck-typed method
        title = ""
    add_visible = page.locator(SEL_ADD_TO_CART).count() > 0
    try:
        add_shown = (page.locator(SEL_ADD_TO_CART).first.is_visible()
                     if add_visible else False)
    except Exception:  # noqa: BLE001 — visibility read is best-effort
        add_shown = False
    go_visible = page.locator(SEL_GO_TO_CART).count() > 0
    return {"url": url if isinstance(url, str) else "",
            "title": title[:300],
            "add_visible": bool(add_shown or add_visible),
            "added": bool(go_visible)}


def read_cart_badge(page: Any) -> Optional[str]:
    """Header cart count, or None when the badge is absent."""
    text = _text(page, SEL_CART_LINK)
    if not text:
        return None
    match = re.search(r"(\d+)", text)
    return match.group(1) if match else None


def read_cart_state(page: Any) -> Dict[str, Any]:
    """Cart page: badge, line items (name + qty), and total text.

    Cart titles carry no link or stable class, so items pair by
    document order: each ``Qty: N`` leaf is followed by its item's
    title leaf (the first substantial text after it).
    """
    body = ""
    try:
        body = (page.locator("body").text_content(timeout=READ_TIMEOUT_MS)
                or "")
    except Exception:  # noqa: BLE001 — body read is best-effort
        pass
    items: List[Dict[str, str]] = []
    leaves = _texts(page, SEL_CART_LEAVES) or []
    for i, leaf in enumerate(leaves):
        match = re.match(r"Qty:\s*(\d+)\s*$", (leaf or "").strip())
        if not match:
            continue
        name = ""
        for following in leaves[i + 1: i + 6]:
            text = (following or "").strip()
            if len(text) >= 20:
                name = text[:200]
                break
        if name:
            items.append({"name": name, "qty": match.group(1)})
    total = None
    if _text(page, SEL_TOTAL_LABEL):
        after_label = False
        for line in body.splitlines():
            text = line.strip()
            if after_label and text.startswith("₹"):
                total = text
                break
            if text.lower() == "total amount":
                after_label = True
    return {"badge": read_cart_badge(page),
            "reached": "/viewcart" in (getattr(page, "url", "") or ""),
            "items": items, "total": total,
            "empty": "cart is empty" in body.lower()}


STAGE_READERS = {
    "search": read_search_state,
    "product": read_product_state,
    "cart": read_cart_state,
}


def wait_for_any(page: Any, selectors: List[str], timeout_ms: int,
                 poll_ms: int = 100) -> Optional[str]:
    """Return the first selector that becomes visible, else None.

    Read-only settle loop for post-click transitions. Plain
    visibility polling — not a retry of any action — bounded by
    ``timeout_ms``. Reads go through the page object, so a
    recording proxy observes them.
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
    snapshot.update(read_cart_state(page))
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


# -- cart gate ----------------------------------------------------------

def _same_product(a: str, b: str) -> bool:
    """Whether two Flipkart titles name the same product.

    Listing titles are truncated heads of the product/cart titles,
    so containment either way (over a normalized, non-trivial
    overlap) counts as a match. Trailing truncation markers
    (``...``/``…``) are stripped first: the site's own ellipsis
    must not break the prefix match.
    """
    def norm(s: str) -> str:
        text = re.sub(r"\s+", " ", (s or "").strip().lower())
        return re.sub(r"\s*(\.\.\.|…)\s*$", "", text)

    left, right = norm(a), norm(b)
    if not left or not right:
        return False
    short, long = sorted((left, right), key=len)
    return len(short) >= 12 and short in long


def cart_gate(cart_state: Mapping[str, Any],
              picked_title: str) -> Optional[Dict[str, str]]:
    """Refuse success unless the cart holds exactly the picked item.

    Returns ``None`` when the run may succeed, else ``{"kind",
    "message"}`` with kind one of ``empty`` or ``mismatch``. The
    guest cart starts empty (throwaway context), so exactly one
    line item with quantity 1 is required.
    """
    lines = cart_state.get("items") or []
    if not lines or cart_state.get("empty"):
        return {"kind": "empty",
                "message": "empty cart: the picked item never landed"}
    if len(lines) != 1:
        return {"kind": "mismatch",
                "message": (f"cart holds {len(lines)} items, "
                            f"wanted exactly the picked one")}
    line = lines[0]
    if not _same_product(line.get("name", ""), picked_title):
        return {"kind": "mismatch",
                "message": (f"cart item {line.get('name', '?')!r} is not "
                            f"the picked {picked_title!r}")}
    if (line.get("qty") or "") != "1":
        return {"kind": "mismatch",
                "message": f"cart quantity is {line.get('qty')!r}, wanted '1'"}
    return None


# -- independent verification --------------------------------------------

def verify_flipkart_cart(snapshot: Optional[Dict[str, Any]],
                         stages: List[Dict[str, Any]],
                         expected: Mapping[str, Any]
                         ) -> Dict[str, Any]:
    """Judge a Flipkart add-to-cart run from recorded stage states.

    ``expected`` carries ``query`` and ``pick`` (1-based result
    index). The picked product's href and title come from the
    recorded search stage itself — F1 judges that the pick exists;
    F2/F3 judge the later, independently captured stages against
    it. Returns ``{"status", "checks"}`` with F1–F3.
    ``unavailable`` only when no stage evidence exists at all — a
    failed search or empty cart is a verified failure, not missing
    evidence.
    """
    states = stage_states(stages)
    if not states and not isinstance(snapshot, dict):
        return {"status": "unavailable", "checks": []}
    checks: List[Dict[str, Any]] = []
    pick = max(1, int(expected.get("pick", 1)))

    search = states.get("search", {})
    results = search.get("results") or []
    picked = results[pick - 1] if len(results) >= pick else {}
    picked_href = str(picked.get("href") or "")
    picked_title = str(picked.get("title") or "")
    picked_ok = bool(picked_href and picked_title)
    checks.append({
        "check_id": "F1",
        "satisfied": bool(picked_ok),
        "detail": (f"search returned {len(results)} results; "
                   f"picked #{pick}: {picked_title[:80]}" if picked_ok else
                   f"search has {len(results)} results, "
                   f"cannot pick #{pick}"),
    })

    product = states.get("product", {})
    on_product = bool(picked_href) and (
        picked_href.split("?")[0] in str(product.get("url") or ""))
    title_ok = _same_product(str(product.get("title") or ""), picked_title)
    added = product.get("added") is True
    reached = bool(on_product and title_ok)
    checks.append({
        "check_id": "F2",
        "satisfied": bool(reached and added),
        "detail": (f"product reached and added: {picked_title[:80]}"
                   if reached and added else
                   "product not confirmed added "
                   f"(on_page={on_product}, title={title_ok}, "
                   f"added={added})"),
    })

    cart = states.get("cart", {})
    gate = cart_gate(cart, picked_title)
    checks.append({
        "check_id": "F3",
        "satisfied": gate is None,
        "detail": ("cart holds exactly the picked item (qty 1)"
                   if gate is None else gate["message"]),
    })
    return {"status": "verified", "checks": checks}
