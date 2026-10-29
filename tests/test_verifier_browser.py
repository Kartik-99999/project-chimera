"""Browser tests for harness-side observation and verification.

Two episodes against the real demo app in Chromium: one success and one
persistent-fault failure. Each captures an independent state snapshot
through the agent's ``observe`` hook and evaluates P1–P3 from it. These
are the only Stage 3 tests that launch a browser.
"""

from benchmarks.verifier import capture_page_state, verify_postconditions
from chimera.agent import create_project, get_demo_url_with_faults


def test_success_snapshot_verifies_exactly():
    result = create_project("Browser Snapshot", observe=capture_page_state)
    assert result["success"] is True, f"Expected success: {result['error']}"
    assert result["observation_error"] is None
    assert result["observation"] == {
        "confirmation_visible": True,
        "items": ["Browser Snapshot"],
    }
    evidence = verify_postconditions(
        snapshot={**result["observation"], "run_id": result["run_id"]},
        expected_stored_name="Browser Snapshot",
        snapshot_ref=result["trace_path"] or "",
        run_id=result["run_id"],
    )
    assert evidence.status == "verified"
    assert evidence.all_satisfied is True


def test_disabled_fault_snapshot_shows_empty_hidden_state():
    result = create_project(
        "Never Created",
        url=get_demo_url_with_faults(disabled=True),
        observe=capture_page_state,
    )
    assert result["success"] is False
    assert result["observation_error"] is None
    assert result["observation"] == {
        "confirmation_visible": False,
        "items": [],
    }
    evidence = verify_postconditions(
        snapshot={**result["observation"], "run_id": result["run_id"]},
        expected_stored_name="Never Created",
        snapshot_ref=result["trace_path"] or "",
        run_id=result["run_id"],
    )
    assert evidence.status == "verified"
    assert evidence.all_satisfied is False
    verdicts = {c.postcondition_id: c.satisfied for c in evidence.checks}
    assert verdicts == {"P1": False, "P2": False, "P3": False}
