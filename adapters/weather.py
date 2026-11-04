"""BBC Weather adapter: fail-closed reads of one city forecast page."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

APPROVED_ORIGIN = "https://www.bbc.com"

HOME_PATH = "/"
HOME_URL = APPROVED_ORIGIN + HOME_PATH

# City key -> (BBC location id, heading label).
CITIES = {
    "london": ("2643743", "London"),
    "new-york": ("5128581", "New York"),
    "tokyo": ("1850147", "Tokyo"),
    "sydney": ("2147714", "Sydney"),
    "paris": ("2988507", "Paris"),
}
WEATHER_PATH_RE = re.compile(r"^/weather/\d+/?$")

STAGES_SUFFIX = ".stages.json"

READ_TIMEOUT_MS = 8000
MAX_TEMPS = 12

SEL_H1 = "h1"
SEL_TEMP = ".wr-value--temperature"

WEATHER_FILL_TARGETS: tuple = ()
WEATHER_CLICK_TARGETS: tuple = ()


class UnapprovedURLError(ValueError):
    """A navigation target fell outside the approved weather pages."""


def assert_approved_url(url: str) -> str:
    """Fail closed unless the URL is home or a city weather page."""
    match = re.match(r"^(https://[^/]+)(/[^?#]*)?", url or "")
    if not match or match.group(1) != APPROVED_ORIGIN:
        raise UnapprovedURLError(
            f"refusing navigation outside {APPROVED_ORIGIN}: {url!r}")
    path = match.group(2) or "/"
    if path == HOME_PATH or WEATHER_PATH_RE.match(path):
        return url
    raise UnapprovedURLError(
        f"refusing unapproved BBC Weather path: {url!r}")


def city_url(city: str) -> str:
    """Deterministic weather URL for a validated city key."""
    entry = CITIES.get((city or "").strip().lower())
    if entry is None:
        raise ValueError(
            f"refusing city outside {sorted(CITIES)}: {city!r}")
    return f"{APPROVED_ORIGIN}/weather/{entry[0]}"


def utcnow() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_weather_state(page: Any) -> Dict[str, Any]:
    """Forecast identity: city heading plus recorded temperatures."""
    try:
        url = page.url
    except Exception:  # noqa: BLE001 — duck-typed property
        url = ""
    try:
        heading = (page.locator(SEL_H1).first.text_content(
            timeout=READ_TIMEOUT_MS) or "").strip()
    except Exception:  # noqa: BLE001 — missing heading reads empty
        heading = ""
    temps: List[str] = []
    try:
        items = page.locator(SEL_TEMP)
        total = items.count()
        for i in range(min(total, MAX_TEMPS)):
            try:
                text = (items.nth(i).text_content(timeout=READ_TIMEOUT_MS)
                        or "").strip()
            except Exception:  # noqa: BLE001 — one bad row skips
                continue
            if text:
                temps.append(text[:40])
        count = total
    except Exception:  # noqa: BLE001 — temperature scan best-effort
        count = 0
    return {"url": url if isinstance(url, str) else "",
            "heading": heading, "count": int(count), "temps": temps}


STAGE_READERS = {
    "forecast": read_weather_state,
}


def capture_end_snapshot(page: Any) -> Dict[str, Any]:
    """Final pre-teardown state read (executor observe hook)."""
    return read_weather_state(page)


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

def verify_bbc_weather(snapshot: Dict[str, Any] | None,
                       stages: List[Dict[str, Any]],
                       expected: Dict[str, Any]) -> Dict[str, Any]:
    """Judge a BBC Weather capture from recorded stage states.

    ``expected`` carries ``city``. BW1 judges the requested city
    page was served; BW2 judges temperatures were recorded.
    """
    states = stage_states(stages)
    if not states and not isinstance(snapshot, dict):
        return {"status": "unavailable", "checks": []}
    checks: List[Dict[str, Any]] = []
    city = str(expected.get("city") or "").strip().lower()
    entry = CITIES.get(city)

    found = states.get("forecast", {})
    heading = str(found.get("heading") or "")
    url = str(found.get("url") or "")
    served = bool(
        entry and heading.startswith(entry[1])
        and f"/weather/{entry[0]}" in url.split("?")[0].split("#")[0])
    checks.append({
        "check_id": "BW1",
        "satisfied": bool(served),
        "detail": (f"city verified: {heading[:80]}" if served else
                   f"city mismatch: heading={heading[:60]!r}, "
                   f"url={url[:80]!r}, wanted {city!r}"),
    })

    temps = found.get("temps")
    if not isinstance(temps, list):
        temps = []
    texts = [t for t in temps if isinstance(t, str) and t.strip()]
    held = bool(served and texts)
    checks.append({
        "check_id": "BW2",
        "satisfied": bool(held),
        "detail": (f"{len(texts)} temperatures recorded, "
                   f"first: {texts[0][:40]}" if held else
                   "no temperatures recorded"),
    })
    return {"status": "verified", "checks": checks}
