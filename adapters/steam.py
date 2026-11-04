"""Steam store adapter: fail-closed search and game reads, no purchases."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote_plus

APPROVED_ORIGIN = "https://store.steampowered.com"

HOME_PATH = "/"
HOME_URL = APPROVED_ORIGIN + HOME_PATH

SEARCH_PATH = "/search/"
APP_PATH_RE = re.compile(r"^/app/\d+(/[^?#]*)?$")
MAX_QUERY_LEN = 100
MAX_RESULTS = 10

STAGES_SUFFIX = ".stages.json"

READ_TIMEOUT_MS = 8000

SEL_SEARCH_ROW = "#search_resultsRows a"
SEL_RESULT_NAME = ".search_name"
SEL_GAME_NAME = "#appHubAppName"
SEL_PRICE = ".game_purchase_price, .discount_final_price"

STEAM_FILL_TARGETS: tuple = ()
STEAM_CLICK_TARGETS: tuple = ()


class UnapprovedURLError(ValueError):
    """A navigation target fell outside the approved Steam pages."""


def assert_approved_url(url: str) -> str:
    """Fail closed unless the URL is home, search, or a game page."""
    match = re.match(r"^(https://[^/]+)(/[^?#]*)?", url or "")
    if not match or match.group(1) != APPROVED_ORIGIN:
        raise UnapprovedURLError(
            f"refusing navigation outside {APPROVED_ORIGIN}: {url!r}")
    path = match.group(2) or "/"
    if path in (HOME_PATH, SEARCH_PATH, "/search"):
        return url
    if APP_PATH_RE.match(path):
        return url
    raise UnapprovedURLError(
        f"refusing unapproved Steam path: {url!r}")


def search_url(query: str) -> str:
    """Deterministic store-search URL for a validated query."""
    clean = (query or "").strip()
    if not clean:
        raise ValueError("refusing blank Steam search query")
    if len(clean) > MAX_QUERY_LEN:
        raise ValueError(
            f"refusing Steam query over {MAX_QUERY_LEN} chars")
    return f"{APPROVED_ORIGIN}{SEARCH_PATH}?term={quote_plus(clean)}"


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


def read_search_state(page: Any) -> Dict[str, Any]:
    """Search results: app rows paired with their names by order."""
    try:
        url = page.url
    except Exception:  # noqa: BLE001 — duck-typed property
        url = ""
    results: List[Dict[str, str]] = []
    try:
        # NOTE: all_text_contents() takes no timeout kwarg — pass none.
        names = [(t or "").strip() for t in
                 page.locator(SEL_RESULT_NAME).all_text_contents()]
    except Exception:  # noqa: BLE001 — name list best-effort
        names = []
    count = 0
    try:
        rows = page.locator(SEL_SEARCH_ROW)
        total = rows.count()
        for i in range(total):
            try:
                href = (rows.nth(i).get_attribute(
                    "href", timeout=READ_TIMEOUT_MS) or "")
            except Exception:  # noqa: BLE001 — one bad row skips
                continue
            if "/app/" not in href:
                continue
            name = names[i] if i < len(names) else ""
            name = " ".join(name.split())
            if name and len(results) < MAX_RESULTS:
                results.append({"name": name[:200],
                                "href": href[:300]})
            count += 1
    except Exception:  # noqa: BLE001 — row scan best-effort
        pass
    return {"url": url if isinstance(url, str) else "", "count": count,
            "results": results}


def read_game_state(page: Any) -> Dict[str, Any]:
    """Game identity: store name and displayed price text."""
    try:
        url = page.url
    except Exception:  # noqa: BLE001 — duck-typed property
        url = ""
    try:
        name = (page.locator(SEL_GAME_NAME).first.text_content(
            timeout=READ_TIMEOUT_MS) or "").strip()
    except Exception:  # noqa: BLE001 — missing name reads empty
        name = ""
    try:
        price = (page.locator(SEL_PRICE).first.text_content(
            timeout=READ_TIMEOUT_MS) or "").strip()
    except Exception:  # noqa: BLE001 — missing price reads empty
        price = ""
    return {"url": url if isinstance(url, str) else "",
            "name": " ".join(name.split())[:200],
            "price": " ".join(price.split())[:60]}


STAGE_READERS = {
    "search": read_search_state,
    "game": read_game_state,
}


def capture_end_snapshot(page: Any) -> Dict[str, Any]:
    """Final pre-teardown state read (executor observe hook)."""
    return read_game_state(page)


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

def verify_steam_price(snapshot: Dict[str, Any] | None,
                       stages: List[Dict[str, Any]],
                       expected: Dict[str, Any]) -> Dict[str, Any]:
    """Judge a Steam price check from recorded stage states.

    ``expected`` carries ``query`` and ``pick``. ST1 judges the
    search returned the picked result; ST2 judges the game page
    names it with a displayed price.
    """
    states = stage_states(stages)
    if not states and not isinstance(snapshot, dict):
        return {"status": "unavailable", "checks": []}
    checks: List[Dict[str, Any]] = []
    try:
        pick = int(expected.get("pick") or 0)
    except (TypeError, ValueError):
        pick = 0

    search = states.get("search", {})
    results = search.get("results")
    if not isinstance(results, list):
        results = []
    count = int(search.get("count") or 0)
    picked = results[pick - 1] if 1 <= pick <= len(results) else {}
    picked_name = str(picked.get("name") or "") if isinstance(
        picked, dict) else ""
    found = bool(picked_name)
    checks.append({
        "check_id": "ST1",
        "satisfied": bool(found),
        "detail": (f"search returned {count} games, "
                   f"picked #{pick}: {picked_name[:60]}" if found else
                   f"search returned {count} games, "
                   f"cannot pick #{pick}"),
    })

    game = states.get("game", {})
    name = str(game.get("name") or "")
    price = str(game.get("price") or "")
    held = bool(found and name and name == picked_name and price)
    checks.append({
        "check_id": "ST2",
        "satisfied": bool(held),
        "detail": (f"game verified: {name[:60]} at {price[:40]}"
                   if held else
                   f"game mismatch: page={name[:60]!r}, "
                   f"price={price[:40]!r}, picked {picked_name[:60]!r}"),
    })
    return {"status": "verified", "checks": checks}
