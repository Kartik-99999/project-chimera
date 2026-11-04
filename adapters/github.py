"""GitHub public-profile adapter: fail-closed reads, no logins, no writes."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote

APPROVED_ORIGIN = "https://github.com"

HOME_PATH = "/"
HOME_URL = APPROVED_ORIGIN + HOME_PATH

USERNAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
PROFILE_PATH_RE = re.compile(r"^/[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?/?$")
# Top-level names GitHub reserves for stateful product pages; the
# driver never navigates to them even though they look like users.
RESERVED_NAMES = frozenset({
    "login", "session", "sessions", "join", "settings", "account",
    "password_reset", "confirm_verification", "recovery", "logout",
    "new", "search", "notifications", "watching", "explore",
})
# Regex alternation of RESERVED_NAMES for observer-policy patterns.
RESERVED_ALTERNATION = "(?:" + "|".join(sorted(RESERVED_NAMES)) + ")"

STAGES_SUFFIX = ".stages.json"

READ_TIMEOUT_MS = 8000

SEL_NICKNAME = ".p-nickname"
SEL_NAME = ".p-name"

GITHUB_FILL_TARGETS: tuple = ()
GITHUB_CLICK_TARGETS: tuple = ()


class UnapprovedURLError(ValueError):
    """A navigation target fell outside the approved GitHub pages."""


def assert_approved_url(url: str) -> str:
    """Fail closed unless the URL is home or a public profile page."""
    match = re.match(r"^(https://[^/]+)(/[^?#]*)?", url or "")
    if not match or match.group(1) != APPROVED_ORIGIN:
        raise UnapprovedURLError(
            f"refusing navigation outside {APPROVED_ORIGIN}: {url!r}")
    path = match.group(2) or "/"
    if path == HOME_PATH:
        return url
    if PROFILE_PATH_RE.match(path):
        slug = path.strip("/").split("/")[0].lower()
        if slug in RESERVED_NAMES:
            raise UnapprovedURLError(
                f"refusing reserved GitHub path: {url!r}")
        return url
    raise UnapprovedURLError(
        f"refusing unapproved GitHub path: {url!r}")


def profile_url(username: str) -> str:
    """Deterministic profile URL for a validated username."""
    clean = (username or "").strip()
    if not USERNAME_RE.match(clean):
        raise ValueError(
            f"refusing username outside the allowed shape: {username!r}")
    if clean.lower() in RESERVED_NAMES:
        raise ValueError(
            f"refusing reserved GitHub name: {username!r}")
    return f"{APPROVED_ORIGIN}/{quote(clean, safe='-')}"


def utcnow() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_profile_state(page: Any) -> Dict[str, Any]:
    """Profile identity: nickname and display name (empty on 404)."""
    try:
        url = page.url
    except Exception:  # noqa: BLE001 — duck-typed property
        url = ""
    try:
        nickname = (page.locator(SEL_NICKNAME).first.text_content(
            timeout=READ_TIMEOUT_MS) or "").strip()
    except Exception:  # noqa: BLE001 — missing handle reads empty
        nickname = ""
    try:
        name = (page.locator(SEL_NAME).first.text_content(
            timeout=READ_TIMEOUT_MS) or "").strip()
    except Exception:  # noqa: BLE001 — missing name reads empty
        name = ""
    return {"url": url if isinstance(url, str) else "",
            "nickname": nickname, "name": name}


STAGE_READERS = {
    "profile": read_profile_state,
}


def capture_end_snapshot(page: Any) -> Dict[str, Any]:
    """Final pre-teardown state read (executor observe hook)."""
    return read_profile_state(page)


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

def verify_github_profile(snapshot: Dict[str, Any] | None,
                          stages: List[Dict[str, Any]],
                          expected: Dict[str, Any]) -> Dict[str, Any]:
    """Judge a GitHub profile lookup from recorded stage states.

    ``expected`` carries ``username``. GH1 judges the profile
    handle matches; GH2 judges a display name is present.
    """
    states = stage_states(stages)
    if not states and not isinstance(snapshot, dict):
        return {"status": "unavailable", "checks": []}
    checks: List[Dict[str, Any]] = []
    want = str(expected.get("username") or "").strip().lower()

    profile = states.get("profile", {})
    nickname = str(profile.get("nickname") or "").strip()
    match = bool(nickname) and nickname.lower() == want
    checks.append({
        "check_id": "GH1",
        "satisfied": bool(match),
        "detail": (f"profile verified: {nickname}" if match else
                   f"no such profile (handle={nickname!r}, "
                   f"wanted {want!r})"),
    })

    name = str(profile.get("name") or "").strip()
    held = bool(match and name)
    checks.append({
        "check_id": "GH2",
        "satisfied": bool(held),
        "detail": (f"display name: {name[:80]}" if held else
                   "display name missing"),
    })
    return {"status": "verified", "checks": checks}
