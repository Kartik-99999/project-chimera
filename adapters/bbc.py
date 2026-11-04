"""BBC section-headlines adapter: fail-closed reads, no logins, no clicks."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

APPROVED_ORIGIN = "https://www.bbc.com"

HOME_PATH = "/"
HOME_URL = APPROVED_ORIGIN + HOME_PATH

SECTION_PATHS = {
    "news": "/news",
    "business": "/business",
    "technology": "/technology",
}
SECTION_LABELS = {
    "news": "News",
    "business": "Business",
    "technology": "Technology",
}
SECTION_PATH_RE = re.compile(r"^/(news|business|technology)/?$")

STAGES_SUFFIX = ".stages.json"

READ_TIMEOUT_MS = 8000
MAX_HEADLINES = 30

SEL_H1 = "h1"
SEL_HEADLINE = '[data-testid="card-headline"]'

BBC_FILL_TARGETS: tuple = ()
BBC_CLICK_TARGETS: tuple = ()


class UnapprovedURLError(ValueError):
    """A navigation target fell outside the approved BBC pages."""


def assert_approved_url(url: str) -> str:
    """Fail closed unless the URL is home or an approved section."""
    match = re.match(r"^(https://[^/]+)(/[^?#]*)?", url or "")
    if not match or match.group(1) != APPROVED_ORIGIN:
        raise UnapprovedURLError(
            f"refusing navigation outside {APPROVED_ORIGIN}: {url!r}")
    path = match.group(2) or "/"
    if path == HOME_PATH or SECTION_PATH_RE.match(path):
        return url
    raise UnapprovedURLError(
        f"refusing unapproved BBC path: {url!r}")


def section_url(section: str) -> str:
    """Deterministic section URL for a validated section key."""
    path = SECTION_PATHS.get((section or "").strip().lower())
    if path is None:
        raise ValueError(
            f"refusing BBC section outside {sorted(SECTION_PATHS)}: "
            f"{section!r}")
    return f"{APPROVED_ORIGIN}{path}"


def utcnow() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_section_state(page: Any) -> Dict[str, Any]:
    """Section identity: heading plus the recorded headline list."""
    try:
        url = page.url
    except Exception:  # noqa: BLE001 — duck-typed property
        url = ""
    try:
        heading = (page.locator(SEL_H1).first.text_content(
            timeout=READ_TIMEOUT_MS) or "").strip()
    except Exception:  # noqa: BLE001 — missing heading reads empty
        heading = ""
    headlines: List[str] = []
    try:
        items = page.locator(SEL_HEADLINE)
        total = items.count()
        for i in range(min(total, MAX_HEADLINES)):
            try:
                text = (items.nth(i).text_content(timeout=READ_TIMEOUT_MS)
                        or "").strip()
            except Exception:  # noqa: BLE001 — one bad row skips
                continue
            if text:
                headlines.append(text[:300])
        count = total
    except Exception:  # noqa: BLE001 — headline scan best-effort
        count = 0
    return {"url": url if isinstance(url, str) else "",
            "heading": heading, "count": int(count),
            "headlines": headlines}


STAGE_READERS = {
    "section": read_section_state,
}


def capture_end_snapshot(page: Any) -> Dict[str, Any]:
    """Final pre-teardown state read (executor observe hook)."""
    return read_section_state(page)


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

def verify_bbc_headlines(snapshot: Dict[str, Any] | None,
                         stages: List[Dict[str, Any]],
                         expected: Dict[str, Any]) -> Dict[str, Any]:
    """Judge a BBC headlines capture from recorded stage states.

    ``expected`` carries ``section``. BB1 judges the requested
    section page was served; BB2 judges headlines were recorded.
    """
    states = stage_states(stages)
    if not states and not isinstance(snapshot, dict):
        return {"status": "unavailable", "checks": []}
    checks: List[Dict[str, Any]] = []
    section = str(expected.get("section") or "").strip().lower()
    want_label = SECTION_LABELS.get(section, "")

    found = states.get("section", {})
    heading = str(found.get("heading") or "")
    url = str(found.get("url") or "")
    served = bool(
        want_label and heading == want_label
        and f"/{section}" in url.split("?")[0].split("#")[0])
    checks.append({
        "check_id": "BB1",
        "satisfied": bool(served),
        "detail": (f"section verified: {heading}" if served else
                   f"section mismatch: heading={heading[:60]!r}, "
                   f"url={url[:80]!r}, wanted {section!r}"),
    })

    headlines = found.get("headlines")
    if not isinstance(headlines, list):
        headlines = []
    texts = [h for h in headlines if isinstance(h, str) and h.strip()]
    held = bool(served and texts)
    checks.append({
        "check_id": "BB2",
        "satisfied": bool(held),
        "detail": (f"{len(texts)} headlines recorded, "
                   f"first: {texts[0][:80]}" if held else
                   "no headlines recorded"),
    })
    return {"status": "verified", "checks": checks}
