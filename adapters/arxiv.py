"""arXiv search adapter: fail-closed reads of paper search results."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote_plus, urlsplit, parse_qsl

APPROVED_ORIGIN = "https://arxiv.org"

HOME_PATH = "/"
HOME_URL = APPROVED_ORIGIN + HOME_PATH

SEARCH_PATH = "/search/"
MAX_QUERY_LEN = 100
MAX_RESULTS = 10

STAGES_SUFFIX = ".stages.json"

READ_TIMEOUT_MS = 8000

SEL_ROW = ".arxiv-result"
SEL_TITLE = ".arxiv-result p.title"
SEL_SUMMARY = "h1"

ARXIV_FILL_TARGETS: tuple = ()
ARXIV_CLICK_TARGETS: tuple = ()


class UnapprovedURLError(ValueError):
    """A navigation target fell outside the approved arXiv pages."""


def assert_approved_url(url: str) -> str:
    """Fail closed unless the URL is home or a paper search."""
    match = re.match(r"^(https://[^/]+)(/[^?#]*)?", url or "")
    if not match or match.group(1) != APPROVED_ORIGIN:
        raise UnapprovedURLError(
            f"refusing navigation outside {APPROVED_ORIGIN}: {url!r}")
    path = match.group(2) or "/"
    if path == HOME_PATH:
        return url
    if path.rstrip("/") == SEARCH_PATH.rstrip("/"):
        query = dict(parse_qsl(urlsplit(url).query))
        if query.get("query", "").strip():
            return url
        raise UnapprovedURLError(
            f"refusing query-less arXiv search: {url!r}")
    raise UnapprovedURLError(
        f"refusing unapproved arXiv path: {url!r}")


def search_url(query: str) -> str:
    """Deterministic paper-search URL for a validated query."""
    clean = (query or "").strip()
    if not clean:
        raise ValueError("refusing blank arXiv search query")
    if len(clean) > MAX_QUERY_LEN:
        raise ValueError(
            f"refusing arXiv query over {MAX_QUERY_LEN} chars")
    return (f"{APPROVED_ORIGIN}{SEARCH_PATH}?query={quote_plus(clean)}"
            f"&searchtype=all")


def utcnow() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_search_state(page: Any) -> Dict[str, Any]:
    """Search identity: result count plus recorded paper titles."""
    try:
        url = page.url
    except Exception:  # noqa: BLE001 — duck-typed property
        url = ""
    try:
        summary = (page.locator(SEL_SUMMARY).first.text_content(
            timeout=READ_TIMEOUT_MS) or "").strip()
    except Exception:  # noqa: BLE001 — missing summary reads empty
        summary = ""
    titles: List[str] = []
    try:
        items = page.locator(SEL_TITLE)
        rows = page.locator(SEL_ROW).count()
        total = items.count()
        for i in range(min(total, MAX_RESULTS)):
            try:
                text = (items.nth(i).text_content(timeout=READ_TIMEOUT_MS)
                        or "").strip()
            except Exception:  # noqa: BLE001 — one bad row skips
                continue
            text = " ".join(text.split())
            if text:
                titles.append(text[:200])
        count = rows
    except Exception:  # noqa: BLE001 — result scan best-effort
        count = 0
    return {"url": url if isinstance(url, str) else "",
            "summary": " ".join(summary.split())[:200],
            "count": int(count), "titles": titles}


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

def verify_arxiv_search(snapshot: Dict[str, Any] | None,
                        stages: List[Dict[str, Any]],
                        expected: Dict[str, Any]) -> Dict[str, Any]:
    """Judge an arXiv paper search from recorded stage states.

    ``expected`` carries ``query``. AX1 judges the results were
    served with at least one paper; AX2 judges paper titles were
    recorded.
    """
    states = stage_states(stages)
    if not states and not isinstance(snapshot, dict):
        return {"status": "unavailable", "checks": []}
    checks: List[Dict[str, Any]] = []

    found = states.get("search", {})
    count = int(found.get("count") or 0)
    served = count >= 1
    summary = str(found.get("summary") or "")
    checks.append({
        "check_id": "AX1",
        "satisfied": bool(served),
        "detail": (f"results served: {count} papers"
                   + (f" ({summary[:80]})" if summary else "")
                   if served else
                   "no papers returned"),
    })

    titles = found.get("titles")
    if not isinstance(titles, list):
        titles = []
    texts = [t for t in titles if isinstance(t, str) and t.strip()]
    held = bool(served and texts)
    checks.append({
        "check_id": "AX2",
        "satisfied": bool(held),
        "detail": (f"{len(texts)} paper titles recorded, "
                   f"first: {texts[0][:80]}" if held else
                   "no paper titles recorded"),
    })
    return {"status": "verified", "checks": checks}
