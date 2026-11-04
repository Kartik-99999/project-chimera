"""Reusable application adapter: Wikipedia article lookup (read-only).

https://en.wikipedia.org/ is read but never written: the driver
searches, opens one article, and records what it shows. Search has
two honest outcomes — an exact-title match redirects straight to
the article, anything else lands on the results list — and both
flow through the same two stages (search, article).

Layering: this package imports nothing from ``chimera``,
``benchmarks``, or ``workbench``. Only the standard library.

Stages-file contract (``<run>.stages.json`` next to the trace)::

    {"run_id": str, "stages": [
        {"stage": str, "url": str, "captured_at": str, "state": {...}}]}
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote_plus

APPROVED_ORIGIN = "https://en.wikipedia.org"

HOME_PATH = "/"
SEARCH_PREFIX = "/w/index.php"

HOME_URL = APPROVED_ORIGIN + HOME_PATH

# Article pages: /wiki/<Title> (single segment, no Special: pages).
ARTICLE_PATH_RE = re.compile(r"^/wiki/[^/:]+$")

STAGES_SUFFIX = ".stages.json"

#: Bound for single-element reads on a re-rendering page.
READ_TIMEOUT_MS = 8000

# -- selectors (drivers must use these exact strings) ------------------

SEL_SEARCH_INPUT = "#searchInput"
SEL_RESULT_LINK = ".mw-search-result-heading a"
SEL_ARTICLE_H1 = "h1#firstHeading"
SEL_CONTENT_PARA = "#mw-content-text p"

# Observer-policy targets (css constructions; value_length excluded).
WIKI_FILL_TARGETS = (
    {"by": "css", "selector": SEL_SEARCH_INPUT},
)

WIKI_CLICK_TARGETS: tuple = ()


class UnapprovedURLError(ValueError):
    """A navigation target outside the approved Wikipedia pages."""


def assert_approved_url(url: str) -> str:
    """Fail closed unless the URL is home, search, or an article.

    The search endpoint only passes with a non-empty ``search``
    query — action/edit URLs through the same path are refused.
    """
    from urllib.parse import parse_qs, urlsplit

    try:
        parts = urlsplit(url or "")
    except ValueError:
        raise UnapprovedURLError(f"refusing malformed URL: {url!r}")
    if f"{parts.scheme}://{parts.netloc}" != APPROVED_ORIGIN:
        raise UnapprovedURLError(
            f"refusing navigation outside {APPROVED_ORIGIN}: {url!r}")
    path = parts.path or "/"
    if path == HOME_PATH:
        return url
    if path == SEARCH_PREFIX:
        query = parse_qs(parts.query).get("search", [""])
        if query and query[0].strip():
            return url
        raise UnapprovedURLError(
            f"refusing non-search use of {SEARCH_PREFIX}: {url!r}")
    if ARTICLE_PATH_RE.match(path):
        return url
    raise UnapprovedURLError(
        f"refusing unapproved Wikipedia path: {url!r}")


def search_url(query: str) -> str:
    """Deterministic search URL for a validated query string."""
    return (f"{APPROVED_ORIGIN}{SEARCH_PREFIX}?search={quote_plus(query)}"
            f"&title=Special%3ASearch&ns0=1")


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


# -- duck-typed stage readers (no Playwright import) --------------------

def read_search_state(page: Any) -> Dict[str, Any]:
    """Search outcome: redirect flag plus result titles and hrefs."""
    try:
        url = page.url
    except Exception:  # noqa: BLE001 — duck-typed property
        url = ""
    url = url if isinstance(url, str) else ""
    path = url.split(APPROVED_ORIGIN, 1)[-1].split("?", 1)[0]
    redirected = bool(ARTICLE_PATH_RE.match(path or "/"))
    links = page.locator(SEL_RESULT_LINK)
    count = links.count()
    results: List[Dict[str, str]] = []
    for i in range(count):
        if len(results) >= 10:
            break
        try:
            link = links.nth(i)
            href = link.get_attribute("href", timeout=READ_TIMEOUT_MS) or ""
            title = (link.text_content(timeout=READ_TIMEOUT_MS)
                     or "").strip()
        except Exception:  # noqa: BLE001 — one bad row skips, not fails
            continue
        if href and title:
            results.append({"title": title[:200], "href": href})
    return {"url": url, "redirected": redirected, "count": count,
            "results": results}


def read_article_state(page: Any) -> Dict[str, Any]:
    """Article identity: heading plus the first substantial paragraph."""
    try:
        url = page.url
    except Exception:  # noqa: BLE001 — duck-typed property
        url = ""
    try:
        heading = (page.locator(SEL_ARTICLE_H1).first.text_content(
            timeout=READ_TIMEOUT_MS) or "").strip()
    except Exception:  # noqa: BLE001 — missing heading reads empty
        heading = ""
    summary = ""
    try:
        paras = page.locator(SEL_CONTENT_PARA)
        for i in range(min(paras.count(), 12)):
            try:
                text = (paras.nth(i).text_content(timeout=READ_TIMEOUT_MS)
                        or "").strip()
            except Exception:  # noqa: BLE001 — one bad para skips
                continue
            if len(text) >= 40:
                summary = text[:500]
                break
    except Exception:  # noqa: BLE001 — para scan is best-effort
        pass
    return {"url": url if isinstance(url, str) else "", "heading": heading,
            "summary": summary}


STAGE_READERS = {
    "search": read_search_state,
    "article": read_article_state,
}


def wait_for_any(page: Any, selectors: List[str], timeout_ms: int,
                 poll_ms: int = 100) -> str | None:
    """Return the first selector that becomes visible, else None.

    Read-only settle loop for post-navigation transitions. Plain
    visibility polling — not a retry of any action — bounded by
    ``timeout_ms``. Reads go through the page object, so a
    recording proxy observes them.
    """
    deadline = time.monotonic() + max(0, timeout_ms) / 1000
    while True:
        for selector in selectors:
            try:
                if page.locator(selector).first.is_visible():
                    return selector
            except Exception:  # noqa: BLE001 — a failed read is "not yet"
                continue
        if time.monotonic() >= deadline:
            return None
        time.sleep(max(0.01, poll_ms / 1000))


def capture_end_snapshot(page: Any) -> Dict[str, Any]:
    """Final pre-teardown state read (executor observe hook)."""
    return read_article_state(page)


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

def verify_wikipedia_lookup(snapshot: Dict[str, Any] | None,
                            stages: List[Dict[str, Any]],
                            expected: Dict[str, Any]) -> Dict[str, Any]:
    """Judge a Wikipedia lookup from recorded stage states.

    ``expected`` carries ``query`` and ``pick`` (1-based). F1 judges
    that the search was useful (a direct-article redirect, or enough
    results to pick from); F2 judges the captured article (heading
    present, summary present, consistent with the pick/redirect).
    """
    states = stage_states(stages)
    if not states and not isinstance(snapshot, dict):
        return {"status": "unavailable", "checks": []}
    checks: List[Dict[str, Any]] = []
    pick = max(1, int(expected.get("pick", 1)))

    search = states.get("search", {})
    results = search.get("results") or []
    redirected = search.get("redirected") is True
    picked = results[pick - 1] if len(results) >= pick else {}
    useful = bool(redirected or picked)
    checks.append({
        "check_id": "WI1",
        "satisfied": bool(useful),
        "detail": (f"search redirected straight to the article"
                   if redirected else
                   f"search returned {len(results)} results; "
                   f"picked #{pick}: "
                   f"{(picked.get('title') or '')[:80]}" if picked else
                   f"search has {len(results)} results, "
                   f"cannot pick #{pick}"),
    })

    article = states.get("article", {})
    heading = str(article.get("heading") or "")
    summary = str(article.get("summary") or "")
    if redirected:
        consistent = bool(heading)
    elif picked:
        want = str(picked.get("title") or "").lower()
        consistent = bool(heading) and (
            want in heading.lower() or heading.lower() in want)
    else:
        consistent = False
    held = bool(consistent and len(summary) >= 40)
    checks.append({
        "check_id": "WI2",
        "satisfied": bool(held),
        "detail": (f"article verified: {heading[:80]} "
                   f"({len(summary)} summary chars)" if held else
                   "article not confirmed "
                   f"(heading={heading[:60]!r}, "
                   f"summary_chars={len(summary)})"),
    })
    return {"status": "verified", "checks": checks}
