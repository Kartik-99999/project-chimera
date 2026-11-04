"""User browser sessions: persistent profiles for logged-in runs.

Clean sessions (a fresh browser with no stored state) remain the
default everywhere. Some sites refuse automation from clean
sessions; for those, a workflow may declare ``sessions=("clean",
"user")`` and the run may name a persistent Chromium profile. The
profile lives outside the repository (it holds live session
cookies) and is created by an explicit, interactive login step in
which the *user* — never Chimera — types credentials into a
visible browser window:

    python -m workbench.sessions login <profile> --url <site>

Chimera never sees, stores, or logs credentials; it only reuses
the cookies the user's own login left behind. Every execution
record carries its session label (``clean`` or ``user:<name>``)
so user-state evidence is never mixed with clean-session
evidence.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from workbench.workflows import WorkflowValidationError

PROFILE_NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
ENV_PROFILES_DIR = "CHIMERA_PROFILES_DIR"


class ProfileError(WorkflowValidationError):
    """A user-session request was invalid (maps to HTTP 400)."""


class ProfileNameError(ProfileError):
    """The profile name falls outside the allowed shape."""


class ProfileMissingError(ProfileError):
    """The named profile does not exist yet."""


def profiles_dir() -> Path:
    """Root for persistent browser profiles (outside the repo)."""
    override = os.environ.get(ENV_PROFILES_DIR, "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / ".chimera" / "profiles"


def check_profile_name(name: str) -> str:
    """Validate a profile name; return it or raise."""
    clean = (name or "").strip()
    if not PROFILE_NAME_RE.match(clean):
        raise ProfileNameError(
            f"refusing profile name outside [a-z0-9-]: {name!r}")
    return clean


def profile_path(name: str) -> Path:
    """Resolved, containment-checked directory for a valid name."""
    clean = check_profile_name(name)
    root = profiles_dir().resolve() if profiles_dir().exists() \
        else profiles_dir()
    path = (profiles_dir() / clean).resolve()
    if root != path and root not in path.parents:
        raise ProfileNameError(
            f"refusing profile path outside {profiles_dir()}: {name!r}")
    return path


def list_profiles() -> List[str]:
    """Names of existing profiles (sorted, empty when none)."""
    root = profiles_dir()
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir()
                  if p.is_dir() and PROFILE_NAME_RE.match(p.name))


def remove_profile(name: str) -> bool:
    """Delete a profile and its cookies; True when one existed."""
    path = profile_path(name)
    if not path.is_dir():
        return False
    shutil.rmtree(path)
    return True


def require_profile(name: str) -> Path:
    """Existing profile directory, or an actionable error."""
    path = profile_path(name)
    if not path.is_dir():
        raise ProfileMissingError(
            f"no such Chimera profile {path.name!r}: log in once with "
            f"`python -m workbench.sessions login {path.name}`, then "
            f"re-run with that profile")
    return path


def prepare_profile_dir(name: str) -> Path:
    """Create a profile directory with owner-only permissions."""
    path = profile_path(name)
    path.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path, 0o700)
    except OSError:  # noqa: BLE001 — best-effort hardening
        pass
    return path


class _NullBrowser:
    """Stand-in for persistent contexts (context close suffices)."""

    def close(self) -> None:
        return None


def profile_browser_factory(profile: str,
                            *, headless: bool = True) -> Callable:
    """Browser factory for the agent hook: persistent profile + recorder.

    Same shape as :func:`workbench.executor.real_chimera_factory`
    (``make(log, shot_path)`` returning ``factory(playwright)``),
    but the browser keeps the named profile's cookies, storage,
    and challenge clearances across runs.
    """
    user_data_dir = str(require_profile(profile))

    def make(log: Any, shot_path: Any) -> Callable:
        from benchmarks.observer import RecordingPage
        from workbench.executor import _ShotOnClose

        def factory(playwright: Any) -> tuple:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir, headless=headless)
            raw_page = context.new_page()
            page = RecordingPage(raw_page, log)
            holder["shot"] = _ShotOnClose(context, raw_page, shot_path)
            return _NullBrowser(), holder["shot"], page

        holder: Dict[str, Any] = {}
        factory.holder = holder  # type: ignore[attr-defined]
        return factory

    return make


def login(name: str, url: str,
          input_fn: Optional[Callable[[str], str]] = None) -> Path:
    """Interactive login: headed browser, user types, Chimera waits.

    Opens the site in a visible window on the named profile and
    blocks until the user confirms the login (including any human
    challenge) is done. Credentials are typed into the site's own
    page; Chimera never sees them.
    """
    from playwright.sync_api import sync_playwright

    path = prepare_profile_dir(name)
    ask = input_fn or input
    print(f"Opening {url} in a visible browser on profile {path.name!r}.")
    print("Log in (and clear any human challenge) in that window, then "
          "return here and press Enter. Chimera never sees credentials.")
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            str(path), headless=False)
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        try:
            ask("Press Enter once logged in (Ctrl-C aborts): ")
        finally:
            context.close()
    print(f"Profile {path.name!r} ready at {path}.")
    return path


def main(argv: Optional[List[str]] = None) -> int:
    """CLI: ``login <profile> [--url U]`` | ``list`` | ``remove <p>``."""
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] not in ("login", "list", "remove"):
        print("usage: python -m workbench.sessions "
              "login <profile> [--url URL] | list | remove <profile>",
              file=sys.stderr)
        return 2
    if args[0] == "list":
        for name in list_profiles():
            print(name)
        return 0
    if args[0] == "remove":
        if len(args) != 2:
            print("usage: python -m workbench.sessions remove <profile>",
                  file=sys.stderr)
            return 2
        try:
            existed = remove_profile(args[1])
        except ProfileError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"removed profile {args[1]!r}" if existed
              else f"no such profile {args[1]!r}")
        return 0
    # login <profile> [--url URL]
    rest = args[1:]
    url = "https://www.amazon.com/"
    if "--url" in rest:
        idx = rest.index("--url")
        if idx + 1 >= len(rest):
            print("usage: python -m workbench.sessions login <profile> "
                  "[--url URL]", file=sys.stderr)
            return 2
        url = rest[idx + 1]
        del rest[idx:idx + 2]
    if len(rest) != 1:
        print("usage: python -m workbench.sessions login <profile> "
              "[--url URL]", file=sys.stderr)
        return 2
    try:
        login(rest[0], url)
    except ProfileError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\naborted; the profile keeps whatever state was stored.",
              file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
