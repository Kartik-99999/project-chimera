"""Reusable application adapter: PyPI package lookup (read-only).

https://pypi.org/ is read but never written: the driver opens one
project page directly and records the package name, version, and
summary. Unknown names render no project header — a verified
failure, not missing evidence.

Layering: this package imports nothing from ``chimera``,
``benchmarks``, or ``workbench``. Only the standard library.

Stages-file contract (``<run>.stages.json`` next to the trace)::

    {"run_id": str, "stages": [
        {"stage": str, "url": str, "captured_at": str, "state": {...}}]}
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote

APPROVED_ORIGIN = "https://pypi.org"

HOME_PATH = "/"
HOME_URL = APPROVED_ORIGIN + HOME_PATH

# Project pages: /project/<name>/ (trailing slash optional).
PROJECT_PATH_RE = re.compile(r"^/project/[^/]+/?$")

# Names the driver accepts (PyPI's allowed alphabet).
NAME_RE = re.compile(r"^[A-Za-z0-9_.\-]{1,60}$")

STAGES_SUFFIX = ".stages.json"

#: Bound for single-element reads on a re-rendering page.
READ_TIMEOUT_MS = 8000

# -- selectors (drivers must use these exact strings) ------------------

SEL_PROJECT_H1 = "h1.project-header__name"
SEL_META_DESCRIPTION = 'meta[name="description"]'

# Observer-policy targets: navigation only (no fills or clicks).
PYPI_FILL_TARGETS: tuple = ()
PYPI_CLICK_TARGETS: tuple = ()


class UnapprovedURLError(ValueError):
    """A navigation target outside the approved PyPI pages."""


def assert_approved_url(url: str) -> str:
    """Fail closed unless the URL is home or a project page."""
    match = re.match(r"^(https://[^/]+)(/[^?#]*)?", url or "")
    if not match or match.group(1) != APPROVED_ORIGIN:
        raise UnapprovedURLError(
            f"refusing navigation outside {APPROVED_ORIGIN}: {url!r}")
    path = match.group(2) or "/"
    if path == HOME_PATH or PROJECT_PATH_RE.match(path):
        return url
    raise UnapprovedURLError(
        f"refusing unapproved PyPI path: {url!r}")


def project_url(name: str) -> str:
    """Deterministic project URL for a validated package name."""
    clean = (name or "").strip()
    if not NAME_RE.match(clean):
        raise ValueError(
            f"refusing package name outside the allowed shape: {name!r}")
    return f"{APPROVED_ORIGIN}/project/{quote(clean, safe='-_.')}/"


def normalize(name: str) -> str:
    """PEP 503-ish normalization for name comparison."""
    return re.sub(r"[-_.]+", "-", (name or "").strip().lower())


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


# -- duck-typed stage readers (no Playwright import) --------------------

def read_package_state(page: Any) -> Dict[str, Any]:
    """Project identity: header name, version, and summary."""
    try:
        url = page.url
    except Exception:  # noqa: BLE001 — duck-typed property
        url = ""
    try:
        header = (page.locator(SEL_PROJECT_H1).first.text_content(
            timeout=READ_TIMEOUT_MS) or "").strip()
    except Exception:  # noqa: BLE001 — missing header reads empty
        header = ""
    name, version = "", ""
    if header:
        bits = header.split()
        if len(bits) >= 2:
            name, version = " ".join(bits[:-1]), bits[-1]
        else:
            name = bits[0]
    try:
        summary = (page.locator(SEL_META_DESCRIPTION).first.get_attribute(
            "content", timeout=READ_TIMEOUT_MS) or "").strip()
    except Exception:  # noqa: BLE001 — missing meta reads empty
        summary = ""
    return {"url": url if isinstance(url, str) else "", "name": name,
            "version": version, "summary": summary[:300]}


STAGE_READERS = {
    "package": read_package_state,
}


def capture_end_snapshot(page: Any) -> Dict[str, Any]:
    """Final pre-teardown state read (executor observe hook)."""
    return read_package_state(page)


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

def verify_pypi_lookup(snapshot: Dict[str, Any] | None,
                       stages: List[Dict[str, Any]],
                       expected: Dict[str, Any]) -> Dict[str, Any]:
    """Judge a PyPI lookup from recorded stage states.

    ``expected`` carries ``package``. PY1 judges the header names
    the package; PY2 judges a version and summary are present.
    """
    states = stage_states(stages)
    if not states and not isinstance(snapshot, dict):
        return {"status": "unavailable", "checks": []}
    checks: List[Dict[str, Any]] = []
    want = normalize(str(expected.get("package") or ""))

    package = states.get("package", {})
    got = normalize(str(package.get("name") or ""))
    match = bool(got) and got == want
    checks.append({
        "check_id": "PY1",
        "satisfied": bool(match),
        "detail": (f"package verified: {package.get('name')}" if match else
                   f"no such package (header={got!r}, wanted {want!r})"),
    })

    version = str(package.get("version") or "")
    summary = str(package.get("summary") or "")
    held = bool(match and version and len(summary) >= 10)
    checks.append({
        "check_id": "PY2",
        "satisfied": bool(held),
        "detail": (f"version {version}: {summary[:80]}" if held else
                   "version or summary missing"),
    })
    return {"status": "verified", "checks": checks}
