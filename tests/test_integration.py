"""Browser-level integration tests for Project Chimera's fault-injection
mechanism and Reset control.

These tests use real Playwright + Chromium against the local
``demo_app/index.html``. Each test launches its own browser context
and closes it on teardown, so they are independent of the agent's
``create_project()`` wrapper and of one another.

Run with::

    pytest tests/test_integration.py -v
"""

import json
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

import pytest
from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from chimera.agent import (
    ACTION_TIMEOUT_MS,
    create_project,
    get_demo_url,
    get_demo_url_with_faults,
)
from chimera.safety import CancellationToken


DEMO_HTML = Path(__file__).resolve().parent.parent / "demo_app" / "index.html"


@pytest.fixture(scope="module")
def _playwright() -> Playwright:
    with sync_playwright() as p:
        yield p


@pytest.fixture()
def browser(_playwright: Playwright) -> Browser:
    b = _playwright.chromium.launch(headless=True)
    try:
        yield b
    finally:
        b.close()


def _open(browser: Browser, url: str) -> Page:
    page = browser.new_page()
    page.goto(url)
    return page


# ---------------------------------------------------------------------------
# Scenario 1: normal (no fault) succeeds.
# ---------------------------------------------------------------------------

def test_normal_create_project_succeeds(browser: Browser) -> None:
    """Baseline: no-fault ``create_project`` against the bare URL completes
    end-to-end with the project visible in the list."""
    page = _open(browser, get_demo_url())
    try:
        result = create_project_in_page(page, "Baseline Project")
        assert result["success"] is True, f"Expected success, got: {result['error']}"
        assert result["project_name"] == "Baseline Project"
        assert result["error"] is None
        # The list now contains exactly one item with this name.
        items = page.locator("#project-list li")
        items.first.wait_for(state="visible", timeout=ACTION_TIMEOUT_MS)
        assert items.count() == 1
        assert "Baseline Project" in items.first.text_content()
        # The confirmation is visible (not hidden).
        assert "hidden" not in (page.locator("#confirmation").get_attribute("class") or "")
    finally:
        page.close()


# ---------------------------------------------------------------------------
# Scenario 2: slow_ms=2000 eventually succeeds.
# ---------------------------------------------------------------------------

def test_slow_load_eventually_succeeds(browser: Browser) -> None:
    """``?slow=2000`` must be transient: the form is disabled for ~2s then
    re-enabled, after which Playwright's auto-wait lets the action proceed."""
    page = _open(browser, get_demo_url_with_faults(slow_ms=2000))
    try:
        started = time.monotonic()
        result = create_project_in_page(page, "Slow Project")
        elapsed = time.monotonic() - started
        assert result["success"] is True, (
            f"Expected success after slow delay, got: {result['error']}"
        )
        # The form was disabled for ~2s, so the run should take at least
        # that long. Use a conservative lower bound (1.5s) to avoid flakiness.
        assert elapsed >= 1.5, f"Returned too quickly ({elapsed:.2f}s); slow=2000 was ignored"
        # The project is in the list.
        items = page.locator("#project-list li")
        items.first.wait_for(state="visible", timeout=ACTION_TIMEOUT_MS)
        assert "Slow Project" in items.first.text_content()
    finally:
        page.close()


# ---------------------------------------------------------------------------
# Scenario 3: disabled=True fails within the action timeout.
# ---------------------------------------------------------------------------

def test_persistent_disabled_fails_within_timeout(browser: Browser) -> None:
    """``?disabled=1`` keeps the Create button disabled; the FILL/CLICK
    actions time out at ``ACTION_TIMEOUT_MS`` and the run returns failure."""
    page = _open(browser, get_demo_url_with_faults(disabled=True))
    try:
        started = time.monotonic()
        result = create_project_in_page(page, "Disabled Project")
        elapsed = time.monotonic() - started
        assert result["success"] is False
        assert result["error"] is not None
        # Bound: the FILL wait alone can consume up to ACTION_TIMEOUT_MS.
        # The total run should not exceed a small multiple of that.
        assert elapsed < (ACTION_TIMEOUT_MS * 3 / 1000) + 1.0, (
            f"Run took {elapsed:.2f}s — exceeded the bounded failure window"
        )
        # Nothing was added to the list.
        assert page.locator("#project-list li").count() == 0
        # The confirmation stayed hidden.
        assert "hidden" in (page.locator("#confirmation").get_attribute("class") or "")
    finally:
        page.close()


# ---------------------------------------------------------------------------
# Scenario 4: slow_ms=2000 + disabled=True fails safely.
# ---------------------------------------------------------------------------

def test_slow_then_persistent_disabled_fails_safely(browser: Browser) -> None:
    """``?slow=2000&disabled=1``: the form re-enables after ~2s, but the
    sticky ``disabled`` flag re-disables it. The FILL/CLICK must time out
    within the action timeout. The run must NOT report success."""
    page = _open(
        browser,
        get_demo_url_with_faults(slow_ms=2000, disabled=True),
    )
    try:
        started = time.monotonic()
        result = create_project_in_page(page, "Sticky Disabled Project")
        elapsed = time.monotonic() - started
        assert result["success"] is False, (
            f"Expected bounded failure; got success in {elapsed:.2f}s"
        )
        assert result["error"] is not None
        # The slow delay (≥ 1.5s) is consumed before the persistent failure
        # begins; the bounded failure window then adds ACTION_TIMEOUT_MS.
        # Upper bound: slow delay + (action timeout * 2) + slack.
        upper = 2.0 + (ACTION_TIMEOUT_MS * 2 / 1000) + 2.0
        assert elapsed < upper, (
            f"Run took {elapsed:.2f}s — exceeded bounded failure window ({upper:.2f}s)"
        )
        # Nothing was added to the list.
        assert page.locator("#project-list li").count() == 0
    finally:
        page.close()


# ---------------------------------------------------------------------------
# Scenario 5: Reset clears the list, confirmation, input, and active faults.
# ---------------------------------------------------------------------------

def test_reset_clears_state_and_faults(browser: Browser) -> None:
    """After creating a project with faults active, clicking the in-page
    Reset button must clear: the project list, the confirmation message,
    the form input, the disabled attribute, and the fault-status text."""
    page = _open(browser, get_demo_url_with_faults(disabled=True))
    try:
        # The form is disabled by the persistent fault. Bypass the
        # disabled state via evaluate so we can populate state and
        # verify the reset behavior. (We are testing Reset, not the
        # disabled fault — that is covered by
        # ``test_persistent_disabled_fails_within_timeout``.)
        page.evaluate(
            "document.getElementById('create-btn').disabled = false; "
            "document.getElementById('project-name').disabled = false;"
        )
        # Type a value so we can verify the input is cleared by reset.
        name_input = page.get_by_label("Project Name")
        name_input.fill("To Be Reset", timeout=ACTION_TIMEOUT_MS)
        # Submit the form directly (bypassing the click path that would
        # also need a working button).
        page.locator("#project-form").dispatch_event("submit")
        # Sanity: state is populated.
        page.locator("#project-list li").first.wait_for(
            state="visible", timeout=ACTION_TIMEOUT_MS
        )
        assert page.locator("#project-list li").count() == 1
        assert "To Be Reset" in page.locator("#project-list li").first.text_content()
        assert (
            "hidden"
            not in (page.locator("#confirmation").get_attribute("class") or "")
        )

        # Click the Reset button.
        page.locator("#reset-btn").click()

        # Project list cleared.
        assert page.locator("#project-list li").count() == 0
        # Confirmation re-hidden.
        assert "hidden" in (
            page.locator("#confirmation").get_attribute("class") or ""
        )
        # Form input cleared.
        assert page.locator("#project-name").input_value() == ""
        # Create button no longer disabled.
        assert page.locator("#create-btn").is_disabled() is False
        # Fault-status text indicates no active faults.
        status = page.locator("#fault-status").text_content() or ""
        assert "No faults active" in status, (
            f"Expected fault status to indicate no faults, got: {status!r}"
        )
        # Manual control checkboxes also reflect the cleared state.
        assert page.locator("#fault-disabled").is_checked() is False
    finally:
        page.close()


# ---------------------------------------------------------------------------
# Scenario 6: successful run writes a trace artifact with a
# run_succeeded terminal event and the expected event ordering.
# ---------------------------------------------------------------------------

def _run_agent_in_thread(
    name: str,
    url: str,
    trace_dir: Path,
    cancel: Optional[CancellationToken] = None,
) -> dict:
    """Invoke ``create_project`` from a worker thread.

    The agent uses Playwright's sync API, which refuses to start inside
    a running asyncio loop (pytest-asyncio would conflict). Running it
    in a thread gives it a fresh event loop without that conflict.
    """
    with ThreadPoolExecutor(max_workers=1) as ex:
        return ex.submit(
            create_project,
            name,
            url=url,
            trace_dir=trace_dir,
            cancel=cancel,
        ).result()


def test_successful_run_writes_trace_artifact() -> None:
    """``create_project`` must persist a JSON trace artifact for every
    run — success or failure — and the terminal event must agree with
    the independently verified result (FR-018, FR-034)."""
    with tempfile.TemporaryDirectory() as tmp:
        trace_dir = Path(tmp)
        result = _run_agent_in_thread(
            "Traced Success",
            url=get_demo_url(),
            trace_dir=trace_dir,
        )
        assert result["success"] is True, f"Expected success, got: {result['error']}"
        assert result["run_id"], "run_id must be populated"
        assert result["trace_path"] is not None, "trace_path must be set on success"

        # The artifact exists at <trace_dir>/<run_id>.json.
        artifact = Path(result["trace_path"])
        assert artifact.exists()
        assert artifact.parent == trace_dir
        assert artifact.name == f"{result['run_id']}.json"

        data = json.loads(artifact.read_text(encoding="utf-8"))
        assert data["run_id"] == result["run_id"]
        assert data["terminal_status"] == "succeeded"

        # The event sequence ends in the expected terminal.
        events = data["events"]
        event_types = [e["event_type"] for e in events]
        assert event_types[0] == "run_started"
        assert event_types[-1] == "run_succeeded"
        assert "action_attempted" in event_types
        assert "action_succeeded" in event_types
        assert "verification_passed" in event_types

        # The two verification postconditions from the agent are present.
        verification_events = [
            e for e in events if e["event_type"] == "verification_passed"
        ]
        postconditions = {
            e["evidence_references"][0] for e in verification_events
        }
        assert "confirmation_message_visible" in postconditions
        assert "project_in_list" in postconditions

        # Sequence numbers are 1..N and strictly increasing.
        assert [e["sequence_number"] for e in events] == list(
            range(1, len(events) + 1)
        )


# ---------------------------------------------------------------------------
# Scenario 7: failed run still writes a trace artifact, with
# run_failed terminal and a screenshot attached as evidence.
# ---------------------------------------------------------------------------

def test_failed_run_writes_trace_artifact_with_failure_terminal() -> None:
    """When the persistent disabled fault is active, the run must fail
    and STILL persist a trace artifact (FR-018) with ``run_failed`` and
    a screenshot evidence reference (NFR-019)."""
    with tempfile.TemporaryDirectory() as tmp:
        trace_dir = Path(tmp)
        result = _run_agent_in_thread(
            "Traced Failure",
            url=get_demo_url_with_faults(disabled=True),
            trace_dir=trace_dir,
        )
        assert result["success"] is False
        assert result["error"] is not None
        # Trace artifact must still be written for failed runs.
        assert result["trace_path"] is not None, (
            "trace_path must be set even on failure (FR-018, FR-034)"
        )

        data = json.loads(Path(result["trace_path"]).read_text(encoding="utf-8"))
        assert data["terminal_status"] == "failed"
        event_types = [e["event_type"] for e in data["events"]]
        assert event_types[-1] == "run_failed"
        # At least one action_failed event from the FILL/CLICK timeouts.
        assert "action_failed" in event_types

        # The terminal outcome in the trace MUST match the reported
        # result — a successful result with a failed trace (or vice
        # versa) is exactly the FR-034 violation we are guarding against.
        reported_succeeded = result["success"] is True
        trace_succeeded = data["terminal_status"] == "succeeded"
        assert reported_succeeded == trace_succeeded, (
            "Reported result disagrees with trace terminal event"
        )

        # Screenshot was attempted on failure; it is either captured
        # (file:// path) or recorded as screenshot_capture_failed.
        last_failure = next(
            e for e in reversed(data["events"])
            if e["event_type"] == "action_failed"
        )
        evidence = last_failure["evidence_references"]
        assert any(
            ev.startswith("screenshot=") or ev == "screenshot_capture_failed"
            for ev in evidence
        ), f"Expected screenshot evidence, got: {evidence}"


# ---------------------------------------------------------------------------
# Scenario 8: every normal browser action is represented exactly once
# in the trace (no duplicate events, no spurious action_failed).
# ---------------------------------------------------------------------------

def test_each_browser_action_appears_once_in_trace() -> None:
    """A successful run must contain exactly one ``action_attempted``
    and one ``action_succeeded`` for each of navigate/fill/click, plus
    exactly one ``verification_passed`` per postcondition, plus one
    ``run_started`` at the start and one ``run_succeeded`` at the end.
    No ``action_failed`` events should appear in a happy-path run.
    """
    with tempfile.TemporaryDirectory() as tmp:
        trace_dir = Path(tmp)
        result = _run_agent_in_thread(
            "Action Count",
            url=get_demo_url(),
            trace_dir=trace_dir,
        )
        assert result["success"] is True, f"Expected success, got: {result['error']}"

        data = json.loads(Path(result["trace_path"]).read_text(encoding="utf-8"))
        events = data["events"]

        # Exactly one attempted + succeeded per action type.
        for action_type in ("navigate", "fill", "click"):
            attempted = [
                e for e in events
                if e["event_type"] == "action_attempted"
                and e["action_type"] == action_type
            ]
            succeeded = [
                e for e in events
                if e["event_type"] == "action_succeeded"
                and e["action_type"] == action_type
            ]
            failed = [
                e for e in events
                if e["event_type"] == "action_failed"
                and e["action_type"] == action_type
            ]
            assert len(attempted) == 1, (
                f"Expected exactly one action_attempted for {action_type!r}; "
                f"got {len(attempted)}"
            )
            assert len(succeeded) == 1, (
                f"Expected exactly one action_succeeded for {action_type!r}; "
                f"got {len(succeeded)}"
            )
            assert failed == [], (
                f"Unexpected action_failed events for {action_type!r}: {failed}"
            )

        # Exactly one verification_passed per postcondition.
        verifications = [
            e for e in events if e["event_type"] == "verification_passed"
        ]
        postconditions = {e["evidence_references"][0] for e in verifications}
        assert postconditions == {
            "confirmation_message_visible",
            "project_in_list",
        }, f"Unexpected postconditions: {postconditions}"

        # No verification_failed or action_failed in a successful run.
        assert not [e for e in events if e["event_type"] == "verification_failed"]
        assert not [e for e in events if e["event_type"] == "action_failed"]

        # Exactly one run_started and one run_succeeded, in that order.
        assert events[0]["event_type"] == "run_started"
        assert events[-1]["event_type"] == "run_succeeded"

        # Sequence numbers are 1..N with no gaps and no duplicates.
        assert [e["sequence_number"] for e in events] == list(
            range(1, len(events) + 1)
        )


# ---------------------------------------------------------------------------
# Scenario 9: a trace persistence failure cannot produce a successful
# result. This is the agent-level FR-034 invariant: the recorder may
# fail to write, but the agent must report failure in that case.
# ---------------------------------------------------------------------------

def test_trace_write_failure_forces_run_to_failure() -> None:
    """FR-034 at the agent level: if the trace artifact cannot be
    written to disk, ``create_project`` must report
    ``success=False`` and surface a ``TraceWriteError`` — even when
    every browser action actually succeeded."""
    with tempfile.TemporaryDirectory() as tmp:
        trace_dir = Path(tmp)
        # Place a regular file where the trace dir would need to live;
        # recorder.finish() will fail to create the parent directory.
        blocker = trace_dir / "blocker"
        blocker.write_text("not a directory", encoding="utf-8")

        result = _run_agent_in_thread(
            "Trace Write Failure",
            url=get_demo_url(),
            trace_dir=blocker,
        )

        # The browser actions succeeded, but the missing trace must
        # force the result to failure.
        assert result["success"] is False, (
            "Trace write failure must force result['success'] to False; "
            f"got success=True with error={result['error']!r}"
        )
        assert result["trace_path"] is None, (
            "Trace write failure must leave result['trace_path'] as None; "
            f"got {result['trace_path']!r}"
        )
        assert result["error"] is not None
        assert "TraceWriteError" in result["error"], (
            f"Expected TraceWriteError in result['error']; got {result['error']!r}"
        )
        # run_id is still populated (the recorder was constructed
        # before the write attempt).
        assert result["run_id"], "run_id must be set even on trace write failure"


# ---------------------------------------------------------------------------
# Scenario 10 (FR-021): cancellation before execution starts.
# ---------------------------------------------------------------------------

def test_cancel_before_execution_runs_no_actions() -> None:
    """If the token is cancelled before ``create_project`` is called,
    the run must abort at the first safe boundary without performing
    any browser action. The trace must end in ``run_cancelled`` and
    the result must report ``cancelled=True, success=False``."""
    with tempfile.TemporaryDirectory() as tmp:
        trace_dir = Path(tmp)
        token = CancellationToken()
        token.request("user pressed stop before start")

        result = _run_agent_in_thread(
            "Cancel Before",
            url=get_demo_url(),
            trace_dir=trace_dir,
            cancel=token,
        )

        # The result must clearly mark cancellation.
        assert result["cancelled"] is True
        assert result["status"] == "cancelled"
        assert result["success"] is False
        assert "RunCancelledError" in (result["error"] or "")
        # The run_id and trace_path are still populated (the recorder
        # was constructed and the terminal event was written).
        assert result["run_id"]
        assert result["trace_path"] is not None

        data = json.loads(Path(result["trace_path"]).read_text(encoding="utf-8"))
        event_types = [e["event_type"] for e in data["events"]]
        # The cancel was requested before the first action, so only
        # ``run_started`` and the terminal ``run_cancelled`` should
        # appear — no action_attempted, no verification events.
        assert event_types[0] == "run_started"
        assert event_types[-1] == "run_cancelled"
        assert "action_attempted" not in event_types
        assert "action_failed" not in event_types
        assert data["terminal_status"] == "cancelled"
        # The terminal event carries the cancel reason in its message
        # (the ``RunCancelledError`` instance was constructed with the
        # reason as its message, so ``str(exc)`` preserves it).
        terminal = data["events"][-1]
        assert terminal["action_outcome"] == "cancelled"
        assert terminal["error_details"]["message"] == (
            "user pressed stop before start"
        )

        # The browser was closed: nothing leaked. The agent's
        # ``finally: browser.close()`` runs even on cancellation.
        # We can't directly assert the browser is closed from here
        # (it lived in the worker thread), but a follow-up
        # ``create_project`` on the same executor must succeed —
        # the sync_playwright context manager was not left dangling.
        result2 = _run_agent_in_thread(
            "After Cancel",
            url=get_demo_url(),
            trace_dir=trace_dir,
        )
        assert result2["success"] is True, (
            f"Browser leaked across cancellation; second run failed: "
            f"{result2['error']}"
        )


# ---------------------------------------------------------------------------
# Scenario 11 (FR-021): cancellation observed between actions.
# Deterministic handshake: the agent thread is blocked inside the
# recorder right after the navigate succeeds, so the canceller can
# request cancellation at a precisely known point.
# ---------------------------------------------------------------------------

def test_cancel_between_actions_stops_at_next_boundary(monkeypatch) -> None:
    """A token cancelled after the navigate succeeds but before the fill
    attempt must let the navigate finish and then abort at the next safe
    boundary. The trace shows one successful action and no fill or click
    events."""
    import threading

    import chimera.tracing as tracing_mod

    with tempfile.TemporaryDirectory() as tmp:
        trace_dir = Path(tmp)
        token = CancellationToken()
        nav_done = threading.Event()
        cancel_done = threading.Event()

        real_record = tracing_mod.TraceRecorder.record

        def patched_record(self, event_type, **kwargs):  # noqa: ANN001
            result = real_record(self, event_type, **kwargs)
            if (
                event_type == "action_succeeded"
                and kwargs.get("action_type") == "navigate"
            ):
                # Block the agent thread here so the canceller can
                # request cancellation at a precisely known point:
                # after the navigate succeeded, before the fill starts.
                nav_done.set()
                cancel_done.wait(timeout=10)
            return result

        monkeypatch.setattr(
            tracing_mod.TraceRecorder, "record", patched_record
        )

        def canceller() -> None:
            assert nav_done.wait(timeout=10), "navigate never completed"
            token.request("after navigate")
            cancel_done.set()

        threading.Thread(target=canceller, daemon=True).start()

        result = _run_agent_in_thread(
            "Cancel Between",
            url=get_demo_url(),
            trace_dir=trace_dir,
            cancel=token,
        )

        assert result["cancelled"] is True
        assert result["status"] == "cancelled"
        assert result["success"] is False

        data = json.loads(Path(result["trace_path"]).read_text(encoding="utf-8"))
        event_types = [e["event_type"] for e in data["events"]]
        # The navigate ran and succeeded before the cancel was observed.
        nav_succeeded = [
            e for e in data["events"]
            if e["event_type"] == "action_succeeded"
            and e["action_type"] == "navigate"
        ]
        assert len(nav_succeeded) == 1, (
            f"Expected navigate to succeed before cancel; events: {event_types}"
        )
        # Fill and click must NOT have run.
        fill_events = [
            e for e in data["events"] if e["action_type"] == "fill"
        ]
        click_events = [
            e for e in data["events"] if e["action_type"] == "click"
        ]
        assert fill_events == [], (
            f"Fill should not have run after cancel; got: {fill_events}"
        )
        assert click_events == [], (
            f"Click should not have run after cancel; got: {click_events}"
        )
        # Terminal is run_cancelled, exactly once.
        assert event_types[-1] == "run_cancelled"
        assert event_types.count("run_cancelled") == 1
        assert data["terminal_status"] == "cancelled"


# ---------------------------------------------------------------------------
# Scenario 12 (FR-021): cancellation requested while a Playwright
# action is genuinely in flight. Proves the semantics are COOPERATIVE:
# the in-flight action is NOT interrupted, it runs to completion, and
# the cancel is observed at the next safe boundary.
# ---------------------------------------------------------------------------

def test_cancel_during_in_flight_action_is_cooperative(monkeypatch) -> None:
    """The fill is auto-waiting on the slow form when cancellation is
    requested. The fill must be allowed to finish (it is not
    interrupted), and the click that would follow must never run."""
    import threading
    import time

    import chimera.agent as agent_mod

    with tempfile.TemporaryDirectory() as tmp:
        trace_dir = Path(tmp)
        token = CancellationToken()
        fill_in_flight = threading.Event()

        real_execute = agent_mod.execute_with_retry

        def patched_execute(action_type, action, **kwargs):  # noqa: ANN001
            def wrapper(*args, **kw):  # noqa: ANN001
                if action_type == "fill":
                    # Signal from INSIDE the action body: the fill is
                    # now genuinely executing in Playwright.
                    fill_in_flight.set()
                return action(*args, **kw)
            return real_execute(action_type, wrapper, **kwargs)

        monkeypatch.setattr(
            agent_mod, "execute_with_retry", patched_execute
        )

        def canceller() -> None:
            assert fill_in_flight.wait(timeout=10), "fill never started"
            token.request("during fill")

        threading.Thread(target=canceller, daemon=True).start()
        started = time.monotonic()

        result = _run_agent_in_thread(
            "Cancel During",
            url=get_demo_url_with_faults(slow_ms=1200),
            trace_dir=trace_dir,
            cancel=token,
        )
        elapsed = time.monotonic() - started

        assert result["cancelled"] is True, (
            f"Expected cancelled=True; got success={result['success']}, "
            f"error={result['error']!r}"
        )
        assert result["status"] == "cancelled"
        assert result["success"] is False

        data = json.loads(Path(result["trace_path"]).read_text(encoding="utf-8"))
        events = data["events"]
        event_types = [e["event_type"] for e in events]
        # The in-flight fill was allowed to complete — it was NOT
        # interrupted. Its success event is therefore present.
        fill_succeeded = [
            e for e in events
            if e["event_type"] == "action_succeeded"
            and e["action_type"] == "fill"
        ]
        assert len(fill_succeeded) == 1, (
            f"In-flight fill must complete (cooperative cancel); "
            f"events: {event_types}"
        )
        # The click that would have followed must never have run.
        click_events = [e for e in events if e["action_type"] == "click"]
        assert click_events == [], (
            f"Click must not run after cancel was observed; got: {click_events}"
        )
        # The cancel was observed at the next safe boundary, well under
        # the 5s action budget.
        assert elapsed < 4.0, (
            f"Cancel was not observed promptly; run took {elapsed:.2f}s"
        )
        # And the run waited for the in-flight action to finish, proving
        # cancellation is cooperative rather than an immediate interrupt.
        assert elapsed >= 1.0, (
            f"Run returned in {elapsed:.2f}s — the in-flight action was "
            f"interrupted rather than allowed to complete"
        )
        assert data["terminal_status"] == "cancelled"
        assert event_types[-1] == "run_cancelled"
        assert event_types.count("run_cancelled") == 1


# ---------------------------------------------------------------------------
# Scenario 13 (FR-021 + FR-034): a trace-write failure overrides the
# result even when the run was cancelled. A run that cannot be traced
# cannot be reported as a clean cancellation.
# ---------------------------------------------------------------------------

def test_trace_write_failure_overrides_cancelled_result() -> None:
    """FR-034 takes precedence over the cancelled outcome: if the trace
    cannot be written, the result is ``status="failed"``,
    ``success=False``, ``cancelled=False``."""
    with tempfile.TemporaryDirectory() as tmp:
        trace_dir = Path(tmp)
        # A regular file where the trace directory would need to be.
        blocker = trace_dir / "blocker"
        blocker.write_text("not a directory", encoding="utf-8")
        token = CancellationToken()
        token.request("cancelled but untraceable")

        result = _run_agent_in_thread(
            "Cancel And Write Failure",
            url=get_demo_url(),
            trace_dir=blocker,
            cancel=token,
        )

        assert result["status"] == "failed"
        assert result["success"] is False
        assert result["cancelled"] is False
        assert result["trace_path"] is None
        assert "TraceWriteError" in (result["error"] or "")


# ---------------------------------------------------------------------------
# Scenario 14 (FR-021): a run with no cancel token is unchanged.
# Verifies backward compatibility: existing callers that don't pass
# ``cancel=`` see the same shape they always have (success/project_name/
# error/trace_path/run_id) plus the new ``cancelled=False, status=...``.
# ---------------------------------------------------------------------------

def test_run_without_cancel_token_keeps_default_shape() -> None:
    """Callers that don't request cancellation must get a result with
    ``cancelled=False`` and ``status`` in ``{"succeeded","failed"}``.
    No ``cancelled`` outcome should be reachable without a token."""
    with tempfile.TemporaryDirectory() as tmp:
        trace_dir = Path(tmp)
        result = _run_agent_in_thread(
            "No Cancel Token",
            url=get_demo_url(),
            trace_dir=trace_dir,
        )
        # Backward-compatible fields: success, project_name, error,
        # trace_path, run_id are all populated as before.
        assert result["success"] is True
        assert result["project_name"] == "No Cancel Token"
        assert result["error"] is None
        assert result["trace_path"] is not None
        assert result["run_id"]
        # New additive fields have safe defaults.
        assert result["cancelled"] is False
        assert result["status"] == "succeeded"


# ---------------------------------------------------------------------------
# Scenario 15 (FR-021): a failed run with a cancel token must still
# be classified as ``status="failed"``, not ``status="cancelled"``.
# Cancellation is a distinct terminal outcome; an ordinary action
# failure must not be re-classified as a cancellation.
# ---------------------------------------------------------------------------

def test_action_failure_is_not_classified_as_cancellation() -> None:
    """A cancel token that is never ``request()``-ed must not turn an
    ordinary action failure into a cancellation. ``status`` must be
    ``"failed"`` and ``cancelled`` must be ``False``."""
    with tempfile.TemporaryDirectory() as tmp:
        trace_dir = Path(tmp)
        token = CancellationToken()  # never requested
        result = _run_agent_in_thread(
            "Failure Not Cancellation",
            url=get_demo_url_with_faults(disabled=True),
            trace_dir=trace_dir,
            cancel=token,
        )
        assert result["success"] is False
        assert result["cancelled"] is False
        assert result["status"] == "failed"
        assert "RunCancelledError" not in (result["error"] or "")


# ---------------------------------------------------------------------------
# Scenario 16 (NFR-012): session isolation between runs.
# ---------------------------------------------------------------------------

def _capture_contexts(monkeypatch) -> list:
    """Record every BrowserContext the agent creates, and every browser
    it launches, so isolation can be asserted directly."""
    import playwright.sync_api as pw_api

    contexts: list = []
    browsers: list = []
    real_new_context = pw_api.Browser.new_context
    real_launch = pw_api.BrowserType.launch

    def patched_new_context(self, **kwargs):  # noqa: ANN001
        ctx = real_new_context(self, **kwargs)
        contexts.append(ctx)
        return ctx

    def patched_launch(self, **kwargs):  # noqa: ANN001
        browser = real_launch(self, **kwargs)
        browsers.append(browser)
        return browser

    monkeypatch.setattr(pw_api.Browser, "new_context", patched_new_context)
    monkeypatch.setattr(pw_api.BrowserType, "launch", patched_launch)
    return contexts, browsers


def test_each_run_gets_a_fresh_browser_context(monkeypatch) -> None:
    """NFR-012: every run must create its own BrowserContext, and the
    context must be closed when the run ends."""
    contexts, browsers = _capture_contexts(monkeypatch)

    with tempfile.TemporaryDirectory() as tmp:
        trace_dir = Path(tmp)
        first = _run_agent_in_thread(
            "Isolated One", url=get_demo_url(), trace_dir=trace_dir
        )
        second = _run_agent_in_thread(
            "Isolated Two", url=get_demo_url(), trace_dir=trace_dir
        )

    assert first["success"] is True
    assert second["success"] is True
    # One context and one browser per run.
    assert len(contexts) == 2, f"Expected 2 contexts, got {len(contexts)}"
    assert len(browsers) == 2, f"Expected 2 browsers, got {len(browsers)}"
    # The two runs did NOT share a context object.
    assert contexts[0] is not contexts[1], (
        "Runs must not share a BrowserContext (NFR-012)"
    )
    assert browsers[0] is not browsers[1], (
        "Runs must not share a Browser instance (NFR-012)"
    )
    # Each context belongs to its own run's browser.
    assert contexts[0].browser is browsers[0]
    assert contexts[1].browser is browsers[1]


def test_session_state_does_not_leak_between_runs(monkeypatch) -> None:
    """NFR-012: cookies and other session state written during one run
    must not be visible to the next run.

    The evidence is captured *during* each run: Playwright's event
    loop is torn down when the run returns, so the context objects
    cannot be inspected afterwards.
    """
    import playwright.sync_api as pw_api

    real_new_context = pw_api.Browser.new_context
    # Cookies visible in each context at the moment it is created.
    cookies_at_creation: list = []

    def patched_new_context(self, **kwargs):  # noqa: ANN001
        ctx = real_new_context(self, **kwargs)
        # A brand-new context must start with an empty cookie jar.
        cookies_at_creation.append(list(ctx.cookies()))
        # Seed session state that a later run must not see.
        ctx.add_cookies([
            {
                "name": "chimera_leak_probe",
                "value": "seeded",
                "domain": "leak-probe.test",
                "path": "/",
            }
        ])
        return ctx

    monkeypatch.setattr(pw_api.Browser, "new_context", patched_new_context)

    with tempfile.TemporaryDirectory() as tmp:
        trace_dir = Path(tmp)
        first = _run_agent_in_thread(
            "Leak Probe One", url=get_demo_url(), trace_dir=trace_dir
        )
        second = _run_agent_in_thread(
            "Leak Probe Two", url=get_demo_url(), trace_dir=trace_dir
        )

    assert first["success"] is True
    assert second["success"] is True
    assert len(cookies_at_creation) == 2, (
        f"Expected one context per run; got {len(cookies_at_creation)}"
    )
    # Both runs started from an empty cookie jar. Run 1 seeded a probe
    # cookie into its own context; run 2's fresh context did not see it.
    assert cookies_at_creation[0] == [], (
        f"Run 1 context should have started empty: {cookies_at_creation[0]}"
    )
    assert cookies_at_creation[1] == [], (
        f"Session state leaked into run 2: {cookies_at_creation[1]}"
    )


def test_browser_resources_are_closed_after_each_run(monkeypatch) -> None:
    """The per-run context and the browser must be closed when the run
    ends, on both the success and the failure path."""
    import playwright.sync_api as pw_api

    closed_contexts: list = []
    closed_browsers: list = []
    real_ctx_close = pw_api.BrowserContext.close
    real_browser_close = pw_api.Browser.close

    def patched_ctx_close(self, **kwargs):  # noqa: ANN001
        closed_contexts.append(self)
        return real_ctx_close(self, **kwargs)

    def patched_browser_close(self, **kwargs):  # noqa: ANN001
        closed_browsers.append(self)
        return real_browser_close(self, **kwargs)

    monkeypatch.setattr(pw_api.BrowserContext, "close", patched_ctx_close)
    monkeypatch.setattr(pw_api.Browser, "close", patched_browser_close)

    with tempfile.TemporaryDirectory() as tmp:
        trace_dir = Path(tmp)
        ok = _run_agent_in_thread(
            "Cleanup Ok", url=get_demo_url(), trace_dir=trace_dir
        )
        assert ok["success"] is True
        # A successful run closed exactly one context and one browser.
        assert len(closed_contexts) == 1, (
            f"Expected 1 context closed after success, got {len(closed_contexts)}"
        )
        assert len(closed_browsers) == 1, (
            f"Expected 1 browser closed after success, got {len(closed_browsers)}"
        )

        failed = _run_agent_in_thread(
            "Cleanup Fail",
            url=get_demo_url_with_faults(disabled=True),
            trace_dir=trace_dir,
        )
        assert failed["success"] is False
        # The failure path must clean up as well.
        assert len(closed_contexts) == 2, (
            f"Expected 2 contexts closed after failure, got {len(closed_contexts)}"
        )
        assert len(closed_browsers) == 2, (
            f"Expected 2 browsers closed after failure, got {len(closed_browsers)}"
        )
        # Each run closed its own context (distinct objects).
        assert closed_contexts[0] is not closed_contexts[1]
        assert closed_browsers[0] is not closed_browsers[1]


def test_cancelled_run_also_closes_its_context(monkeypatch) -> None:
    """A cancelled run must release its browser resources too."""
    import playwright.sync_api as pw_api

    closed_contexts: list = []
    closed_browsers: list = []
    real_ctx_close = pw_api.BrowserContext.close
    real_browser_close = pw_api.Browser.close

    def patched_ctx_close(self, **kwargs):  # noqa: ANN001
        closed_contexts.append(self)
        return real_ctx_close(self, **kwargs)

    def patched_browser_close(self, **kwargs):  # noqa: ANN001
        closed_browsers.append(self)
        return real_browser_close(self, **kwargs)

    monkeypatch.setattr(pw_api.BrowserContext, "close", patched_ctx_close)
    monkeypatch.setattr(pw_api.Browser, "close", patched_browser_close)

    token = CancellationToken()
    token.request("cancel for cleanup check")

    with tempfile.TemporaryDirectory() as tmp:
        result = _run_agent_in_thread(
            "Cancel Cleanup",
            url=get_demo_url(),
            trace_dir=Path(tmp),
            cancel=token,
        )
    assert result["cancelled"] is True
    assert len(closed_contexts) == 1, (
        f"Cancelled run must close its context; got {len(closed_contexts)}"
    )
    assert len(closed_browsers) == 1, (
        f"Cancelled run must close its browser; got {len(closed_browsers)}"
    )


# ---------------------------------------------------------------------------
# Helpers (kept local; the safety wrapper is exercised through the agent
# path, not duplicated here).
# ---------------------------------------------------------------------------

def create_project_in_page(page: Page, project_name: str) -> dict:
    """Fill, submit, and verify state directly in an already-open page.

    Unlike :func:`chimera.agent.create_project` this does NOT launch its own
    browser, so the test fixture owns the lifecycle. The same effect
    (allowlisted actions, bounded retries, explicit postcondition checks)
    is preserved by calling the same primitives.
    """
    from chimera.safety import ActionType, RetryPolicy, execute_with_retry

    policy = RetryPolicy(
        max_attempts=2,
        base_delay_seconds=0.05,
        max_delay_seconds=0.2,
        max_total_seconds=5.0,
    )
    result = {"success": False, "project_name": project_name, "error": None}
    try:
        name_input = page.get_by_label("Project Name")
        execute_with_retry(
            ActionType.FILL.value,
            lambda: name_input.fill(project_name, timeout=ACTION_TIMEOUT_MS),
            policy=policy,
        )
        create_button = page.get_by_role("button", name="Create Project")
        execute_with_retry(
            ActionType.CLICK.value,
            lambda: create_button.click(timeout=ACTION_TIMEOUT_MS),
            policy=policy,
            is_effect_achieved=lambda: page.locator(
                "#confirmation"
            ).is_visible(),
        )
        page.locator("#confirmation").wait_for(
            state="visible", timeout=ACTION_TIMEOUT_MS
        )
        page.locator("#project-list li", has_text=project_name).wait_for(
            state="visible", timeout=ACTION_TIMEOUT_MS
        )
        result["success"] = True
    except Exception as exc:  # noqa: BLE001
        if exc.__cause__ is not None:
            result["error"] = (
                f"{type(exc).__name__}: {exc} "
                f"(caused by {type(exc.__cause__).__name__}: {exc.__cause__})"
            )
        else:
            result["error"] = f"{type(exc).__name__}: {exc}"
    return result
