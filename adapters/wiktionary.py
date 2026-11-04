"""Reusable application adapter: Wiktionary word lookup (read-only).

https://en.wiktionary.org/ is read but never written: the driver
opens one dictionary entry directly and records whether the word
exists and what it defines. Missing words render a "no entry"
marker instead of definitions — that is a verified failure, not
missing evidence.

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

APPROVED_ORIGIN = "https://en.wiktionary.org"

HOME_PATH = "/"
HOME_URL = APPROVED_ORIGIN + HOME_PATH

# Entry pages: /wiki/<word> (single segment, never Special:).
ENTRY_PATH_RE = re.compile(r"^/wiki/[^/:]+$")

# Words the driver accepts: letters plus the in-word punctuation
# real headwords use. Anything else is refused before navigation.
WORD_RE = re.compile(r"^[A-Za-z][A-Za-z'’\- ]{0,39}$")

STAGES_SUFFIX = ".stages.json"

#: Bound for single-element reads on a re-rendering page.
READ_TIMEOUT_MS = 8000

# -- selectors (drivers must use these exact strings) ------------------

SEL_ENTRY_H1 = "h1#firstHeading"
SEL_NO_ENTRY = ".noarticletext"
SEL_DEFINITION = ".mw-parser-output ol li"

# Observer-policy targets: navigation only (no fills or clicks).
WIKT_FILL_TARGETS: tuple = ()
WIKT_CLICK_TARGETS: tuple = ()


class UnapprovedURLError(ValueError):
    """A navigation target outside the approved Wiktionary pages."""


def assert_approved_url(url: str) -> str:
    """Fail closed unless the URL is home or a dictionary entry."""
    match = re.match(r"^(https://[^/]+)(/[^?#]*)?", url or "")
    if not match or match.group(1) != APPROVED_ORIGIN:
        raise UnapprovedURLError(
            f"refusing navigation outside {APPROVED_ORIGIN}: {url!r}")
    path = match.group(2) or "/"
    if path == HOME_PATH or ENTRY_PATH_RE.match(path):
        return url
    raise UnapprovedURLError(
        f"refusing unapproved Wiktionary path: {url!r}")


def entry_url(word: str) -> str:
    """Deterministic entry URL for a validated word."""
    clean = (word or "").strip()
    if not WORD_RE.match(clean):
        raise ValueError(f"refusing word outside the allowed shape: {word!r}")
    slug = quote(clean.replace(" ", "_"), safe="-_.")
    return f"{APPROVED_ORIGIN}/wiki/{slug}"


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


# -- duck-typed stage readers (no Playwright import) --------------------

def read_entry_state(page: Any) -> Dict[str, Any]:
    """Entry identity: heading, missing marker, definition count."""
    try:
        url = page.url
    except Exception:  # noqa: BLE001 — duck-typed property
        url = ""
    try:
        heading = (page.locator(SEL_ENTRY_H1).first.text_content(
            timeout=READ_TIMEOUT_MS) or "").strip()
    except Exception:  # noqa: BLE001 — missing heading reads empty
        heading = ""
    try:
        missing = page.locator(SEL_NO_ENTRY).count() > 0
    except Exception:  # noqa: BLE001 — marker read is best-effort
        missing = False
    definitions = 0
    first_def = ""
    try:
        items = page.locator(SEL_DEFINITION)
        total = items.count()
        for i in range(min(total, 30)):
            try:
                text = (items.nth(i).text_content(timeout=READ_TIMEOUT_MS)
                        or "").strip()
            except Exception:  # noqa: BLE001 — one bad row skips
                continue
            if len(text) >= 10:
                definitions += 1
                if not first_def:
                    first_def = text[:300]
    except Exception:  # noqa: BLE001 — definition scan best-effort
        pass
    return {"url": url if isinstance(url, str) else "", "heading": heading,
            "missing": bool(missing), "definitions": definitions,
            "first_def": first_def}


STAGE_READERS = {
    "entry": read_entry_state,
}


def capture_end_snapshot(page: Any) -> Dict[str, Any]:
    """Final pre-teardown state read (executor observe hook)."""
    return read_entry_state(page)


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

def verify_wiktionary_lookup(snapshot: Dict[str, Any] | None,
                             stages: List[Dict[str, Any]],
                             expected: Dict[str, Any]) -> Dict[str, Any]:
    """Judge a Wiktionary lookup from recorded stage states.

    ``expected`` carries ``word``. WX1 judges the entry exists and
    matches; WX2 judges definitions are present.
    """
    states = stage_states(stages)
    if not states and not isinstance(snapshot, dict):
        return {"status": "unavailable", "checks": []}
    checks: List[Dict[str, Any]] = []
    want = str(expected.get("word") or "").strip().lower()

    entry = states.get("entry", {})
    heading = str(entry.get("heading") or "")
    missing = entry.get("missing") is True
    match = bool(heading) and not missing and heading.strip().lower() == want
    checks.append({
        "check_id": "WX1",
        "satisfied": bool(match),
        "detail": (f"entry verified: {heading[:80]}" if match else
                   "no such entry" if missing else
                   f"entry mismatch: heading={heading[:60]!r}, "
                   f"wanted {want!r}"),
    })

    definitions = int(entry.get("definitions") or 0)
    checks.append({
        "check_id": "WX2",
        "satisfied": bool(match and definitions >= 1),
        "detail": (f"{definitions} definitions recorded" if match and
                   definitions >= 1 else
                   "no definitions recorded"),
    })
    return {"status": "verified", "checks": checks}
