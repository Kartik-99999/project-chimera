"""Browser tests for harness-side action observation.

Two episodes against the real demo app in Chromium, both through the
recording browser factory: one success and one persistent-fault
failure. Each asserts the exact observed action sequence, that every
action is judged allowed, and that the measured violation counts are
zero — including on the failed episode, proving the counts are
independent of the agent's terminal status.
"""

from benchmarks.observer import (
    ActionLog,
    episode_policy,
    evaluate_log,
    recording_browser_factory,
)
from chimera.agent import create_project, get_demo_url_with_faults


def _observed(url, **kwargs):
    log = ActionLog(run_id="")
    result = create_project(
        url=url,
        browser_factory=recording_browser_factory(log),
        **kwargs,
    )
    log.run_id = result["run_id"]
    return result, log


def test_success_episode_observes_exact_allowed_sequence():
    url = get_demo_url_with_faults()
    result, log = _observed(url, project_name="Observed Project")
    assert result["success"] is True, f"Expected success: {result['error']}"
    kinds = [(r.action_type, r.outcome) for r in log.records]
    assert kinds == [
        ("navigate", "ok"),
        ("fill", "ok"),
        ("click", "ok"),
        ("wait", "ok"),
        ("wait", "ok"),
    ]
    assert log.records[0].target == {"url": url}
    unauthorized, safety = evaluate_log(log, episode_policy(url))
    assert unauthorized.value == 0
    assert safety.value == 0


def test_failed_episode_still_measures_zero_violations():
    url = get_demo_url_with_faults(disabled=True)
    result, log = _observed(url, project_name="Never Created")
    assert result["success"] is False
    kinds = [(r.action_type, r.outcome) for r in log.records]
    assert kinds[0] == ("navigate", "ok")
    assert kinds[1] == ("fill", "error")
    # The failed fill still targeted the permitted input.
    assert log.records[1].target["by"] == "label"
    unauthorized, safety = evaluate_log(log, episode_policy(url))
    assert unauthorized.value == 0
    assert safety.value == 0
