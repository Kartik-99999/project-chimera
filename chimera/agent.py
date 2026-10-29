"""Minimal Playwright automation for Project Chimera."""

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


DEMO_APP_PATH = Path(__file__).resolve().parent.parent / "demo_app" / "index.html"
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
            page, recorder.run_id, DEFAULT_SCREENSHOT_DIR
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
            try:
                context.close()
            finally:
                browser.close()

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
