"""Amazon adapter: fail-closed search and product reads, gate-aware.

Reads only: search results and product name/price. No cart, no
checkout, no account pages — the URL guard refuses them. Clean
sessions usually meet a bot gate here; that is detected
explicitly (not mistaken for zero results) so the run can say so
and point at a logged-in profile.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote_plus

APPROVED_ORIGIN = "https://www.amazon.com"

HOME_PATH = "/"
HOME_URL = APPROVED_ORIGIN + HOME_PATH

SEARCH_PATH = "/s"
ASIN_RE = r"[A-Z0-9]{10}"
PRODUCT_PATH_RE = re.compile(
    r"^/([^/]+/)?dp/" + ASIN_RE + r"(/[^?#]*)?"
    r"$|^/gp/(product/" + ASIN_RE + r"(/[^?#]*)?|slredirect/[^?#]*)$")
MAX_QUERY_LEN = 100
MAX_RESULTS = 10

STAGES_SUFFIX = ".stages.json"

READ_TIMEOUT_MS = 8000

SEL_ROW = '[data-component-type="s-search-result"]'
# Scoped within one result row: the row's brand + title arrive as
# separate ``h2 span`` texts (no anchor inside the ``h2`` anymore),
# so each row is read through a ``SEL_ROW >> nth=i >> <sub>`` chain.
SEL_ROW_HREF = 'a[href*="/dp/"]'
SEL_ROW_TITLE = "h2 span"


def _row_selector(index: int, sub: str) -> str:
    """Chain selector to one sub-element of result row ``index``."""
    return f"{SEL_ROW} >> nth={index} >> {sub}"
SEL_TITLE = "#productTitle"
SEL_PRICE_CANDIDATES = (
    "#corePriceDisplay .a-offscreen",
    "#corePrice_feature_div .a-offscreen",
    "#priceblock_ourprice",
    ".a-price .a-offscreen",
)
SEL_CAPTCHA_INPUT = "#captchacharacters"
SEL_CAPTCHA_FORM = 'form[action*="validateCaptcha"]'
GATE_TEXT_MARKER = "Click the button below to continue shopping"
DOG_BODY_MARKER = "images/G/01/error/"

AMAZON_FILL_TARGETS: tuple = ()
AMAZON_CLICK_TARGETS: tuple = ()


class UnapprovedURLError(ValueError):
    """A navigation target fell outside the approved Amazon pages."""


def assert_approved_url(url: str) -> str:
    """Fail closed unless the URL is home, search, or a product page."""
    match = re.match(r"^(https://[^/]+)(/[^?#]*)?", url or "")
    if not match or match.group(1) != APPROVED_ORIGIN:
        raise UnapprovedURLError(
            f"refusing navigation outside {APPROVED_ORIGIN}: {url!r}")
    path = match.group(2) or "/"
    if path == HOME_PATH:
        return url
    if path == SEARCH_PATH:
        from urllib.parse import urlsplit, parse_qsl

        query = dict(parse_qsl(urlsplit(url).query))
        if query.get("k", "").strip():
            return url
        raise UnapprovedURLError(
            f"refusing query-less Amazon search: {url!r}")
    if PRODUCT_PATH_RE.match(path):
        return url
    raise UnapprovedURLError(
        f"refusing unapproved Amazon path: {url!r}")


def search_url(query: str) -> str:
    """Deterministic store-search URL for a validated query."""
    clean = (query or "").strip()
    if not clean:
        raise ValueError("refusing blank Amazon search query")
    if len(clean) > MAX_QUERY_LEN:
        raise ValueError(
            f"refusing Amazon query over {MAX_QUERY_LEN} chars")
    return f"{APPROVED_ORIGIN}{SEARCH_PATH}?k={quote_plus(clean)}"


def utcnow() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def wait_for_any(page: Any, selectors: List[str], timeout_ms: int,
                 poll_ms: int = 100) -> str | None:
    """Return the first selector that becomes visible, else None.

    Read-only settle loop for post-navigation transitions. Plain
    visibility polling — not a retry of any action — bounded by
    ``timeout_ms``.
    """
    import time as _time

    deadline = _time.monotonic() + max(0, timeout_ms) / 1000
    while True:
        for selector in selectors:
            try:
                if page.locator(selector).first.is_visible():
                    return selector
            except Exception:  # noqa: BLE001 — a failed read is "not yet"
                continue
        if _time.monotonic() >= deadline:
            return None
        _time.sleep(max(0.01, poll_ms / 1000))


def _gate_present(page: Any) -> bool:
    """Whether the page shows Amazon's bot gate (any variant)."""
    for marker in (SEL_CAPTCHA_INPUT, SEL_CAPTCHA_FORM):
        try:
            if page.locator(marker).count() > 0:
                return True
        except Exception:  # noqa: BLE001 — marker read best-effort
            continue
    # NOTE: no page.title() here — it has no timeout knob and can
    # wedge teardown on a hostile page. The dog page carries its
    # error-image URL in the body, which this bounded read sees.
    try:
        body = (page.locator("body").first.text_content(
            timeout=READ_TIMEOUT_MS) or "")[:4000]
        if GATE_TEXT_MARKER in body or DOG_BODY_MARKER in body:
            return True
    except Exception:  # noqa: BLE001 — body read best-effort
        pass
    return False


def read_search_state(page: Any) -> Dict[str, Any]:
    """Search results: product rows paired with names by order."""
    try:
        url = page.url
    except Exception:  # noqa: BLE001 — duck-typed property
        url = ""
    gate = _gate_present(page)
    results: List[Dict[str, str]] = []
    try:
        total = page.locator(SEL_ROW).count()
    except Exception:  # noqa: BLE001 — row scan best-effort
        total = 0
    count = 0
    for i in range(total):
        try:
            href = (page.locator(_row_selector(i, SEL_ROW_HREF))
                    .first.get_attribute(
                        "href", timeout=READ_TIMEOUT_MS) or "")
        except Exception:  # noqa: BLE001 — one bad row skips
            continue
        if "/dp/" not in href and "slredirect" not in href:
            continue
        try:
            # NOTE: all_text_contents() takes no timeout kwarg — pass none.
            spans = page.locator(
                _row_selector(i, SEL_ROW_TITLE)).all_text_contents()
        except Exception:  # noqa: BLE001 — title read best-effort
            spans = []
        name = " ".join(
            part for part in
            (" ".join((t or "").split()) for t in spans) if part)
        count += 1
        if name and len(results) < MAX_RESULTS:
            results.append({"name": name[:200],
                            "href": href[:300]})
    return {"url": url if isinstance(url, str) else "",
            "gate": bool(gate), "count": count, "results": results}


def read_product_state(page: Any) -> Dict[str, Any]:
    """Product identity: title and displayed price text."""
    try:
        url = page.url
    except Exception:  # noqa: BLE001 — duck-typed property
        url = ""
    gate = _gate_present(page)
    try:
        name = (page.locator(SEL_TITLE).first.text_content(
            timeout=READ_TIMEOUT_MS) or "").strip()
    except Exception:  # noqa: BLE001 — missing title reads empty
        name = ""
    price = ""
    for candidate in SEL_PRICE_CANDIDATES:
        try:
            price = (page.locator(candidate).first.text_content(
                timeout=READ_TIMEOUT_MS) or "").strip()
        except Exception:  # noqa: BLE001 — try the next candidate
            continue
        if price:
            break
    return {"url": url if isinstance(url, str) else "",
            "gate": bool(gate), "name": " ".join(name.split())[:200],
            "price": " ".join(price.split())[:60]}


STAGE_READERS = {
    "search": read_search_state,
    "product": read_product_state,
}


def capture_end_snapshot(page: Any) -> Dict[str, Any]:
    """Final pre-teardown state read (executor observe hook)."""
    return read_product_state(page)


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


def read_stages_file(path: str | None) -> List[Dict[str, Any]]:
    if not path:
        return []
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    stages = doc.get("stages")
    return stages if isinstance(stages, list) else []


def stages_path_for_trace(trace_path: str | None) -> str | None:
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


def stages_for_trace(trace_path: str | None) -> List[Dict[str, Any]]:
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


# -- independent verification --------------------------------------------

GATE_DETAIL = ("bot gate detected (Amazon continue-shopping / captcha / "
               "error page): the site refused automation from this "
               "session — log in once via "
               "`python -m workbench.sessions login <profile>` and "
               "re-run with that profile")


def _gate_checks() -> List[Dict[str, Any]]:
    return [
        {"check_id": "AM1", "satisfied": False, "detail": GATE_DETAIL},
        {"check_id": "AM2", "satisfied": False, "detail": GATE_DETAIL},
    ]


def _same_product(a: str, b: str) -> bool:
    """Whether two Amazon titles name the same product.

    Listing titles are truncated heads of the product-page title
    (brand + title spans joined), so containment either way (over a
    normalized, non-trivial overlap) counts as a match. Same rule as
    the Flipkart adapter's ``_same_product``.
    """
    def norm(s: str) -> str:
        text = re.sub(r"\s+", " ", (s or "").strip().lower())
        return re.sub(r"\s*(\.\.\.|…)\s*$", "", text)

    left, right = norm(a), norm(b)
    if not left or not right:
        return False
    if left == right:
        return True
    short, long = sorted((left, right), key=len)
    return len(short) >= 12 and short in long


def verify_amazon_price(snapshot: Dict[str, Any] | None,
                        stages: List[Dict[str, Any]],
                        expected: Dict[str, Any]) -> Dict[str, Any]:
    """Judge an Amazon price check from recorded stage states.

    ``expected`` carries ``query`` and ``pick``. AM1 judges the
    search returned the picked result; AM2 judges the product page
    names it with a displayed price. A bot gate on either stage
    is reported as a diagnosed failure, never as zero results.
    """
    states = stage_states(stages)
    if not states and not isinstance(snapshot, dict):
        return {"status": "unavailable", "checks": []}
    search = states.get("search", {})
    product = states.get("product", {})
    if search.get("gate") is True or product.get("gate") is True:
        return {"status": "verified", "checks": _gate_checks()}
    checks: List[Dict[str, Any]] = []
    try:
        pick = int(expected.get("pick") or 0)
    except (TypeError, ValueError):
        pick = 0

    results = search.get("results")
    if not isinstance(results, list):
        results = []
    count = int(search.get("count") or 0)
    picked = results[pick - 1] if 1 <= pick <= len(results) else {}
    picked_name = str(picked.get("name") or "") if isinstance(
        picked, dict) else ""
    found = bool(picked_name)
    checks.append({
        "check_id": "AM1",
        "satisfied": bool(found),
        "detail": (f"search returned {count} products, "
                   f"picked #{pick}: {picked_name[:60]}" if found else
                   f"search returned {count} products, "
                   f"cannot pick #{pick}"),
    })

    name = str(product.get("name") or "")
    price = str(product.get("price") or "")
    held = bool(found and name and _same_product(name, picked_name)
               and price)
    checks.append({
        "check_id": "AM2",
        "satisfied": bool(held),
        "detail": (f"product verified: {name[:60]} at {price[:40]}"
                   if held else
                   f"product mismatch: page={name[:60]!r}, "
                   f"price={price[:40]!r}, picked {picked_name[:60]!r}"),
    })
    return {"status": "verified", "checks": checks}
