"""Tests for the benchmark harness runner (harness Stage 2).

Covers: manifest loading and invalid manifests, deterministic trial
ordering, per-episode state isolation, matching and mismatching retry
policies (AMB-9/ADR-005), refusal before execution, timeout handling,
result persistence and round-tripping, execution and trace-integrity
failures, and unavailable metrics retaining their reasons.

All episodes run against fake executors that write fixture traces to a
temporary directory — no browser is launched. These are harness tests;
they assert nothing about the agent's performance
(``docs/evaluation.md`` §1).
"""

from __future__ import annotations

import copy
import dataclasses
import json
import sys
import tempfile
import time
import types
import unittest
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest import mock

from benchmarks.manifest import ManifestValidationError, load_manifest, parse_manifest
from benchmarks.results import EpisodeOutcome, RunResult
from benchmarks.runner import (
    ConfigurationError,
    EpisodeExecution,
    PolicyMismatchError,
    Runner,
    RunnerError,
    TraceIntegrityError,
    check_policy_alignment,
    collect_environment,
    episode_budget_seconds,
    load_run_result,
    run_manifest,
)


MANIFEST_DIR = Path(__file__).resolve().parent.parent / "benchmarks" / "manifests"

# The agent's effective policy, read live so the fixture tracks the
# product. This mirrors what check_policy_alignment compares against.
import chimera.agent as _agent_module

AGENT_POLICY = {
    "max_attempts": _agent_module.DEFAULT_POLICY.max_attempts,
    "base_delay_seconds": _agent_module.DEFAULT_POLICY.base_delay_seconds,
    "max_delay_seconds": _agent_module.DEFAULT_POLICY.max_delay_seconds,
    "max_total_seconds": _agent_module.DEFAULT_POLICY.max_total_seconds,
}
AGENT_ACTION_TIMEOUT_MS = _agent_module.ACTION_TIMEOUT_MS


def _postconditions() -> List[Dict[str, Any]]:
    return [
        {"id": "P1", "kind": "confirmation_visible",
         "description": "Confirmation is visible.",
         "verified_by": "independent_verifier"},
        {"id": "P2", "kind": "exact_stored_name_in_list",
         "description": "Exact stored name in list.",
         "verified_by": "independent_verifier"},
        {"id": "P3", "kind": "no_unexpected_entries",
         "description": "No unexpected entries.",
         "verified_by": "independent_verifier"},
    ]


def _scenario(
    scenario_id: str = "S-NORM",
    *,
    slow_ms: int = 0,
    disabled: bool = False,
    expected_outcome: str = "succeeded",
    timeout_seconds: float = 30.0,
    input_ids: Tuple[str, ...] = ("I-PLAIN",),
) -> Dict[str, Any]:
    inputs = [
        {"id": input_id, "project_name": f"Project {input_id}",
         "expected_stored_name": f"Project {input_id}"}
        for input_id in input_ids
    ]
    return {
        "id": scenario_id,
        "description": f"Fixture scenario {scenario_id}.",
        "fault_variants": [{"slow_ms": slow_ms, "disabled": disabled}],
        "expected_outcome": expected_outcome,
        "timeout_seconds": timeout_seconds,
        "preconditions": [],
        "postconditions": _postconditions(),
        "inputs": inputs,
    }


def _manifest_dict(
    *,
    manifest_id: str = "fixture-dev",
    split: str = "development",
    trials_per_cell: int = 2,
    warmup_episodes: int = 1,
    episode_timeout_seconds: float = 30.0,
    scenarios: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "benchmark_id": "chimera-local",
        "benchmark_version": "1.0.0",
        "manifest_id": manifest_id,
        "split": split,
        "description": "Runner test fixture.",
        "slow_band_ms": {"min_ms": 500, "max_ms": 4000},
        "config": {
            "trials_per_cell": trials_per_cell,
            "warmup_episodes": warmup_episodes,
            "episode_timeout_seconds": episode_timeout_seconds,
            "action_timeout_ms": AGENT_ACTION_TIMEOUT_MS,
            "policy": dict(AGENT_POLICY),
        },
        "scenarios": scenarios if scenarios is not None else [_scenario()],
    }


def _write_trace(
    trace_dir: Path,
    run_id: str,
    terminal: str,
    *,
    attempts: Tuple[str, ...] = ("navigate", "fill", "click"),
) -> Path:
    """Write a minimal but integrity-valid trace artifact."""
    events: List[Dict[str, Any]] = []
    seq = 0

    def _event(event_type: str, **fields: Any) -> None:
        nonlocal seq
        seq += 1
        base = {
            "sequence_number": seq,
            "event_type": event_type,
            "timestamp": "2026-10-28T00:00:00.000Z",
            "action_type": None,
            "action_outcome": "ok",
            "error_details": None,
            "evidence_references": [],
        }
        base.update(fields)
        events.append(base)

    _event("run_started", evidence_references=["url=file://fixture"])
    for action in attempts:
        _event("action_attempted", action_type=action)
        if terminal == "failed" and action == attempts[-1]:
            _event("action_failed", action_type=action, action_outcome="failure",
                   error_details={"type": "TimeoutError", "message": "fixture"})
        elif terminal == "cancelled" and action == attempts[-1]:
            break
        else:
            _event("action_succeeded", action_type=action)
    outcome = {"succeeded": "ok", "failed": "failure", "cancelled": "cancelled"}[terminal]
    _event(f"run_{terminal}", action_outcome=outcome)
    artifact = {
        "schema_version": 1,
        "run_id": run_id,
        "agent_version": "milestone-1-foundation",
        "started_at": "2026-10-28T00:00:00.000Z",
        "completed_at": "2026-10-28T00:00:01.000Z",
        "terminal_status": terminal,
        "event_count": len(events),
        "events": events,
    }
    path = trace_dir / f"{run_id}.json"
    trace_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact), encoding="utf-8")
    return path


class _FixtureEnvironment:
    """A fixed environment record so runs never probe the real one."""

    @staticmethod
    def make() -> Any:
        from benchmarks.results import EnvironmentInfo

        return EnvironmentInfo(
            python_version="3.9.6-test",
            playwright_version="1.60.0-test",
            browser="chromium",
            browser_build="test-build",
            platform="test-platform",
            demo_app_sha256="d" * 64,
            dev_manifest_sha256="e" * 64,
            eval_manifest_sha256="f" * 64,
        )


class RecordingExecutor:
    """A fake executor that writes fixture traces and records its calls."""

    def __init__(self, terminal: str = "succeeded") -> None:
        self.terminal = terminal
        self.calls: List[Dict[str, Any]] = []

    def __call__(self, **kwargs: Any) -> EpisodeExecution:
        run_id = str(uuid.uuid4())
        trace_path = _write_trace(kwargs["trace_dir"], run_id, self.terminal)
        self.calls.append({
            "scenario_id": kwargs["scenario"].id,
            "input_id": kwargs["task_input"].id,
            # The token object itself is retained: comparing bare id()
            # values would be flaky because CPython reuses freed ids.
            "token": kwargs["token"],
            "timeout_seconds": kwargs["timeout_seconds"],
            "run_id": run_id,
        })
        return EpisodeExecution(
            run_id=run_id,
            trace_path=str(trace_path),
            reported_status=self.terminal,
            error=None if self.terminal == "succeeded"
            else f"{self.terminal} (fixture)",
        )


class RunnerTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.output_path = self.tmp / "result.json"
        self.trace_dir = self.tmp / "traces"

    def _manifest_path(self, data: Dict[str, Any], name: str = "m.json") -> Path:
        path = self.tmp / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def _runner(self, data: Dict[str, Any], **overrides: Any) -> Runner:
        manifest = parse_manifest(data)
        kwargs: Dict[str, Any] = dict(
            output_path=self.output_path,
            trace_dir=self.trace_dir,
            environment=_FixtureEnvironment.make(),
        )
        kwargs.update(overrides)
        return Runner(manifest, **kwargs)


class ManifestLoadingTests(RunnerTestBase):
    def test_run_manifest_loads_and_validates_a_fixture(self) -> None:
        path = self._manifest_path(_manifest_dict())
        executor = RecordingExecutor()
        result = run_manifest(
            path, self.output_path, trace_dir=self.trace_dir,
            executor=executor, environment=_FixtureEnvironment.make(),
        )
        self.assertEqual(result.manifest_id, "fixture-dev")
        self.assertEqual(result.totals.episodes, 2)  # 1 cell x 2 trials
        self.assertEqual(len(executor.calls), 3)  # + 1 warm-up

    def test_invalid_json_is_refused_before_execution(self) -> None:
        path = self.tmp / "bad.json"
        path.write_text("{not json", encoding="utf-8")
        executor = RecordingExecutor()
        with self.assertRaises(ManifestValidationError):
            run_manifest(path, self.output_path, trace_dir=self.trace_dir,
                         executor=executor)
        self.assertEqual(executor.calls, [])
        self.assertFalse(self.output_path.exists())

    def test_unsupported_schema_version_is_refused(self) -> None:
        data = _manifest_dict()
        data["schema_version"] = 999
        path = self._manifest_path(data)
        executor = RecordingExecutor()
        with self.assertRaises(ManifestValidationError):
            run_manifest(path, self.output_path, trace_dir=self.trace_dir,
                         executor=executor)
        self.assertEqual(executor.calls, [])

    def test_unsupported_scenario_is_refused_before_execution(self) -> None:
        data = _manifest_dict(scenarios=[_scenario("S-MULTI")])
        runner = self._runner(data, executor=RecordingExecutor())
        with self.assertRaises(ConfigurationError) as ctx:
            runner.run()
        self.assertIn("S-MULTI", str(ctx.exception))
        self.assertFalse(self.output_path.exists())
        self.assertFalse(self.trace_dir.exists())  # no episode state created

    def test_unsupported_baseline_is_refused_before_execution(self) -> None:
        executor = RecordingExecutor()
        runner = self._runner(_manifest_dict(), executor=executor, baseline="A")
        with self.assertRaises(ConfigurationError) as ctx:
            runner.run()
        self.assertIn("baseline", str(ctx.exception))
        self.assertEqual(executor.calls, [])
        self.assertFalse(self.output_path.exists())


class DeterministicOrderingTests(RunnerTestBase):
    def _order_fixture(self) -> Dict[str, Any]:
        return _manifest_dict(
            trials_per_cell=2,
            warmup_episodes=1,
            scenarios=[
                _scenario("S-NORM", input_ids=("I-PLAIN", "I-SPACE")),
                _scenario("S-SLOW", slow_ms=2000, input_ids=("I-PLAIN",)),
            ],
        )

    def _call_keys(self, executor: RecordingExecutor) -> List[Tuple[str, str]]:
        return [(c["scenario_id"], c["input_id"]) for c in executor.calls]

    def test_cells_run_in_manifest_order_trials_in_sequence(self) -> None:
        executor = RecordingExecutor()
        self._runner(self._order_fixture(), executor=executor).run()
        # Warm-up replays the first cell; then each cell runs its trials
        # in sequence, cells in manifest-declared order.
        self.assertEqual(self._call_keys(executor), [
            ("S-NORM", "I-PLAIN"),  # warm-up
            ("S-NORM", "I-PLAIN"), ("S-NORM", "I-PLAIN"),
            ("S-NORM", "I-SPACE"), ("S-NORM", "I-SPACE"),
            ("S-SLOW", "I-PLAIN"), ("S-SLOW", "I-PLAIN"),
        ])

    def test_trial_ids_follow_execution_order(self) -> None:
        result = self._runner(
            self._order_fixture(), executor=RecordingExecutor()).run()
        self.assertEqual(
            [e.trial_id for e in result.episodes],
            ["warmup:0001", "trial-0001", "trial-0002", "trial-0003",
             "trial-0004", "trial-0005", "trial-0006"],
        )

    def test_two_runs_produce_the_same_order(self) -> None:
        first = RecordingExecutor()
        second = RecordingExecutor()
        self._runner(self._order_fixture(), executor=first).run()
        self._runner(self._order_fixture(), executor=second,
                     output_path=self.tmp / "r2.json",
                     trace_dir=self.tmp / "traces2").run()
        self.assertEqual(self._call_keys(first), self._call_keys(second))


class IsolationTests(RunnerTestBase):
    def test_each_episode_gets_a_fresh_cancellation_token(self) -> None:
        executor = RecordingExecutor()
        self._runner(_manifest_dict(trials_per_cell=3, warmup_episodes=1),
                     executor=executor).run()
        tokens = [c["token"] for c in executor.calls]
        self.assertEqual(len(tokens), 4)
        for index, token in enumerate(tokens):
            for other in tokens[index + 1:]:
                self.assertIsNot(token, other)

    def test_each_episode_gets_a_distinct_run_id(self) -> None:
        result = self._runner(
            _manifest_dict(trials_per_cell=2, warmup_episodes=1),
            executor=RecordingExecutor()).run()
        run_ids = [e.run_id for e in result.episodes]
        self.assertEqual(len(run_ids), 3)
        self.assertEqual(len(set(run_ids)), 3)

    def test_duplicate_run_id_aborts_the_run(self) -> None:
        fixed_run_id = str(uuid.uuid4())

        def _reused_executor(**kwargs: Any) -> EpisodeExecution:
            trace_path = _write_trace(kwargs["trace_dir"], fixed_run_id, "succeeded")
            return EpisodeExecution(run_id=fixed_run_id, trace_path=str(trace_path),
                                    reported_status="succeeded")

        runner = self._runner(_manifest_dict(trials_per_cell=2, warmup_episodes=0),
                              executor=_reused_executor)
        with self.assertRaises(TraceIntegrityError) as ctx:
            runner.run()
        self.assertIn("duplicate run_id", str(ctx.exception))
        # The partial result is still persisted for inspection.
        self.assertTrue(self.output_path.exists())


class PolicyAlignmentTests(RunnerTestBase):
    def test_matching_policy_runs(self) -> None:
        check_policy_alignment(parse_manifest(_manifest_dict()))  # no raise
        result = self._runner(_manifest_dict(), executor=RecordingExecutor()).run()
        self.assertEqual(result.totals.episodes, 2)

    def test_shipped_manifests_match_the_agent_policy(self) -> None:
        for name in ("dev-v1.json", "eval-v1.json"):
            check_policy_alignment(load_manifest(MANIFEST_DIR / name))

    def test_mismatched_max_attempts_is_refused(self) -> None:
        data = _manifest_dict()
        data["config"]["policy"]["max_attempts"] = 5
        with self.assertRaises(PolicyMismatchError) as ctx:
            check_policy_alignment(parse_manifest(data))
        message = str(ctx.exception)
        self.assertIn("max_attempts", message)
        self.assertIn("5", message)
        self.assertIn(str(AGENT_POLICY["max_attempts"]), message)

    def test_mismatched_action_timeout_is_refused(self) -> None:
        # A valid manifest (band max 4000 < 6000) whose policy diverges.
        data = _manifest_dict()
        data["config"]["action_timeout_ms"] = 6000
        with self.assertRaises(PolicyMismatchError) as ctx:
            check_policy_alignment(parse_manifest(data))
        message = str(ctx.exception)
        self.assertIn("action_timeout_ms", message)
        self.assertIn("6000", message)

    def test_every_diverging_field_is_named(self) -> None:
        # A valid manifest (0.2 >= 0.1; band max 4000 < 6000) with three
        # diverging fields.
        data = _manifest_dict()
        data["config"]["policy"]["max_attempts"] = 9
        data["config"]["policy"]["base_delay_seconds"] = 0.1
        data["config"]["action_timeout_ms"] = 6000
        with self.assertRaises(PolicyMismatchError) as ctx:
            check_policy_alignment(parse_manifest(data))
        message = str(ctx.exception)
        for field in ("max_attempts", "base_delay_seconds", "action_timeout_ms"):
            self.assertIn(field, message)

    def test_policy_mismatch_is_a_configuration_and_runner_error(self) -> None:
        self.assertTrue(issubclass(PolicyMismatchError, ConfigurationError))
        self.assertTrue(issubclass(PolicyMismatchError, RunnerError))

    def test_refusal_executes_no_episode(self) -> None:
        data = _manifest_dict()
        data["config"]["policy"]["max_attempts"] = 5
        executor = RecordingExecutor()
        runner = self._runner(data, executor=executor)
        with self.assertRaises(PolicyMismatchError):
            runner.run()
        self.assertEqual(executor.calls, [])
        self.assertFalse(self.output_path.exists())
        self.assertFalse(self.trace_dir.exists())

    def test_uninspectable_policy_fails_closed(self) -> None:
        manifest = parse_manifest(_manifest_dict())
        cases = {
            "missing module attributes": types.ModuleType("chimera.agent"),
            "non-numeric policy field": self._bad_policy_module("max_attempts", "two"),
            "self-contradictory derivation": self._bad_timeout_module(),
        }
        for label, stub in cases.items():
            with self.subTest(label):
                with mock.patch.dict(sys.modules, {"chimera.agent": stub}):
                    with self.assertRaises(PolicyMismatchError):
                        check_policy_alignment(manifest)

    @staticmethod
    def _bad_policy_module(field: str, value: Any) -> types.ModuleType:
        stub = types.ModuleType("chimera.agent")
        policy = copy.deepcopy(AGENT_POLICY)
        policy[field] = value
        stub.DEFAULT_POLICY = types.SimpleNamespace(**policy)
        stub.ACTION_TIMEOUT_MS = AGENT_ACTION_TIMEOUT_MS
        return stub

    @staticmethod
    def _bad_timeout_module() -> types.ModuleType:
        stub = types.ModuleType("chimera.agent")
        stub.DEFAULT_POLICY = types.SimpleNamespace(**AGENT_POLICY)
        stub.ACTION_TIMEOUT_MS = AGENT_ACTION_TIMEOUT_MS + 1
        return stub


class TimeoutTests(RunnerTestBase):
    def test_episode_budget_is_the_smaller_timeout(self) -> None:
        manifest = parse_manifest(_manifest_dict(
            episode_timeout_seconds=30.0,
            scenarios=[_scenario("S-NORM", timeout_seconds=12.0)],
        ))
        self.assertEqual(
            episode_budget_seconds(manifest, manifest.scenario("S-NORM")), 12.0)
        # A scenario timeout above the run-wide budget is not
        # representable through the validator (which requires
        # scenario <= episode), so the min() direction is exercised by
        # replacing the validated value on the object itself.
        widened = dataclasses.replace(
            manifest.scenario("S-NORM"), timeout_seconds=45.0)
        self.assertEqual(episode_budget_seconds(manifest, widened), 30.0)

    def test_executor_receives_the_episode_budget(self) -> None:
        executor = RecordingExecutor()
        self._runner(_manifest_dict(
            episode_timeout_seconds=30.0,
            scenarios=[_scenario("S-NORM", timeout_seconds=12.0)],
            trials_per_cell=1, warmup_episodes=0,
        ), executor=executor).run()
        self.assertEqual(executor.calls[0]["timeout_seconds"], 12.0)

    def test_timeout_records_a_cancelled_episode(self) -> None:
        def _slow_executor(**kwargs: Any) -> EpisodeExecution:
            token = kwargs["token"]
            deadline = time.monotonic() + 5.0
            while not token.is_cancelled() and time.monotonic() < deadline:
                time.sleep(0.005)
            run_id = str(uuid.uuid4())
            trace_path = _write_trace(kwargs["trace_dir"], run_id, "cancelled")
            return EpisodeExecution(run_id=run_id, trace_path=str(trace_path),
                                    reported_status="cancelled",
                                    error="cancelled by token (fixture)")

        result = self._runner(_manifest_dict(
            episode_timeout_seconds=0.05,
            scenarios=[_scenario("S-NORM", timeout_seconds=0.05)],
            trials_per_cell=1, warmup_episodes=0,
        ), executor=_slow_executor).run()
        (episode,) = result.episodes
        self.assertEqual(episode.outcome, EpisodeOutcome.CANCELLED)
        self.assertEqual(episode.agent_terminal_status, "cancelled")
        self.assertIn("timeout", (episode.error or "").lower())
        self.assertIn("0.050s", episode.error or "")
        self.assertGreaterEqual(episode.duration_ms, 0)
        self.assertIsNotNone(episode.trace_artifact)


class PersistenceTests(RunnerTestBase):
    def test_result_persists_and_round_trips(self) -> None:
        executor = RecordingExecutor()
        result = self._runner(
            _manifest_dict(trials_per_cell=2, warmup_episodes=1),
            executor=executor, run_id="fixed-run-id").run()
        self.assertTrue(self.output_path.exists())
        loaded = load_run_result(self.output_path)
        self.assertIsInstance(loaded, RunResult)
        self.assertEqual(loaded.run_id, "fixed-run-id")
        self.assertEqual(loaded.status, "measured")
        self.assertEqual(loaded.schema_version, 1)
        self.assertEqual(loaded.manifest_id, "fixture-dev")
        self.assertEqual(loaded.manifest_version, "1.0.0")
        self.assertEqual(loaded.manifest_schema_version, 1)
        self.assertEqual(loaded.manifest_sha256, result.manifest_sha256)
        self.assertEqual(len(loaded.episodes), 3)  # 1 warm-up + 2 trials
        self.assertEqual(loaded.totals.episodes, 2)
        self.assertEqual(len(loaded.cells), 1)
        for episode in loaded.episodes:
            self.assertTrue(episode.trial_id)
            self.assertTrue(episode.run_id)
            self.assertEqual(episode.scenario_id, "S-NORM")
            self.assertEqual(episode.manifest_id, "fixture-dev")
            self.assertTrue(episode.started_at)
            self.assertTrue(episode.completed_at)
            self.assertGreaterEqual(episode.duration_ms, 0)
            self.assertEqual(episode.outcome, EpisodeOutcome.SUCCEEDED)
            self.assertTrue(episode.trace_artifact)
            self.assertTrue(episode.trace_artifact.endswith(".json"))

    def test_run_result_json_matches_the_schema_shape(self) -> None:
        self._runner(_manifest_dict(trials_per_cell=1, warmup_episodes=0),
                     executor=RecordingExecutor()).run()
        data = json.loads(self.output_path.read_text(encoding="utf-8"))
        for key in ("schema_version", "benchmark_id", "run_id", "environment",
                    "config", "cells", "episodes", "totals", "notes"):
            self.assertIn(key, data)
        self.assertEqual(data["config"]["policy"]["max_attempts"],
                         AGENT_POLICY["max_attempts"])

    def test_shipped_dev_manifest_runs_end_to_end_with_a_fake(self) -> None:
        executor = RecordingExecutor()
        result = run_manifest(
            MANIFEST_DIR / "dev-v1.json", self.output_path,
            trace_dir=self.trace_dir, executor=executor,
            environment=_FixtureEnvironment.make())
        self.assertEqual(len(result.cells), 16)
        self.assertEqual(result.totals.episodes, 80)  # 16 cells x 5 trials
        self.assertEqual(len(result.episodes), 81)  # + 1 warm-up
        self.assertTrue(all(e.outcome == EpisodeOutcome.SUCCEEDED
                            for e in result.episodes))


class ExecutionFailureTests(RunnerTestBase):
    def test_agent_failure_is_recorded_and_the_run_continues(self) -> None:
        executor = RecordingExecutor(terminal="failed")
        result = self._runner(
            _manifest_dict(trials_per_cell=2, warmup_episodes=0),
            executor=executor).run()
        self.assertEqual(len(executor.calls), 2)
        for episode in result.episodes:
            self.assertEqual(episode.outcome, EpisodeOutcome.FAILED)
            self.assertEqual(episode.agent_terminal_status, "failed")
            self.assertIsNotNone(episode.error)
        self.assertEqual(result.cells[0].outcomes["failed"].value, 2)

    def test_retries_and_actions_come_from_the_trace(self) -> None:
        def _retrying_executor(**kwargs: Any) -> EpisodeExecution:
            run_id = str(uuid.uuid4())
            trace_path = _write_trace(
                kwargs["trace_dir"], run_id, "succeeded",
                attempts=("navigate", "fill", "fill", "click"),
            )
            return EpisodeExecution(run_id=run_id, trace_path=str(trace_path),
                                    reported_status="succeeded")

        result = self._runner(
            _manifest_dict(trials_per_cell=1, warmup_episodes=0),
            executor=_retrying_executor).run()
        (episode,) = result.episodes
        # 4 attempts across 3 distinct action types -> 1 retry.
        self.assertEqual(episode.retries.value, 1)
        self.assertEqual(episode.actions_executed.value, 4)

    def test_executor_crash_is_a_reported_harness_error(self) -> None:
        calls: List[str] = []

        def _crashing_executor(**kwargs: Any) -> EpisodeExecution:
            calls.append(kwargs["task_input"].id)
            raise RuntimeError("boom (fixture)")

        result = self._runner(
            _manifest_dict(trials_per_cell=2, warmup_episodes=0),
            executor=_crashing_executor).run()
        self.assertEqual(calls, ["I-PLAIN", "I-PLAIN"])  # run continues
        for episode in result.episodes:
            self.assertEqual(episode.outcome, EpisodeOutcome.FAILED)
            self.assertTrue((episode.error or "").startswith("harness_error:"))
            self.assertIn("boom", episode.error or "")
            self.assertIsNone(episode.trace_artifact)
            self.assertFalse(episode.retries.is_available)
            self.assertTrue(episode.retries.unavailable_reason)


class TraceIntegrityTests(RunnerTestBase):
    def test_corrupt_trace_aborts_the_run(self) -> None:
        state = {"calls": 0}

        def _flaky_executor(**kwargs: Any) -> EpisodeExecution:
            state["calls"] += 1
            run_id = str(uuid.uuid4())
            path = kwargs["trace_dir"] / f"{run_id}.json"
            kwargs["trace_dir"].mkdir(parents=True, exist_ok=True)
            if state["calls"] == 1:
                path.write_text(json.dumps(_trace_doc(run_id, "succeeded")),
                                encoding="utf-8")
            else:
                path.write_text("{corrupt", encoding="utf-8")
            return EpisodeExecution(run_id=run_id, trace_path=str(path),
                                    reported_status="succeeded")

        runner = self._runner(
            _manifest_dict(trials_per_cell=3, warmup_episodes=0),
            executor=_flaky_executor)
        with self.assertRaises(TraceIntegrityError):
            runner.run()
        self.assertEqual(state["calls"], 2)  # stopped: no third episode
        partial = load_run_result(self.output_path)
        self.assertEqual(len(partial.episodes), 1)  # only the verified one
        self.assertIn("ABORTED", partial.notes)

    def test_trace_run_id_mismatch_aborts(self) -> None:
        def _mismatched_executor(**kwargs: Any) -> EpisodeExecution:
            trace_path = _write_trace(kwargs["trace_dir"], str(uuid.uuid4()),
                                      "succeeded")
            return EpisodeExecution(run_id=str(uuid.uuid4()),
                                    trace_path=str(trace_path),
                                    reported_status="succeeded")

        with self.assertRaises(TraceIntegrityError) as ctx:
            self._runner(_manifest_dict(trials_per_cell=1, warmup_episodes=0),
                         executor=_mismatched_executor).run()
        self.assertIn("mismatch", str(ctx.exception))

    def test_missing_trace_aborts(self) -> None:
        def _traceless_executor(**kwargs: Any) -> EpisodeExecution:
            return EpisodeExecution(run_id=str(uuid.uuid4()), trace_path=None,
                                    reported_status="succeeded")

        with self.assertRaises(TraceIntegrityError) as ctx:
            self._runner(_manifest_dict(trials_per_cell=1, warmup_episodes=0),
                         executor=_traceless_executor).run()
        self.assertIn("missing", str(ctx.exception))

    def test_gapped_sequence_aborts(self) -> None:
        def _gapped_executor(**kwargs: Any) -> EpisodeExecution:
            run_id = str(uuid.uuid4())
            doc = _trace_doc(run_id, "succeeded")
            doc["events"][1]["sequence_number"] = 99
            path = kwargs["trace_dir"] / f"{run_id}.json"
            kwargs["trace_dir"].mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(doc), encoding="utf-8")
            return EpisodeExecution(run_id=run_id, trace_path=str(path),
                                    reported_status="succeeded")

        with self.assertRaises(TraceIntegrityError) as ctx:
            self._runner(_manifest_dict(trials_per_cell=1, warmup_episodes=0),
                         executor=_gapped_executor).run()
        self.assertIn("sequence", str(ctx.exception))

    def test_terminal_status_comes_from_the_artifact_not_the_return(self) -> None:
        def _lying_executor(**kwargs: Any) -> EpisodeExecution:
            run_id = str(uuid.uuid4())
            trace_path = _write_trace(kwargs["trace_dir"], run_id, "failed")
            return EpisodeExecution(run_id=run_id, trace_path=str(trace_path),
                                    reported_status="succeeded",  # contradicts trace
                                    error=None)

        result = self._runner(
            _manifest_dict(trials_per_cell=1, warmup_episodes=0),
            executor=_lying_executor).run()
        (episode,) = result.episodes
        self.assertEqual(episode.agent_terminal_status, "failed")
        self.assertEqual(episode.outcome, EpisodeOutcome.FAILED)


def _trace_doc(run_id: str, terminal: str) -> Dict[str, Any]:
    events = [
        {"sequence_number": 1, "event_type": "run_started",
         "timestamp": "2026-10-28T00:00:00.000Z", "action_type": None,
         "action_outcome": "ok", "error_details": None, "evidence_references": []},
        {"sequence_number": 2, "event_type": f"run_{terminal}",
         "timestamp": "2026-10-28T00:00:01.000Z", "action_type": None,
         "action_outcome": "ok", "error_details": None, "evidence_references": []},
    ]
    return {
        "schema_version": 1,
        "run_id": run_id,
        "agent_version": "milestone-1-foundation",
        "started_at": "2026-10-28T00:00:00.000Z",
        "completed_at": "2026-10-28T00:00:01.000Z",
        "terminal_status": terminal,
        "event_count": len(events),
        "events": events,
    }


class UnavailableMetricTests(RunnerTestBase):
    def _measured_run(self) -> RunResult:
        return self._runner(
            _manifest_dict(trials_per_cell=2, warmup_episodes=1),
            executor=RecordingExecutor()).run()

    def test_verifier_gated_metrics_are_unavailable_with_reasons(self) -> None:
        result = self._measured_run()
        cell = result.cells[0]
        self.assertFalse(cell.false_successes.is_available)
        self.assertTrue(cell.false_successes.unavailable_reason)
        self.assertFalse(cell.verifier_disagreements.is_available)
        for check in cell.independent_verification.values():
            self.assertFalse(check.is_available)
            self.assertTrue(check.unavailable_reason)
        for episode in result.episodes:
            self.assertEqual(episode.verification.status, "unavailable")
            self.assertTrue(episode.verification.unavailable_reason)
        self.assertFalse(result.totals.false_success_rate.is_available)

    def test_observer_gated_metrics_are_unavailable_with_reasons(self) -> None:
        result = self._measured_run()
        cell = result.cells[0]
        self.assertFalse(cell.unauthorized_actions.is_available)
        self.assertFalse(cell.safety_violations.is_available)
        self.assertFalse(result.totals.unauthorized_actions.is_available)

    def test_future_work_metrics_are_unavailable_with_reasons(self) -> None:
        result = self._measured_run()
        cell = result.cells[0]
        self.assertFalse(cell.outcomes["inconclusive"].is_available)
        self.assertFalse(cell.model_calls.is_available)
        self.assertFalse(cell.model_cost_usd.is_available)
        self.assertFalse(cell.human_interventions.is_available)

    def test_no_unavailable_metric_is_a_zero(self) -> None:
        result = self._measured_run()
        found = {"unavailable": 0}

        def _walk(node: Any) -> None:
            if isinstance(node, dict):
                if set(node) == {"value", "unavailable_reason"}:
                    if node["unavailable_reason"] is not None:
                        found["unavailable"] += 1
                        self.assertIsNone(node["value"])
                        self.assertTrue(str(node["unavailable_reason"]).strip())
                    return
                for value in node.values():
                    _walk(value)
            elif isinstance(node, list):
                for value in node:
                    _walk(value)

        _walk(result.to_dict())
        self.assertGreater(found["unavailable"], 0)


class WarmupTests(RunnerTestBase):
    def test_warmup_is_recorded_but_excluded_from_aggregates(self) -> None:
        result = self._runner(
            _manifest_dict(trials_per_cell=2, warmup_episodes=1),
            executor=RecordingExecutor()).run()
        warmups = [e for e in result.episodes
                   if e.trial_id.startswith("warmup:")]
        measured = [e for e in result.episodes
                    if not e.trial_id.startswith("warmup:")]
        self.assertEqual(len(warmups), 1)
        self.assertEqual(len(measured), 2)
        self.assertEqual(result.totals.episodes, 2)
        self.assertEqual(sum(c.trials for c in result.cells), 2)
        self.assertEqual(result.totals.by_baseline, {"chimera": 2})
        self.assertIn("warmup_episodes_executed=1", result.notes)

    def test_zero_warmup_runs_no_warmup_episode(self) -> None:
        executor = RecordingExecutor()
        result = self._runner(
            _manifest_dict(trials_per_cell=1, warmup_episodes=0),
            executor=executor).run()
        self.assertEqual(len(executor.calls), 1)
        self.assertEqual([e.trial_id for e in result.episodes], ["trial-0001"])


class SplitSeparationTests(RunnerTestBase):
    def test_dev_and_eval_runs_stay_separate(self) -> None:
        dev_data = _manifest_dict(
            manifest_id="fixture-dev", split="development",
            scenarios=[_scenario("S-SLOW", slow_ms=2000)],
            trials_per_cell=1, warmup_episodes=0,
        )
        eval_data = _manifest_dict(
            manifest_id="fixture-eval", split="evaluation",
            scenarios=[_scenario("S-SLOW", slow_ms=1350)],
            trials_per_cell=1, warmup_episodes=0,
        )
        dev_result = self._runner(
            dev_data, executor=RecordingExecutor(),
            output_path=self.tmp / "dev.json",
            trace_dir=self.tmp / "dev-traces").run()
        eval_result = self._runner(
            eval_data, executor=RecordingExecutor(),
            output_path=self.tmp / "eval.json",
            trace_dir=self.tmp / "eval-traces").run()
        self.assertEqual(dev_result.manifest_id, "fixture-dev")
        self.assertEqual(dev_result.config["split"], "development")
        self.assertEqual(eval_result.manifest_id, "fixture-eval")
        self.assertEqual(eval_result.config["split"], "evaluation")
        self.assertNotEqual(dev_result.manifest_sha256, eval_result.manifest_sha256)
        for episode in dev_result.episodes:
            self.assertEqual(episode.manifest_id, "fixture-dev")
        for episode in eval_result.episodes:
            self.assertEqual(episode.manifest_id, "fixture-eval")


class EnvironmentTests(unittest.TestCase):
    def test_collect_environment_records_both_shipped_hashes(self) -> None:
        env = collect_environment()
        self.assertTrue(env.python_version)
        self.assertTrue(env.playwright_version)
        self.assertTrue(env.platform)
        self.assertTrue(env.demo_app_sha256)
        self.assertEqual(env.dev_manifest_sha256,
                         load_manifest(MANIFEST_DIR / "dev-v1.json").sha256())
        self.assertEqual(env.eval_manifest_sha256,
                         load_manifest(MANIFEST_DIR / "eval-v1.json").sha256())


if __name__ == "__main__":
    unittest.main()
