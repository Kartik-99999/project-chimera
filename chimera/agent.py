"""Minimal Playwright automation for Project Chimera."""

import json
import time
from pathlib import Path
from typing import Any, Callable, Optional, Tuple

from chimera.safety import (
    ActionType,
    CancellationToken,
    RetryPolicy,
    RunCancelledError,
    execute_with_retry,
)
from chimera.tracing import (
    TraceRecorder,
    TraceWriteError,
    capture_failure_screenshot,
)
from adapters import saucedemo as sauce_adapter
from adapters import flipkart as flipkart_adapter
from adapters import wikipedia as wiki_adapter
from adapters import wiktionary as wikt_adapter
from adapters import pypi as pypi_adapter
from adapters import bbc as bbc_adapter
from adapters import github as github_adapter
from adapters import crates as crates_adapter
from adapters import weather as weather_adapter
from adapters import github_search as gsearch_adapter
from adapters import steam as steam_adapter
from adapters import arxiv as arxiv_adapter
from adapters import stackoverflow as so_adapter
from adapters import amazon as amazon_adapter


DEMO_APP_PATH = Path(__file__).resolve().parent.parent / "demo_app" / "index.html"
CONTACT_APP_PATH = Path(__file__).resolve().parent.parent / "demo_app" / "contact.html"
PROJECT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_TRACE_DIR = PROJECT_DATA_DIR / "traces"
DEFAULT_SCREENSHOT_DIR = PROJECT_DATA_DIR / "screenshots"

# Conservative policy for a local demo app. Real runs will tighten this.
DEFAULT_POLICY = RetryPolicy(
    max_attempts=2,
    base_delay_seconds=0.05,
    max_delay_seconds=0.2,
    max_total_seconds=5.0,
)

# Per-action timeout, derived from the policy's wall-clock budget so a single
# action cannot outlive it. Without this, Playwright's own 30s default action
# timeout would silently override max_total_seconds, and a persistently
# disabled control would block the run for 30s instead of failing within the
# policy's stated bound.
ACTION_TIMEOUT_MS = int(DEFAULT_POLICY.max_total_seconds * 1000)


def _close_browser(context: Any, browser: Any, trace_dir: Any,
                 run_id: str) -> None:
    """Close the per-run context, then the browser, on this thread.

    Both closes run even when the run failed; the run always
    finishes. Playwright's sync API is bound to the thread that
    created it, so these MUST run on the calling (owning) thread:
    a helper thread raises "Cannot switch to a different thread"
    on every close, which also kills the executor's final-state
    screenshot. A close that raises is written to a
    ``<run_id>.teardown.json`` sidecar next to the trace — the
    trace itself is already sealed by teardown time — and never
    fails the run. A genuinely wedged close is bounded one level
    up by the executor's run watchdog; same discipline as
    ``studio.py`` and ``baseline_a.py``.
    """
    notes = []
    for label, target in (("context", context), ("browser", browser)):
        try:
            target.close()
        except Exception as exc:  # noqa: BLE001 — recorded below
            notes.append(
                f"{label} close failed: {type(exc).__name__}: {exc}")
    if notes:
        try:
            sidecar = Path(trace_dir) / f"{run_id}.teardown.json"
            sidecar.write_text(json.dumps(
                {"run_id": run_id, "notes": notes}, indent=2),
                encoding="utf-8")
        except Exception:  # noqa: BLE001 — teardown note best-effort
            pass


def get_demo_url() -> str:
    """Return a file:// URL for the local demo app (no fault params)."""
    return f"file://{DEMO_APP_PATH}"


def get_demo_url_with_faults(
    *, slow_ms: int = 0, disabled: bool = False
) -> str:
    """Return the demo URL with deterministic fault-injection query params.

    Supported params (read by ``demo_app/index.html`` on load):

    - ``slow=<ms>``     — the form starts disabled for ``<ms>`` milliseconds,
                          then re-enables (simulates a slow page load).
    - ``disabled=1``    — the Create button starts disabled and stays that
                          way until the in-page Reset is pressed.

    When no fault is requested (default), the returned URL is identical
    to :func:`get_demo_url`. This keeps the existing ``create_project``
    workflow bit-for-bit unchanged.
    """
    base = get_demo_url()
    params: list[str] = []
    if slow_ms and slow_ms > 0:
        params.append(f"slow={int(slow_ms)}")
    if disabled:
        params.append("disabled=1")
    if not params:
        return base
    return f"{base}?{'&'.join(params)}"


def create_project(
    project_name: str,
    *,
    url: Optional[str] = None,
    trace_dir: Optional[Path] = None,
    cancel: Optional[CancellationToken] = None,
    observe: Optional[Callable[[Any], Any]] = None,
    browser_factory: Optional[Callable[[Any], Tuple[Any, Any, Any]]] = None,
) -> dict:
    """Open the demo app, create a project, and verify the result.

    Returns a dict with success status and details.
    We verify state explicitly: the confirmation message must be visible
    and the project must appear in the list. Clicking alone is not enough.

    Parameters
    ----------
    project_name:
        Name to enter into the form.
    url:
        Optional override for the demo URL. Defaults to
        :func:`get_demo_url`. Use :func:`get_demo_url_with_faults` to
        inject deterministic faults.
    trace_dir:
        Optional override for the trace artifact directory. Defaults to
        ``<project>/data/traces``. The returned dict gains a
        ``trace_path`` field naming the persisted artifact (or
        ``None`` if writing failed).
    cancel:
        Optional :class:`~chimera.safety.CancellationToken`. When the
        token is cancelled, the run aborts at the next safe execution
        boundary (between actions, between verifications, and inside
        the bounded action's effect check). Cancellation is cooperative
        and does not interrupt an in-flight Playwright call from
        another thread (FR-021).
    observe:
        Optional harness observation callback. When supplied, it is
        called once with the live Playwright page after the workflow
        has settled (on success, failure, or cancellation) and before
        the browser context is closed, so the harness can capture an
        independent state snapshot that would not survive teardown.
        Its return value is reported as ``result["observation"]``; if
        it raises, the error is reported as
        ``result["observation_error"]`` and the run's outcome is
        unchanged. Both keys are present only when ``observe`` is
        supplied. The callback runs on the agent's own thread and must
        not retain the page past teardown.
    browser_factory:
        Optional harness hook replacing browser acquisition. When
        supplied, it is called with the ``sync_playwright`` handle and
        must return ``(browser, context, page)``; the agent closes the
        context and browser exactly as on the default path. The harness
        uses this to hand the agent a recording page proxy for
        independent action observation
        (``docs/benchmark_design.md`` §8.2). When omitted, the agent
        launches its own Chromium, context, and page as before.

    Returns
    -------
    dict
        Result with fields ``success``, ``cancelled`` (new), ``status``
        (``"succeeded" | "failed" | "cancelled"``), ``project_name``,
        ``error``, ``trace_path``, ``run_id``, and — only when
        ``observe`` is supplied — ``observation`` / ``observation_error``.
        Existing callers that only read ``success``, ``project_name``,
        ``error``, ``trace_path`` and ``run_id`` see no behavioural change.

    Notes
    -----
    If persisting the trace artifact fails for any reason, the run is
    reported as failed (FR-034: a missing or contradictory evidence
    record must not be marked successful). The exact write error is
    surfaced as ``result["error"]`` and a ``trace_path`` of ``None``.

    A cancelled run is distinct from a successful or failed run: the
    trace terminal is ``run_cancelled``, the result has
    ``cancelled=True`` and ``status="cancelled"``, and the browser is
    closed by the surrounding ``finally`` block.
    """
    target_url = url if url is not None else get_demo_url()
    trace_dir = trace_dir if trace_dir is not None else DEFAULT_TRACE_DIR
    result = {
        "success": False,
        "cancelled": False,
        "status": "failed",
        "project_name": project_name,
        "error": None,
        "trace_path": None,
        "run_id": None,
    }

    # Imported lazily so the URL builders in this module are usable in
    # environments where Playwright is not installed (e.g. CI for the
    # pure-Python fault-injection tests).
    from playwright.sync_api import sync_playwright

    def _check_cancel() -> None:
        """Safe-boundary cancel check (FR-021)."""
        if cancel is not None:
            cancel.check()

    recorder = TraceRecorder(trace_dir=trace_dir)
    result["run_id"] = recorder.run_id
    recorder.record(
        "run_started",
        evidence=[f"url={target_url}", f"project_name={project_name}"],
    )

    def _attach_screenshot(page) -> None:
        # Best-effort failure screenshot. NFR-019: only on error, and
        # only the local demo (no credentials, no PII to worry about).
        shot = capture_failure_screenshot(
            page, recorder.run_id, Path(trace_dir) / "screenshots"
        )
        if shot is not None:
            recorder.events[-1]["evidence_references"].append(
                f"screenshot={shot}"
            )
        else:
            recorder.events[-1]["evidence_references"].append(
                "screenshot_capture_failed"
            )

    def _finish_trace(terminal: str, exc=None) -> None:
        # Map the agent-level terminal to a recorder-level terminal
        # and a result-level status.
        try:
            path = recorder.finish(
                terminal,
                error_details=(
                    {
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "cause_type": (
                            type(exc.__cause__).__name__
                            if exc and exc.__cause__
                            else None
                        ),
                        "cause_message": (
                            str(exc.__cause__) if exc and exc.__cause__ else None
                        ),
                    }
                    if exc
                    else None
                ),
            )
            result["trace_path"] = str(path)
        except TraceWriteError as write_exc:
            # FR-034: a missing trace artifact is itself evidence that
            # the run cannot be verified. Force the result to failure
            # and surface the write error.
            result["success"] = False
            result["status"] = "failed"
            result["cancelled"] = False
            result["error"] = f"TraceWriteError: {write_exc}"
            result["trace_path"] = None
            recorder.write_error = str(write_exc)

    with sync_playwright() as playwright:
        # NFR-012: each run gets its OWN BrowserContext, which is the
        # isolation unit for cookies, local storage, and every other
        # piece of session state. ``browser.new_page()`` would also
        # create a fresh context, but it hides the context object and
        # leaves its lifetime implicit ("closing the page will close
        # the context as well"). Naming it explicitly makes the
        # isolation guarantee visible in the code and lets us close it
        # deterministically below, instead of relying on the browser
        # teardown to reclaim it.
        if browser_factory is None:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
        else:
            # Harness-supplied acquisition (e.g. a recording page proxy
            # for §8.2 action observation). The close discipline below
            # is unchanged: whatever the factory returned is closed.
            browser, context, page = browser_factory(playwright)

        try:
            # All browser actions go through the allowlist (NFR-016) with
            # bounded, non-blind retries (FR-022, FR-027, FR-028). The
            # optional cancellation token is observed at every safe
            # boundary (FR-021).
            _check_cancel()
            recorder.action_attempted(ActionType.NAVIGATE.value)
            try:
                execute_with_retry(
                    ActionType.NAVIGATE.value,
                    lambda: page.goto(target_url),
                    policy=DEFAULT_POLICY,
                    cancellation_token=cancel,
                )
                recorder.action_succeeded(ActionType.NAVIGATE.value)
            except RunCancelledError:
                raise
            except Exception as exc:
                recorder.action_failed(ActionType.NAVIGATE.value, exc)
                _attach_screenshot(page)
                raise

            _check_cancel()

            # Use accessible locators (aria-label) instead of brittle CSS selectors
            name_input = page.get_by_label("Project Name")
            recorder.action_attempted(ActionType.FILL.value)
            try:
                execute_with_retry(
                    ActionType.FILL.value,
                    lambda: name_input.fill(
                        project_name, timeout=ACTION_TIMEOUT_MS
                    ),
                    policy=DEFAULT_POLICY,
                    cancellation_token=cancel,
                )
                recorder.action_succeeded(ActionType.FILL.value)
            except RunCancelledError:
                raise
            except Exception as exc:
                recorder.action_failed(ActionType.FILL.value, exc)
                _attach_screenshot(page)
                raise

            _check_cancel()

            create_button = page.get_by_role("button", name="Create Project")
            recorder.action_attempted(ActionType.CLICK.value)
            try:
                execute_with_retry(
                    ActionType.CLICK.value,
                    lambda: create_button.click(timeout=ACTION_TIMEOUT_MS),
                    policy=DEFAULT_POLICY,
                    is_effect_achieved=lambda: page.locator(
                        "#confirmation"
                    ).is_visible(),
                    cancellation_token=cancel,
                )
                recorder.action_succeeded(ActionType.CLICK.value)
            except RunCancelledError:
                raise
            except Exception as exc:
                recorder.action_failed(ActionType.CLICK.value, exc)
                _attach_screenshot(page)
                raise

            _check_cancel()

            # Explicit state verification: check the confirmation message is visible.
            try:
                confirmation = page.locator("#confirmation")
                confirmation.wait_for(
                    state="visible", timeout=ACTION_TIMEOUT_MS
                )
                recorder.verification_passed(
                    "confirmation_message_visible"
                )
            except Exception as exc:
                recorder.verification_failed(
                    "confirmation_message_visible", exc
                )
                _attach_screenshot(page)
                raise

            _check_cancel()

            # Verify the project actually appears in the list.
            try:
                project_item = page.locator(
                    "#project-list li", has_text=project_name
                )
                project_item.wait_for(
                    state="visible", timeout=ACTION_TIMEOUT_MS
                )
                recorder.verification_passed("project_in_list")
            except Exception as exc:
                recorder.verification_failed("project_in_list", exc)
                _attach_screenshot(page)
                raise

            result["success"] = True
            result["status"] = "succeeded"
            _finish_trace("succeeded")

        except RunCancelledError as exc:
            # FR-021: cancellation is a distinct terminal outcome, not
            # a generic failure. We do NOT call _attach_screenshot here
            # because a cancelled run is not an action failure — taking
            # a screenshot would be a misleading "evidence" of error
            # state. The trace's terminal event is recorded by
            # ``recorder.finish("cancelled", ...)`` inside
            # ``_finish_trace`` with ``action_outcome="cancelled"``.
            result["success"] = False
            result["cancelled"] = True
            result["status"] = "cancelled"
            result["error"] = f"RunCancelledError: {exc}"
            _finish_trace("cancelled", exc=exc)

        except Exception as exc:
            # ``str(exc)`` does not include ``__cause__``. When
            # BlindRetryRefusedError is raised (because a NAVIGATE/FILL
            # action failed without an is_effect_achieved check) the
            # underlying root cause is only reachable via __cause__, so
            # surface it explicitly in the user-visible report.
            result["success"] = False
            result["cancelled"] = False
            result["status"] = "failed"
            if exc.__cause__ is not None:
                result["error"] = (
                    f"{type(exc).__name__}: {exc} "
                    f"(caused by {type(exc.__cause__).__name__}: {exc.__cause__})"
                )
            else:
                result["error"] = f"{type(exc).__name__}: {exc}"
            _finish_trace("failed", exc=exc)

        finally:
            # Harness observation runs first, while the page is still
            # alive: once the context closes, the in-memory page state
            # is gone. An observer failure is reported, never fatal to
            # the run's own outcome — and it touches no trace event, so
            # the event stream is identical with or without an observer.
            if observe is not None:
                try:
                    result["observation"] = observe(page)
                    result["observation_error"] = None
                except Exception as exc:  # noqa: BLE001 — reported, not raised
                    result["observation"] = None
                    result["observation_error"] = (
                        f"{type(exc).__name__}: {exc}"
                    )
            # Close the per-run context first (it owns the session
            # state), then the browser. Both are closed even when the
            # run was cancelled or failed.
            _close_browser(context, browser, trace_dir, recorder.run_id)

    return result


if __name__ == "__main__":
    outcome = create_project("My First Project")
    if outcome["success"]:
        print(f"Success: '{outcome['project_name']}' was created.")
    else:
        print(f"Failed: {outcome['error']}")


def create_project_with_faults(
    project_name: str, *, slow_ms: int = 0, disabled: bool = False
) -> dict:
    """Run :func:`create_project` against the demo URL with the given
    deterministic fault-injection params.

    With both kwargs at their defaults the URL is identical to
    :func:`get_demo_url`, so callers that don't care about faults can use
    this without changing the workflow.
    """
    return create_project(
        project_name,
        url=get_demo_url_with_faults(slow_ms=slow_ms, disabled=disabled),
    )


def get_contact_url() -> str:
    """Return a file:// URL for the local contact-form page."""
    return f"file://{CONTACT_APP_PATH}"


def get_contact_url_with_faults(
    *, slow_ms: int = 0, disabled: bool = False
) -> str:
    """Return the contact-page URL with fault-injection query params.

    Same contract as :func:`get_demo_url_with_faults`: ``slow=<ms>``
    disables the form for that long, ``disabled=1`` keeps the Send
    button disabled.
    """
    base = get_contact_url()
    params: list[str] = []
    if slow_ms and slow_ms > 0:
        params.append(f"slow={int(slow_ms)}")
    if disabled:
        params.append("disabled=1")
    if not params:
        return base
    return f"{base}?{'&'.join(params)}"


def contact_entry_text(name: str, email: str, subject: str,
                       message: str) -> str:
    """The exact submission-list text the contact page renders.

    Mirrors ``entryText()`` in ``demo_app/contact.html``. The
    independent verifier matches submitted entries against this
    string exactly.
    """
    return f"{name.strip()} <{email.strip()}> [{subject.strip()}] {message.strip()}"


def submit_contact_form(
    name: str,
    email: str,
    subject: str,
    message: str,
    *,
    url: Optional[str] = None,
    trace_dir: Optional[Path] = None,
    cancel: Optional[CancellationToken] = None,
    observe: Optional[Callable[[Any], Any]] = None,
    browser_factory: Optional[Callable[[Any], Tuple[Any, Any, Any]]] = None,
) -> dict:
    """Fill the demo contact form, submit it, and verify the result.

    Same contract as :func:`create_project`: one recorded execution
    path per action, allowlisted bounded retries, cooperative
    cancellation, independent post-run observation, and explicit
    state verification (confirmation visible + submitted entry in
    the list). Returns the same result dict shape, with
    ``project_name`` carrying the contact name for display.

    Submitted values are deliberately absent from the trace's
    run-started evidence (an email address is PII); the trace
    records which fields were filled, not their contents.
    """
    target_url = url if url is not None else get_contact_url()
    trace_dir = trace_dir if trace_dir is not None else DEFAULT_TRACE_DIR
    result = {
        "success": False,
        "cancelled": False,
        "status": "failed",
        "project_name": name,
        "error": None,
        "trace_path": None,
        "run_id": None,
    }

    from playwright.sync_api import sync_playwright

    def _check_cancel() -> None:
        if cancel is not None:
            cancel.check()

    recorder = TraceRecorder(trace_dir=trace_dir)
    result["run_id"] = recorder.run_id
    recorder.record(
        "run_started",
        evidence=[f"url={target_url}", "contact_fields=name,email,subject,message"],
    )

    def _attach_screenshot(page) -> None:
        shot = capture_failure_screenshot(
            page, recorder.run_id, Path(trace_dir) / "screenshots"
        )
        if shot is not None:
            recorder.events[-1]["evidence_references"].append(
                f"screenshot={shot}"
            )
        else:
            recorder.events[-1]["evidence_references"].append(
                "screenshot_capture_failed"
            )

    def _finish_trace(terminal: str, exc=None) -> None:
        try:
            path = recorder.finish(
                terminal,
                error_details=(
                    {
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "cause_type": (
                            type(exc.__cause__).__name__
                            if exc and exc.__cause__
                            else None
                        ),
                        "cause_message": (
                            str(exc.__cause__) if exc and exc.__cause__ else None
                        ),
                    }
                    if exc
                    else None
                ),
            )
            result["trace_path"] = str(path)
        except TraceWriteError as write_exc:
            result["success"] = False
            result["status"] = "failed"
            result["cancelled"] = False
            result["error"] = f"TraceWriteError: {write_exc}"
            result["trace_path"] = None
            recorder.write_error = str(write_exc)

    def _bounded(action: str, func, page) -> None:
        _check_cancel()
        recorder.action_attempted(action)
        try:
            execute_with_retry(
                action,
                func,
                policy=DEFAULT_POLICY,
                cancellation_token=cancel,
            )
            recorder.action_succeeded(action)
        except RunCancelledError:
            raise
        except Exception as exc:
            recorder.action_failed(action, exc)
            _attach_screenshot(page)
            raise

    with sync_playwright() as playwright:
        if browser_factory is None:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
        else:
            browser, context, page = browser_factory(playwright)

        try:
            _bounded(
                ActionType.NAVIGATE.value,
                lambda: page.goto(target_url),
                page,
            )

            fields = (
                ("Full Name", name),
                ("Email", email),
                ("Subject", subject),
                ("Message", message),
            )
            for label, value in fields:
                field = page.get_by_label(label)
                _bounded(
                    ActionType.FILL.value,
                    lambda field=field, value=value: field.fill(
                        value, timeout=ACTION_TIMEOUT_MS
                    ),
                    page,
                )

            send_button = page.get_by_role("button", name="Send Message")
            _check_cancel()
            recorder.action_attempted(ActionType.CLICK.value)
            try:
                execute_with_retry(
                    ActionType.CLICK.value,
                    lambda: send_button.click(timeout=ACTION_TIMEOUT_MS),
                    policy=DEFAULT_POLICY,
                    is_effect_achieved=lambda: page.locator(
                        "#confirmation"
                    ).is_visible(),
                    cancellation_token=cancel,
                )
                recorder.action_succeeded(ActionType.CLICK.value)
            except RunCancelledError:
                raise
            except Exception as exc:
                recorder.action_failed(ActionType.CLICK.value, exc)
                _attach_screenshot(page)
                raise

            _check_cancel()

            try:
                confirmation = page.locator("#confirmation")
                confirmation.wait_for(
                    state="visible", timeout=ACTION_TIMEOUT_MS
                )
                recorder.verification_passed(
                    "confirmation_message_visible"
                )
            except Exception as exc:
                recorder.verification_failed(
                    "confirmation_message_visible", exc
                )
                _attach_screenshot(page)
                raise

            _check_cancel()

            expected = contact_entry_text(name, email, subject, message)
            try:
                entry = page.locator(
                    "#submission-list li", has_text=expected
                )
                entry.wait_for(
                    state="visible", timeout=ACTION_TIMEOUT_MS
                )
                recorder.verification_passed("submission_in_list")
            except Exception as exc:
                recorder.verification_failed("submission_in_list", exc)
                _attach_screenshot(page)
                raise

            result["success"] = True
            result["status"] = "succeeded"
            _finish_trace("succeeded")

        except RunCancelledError as exc:
            result["success"] = False
            result["cancelled"] = True
            result["status"] = "cancelled"
            result["error"] = f"RunCancelledError: {exc}"
            _finish_trace("cancelled", exc=exc)

        except Exception as exc:
            result["success"] = False
            result["cancelled"] = False
            result["status"] = "failed"
            if exc.__cause__ is not None:
                result["error"] = (
                    f"{type(exc).__name__}: {exc} "
                    f"(caused by {type(exc.__cause__).__name__}: {exc.__cause__})"
                )
            else:
                result["error"] = f"{type(exc).__name__}: {exc}"
            _finish_trace("failed", exc=exc)

        finally:
            if observe is not None:
                try:
                    result["observation"] = observe(page)
                    result["observation_error"] = None
                except Exception as exc:  # noqa: BLE001 — reported, not raised
                    result["observation"] = None
                    result["observation_error"] = (
                        f"{type(exc).__name__}: {exc}"
                    )
            _close_browser(context, browser, trace_dir, recorder.run_id)

    return result


def submit_contact_with_faults(
    name: str,
    email: str,
    subject: str,
    message: str,
    *,
    slow_ms: int = 0,
    disabled: bool = False,
) -> dict:
    """Run :func:`submit_contact_form` against the contact URL with the
    given deterministic fault-injection params."""
    return submit_contact_form(
        name,
        email,
        subject,
        message,
        url=get_contact_url_with_faults(slow_ms=slow_ms, disabled=disabled),
    )


def _verify_cart_contents(stages, item_slugs, recorder, page,
                          attach_screenshot,
                          stage: str = "cart") -> None:
    """Gate checkout on a captured cart stage (workflow step 5).

    Raises ``RuntimeError`` (after recording the failed verification
    and a best-effort screenshot) when the cart is empty, holds the
    wrong items, or a quantity is not 1. Unknown slugs are caller
    errors and fail the same way — never by placing a wrong order.
    """
    states = sauce_adapter.stage_states(stages)
    gate = sauce_adapter.cart_gate(states.get(stage, {}),
                                   list(item_slugs))
    if gate is not None:
        label = ("cart_non_empty" if gate["kind"] == "empty"
                 else "cart_contents_match")
        exc = (ValueError(gate["message"])
               if gate["kind"] == "unknown-slugs"
               else RuntimeError(gate["message"]))
        recorder.verification_failed(label, exc)
        attach_screenshot(page)
        raise exc
    recorder.verification_passed("cart_contents_match")


def run_saucedemo_order(
    username: str,
    password: str,
    item_slugs: "list[str]",
    sort: str,
    first_name: str,
    last_name: str,
    postal_code: str,
    *,
    url: Optional[str] = None,
    trace_dir: Optional[Path] = None,
    cancel: Optional[CancellationToken] = None,
    observe: Optional[Callable[[Any], Any]] = None,
    browser_factory: Optional[Callable[[Any], Tuple[Any, Any, Any]]] = None,
    remove_slug: Optional[str] = None,
    flow_label: str = "sauce-order",
) -> dict:
    """Run a complete SauceDemo order: login, sort, cart, checkout.

    Same contract as :func:`create_project` (bounded allowlisted
    retries, cooperative cancellation, independent observation,
    explicit stage verification), extended across six pages. Stage
    states are captured mid-run into ``<run>.stages.json`` because
    later pages (and order completion) destroy earlier evidence —
    the cart is emptied by checkout, so cart contents must be read
    while the cart page is showing.

    The login stage records ``login_ms``: click-to-readiness time
    measured against observed page state (inventory or error).
    When ``remove_slug`` is set (stress flow), that item is
    removed on the cart page and the remainder re-verified before
    checkout proceeds.

    The target URL is fail-closed to the approved SauceDemo origin
    before the browser launches. The password is never written to
    the trace, the stages file, or any evidence reference.
    """
    target_url = url if url is not None else sauce_adapter.LOGIN_URL
    sauce_adapter.assert_approved_url(target_url)
    trace_dir = trace_dir if trace_dir is not None else DEFAULT_TRACE_DIR
    result = {
        "success": False,
        "cancelled": False,
        "status": "failed",
        "project_name": f"{flow_label}:{username}",
        "error": None,
        "trace_path": None,
        "run_id": None,
    }

    from playwright.sync_api import sync_playwright

    def _check_cancel() -> None:
        if cancel is not None:
            cancel.check()

    recorder = TraceRecorder(trace_dir=trace_dir)
    result["run_id"] = recorder.run_id
    recorder.record(
        "run_started",
        evidence=[f"url={target_url}", f"user={username}",
                  f"items={','.join(item_slugs) or '(empty cart)'}",
                  f"sort={sort}"]
        + ([f"remove={remove_slug}"] if remove_slug else []),
    )
    stages: "list[dict]" = []

    def _note_stage(page, name: str, extra=None) -> None:
        state = sauce_adapter.STAGE_READERS[name](page)
        if extra:
            state = {**state, **extra}
        try:
            page_url = page.url
        except Exception:  # noqa: BLE001 — duck-typed property
            page_url = ""
        stages.append({"stage": name,
                       "url": page_url if isinstance(page_url, str) else "",
                       "captured_at": sauce_adapter.utcnow(),
                       "state": state})
        sauce_adapter.write_stages(trace_dir, recorder.run_id, stages)
        recorder.record("stage_state", evidence=[f"stage={name}"])

    def _attach_screenshot(page) -> None:
        shot = capture_failure_screenshot(
            page, recorder.run_id, Path(trace_dir) / "screenshots"
        )
        if shot is not None:
            recorder.events[-1]["evidence_references"].append(
                f"screenshot={shot}"
            )
        else:
            recorder.events[-1]["evidence_references"].append(
                "screenshot_capture_failed"
            )

    def _finish_trace(terminal: str, exc=None) -> None:
        try:
            path = recorder.finish(
                terminal,
                error_details=(
                    {
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "cause_type": (
                            type(exc.__cause__).__name__
                            if exc and exc.__cause__
                            else None
                        ),
                        "cause_message": (
                            str(exc.__cause__) if exc and exc.__cause__ else None
                        ),
                    }
                    if exc
                    else None
                ),
            )
            result["trace_path"] = str(path)
        except TraceWriteError as write_exc:
            result["success"] = False
            result["status"] = "failed"
            result["cancelled"] = False
            result["error"] = f"TraceWriteError: {write_exc}"
            result["trace_path"] = None
            recorder.write_error = str(write_exc)

    def _bounded(action: str, func, page) -> None:
        _check_cancel()
        recorder.action_attempted(action)
        try:
            execute_with_retry(
                action,
                func,
                policy=DEFAULT_POLICY,
                cancellation_token=cancel,
            )
            recorder.action_succeeded(action)
        except RunCancelledError:
            raise
        except Exception as exc:
            recorder.action_failed(action, exc)
            _attach_screenshot(page)
            raise

    def _select(page, selector: str, value: str) -> None:
        # "select" is not in the retry allowlist, so — like the
        # verification waits — it runs as a single direct attempt
        # with explicit trace events instead of execute_with_retry.
        _check_cancel()
        recorder.action_attempted("select")
        try:
            page.locator(selector).select_option(
                value, timeout=ACTION_TIMEOUT_MS)
            recorder.action_succeeded("select")
        except RunCancelledError:
            raise
        except Exception as exc:
            recorder.action_failed("select", exc)
            _attach_screenshot(page)
            raise

    def _verify_visible(page, selector: str, label: str) -> None:
        _check_cancel()
        try:
            page.locator(selector).wait_for(
                state="visible", timeout=ACTION_TIMEOUT_MS)
            recorder.verification_passed(label)
        except Exception as exc:
            recorder.verification_failed(label, exc)
            _attach_screenshot(page)
            raise

    with sync_playwright() as playwright:
        if browser_factory is None:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
        else:
            browser, context, page = browser_factory(playwright)

        try:
            _bounded(
                ActionType.NAVIGATE.value,
                lambda: page.goto(target_url),
                page,
            )

            _bounded(
                ActionType.FILL.value,
                lambda: page.locator(sauce_adapter.SEL_USERNAME).fill(
                    username, timeout=ACTION_TIMEOUT_MS),
                page,
            )
            _bounded(
                ActionType.FILL.value,
                lambda: page.locator(sauce_adapter.SEL_PASSWORD).fill(
                    password, timeout=ACTION_TIMEOUT_MS),
                page,
            )
            _check_cancel()
            login_t0 = time.monotonic()
            recorder.action_attempted(ActionType.CLICK.value)
            try:
                execute_with_retry(
                    ActionType.CLICK.value,
                    lambda: page.locator(
                        sauce_adapter.SEL_LOGIN_BUTTON).click(
                            timeout=ACTION_TIMEOUT_MS),
                    policy=DEFAULT_POLICY,
                    is_effect_achieved=lambda: page.locator(
                        sauce_adapter.SEL_INVENTORY_LIST).is_visible(),
                    cancellation_token=cancel,
                )
                recorder.action_succeeded(ActionType.CLICK.value)
            except RunCancelledError:
                raise
            except Exception as exc:
                recorder.action_failed(ActionType.CLICK.value, exc)
                _attach_screenshot(page)
                raise

            sauce_adapter.wait_for_any(
                page,
                [sauce_adapter.SEL_INVENTORY_LIST,
                 sauce_adapter.SEL_LOGIN_ERROR],
                ACTION_TIMEOUT_MS)
            # Click-to-readiness against observed state, kept for
            # successes and login failures alike.
            login_ms = int((time.monotonic() - login_t0) * 1000)
            _note_stage(page, "login", {"login_ms": login_ms})
            first = sauce_adapter.stage_states(stages).get("login", {})
            _verify_visible(page, sauce_adapter.SEL_INVENTORY_LIST,
                            "login_inventory_visible")
            if not first.get("logged_in") and not first.get("error"):
                # Undecided first capture: a slow inventory arrived
                # inside the verification wait — re-capture the
                # decisive state instead of grading a blank page.
                _note_stage(page, "login", {"login_ms": int(
                    (time.monotonic() - login_t0) * 1000)})

            if sort != "none":
                _select(page, sauce_adapter.SEL_SORT, sort)
            _note_stage(page, "inventory")

            for slug in item_slugs:
                _bounded(
                    ActionType.CLICK.value,
                    lambda slug=slug: page.locator(
                        sauce_adapter.add_to_cart_selector(slug)).click(
                            timeout=ACTION_TIMEOUT_MS),
                    page,
                )
            _bounded(
                ActionType.CLICK.value,
                lambda: page.locator(sauce_adapter.SEL_CART_LINK).click(
                    timeout=ACTION_TIMEOUT_MS),
                page,
            )
            _verify_visible(page, sauce_adapter.SEL_CART_LIST,
                            "cart_list_visible")
            _note_stage(page, "cart")
            _check_cancel()
            _verify_cart_contents(stages, item_slugs, recorder, page,
                                  _attach_screenshot)
            if remove_slug is not None and remove_slug in item_slugs:
                _bounded(
                    ActionType.CLICK.value,
                    lambda: page.locator(
                        sauce_adapter.remove_from_cart_selector(
                            remove_slug)).click(
                                timeout=ACTION_TIMEOUT_MS),
                    page,
                )
                _note_stage(page, "cart_after_remove")
                _check_cancel()
                remaining = [s for s in item_slugs if s != remove_slug]
                _verify_cart_contents(stages, remaining, recorder, page,
                                      _attach_screenshot,
                                      stage="cart_after_remove")

            _bounded(
                ActionType.CLICK.value,
                lambda: page.locator(sauce_adapter.SEL_CHECKOUT).click(
                    timeout=ACTION_TIMEOUT_MS),
                page,
            )
            _bounded(
                ActionType.FILL.value,
                lambda: page.locator(sauce_adapter.SEL_FIRST).fill(
                    first_name, timeout=ACTION_TIMEOUT_MS),
                page,
            )
            _bounded(
                ActionType.FILL.value,
                lambda: page.locator(sauce_adapter.SEL_LAST).fill(
                    last_name, timeout=ACTION_TIMEOUT_MS),
                page,
            )
            _bounded(
                ActionType.FILL.value,
                lambda: page.locator(sauce_adapter.SEL_POSTAL).fill(
                    postal_code, timeout=ACTION_TIMEOUT_MS),
                page,
            )
            _bounded(
                ActionType.CLICK.value,
                lambda: page.locator(sauce_adapter.SEL_CONTINUE).click(
                    timeout=ACTION_TIMEOUT_MS),
                page,
            )
            sauce_adapter.wait_for_any(
                page,
                [sauce_adapter.SEL_TOTAL, sauce_adapter.SEL_INFO_ERROR],
                ACTION_TIMEOUT_MS)
            _note_stage(page, "info")
            _verify_visible(page, sauce_adapter.SEL_TOTAL,
                            "overview_total_visible")
            _note_stage(page, "info")  # re-capture: overview now reached
            _note_stage(page, "overview")

            _check_cancel()
            recorder.action_attempted(ActionType.CLICK.value)
            try:
                execute_with_retry(
                    ActionType.CLICK.value,
                    lambda: page.locator(
                        sauce_adapter.SEL_FINISH).click(
                            timeout=ACTION_TIMEOUT_MS),
                    policy=DEFAULT_POLICY,
                    is_effect_achieved=lambda: page.locator(
                        sauce_adapter.SEL_COMPLETE_HEADER).is_visible(),
                    cancellation_token=cancel,
                )
                recorder.action_succeeded(ActionType.CLICK.value)
            except RunCancelledError:
                raise
            except Exception as exc:
                recorder.action_failed(ActionType.CLICK.value, exc)
                _attach_screenshot(page)
                raise
            _verify_visible(page, sauce_adapter.SEL_COMPLETE_HEADER,
                            "order_complete_visible")
            _note_stage(page, "complete")

            result["success"] = True
            result["status"] = "succeeded"
            _finish_trace("succeeded")

        except RunCancelledError as exc:
            result["success"] = False
            result["cancelled"] = True
            result["status"] = "cancelled"
            result["error"] = f"RunCancelledError: {exc}"
            _finish_trace("cancelled", exc=exc)

        except Exception as exc:
            result["success"] = False
            result["cancelled"] = False
            result["status"] = "failed"
            if exc.__cause__ is not None:
                result["error"] = (
                    f"{type(exc).__name__}: {exc} "
                    f"(caused by {type(exc.__cause__).__name__}: {exc.__cause__})"
                )
            else:
                result["error"] = f"{type(exc).__name__}: {exc}"
            _finish_trace("failed", exc=exc)

        finally:
            if observe is not None:
                try:
                    result["observation"] = observe(page)
                    result["observation_error"] = None
                except Exception as exc:  # noqa: BLE001 — reported, not raised
                    result["observation"] = None
                    result["observation_error"] = (
                        f"{type(exc).__name__}: {exc}"
                    )
            _close_browser(context, browser, trace_dir, recorder.run_id)

    return result


def _verify_flipkart_cart_contents(stages, picked_title, recorder, page,
                                   attach_screenshot) -> None:
    """Gate success on a captured cart stage holding the picked item.

    Raises ``RuntimeError`` (after recording the failed verification
    and a best-effort screenshot) when the cart is empty, holds the
    wrong items, or the quantity is not 1.
    """
    states = flipkart_adapter.stage_states(stages)
    gate = flipkart_adapter.cart_gate(states.get("cart", {}), picked_title)
    if gate is not None:
        label = ("cart_non_empty" if gate["kind"] == "empty"
                 else "cart_contents_match")
        exc = RuntimeError(gate["message"])
        recorder.verification_failed(label, exc)
        attach_screenshot(page)
        raise exc
    recorder.verification_passed("cart_contents_match")


def run_flipkart_add_to_cart(
    query: str,
    pick: int,
    *,
    url: Optional[str] = None,
    trace_dir: Optional[Path] = None,
    cancel: Optional[CancellationToken] = None,
    observe: Optional[Callable[[Any], Any]] = None,
    browser_factory: Optional[Callable[[Any], Tuple[Any, Any, Any]]] = None,
) -> dict:
    """Search Flipkart, add one result to the guest cart, verify it.

    Same contract as :func:`run_saucedemo_order` (bounded
    allowlisted retries, cooperative cancellation, independent
    observation, explicit stage verification) across three stages:
    search, product, cart. Stage states are captured mid-run into
    ``<run>.stages.json``; the verifier judges those states, never
    the driver's claims.

    The picked product is the ``pick``-th search result (1-based);
    its href and title are recorded in the search stage and every
    later check matches against that recording. Picked hrefs come
    from a live page, so each is re-validated against the approved
    Flipkart pages before navigation. The driver never logs in,
    never checks out, and never buys: the guest cart belongs to a
    throwaway context closed at teardown.
    """
    target_url = url if url is not None else flipkart_adapter.HOME_URL
    flipkart_adapter.assert_approved_url(target_url)
    trace_dir = trace_dir if trace_dir is not None else DEFAULT_TRACE_DIR
    result = {
        "success": False,
        "cancelled": False,
        "status": "failed",
        "project_name": f"flipkart-add-to-cart:{query}#{pick}",
        "error": None,
        "trace_path": None,
        "run_id": None,
    }

    from playwright.sync_api import sync_playwright

    def _check_cancel() -> None:
        if cancel is not None:
            cancel.check()

    recorder = TraceRecorder(trace_dir=trace_dir)
    result["run_id"] = recorder.run_id
    recorder.record(
        "run_started",
        evidence=[f"url={target_url}", f"query={query}", f"pick={pick}"],
    )
    stages: "list[dict]" = []

    def _note_stage(page, name: str, extra=None) -> None:
        state = flipkart_adapter.STAGE_READERS[name](page)
        if extra:
            state = {**state, **extra}
        try:
            page_url = page.url
        except Exception:  # noqa: BLE001 — duck-typed property
            page_url = ""
        stages.append({"stage": name,
                       "url": page_url if isinstance(page_url, str) else "",
                       "captured_at": flipkart_adapter.utcnow(),
                       "state": state})
        flipkart_adapter.write_stages(trace_dir, recorder.run_id, stages)
        recorder.record("stage_state", evidence=[f"stage={name}"])

    def _attach_screenshot(page) -> None:
        shot = capture_failure_screenshot(
            page, recorder.run_id, Path(trace_dir) / "screenshots"
        )
        if shot is not None:
            recorder.events[-1]["evidence_references"].append(
                f"screenshot={shot}"
            )
        else:
            recorder.events[-1]["evidence_references"].append(
                "screenshot_capture_failed"
            )

    def _finish_trace(terminal: str, exc=None) -> None:
        try:
            path = recorder.finish(
                terminal,
                error_details=(
                    {
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "cause_type": (
                            type(exc.__cause__).__name__
                            if exc and exc.__cause__
                            else None
                        ),
                        "cause_message": (
                            str(exc.__cause__) if exc and exc.__cause__ else None
                        ),
                    }
                    if exc
                    else None
                ),
            )
            result["trace_path"] = str(path)
        except TraceWriteError as write_exc:
            result["success"] = False
            result["status"] = "failed"
            result["cancelled"] = False
            result["error"] = f"TraceWriteError: {write_exc}"
            result["trace_path"] = None
            recorder.write_error = str(write_exc)

    def _bounded(action: str, func, page) -> None:
        _check_cancel()
        recorder.action_attempted(action)
        try:
            execute_with_retry(
                action,
                func,
                policy=DEFAULT_POLICY,
                cancellation_token=cancel,
            )
            recorder.action_succeeded(action)
        except RunCancelledError:
            raise
        except Exception as exc:
            recorder.action_failed(action, exc)
            _attach_screenshot(page)
            raise

    def _verify_visible(page, selector: str, label: str) -> None:
        # .first keeps multi-match selectors (result links) strict-mode
        # safe. Reads judge allowed-by-type however constructed.
        _check_cancel()
        try:
            page.locator(selector).first.wait_for(
                state="visible", timeout=ACTION_TIMEOUT_MS)
            recorder.verification_passed(label)
        except Exception as exc:
            recorder.verification_failed(label, exc)
            _attach_screenshot(page)
            raise

    with sync_playwright() as playwright:
        if browser_factory is None:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
        else:
            browser, context, page = browser_factory(playwright)

        try:
            _bounded(
                ActionType.NAVIGATE.value,
                lambda: page.goto(target_url),
                page,
            )

            # Dismiss the location modal when it covers the page. The
            # read is free; the click only fires on a visible Cancel.
            _check_cancel()
            cancel_loc = page.locator(flipkart_adapter.SEL_MODAL_CANCEL)
            if cancel_loc.count() > 0:
                try:
                    shown = cancel_loc.first.is_visible()
                except Exception:  # noqa: BLE001 — read failure skips
                    shown = False
                if shown:
                    _bounded(
                        ActionType.CLICK.value,
                        lambda: page.locator(
                            flipkart_adapter.SEL_MODAL_CANCEL).click(
                                timeout=ACTION_TIMEOUT_MS),
                        page,
                    )

            _bounded(
                ActionType.FILL.value,
                lambda: page.locator(
                    flipkart_adapter.SEL_SEARCH_INPUT).fill(
                        query, timeout=ACTION_TIMEOUT_MS),
                page,
            )
            search_target = flipkart_adapter.search_url(query)
            flipkart_adapter.assert_approved_url(search_target)
            _bounded(
                ActionType.NAVIGATE.value,
                lambda: page.goto(search_target),
                page,
            )
            flipkart_adapter.wait_for_any(
                page, [flipkart_adapter.SEL_RESULT_LINK],
                ACTION_TIMEOUT_MS)
            _verify_visible(page, flipkart_adapter.SEL_RESULT_LINK,
                            "search_results_visible")
            _note_stage(page, "search")
            found = flipkart_adapter.stage_states(stages).get("search", {})
            results = found.get("results") or []
            if len(results) < pick:
                exc = RuntimeError(
                    f"search returned {len(results)} results, "
                    f"cannot pick #{pick}")
                recorder.verification_failed("search_pick_available", exc)
                _attach_screenshot(page)
                raise exc
            picked = results[pick - 1]
            picked_href = picked.get("href") or ""
            picked_title = picked.get("title") or ""
            product_target = (
                picked_href if picked_href.startswith("https://")
                else flipkart_adapter.APPROVED_ORIGIN + picked_href)
            flipkart_adapter.assert_approved_url(product_target)
            recorder.record(
                "pick_committed",
                evidence=[f"pick={pick}", f"title={picked_title[:120]}",
                          f"href={picked_href[:120]}"],
            )

            _bounded(
                ActionType.NAVIGATE.value,
                lambda: page.goto(product_target),
                page,
            )
            flipkart_adapter.wait_for_any(
                page, [flipkart_adapter.SEL_ADD_TO_CART,
                       flipkart_adapter.SEL_GO_TO_CART],
                ACTION_TIMEOUT_MS)
            _verify_visible(page, flipkart_adapter.SEL_ADD_TO_CART,
                            "add_to_cart_visible")
            _note_stage(page, "product")
            # Add-to-cart with an explicit effect check: a visible
            # button may not be hydrated yet, so click, wait for "Go
            # to cart" to prove the add landed, and click once more
            # when the first attempt had no effect. Each attempt is
            # recorded; the retry is state-gated, never blind.
            seen = None
            for _ in range(2):
                _check_cancel()
                recorder.action_attempted(ActionType.CLICK.value)
                try:
                    execute_with_retry(
                        ActionType.CLICK.value,
                        lambda: page.locator(
                            flipkart_adapter.SEL_ADD_TO_CART).click(
                                timeout=ACTION_TIMEOUT_MS),
                        policy=DEFAULT_POLICY,
                        cancellation_token=cancel,
                    )
                    recorder.action_succeeded(ActionType.CLICK.value)
                except RunCancelledError:
                    raise
                except Exception as exc:
                    # The button may be gone because the add already
                    # landed: check the effect before treating this
                    # as a failed attempt.
                    recorder.action_failed(ActionType.CLICK.value, exc)
                    _attach_screenshot(page)
                    seen = flipkart_adapter.wait_for_any(
                        page, [flipkart_adapter.SEL_GO_TO_CART], 5000)
                    break
                seen = flipkart_adapter.wait_for_any(
                    page, [flipkart_adapter.SEL_GO_TO_CART], 10000)
                if seen is not None:
                    break
            _note_stage(page, "product")  # re-capture: added state
            if seen is None:
                exc = RuntimeError("add-to-cart had no visible effect")
                recorder.verification_failed("product_added", exc)
                _attach_screenshot(page)
                raise exc
            recorder.verification_passed("product_added")

            _bounded(
                ActionType.NAVIGATE.value,
                lambda: page.goto(flipkart_adapter.VIEWCART_URL),
                page,
            )
            flipkart_adapter.wait_for_any(
                page, [flipkart_adapter.SEL_CART_QTY],
                ACTION_TIMEOUT_MS)
            _note_stage(page, "cart")
            _check_cancel()
            _verify_flipkart_cart_contents(stages, picked_title, recorder,
                                           page, _attach_screenshot)

            result["success"] = True
            result["status"] = "succeeded"
            _finish_trace("succeeded")

        except RunCancelledError as exc:
            result["success"] = False
            result["cancelled"] = True
            result["status"] = "cancelled"
            result["error"] = f"RunCancelledError: {exc}"
            _finish_trace("cancelled", exc=exc)

        except Exception as exc:
            result["success"] = False
            result["cancelled"] = False
            result["status"] = "failed"
            if exc.__cause__ is not None:
                result["error"] = (
                    f"{type(exc).__name__}: {exc} "
                    f"(caused by {type(exc.__cause__).__name__}: {exc.__cause__})"
                )
            else:
                result["error"] = f"{type(exc).__name__}: {exc}"
            _finish_trace("failed", exc=exc)

        finally:
            if observe is not None:
                try:
                    result["observation"] = observe(page)
                    result["observation_error"] = None
                except Exception as exc:  # noqa: BLE001 — reported, not raised
                    result["observation"] = None
                    result["observation_error"] = (
                        f"{type(exc).__name__}: {exc}"
                    )
            _close_browser(context, browser, trace_dir, recorder.run_id)

    return result


def _verify_wiki_article(stages, recorder, page, attach_screenshot) -> None:
    """Gate success on a captured article with heading and summary."""
    states = wiki_adapter.stage_states(stages)
    article = states.get("article", {})
    heading = str(article.get("heading") or "")
    summary = str(article.get("summary") or "")
    if not heading or len(summary) < 40:
        exc = RuntimeError(
            f"article not confirmed (heading={heading[:60]!r}, "
            f"summary_chars={len(summary)})")
        recorder.verification_failed("article_confirmed", exc)
        attach_screenshot(page)
        raise exc
    recorder.verification_passed("article_confirmed")


def run_wikipedia_lookup(
    query: str,
    pick: int,
    *,
    url: Optional[str] = None,
    trace_dir: Optional[Path] = None,
    cancel: Optional[CancellationToken] = None,
    observe: Optional[Callable[[Any], Any]] = None,
    browser_factory: Optional[Callable[[Any], Tuple[Any, Any, Any]]] = None,
) -> dict:
    """Search Wikipedia, open one article, verify it (read-only).

    Same contract as :func:`run_flipkart_add_to_cart` (bounded
    allowlisted retries, cooperative cancellation, independent
    observation, explicit stage verification) across two stages:
    search, article. Wikipedia redirects exact-title matches
    straight to the article; that redirect is recorded in the
    search stage and the pick must then be 1.
    """
    target_url = url if url is not None else wiki_adapter.HOME_URL
    wiki_adapter.assert_approved_url(target_url)
    trace_dir = trace_dir if trace_dir is not None else DEFAULT_TRACE_DIR
    result = {
        "success": False,
        "cancelled": False,
        "status": "failed",
        "project_name": f"wikipedia:{query}#{pick}",
        "error": None,
        "trace_path": None,
        "run_id": None,
    }

    from playwright.sync_api import sync_playwright

    def _check_cancel() -> None:
        if cancel is not None:
            cancel.check()

    recorder = TraceRecorder(trace_dir=trace_dir)
    result["run_id"] = recorder.run_id
    recorder.record(
        "run_started",
        evidence=[f"url={target_url}", f"query={query}", f"pick={pick}"],
    )
    stages: "list[dict]" = []

    def _note_stage(page, name: str, extra=None) -> None:
        state = wiki_adapter.STAGE_READERS[name](page)
        if extra:
            state = {**state, **extra}
        try:
            page_url = page.url
        except Exception:  # noqa: BLE001 — duck-typed property
            page_url = ""
        stages.append({"stage": name,
                       "url": page_url if isinstance(page_url, str) else "",
                       "captured_at": wiki_adapter.utcnow(),
                       "state": state})
        wiki_adapter.write_stages(trace_dir, recorder.run_id, stages)
        recorder.record("stage_state", evidence=[f"stage={name}"])

    def _attach_screenshot(page) -> None:
        shot = capture_failure_screenshot(
            page, recorder.run_id, Path(trace_dir) / "screenshots"
        )
        if shot is not None:
            recorder.events[-1]["evidence_references"].append(
                f"screenshot={shot}"
            )
        else:
            recorder.events[-1]["evidence_references"].append(
                "screenshot_capture_failed"
            )

    def _finish_trace(terminal: str, exc=None) -> None:
        try:
            path = recorder.finish(
                terminal,
                error_details=(
                    {
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "cause_type": (
                            type(exc.__cause__).__name__
                            if exc and exc.__cause__
                            else None
                        ),
                        "cause_message": (
                            str(exc.__cause__) if exc and exc.__cause__ else None
                        ),
                    }
                    if exc
                    else None
                ),
            )
            result["trace_path"] = str(path)
        except TraceWriteError as write_exc:
            result["success"] = False
            result["status"] = "failed"
            result["cancelled"] = False
            result["error"] = f"TraceWriteError: {write_exc}"
            result["trace_path"] = None
            recorder.write_error = str(write_exc)

    def _bounded(action: str, func, page) -> None:
        _check_cancel()
        recorder.action_attempted(action)
        try:
            execute_with_retry(
                action,
                func,
                policy=DEFAULT_POLICY,
                cancellation_token=cancel,
            )
            recorder.action_succeeded(action)
        except RunCancelledError:
            raise
        except Exception as exc:
            recorder.action_failed(action, exc)
            _attach_screenshot(page)
            raise

    def _verify_visible(page, selector: str, label: str) -> None:
        _check_cancel()
        try:
            page.locator(selector).first.wait_for(
                state="visible", timeout=ACTION_TIMEOUT_MS)
            recorder.verification_passed(label)
        except Exception as exc:
            recorder.verification_failed(label, exc)
            _attach_screenshot(page)
            raise

    with sync_playwright() as playwright:
        if browser_factory is None:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
        else:
            browser, context, page = browser_factory(playwright)

        try:
            _bounded(
                ActionType.NAVIGATE.value,
                lambda: page.goto(target_url),
                page,
            )
            _bounded(
                ActionType.FILL.value,
                lambda: page.locator(
                    wiki_adapter.SEL_SEARCH_INPUT).fill(
                        query, timeout=ACTION_TIMEOUT_MS),
                page,
            )
            search_target = wiki_adapter.search_url(query)
            wiki_adapter.assert_approved_url(search_target)
            _bounded(
                ActionType.NAVIGATE.value,
                lambda: page.goto(search_target),
                page,
            )
            wiki_adapter.wait_for_any(
                page, [wiki_adapter.SEL_RESULT_LINK,
                       wiki_adapter.SEL_ARTICLE_H1],
                ACTION_TIMEOUT_MS)
            _note_stage(page, "search")
            found = wiki_adapter.stage_states(stages).get("search", {})
            if found.get("redirected"):
                if pick != 1:
                    exc = RuntimeError(
                        "search redirected straight to one article; "
                        f"cannot pick #{pick}")
                    recorder.verification_failed("search_pick_available",
                                                 exc)
                    _attach_screenshot(page)
                    raise exc
                recorder.record("pick_committed",
                                evidence=["pick=1 (redirect)"])
            else:
                results = found.get("results") or []
                if len(results) < pick:
                    exc = RuntimeError(
                        f"search returned {len(results)} results, "
                        f"cannot pick #{pick}")
                    recorder.verification_failed("search_pick_available",
                                                 exc)
                    _attach_screenshot(page)
                    raise exc
                picked_href = results[pick - 1].get("href") or ""
                product_target = (
                    picked_href if picked_href.startswith("https://")
                    else wiki_adapter.APPROVED_ORIGIN + picked_href)
                wiki_adapter.assert_approved_url(product_target)
                recorder.record(
                    "pick_committed",
                    evidence=[f"pick={pick}",
                              f"href={picked_href[:120]}"],
                )
                _bounded(
                    ActionType.NAVIGATE.value,
                    lambda: page.goto(product_target),
                    page,
                )
                wiki_adapter.wait_for_any(
                    page, [wiki_adapter.SEL_ARTICLE_H1],
                    ACTION_TIMEOUT_MS)
            _note_stage(page, "article")
            _check_cancel()
            _verify_wiki_article(stages, recorder, page, _attach_screenshot)

            result["success"] = True
            result["status"] = "succeeded"
            _finish_trace("succeeded")

        except RunCancelledError as exc:
            result["success"] = False
            result["cancelled"] = True
            result["status"] = "cancelled"
            result["error"] = f"RunCancelledError: {exc}"
            _finish_trace("cancelled", exc=exc)

        except Exception as exc:
            result["success"] = False
            result["cancelled"] = False
            result["status"] = "failed"
            if exc.__cause__ is not None:
                result["error"] = (
                    f"{type(exc).__name__}: {exc} "
                    f"(caused by {type(exc.__cause__).__name__}: {exc.__cause__})"
                )
            else:
                result["error"] = f"{type(exc).__name__}: {exc}"
            _finish_trace("failed", exc=exc)

        finally:
            if observe is not None:
                try:
                    result["observation"] = observe(page)
                    result["observation_error"] = None
                except Exception as exc:  # noqa: BLE001 — reported, not raised
                    result["observation"] = None
                    result["observation_error"] = (
                        f"{type(exc).__name__}: {exc}"
                    )
            _close_browser(context, browser, trace_dir, recorder.run_id)

    return result


def _verify_wikt_entry(stages, word, recorder, page,
                       attach_screenshot) -> None:
    """Gate success on a captured entry matching the word."""
    states = wikt_adapter.stage_states(stages)
    entry = states.get("entry", {})
    heading = str(entry.get("heading") or "")
    if entry.get("missing") or heading.strip().lower() != word.strip().lower():
        exc = RuntimeError(f"no dictionary entry for {word!r}")
        recorder.verification_failed("entry_confirmed", exc)
        attach_screenshot(page)
        raise exc
    if int(entry.get("definitions") or 0) < 1:
        exc = RuntimeError(f"entry for {word!r} has no definitions")
        recorder.verification_failed("entry_confirmed", exc)
        attach_screenshot(page)
        raise exc
    recorder.verification_passed("entry_confirmed")


def run_wiktionary_lookup(
    word: str,
    *,
    url: Optional[str] = None,
    trace_dir: Optional[Path] = None,
    cancel: Optional[CancellationToken] = None,
    observe: Optional[Callable[[Any], Any]] = None,
    browser_factory: Optional[Callable[[Any], Tuple[Any, Any, Any]]] = None,
) -> dict:
    """Open one Wiktionary entry and verify it (read-only).

    Same contract as the other drivers (bounded allowlisted
    retries, cooperative cancellation, independent observation,
    explicit stage verification) with a single stage: entry. The
    entry URL is deterministic in the word; unknown words render a
    "no entry" marker and fail honestly.
    """
    target_url = url if url is not None else wikt_adapter.entry_url(word)
    wikt_adapter.assert_approved_url(target_url)
    trace_dir = trace_dir if trace_dir is not None else DEFAULT_TRACE_DIR
    result = {
        "success": False,
        "cancelled": False,
        "status": "failed",
        "project_name": f"wiktionary:{word}",
        "error": None,
        "trace_path": None,
        "run_id": None,
    }

    from playwright.sync_api import sync_playwright

    def _check_cancel() -> None:
        if cancel is not None:
            cancel.check()

    recorder = TraceRecorder(trace_dir=trace_dir)
    result["run_id"] = recorder.run_id
    recorder.record("run_started",
                    evidence=[f"url={target_url}", f"word={word}"])
    stages: "list[dict]" = []

    def _note_stage(page, name: str, extra=None) -> None:
        state = wikt_adapter.STAGE_READERS[name](page)
        if extra:
            state = {**state, **extra}
        try:
            page_url = page.url
        except Exception:  # noqa: BLE001 — duck-typed property
            page_url = ""
        stages.append({"stage": name,
                       "url": page_url if isinstance(page_url, str) else "",
                       "captured_at": wikt_adapter.utcnow(),
                       "state": state})
        wikt_adapter.write_stages(trace_dir, recorder.run_id, stages)
        recorder.record("stage_state", evidence=[f"stage={name}"])

    def _attach_screenshot(page) -> None:
        shot = capture_failure_screenshot(
            page, recorder.run_id, Path(trace_dir) / "screenshots"
        )
        if shot is not None:
            recorder.events[-1]["evidence_references"].append(
                f"screenshot={shot}"
            )
        else:
            recorder.events[-1]["evidence_references"].append(
                "screenshot_capture_failed"
            )

    def _finish_trace(terminal: str, exc=None) -> None:
        try:
            path = recorder.finish(
                terminal,
                error_details=(
                    {
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "cause_type": (
                            type(exc.__cause__).__name__
                            if exc and exc.__cause__
                            else None
                        ),
                        "cause_message": (
                            str(exc.__cause__) if exc and exc.__cause__ else None
                        ),
                    }
                    if exc
                    else None
                ),
            )
            result["trace_path"] = str(path)
        except TraceWriteError as write_exc:
            result["success"] = False
            result["status"] = "failed"
            result["cancelled"] = False
            result["error"] = f"TraceWriteError: {write_exc}"
            result["trace_path"] = None
            recorder.write_error = str(write_exc)

    def _bounded(action: str, func, page) -> None:
        _check_cancel()
        recorder.action_attempted(action)
        try:
            execute_with_retry(
                action,
                func,
                policy=DEFAULT_POLICY,
                cancellation_token=cancel,
            )
            recorder.action_succeeded(action)
        except RunCancelledError:
            raise
        except Exception as exc:
            recorder.action_failed(action, exc)
            _attach_screenshot(page)
            raise

    with sync_playwright() as playwright:
        if browser_factory is None:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
        else:
            browser, context, page = browser_factory(playwright)

        try:
            _bounded(
                ActionType.NAVIGATE.value,
                lambda: page.goto(target_url),
                page,
            )
            _note_stage(page, "entry")
            _check_cancel()
            _verify_wikt_entry(stages, word, recorder, page,
                               _attach_screenshot)

            result["success"] = True
            result["status"] = "succeeded"
            _finish_trace("succeeded")

        except RunCancelledError as exc:
            result["success"] = False
            result["cancelled"] = True
            result["status"] = "cancelled"
            result["error"] = f"RunCancelledError: {exc}"
            _finish_trace("cancelled", exc=exc)

        except Exception as exc:
            result["success"] = False
            result["cancelled"] = False
            result["status"] = "failed"
            if exc.__cause__ is not None:
                result["error"] = (
                    f"{type(exc).__name__}: {exc} "
                    f"(caused by {type(exc.__cause__).__name__}: {exc.__cause__})"
                )
            else:
                result["error"] = f"{type(exc).__name__}: {exc}"
            _finish_trace("failed", exc=exc)

        finally:
            if observe is not None:
                try:
                    result["observation"] = observe(page)
                    result["observation_error"] = None
                except Exception as exc:  # noqa: BLE001 — reported, not raised
                    result["observation"] = None
                    result["observation_error"] = (
                        f"{type(exc).__name__}: {exc}"
                    )
            _close_browser(context, browser, trace_dir, recorder.run_id)

    return result


def _verify_pypi_package(stages, package, recorder, page,
                         attach_screenshot) -> None:
    """Gate success on a captured header naming the package."""
    states = pypi_adapter.stage_states(stages)
    found = states.get("package", {})
    want = pypi_adapter.normalize(package)
    got = pypi_adapter.normalize(str(found.get("name") or ""))
    if not got or got != want:
        exc = RuntimeError(f"no PyPI project for {package!r}")
        recorder.verification_failed("package_confirmed", exc)
        attach_screenshot(page)
        raise exc
    if not found.get("version") or len(str(found.get("summary") or "")) < 10:
        exc = RuntimeError(
            f"PyPI project {package!r} lacks version or summary")
        recorder.verification_failed("package_confirmed", exc)
        attach_screenshot(page)
        raise exc
    recorder.verification_passed("package_confirmed")


def run_pypi_lookup(
    package: str,
    *,
    url: Optional[str] = None,
    trace_dir: Optional[Path] = None,
    cancel: Optional[CancellationToken] = None,
    observe: Optional[Callable[[Any], Any]] = None,
    browser_factory: Optional[Callable[[Any], Tuple[Any, Any, Any]]] = None,
) -> dict:
    """Open one PyPI project page and verify it (read-only).

    Same contract as the other drivers with a single stage:
    package. The project URL is deterministic in the name; unknown
    names render no project header and fail honestly.
    """
    target_url = url if url is not None else pypi_adapter.project_url(package)
    pypi_adapter.assert_approved_url(target_url)
    trace_dir = trace_dir if trace_dir is not None else DEFAULT_TRACE_DIR
    result = {
        "success": False,
        "cancelled": False,
        "status": "failed",
        "project_name": f"pypi:{package}",
        "error": None,
        "trace_path": None,
        "run_id": None,
    }

    from playwright.sync_api import sync_playwright

    def _check_cancel() -> None:
        if cancel is not None:
            cancel.check()

    recorder = TraceRecorder(trace_dir=trace_dir)
    result["run_id"] = recorder.run_id
    recorder.record("run_started",
                    evidence=[f"url={target_url}", f"package={package}"])
    stages: "list[dict]" = []

    def _note_stage(page, name: str, extra=None) -> None:
        state = pypi_adapter.STAGE_READERS[name](page)
        if extra:
            state = {**state, **extra}
        try:
            page_url = page.url
        except Exception:  # noqa: BLE001 — duck-typed property
            page_url = ""
        stages.append({"stage": name,
                       "url": page_url if isinstance(page_url, str) else "",
                       "captured_at": pypi_adapter.utcnow(),
                       "state": state})
        pypi_adapter.write_stages(trace_dir, recorder.run_id, stages)
        recorder.record("stage_state", evidence=[f"stage={name}"])

    def _attach_screenshot(page) -> None:
        shot = capture_failure_screenshot(
            page, recorder.run_id, Path(trace_dir) / "screenshots"
        )
        if shot is not None:
            recorder.events[-1]["evidence_references"].append(
                f"screenshot={shot}"
            )
        else:
            recorder.events[-1]["evidence_references"].append(
                "screenshot_capture_failed"
            )

    def _finish_trace(terminal: str, exc=None) -> None:
        try:
            path = recorder.finish(
                terminal,
                error_details=(
                    {
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "cause_type": (
                            type(exc.__cause__).__name__
                            if exc and exc.__cause__
                            else None
                        ),
                        "cause_message": (
                            str(exc.__cause__) if exc and exc.__cause__ else None
                        ),
                    }
                    if exc
                    else None
                ),
            )
            result["trace_path"] = str(path)
        except TraceWriteError as write_exc:
            result["success"] = False
            result["status"] = "failed"
            result["cancelled"] = False
            result["error"] = f"TraceWriteError: {write_exc}"
            result["trace_path"] = None
            recorder.write_error = str(write_exc)

    def _bounded(action: str, func, page) -> None:
        _check_cancel()
        recorder.action_attempted(action)
        try:
            execute_with_retry(
                action,
                func,
                policy=DEFAULT_POLICY,
                cancellation_token=cancel,
            )
            recorder.action_succeeded(action)
        except RunCancelledError:
            raise
        except Exception as exc:
            recorder.action_failed(action, exc)
            _attach_screenshot(page)
            raise

    with sync_playwright() as playwright:
        if browser_factory is None:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
        else:
            browser, context, page = browser_factory(playwright)

        try:
            _bounded(
                ActionType.NAVIGATE.value,
                lambda: page.goto(target_url),
                page,
            )
            _note_stage(page, "package")
            _check_cancel()
            _verify_pypi_package(stages, package, recorder, page,
                                 _attach_screenshot)

            result["success"] = True
            result["status"] = "succeeded"
            _finish_trace("succeeded")

        except RunCancelledError as exc:
            result["success"] = False
            result["cancelled"] = True
            result["status"] = "cancelled"
            result["error"] = f"RunCancelledError: {exc}"
            _finish_trace("cancelled", exc=exc)

        except Exception as exc:
            result["success"] = False
            result["cancelled"] = False
            result["status"] = "failed"
            if exc.__cause__ is not None:
                result["error"] = (
                    f"{type(exc).__name__}: {exc} "
                    f"(caused by {type(exc.__cause__).__name__}: {exc.__cause__})"
                )
            else:
                result["error"] = f"{type(exc).__name__}: {exc}"
            _finish_trace("failed", exc=exc)

        finally:
            if observe is not None:
                try:
                    result["observation"] = observe(page)
                    result["observation_error"] = None
                except Exception as exc:  # noqa: BLE001 — reported, not raised
                    result["observation"] = None
                    result["observation_error"] = (
                        f"{type(exc).__name__}: {exc}"
                    )
            _close_browser(context, browser, trace_dir, recorder.run_id)

    return result


def _verify_bbc_section(stages, section, recorder, page,
                        attach_screenshot) -> None:
    """Gate success on the served section and recorded headlines."""
    states = bbc_adapter.stage_states(stages)
    found = states.get("section", {})
    want_label = bbc_adapter.SECTION_LABELS.get(section, "")
    if not want_label or str(found.get("heading") or "") != want_label:
        exc = RuntimeError(f"BBC section {section!r} was not served")
        recorder.verification_failed("section_confirmed", exc)
        attach_screenshot(page)
        raise exc
    headlines = found.get("headlines")
    texts = [h for h in headlines
             if isinstance(h, str) and h.strip()] \
        if isinstance(headlines, list) else []
    if not texts:
        exc = RuntimeError(
            f"BBC section {section!r} recorded no headlines")
        recorder.verification_failed("section_confirmed", exc)
        attach_screenshot(page)
        raise exc
    recorder.verification_passed("section_confirmed")


def run_bbc_headlines(
    section: str,
    *,
    url: Optional[str] = None,
    trace_dir: Optional[Path] = None,
    cancel: Optional[CancellationToken] = None,
    observe: Optional[Callable[[Any], Any]] = None,
    browser_factory: Optional[Callable[[Any], Tuple[Any, Any, Any]]] = None,
) -> dict:
    """Open one BBC section front and record its headlines (read-only).

    Same contract as the other drivers with a single stage:
    section. The section URL is deterministic in the section key;
    an unserved section or an empty headline list fails honestly.
    """
    target_url = url if url is not None else bbc_adapter.section_url(section)
    bbc_adapter.assert_approved_url(target_url)
    trace_dir = trace_dir if trace_dir is not None else DEFAULT_TRACE_DIR
    result = {
        "success": False,
        "cancelled": False,
        "status": "failed",
        "project_name": f"bbc:{section}",
        "error": None,
        "trace_path": None,
        "run_id": None,
    }

    from playwright.sync_api import sync_playwright

    def _check_cancel() -> None:
        if cancel is not None:
            cancel.check()

    recorder = TraceRecorder(trace_dir=trace_dir)
    result["run_id"] = recorder.run_id
    recorder.record("run_started",
                    evidence=[f"url={target_url}", f"section={section}"])
    stages: "list[dict]" = []

    def _note_stage(page, name: str, extra=None) -> None:
        state = bbc_adapter.STAGE_READERS[name](page)
        if extra:
            state = {**state, **extra}
        try:
            page_url = page.url
        except Exception:  # noqa: BLE001 — duck-typed property
            page_url = ""
        stages.append({"stage": name,
                       "url": page_url if isinstance(page_url, str) else "",
                       "captured_at": bbc_adapter.utcnow(),
                       "state": state})
        bbc_adapter.write_stages(trace_dir, recorder.run_id, stages)
        recorder.record("stage_state", evidence=[f"stage={name}"])

    def _attach_screenshot(page) -> None:
        shot = capture_failure_screenshot(
            page, recorder.run_id, Path(trace_dir) / "screenshots"
        )
        if shot is not None:
            recorder.events[-1]["evidence_references"].append(
                f"screenshot={shot}"
            )
        else:
            recorder.events[-1]["evidence_references"].append(
                "screenshot_capture_failed"
            )

    def _finish_trace(terminal: str, exc=None) -> None:
        try:
            path = recorder.finish(
                terminal,
                error_details=(
                    {
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "cause_type": (
                            type(exc.__cause__).__name__
                            if exc and exc.__cause__
                            else None
                        ),
                        "cause_message": (
                            str(exc.__cause__) if exc and exc.__cause__ else None
                        ),
                    }
                    if exc
                    else None
                ),
            )
            result["trace_path"] = str(path)
        except TraceWriteError as write_exc:
            result["success"] = False
            result["status"] = "failed"
            result["cancelled"] = False
            result["error"] = f"TraceWriteError: {write_exc}"
            result["trace_path"] = None
            recorder.write_error = str(write_exc)

    def _bounded(action: str, func, page) -> None:
        _check_cancel()
        recorder.action_attempted(action)
        try:
            execute_with_retry(
                action,
                func,
                policy=DEFAULT_POLICY,
                cancellation_token=cancel,
            )
            recorder.action_succeeded(action)
        except RunCancelledError:
            raise
        except Exception as exc:
            recorder.action_failed(action, exc)
            _attach_screenshot(page)
            raise

    with sync_playwright() as playwright:
        if browser_factory is None:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
        else:
            browser, context, page = browser_factory(playwright)

        try:
            _bounded(
                ActionType.NAVIGATE.value,
                lambda: page.goto(target_url),
                page,
            )
            _note_stage(page, "section")
            _check_cancel()
            _verify_bbc_section(stages, section, recorder, page,
                                _attach_screenshot)

            result["success"] = True
            result["status"] = "succeeded"
            _finish_trace("succeeded")

        except RunCancelledError as exc:
            result["success"] = False
            result["cancelled"] = True
            result["status"] = "cancelled"
            result["error"] = f"RunCancelledError: {exc}"
            _finish_trace("cancelled", exc=exc)

        except Exception as exc:
            result["success"] = False
            result["cancelled"] = False
            result["status"] = "failed"
            if exc.__cause__ is not None:
                result["error"] = (
                    f"{type(exc).__name__}: {exc} "
                    f"(caused by {type(exc.__cause__).__name__}: {exc.__cause__})"
                )
            else:
                result["error"] = f"{type(exc).__name__}: {exc}"
            _finish_trace("failed", exc=exc)

        finally:
            if observe is not None:
                try:
                    result["observation"] = observe(page)
                    result["observation_error"] = None
                except Exception as exc:  # noqa: BLE001 — reported, not raised
                    result["observation"] = None
                    result["observation_error"] = (
                        f"{type(exc).__name__}: {exc}"
                    )
            _close_browser(context, browser, trace_dir, recorder.run_id)

    return result


def _verify_github_profile(stages, username, recorder, page,
                           attach_screenshot) -> None:
    """Gate success on a captured handle matching the username."""
    states = github_adapter.stage_states(stages)
    profile = states.get("profile", {})
    nickname = str(profile.get("nickname") or "").strip()
    if not nickname or nickname.lower() != username.strip().lower():
        exc = RuntimeError(f"no GitHub profile for {username!r}")
        recorder.verification_failed("profile_confirmed", exc)
        attach_screenshot(page)
        raise exc
    if not str(profile.get("name") or "").strip():
        exc = RuntimeError(
            f"GitHub profile {username!r} has no display name")
        recorder.verification_failed("profile_confirmed", exc)
        attach_screenshot(page)
        raise exc
    recorder.verification_passed("profile_confirmed")


def run_github_profile(
    username: str,
    *,
    url: Optional[str] = None,
    trace_dir: Optional[Path] = None,
    cancel: Optional[CancellationToken] = None,
    observe: Optional[Callable[[Any], Any]] = None,
    browser_factory: Optional[Callable[[Any], Tuple[Any, Any, Any]]] = None,
) -> dict:
    """Open one GitHub public profile and verify it (read-only).

    Same contract as the other drivers with a single stage:
    profile. The profile URL is deterministic in the username;
    unknown names render a 404 with no profile handle and fail
    honestly.
    """
    target_url = (url if url is not None
                  else github_adapter.profile_url(username))
    github_adapter.assert_approved_url(target_url)
    trace_dir = trace_dir if trace_dir is not None else DEFAULT_TRACE_DIR
    result = {
        "success": False,
        "cancelled": False,
        "status": "failed",
        "project_name": f"github:{username}",
        "error": None,
        "trace_path": None,
        "run_id": None,
    }

    from playwright.sync_api import sync_playwright

    def _check_cancel() -> None:
        if cancel is not None:
            cancel.check()

    recorder = TraceRecorder(trace_dir=trace_dir)
    result["run_id"] = recorder.run_id
    recorder.record("run_started",
                    evidence=[f"url={target_url}", f"username={username}"])
    stages: "list[dict]" = []

    def _note_stage(page, name: str, extra=None) -> None:
        state = github_adapter.STAGE_READERS[name](page)
        if extra:
            state = {**state, **extra}
        try:
            page_url = page.url
        except Exception:  # noqa: BLE001 — duck-typed property
            page_url = ""
        stages.append({"stage": name,
                       "url": page_url if isinstance(page_url, str) else "",
                       "captured_at": github_adapter.utcnow(),
                       "state": state})
        github_adapter.write_stages(trace_dir, recorder.run_id, stages)
        recorder.record("stage_state", evidence=[f"stage={name}"])

    def _attach_screenshot(page) -> None:
        shot = capture_failure_screenshot(
            page, recorder.run_id, Path(trace_dir) / "screenshots"
        )
        if shot is not None:
            recorder.events[-1]["evidence_references"].append(
                f"screenshot={shot}"
            )
        else:
            recorder.events[-1]["evidence_references"].append(
                "screenshot_capture_failed"
            )

    def _finish_trace(terminal: str, exc=None) -> None:
        try:
            path = recorder.finish(
                terminal,
                error_details=(
                    {
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "cause_type": (
                            type(exc.__cause__).__name__
                            if exc and exc.__cause__
                            else None
                        ),
                        "cause_message": (
                            str(exc.__cause__) if exc and exc.__cause__ else None
                        ),
                    }
                    if exc
                    else None
                ),
            )
            result["trace_path"] = str(path)
        except TraceWriteError as write_exc:
            result["success"] = False
            result["status"] = "failed"
            result["cancelled"] = False
            result["error"] = f"TraceWriteError: {write_exc}"
            result["trace_path"] = None
            recorder.write_error = str(write_exc)

    def _bounded(action: str, func, page) -> None:
        _check_cancel()
        recorder.action_attempted(action)
        try:
            execute_with_retry(
                action,
                func,
                policy=DEFAULT_POLICY,
                cancellation_token=cancel,
            )
            recorder.action_succeeded(action)
        except RunCancelledError:
            raise
        except Exception as exc:
            recorder.action_failed(action, exc)
            _attach_screenshot(page)
            raise

    with sync_playwright() as playwright:
        if browser_factory is None:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
        else:
            browser, context, page = browser_factory(playwright)

        try:
            _bounded(
                ActionType.NAVIGATE.value,
                lambda: page.goto(target_url,
                                      wait_until="domcontentloaded"),
                page,
            )
            _note_stage(page, "profile")
            _check_cancel()
            _verify_github_profile(stages, username, recorder, page,
                                   _attach_screenshot)

            result["success"] = True
            result["status"] = "succeeded"
            _finish_trace("succeeded")

        except RunCancelledError as exc:
            result["success"] = False
            result["cancelled"] = True
            result["status"] = "cancelled"
            result["error"] = f"RunCancelledError: {exc}"
            _finish_trace("cancelled", exc=exc)

        except Exception as exc:
            result["success"] = False
            result["cancelled"] = False
            result["status"] = "failed"
            if exc.__cause__ is not None:
                result["error"] = (
                    f"{type(exc).__name__}: {exc} "
                    f"(caused by {type(exc.__cause__).__name__}: {exc.__cause__})"
                )
            else:
                result["error"] = f"{type(exc).__name__}: {exc}"
            _finish_trace("failed", exc=exc)

        finally:
            if observe is not None:
                try:
                    result["observation"] = observe(page)
                    result["observation_error"] = None
                except Exception as exc:  # noqa: BLE001 — reported, not raised
                    result["observation"] = None
                    result["observation_error"] = (
                        f"{type(exc).__name__}: {exc}"
                    )
            _close_browser(context, browser, trace_dir, recorder.run_id)

    return result


def _verify_crates_crate(stages, crate, recorder, page,
                         attach_screenshot) -> None:
    """Gate success on a captured header naming the crate."""
    states = crates_adapter.stage_states(stages)
    found = states.get("crate", {})
    want = crate.strip().lower()
    got = str(found.get("name") or "").strip().lower()
    if found.get("missing") or not got or got != want:
        exc = RuntimeError(f"no crates.io crate for {crate!r}")
        recorder.verification_failed("crate_confirmed", exc)
        attach_screenshot(page)
        raise exc
    if not found.get("version") or len(str(found.get("summary") or "")) < 10:
        exc = RuntimeError(
            f"crates.io crate {crate!r} lacks version or summary")
        recorder.verification_failed("crate_confirmed", exc)
        attach_screenshot(page)
        raise exc
    recorder.verification_passed("crate_confirmed")


def run_crates_lookup(
    crate: str,
    *,
    url: Optional[str] = None,
    trace_dir: Optional[Path] = None,
    cancel: Optional[CancellationToken] = None,
    observe: Optional[Callable[[Any], Any]] = None,
    browser_factory: Optional[Callable[[Any], Tuple[Any, Any, Any]]] = None,
) -> dict:
    """Open one crates.io crate page and verify it (read-only).

    Same contract as the other drivers with a single stage:
    crate. The crate URL is deterministic in the name; unknown
    names render a "not found" page and fail honestly.
    """
    target_url = url if url is not None else crates_adapter.crate_url(crate)
    crates_adapter.assert_approved_url(target_url)
    trace_dir = trace_dir if trace_dir is not None else DEFAULT_TRACE_DIR
    result = {
        "success": False,
        "cancelled": False,
        "status": "failed",
        "project_name": f"crates:{crate}",
        "error": None,
        "trace_path": None,
        "run_id": None,
    }

    from playwright.sync_api import sync_playwright

    def _check_cancel() -> None:
        if cancel is not None:
            cancel.check()

    recorder = TraceRecorder(trace_dir=trace_dir)
    result["run_id"] = recorder.run_id
    recorder.record("run_started",
                    evidence=[f"url={target_url}", f"crate={crate}"])
    stages: "list[dict]" = []

    def _note_stage(page, name: str, extra=None) -> None:
        state = crates_adapter.STAGE_READERS[name](page)
        if extra:
            state = {**state, **extra}
        try:
            page_url = page.url
        except Exception:  # noqa: BLE001 — duck-typed property
            page_url = ""
        stages.append({"stage": name,
                       "url": page_url if isinstance(page_url, str) else "",
                       "captured_at": crates_adapter.utcnow(),
                       "state": state})
        crates_adapter.write_stages(trace_dir, recorder.run_id, stages)
        recorder.record("stage_state", evidence=[f"stage={name}"])

    def _attach_screenshot(page) -> None:
        shot = capture_failure_screenshot(
            page, recorder.run_id, Path(trace_dir) / "screenshots"
        )
        if shot is not None:
            recorder.events[-1]["evidence_references"].append(
                f"screenshot={shot}"
            )
        else:
            recorder.events[-1]["evidence_references"].append(
                "screenshot_capture_failed"
            )

    def _finish_trace(terminal: str, exc=None) -> None:
        try:
            path = recorder.finish(
                terminal,
                error_details=(
                    {
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "cause_type": (
                            type(exc.__cause__).__name__
                            if exc and exc.__cause__
                            else None
                        ),
                        "cause_message": (
                            str(exc.__cause__) if exc and exc.__cause__ else None
                        ),
                    }
                    if exc
                    else None
                ),
            )
            result["trace_path"] = str(path)
        except TraceWriteError as write_exc:
            result["success"] = False
            result["status"] = "failed"
            result["cancelled"] = False
            result["error"] = f"TraceWriteError: {write_exc}"
            result["trace_path"] = None
            recorder.write_error = str(write_exc)

    def _bounded(action: str, func, page) -> None:
        _check_cancel()
        recorder.action_attempted(action)
        try:
            execute_with_retry(
                action,
                func,
                policy=DEFAULT_POLICY,
                cancellation_token=cancel,
            )
            recorder.action_succeeded(action)
        except RunCancelledError:
            raise
        except Exception as exc:
            recorder.action_failed(action, exc)
            _attach_screenshot(page)
            raise

    with sync_playwright() as playwright:
        if browser_factory is None:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
        else:
            browser, context, page = browser_factory(playwright)

        try:
            _bounded(
                ActionType.NAVIGATE.value,
                lambda: page.goto(target_url),
                page,
            )
            _note_stage(page, "crate")
            _check_cancel()
            _verify_crates_crate(stages, crate, recorder, page,
                                 _attach_screenshot)

            result["success"] = True
            result["status"] = "succeeded"
            _finish_trace("succeeded")

        except RunCancelledError as exc:
            result["success"] = False
            result["cancelled"] = True
            result["status"] = "cancelled"
            result["error"] = f"RunCancelledError: {exc}"
            _finish_trace("cancelled", exc=exc)

        except Exception as exc:
            result["success"] = False
            result["cancelled"] = False
            result["status"] = "failed"
            if exc.__cause__ is not None:
                result["error"] = (
                    f"{type(exc).__name__}: {exc} "
                    f"(caused by {type(exc.__cause__).__name__}: {exc.__cause__})"
                )
            else:
                result["error"] = f"{type(exc).__name__}: {exc}"
            _finish_trace("failed", exc=exc)

        finally:
            if observe is not None:
                try:
                    result["observation"] = observe(page)
                    result["observation_error"] = None
                except Exception as exc:  # noqa: BLE001 — reported, not raised
                    result["observation"] = None
                    result["observation_error"] = (
                        f"{type(exc).__name__}: {exc}"
                    )
            _close_browser(context, browser, trace_dir, recorder.run_id)

    return result


def _verify_weather_forecast(stages, city, recorder, page,
                             attach_screenshot) -> None:
    """Gate success on the served city and recorded temperatures."""
    states = weather_adapter.stage_states(stages)
    found = states.get("forecast", {})
    entry = weather_adapter.CITIES.get(city, ("", ""))
    if not entry[1] or not str(found.get("heading") or "").startswith(
            entry[1]):
        exc = RuntimeError(f"BBC Weather city {city!r} was not served")
        recorder.verification_failed("forecast_confirmed", exc)
        attach_screenshot(page)
        raise exc
    temps = found.get("temps")
    texts = [t for t in temps if isinstance(t, str) and t.strip()] \
        if isinstance(temps, list) else []
    if not texts:
        exc = RuntimeError(
            f"BBC Weather for {city!r} recorded no temperatures")
        recorder.verification_failed("forecast_confirmed", exc)
        attach_screenshot(page)
        raise exc
    recorder.verification_passed("forecast_confirmed")


def run_bbc_weather(
    city: str,
    *,
    url: Optional[str] = None,
    trace_dir: Optional[Path] = None,
    cancel: Optional[CancellationToken] = None,
    observe: Optional[Callable[[Any], Any]] = None,
    browser_factory: Optional[Callable[[Any], Tuple[Any, Any, Any]]] = None,
) -> dict:
    """Open one BBC Weather city page and record it (read-only).

    Same contract as the other drivers with a single stage:
    forecast. The city URL is deterministic in the city key; an
    unserved city or an empty temperature list fails honestly.
    """
    target_url = url if url is not None else weather_adapter.city_url(city)
    weather_adapter.assert_approved_url(target_url)
    trace_dir = trace_dir if trace_dir is not None else DEFAULT_TRACE_DIR
    result = {
        "success": False,
        "cancelled": False,
        "status": "failed",
        "project_name": f"weather:{city}",
        "error": None,
        "trace_path": None,
        "run_id": None,
    }

    from playwright.sync_api import sync_playwright

    def _check_cancel() -> None:
        if cancel is not None:
            cancel.check()

    recorder = TraceRecorder(trace_dir=trace_dir)
    result["run_id"] = recorder.run_id
    recorder.record("run_started",
                    evidence=[f"url={target_url}", f"city={city}"])
    stages: "list[dict]" = []

    def _note_stage(page, name: str, extra=None) -> None:
        state = weather_adapter.STAGE_READERS[name](page)
        if extra:
            state = {**state, **extra}
        try:
            page_url = page.url
        except Exception:  # noqa: BLE001 — duck-typed property
            page_url = ""
        stages.append({"stage": name,
                       "url": page_url if isinstance(page_url, str) else "",
                       "captured_at": weather_adapter.utcnow(),
                       "state": state})
        weather_adapter.write_stages(trace_dir, recorder.run_id, stages)
        recorder.record("stage_state", evidence=[f"stage={name}"])

    def _attach_screenshot(page) -> None:
        shot = capture_failure_screenshot(
            page, recorder.run_id, Path(trace_dir) / "screenshots"
        )
        if shot is not None:
            recorder.events[-1]["evidence_references"].append(
                f"screenshot={shot}"
            )
        else:
            recorder.events[-1]["evidence_references"].append(
                "screenshot_capture_failed"
            )

    def _finish_trace(terminal: str, exc=None) -> None:
        try:
            path = recorder.finish(
                terminal,
                error_details=(
                    {
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "cause_type": (
                            type(exc.__cause__).__name__
                            if exc and exc.__cause__
                            else None
                        ),
                        "cause_message": (
                            str(exc.__cause__) if exc and exc.__cause__ else None
                        ),
                    }
                    if exc
                    else None
                ),
            )
            result["trace_path"] = str(path)
        except TraceWriteError as write_exc:
            result["success"] = False
            result["status"] = "failed"
            result["cancelled"] = False
            result["error"] = f"TraceWriteError: {write_exc}"
            result["trace_path"] = None
            recorder.write_error = str(write_exc)

    def _bounded(action: str, func, page) -> None:
        _check_cancel()
        recorder.action_attempted(action)
        try:
            execute_with_retry(
                action,
                func,
                policy=DEFAULT_POLICY,
                cancellation_token=cancel,
            )
            recorder.action_succeeded(action)
        except RunCancelledError:
            raise
        except Exception as exc:
            recorder.action_failed(action, exc)
            _attach_screenshot(page)
            raise

    with sync_playwright() as playwright:
        if browser_factory is None:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
        else:
            browser, context, page = browser_factory(playwright)

        try:
            _bounded(
                ActionType.NAVIGATE.value,
                lambda: page.goto(target_url),
                page,
            )
            _note_stage(page, "forecast")
            _check_cancel()
            _verify_weather_forecast(stages, city, recorder, page,
                                     _attach_screenshot)

            result["success"] = True
            result["status"] = "succeeded"
            _finish_trace("succeeded")

        except RunCancelledError as exc:
            result["success"] = False
            result["cancelled"] = True
            result["status"] = "cancelled"
            result["error"] = f"RunCancelledError: {exc}"
            _finish_trace("cancelled", exc=exc)

        except Exception as exc:
            result["success"] = False
            result["cancelled"] = False
            result["status"] = "failed"
            if exc.__cause__ is not None:
                result["error"] = (
                    f"{type(exc).__name__}: {exc} "
                    f"(caused by {type(exc.__cause__).__name__}: {exc.__cause__})"
                )
            else:
                result["error"] = f"{type(exc).__name__}: {exc}"
            _finish_trace("failed", exc=exc)

        finally:
            if observe is not None:
                try:
                    result["observation"] = observe(page)
                    result["observation_error"] = None
                except Exception as exc:  # noqa: BLE001 — reported, not raised
                    result["observation"] = None
                    result["observation_error"] = (
                        f"{type(exc).__name__}: {exc}"
                    )
            _close_browser(context, browser, trace_dir, recorder.run_id)

    return result


def _verify_github_results(stages, query, recorder, page,
                           attach_screenshot) -> None:
    """Gate success on served results with recorded repo names."""
    states = gsearch_adapter.stage_states(stages)
    found = states.get("search", {})
    if not found.get("served") or int(found.get("count") or 0) < 1:
        exc = RuntimeError(
            f"GitHub search for {query!r} returned no repositories")
        recorder.verification_failed("results_confirmed", exc)
        attach_screenshot(page)
        raise exc
    titles = found.get("titles")
    texts = [t for t in titles if isinstance(t, str) and t.strip()] \
        if isinstance(titles, list) else []
    if not texts:
        exc = RuntimeError(
            f"GitHub search for {query!r} recorded no repo names")
        recorder.verification_failed("results_confirmed", exc)
        attach_screenshot(page)
        raise exc
    recorder.verification_passed("results_confirmed")


def run_github_search(
    query: str,
    *,
    url: Optional[str] = None,
    trace_dir: Optional[Path] = None,
    cancel: Optional[CancellationToken] = None,
    observe: Optional[Callable[[Any], Any]] = None,
    browser_factory: Optional[Callable[[Any], Tuple[Any, Any, Any]]] = None,
) -> dict:
    """Search GitHub repositories and record the results (read-only).

    Same contract as the other drivers with a single stage:
    search. The search URL is deterministic in the query; a query
    with no repositories fails honestly.
    """
    target_url = url if url is not None else gsearch_adapter.search_url(query)
    gsearch_adapter.assert_approved_url(target_url)
    trace_dir = trace_dir if trace_dir is not None else DEFAULT_TRACE_DIR
    result = {
        "success": False,
        "cancelled": False,
        "status": "failed",
        "project_name": f"ghsearch:{query}",
        "error": None,
        "trace_path": None,
        "run_id": None,
    }

    from playwright.sync_api import sync_playwright

    def _check_cancel() -> None:
        if cancel is not None:
            cancel.check()

    recorder = TraceRecorder(trace_dir=trace_dir)
    result["run_id"] = recorder.run_id
    recorder.record("run_started",
                    evidence=[f"url={target_url}", f"query={query}"])
    stages: "list[dict]" = []

    def _note_stage(page, name: str, extra=None) -> None:
        state = gsearch_adapter.STAGE_READERS[name](page)
        if extra:
            state = {**state, **extra}
        try:
            page_url = page.url
        except Exception:  # noqa: BLE001 — duck-typed property
            page_url = ""
        stages.append({"stage": name,
                       "url": page_url if isinstance(page_url, str) else "",
                       "captured_at": gsearch_adapter.utcnow(),
                       "state": state})
        gsearch_adapter.write_stages(trace_dir, recorder.run_id, stages)
        recorder.record("stage_state", evidence=[f"stage={name}"])

    def _attach_screenshot(page) -> None:
        shot = capture_failure_screenshot(
            page, recorder.run_id, Path(trace_dir) / "screenshots"
        )
        if shot is not None:
            recorder.events[-1]["evidence_references"].append(
                f"screenshot={shot}"
            )
        else:
            recorder.events[-1]["evidence_references"].append(
                "screenshot_capture_failed"
            )

    def _finish_trace(terminal: str, exc=None) -> None:
        try:
            path = recorder.finish(
                terminal,
                error_details=(
                    {
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "cause_type": (
                            type(exc.__cause__).__name__
                            if exc and exc.__cause__
                            else None
                        ),
                        "cause_message": (
                            str(exc.__cause__) if exc and exc.__cause__ else None
                        ),
                    }
                    if exc
                    else None
                ),
            )
            result["trace_path"] = str(path)
        except TraceWriteError as write_exc:
            result["success"] = False
            result["status"] = "failed"
            result["cancelled"] = False
            result["error"] = f"TraceWriteError: {write_exc}"
            result["trace_path"] = None
            recorder.write_error = str(write_exc)

    def _bounded(action: str, func, page) -> None:
        _check_cancel()
        recorder.action_attempted(action)
        try:
            execute_with_retry(
                action,
                func,
                policy=DEFAULT_POLICY,
                cancellation_token=cancel,
            )
            recorder.action_succeeded(action)
        except RunCancelledError:
            raise
        except Exception as exc:
            recorder.action_failed(action, exc)
            _attach_screenshot(page)
            raise

    with sync_playwright() as playwright:
        if browser_factory is None:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
        else:
            browser, context, page = browser_factory(playwright)

        try:
            _bounded(
                ActionType.NAVIGATE.value,
                lambda: page.goto(target_url,
                                      wait_until="domcontentloaded"),
                page,
            )
            _note_stage(page, "search")
            _check_cancel()
            _verify_github_results(stages, query, recorder, page,
                                   _attach_screenshot)

            result["success"] = True
            result["status"] = "succeeded"
            _finish_trace("succeeded")

        except RunCancelledError as exc:
            result["success"] = False
            result["cancelled"] = True
            result["status"] = "cancelled"
            result["error"] = f"RunCancelledError: {exc}"
            _finish_trace("cancelled", exc=exc)

        except Exception as exc:
            result["success"] = False
            result["cancelled"] = False
            result["status"] = "failed"
            if exc.__cause__ is not None:
                result["error"] = (
                    f"{type(exc).__name__}: {exc} "
                    f"(caused by {type(exc.__cause__).__name__}: {exc.__cause__})"
                )
            else:
                result["error"] = f"{type(exc).__name__}: {exc}"
            _finish_trace("failed", exc=exc)

        finally:
            if observe is not None:
                try:
                    result["observation"] = observe(page)
                    result["observation_error"] = None
                except Exception as exc:  # noqa: BLE001 — reported, not raised
                    result["observation"] = None
                    result["observation_error"] = (
                        f"{type(exc).__name__}: {exc}"
                    )
            _close_browser(context, browser, trace_dir, recorder.run_id)

    return result


def _verify_steam_game(stages, query, pick, recorder, page,
                       attach_screenshot) -> None:
    """Gate success on the picked game, its name, and its price."""
    states = steam_adapter.stage_states(stages)
    search = states.get("search", {})
    results = search.get("results")
    if not isinstance(results, list):
        results = []
    if len(results) < pick:
        exc = RuntimeError(
            f"search returned {len(results)} games, cannot pick #{pick}")
        recorder.verification_failed("game_confirmed", exc)
        attach_screenshot(page)
        raise exc
    picked = results[pick - 1].get("name") or ""
    game = states.get("game", {})
    name = str(game.get("name") or "")
    if not name or name != picked:
        exc = RuntimeError(
            "Steam game page does not name the picked game "
            f"(page={name!r}, picked {picked!r})")
        recorder.verification_failed("game_confirmed", exc)
        attach_screenshot(page)
        raise exc
    if not str(game.get("price") or ""):
        exc = RuntimeError(f"Steam game {picked!r} shows no price")
        recorder.verification_failed("game_confirmed", exc)
        attach_screenshot(page)
        raise exc
    recorder.verification_passed("game_confirmed")


def run_steam_price(
    query: str,
    pick: int,
    *,
    url: Optional[str] = None,
    trace_dir: Optional[Path] = None,
    cancel: Optional[CancellationToken] = None,
    observe: Optional[Callable[[Any], Any]] = None,
    browser_factory: Optional[Callable[[Any], Tuple[Any, Any, Any]]] = None,
) -> dict:
    """Search the Steam store, open one game, record its price (read-only).

    Same contract as the Wikipedia driver across two stages:
    search, game. Nothing is bought, no account is used, and no
    age gate is ever submitted: a gated or missing game page
    fails honestly.
    """
    target_url = url if url is not None else steam_adapter.HOME_URL
    steam_adapter.assert_approved_url(target_url)
    trace_dir = trace_dir if trace_dir is not None else DEFAULT_TRACE_DIR
    result = {
        "success": False,
        "cancelled": False,
        "status": "failed",
        "project_name": f"steam:{query}#{pick}",
        "error": None,
        "trace_path": None,
        "run_id": None,
    }

    from playwright.sync_api import sync_playwright

    def _check_cancel() -> None:
        if cancel is not None:
            cancel.check()

    recorder = TraceRecorder(trace_dir=trace_dir)
    result["run_id"] = recorder.run_id
    recorder.record(
        "run_started",
        evidence=[f"url={target_url}", f"query={query}", f"pick={pick}"],
    )
    stages: "list[dict]" = []

    def _note_stage(page, name: str, extra=None) -> None:
        state = steam_adapter.STAGE_READERS[name](page)
        if extra:
            state = {**state, **extra}
        try:
            page_url = page.url
        except Exception:  # noqa: BLE001 — duck-typed property
            page_url = ""
        stages.append({"stage": name,
                       "url": page_url if isinstance(page_url, str) else "",
                       "captured_at": steam_adapter.utcnow(),
                       "state": state})
        steam_adapter.write_stages(trace_dir, recorder.run_id, stages)
        recorder.record("stage_state", evidence=[f"stage={name}"])

    def _attach_screenshot(page) -> None:
        shot = capture_failure_screenshot(
            page, recorder.run_id, Path(trace_dir) / "screenshots"
        )
        if shot is not None:
            recorder.events[-1]["evidence_references"].append(
                f"screenshot={shot}"
            )
        else:
            recorder.events[-1]["evidence_references"].append(
                "screenshot_capture_failed"
            )

    def _finish_trace(terminal: str, exc=None) -> None:
        try:
            path = recorder.finish(
                terminal,
                error_details=(
                    {
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "cause_type": (
                            type(exc.__cause__).__name__
                            if exc and exc.__cause__
                            else None
                        ),
                        "cause_message": (
                            str(exc.__cause__) if exc and exc.__cause__ else None
                        ),
                    }
                    if exc
                    else None
                ),
            )
            result["trace_path"] = str(path)
        except TraceWriteError as write_exc:
            result["success"] = False
            result["status"] = "failed"
            result["cancelled"] = False
            result["error"] = f"TraceWriteError: {write_exc}"
            result["trace_path"] = None
            recorder.write_error = str(write_exc)

    def _bounded(action: str, func, page) -> None:
        _check_cancel()
        recorder.action_attempted(action)
        try:
            execute_with_retry(
                action,
                func,
                policy=DEFAULT_POLICY,
                cancellation_token=cancel,
            )
            recorder.action_succeeded(action)
        except RunCancelledError:
            raise
        except Exception as exc:
            recorder.action_failed(action, exc)
            _attach_screenshot(page)
            raise

    with sync_playwright() as playwright:
        if browser_factory is None:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
        else:
            browser, context, page = browser_factory(playwright)

        try:
            search_target = steam_adapter.search_url(query)
            steam_adapter.assert_approved_url(search_target)
            _bounded(
                ActionType.NAVIGATE.value,
                lambda: page.goto(search_target),
                page,
            )
            steam_adapter.wait_for_any(
                page, [steam_adapter.SEL_SEARCH_ROW],
                ACTION_TIMEOUT_MS)
            _note_stage(page, "search")
            found = steam_adapter.stage_states(stages).get("search", {})
            results = found.get("results") or []
            if len(results) < pick:
                exc = RuntimeError(
                    f"search returned {len(results)} games, "
                    f"cannot pick #{pick}")
                recorder.verification_failed("search_pick_available", exc)
                _attach_screenshot(page)
                raise exc
            picked_href = results[pick - 1].get("href") or ""
            game_target = (
                picked_href if picked_href.startswith("https://")
                else steam_adapter.APPROVED_ORIGIN + picked_href)
            steam_adapter.assert_approved_url(game_target)
            recorder.record(
                "pick_committed",
                evidence=[f"pick={pick}",
                          f"href={picked_href[:120]}"],
            )
            _bounded(
                ActionType.NAVIGATE.value,
                lambda: page.goto(game_target),
                page,
            )
            steam_adapter.wait_for_any(
                page, [steam_adapter.SEL_GAME_NAME],
                ACTION_TIMEOUT_MS)
            _note_stage(page, "game")
            _check_cancel()
            _verify_steam_game(stages, query, pick, recorder, page,
                               _attach_screenshot)

            result["success"] = True
            result["status"] = "succeeded"
            _finish_trace("succeeded")

        except RunCancelledError as exc:
            result["success"] = False
            result["cancelled"] = True
            result["status"] = "cancelled"
            result["error"] = f"RunCancelledError: {exc}"
            _finish_trace("cancelled", exc=exc)

        except Exception as exc:
            result["success"] = False
            result["cancelled"] = False
            result["status"] = "failed"
            if exc.__cause__ is not None:
                result["error"] = (
                    f"{type(exc).__name__}: {exc} "
                    f"(caused by {type(exc.__cause__).__name__}: {exc.__cause__})"
                )
            else:
                result["error"] = f"{type(exc).__name__}: {exc}"
            _finish_trace("failed", exc=exc)

        finally:
            if observe is not None:
                try:
                    result["observation"] = observe(page)
                    result["observation_error"] = None
                except Exception as exc:  # noqa: BLE001 — reported, not raised
                    result["observation"] = None
                    result["observation_error"] = (
                        f"{type(exc).__name__}: {exc}"
                    )
            _close_browser(context, browser, trace_dir, recorder.run_id)

    return result


def _verify_arxiv_results(stages, query, recorder, page,
                          attach_screenshot) -> None:
    """Gate success on served results with recorded paper titles."""
    states = arxiv_adapter.stage_states(stages)
    found = states.get("search", {})
    if int(found.get("count") or 0) < 1:
        exc = RuntimeError(
            f"arXiv search for {query!r} returned no papers")
        recorder.verification_failed("results_confirmed", exc)
        attach_screenshot(page)
        raise exc
    titles = found.get("titles")
    texts = [t for t in titles if isinstance(t, str) and t.strip()] \
        if isinstance(titles, list) else []
    if not texts:
        exc = RuntimeError(
            f"arXiv search for {query!r} recorded no paper titles")
        recorder.verification_failed("results_confirmed", exc)
        attach_screenshot(page)
        raise exc
    recorder.verification_passed("results_confirmed")


def run_arxiv_search(
    query: str,
    *,
    url: Optional[str] = None,
    trace_dir: Optional[Path] = None,
    cancel: Optional[CancellationToken] = None,
    observe: Optional[Callable[[Any], Any]] = None,
    browser_factory: Optional[Callable[[Any], Tuple[Any, Any, Any]]] = None,
) -> dict:
    """Search arXiv papers and record the results (read-only).

    Same contract as the other drivers with a single stage:
    search. The search URL is deterministic in the query; a query
    with no papers fails honestly.
    """
    target_url = url if url is not None else arxiv_adapter.search_url(query)
    arxiv_adapter.assert_approved_url(target_url)
    trace_dir = trace_dir if trace_dir is not None else DEFAULT_TRACE_DIR
    result = {
        "success": False,
        "cancelled": False,
        "status": "failed",
        "project_name": f"arxiv:{query}",
        "error": None,
        "trace_path": None,
        "run_id": None,
    }

    from playwright.sync_api import sync_playwright

    def _check_cancel() -> None:
        if cancel is not None:
            cancel.check()

    recorder = TraceRecorder(trace_dir=trace_dir)
    result["run_id"] = recorder.run_id
    recorder.record("run_started",
                    evidence=[f"url={target_url}", f"query={query}"])
    stages: "list[dict]" = []

    def _note_stage(page, name: str, extra=None) -> None:
        state = arxiv_adapter.STAGE_READERS[name](page)
        if extra:
            state = {**state, **extra}
        try:
            page_url = page.url
        except Exception:  # noqa: BLE001 — duck-typed property
            page_url = ""
        stages.append({"stage": name,
                       "url": page_url if isinstance(page_url, str) else "",
                       "captured_at": arxiv_adapter.utcnow(),
                       "state": state})
        arxiv_adapter.write_stages(trace_dir, recorder.run_id, stages)
        recorder.record("stage_state", evidence=[f"stage={name}"])

    def _attach_screenshot(page) -> None:
        shot = capture_failure_screenshot(
            page, recorder.run_id, Path(trace_dir) / "screenshots"
        )
        if shot is not None:
            recorder.events[-1]["evidence_references"].append(
                f"screenshot={shot}"
            )
        else:
            recorder.events[-1]["evidence_references"].append(
                "screenshot_capture_failed"
            )

    def _finish_trace(terminal: str, exc=None) -> None:
        try:
            path = recorder.finish(
                terminal,
                error_details=(
                    {
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "cause_type": (
                            type(exc.__cause__).__name__
                            if exc and exc.__cause__
                            else None
                        ),
                        "cause_message": (
                            str(exc.__cause__) if exc and exc.__cause__ else None
                        ),
                    }
                    if exc
                    else None
                ),
            )
            result["trace_path"] = str(path)
        except TraceWriteError as write_exc:
            result["success"] = False
            result["status"] = "failed"
            result["cancelled"] = False
            result["error"] = f"TraceWriteError: {write_exc}"
            result["trace_path"] = None
            recorder.write_error = str(write_exc)

    def _bounded(action: str, func, page) -> None:
        _check_cancel()
        recorder.action_attempted(action)
        try:
            execute_with_retry(
                action,
                func,
                policy=DEFAULT_POLICY,
                cancellation_token=cancel,
            )
            recorder.action_succeeded(action)
        except RunCancelledError:
            raise
        except Exception as exc:
            recorder.action_failed(action, exc)
            _attach_screenshot(page)
            raise

    with sync_playwright() as playwright:
        if browser_factory is None:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
        else:
            browser, context, page = browser_factory(playwright)

        try:
            _bounded(
                ActionType.NAVIGATE.value,
                lambda: page.goto(target_url),
                page,
            )
            _note_stage(page, "search")
            _check_cancel()
            _verify_arxiv_results(stages, query, recorder, page,
                                  _attach_screenshot)

            result["success"] = True
            result["status"] = "succeeded"
            _finish_trace("succeeded")

        except RunCancelledError as exc:
            result["success"] = False
            result["cancelled"] = True
            result["status"] = "cancelled"
            result["error"] = f"RunCancelledError: {exc}"
            _finish_trace("cancelled", exc=exc)

        except Exception as exc:
            result["success"] = False
            result["cancelled"] = False
            result["status"] = "failed"
            if exc.__cause__ is not None:
                result["error"] = (
                    f"{type(exc).__name__}: {exc} "
                    f"(caused by {type(exc.__cause__).__name__}: {exc.__cause__})"
                )
            else:
                result["error"] = f"{type(exc).__name__}: {exc}"
            _finish_trace("failed", exc=exc)

        finally:
            if observe is not None:
                try:
                    result["observation"] = observe(page)
                    result["observation_error"] = None
                except Exception as exc:  # noqa: BLE001 — reported, not raised
                    result["observation"] = None
                    result["observation_error"] = (
                        f"{type(exc).__name__}: {exc}"
                    )
            _close_browser(context, browser, trace_dir, recorder.run_id)

    return result


def _verify_so_results(stages, query, recorder, page,
                       attach_screenshot) -> None:
    """Gate success on served results with recorded titles."""
    states = so_adapter.stage_states(stages)
    found = states.get("search", {})
    if found.get("gate") is True:
        exc = RuntimeError(
            "Stack Overflow showed a bot gate; log in once via "
            "`python -m workbench.sessions login <profile>` and "
            "re-run with that profile")
        recorder.verification_failed("results_confirmed", exc)
        attach_screenshot(page)
        raise exc
    if int(found.get("count") or 0) < 1:
        exc = RuntimeError(
            f"Stack Overflow search for {query!r} returned no questions")
        recorder.verification_failed("results_confirmed", exc)
        attach_screenshot(page)
        raise exc
    titles = found.get("titles")
    texts = [t for t in titles if isinstance(t, str) and t.strip()] \
        if isinstance(titles, list) else []
    if not texts:
        exc = RuntimeError(
            f"Stack Overflow search for {query!r} recorded no titles")
        recorder.verification_failed("results_confirmed", exc)
        attach_screenshot(page)
        raise exc
    recorder.verification_passed("results_confirmed")


def run_so_search(
    query: str,
    *,
    url: Optional[str] = None,
    trace_dir: Optional[Path] = None,
    cancel: Optional[CancellationToken] = None,
    observe: Optional[Callable[[Any], Any]] = None,
    browser_factory: Optional[Callable[[Any], Tuple[Any, Any, Any]]] = None,
) -> dict:
    """Search Stack Overflow questions and record titles (read-only).

    Same contract as the other drivers with a single stage:
    search. Clean sessions usually meet a bot gate; that fails
    honestly with login instructions instead of empty results.
    """
    target_url = url if url is not None else so_adapter.search_url(query)
    so_adapter.assert_approved_url(target_url)
    trace_dir = trace_dir if trace_dir is not None else DEFAULT_TRACE_DIR
    result = {
        "success": False,
        "cancelled": False,
        "status": "failed",
        "project_name": f"so:{query}",
        "error": None,
        "trace_path": None,
        "run_id": None,
    }

    from playwright.sync_api import sync_playwright

    def _check_cancel() -> None:
        if cancel is not None:
            cancel.check()

    recorder = TraceRecorder(trace_dir=trace_dir)
    result["run_id"] = recorder.run_id
    recorder.record("run_started",
                    evidence=[f"url={target_url}", f"query={query}"])
    stages: "list[dict]" = []

    def _note_stage(page, name: str, extra=None) -> None:
        state = so_adapter.STAGE_READERS[name](page)
        if extra:
            state = {**state, **extra}
        try:
            page_url = page.url
        except Exception:  # noqa: BLE001 — duck-typed property
            page_url = ""
        stages.append({"stage": name,
                       "url": page_url if isinstance(page_url, str) else "",
                       "captured_at": so_adapter.utcnow(),
                       "state": state})
        so_adapter.write_stages(trace_dir, recorder.run_id, stages)
        recorder.record("stage_state", evidence=[f"stage={name}"])

    def _attach_screenshot(page) -> None:
        shot = capture_failure_screenshot(
            page, recorder.run_id, Path(trace_dir) / "screenshots"
        )
        if shot is not None:
            recorder.events[-1]["evidence_references"].append(
                f"screenshot={shot}"
            )
        else:
            recorder.events[-1]["evidence_references"].append(
                "screenshot_capture_failed"
            )

    def _finish_trace(terminal: str, exc=None) -> None:
        try:
            path = recorder.finish(
                terminal,
                error_details=(
                    {
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "cause_type": (
                            type(exc.__cause__).__name__
                            if exc and exc.__cause__
                            else None
                        ),
                        "cause_message": (
                            str(exc.__cause__) if exc and exc.__cause__ else None
                        ),
                    }
                    if exc
                    else None
                ),
            )
            result["trace_path"] = str(path)
        except TraceWriteError as write_exc:
            result["success"] = False
            result["status"] = "failed"
            result["cancelled"] = False
            result["error"] = f"TraceWriteError: {write_exc}"
            result["trace_path"] = None
            recorder.write_error = str(write_exc)

    def _bounded(action: str, func, page) -> None:
        _check_cancel()
        recorder.action_attempted(action)
        try:
            execute_with_retry(
                action,
                func,
                policy=DEFAULT_POLICY,
                cancellation_token=cancel,
            )
            recorder.action_succeeded(action)
        except RunCancelledError:
            raise
        except Exception as exc:
            recorder.action_failed(action, exc)
            _attach_screenshot(page)
            raise

    with sync_playwright() as playwright:
        if browser_factory is None:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
        else:
            browser, context, page = browser_factory(playwright)

        try:
            _bounded(
                ActionType.NAVIGATE.value,
                lambda: page.goto(target_url),
                page,
            )
            _note_stage(page, "search")
            _check_cancel()
            _verify_so_results(stages, query, recorder, page,
                               _attach_screenshot)

            result["success"] = True
            result["status"] = "succeeded"
            _finish_trace("succeeded")

        except RunCancelledError as exc:
            result["success"] = False
            result["cancelled"] = True
            result["status"] = "cancelled"
            result["error"] = f"RunCancelledError: {exc}"
            _finish_trace("cancelled", exc=exc)

        except Exception as exc:
            result["success"] = False
            result["cancelled"] = False
            result["status"] = "failed"
            if exc.__cause__ is not None:
                result["error"] = (
                    f"{type(exc).__name__}: {exc} "
                    f"(caused by {type(exc.__cause__).__name__}: {exc.__cause__})"
                )
            else:
                result["error"] = f"{type(exc).__name__}: {exc}"
            _finish_trace("failed", exc=exc)

        finally:
            if observe is not None:
                try:
                    result["observation"] = observe(page)
                    result["observation_error"] = None
                except Exception as exc:  # noqa: BLE001 — reported, not raised
                    result["observation"] = None
                    result["observation_error"] = (
                        f"{type(exc).__name__}: {exc}"
                    )
            _close_browser(context, browser, trace_dir, recorder.run_id)

    return result


def _verify_amazon_product(stages, query, pick, recorder, page,
                           attach_screenshot) -> None:
    """Gate success on the picked product, its name, and its price."""
    states = amazon_adapter.stage_states(stages)
    search = states.get("search", {})
    product = states.get("product", {})
    if search.get("gate") is True or product.get("gate") is True:
        exc = RuntimeError(
            "Amazon showed a bot gate; log in once via "
            "`python -m workbench.sessions login <profile>` and "
            "re-run with that profile")
        recorder.verification_failed("product_confirmed", exc)
        attach_screenshot(page)
        raise exc
    results = search.get("results")
    if not isinstance(results, list):
        results = []
    if len(results) < pick:
        exc = RuntimeError(
            f"search returned {len(results)} products, cannot pick #{pick}")
        recorder.verification_failed("product_confirmed", exc)
        attach_screenshot(page)
        raise exc
    picked = results[pick - 1].get("name") or ""
    name = str(product.get("name") or "")
    if not name or not amazon_adapter._same_product(name, picked):
        exc = RuntimeError(
            "Amazon product page does not name the picked product "
            f"(page={name!r}, picked {picked!r})")
        recorder.verification_failed("product_confirmed", exc)
        attach_screenshot(page)
        raise exc
    if not str(product.get("price") or ""):
        exc = RuntimeError(f"Amazon product {picked!r} shows no price")
        recorder.verification_failed("product_confirmed", exc)
        attach_screenshot(page)
        raise exc
    recorder.verification_passed("product_confirmed")


def run_amazon_price(
    query: str,
    pick: int,
    *,
    url: Optional[str] = None,
    trace_dir: Optional[Path] = None,
    cancel: Optional[CancellationToken] = None,
    observe: Optional[Callable[[Any], Any]] = None,
    browser_factory: Optional[Callable[[Any], Tuple[Any, Any, Any]]] = None,
) -> dict:
    """Search Amazon, open one product, record its price (read-only).

    Same contract as the Steam driver across two stages: search,
    product. Nothing is bought, no cart or account page is ever
    opened, and a bot gate or captcha is never answered: gated
    pages fail honestly with login instructions.
    """
    target_url = url if url is not None else amazon_adapter.HOME_URL
    amazon_adapter.assert_approved_url(target_url)
    trace_dir = trace_dir if trace_dir is not None else DEFAULT_TRACE_DIR
    result = {
        "success": False,
        "cancelled": False,
        "status": "failed",
        "project_name": f"amazon:{query}#{pick}",
        "error": None,
        "trace_path": None,
        "run_id": None,
    }

    from playwright.sync_api import sync_playwright

    def _check_cancel() -> None:
        if cancel is not None:
            cancel.check()

    recorder = TraceRecorder(trace_dir=trace_dir)
    result["run_id"] = recorder.run_id
    recorder.record(
        "run_started",
        evidence=[f"url={target_url}", f"query={query}", f"pick={pick}"],
    )
    stages: "list[dict]" = []

    def _note_stage(page, name: str, extra=None) -> None:
        state = amazon_adapter.STAGE_READERS[name](page)
        if extra:
            state = {**state, **extra}
        try:
            page_url = page.url
        except Exception:  # noqa: BLE001 — duck-typed property
            page_url = ""
        stages.append({"stage": name,
                       "url": page_url if isinstance(page_url, str) else "",
                       "captured_at": amazon_adapter.utcnow(),
                       "state": state})
        amazon_adapter.write_stages(trace_dir, recorder.run_id, stages)
        recorder.record("stage_state", evidence=[f"stage={name}"])

    def _attach_screenshot(page) -> None:
        shot = capture_failure_screenshot(
            page, recorder.run_id, Path(trace_dir) / "screenshots"
        )
        if shot is not None:
            recorder.events[-1]["evidence_references"].append(
                f"screenshot={shot}"
            )
        else:
            recorder.events[-1]["evidence_references"].append(
                "screenshot_capture_failed"
            )

    def _finish_trace(terminal: str, exc=None) -> None:
        try:
            path = recorder.finish(
                terminal,
                error_details=(
                    {
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "cause_type": (
                            type(exc.__cause__).__name__
                            if exc and exc.__cause__
                            else None
                        ),
                        "cause_message": (
                            str(exc.__cause__) if exc and exc.__cause__ else None
                        ),
                    }
                    if exc
                    else None
                ),
            )
            result["trace_path"] = str(path)
        except TraceWriteError as write_exc:
            result["success"] = False
            result["status"] = "failed"
            result["cancelled"] = False
            result["error"] = f"TraceWriteError: {write_exc}"
            result["trace_path"] = None
            recorder.write_error = str(write_exc)

    def _bounded(action: str, func, page) -> None:
        _check_cancel()
        recorder.action_attempted(action)
        try:
            execute_with_retry(
                action,
                func,
                policy=DEFAULT_POLICY,
                cancellation_token=cancel,
            )
            recorder.action_succeeded(action)
        except RunCancelledError:
            raise
        except Exception as exc:
            recorder.action_failed(action, exc)
            _attach_screenshot(page)
            raise

    with sync_playwright() as playwright:
        if browser_factory is None:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
        else:
            browser, context, page = browser_factory(playwright)

        try:
            search_target = amazon_adapter.search_url(query)
            amazon_adapter.assert_approved_url(search_target)
            _bounded(
                ActionType.NAVIGATE.value,
                lambda: page.goto(search_target),
                page,
            )
            amazon_adapter.wait_for_any(
                page, [amazon_adapter.SEL_ROW],
                ACTION_TIMEOUT_MS)
            _note_stage(page, "search")
            found = amazon_adapter.stage_states(stages).get("search", {})
            if found.get("gate") is True:
                exc = RuntimeError(
                    "Amazon showed a bot gate; log in once via "
                    "`python -m workbench.sessions login <profile>` and "
                    "re-run with that profile")
                recorder.verification_failed("search_pick_available", exc)
                _attach_screenshot(page)
                raise exc
            results = found.get("results") or []
            if len(results) < pick:
                exc = RuntimeError(
                    f"search returned {len(results)} products, "
                    f"cannot pick #{pick}")
                recorder.verification_failed("search_pick_available", exc)
                _attach_screenshot(page)
                raise exc
            picked_href = results[pick - 1].get("href") or ""
            product_target = (
                picked_href if picked_href.startswith("https://")
                else amazon_adapter.APPROVED_ORIGIN + picked_href)
            amazon_adapter.assert_approved_url(product_target)
            recorder.record(
                "pick_committed",
                evidence=[f"pick={pick}",
                          f"href={picked_href[:120]}"],
            )
            _bounded(
                ActionType.NAVIGATE.value,
                lambda: page.goto(product_target),
                page,
            )
            amazon_adapter.wait_for_any(
                page, [amazon_adapter.SEL_TITLE],
                ACTION_TIMEOUT_MS)
            _note_stage(page, "product")
            _check_cancel()
            _verify_amazon_product(stages, query, pick, recorder, page,
                                   _attach_screenshot)

            result["success"] = True
            result["status"] = "succeeded"
            _finish_trace("succeeded")

        except RunCancelledError as exc:
            result["success"] = False
            result["cancelled"] = True
            result["status"] = "cancelled"
            result["error"] = f"RunCancelledError: {exc}"
            _finish_trace("cancelled", exc=exc)

        except Exception as exc:
            result["success"] = False
            result["cancelled"] = False
            result["status"] = "failed"
            if exc.__cause__ is not None:
                result["error"] = (
                    f"{type(exc).__name__}: {exc} "
                    f"(caused by {type(exc.__cause__).__name__}: {exc.__cause__})"
                )
            else:
                result["error"] = f"{type(exc).__name__}: {exc}"
            _finish_trace("failed", exc=exc)

        finally:
            if observe is not None:
                try:
                    result["observation"] = observe(page)
                    result["observation_error"] = None
                except Exception as exc:  # noqa: BLE001 — reported, not raised
                    result["observation"] = None
                    result["observation_error"] = (
                        f"{type(exc).__name__}: {exc}"
                    )
            _close_browser(context, browser, trace_dir, recorder.run_id)

    return result
