"""crates.io adapter: fail-closed reads of one crate page."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote

APPROVED_ORIGIN = "https://crates.io"

HOME_PATH = "/"
HOME_URL = APPROVED_ORIGIN + HOME_PATH

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
CRATE_PATH_RE = re.compile(r"^/crates/[^/]+/?$")

STAGES_SUFFIX = ".stages.json"

READ_TIMEOUT_MS = 8000

SEL_H1 = "main h1"
SEL_META_DESCRIPTION = 'meta[name="description"]'

CRATES_FILL_TARGETS: tuple = ()
CRATES_CLICK_TARGETS: tuple = ()


class UnapprovedURLError(ValueError):
    """A navigation target fell outside the approved crates.io pages."""


def assert_approved_url(url: str) -> str:
    """Fail closed unless the URL is home or a crate page."""
    match = re.match(r"^(https://[^/]+)(/[^?#]*)?", url or "")
    if not match or match.group(1) != APPROVED_ORIGIN:
        raise UnapprovedURLError(
            f"refusing navigation outside {APPROVED_ORIGIN}: {url!r}")
    path = match.group(2) or "/"
    if path == HOME_PATH or CRATE_PATH_RE.match(path):
        return url
    raise UnapprovedURLError(
        f"refusing unapproved crates.io path: {url!r}")


def crate_url(name: str) -> str:
    """Deterministic crate URL for a validated crate name."""
    clean = (name or "").strip()
    if not NAME_RE.match(clean):
        raise ValueError(
            f"refusing crate name outside the allowed shape: {name!r}")
    return f"{APPROVED_ORIGIN}/crates/{quote(clean, safe='-_')}"


def utcnow() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_crate_state(page: Any) -> Dict[str, Any]:
    """Crate identity: header name, version, and summary."""
    try:
        url = page.url
    except Exception:  # noqa: BLE001 — duck-typed property
        url = ""
    try:
        header = (page.locator(SEL_H1).first.text_content(
            timeout=READ_TIMEOUT_MS) or "").strip()
    except Exception:  # noqa: BLE001 — missing header reads empty
        header = ""
    missing = "not found" in header.lower()
    name, version = "", ""
    if header and not missing:
        bits = header.split(" v", 1)
        if len(bits) == 2:
            name, version = bits[0].strip(), bits[1].strip()
        else:
            name = bits[0].strip()
    try:
        summary = (page.locator(SEL_META_DESCRIPTION).first.get_attribute(
            "content", timeout=READ_TIMEOUT_MS) or "").strip()
    except Exception:  # noqa: BLE001 — missing meta reads empty
        summary = ""
    return {"url": url if isinstance(url, str) else "", "name": name,
            "version": version, "summary": summary[:300],
            "missing": bool(missing)}


STAGE_READERS = {
    "crate": read_crate_state,
}


def capture_end_snapshot(page: Any) -> Dict[str, Any]:
    """Final pre-teardown state read (executor observe hook)."""
    return read_crate_state(page)


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

def verify_crates_lookup(snapshot: Dict[str, Any] | None,
                         stages: List[Dict[str, Any]],
                         expected: Dict[str, Any]) -> Dict[str, Any]:
    """Judge a crates.io lookup from recorded stage states.

    ``expected`` carries ``crate``. CR1 judges the header names
    the crate; CR2 judges a version and summary are present.
    """
    states = stage_states(stages)
    if not states and not isinstance(snapshot, dict):
        return {"status": "unavailable", "checks": []}
    checks: List[Dict[str, Any]] = []
    want = str(expected.get("crate") or "").strip().lower()

    crate = states.get("crate", {})
    got = str(crate.get("name") or "").strip().lower()
    match = bool(got) and got == want and not crate.get("missing")
    checks.append({
        "check_id": "CR1",
        "satisfied": bool(match),
        "detail": (f"crate verified: {crate.get('name')}" if match else
                   "no such crate" if crate.get("missing") else
                   f"crate mismatch (header={got!r}, wanted {want!r})"),
    })

    version = str(crate.get("version") or "")
    summary = str(crate.get("summary") or "")
    held = bool(match and version and len(summary) >= 10)
    checks.append({
        "check_id": "CR2",
        "satisfied": bool(held),
        "detail": (f"version {version}: {summary[:80]}" if held else
                   "version or summary missing"),
    })
    return {"status": "verified", "checks": checks}
