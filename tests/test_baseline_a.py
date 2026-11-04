"""Tests for Baseline A, the deterministic replay driver.

Covers: the driver-report schema, the replay driver against fake pages
(success, step failure, single attempts, timeout=0, cancellation,
determinism), runner integration (fake executors reporting driver
reports, policy and manifest constraints, default executor selection),
and harness-only placement.

These are harness tests; they assert nothing about the agent's
performance (``docs/evaluation.md`` §1).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

from benchmarks.baseline_a import (
    BASELINE_ID,
    REPORT_SCHEMA,
    REPLAY_ACTION_TIMEOUT_ENV_VAR,
    DriverReport,
    DriverReportError,
    load_driver_report,
    replay_path_for,
    replay_url,
    run_replay,
)
from benchmarks.results import EnvironmentInfo, EpisodeOutcome

PROJECT_DIR = Path(__file__).resolve().parent.parent


def _report_dict(run_id: str = "run-1", **overrides: Any) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "run_id": run_id,
        "terminal_status": "succeeded",
        "steps": [
            {"step": "navigate", "target": "file://demo",
             "outcome": "ok", "error_type": None},
            {"step": "fill", "target": 'label "Project Name"',
             "outcome": "ok", "error_type": None},
            {"step": "click", "target": 'button "Create Project"',
             "outcome": "ok", "error_type": None},
        ],
        "started_at": "2026-10-28T00:00:00.000Z",
        "completed_at": "2026-10-28T00:00:01.000Z",
    }
    base.update(overrides)
    return base


class ReportSchemaTests(unittest.TestCase):
    def test_valid_report_round_trips(self) -> None:
        report = DriverReport.from_dict(_report_dict())
        self.assertEqual(report.terminal_status, "succeeded")
        self.assertEqual([s.step for s in report.steps],
                         ["navigate", "fill", "click"])
        self.assertEqual(DriverReport.from_dict(report.to_dict()), report)
        self.assertEqual(DriverReport.from_json(report.to_json()), report)

    def test_malformed_reports_fail_closed(self) -> None:
        cases = {
            "wrong schema": _report_dict(schema="trace/1"),
            "bad terminal": _report_dict(terminal_status="inconclusive"),
            "repeated step": _report_dict(steps=[
                {"step": "navigate", "target": "u", "outcome": "ok",
                 "error_type": None},
                {"step": "navigate", "target": "u", "outcome": "ok",
                 "error_type": None},
            ]),
            "out-of-order steps": _report_dict(steps=[
                {"step": "click", "target": "b", "outcome": "ok",
                 "error_type": None},
                {"step": "fill", "target": "i", "outcome": "ok",
                 "error_type": None},
            ]),
            "unknown step": _report_dict(steps=[
                {"step": "wait", "target": "t", "outcome": "ok",
                 "error_type": None},
            ]),
            "bad outcome": _report_dict(steps=[
                {"step": "navigate", "target": "u", "outcome": "maybe",
                 "error_type": None},
            ]),
            "empty run_id": _report_dict(run_id="  "),
            "steps not a list": _report_dict(steps="navigate"),
        }
        for label, raw in cases.items():
            with self.subTest(label):
                with self.assertRaises(DriverReportError):
                    DriverReport.from_dict(raw)

    def test_succeeded_with_no_steps_is_rejected(self) -> None:
        with self.assertRaises(DriverReportError) as ctx:
            DriverReport.from_dict(_report_dict(steps=[]))
        self.assertIn("no steps attempted", str(ctx.exception))

    def test_cancelled_with_no_steps_is_accepted(self) -> None:
        report = DriverReport.from_dict(
            _report_dict(terminal_status="cancelled", steps=[]))
        self.assertEqual(report.steps, ())

    def test_non_object_and_bad_json_rejected(self) -> None:
        with self.assertRaises(DriverReportError):
            DriverReport.from_dict([])
        with self.assertRaises(DriverReportError):
            DriverReport.from_json("{invalid")

    def test_load_driver_report_checks_file_and_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "absent.replay.json"
            with self.assertRaises(DriverReportError) as ctx:
                load_driver_report(missing, "run-1")
            self.assertIn("unreadable", str(ctx.exception))
            path = replay_path_for(Path(tmp), "run-1")
            self.assertTrue(str(path).endswith(".replay.json"))
            path.write_text(DriverReport.from_dict(
                _report_dict()).to_json(), encoding="utf-8")
            self.assertEqual(load_driver_report(path, "run-1").run_id,
                             "run-1")
            with self.assertRaises(DriverReportError) as ctx:
                load_driver_report(path, "run-2")
            self.assertIn("mismatch", str(ctx.exception))


class ReplayDriverTests(unittest.TestCase):
    """``run_replay`` against fake pages (no browser)."""

    class _Locator:
        def __init__(self, fail: Optional[Exception] = None) -> None:
            self.fail = fail
            self.calls: List[Any] = []

        def _maybe_fail(self, name: str, *args: Any) -> None:
            self.calls.append((name,) + args)
            if self.fail is not None:
                raise self.fail

        def fill(self, value: str, **kwargs: Any) -> None:
            self._maybe_fail("fill", value, kwargs)

        def click(self, **kwargs: Any) -> None:
            self._maybe_fail("click", kwargs)

        def is_visible(self, **kwargs: Any) -> bool:
            return True

        def all_text_contents(self, **kwargs: Any) -> List[str]:
            return ["Benchmark Project"]

    class _Page:
        def __init__(self, input_fail: Optional[Exception] = None,
                     button_fail: Optional[Exception] = None) -> None:
            self.input = ReplayDriverTests._Locator(fail=input_fail)
            self.button = ReplayDriverTests._Locator(fail=button_fail)
            self.generic = ReplayDriverTests._Locator()
            self.visited: List[str] = []

        def goto(self, url: str, **kwargs: Any) -> None:
            self.visited.append(url)

        def get_by_label(self, label: str, **kwargs: Any) -> Any:
            assert label == "Project Name"
            return self.input

        def get_by_role(self, role: str, **kwargs: Any) -> Any:
            assert role == "button"
            return self.button

        def locator(self, selector: str, **kwargs: Any) -> Any:
            return self.generic

    class _Context:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

    class _Browser:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.page = self._Page()
        self.context = self._Context()
        self.browser = self._Browser()
        # Budget-override env var must never leak between tests.
        self._saved_env = os.environ.pop(REPLAY_ACTION_TIMEOUT_ENV_VAR, None)
        self.addCleanup(self._restore_env)

    def _restore_env(self) -> None:
        if self._saved_env is None:
            os.environ.pop(REPLAY_ACTION_TIMEOUT_ENV_VAR, None)
        else:
            os.environ[REPLAY_ACTION_TIMEOUT_ENV_VAR] = self._saved_env

    def _factory(self, page: Optional["_Page"] = None):
        page = page if page is not None else self.page

        def _make():
            return self.browser, self.context, page

        return _make

    def test_success_runs_fixed_steps_and_persists_artifacts(self) -> None:
        outcome = run_replay(
            project_name="Benchmark Project", url="file://demo",
            trace_dir=self.tmp, page_factory=self._factory(),
            run_id="run-1")
        self.assertEqual(outcome.terminal_status, "succeeded")
        self.assertIsNone(outcome.error)
        self.assertTrue(Path(outcome.report_path).is_file())
        self.assertIsNotNone(outcome.snapshot)
        assert outcome.snapshot is not None
        self.assertEqual(outcome.snapshot["items"], ["Benchmark Project"])
        self.assertIsNotNone(outcome.snapshot_ref)
        self.assertIsNone(outcome.observation_error)
        kinds = [r["action_type"] for r in outcome.action_log["records"]]
        self.assertEqual(kinds[0:3], ["navigate", "fill", "click"])
        self.assertIs(self.context.closed, True)
        self.assertIs(self.browser.closed, True)

    def test_fill_failure_stops_before_click(self) -> None:
        page = self._Page(input_fail=TimeoutError("control disabled"))
        outcome = run_replay(
            project_name="Benchmark Project", url="file://demo",
            trace_dir=self.tmp, page_factory=self._factory(page),
            run_id="run-2")
        self.assertEqual(outcome.terminal_status, "failed")
        self.assertIn("TimeoutError", outcome.error or "")
        self.assertEqual(len(page.input.calls), 1)
        self.assertEqual(page.button.calls, [])
        self.assertEqual(page.visited, ["file://demo"])
        report = load_driver_report(Path(outcome.report_path), "run-2")
        self.assertEqual(
            [(s.step, s.outcome) for s in report.steps],
            [("navigate", "ok"), ("fill", "error")])

    def test_each_step_attempted_exactly_once(self) -> None:
        run_replay(project_name="P", url="file://demo", trace_dir=self.tmp,
                   page_factory=self._factory(), run_id="run-3")
        self.assertEqual(len(self.page.input.calls), 1)
        self.assertEqual(len(self.page.button.calls), 1)
        self.assertEqual(len(self.page.visited), 1)

    def test_fill_and_click_use_fixed_short_timeout(self) -> None:
        from benchmarks.baseline_a import REPLAY_ACTION_TIMEOUT_MS
        from benchmarks.manifest import load_manifest

        run_replay(project_name="P", url="file://demo", trace_dir=self.tmp,
                   page_factory=self._factory(), run_id="run-4")
        (fill_name, _, fill_kwargs), = self.page.input.calls
        self.assertEqual(fill_name, "fill")
        self.assertEqual(fill_kwargs.get("timeout"),
                         REPLAY_ACTION_TIMEOUT_MS)
        (click_name, click_kwargs), = self.page.button.calls
        self.assertEqual(click_name, "click")
        self.assertEqual(click_kwargs.get("timeout"),
                         REPLAY_ACTION_TIMEOUT_MS)
        # The timeout must be positive (Playwright 0 disables the
        # timeout and waits indefinitely) and below every slow value
        # in both shipped manifests, so replay can never wait out a
        # transient fault.
        self.assertGreater(REPLAY_ACTION_TIMEOUT_MS, 0)
        slowest = min(
            fault.slow_ms
            for name in ("dev-v1.json", "eval-v1.json")
            for scenario in load_manifest(
                PROJECT_DIR / "benchmarks" / "manifests" / name).scenarios
            for fault in scenario.fault_variants
            if fault.slow_ms)
        self.assertLess(REPLAY_ACTION_TIMEOUT_MS, slowest)

    def test_explicit_timeout_override_reaches_fill_and_click(self) -> None:
        run_replay(project_name="P", url="file://demo", trace_dir=self.tmp,
                   page_factory=self._factory(), run_id="run-t2500",
                   action_timeout_ms=2500)
        (_, _, fill_kwargs), = self.page.input.calls
        self.assertEqual(fill_kwargs.get("timeout"), 2500)
        (_, click_kwargs), = self.page.button.calls
        self.assertEqual(click_kwargs.get("timeout"), 2500)

    def test_env_timeout_override_reaches_fill_and_click(self) -> None:
        os.environ[REPLAY_ACTION_TIMEOUT_ENV_VAR] = "5000"
        run_replay(project_name="P", url="file://demo", trace_dir=self.tmp,
                   page_factory=self._factory(), run_id="run-tenv")
        (_, _, fill_kwargs), = self.page.input.calls
        self.assertEqual(fill_kwargs.get("timeout"), 5000)
        (_, click_kwargs), = self.page.button.calls
        self.assertEqual(click_kwargs.get("timeout"), 5000)

    def test_explicit_override_beats_env_var(self) -> None:
        os.environ[REPLAY_ACTION_TIMEOUT_ENV_VAR] = "5000"
        run_replay(project_name="P", url="file://demo", trace_dir=self.tmp,
                   page_factory=self._factory(), run_id="run-tboth",
                   action_timeout_ms=1200)
        (_, _, fill_kwargs), = self.page.input.calls
        self.assertEqual(fill_kwargs.get("timeout"), 1200)

    def test_invalid_timeouts_fail_loudly(self) -> None:
        for bad in (0, -100):
            with self.assertRaises(ValueError, msg=bad):
                run_replay(project_name="P", url="file://demo",
                           trace_dir=self.tmp,
                           page_factory=self._factory(),
                           run_id=f"run-bad{bad}",
                           action_timeout_ms=bad)
        for raw in ("0", "-5", "abc"):
            os.environ[REPLAY_ACTION_TIMEOUT_ENV_VAR] = raw
            with self.assertRaises(ValueError, msg=raw):
                run_replay(project_name="P", url="file://demo",
                           trace_dir=self.tmp,
                           page_factory=self._factory(),
                           run_id=f"run-badenv{raw}")

    def test_cancelled_token_before_start_cancels_cleanly(self) -> None:
        from chimera.safety import CancellationToken

        token = CancellationToken()
        token.request("test cancel")
        outcome = run_replay(
            project_name="P", url="file://demo", trace_dir=self.tmp,
            token=token, page_factory=self._factory(), run_id="run-5")
        self.assertEqual(outcome.terminal_status, "cancelled")
        self.assertIn("RunCancelledError", outcome.error or "")
        self.assertEqual(self.page.visited, [])
        report = load_driver_report(Path(outcome.report_path), "run-5")
        self.assertEqual(report.steps, ())
        self.assertIs(self.context.closed, True)

    def test_snapshot_failure_is_reported_not_fatal(self) -> None:
        class _BlindLocator(self._Locator):
            def is_visible(self, **kwargs: Any) -> bool:
                raise RuntimeError("probe exploded")

            def all_text_contents(self, **kwargs: Any) -> List[str]:
                raise RuntimeError("probe exploded")

        self.page.generic = _BlindLocator()
        outcome = run_replay(
            project_name="P", url="file://demo", trace_dir=self.tmp,
            page_factory=self._factory(), run_id="run-6")
        self.assertEqual(outcome.terminal_status, "succeeded")
        self.assertIsNone(outcome.snapshot)
        self.assertIn("probe exploded", outcome.observation_error or "")

    def test_replay_is_deterministic(self) -> None:
        first = run_replay(
            project_name="P", url="file://demo", trace_dir=self.tmp,
            page_factory=self._factory(), run_id="det-1")
        page2 = self._Page()
        context2 = self._Context()
        browser2 = self._Browser()
        second = run_replay(
            project_name="P", url="file://demo", trace_dir=self.tmp,
            page_factory=lambda: (browser2, context2, page2),
            run_id="det-2")
        self.assertEqual(first.terminal_status, second.terminal_status)
        self.assertEqual(first.error, second.error)
        first_log = [dict(r, seq=0) for r in first.action_log["records"]]
        second_log = [dict(r, seq=0) for r in second.action_log["records"]]
        for first_record, second_record in zip(first_log, second_log):
            first_record.pop("elapsed_ms", None)
            second_record.pop("elapsed_ms", None)
        self.assertEqual(first_log, second_log)


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
            "manifest_id": "fixture-replay",
            "split": "development",
            "description": "Baseline A wiring fixture.",
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

    def _environment(self) -> EnvironmentInfo:
        return EnvironmentInfo(
            python_version="3.9.6-test", playwright_version="test",
            browser="chromium", browser_build="test", platform="test",
            demo_app_sha256="d" * 64, dev_manifest_sha256="e" * 64,
            eval_manifest_sha256="f" * 64)

    def _executor(self, terminal: str = "succeeded",
                  report_override: Any = "write",
                  with_snapshot: bool = True,
                  with_log: bool = True):
        import uuid as _uuid

        from benchmarks.runner import EpisodeExecution

        def _run(**kwargs: Any) -> EpisodeExecution:
            run_id = str(_uuid.uuid4())
            trace_dir = Path(kwargs["trace_dir"])
            trace_dir.mkdir(parents=True, exist_ok=True)
            report_path: Optional[str] = None
            if report_override == "write":
                report = DriverReport.from_dict(_report_dict(
                    run_id, terminal_status=terminal))
                path = trace_dir / f"{run_id}.replay.json"
                path.write_text(report.to_json(), encoding="utf-8")
                report_path = str(path)
            elif isinstance(report_override, str):
                path = trace_dir / f"{run_id}.replay.json"
                path.write_text(report_override, encoding="utf-8")
                report_path = str(path)
            snapshot = None
            if with_snapshot:
                snapshot = {"run_id": run_id, "confirmation_visible": True,
                            "items": ["Benchmark Project"], "captured_at": ""}
            action_log = None
            if with_log:
                action_log = {
                    "run_id": run_id, "attached": True, "complete": True,
                    "records": [
                        {"seq": 1, "action_type": "navigate",
                         "target": {"url": "file://demo"},
                         "target_summary": "goto", "outcome": "ok",
                         "policy": "allowed", "policy_reason": "",
                         "error_type": None, "elapsed_ms": 0},
                    ],
                }
            return EpisodeExecution(
                run_id=run_id, trace_path=None,
                reported_status=terminal,
                error=None if terminal == "succeeded" else "fixture",
                state_snapshot=snapshot,
                snapshot_ref=f"fixture:{run_id}" if snapshot else None,
                episode_url="file://demo", action_log=action_log,
                driver_report_path=report_path)

        return _run

    def _run(self, baseline: str = BASELINE_ID, **executor_kwargs: Any) -> Any:
        from benchmarks.runner import Runner

        trials = executor_kwargs.pop("trials", 2)
        return Runner(
            self._manifest(trials=trials),
            output_path=self.tmp / "r.json", trace_dir=self.tmp / "t",
            executor=self._executor(**executor_kwargs),
            environment=self._environment(),
            baseline=baseline).run()

    def test_replay_run_reads_terminal_from_driver_report(self) -> None:
        result = self._run()
        self.assertEqual(result.totals.episodes, 2)
        for episode in result.episodes:
            self.assertEqual(episode.baseline, BASELINE_ID)
            self.assertEqual(episode.outcome, EpisodeOutcome.SUCCEEDED)
            self.assertEqual(episode.agent_terminal_status, "succeeded")
            self.assertTrue(episode.trace_artifact.endswith(".replay.json"))
            self.assertEqual(episode.retries.value, 0)
            self.assertEqual(episode.actions_executed.value, 3)
        self.assertEqual(result.cells[0].baseline, BASELINE_ID)
        self.assertEqual(result.totals.by_baseline, {BASELINE_ID: 2})
        self.assertEqual(result.config["baseline"], BASELINE_ID)

    def test_failed_report_records_failure_and_continues(self) -> None:
        result = self._run(terminal="failed")
        for episode in result.episodes:
            self.assertEqual(episode.outcome, EpisodeOutcome.FAILED)
        self.assertEqual(result.cells[0].outcomes["failed"].value, 2)

    def test_replay_uses_verifier_and_observer(self) -> None:
        from benchmarks.results import VerificationEvidence

        result = self._run()
        for episode in result.episodes:
            self.assertEqual(episode.verification.status,
                             VerificationEvidence.VERIFIED)
            self.assertIs(episode.verification.all_satisfied, True)
            self.assertEqual(episode.unauthorized_actions.value, 0)
            self.assertEqual(episode.safety_violations.value, 0)
        self.assertEqual(result.cells[0].false_successes.value, 0)

    def test_corrupt_driver_report_aborts_the_run(self) -> None:
        from benchmarks.runner import Runner, TraceIntegrityError

        state = {"n": 0}
        good = self._executor()
        bad = self._executor(report_override="{corrupt")

        def _flaky(**kwargs: Any) -> Any:
            state["n"] += 1
            return (good if state["n"] == 1 else bad)(**kwargs)

        runner = Runner(
            self._manifest(trials=3), output_path=self.tmp / "r.json",
            trace_dir=self.tmp / "t", executor=_flaky,
            environment=self._environment(), baseline=BASELINE_ID)
        with self.assertRaises(TraceIntegrityError):
            runner.run()
        self.assertEqual(state["n"], 2)

    def test_missing_driver_report_aborts_the_run(self) -> None:
        from benchmarks.runner import Runner, TraceIntegrityError

        runner = Runner(
            self._manifest(trials=1), output_path=self.tmp / "r.json",
            trace_dir=self.tmp / "t",
            executor=self._executor(report_override=None),
            environment=self._environment(), baseline=BASELINE_ID)
        with self.assertRaises(TraceIntegrityError) as ctx:
            runner.run()
        self.assertIn("driver report missing", str(ctx.exception))

    def test_policy_check_still_applies_to_replay_runs(self) -> None:
        import dataclasses as _dataclasses

        from benchmarks.runner import PolicyMismatchError, Runner

        manifest = self._manifest()
        calls: List[str] = []

        def _counting(**kwargs: Any) -> Any:
            calls.append("x")
            return self._executor()(**kwargs)

        divergent = _dataclasses.replace(
            manifest.config.policy, max_attempts=9)
        divergent_manifest = _dataclasses.replace(
            manifest, config=_dataclasses.replace(
                manifest.config, policy=divergent))
        runner = Runner(
            divergent_manifest, output_path=self.tmp / "r.json",
            trace_dir=self.tmp / "t", executor=_counting,
            environment=self._environment(), baseline=BASELINE_ID)
        with self.assertRaises(PolicyMismatchError):
            runner.run()
        self.assertEqual(calls, [])

    def test_default_executor_follows_baseline(self) -> None:
        from benchmarks.baseline_a import replay_executor
        from benchmarks.runner import Runner, default_executor

        chimera = Runner(
            self._manifest(), output_path=self.tmp / "c.json",
            trace_dir=self.tmp / "t", environment=self._environment())
        replay = Runner(
            self._manifest(), output_path=self.tmp / "r.json",
            trace_dir=self.tmp / "t", environment=self._environment(),
            baseline=BASELINE_ID)
        self.assertIs(chimera.executor, default_executor)
        self.assertIs(replay.executor, replay_executor)

    def test_unknown_baseline_still_refused(self) -> None:
        from benchmarks.runner import ConfigurationError, Runner

        runner = Runner(
            self._manifest(), output_path=self.tmp / "r.json",
            trace_dir=self.tmp / "t", executor=self._executor(),
            environment=self._environment(), baseline="A")
        with self.assertRaises(ConfigurationError):
            runner.run()

    def test_replay_result_round_trips(self) -> None:
        from benchmarks.runner import Runner, load_run_result

        Runner(
            self._manifest(trials=1), output_path=self.tmp / "r.json",
            trace_dir=self.tmp / "t", executor=self._executor(),
            environment=self._environment(),
            baseline=BASELINE_ID).run()
        loaded = load_run_result(self.tmp / "r.json")
        (episode,) = loaded.episodes
        self.assertEqual(episode.baseline, BASELINE_ID)
        self.assertEqual(episode.retries.value, 0)


class PlacementTests(unittest.TestCase):
    """Baseline A is harness code: never under ``chimera/``, never
    importing the agent."""

    def test_module_lives_in_benchmarks(self) -> None:
        import benchmarks.baseline_a as module

        path = Path(module.__file__ or "")
        self.assertEqual(path.parent.name, "benchmarks")
        self.assertNotIn("chimera", path.parts[:-1])

    def test_no_agent_or_playwright_import_at_module_scope(self) -> None:
        probe = (
            "import sys; "
            "import benchmarks.baseline_a as _b; "
            "loaded = [m for m in sys.modules "
            "if m.split('.')[0] in ('chimera', 'playwright')]; "
            "assert not loaded, loaded; "
            "print('clean')"
        )
        completed = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=str(PROJECT_DIR), capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("clean", completed.stdout)

    def test_source_imports_no_agent_module(self) -> None:
        import ast as _ast

        source = (PROJECT_DIR / "benchmarks" / "baseline_a.py").read_text(
            encoding="utf-8")
        for node in _ast.walk(_ast.parse(source)):
            if isinstance(node, _ast.Import):
                for alias in node.names:
                    self.assertFalse(
                        alias.name == "chimera.agent"
                        or alias.name.startswith("chimera.agent."),
                        "replay must not import the agent")
            elif isinstance(node, _ast.ImportFrom):
                module = node.module or ""
                self.assertFalse(
                    module == "chimera.agent"
                    or module.startswith("chimera.agent."),
                    "replay must not import the agent")
            elif isinstance(node, _ast.Name):
                self.assertNotIn(node.id, ("TraceRecorder", "create_project"),
                                 "replay must not use agent tracing")

    def test_replay_url_matches_agent_url(self) -> None:
        from benchmarks.manifest import FaultConfig
        from chimera.agent import get_demo_url_with_faults

        cases = [(0, False), (2000, False), (0, True), (2000, True)]
        for slow_ms, disabled in cases:
            with self.subTest(slow_ms=slow_ms, disabled=disabled):
                fault = FaultConfig(slow_ms=slow_ms, disabled=disabled)
                self.assertEqual(
                    replay_url(fault),
                    get_demo_url_with_faults(
                        slow_ms=slow_ms, disabled=disabled))


if __name__ == "__main__":
    unittest.main()
