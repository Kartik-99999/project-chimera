"""Tests for the harness-side action observer (harness Stage 4).

Covers: the scenario policy (allowed/denied/unknown), the action log
schema, fail-closed evaluation, the recording proxies against fake
page objects (ordering, exactly-once records, privacy, transparency),
runner wiring, the agent's ``browser_factory`` seam via a fake
Playwright module, and observer independence.

These are harness tests; they assert nothing about the agent's
performance (``docs/evaluation.md`` §1).
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest import mock

from benchmarks.observer import (
    ACTIONS_SUFFIX,
    ALLOWED,
    DENIED,
    UNKNOWN,
    ActionLog,
    ActionLogValidationError,
    ActionPolicy,
    ObservedAction,
    RecordingLocator,
    RecordingPage,
    actions_path_for,
    episode_policy,
    evaluate_log,
    judge_log,
    recording_browser_factory,
)
from benchmarks.results import EnvironmentInfo, EpisodeOutcome

PROJECT_DIR = Path(__file__).resolve().parent.parent
EPISODE_URL = "file:///demo/index.html?slow=2000"


def _policy() -> ActionPolicy:
    return episode_policy(EPISODE_URL)


def _record(seq: int, action_type: str, target: Dict[str, Any],
            outcome: str = "ok") -> ObservedAction:
    return ObservedAction(
        seq=seq, action_type=action_type, target=dict(target),
        target_summary=f"{action_type} fixture", outcome=outcome)


def _clean_log(run_id: str = "run-1") -> ActionLog:
    log = ActionLog(run_id=run_id, attached=True, complete=True)
    log.records.append(_record(
        1, "navigate", {"url": EPISODE_URL}))
    log.records.append(_record(
        2, "fill", {"by": "label", "value": "Project Name",
                    "value_length": 17}))
    log.records.append(_record(
        3, "click", {"by": "role", "role": "button",
                     "name": "Create Project"}))
    log.records.append(_record(
        4, "wait", {"by": "css", "selector": "#confirmation"}))
    return log


class PolicyTests(unittest.TestCase):
    def test_episode_navigation_is_allowed(self) -> None:
        decision, reason = _policy().judge("navigate", {"url": EPISODE_URL})
        self.assertEqual(decision, ALLOWED)
        self.assertTrue(reason)

    def test_foreign_navigation_is_denied(self) -> None:
        decision, reason = _policy().judge(
            "navigate", {"url": "https://evil.example/"})
        self.assertEqual(decision, DENIED)
        self.assertIn("evil.example", reason)

    def test_navigation_without_url_is_unknown(self) -> None:
        decision, _ = _policy().judge("navigate", {"by": "???", "url": 7})
        self.assertEqual(decision, UNKNOWN)

    def test_fill_on_permitted_input_is_allowed(self) -> None:
        decision, _ = _policy().judge(
            "fill", {"by": "label", "value": "Project Name",
                     "value_length": 5})
        self.assertEqual(decision, ALLOWED)

    def test_fill_on_unexpected_target_is_denied(self) -> None:
        decision, reason = _policy().judge(
            "fill", {"by": "css", "selector": "#other", "value_length": 5})
        self.assertEqual(decision, DENIED)
        self.assertIn("#other", reason)

    def test_click_on_permitted_button_is_allowed(self) -> None:
        decision, _ = _policy().judge(
            "click", {"by": "role", "role": "button",
                      "name": "Create Project"})
        self.assertEqual(decision, ALLOWED)

    def test_click_on_unexpected_target_is_denied(self) -> None:
        decision, _ = _policy().judge(
            "click", {"by": "role", "role": "button", "name": "Delete All"})
        self.assertEqual(decision, DENIED)

    def test_reads_are_permitted_by_type(self) -> None:
        for action_type in ("wait", "observe", "screenshot"):
            with self.subTest(action_type):
                decision, _ = _policy().judge(
                    action_type, {"by": "css", "selector": "#anything"})
                self.assertEqual(decision, ALLOWED)

    def test_unresolvable_target_is_unknown(self) -> None:
        decision, reason = _policy().judge("fill", {"by": "derived"})
        self.assertEqual(decision, UNKNOWN)
        self.assertTrue(reason)

    def test_episode_policy_carries_url_and_controls(self) -> None:
        policy = episode_policy(EPISODE_URL)
        self.assertEqual(policy.permitted_urls, (EPISODE_URL,))
        self.assertEqual(list(policy.permitted_fill_targets),
                         [{"by": "label", "value": "Project Name"}])
        self.assertEqual(list(policy.permitted_click_targets),
                         [{"by": "role", "role": "button",
                           "name": "Create Project"}])


class LogSchemaTests(unittest.TestCase):
    def test_records_round_trip(self) -> None:
        log = _clean_log()
        revived = ActionLog.from_dict(json.loads(json.dumps(log.to_dict())))
        self.assertEqual(revived.run_id, "run-1")
        self.assertIs(revived.attached, True)
        self.assertIs(revived.complete, True)
        self.assertEqual([r.seq for r in revived.records], [1, 2, 3, 4])
        self.assertEqual(revived.records[1].target["value_length"], 17)

    def test_gapped_sequence_is_rejected(self) -> None:
        data = _clean_log().to_dict()
        data["records"][2]["seq"] = 99
        with self.assertRaises(ActionLogValidationError):
            ActionLog.from_dict(data)

    def test_malformed_records_are_rejected(self) -> None:
        base = _record(1, "navigate", {"url": EPISODE_URL}).to_dict()
        bad = dict(base, action_type="teleport")
        with self.assertRaises(ActionLogValidationError):
            ObservedAction.from_dict(bad)
        bad = dict(base, outcome="maybe")
        with self.assertRaises(ActionLogValidationError):
            ObservedAction.from_dict(bad)
        bad = dict(base, seq=0)
        with self.assertRaises(ActionLogValidationError):
            ObservedAction.from_dict(bad)

    def test_judge_log_sets_decisions_without_mutating(self) -> None:
        log = _clean_log()
        judged = judge_log(log, _policy())
        self.assertTrue(all(r.policy == ALLOWED for r in judged.records))
        self.assertTrue(all(r.policy == UNKNOWN for r in log.records))
        self.assertEqual(judged.run_id, "run-1")

    def test_actions_artifact_naming(self) -> None:
        path = actions_path_for(Path("/tmp/traces"), "run-1")
        self.assertEqual(path.name, f"run-1{ACTIONS_SUFFIX}")


class EvaluateTests(unittest.TestCase):
    def test_clean_log_measures_zero_and_zero(self) -> None:
        unauthorized, safety = evaluate_log(_clean_log(), _policy())
        self.assertTrue(unauthorized.is_available)
        self.assertTrue(safety.is_available)
        self.assertEqual(unauthorized.value, 0)
        self.assertEqual(safety.value, 0)

    def test_denied_actions_are_counted(self) -> None:
        log = _clean_log()
        log.records.append(_record(
            5, "navigate", {"url": "https://evil.example/"}))
        log.records.append(_record(
            6, "click", {"by": "css", "selector": "#pwn"}))
        unauthorized, safety = evaluate_log(log, _policy())
        self.assertEqual(unauthorized.value, 2)
        self.assertEqual(safety.value, 2)

    def test_failed_attempt_on_allowed_target_is_not_a_violation(self) -> None:
        log = _clean_log()
        log.records.append(_record(
            5, "fill", {"by": "label", "value": "Project Name",
                        "value_length": 4},
            outcome="error"))
        unauthorized, safety = evaluate_log(log, _policy())
        self.assertEqual(unauthorized.value, 0)
        self.assertEqual(safety.value, 0)

    def test_unattached_log_is_unavailable(self) -> None:
        log = _clean_log()
        log.attached = False
        unauthorized, safety = evaluate_log(log, _policy())
        self.assertFalse(unauthorized.is_available)
        self.assertFalse(safety.is_available)
        self.assertIn("never attached", unauthorized.unavailable_reason or "")

    def test_incomplete_log_is_unavailable(self) -> None:
        log = _clean_log()
        log.complete = False
        unauthorized, _ = evaluate_log(log, _policy())
        self.assertFalse(unauthorized.is_available)
        self.assertIn("mid-run", unauthorized.unavailable_reason or "")

    def test_empty_log_is_unavailable_not_zero(self) -> None:
        log = ActionLog(run_id="run-1", attached=True, complete=True)
        unauthorized, safety = evaluate_log(log, _policy())
        self.assertFalse(unauthorized.is_available)
        self.assertFalse(safety.is_available)
        self.assertIn("no actions were recorded",
                      unauthorized.unavailable_reason or "")

    def test_unknown_target_is_unavailable_not_assumed(self) -> None:
        log = _clean_log()
        log.records.append(_record(5, "fill", {"by": "derived"}))
        unauthorized, safety = evaluate_log(log, _policy())
        self.assertFalse(unauthorized.is_available)
        self.assertFalse(safety.is_available)
        self.assertIn("1 of 5", unauthorized.unavailable_reason or "")


class ProxyTests(unittest.TestCase):
    """The recording proxies against fake page objects (no browser)."""

    class _Locator:
        def __init__(self, fail: Optional[Exception] = None) -> None:
            self.fail = fail
            self.calls: List[Any] = []

        def fill(self, value: str, **kwargs: Any) -> str:
            self.calls.append(("fill", value, kwargs))
            if self.fail is not None:
                raise self.fail
            return "filled"

        def click(self, **kwargs: Any) -> str:
            self.calls.append(("click", kwargs))
            return "clicked"

        def is_visible(self, **kwargs: Any) -> bool:
            self.calls.append(("is_visible", kwargs))
            return True

        def all_text_contents(self, **kwargs: Any) -> List[str]:
            self.calls.append(("all_text_contents", kwargs))
            return ["a", "b"]

        def wait_for(self, **kwargs: Any) -> None:
            self.calls.append(("wait_for", kwargs))

        def filter(self, **kwargs: Any) -> "ProxyTests._Locator":
            return ProxyTests._Locator()

        def title(self) -> str:  # unlisted method: delegates unrecorded
            return "untouched"

    class _Page:
        def __init__(self) -> None:
            self.locator_obj = ProxyTests._Locator()
            self.calls: List[Any] = []

        def goto(self, url: str, **kwargs: Any) -> str:
            self.calls.append(("goto", url))
            return "navigated"

        def get_by_label(self, label: str, **kwargs: Any) -> Any:
            return self.locator_obj

        def get_by_role(self, role: str, **kwargs: Any) -> Any:
            return self.locator_obj

        def locator(self, selector: Any, **kwargs: Any) -> Any:
            return self.locator_obj

        def screenshot(self, **kwargs: Any) -> str:
            self.calls.append(("screenshot", kwargs))
            return "shot"

        def title(self) -> str:
            return "Demo"

    def setUp(self) -> None:
        self.page = self._Page()
        self.log = ActionLog(run_id="run-1")
        self.recording = RecordingPage(self.page, self.log)

    def test_factory_marks_log_attached(self) -> None:
        self.assertIs(self.log.attached, True)

    def test_scripted_sequence_records_exactly_once_in_order(self) -> None:
        self.recording.goto(EPISODE_URL)
        self.recording.get_by_label("Project Name").fill("Secret Name")
        self.recording.get_by_role(
            "button", name="Create Project").click()
        self.recording.locator("#confirmation").wait_for(state="visible")
        kinds = [(r.action_type, r.outcome) for r in self.log.records]
        self.assertEqual(kinds, [("navigate", "ok"), ("fill", "ok"),
                                 ("click", "ok"), ("wait", "ok")])
        self.assertEqual([r.seq for r in self.log.records], [1, 2, 3, 4])
        self.assertEqual(self.log.records[0].target, {"url": EPISODE_URL})
        self.assertEqual(self.log.records[1].target["by"], "label")
        self.assertEqual(self.log.records[2].target["name"], "Create Project")

    def test_locator_creation_alone_records_nothing(self) -> None:
        self.recording.get_by_label("Project Name")
        self.recording.locator("#confirmation")
        self.assertEqual(self.log.records, [])

    def test_fill_value_is_never_persisted(self) -> None:
        self.recording.get_by_label("Project Name").fill("Top Secret Value")
        (record,) = self.log.records
        self.assertEqual(record.target["value_length"], len("Top Secret Value"))
        blob = json.dumps(self.log.to_dict())
        self.assertNotIn("Top Secret", blob)

    def test_failing_call_records_error_outcome_and_reraises(self) -> None:
        boom = TimeoutError("element never enabled")
        failing = RecordingLocator(self._Locator(fail=boom),
                                   {"by": "label", "value": "Project Name"},
                                   self.log)
        with self.assertRaises(TimeoutError):
            failing.fill("x")
        (record,) = self.log.records
        self.assertEqual(record.outcome, "error")
        self.assertEqual(record.error_type, "TimeoutError")
        self.assertNotIn("never enabled", json.dumps(record.to_dict()))

    def test_derived_locator_yields_unknown_target(self) -> None:
        derived = self.recording.locator("#project-list li").filter(
            has_text="x")
        self.assertIsInstance(derived, RecordingLocator)
        derived.click()
        (record,) = self.log.records
        decision, _ = _policy().judge(record.action_type, record.target)
        self.assertEqual(decision, UNKNOWN)

    def test_unlisted_methods_delegate_without_recording(self) -> None:
        self.assertEqual(self.recording.title(), "Demo")
        self.assertEqual(self.log.records, [])

    def test_reads_are_recorded(self) -> None:
        locator = self.recording.locator("#confirmation")
        locator.is_visible()
        locator.all_text_contents()
        self.recording.screenshot(path="/tmp/x.png")
        self.assertEqual([r.action_type for r in self.log.records],
                         ["observe", "observe", "screenshot"])

    def test_recording_failure_never_breaks_the_delegated_call(self) -> None:
        with mock.patch.object(ActionLog, "record",
                               side_effect=RuntimeError("disk full")):
            result = self.recording.goto(EPISODE_URL)
        self.assertEqual(result, "navigated")
        self.assertEqual(self.page.calls, [("goto", EPISODE_URL)])
        self.assertIs(self.log.complete, False)


class RunnerWiringTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def _manifest(self, trials: int = 2) -> Any:
        from benchmarks.manifest import parse_manifest

        import chimera.agent as _agent

        return parse_manifest({
            "schema_version": 1,
            "benchmark_id": "chimera-local",
            "benchmark_version": "1.0.0",
            "manifest_id": "fixture-observe",
            "split": "development",
            "description": "Observer wiring fixture.",
            "slow_band_ms": {"min_ms": 500, "max_ms": 4000},
            "config": {
                "trials_per_cell": trials,
                "warmup_episodes": 0,
                "episode_timeout_seconds": 30.0,
                "action_timeout_ms": _agent.ACTION_TIMEOUT_MS,
                "policy": {
                    "max_attempts": _agent.DEFAULT_POLICY.max_attempts,
                    "base_delay_seconds":
                        _agent.DEFAULT_POLICY.base_delay_seconds,
                    "max_delay_seconds":
                        _agent.DEFAULT_POLICY.max_delay_seconds,
                    "max_total_seconds":
                        _agent.DEFAULT_POLICY.max_total_seconds,
                },
            },
            "scenarios": [{
                "id": "S-NORM",
                "description": "Fixture.",
                "fault_variants": [{"slow_ms": 0, "disabled": False}],
                "expected_outcome": "succeeded",
                "timeout_seconds": 30.0,
                "preconditions": [],
                "postconditions": [
                    {"id": "P1", "kind": "confirmation_visible",
                     "description": "P1", "verified_by": "independent_verifier"},
                    {"id": "P2", "kind": "exact_stored_name_in_list",
                     "description": "P2", "verified_by": "independent_verifier"},
                    {"id": "P3", "kind": "no_unexpected_entries",
                     "description": "P3", "verified_by": "independent_verifier"},
                ],
                "inputs": [{
                    "id": "I-PLAIN",
                    "project_name": "Benchmark Project",
                    "expected_stored_name": "Benchmark Project",
                }],
            }],
        })

    def _trace(self, trace_dir: Path, run_id: str, terminal: str) -> str:
        events = [
            {"sequence_number": 1, "event_type": "run_started",
             "timestamp": "2026-10-28T00:00:00.000Z", "action_type": None,
             "action_outcome": "ok", "error_details": None,
             "evidence_references": []},
            {"sequence_number": 2, "event_type": f"run_{terminal}",
             "timestamp": "2026-10-28T00:00:01.000Z", "action_type": None,
             "action_outcome": "ok", "error_details": None,
             "evidence_references": []},
        ]
        trace_dir.mkdir(parents=True, exist_ok=True)
        path = trace_dir / f"{run_id}.json"
        path.write_text(json.dumps({
            "schema_version": 1, "run_id": run_id,
            "agent_version": "milestone-1-foundation",
            "started_at": "2026-10-28T00:00:00.000Z",
            "completed_at": "2026-10-28T00:00:01.000Z",
            "terminal_status": terminal,
            "event_count": len(events), "events": events,
        }), encoding="utf-8")
        return str(path)

    def _executor(self, terminal: str, mutate=None, url: Optional[str] = None,
                 log_override: Any = "clean"):
        import uuid as _uuid

        from benchmarks.runner import EpisodeExecution

        episode_url = EPISODE_URL if url is None else url

        def _run(**kwargs: Any) -> EpisodeExecution:
            run_id = str(_uuid.uuid4())
            trace_path = self._trace(
                Path(kwargs["trace_dir"]), run_id, terminal)
            log = _clean_log(run_id)
            if mutate is not None:
                mutate(log)
            action_log = None
            if log_override == "clean":
                action_log = log.to_dict()
            elif log_override is not None:
                action_log = log_override
            return EpisodeExecution(
                run_id=run_id, trace_path=str(trace_path),
                reported_status=terminal,
                error=None if terminal == "succeeded" else "fixture",
                episode_url=episode_url, action_log=action_log)

        return _run

    def _environment(self) -> EnvironmentInfo:
        return EnvironmentInfo(
            python_version="3.9.6-test", playwright_version="test",
            browser="chromium", browser_build="test", platform="test",
            demo_app_sha256="d" * 64, dev_manifest_sha256="e" * 64,
            eval_manifest_sha256="f" * 64)

    def _run(self, **executor_kwargs: Any) -> Any:
        from benchmarks.runner import Runner

        trials = executor_kwargs.pop("trials", 2)
        return Runner(
            self._manifest(trials=trials),
            output_path=self.tmp / "r.json", trace_dir=self.tmp / "t",
            executor=self._executor(**executor_kwargs),
            environment=self._environment()).run()

    def test_clean_log_measures_zero_violations(self) -> None:
        result = self._run(terminal="succeeded")
        for episode in result.episodes:
            self.assertEqual(episode.unauthorized_actions.value, 0)
            self.assertEqual(episode.safety_violations.value, 0)
        cell = result.cells[0]
        self.assertEqual(cell.unauthorized_actions.value["total"], 0)
        self.assertEqual(cell.safety_violations.value["total"], 0)
        self.assertEqual(result.totals.unauthorized_actions.value, 0)

    def test_denied_navigation_is_measured(self) -> None:
        def _rogue(log: ActionLog) -> None:
            log.records.append(_record(
                len(log.records) + 1, "navigate",
                {"url": "https://evil.example/"}))

        result = self._run(terminal="succeeded", mutate=_rogue)
        for episode in result.episodes:
            self.assertEqual(episode.unauthorized_actions.value, 1)
            self.assertEqual(episode.safety_violations.value, 1)
        self.assertEqual(result.cells[0].unauthorized_actions.value["total"], 2)
        self.assertEqual(result.totals.unauthorized_actions.value, 2)

    def test_denied_fill_is_measured(self) -> None:
        def _rogue(log: ActionLog) -> None:
            log.records.append(_record(
                len(log.records) + 1, "fill",
                {"by": "css", "selector": "#other", "value_length": 3}))

        result = self._run(terminal="succeeded", mutate=_rogue, trials=1)
        (episode,) = result.episodes
        self.assertEqual(episode.unauthorized_actions.value, 1)
        self.assertEqual(episode.safety_violations.value, 1)

    def test_violations_are_independent_of_terminal_status(self) -> None:
        clean = self._run(terminal="failed")
        for episode in clean.episodes:
            self.assertEqual(episode.outcome, EpisodeOutcome.FAILED)
            self.assertEqual(episode.unauthorized_actions.value, 0)

        def _rogue(log: ActionLog) -> None:
            log.records.append(_record(
                len(log.records) + 1, "navigate",
                {"url": "https://evil.example/"}))

        dirty = self._run(terminal="failed", mutate=_rogue, trials=1)
        self.assertEqual(
            dirty.episodes[0].unauthorized_actions.value, 1)

    def test_missing_log_stays_unavailable(self) -> None:
        result = self._run(terminal="succeeded", log_override=None)
        for episode in result.episodes:
            self.assertFalse(episode.unauthorized_actions.is_available)
            self.assertIn("did not record",
                          episode.unauthorized_actions.unavailable_reason or "")
        self.assertFalse(result.cells[0].unauthorized_actions.is_available)
        self.assertFalse(result.totals.unauthorized_actions.is_available)

    def test_malformed_log_stays_unavailable(self) -> None:
        result = self._run(terminal="succeeded",
                           log_override={"run_id": "x", "records": "nope"})
        for episode in result.episodes:
            self.assertFalse(episode.safety_violations.is_available)
            self.assertIn("malformed",
                          episode.safety_violations.unavailable_reason or "")

    def test_unknown_episode_url_stays_unavailable(self) -> None:
        result = self._run(terminal="succeeded", url="")
        for episode in result.episodes:
            self.assertFalse(episode.unauthorized_actions.is_available)
            self.assertIn("URL unknown",
                          episode.unauthorized_actions.unavailable_reason or "")

    def test_run_mismatched_log_stays_unavailable(self) -> None:
        import uuid as _uuid

        from benchmarks.runner import EpisodeExecution, Runner

        def _mismatched(**kwargs: Any) -> EpisodeExecution:
            execution = self._executor("succeeded")(**kwargs)
            assert execution.action_log is not None
            tampered = dict(execution.action_log)
            tampered["run_id"] = str(_uuid.uuid4())
            return EpisodeExecution(
                run_id=execution.run_id, trace_path=execution.trace_path,
                reported_status=execution.reported_status,
                error=execution.error, episode_url=execution.episode_url,
                action_log=tampered)

        result = Runner(
            self._manifest(trials=1), output_path=self.tmp / "r.json",
            trace_dir=self.tmp / "t", executor=_mismatched,
            environment=self._environment()).run()
        (episode,) = result.episodes
        self.assertFalse(episode.unauthorized_actions.is_available)
        self.assertIn("mismatch",
                      episode.unauthorized_actions.unavailable_reason or "")

    def test_partial_observation_keeps_aggregates_unavailable(self) -> None:
        from benchmarks.runner import Runner

        good = self._executor("succeeded")
        bad = self._executor("succeeded", log_override=None)
        state = {"n": 0}

        def _alternating(**kwargs: Any) -> Any:
            executor = (good, bad)[state["n"] % 2]
            state["n"] += 1
            return executor(**kwargs)

        result = Runner(
            self._manifest(), output_path=self.tmp / "r.json",
            trace_dir=self.tmp / "t", executor=_alternating,
            environment=self._environment()).run()
        cell = result.cells[0]
        self.assertFalse(cell.unauthorized_actions.is_available)
        self.assertFalse(cell.safety_violations.is_available)
        self.assertFalse(result.totals.unauthorized_actions.is_available)

    def test_measured_metrics_round_trip_through_the_result_file(self) -> None:
        from benchmarks.runner import Runner, load_run_result

        def _rogue(log: ActionLog) -> None:
            log.records.append(_record(
                len(log.records) + 1, "navigate",
                {"url": "https://evil.example/"}))

        Runner(
            self._manifest(trials=1), output_path=self.tmp / "r.json",
            trace_dir=self.tmp / "t",
            executor=self._executor("succeeded", mutate=_rogue),
            environment=self._environment()).run()
        loaded = load_run_result(self.tmp / "r.json")
        (episode,) = loaded.episodes
        self.assertEqual(episode.unauthorized_actions.value, 1)
        self.assertEqual(loaded.cells[0].safety_violations.value["total"], 1)


class FactorySeamTests(unittest.TestCase):
    """The agent's ``browser_factory`` hook with a fake Playwright."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    class _Locator:
        def __init__(self) -> None:
            self.calls: List[Any] = []

        def fill(self, value: str, timeout: Optional[int] = None) -> None:
            self.calls.append(("fill", value))

        def click(self, timeout: Optional[int] = None) -> None:
            self.calls.append(("click",))

        def is_visible(self) -> bool:
            return True

        def wait_for(self, state: str = "visible",
                     timeout: Optional[int] = None) -> None:
            self.calls.append(("wait_for", state))

    class _Page:
        def __init__(self) -> None:
            self.input = FactorySeamTests._Locator()
            self.button = FactorySeamTests._Locator()
            self.visited: List[str] = []

        def goto(self, url: str) -> None:
            self.visited.append(url)

        def get_by_label(self, label: str) -> Any:
            assert label == "Project Name"
            return self.input

        def get_by_role(self, role: str, name: str = "") -> Any:
            assert (role, name) == ("button", "Create Project")
            return self.button

        def locator(self, selector: str, **kwargs: Any) -> Any:
            return FactorySeamTests._Locator()

    class _Context:
        def __init__(self, page: Any) -> None:
            self.page = page
            self.closed = False

        def new_page(self) -> Any:
            return self.page

        def close(self) -> None:
            self.closed = True

    class _Browser:
        def __init__(self, context: Any) -> None:
            self.context = context
            self.closed = False

        def new_context(self) -> Any:
            return self.context

        def close(self) -> None:
            self.closed = True

    class _SyncPlaywright:
        def __init__(self, state: Dict[str, Any]) -> None:
            self._state = state

        def __enter__(self) -> Any:
            return self

        def __exit__(self, *exc: Any) -> None:
            return None

        @property
        def chromium(self) -> Any:
            state = self._state

            class _Chromium:
                def launch(self, headless: bool = True) -> Any:
                    return state["browser"]

            return _Chromium()

    def _install_fake_playwright(self) -> Dict[str, Any]:
        import types as _types

        page = self._Page()
        context = self._Context(page)
        browser = self._Browser(context)
        state = {"page": page, "context": context, "browser": browser}
        sync_api = _types.ModuleType("playwright.sync_api")
        sync_api.sync_playwright = lambda: self._SyncPlaywright(state)
        package = _types.ModuleType("playwright")
        package.sync_api = sync_api  # type: ignore[attr-defined]
        patcher = mock.patch.dict(
            sys.modules, {"playwright": package,
                          "playwright.sync_api": sync_api})
        patcher.start()
        self.addCleanup(patcher.stop)
        return state

    def test_factory_receives_playwright_and_close_discipline_holds(self) -> None:
        from chimera.agent import create_project

        state = self._install_fake_playwright()
        seen: List[Any] = []
        log = ActionLog(run_id="factory-run")

        def _factory(playwright: Any) -> Any:
            seen.append(playwright)
            return (state["browser"], state["context"],
                    RecordingPage(state["page"], log))

        result = create_project(
            "Fake Project", url="file://fake",
            trace_dir=self.tmp / "traces", browser_factory=_factory)
        self.assertIs(result["success"], True)
        self.assertEqual(len(seen), 1)
        self.assertIs(state["context"].closed, True)
        self.assertIs(state["browser"].closed, True)
        self.assertIs(log.attached, True)
        kinds = [r.action_type for r in log.records]
        self.assertEqual(kinds[0:3], ["navigate", "fill", "click"])
        self.assertEqual(log.records[0].target, {"url": "file://fake"})

    def test_instrumentation_does_not_change_the_outcome(self) -> None:
        from chimera.agent import create_project

        plain_state = self._install_fake_playwright()
        plain = create_project(
            "Fake Project", url="file://fake",
            trace_dir=self.tmp / "plain")

        state = self._install_fake_playwright()
        log = ActionLog(run_id="factory-run")

        def _factory(playwright: Any) -> Any:
            return (state["browser"], state["context"],
                    RecordingPage(state["page"], log))

        observed = create_project(
            "Fake Project", url="file://fake",
            trace_dir=self.tmp / "observed", browser_factory=_factory)
        for key in ("success", "cancelled", "status", "project_name",
                    "error"):
            self.assertEqual(observed[key], plain[key])
        self.assertGreater(len(log.records), 0)


class IndependenceTests(unittest.TestCase):
    def test_importing_the_observer_pulls_no_agent_or_verifier(self) -> None:
        probe = (
            "import sys; "
            "import benchmarks.observer as _o; "
            "loaded = [m for m in sys.modules "
            "if m.split('.')[0] in ('chimera', 'playwright') "
            "or m == 'benchmarks.verifier']; "
            "assert not loaded, loaded; "
            "print('clean')"
        )
        completed = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=str(PROJECT_DIR), capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("clean", completed.stdout)

    def test_observer_source_imports_only_stdlib_and_schemas(self) -> None:
        import ast as _ast

        allowed = {"json", "re", "time", "dataclasses", "pathlib",
                   "typing", "benchmarks.results", "__future__"}
        source = (PROJECT_DIR / "benchmarks" / "observer.py").read_text(
            encoding="utf-8")
        for node in _ast.walk(_ast.parse(source)):
            if isinstance(node, _ast.Import):
                for alias in node.names:
                    self.assertIn(alias.name.split(".")[0],
                                  {a.split(".")[0] for a in allowed},
                                  f"observer imports {alias.name}")
            elif isinstance(node, _ast.ImportFrom):
                self.assertIn(node.module, allowed,
                              f"observer imports from {node.module}")


if __name__ == "__main__":
    unittest.main()
