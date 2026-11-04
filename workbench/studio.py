"""Workflow Studio: user-defined browser workflows.

Fixed workflows (``workbench.workflows``) are closed scripts. Studio
workflows are user-composed step lists executed by a generic
step-runner under an explicit per-step contract::

    precondition -> action -> postcondition/effect + evidence

Two drivers run the same definition: Chimera (bounded retries with
evidence-based recovery — state is re-read before every repeat, and
non-idempotent actions without an observable effect are never
retried) and Baseline A (one attempt per step, no recovery). Both
persist identical ``<run>.steps.json`` records; the verdict comes
from judging those records, never from driver claims.

Supported environments are the bundled Demo Task Manager and the
SauceDemo practice store only. Arbitrary websites are not supported.
"""

from __future__ import annotations

import json
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from adapters import saucedemo as sauce_adapter

STEP_TYPES = (
    "navigate",
    "click",
    "fill",
    "select",
    "wait",
    "verify-text",
    "verify-count",
    "capture",
    "verify-state",
)

ENVIRONMENTS = ("demo", "saucedemo")

#: Step types that change (or may change) page state.
ACTION_TYPES = ("navigate", "click", "fill", "select")

#: Safe idempotency defaults. Clicks default non-idempotent (they may
#: submit, purchase, or create); fills and selects overwrite a value
#: and default idempotent; navigation, waits, verifications, and
#: captures are read-only or repeat-safe.
DEFAULT_IDEMPOTENT = {
    "navigate": True,
    "click": False,
    "fill": True,
    "select": True,
    "wait": True,
    "verify-text": True,
    "verify-count": True,
    "capture": True,
    "verify-state": True,
}

DEFAULT_TIMEOUT_MS = 5000
MIN_TIMEOUT_MS = 100
MAX_TIMEOUT_MS = 60000
MIN_ATTEMPTS = 1
MAX_ATTEMPTS = 5
DEFAULT_CHIMERA_ATTEMPTS = 3
MAX_STEPS = 50
MAX_LABEL = 120
MAX_SELECTOR = 500
MAX_TEXT = 2000

STEPS_SUFFIX = ".steps.json"
STUDIO_REPORT_SCHEMA = "studio-replay/1"
REDACTED = "***"

VAR_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


class StudioError(ValueError):
    """A studio definition, variable set, or execution is invalid."""


class StudioStepError(RuntimeError):
    """One step failed. ``code`` classifies the failure for reporting."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


# ---------------------------------------------------------------------------
# Variables and secrets
# ---------------------------------------------------------------------------


def variable_map(definition: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    out = {}
    for var in definition.get("variables", []) or []:
        if isinstance(var, dict) and var.get("name"):
            out[str(var["name"])] = var
    return out


def resolve_variables(definition: Mapping[str, Any],
                      provided: Mapping[str, Any]) -> Dict[str, str]:
    """Merge provided run values over non-secret defaults.

    Raises :class:`StudioError` naming every missing variable. Secret
    variables never carry persisted defaults (rejected at validation),
    so a secret is missing unless provided for this run.
    """
    values: Dict[str, str] = {}
    missing = []
    for name, var in variable_map(definition).items():
        if name in provided and provided[name] is not None:
            values[name] = str(provided[name])
        elif var.get("secret"):
            missing.append(name)
        elif var.get("default") is not None:
            values[name] = str(var["default"])
        else:
            missing.append(name)
    if missing:
        raise StudioError(
            f"missing value(s) for variable(s): {sorted(missing)}")
    return values


def secret_values(definition: Mapping[str, Any],
                  values: Mapping[str, str]) -> List[str]:
    secrets = []
    for name, var in variable_map(definition).items():
        if var.get("secret") and values.get(name):
            secrets.append(values[name])
    return sorted(set(secrets), key=len, reverse=True)


def substitute(text: Any, values: Mapping[str, str]) -> Any:
    """Render ``{{var}}`` references. Non-strings pass through."""
    if not isinstance(text, str):
        return text

    def _replace(match: re.Match) -> str:
        return values.get(match.group(1), match.group(0))

    return VAR_RE.sub(_replace, text)


def redact(text: Any, secrets: List[str]) -> Any:
    """Replace every secret value with ``***``. Non-strings pass through."""
    if not isinstance(text, str) or not secrets:
        return text
    for secret in secrets:
        if secret:
            text = text.replace(secret, REDACTED)
    return text


def referenced_variables(value: Any) -> List[str]:
    if not isinstance(value, str):
        return []
    return sorted(set(VAR_RE.findall(value)))


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

_TEXTISH_FIELDS = ("url", "selector", "value", "text")


def _is_balanced(text: str) -> bool:
    stack: List[str] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    quote = None
    escaped = False
    for char in text:
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
        elif char in "([":
            stack.append(char)
        elif char in pairs:
            if not stack or stack.pop() != pairs[char]:
                return False
    return quote is None and not stack


def check_selector(selector: Any) -> Optional[str]:
    """Syntactic selector sanity. Returns an error message or None."""
    if not isinstance(selector, str) or not selector.strip():
        return "selector is required"
    if len(selector) > MAX_SELECTOR:
        return f"selector exceeds {MAX_SELECTOR} characters"
    if "\x00" in selector or "<" in selector or ">" in selector:
        return "selector contains invalid characters"
    if not _is_balanced(selector):
        return "selector has unbalanced brackets or quotes"
    return None


def _check_url(url: Any, environment: str) -> Optional[str]:
    if not isinstance(url, str) or not url.strip():
        return "url is required"
    if environment == "saucedemo":
        if url.startswith("{{"):
            return None  # variable; validated at runtime with values
        if url.startswith("/"):
            if url not in sauce_adapter.APPROVED_PATHS:
                return f"unapproved SauceDemo path: {url!r}"
            return None
        try:
            sauce_adapter.assert_approved_url(url)
        except sauce_adapter.UnapprovedURLError as exc:
            return str(exc)
        return None
    # Demo Task Manager: only the bundled pages, same directory.
    if url.startswith("{{"):
        return None
    from chimera.agent import CONTACT_APP_PATH, DEMO_APP_PATH

    allowed = {f"file://{DEMO_APP_PATH}", f"file://{CONTACT_APP_PATH}"}
    base = url.split("?", 1)[0].split("#", 1)[0]
    if base in ("demo", "contact"):
        return None
    if base not in allowed:
        return f"demo workflows may only open the bundled pages, got {url!r}"
    return None


def _check_effect(effect: Any, where: str) -> List[Dict[str, str]]:
    errors = []
    if effect is None:
        return errors
    if not isinstance(effect, dict):
        return [{"step": where, "code": "bad-effect",
                 "message": "effect must be an object"}]
    kind = effect.get("kind")
    if kind not in ("visible", "hidden", "text-present", "text-absent",
                    "count"):
        errors.append({"step": where, "code": "bad-effect",
                       "message": f"unknown effect kind {kind!r}"})
        return errors
    if kind in ("visible", "hidden", "count"):
        problem = check_selector(effect.get("selector"))
        if problem:
            errors.append({"step": where, "code": "bad-effect",
                           "message": f"effect selector: {problem}"})
    if kind == "count" and not isinstance(effect.get("count"), int):
        errors.append({"step": where, "code": "bad-effect",
                       "message": "effect count must be a whole number"})
    if kind in ("text-present", "text-absent") \
            and not effect.get("text"):
        errors.append({"step": where, "code": "bad-effect",
                       "message": "effect text is required"})
    return errors


def validate_definition(definition: Mapping[str, Any]) -> List[Dict[str, str]]:
    """Validate a studio definition. Returns errors (empty when valid).

    Detects missing inputs, bad selectors, unreachable steps (anything
    after a terminal ``verify-state``), unknown variable references,
    out-of-range timeouts/attempts, and contradictory verifications
    (same text expected present and absent; same selector counted
    with disjoint exact values).
    """
    errors: List[Dict[str, str]] = []
    if not isinstance(definition, Mapping):
        return [{"step": "", "code": "bad-definition",
                 "message": "definition must be an object"}]
    environment = definition.get("environment")
    if environment not in ENVIRONMENTS:
        errors.append({"step": "", "code": "bad-environment",
                       "message": f"environment must be one of "
                                  f"{list(ENVIRONMENTS)}"})
        environment = "demo"
    names = set()
    for var in definition.get("variables", []) or []:
        if not isinstance(var, dict) or not var.get("name"):
            errors.append({"step": "", "code": "bad-variable",
                           "message": "every variable needs a name"})
            continue
        name = str(var["name"])
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            errors.append({"step": "", "code": "bad-variable",
                           "message": f"invalid variable name {name!r}"})
        if name in names:
            errors.append({"step": "", "code": "bad-variable",
                           "message": f"duplicate variable {name!r}"})
        names.add(name)
        if var.get("secret") and var.get("default") not in (None, ""):
            errors.append({"step": "", "code": "bad-variable",
                           "message": f"secret {name!r} must not carry a "
                                      "persisted default"})
    steps = definition.get("steps", [])
    if not isinstance(steps, list) or not steps:
        errors.append({"step": "", "code": "no-steps",
                       "message": "at least one step is required"})
        return errors
    if len(steps) > MAX_STEPS:
        errors.append({"step": "", "code": "too-many-steps",
                       "message": f"at most {MAX_STEPS} steps"})
    seen_keys = set()
    terminal_at = None
    text_expects: Dict[str, set] = {}
    count_expects: Dict[str, set] = {}
    for order, step in enumerate(steps, start=1):
        where = f"step {order}"
        if not isinstance(step, dict):
            errors.append({"step": where, "code": "bad-step",
                           "message": "step must be an object"})
            continue
        key = str(step.get("key") or f"s{order}")
        where = f"{where} ({key})"
        if key in seen_keys:
            errors.append({"step": where, "code": "duplicate-key",
                           "message": f"duplicate step key {key!r}"})
        seen_keys.add(key)
        kind = step.get("type")
        if kind not in STEP_TYPES:
            errors.append({"step": where, "code": "bad-type",
                           "message": f"unknown step type {kind!r}"})
            continue
        if kind == "verify-state":
            terminal_at = order
        timeout = step.get("timeout_ms", DEFAULT_TIMEOUT_MS)
        if isinstance(timeout, bool) or not isinstance(timeout, int) \
                or not MIN_TIMEOUT_MS <= timeout <= MAX_TIMEOUT_MS:
            errors.append({"step": where, "code": "bad-timeout",
                           "message": f"timeout_ms must be "
                                      f"{MIN_TIMEOUT_MS}..{MAX_TIMEOUT_MS}"})
        attempts = step.get("max_attempts", DEFAULT_CHIMERA_ATTEMPTS)
        if isinstance(attempts, bool) or not isinstance(attempts, int) \
                or not MIN_ATTEMPTS <= attempts <= MAX_ATTEMPTS:
            errors.append({"step": where, "code": "bad-attempts",
                           "message": f"max_attempts must be "
                                      f"{MIN_ATTEMPTS}..{MAX_ATTEMPTS}"})
        if kind == "navigate":
            problem = _check_url(step.get("url"), environment)
            if problem:
                errors.append({"step": where, "code": "bad-url",
                               "message": problem})
        if kind in ("click", "fill", "select", "verify-count"):
            problem = check_selector(step.get("selector"))
            if problem:
                errors.append({"step": where, "code": "bad-selector",
                               "message": problem})
        if kind in ("fill", "select") and step.get("value") is None:
            errors.append({"step": where, "code": "missing-value",
                           "message": "value is required"})
        if kind == "wait":
            condition = step.get("condition")
            if condition not in ("visible", "hidden", "text-present"):
                errors.append({"step": where, "code": "bad-condition",
                               "message": f"unknown wait condition "
                                          f"{condition!r}"})
            elif condition in ("visible", "hidden"):
                problem = check_selector(step.get("selector"))
                if problem:
                    errors.append({"step": where, "code": "bad-selector",
                                   "message": problem})
            elif not step.get("text"):
                errors.append({"step": where, "code": "missing-text",
                               "message": "text is required"})
        if kind == "verify-text":
            if not step.get("text"):
                errors.append({"step": where, "code": "missing-text",
                               "message": "text is required"})
            if step.get("expect", "present") not in ("present", "absent"):
                errors.append({"step": where, "code": "bad-expect",
                               "message": "expect must be present|absent"})
            else:
                text_expects.setdefault(
                    str(step.get("text")), set()).add(
                        step.get("expect", "present"))
            if step.get("selector"):
                problem = check_selector(step.get("selector"))
                if problem:
                    errors.append({"step": where, "code": "bad-selector",
                                   "message": problem})
        if kind == "verify-count":
            count = step.get("count")
            if isinstance(count, bool) or not isinstance(count, int) \
                    or count < 0:
                errors.append({"step": where, "code": "bad-count",
                               "message": "count must be a number >= 0"})
            if step.get("op", "eq") not in ("eq", "gte", "lte"):
                errors.append({"step": where, "code": "bad-op",
                               "message": "op must be eq|gte|lte"})
            elif count_expects is not None and isinstance(count, int) \
                    and step.get("op", "eq") == "eq":
                count_expects.setdefault(
                    str(step.get("selector")), set()).add(count)
        if kind == "verify-state":
            assertions = step.get("assertions")
            if not isinstance(assertions, list) or not assertions:
                errors.append({"step": where, "code": "missing-assertions",
                               "message": "at least one assertion "
                                          "is required"})
            else:
                for assertion in assertions:
                    errors.extend(_check_effect(assertion, where))
                    if isinstance(assertion, dict):
                        for field in ("selector", "text"):
                            for ref in referenced_variables(
                                    assertion.get(field)):
                                if ref not in names:
                                    errors.append({
                                        "step": where,
                                        "code": "unknown-variable",
                                        "message": f"unknown variable "
                                                   f"{{{{{ref}}}}}"})
        if kind in ("click", "fill", "select"):
            errors.extend(_check_effect(step.get("effect"), where))
            for extra in (step.get("effect"), step.get("precondition")):
                if isinstance(extra, dict):
                    for field in ("selector", "text"):
                        for ref in referenced_variables(
                                extra.get(field)):
                            if ref not in names:
                                errors.append({
                                    "step": where,
                                    "code": "unknown-variable",
                                    "message": f"unknown variable "
                                               f"{{{{{ref}}}}}"})
            precondition = step.get("precondition")
            if precondition is not None:
                if not isinstance(precondition, dict) or \
                        precondition.get("kind") not in ("visible",
                                                         "hidden"):
                    errors.append({"step": where, "code": "bad-precondition",
                                   "message": "precondition kind must be "
                                              "visible|hidden"})
                else:
                    problem = check_selector(
                        precondition.get("selector"))
                    if problem:
                        errors.append({"step": where,
                                       "code": "bad-precondition",
                                       "message": problem})
        for field in _TEXTISH_FIELDS:
            for ref in referenced_variables(step.get(field)):
                if ref not in names:
                    errors.append({"step": where, "code": "unknown-variable",
                                   "message": f"unknown variable "
                                              f"{{{{{ref}}}}}"})
    if terminal_at is not None and terminal_at != len(steps):
        errors.append({"step": f"step {terminal_at + 1}",
                       "code": "unreachable-step",
                       "message": "verify-state is terminal: steps after "
                                  "it never run"})
    for text, expects in text_expects.items():
        if expects == {"present", "absent"}:
            errors.append({"step": "", "code": "contradiction",
                           "message": f"text {text!r} expected both "
                                      "present and absent"})
    for selector, counts in count_expects.items():
        if len(counts) > 1:
            errors.append({"step": "", "code": "contradiction",
                           "message": f"selector {selector!r} counted with "
                                      f"disjoint values {sorted(counts)}"})
    return errors


def validate_env_params(env_params: Any) -> List[str]:
    """Validate workflow-level environment parameters."""
    if env_params is None:
        return []
    if not isinstance(env_params, dict):
        return ["env_params must be an object"]
    errors = []
    slow = env_params.get("slow_ms", 0)
    if isinstance(slow, bool) or not isinstance(slow, int) \
            or not 0 <= slow <= 30000:
        errors.append("slow_ms must be 0..30000")
    if not isinstance(env_params.get("disabled", False), bool):
        errors.append("disabled must be true/false")
    unknown = set(env_params) - {"slow_ms", "disabled"}
    if unknown:
        errors.append(f"unknown env_params: {sorted(unknown)}")
    return errors


# ---------------------------------------------------------------------------
# Steps file + independent verifier
# ---------------------------------------------------------------------------


def steps_path_for(trace_dir: Path, run_id: str) -> Path:
    return Path(trace_dir) / f"{run_id}{STEPS_SUFFIX}"


def write_steps(trace_dir: Path, run_id: str,
                records: List[Dict[str, Any]]) -> str:
    path = steps_path_for(trace_dir, run_id)
    payload = {"run_id": run_id, "steps": records}
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)
    return str(path)


def steps_path_for_trace(trace_path: Optional[str]) -> Optional[str]:
    if not trace_path:
        return None
    stem = str(trace_path)
    if stem.endswith(".replay.json"):
        stem = stem[: -len(".replay.json")]
    elif stem.endswith(".json"):
        stem = stem[: -len(".json")]
    else:
        return None
    return stem + STEPS_SUFFIX


def steps_for_trace(trace_path: Optional[str]) -> List[Dict[str, Any]]:
    path = steps_path_for_trace(trace_path)
    if not path:
        return []
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    steps = doc.get("steps")
    return steps if isinstance(steps, list) else []


def check_id_for(order: int, kind: str) -> str:
    return f"{order:02d}-{kind}"


def verify_studio_run(snapshot: Optional[Dict[str, Any]],
                      records: List[Dict[str, Any]],
                      expected: Mapping[str, Any]
                      ) -> Dict[str, Any]:
    """Judge a studio run from its persisted step records.

    ``expected`` carries the definition's ordered steps (key, order,
    type, label). Each step becomes one check; steps without a
    record (flow stopped early) are unavailable with an explicit
    reason — never silently satisfied or failed. ``unavailable``
    only when no step evidence exists at all.
    """
    checks: List[Dict[str, Any]] = []
    by_order = {r.get("order"): r for r in records
                if isinstance(r, dict)}
    for spec in expected.get("steps", []) or []:
        order = spec.get("order")
        check_id = check_id_for(order, spec.get("type", "?"))
        record = by_order.get(order)
        if not isinstance(record, dict):
            checks.append({
                "check_id": check_id,
                "satisfied": None,
                "detail": (f"step {order} "
                           f"({spec.get('label') or spec.get('type')}) "
                           f"has no record: flow stopped before it ran"),
            })
            continue
        satisfied = record.get("satisfied")
        if satisfied is True:
            ok: Optional[bool] = True
        elif satisfied is False:
            ok = False
        else:
            ok = None
        detail = record.get("detail") or record.get("status") or "no detail"
        checks.append({"check_id": check_id, "satisfied": ok,
                       "detail": str(detail)[:300]})
    if not checks:
        return {"status": "unavailable", "checks": []}
    if not records and not isinstance(snapshot, dict):
        return {"status": "unavailable", "checks": checks}
    return {"status": "verified", "checks": checks}


# ---------------------------------------------------------------------------
# Observer policy
# ---------------------------------------------------------------------------


def build_policy(definition: Mapping[str, Any]):
    """Observer policy from the definition's own declared targets.

    Only urls, fills, clicks, and selects the workflow declares are
    permitted; anything else the driver does is judged denied. Reads
    are permitted by type.
    """
    from benchmarks.observer import ActionPolicy

    from chimera.agent import get_contact_url, get_demo_url

    environment = definition.get("environment")
    if environment == "saucedemo":
        urls: List[str] = list(sauce_adapter.SAUCE_URLS)
    else:
        urls = [get_demo_url(), get_contact_url()]
        slow = (definition.get("env_params") or {}).get("slow_ms") or 0
        disabled = (definition.get("env_params") or {}).get(
            "disabled", False)
        if slow or disabled:
            from chimera.agent import get_demo_url_with_faults

            urls.append(get_demo_url_with_faults(
                slow_ms=int(slow), disabled=bool(disabled)))
    fills, clicks, selects = [], [], []
    for step in definition.get("steps", []) or []:
        target = {"by": "css", "selector": step.get("selector", "")}
        if step.get("type") == "fill":
            fills.append(target)
        elif step.get("type") == "click":
            clicks.append(target)
        elif step.get("type") == "select":
            selects.append(target)
    return ActionPolicy(
        permitted_urls=tuple(urls),
        permitted_fill_targets=tuple(fills),
        permitted_click_targets=tuple(clicks),
        permitted_select_targets=tuple(selects),
    )


# ---------------------------------------------------------------------------
# Page observation primitives (shared by both drivers)
# ---------------------------------------------------------------------------


def _safe_url(page: Any) -> str:
    try:
        url = page.url
    except Exception:  # noqa: BLE001 — duck-typed property
        return ""
    return url if isinstance(url, str) else ""


def _count_of(page: Any, selector: str) -> int:
    return int(page.locator(selector).count())


def _visible_of(page: Any, selector: str) -> bool:
    locator = page.locator(selector)
    if locator.count() == 0:
        return False
    try:
        return bool(locator.first.is_visible())
    except Exception:  # noqa: BLE001 — treat unreadable as hidden
        return False


def _texts_of(page: Any, selector: str) -> List[str]:
    locator = page.locator(selector)
    if locator.count() == 0:
        return []
    try:
        return list(locator.all_text_contents())
    except Exception:  # noqa: BLE001 — treat unreadable as absent
        return []


def _value_of(page: Any, selector: str) -> str:
    return str(page.locator(selector).first.input_value())


def read_condition(page: Any, kind: str, selector: str = "",
                   text: str = "", count: int = 0, op: str = "eq",
                   value: str = "") -> Tuple[bool, str]:
    """Evaluate one state predicate. Returns (satisfied, observed)."""
    if kind == "visible":
        seen = _visible_of(page, selector)
        return seen, f"visible={str(seen).lower()}"
    if kind == "hidden":
        seen = _visible_of(page, selector)
        return not seen, f"visible={str(seen).lower()}"
    if kind in ("text-present", "text-absent"):
        haystack = " ".join(_texts_of(page, selector or "body"))
        found = text in haystack
        ok = found if kind == "text-present" else not found
        return ok, f"text {'found' if found else 'absent'}"
    if kind == "count":
        seen = _count_of(page, selector)
        if op == "gte":
            ok = seen >= count
        elif op == "lte":
            ok = seen <= count
        else:
            ok = seen == count
        return ok, f"count={seen} expected {op} {count}"
    if kind == "value":
        seen = _value_of(page, selector)
        return seen == value, "value matches" if seen == value \
            else "value differs"
    raise StudioStepError("bad-condition", f"unknown condition {kind!r}")


def read_effect(page: Any, effect: Mapping[str, Any]) -> Tuple[bool, str]:
    """Evaluate an effect/precondition object. May raise on hard reads."""
    kind = effect.get("kind", "")
    return read_condition(
        page, kind, selector=str(effect.get("selector") or ""),
        text=str(effect.get("text") or ""),
        count=int(effect.get("count") or 0),
        op=str(effect.get("op") or "eq"))


def _poll_until(page: Any, kind: str, selector: str, text: str,
                timeout_ms: int, token: Any) -> Tuple[bool, str]:
    """Poll a wait condition until met, timed out, or cancelled."""
    deadline = time.monotonic() + max(0, timeout_ms) / 1000
    observed = ""
    while True:
        if token is not None:
            token.check()
        try:
            ok, observed = read_condition(
                page, kind, selector=selector, text=text)
        except Exception:  # noqa: BLE001 — failed reads mean "not yet"
            ok, observed = False, "unreadable"
        if ok:
            return True, observed
        if time.monotonic() >= deadline:
            return False, observed
        time.sleep(0.1)


def _confirm(reader: Callable[[], Tuple[bool, str]],
             timeout_ms: int, token: Any) -> Tuple[bool, str]:
    """Poll a post-act confirmation until it holds or times out.

    Read-only settling (both drivers): acting and observing are
    distinct — the step's timeout bounds how long the driver gives
    the page to reach the confirmed state. Unreadable polls count
    as "not yet", so a failed confirmation reports the last
    observed state rather than a read error.
    """
    deadline = time.monotonic() + max(0, timeout_ms) / 1000
    ok, observed = False, "unreadable"
    while True:
        if token is not None:
            token.check()
        try:
            ok, observed = reader()
        except Exception:  # noqa: BLE001 — failed reads mean "not yet"
            ok, observed = False, "unreadable"
        if ok:
            return True, observed
        if time.monotonic() >= deadline:
            return False, observed
        time.sleep(0.1)


def _resolve_navigate_url(url: str, environment: str,
                           env_params: Optional[Mapping[str, Any]] = None,
                           ) -> str:
    if environment == "saucedemo":
        if url.startswith("/"):
            return sauce_adapter.APPROVED_ORIGIN + url
        return url
    from chimera.agent import (CONTACT_APP_PATH, DEMO_APP_PATH,
                               get_contact_url, get_demo_url)

    params = env_params or {}
    slow = int(params.get("slow_ms") or 0)
    disabled = bool(params.get("disabled", False))
    if url == "demo" and (slow or disabled):
        from chimera.agent import get_demo_url_with_faults

        return get_demo_url_with_faults(slow_ms=slow,
                                        disabled=disabled)
    if url in ("demo", "contact"):
        return get_demo_url() if url == "demo" else get_contact_url()
    if url.startswith("file://"):
        return url
    if url.startswith("/"):
        demo_dir = DEMO_APP_PATH.parent
        target = (demo_dir / url.lstrip("/")).resolve()
        if target == DEMO_APP_PATH.resolve() \
                or target == CONTACT_APP_PATH.resolve():
            return f"file://{target}"
    return url


def _assert_demo_url(url: str) -> str:
    """Fail closed unless the RENDERED URL is exactly a bundled page.

    Runtime counterpart of :func:`_check_url`: variable-rendered
    navigate URLs bypass static validation, so the rendered value is
    re-checked here, right before ``page.goto``. Only the two
    bundled files are allowed; query strings (fault injection) and
    fragments are ignored, and ``..`` segments are resolved before
    comparing, so ``file://`` escapes cannot smuggle other paths.
    """
    from urllib.parse import unquote, urlsplit

    from chimera.agent import CONTACT_APP_PATH, DEMO_APP_PATH

    def _refuse() -> None:
        raise StudioStepError(
            "bad-url",
            "demo workflows may only open the bundled pages, "
            f"got {url!r}")

    try:
        parts = urlsplit(url or "")
    except Exception:  # noqa: BLE001 — fail closed
        _refuse()
    if parts.scheme != "file" or parts.netloc not in ("", "localhost"):
        _refuse()
    try:
        target = Path(unquote(parts.path)).resolve()
    except Exception:  # noqa: BLE001 — fail closed
        _refuse()
    allowed = {DEMO_APP_PATH.resolve(), CONTACT_APP_PATH.resolve()}
    if target not in allowed:
        _refuse()
    return url


# ---------------------------------------------------------------------------
# Attempt engine
# ---------------------------------------------------------------------------


def _attempt_record(number: int, started: float, **fields: Any
                    ) -> Dict[str, Any]:
    record = {"n": number,
              "started_at": datetime.now(timezone.utc).isoformat(
                  timespec="milliseconds"),
              "duration_ms": int((time.monotonic() - started) * 1000)}
    record.update(fields)
    return record


def _act(page: Any, step: Mapping[str, Any], rendered: Dict[str, str],
         timeout_ms: int, environment: str,
         env_params: Optional[Mapping[str, Any]] = None) -> str:
    """Perform the step's action once. Returns an observed summary."""
    kind = step["type"]
    selector = rendered.get("selector", "")
    if kind == "navigate":
        url = _resolve_navigate_url(rendered.get("url", ""), environment,
                                     env_params)
        if environment == "saucedemo":
            sauce_adapter.assert_approved_url(url)
        else:
            _assert_demo_url(url)
        page.goto(url)
        return f"url={_safe_url(page)}"
    if kind == "click":
        page.locator(selector).click(timeout=timeout_ms)
        return "clicked"
    if kind == "fill":
        page.locator(selector).fill(rendered.get("value", ""),
                                    timeout=timeout_ms)
        return "filled"
    if kind == "select":
        page.locator(selector).select_option(rendered.get("value", ""),
                                             timeout=timeout_ms)
        return "selected"
    raise StudioStepError("bad-step", f"{kind} steps perform no action")


def _postcondition(page: Any, step: Mapping[str, Any],
                   rendered: Dict[str, str], environment: str,
                   env_params: Optional[Mapping[str, Any]] = None,
                   ) -> Tuple[bool, str]:
    """Evaluate the step's built-in postcondition after acting."""
    kind = step["type"]
    if kind == "navigate":
        want = _resolve_navigate_url(rendered.get("url", ""), environment,
                                      env_params)
        got = _safe_url(page)
        return got == want, f"url={got}"
    if kind in ("fill", "select"):
        return read_condition(page, "value",
                              selector=rendered.get("selector", ""),
                              value=rendered.get("value", ""))
    return True, "action completed"


def _render_step(step: Mapping[str, Any],
                 values: Mapping[str, str]) -> Dict[str, str]:
    return {field: substitute(step.get(field, ""), values)
            for field in ("url", "selector", "value", "text")}


def _render_effect(effect: Mapping[str, Any],
                   values: Mapping[str, str]) -> Dict[str, Any]:
    rendered = dict(effect)
    for field in ("selector", "text"):
        if field in rendered:
            rendered[field] = substitute(rendered[field], values)
    return rendered


def run_step_chimera(page: Any, step: Mapping[str, Any], order: int,
                     values: Mapping[str, str], secrets: List[str],
                     environment: str, token: Any,
                     screenshots_dir: Optional[Path] = None,
                     run_id: str = "",
                     env_params: Optional[Mapping[str, Any]] = None,
                     ) -> Dict[str, Any]:
    """Run one step with evidence-based recovery (Chimera driver).

    Recovery rules: the effect (when declared) is read before the
    first attempt — an already-satisfied effect skips the action
    entirely. Non-idempotent steps without an observable effect get
    exactly one attempt; further retries are refused rather than
    repeated blindly. Idempotent steps retry to ``max_attempts``.
    """
    timeout_ms = int(step.get("timeout_ms", DEFAULT_TIMEOUT_MS))
    max_attempts = int(step.get("max_attempts",
                                DEFAULT_CHIMERA_ATTEMPTS))
    idempotent = bool(step.get("idempotent",
                               DEFAULT_IDEMPOTENT[step["type"]]))
    rendered = _render_step(step, values)
    effect = step.get("effect")
    attempts: List[Dict[str, Any]] = []
    evidence: List[Dict[str, str]] = []
    record: Dict[str, Any] = {
        "key": step.get("key", f"s{order}"), "order": order,
        "type": step["type"], "label": step.get("label", ""),
        "idempotent": idempotent, "attempts": attempts,
        "evidence": evidence,
    }

    def _fail(code: str, detail: str) -> Dict[str, Any]:
        record.update(status="failed", satisfied=False,
                      detail=redact(detail, secrets))
        return record

    def _pass(detail: str) -> Dict[str, Any]:
        record.update(status="passed", satisfied=True,
                      detail=redact(detail, secrets))
        return record

    kind = step["type"]
    if kind in ("wait", "verify-text", "verify-count", "capture",
                "verify-state"):
        return _run_read_step(page, step, order, rendered, values,
                              record, attempts, evidence, secrets,
                              token, screenshots_dir, run_id,
                              poll=True)
    # -- action steps -------------------------------------------------
    precondition = step.get("precondition")
    if precondition:
        try:
            ok, observed = read_effect(
                page, _render_effect(precondition, values))
        except Exception as exc:  # noqa: BLE001 — fail closed
            return _fail("precondition-unreadable",
                         f"precondition unreadable: {exc}")
        if not ok:
            return _fail("precondition-failed",
                         f"precondition not met: {observed}")
    if effect:
        effect = _render_effect(effect, values)
        try:
            already, observed = read_effect(page, effect)
        except Exception as exc:  # noqa: BLE001 — fail closed
            return _fail("effect-unreadable",
                         f"effect unreadable before acting: {exc}")
        if already:
            attempts.append(_attempt_record(
                1, time.monotonic(), skipped=True,
                reason="effect already satisfied",
                observation=redact(observed, secrets)))
            return _pass(f"already satisfied: {observed}")
    attempt = 0
    while True:
        if token is not None:
            token.check()
        attempt += 1
        if attempt > 1:
            if not idempotent and not effect:
                attempts.append(_attempt_record(
                    attempt, time.monotonic(), skipped=True,
                    reason=("retry refused: non-idempotent step without "
                            "an observable effect"),
                    retry_refused=True))
                return _fail(
                    "retry-refused",
                    attempts[-2].get("error", "action failed"))
            if effect:
                try:
                    done, observed = read_effect(page, effect)
                except Exception as exc:  # noqa: BLE001 — fail closed
                    return _fail("unsafe-retry-refused",
                                 f"effect unreadable before retry: {exc}")
                if done:
                    attempts.append(_attempt_record(
                        attempt, time.monotonic(), skipped=True,
                        reason="effect satisfied before retry",
                        observation=redact(observed, secrets)))
                    return _pass(f"recovered: {observed}")
            delay = min(0.1 * (2 ** (attempt - 2)), 1.0)
            if delay > 0:
                time.sleep(delay)
        started = time.monotonic()
        try:
            summary = _act(page, step, rendered, timeout_ms, environment,
                            env_params)
        except Exception as exc:  # noqa: BLE001 — attempt outcome
            attempts.append(_attempt_record(
                attempt, started, error=redact(
                    f"{type(exc).__name__}: {exc}", secrets)))
            if attempt >= max_attempts:
                return _fail("action-failed",
                             attempts[-1]["error"])
            continue
        if effect:
            reader = lambda: read_effect(page, effect)  # noqa: E731
        else:
            reader = lambda: _postcondition(  # noqa: E731
                page, step, rendered, environment, env_params)
        ok, observed = _confirm(reader, timeout_ms, token)
        attempts.append(_attempt_record(
            attempt, started, action=redact(summary, secrets),
            observation=redact(observed, secrets)))
        if ok:
            return _pass(observed)
        if attempt >= max_attempts:
            return _fail("postcondition-failed", observed)


def _run_read_step(page: Any, step: Mapping[str, Any], order: int,
                   rendered: Dict[str, str], values: Mapping[str, str],
                   record: Dict[str, Any],
                   attempts: List[Dict[str, Any]],
                   evidence: List[Dict[str, str]], secrets: List[str],
                   token: Any, screenshots_dir: Optional[Path],
                   run_id: str, poll: bool) -> Dict[str, Any]:
    """Run a read-only step.

    ``poll`` (Chimera) asserts eventually within the timeout;
    without it (replay) the step reads exactly once.
    """
    kind = step["type"]
    timeout_ms = int(step.get("timeout_ms", DEFAULT_TIMEOUT_MS))
    started = time.monotonic()
    if kind == "wait":
        condition = step.get("condition", "visible")
        selector = rendered.get("selector", "") if condition != \
            "text-present" else "body"
        ok, observed = _poll_until(page, condition, selector,
                                   rendered.get("text", ""), timeout_ms,
                                   token)
        attempts.append(_attempt_record(
            1, started, observation=redact(observed, secrets)))
        record.update(status="passed" if ok else "failed",
                      satisfied=ok,
                      detail=redact(observed if ok else
                                    f"timed out after {timeout_ms}ms: "
                                    f"{observed}", secrets))
        return record
    if kind == "capture":
        name = f"{run_id}_s{order:02d}.png" if run_id else f"s{order}.png"
        try:
            target = Path(screenshots_dir) if screenshots_dir else Path(".")
            target.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(target / name))
        except Exception as exc:  # noqa: BLE001 — capture is the contract
            attempts.append(_attempt_record(
                1, started,
                error=f"{type(exc).__name__}: {exc}"))
            record.update(status="failed", satisfied=False,
                          detail=f"capture failed: {exc}")
            return record
        attempts.append(_attempt_record(1, started))
        evidence.append({"kind": "screenshot", "ref": name})
        record.update(status="passed", satisfied=True,
                      detail=f"captured {name}")
        return record
    if kind == "verify-state":
        rendered_assertions = [{
            **assertion,
            "text": substitute(assertion.get("text", ""), values),
            "selector": substitute(assertion.get("selector", ""),
                                    values),
        } for assertion in step.get("assertions", []) or []]

        def _all_hold() -> Tuple[bool, str]:
            failures = []
            for assertion in rendered_assertions:
                ok, observed = read_effect(page, assertion)
                if not ok:
                    failures.append(observed)
            if failures:
                return False, "; ".join(failures)[:300]
            return True, (f"{len(rendered_assertions)} "
                          f"assertions hold")

        if poll:
            ok, observed = _confirm(_all_hold, timeout_ms, token)
            failures = [] if ok else [observed]
        else:
            try:
                ok, observed = _all_hold()
            except Exception as exc:  # noqa: BLE001 — fail closed
                ok, observed = False, f"unreadable: {exc}"
            failures = [] if ok else [observed]
        attempts.append(_attempt_record(1, started))
        if failures:
            record.update(status="failed", satisfied=False,
                          detail="; ".join(failures)[:300])
        else:
            record.update(status="passed", satisfied=True,
                          detail=(f"{len(step.get('assertions', []))} "
                                  f"assertions hold"))
        return record
    # verify-text / verify-count: assert (eventually when polling).
    if kind == "verify-text":
        reader = lambda: read_condition(  # noqa: E731
            page, "text-present"
            if step.get("expect", "present") == "present"
            else "text-absent",
            selector=rendered.get("selector", ""),
            text=rendered.get("text", ""))
    else:
        reader = lambda: read_condition(  # noqa: E731
            page, "count", selector=rendered.get("selector", ""),
            count=int(step.get("count", 0)),
            op=str(step.get("op", "eq")))
    if poll:
        ok, observed = _confirm(reader, timeout_ms, token)
    else:
        try:
            ok, observed = reader()
        except Exception as exc:  # noqa: BLE001 — fail closed
            attempts.append(_attempt_record(
                1, started, error=f"{type(exc).__name__}: {exc}"))
            record.update(status="failed", satisfied=False,
                          detail=f"verification unreadable: {exc}")
            return record
    attempts.append(_attempt_record(
        1, started, observation=redact(observed, secrets)))
    record.update(status="passed" if ok else "failed", satisfied=ok,
                  detail=redact(observed, secrets))
    return record


def run_step_replay(page: Any, step: Mapping[str, Any], order: int,
                    values: Mapping[str, str], secrets: List[str],
                    environment: str, token: Any,
                    screenshots_dir: Optional[Path] = None,
                    run_id: str = "",
                    env_params: Optional[Mapping[str, Any]] = None,
                    ) -> Dict[str, Any]:
    """Run one step with no recovery (Baseline A driver).

    Exactly one attempt per step. Post-act confirmations poll like
    Chimera (read-only settling after acting); standalone reads —
    waits and verifications — read exactly once: replay never waits
    out a transient state it did not just cause.
    """
    kind = step["type"]
    rendered = _render_step(step, values)
    attempts: List[Dict[str, Any]] = []
    evidence: List[Dict[str, str]] = []
    record: Dict[str, Any] = {
        "key": step.get("key", f"s{order}"), "order": order,
        "type": kind, "label": step.get("label", ""),
        "idempotent": bool(step.get(
            "idempotent", DEFAULT_IDEMPOTENT[kind])),
        "attempts": attempts, "evidence": evidence,
    }

    def _fail(code: str, detail: str) -> Dict[str, Any]:
        record.update(status="failed", satisfied=False,
                      detail=redact(detail, secrets))
        return record

    def _pass(detail: str) -> Dict[str, Any]:
        record.update(status="passed", satisfied=True,
                      detail=redact(detail, secrets))
        return record

    if token is not None:
        token.check()
    timeout_ms = int(step.get("timeout_ms", DEFAULT_TIMEOUT_MS))
    if kind == "wait":
        condition = step.get("condition", "visible")
        selector = rendered.get("selector", "") if condition != \
            "text-present" else "body"
        started = time.monotonic()
        try:
            ok, observed = read_condition(
                page, condition, selector=selector,
                text=rendered.get("text", ""))
        except Exception as exc:  # noqa: BLE001 — single read failed
            attempts.append(_attempt_record(
                1, started, error=f"{type(exc).__name__}: {exc}"))
            return _fail("wait-unreadable", attempts[-1]["error"])
        attempts.append(_attempt_record(
            1, started, observation=redact(observed, secrets)))
        if ok:
            return _pass(observed)
        return _fail("wait-not-met",
                     f"condition not met on single read: {observed}")
    if kind in ("verify-text", "verify-count", "capture", "verify-state"):
        return _run_read_step(page, step, order, rendered, values,
                              record, attempts, evidence, secrets,
                              token, screenshots_dir, run_id,
                              poll=False)
    started = time.monotonic()
    try:
        summary = _act(page, step, rendered, timeout_ms, environment,
                        env_params)
    except Exception as exc:  # noqa: BLE001 — the single attempt failed
        attempts.append(_attempt_record(
            1, started, error=redact(f"{type(exc).__name__}: {exc}",
                                     secrets)))
        return _fail("action-failed", attempts[-1]["error"])
    effect = step.get("effect")
    if effect:
        reader = lambda: read_effect(  # noqa: E731
            page, _render_effect(effect, values))
    else:
        reader = lambda: _postcondition(  # noqa: E731
            page, step, rendered, environment, env_params)
    ok, observed = _confirm(reader, timeout_ms, token)
    attempts.append(_attempt_record(
        1, started, action=redact(summary, secrets),
        observation=redact(observed, secrets)))
    if ok:
        return _pass(observed)
    return _fail("postcondition-failed", observed)


# ---------------------------------------------------------------------------
# Drivers
# ---------------------------------------------------------------------------

STUDIO_PREFIX = "studio:"


def studio_workflow_id(workflow_uuid: str) -> str:
    return f"{STUDIO_PREFIX}{workflow_uuid}"


def capture_end_state(page: Any) -> Dict[str, Any]:
    """Final pre-teardown state read (executor observe hook)."""
    try:
        title = page.title()
    except Exception:  # noqa: BLE001 — duck-typed call
        title = ""
    return {"url": _safe_url(page),
            "title": title if isinstance(title, str) else ""}


def _wrap_page(page: Any, log: Any = None) -> Any:
    from benchmarks.observer import ActionLog, RecordingPage

    if isinstance(page, RecordingPage):
        return page
    return RecordingPage(page, log if log is not None
                         else ActionLog(run_id=uuid.uuid4().hex[:8]))


def run_studio_chimera(
    *,
    definition: Mapping[str, Any],
    variables: Mapping[str, Any],
    trace_dir: Path,
    token: Any = None,
    observe: Optional[Callable[[Any], Any]] = None,
    browser_factory: Optional[Callable[..., Any]] = None,
    screenshots_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run a studio definition with recovery (Chimera driver).

    Same result contract as the fixed agent flows: bounded
    attempts, cooperative cancellation, a persisted trace, step
    records, and best-effort failure screenshots. Secrets never
    reach the trace, the steps file, or evidence references.
    """
    from chimera.safety import RunCancelledError
    from chimera.tracing import TraceRecorder

    problems = validate_definition(definition)
    if problems:
        raise StudioError(
            f"invalid definition: {problems[0]['message']}")
    values = resolve_variables(definition, variables)
    secrets = secret_values(definition, values)
    environment = definition.get("environment", "demo")
    env_params = definition.get("env_params") or {}
    steps = list(definition.get("steps", []))
    trace_dir = Path(trace_dir)
    trace_dir.mkdir(parents=True, exist_ok=True)
    shots = Path(screenshots_dir) if screenshots_dir else None

    result: Dict[str, Any] = {
        "success": False, "cancelled": False, "status": "failed",
        "project_name": str(definition.get("name", "studio workflow")),
        "error": None, "trace_path": None, "run_id": None,
    }
    recorder = TraceRecorder(trace_dir=trace_dir)
    result["run_id"] = recorder.run_id
    shown = {k: (REDACTED if v in secrets else v)
             for k, v in values.items()}
    recorder.record("run_started", evidence=[
        f"workflow={definition.get('name', '')}",
        f"environment={environment}",
        f"variables={json.dumps(shown, sort_keys=True)}"])
    records: List[Dict[str, Any]] = []

    def _note(record: Dict[str, Any]) -> None:
        records.append(record)
        write_steps(trace_dir, recorder.run_id, records)
        recorder.record("studio_step", evidence=[
            f"step={record['order']}:{record['type']}",
            f"status={record.get('status')}",
            f"detail={redact(record.get('detail', ''), secrets)}"])

    def _shot(page: Any, order: int) -> None:
        if shots is None:
            return
        try:
            shots.mkdir(parents=True, exist_ok=True)
            page.screenshot(
                path=str(shots / f"{recorder.run_id}_fail{order:02d}.png"))
            recorder.events[-1]["evidence_references"].append(
                f"screenshot={recorder.run_id}_fail{order:02d}.png")
        except Exception:  # noqa: BLE001 — evidence best-effort
            recorder.events[-1]["evidence_references"].append(
                "screenshot_capture_failed")

    def _check_cancel() -> None:
        if token is not None:
            token.check()

    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        if browser_factory is None:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = _wrap_page(context.new_page())
        else:
            browser, context, raw = browser_factory(playwright)
            page = _wrap_page(raw)
        try:
            for order, step in enumerate(steps, start=1):
                _check_cancel()
                kind = step["type"]
                recorder.action_attempted(kind)
                try:
                    record = run_step_chimera(
                        page, step, order, values, secrets,
                        environment, token,
                        screenshots_dir=shots,
                        run_id=recorder.run_id,
                        env_params=env_params)
                except RunCancelledError:
                    raise
                except Exception as exc:  # noqa: BLE001 — step outcome
                    recorder.action_failed(kind, exc)
                    record = {
                        "key": step.get("key", f"s{order}"),
                        "order": order, "type": kind,
                        "label": step.get("label", ""),
                        "attempts": [], "evidence": [],
                        "status": "failed", "satisfied": False,
                        "detail": redact(f"{type(exc).__name__}: {exc}",
                                         secrets),
                    }
                    _note(record)
                    _shot(page, order)
                    result["error"] = (
                        f"StudioStepError[{kind}]: {record['detail']}")
                    break
                if record.get("satisfied") is True:
                    recorder.action_succeeded(kind)
                    if kind in ("verify-text", "verify-count",
                                "verify-state", "wait"):
                        recorder.verification_passed(
                            check_id_for(order, kind))
                else:
                    recorder.action_failed(
                        kind, StudioStepError(
                            "step-failed",
                            str(record.get("detail", ""))))
                    if kind in ("verify-text", "verify-count",
                                "verify-state", "wait"):
                        recorder.verification_failed(
                            check_id_for(order, kind),
                            StudioStepError(
                                "step-failed",
                                str(record.get("detail", ""))))
                    _shot(page, order)
                _note(record)
                if record.get("satisfied") is not True:
                    result["error"] = (
                        f"StudioStepError[{kind}]: "
                        f"{record.get('detail', '')}")
                    break
            else:
                result["success"] = True
                result["status"] = "succeeded"
            for order, step in enumerate(steps, start=1):
                if order > len(records):
                    records.append({
                        "key": step.get("key", f"s{order}"),
                        "order": order, "type": step["type"],
                        "label": step.get("label", ""),
                        "attempts": [], "evidence": [],
                        "status": "not-run", "satisfied": None,
                        "detail": "flow stopped before this step ran",
                    })
            write_steps(trace_dir, recorder.run_id, records)
        except RunCancelledError as exc:
            result["cancelled"] = True
            result["status"] = "cancelled"
            result["error"] = f"RunCancelledError: {exc}"
        except Exception as exc:  # noqa: BLE001 — driver must not die
            result["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            if observe is not None:
                try:
                    result["observation"] = observe(page)
                    result["observation_error"] = None
                except Exception as exc:  # noqa: BLE001 — reported
                    result["observation"] = None
                    result["observation_error"] = (
                        f"{type(exc).__name__}: {exc}")
            try:
                context.close()
            finally:
                browser.close()
    terminal = ("succeeded" if result["success"]
                else ("cancelled" if result["cancelled"] else "failed"))
    try:
        result["trace_path"] = str(recorder.finish(terminal))
    except Exception as exc:  # noqa: BLE001 — trace failure overrides
        result["success"] = False
        result["status"] = "failed"
        result["cancelled"] = False
        result["error"] = f"TraceWriteError: {exc}"
        result["trace_path"] = None
    return result


def run_studio_replay(
    *,
    definition: Mapping[str, Any],
    variables: Mapping[str, Any],
    trace_dir: Path,
    token: Any = None,
    page_factory: Optional[Callable[[], Any]] = None,
    run_id: Optional[str] = None,
    screenshots_dir: Optional[Path] = None,
):
    """Run a studio definition without recovery (Baseline A driver).

    One attempt per step, no retries, no waits beyond a single
    immediate read. Persists the same ``<run>.steps.json`` contract
    as Chimera plus a minimal driver report, so the same verifier
    judges both drivers.
    """
    from benchmarks.baseline_a import ReplayOutcome, replay_path_for
    from benchmarks.observer import (ActionLog, RecordingPage,
                                     actions_path_for, judge_log)
    from chimera.safety import RunCancelledError

    problems = validate_definition(definition)
    if problems:
        raise StudioError(
            f"invalid definition: {problems[0]['message']}")
    values = resolve_variables(definition, variables)
    secrets = secret_values(definition, values)
    environment = definition.get("environment", "demo")
    env_params = definition.get("env_params") or {}
    steps = list(definition.get("steps", []))
    trace_dir = Path(trace_dir)
    trace_dir.mkdir(parents=True, exist_ok=True)
    shots = Path(screenshots_dir) if screenshots_dir else None
    run_id = run_id or uuid.uuid4().hex
    started_at = datetime.now(timezone.utc).isoformat(
        timespec="milliseconds")
    log = ActionLog(run_id=run_id)
    records: List[Dict[str, Any]] = []
    terminal = "succeeded"
    error: Optional[str] = None

    def _check_cancel() -> None:
        if token is not None:
            token.check()

    if page_factory is None:
        from playwright.sync_api import sync_playwright

        playwright_context = sync_playwright()
        playwright = playwright_context.__enter__()
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        raw_page = context.new_page()
        owned = True
    else:
        playwright_context = None
        browser, context, raw_page = page_factory()
        owned = False
    page = raw_page if isinstance(raw_page, RecordingPage) \
        else RecordingPage(raw_page, log)
    try:
        for order, step in enumerate(steps, start=1):
            _check_cancel()
            try:
                record = run_step_replay(
                    page, step, order, values, secrets, environment,
                    token, screenshots_dir=shots, run_id=run_id,
                    env_params=env_params)
            except RunCancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 — step outcome
                record = {
                    "key": step.get("key", f"s{order}"),
                    "order": order, "type": step.get("type", "?"),
                    "label": step.get("label", ""), "attempts": [],
                    "evidence": [], "status": "failed",
                    "satisfied": False,
                    "detail": redact(f"{type(exc).__name__}: {exc}",
                                     secrets),
                }
            records.append(record)
            write_steps(trace_dir, run_id, records)
            if record.get("satisfied") is not True:
                terminal = "failed"
                error = (f"StudioStepError[{record['type']}]: "
                         f"{record.get('detail', '')}")
                break
        for order, step in enumerate(steps, start=1):
            if order > len(records):
                records.append({
                    "key": step.get("key", f"s{order}"),
                    "order": order, "type": step.get("type", "?"),
                    "label": step.get("label", ""), "attempts": [],
                    "evidence": [], "status": "not-run",
                    "satisfied": None,
                    "detail": "flow stopped before this step ran",
                })
        write_steps(trace_dir, run_id, records)
    except RunCancelledError as exc:
        terminal = "cancelled"
        error = f"RunCancelledError: {exc}"
    finally:
        try:
            end_state = capture_end_state(page)
            observation_error = None
        except Exception as exc:  # noqa: BLE001 — reported, not fatal
            end_state = None
            observation_error = f"{type(exc).__name__}: {exc}"
        try:
            context.close()
        finally:
            browser.close()
            if owned and playwright_context is not None:
                playwright_context.__exit__(None, None, None)
    completed_at = datetime.now(timezone.utc).isoformat(
        timespec="milliseconds")
    report = {
        "schema": STUDIO_REPORT_SCHEMA,
        "report_id": run_id,
        "terminal_status": terminal,
        "error": error,
        "workflow": str(definition.get("name", "")),
        "environment": environment,
        "steps": [{"key": r.get("key"), "order": r.get("order"),
                   "type": r.get("type"),
                   "status": r.get("status")} for r in records],
        "started_at": started_at,
        "completed_at": completed_at,
    }
    report_path = replay_path_for(trace_dir, run_id)
    report_tmp = report_path.with_suffix(report_path.suffix + ".tmp")
    report_tmp.write_text(json.dumps(report, sort_keys=True,
                                     ensure_ascii=False) + "\n",
                          encoding="utf-8")
    report_tmp.replace(report_path)
    judged = judge_log(log, build_policy(definition))
    actions_path = actions_path_for(trace_dir, run_id)
    actions_tmp = actions_path.with_suffix(actions_path.suffix + ".tmp")
    actions_tmp.write_text(judged.to_json(), encoding="utf-8")
    actions_tmp.replace(actions_path)
    snapshot = None
    if isinstance(end_state, dict):
        snapshot = {**end_state, "run_id": run_id,
                    "captured_at": completed_at}
    return ReplayOutcome(
        run_id=run_id, terminal_status=terminal,
        report_path=str(report_path), snapshot=snapshot,
        snapshot_ref=None, observation_error=observation_error,
        action_log=judged.to_dict(), error=error,
    )