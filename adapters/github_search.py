"""GitHub repository-search adapter: fail-closed reads, no logins."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote_plus, urlsplit, parse_qsl

APPROVED_ORIGIN = "https://github.com"

HOME_PATH = "/"
HOME_URL = APPROVED_ORIGIN + HOME_PATH

SEARCH_PATH = "/search"
MAX_QUERY_LEN = 100
MAX_RESULTS = 10

STAGES_SUFFIX = ".stages.json"

READ_TIMEOUT_MS = 8000

SEL_LIST = '[data-testid="results-list"]'
SEL_RESULT = '[data-testid="results-list"] [class*="search-title"]'

GSEARCH_FILL_TARGETS: tuple = ()
GSEARCH_CLICK_TARGETS: tuple = ()


class UnapprovedURLError(ValueError):
    """A navigation target fell outside the approved GitHub pages."""


def assert_approved_url(url: str) -> str:
    """Fail closed unless the URL is home or a repository search."""
    match = re.match(r"^(https://[^/]+)(/[^?#]*)?", url or "")
    if not match or match.group(1) != APPROVED_ORIGIN:
        raise UnapprovedURLError(
            f"refusing navigation outside {APPROVED_ORIGIN}: {url!r}")
    path = match.group(2) or "/"
    if path == HOME_PATH:
        return url
    if path == SEARCH_PATH:
        query = dict(parse_qsl(urlsplit(url).query))
        if query.get("q", "").strip():
            return url
        raise UnapprovedURLError(
            f"refusing query-less GitHub search: {url!r}")
    raise UnapprovedURLError(
        f"refusing unapproved GitHub path: {url!r}")


def search_url(query: str) -> str:
    """Deterministic repository-search URL for a validated query."""
    clean = (query or "").strip()
    if not clean:
        raise ValueError("refusing blank GitHub search query")
    if len(clean) > MAX_QUERY_LEN:
        raise ValueError(
            f"refusing GitHub query over {MAX_QUERY_LEN} chars")
    return (f"{APPROVED_ORIGIN}{SEARCH_PATH}?q={quote_plus(clean)}"
            f"&type=repositories")


def utcnow() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_search_state(page: Any) -> Dict[str, Any]:
    """Search identity: result count plus recorded repo names."""
    try:
        url = page.url
    except Exception:  # noqa: BLE001 — duck-typed property
        url = ""
    try:
        served = page.locator(SEL_LIST).count() > 0
    except Exception:  # noqa: BLE001 — list read is best-effort
        served = False
    titles: List[str] = []
    try:
        items = page.locator(SEL_RESULT)
        total = items.count()
        for i in range(min(total, MAX_RESULTS)):
            try:
                text = (items.nth(i).text_content(timeout=READ_TIMEOUT_MS)
                        or "").strip()
            except Exception:  # noqa: BLE001 — one bad row skips
                continue
            if text:
                titles.append(" ".join(text.split())[:200])
        count = total
    except Exception:  # noqa: BLE001 — result scan best-effort
        count = 0
    return {"url": url if isinstance(url, str) else "",
            "served": bool(served), "count": int(count),
            "titles": titles}


STAGE_READERS = {
    "search": read_search_state,
}


def capture_end_snapshot(page: Any) -> Dict[str, Any]:
    """Final pre-teardown state read (executor observe hook)."""
    return read_search_state(page)


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

def verify_github_search(snapshot: Dict[str, Any] | None,
                         stages: List[Dict[str, Any]],
                         expected: Dict[str, Any]) -> Dict[str, Any]:
    """Judge a GitHub repository search from recorded stage states.

    ``expected`` carries ``query``. GS1 judges the results list
    was served with at least one result; GS2 judges repo names
    were recorded.
    """
    states = stage_states(stages)
    if not states and not isinstance(snapshot, dict):
        return {"status": "unavailable", "checks": []}
    checks: List[Dict[str, Any]] = []

    found = states.get("search", {})
    count = int(found.get("count") or 0)
    served = bool(found.get("served")) and count >= 1
    checks.append({
        "check_id": "GS1",
        "satisfied": bool(served),
        "detail": (f"results served: {count} repositories" if served else
                   "no repositories returned"),
    })

    titles = found.get("titles")
    if not isinstance(titles, list):
        titles = []
    texts = [t for t in titles if isinstance(t, str) and t.strip()]
    held = bool(served and texts)
    checks.append({
        "check_id": "GS2",
        "satisfied": bool(held),
        "detail": (f"{len(texts)} repo names recorded, "
                   f"first: {texts[0][:80]}" if held else
                   "no repo names recorded"),
    })
    return {"status": "verified", "checks": checks}
