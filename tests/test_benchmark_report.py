"""Tests for the benchmark report renderer.

Covers: the Wilson upper bound against the evaluation.md §4.3
reference values, complete-fixture rendering with every §6.1 section,
multi-run/multi-baseline reports, audited/provisional/unauditable
cells, unavailable metrics with reasons, integrity and compatibility
refusals, deterministic output, privacy exclusion, verbatim drift
against the evaluation document, and the §6.4 prohibited-claims
guard.

Runs are produced by the real ``Runner`` with fake executors (no
browser, no episodes beyond the fixtures), and audit states by the
real ``plan_audit``/``apply_audit`` — so these tests also prove
report compatibility with the persisted schemas.

Nothing rendered here is a measurement: fixture figures assert
report *shape*, never benchmark performance (``docs/evaluation.md``
§1).
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

from benchmarks.audit import (
    apply_audit,
    cell_key,
    plan_audit,
    plan_targeted_audit,
)
from benchmarks.report import (
    DISCLAIMERS,
    LIMITATIONS_TEXT,
    REPORT_FORMAT,
    ReportError,
    render_report,
    wilson_upper,
)

PROJECT_DIR = Path(__file__).resolve().parent.parent
EVALUATION_DOC = PROJECT_DIR / "docs" / "evaluation.md"


class ReportFixtureBase(unittest.TestCase):
    """Real runner output (fake executors) as report input."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    # -- manifests ----------------------------------------------------

    def _manifest_dict(self, manifest_id: str = "fixture-report",
                       split: str = "development") -> Dict[str, Any]:
        import chimera.agent as _agent

        def _scenario(sid: str, slow_ms: int, disabled: bool,
                      expected: str) -> Dict[str, Any]:
            return {
                "id": sid,
                "description": "Report fixture scenario.",
                "fault_variants": [{"slow_ms": slow_ms,
                                    "disabled": disabled}],
                "expected_outcome": expected,
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
            }

        return {
            "schema_version": 1,
            "benchmark_id": "chimera-local",
            "benchmark_version": "1.0.0",
            "manifest_id": manifest_id,
            "split": split,
            "description": "Report fixture manifest.",
            "slow_band_ms": {"min_ms": 500, "max_ms": 4000},
            "config": {
                "trials_per_cell": 3,
                "warmup_episodes": 1,
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
            "scenarios": [_scenario("S-NORM", 0, False, "succeeded"),
                          _scenario("S-DIS", 0, True, "failed")],
        }

    def _write_manifest(self, name: str = "m.json",
                        **kwargs: Any) -> Path:
        path = self.tmp / name
        path.write_text(json.dumps(self._manifest_dict(**kwargs)),
                        encoding="utf-8")
        return path

    # -- executors ----------------------------------------------------

    def _executor(self, *,
                  terminal_for: Optional[Dict[str, str]] = None,
                  write_snapshot: bool = True,
                  write_actions: bool = True,
                  replay: bool = False):
        import uuid as _uuid

        from benchmarks.runner import EpisodeExecution

        terminal_for = terminal_for or {}

        def _run(**kwargs: Any) -> EpisodeExecution:
            run_id = str(_uuid.uuid4())
            trace_dir = Path(kwargs["trace_dir"])
            trace_dir.mkdir(parents=True, exist_ok=True)
            terminal = terminal_for.get(kwargs["scenario"].id, "succeeded")
            snapshot = {"run_id": run_id, "confirmation_visible": True,
                        "items": ["Benchmark Project"], "captured_at": ""}
            snap_path = trace_dir / f"{run_id}.snapshot.json"
            if write_snapshot:
                snap_path.write_text(json.dumps(snapshot), encoding="utf-8")
            if write_actions:
                (trace_dir / f"{run_id}.actions.json").write_text(
                    json.dumps({"run_id": run_id, "attached": True,
                                "complete": True, "records": []}),
                    encoding="utf-8")
            action_log = {
                "run_id": run_id, "attached": True, "complete": True,
                "records": [{
                    "seq": 1, "action_type": "navigate",
                    "target": {"url": "file://demo"},
                    "target_summary": "goto", "outcome": "ok",
                    "policy": "allowed", "policy_reason": "",
                    "error_type": None, "elapsed_ms": 0,
                }]} if write_actions else None
            if replay:
                from benchmarks.baseline_a import (
                    REPORT_SCHEMA,
                    DriverReport,
                    ReplayStep,
                )
                report = DriverReport(
                    schema=REPORT_SCHEMA, run_id=run_id,
                    terminal_status=terminal,
                    steps=tuple(ReplayStep(step=s, target="t", outcome="ok")
                                for s in ("navigate", "fill", "click")),
                    started_at="2026-10-28T00:00:00.000Z",
                    completed_at="2026-10-28T00:00:01.000Z")
                report_path = trace_dir / f"{run_id}.replay.json"
                report_path.write_text(report.to_json(), encoding="utf-8")
                return EpisodeExecution(
                    run_id=run_id, trace_path=None,
                    reported_status=terminal, error=None,
                    state_snapshot=dict(snapshot) if write_snapshot else None,
                    snapshot_ref=str(snap_path) if write_snapshot else None,
                    episode_url="file://demo", action_log=action_log,
                    driver_report_path=str(report_path))
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
            trace_path = trace_dir / f"{run_id}.json"
            trace_path.write_text(json.dumps({
                "schema_version": 1, "run_id": run_id,
                "agent_version": "milestone-1-foundation",
                "started_at": "2026-10-28T00:00:00.000Z",
                "completed_at": "2026-10-28T00:00:01.000Z",
                "terminal_status": terminal,
                "event_count": len(events), "events": events,
            }), encoding="utf-8")
            return EpisodeExecution(
                run_id=run_id, trace_path=str(trace_path),
                reported_status=terminal, error=None,
                state_snapshot=dict(snapshot) if write_snapshot else None,
                snapshot_ref=str(snap_path) if write_snapshot else None,
                episode_url="file://demo", action_log=action_log)

        return _run

    def _environment(self) -> Any:
        from benchmarks.results import EnvironmentInfo

        return EnvironmentInfo(
            python_version="test", playwright_version="test",
            browser="chromium", browser_build="test", platform="test",
            demo_app_sha256="d" * 64, dev_manifest_sha256="e" * 64,
            eval_manifest_sha256="f" * 64)

    def _run_file(self, manifest_path: Path, name: str = "run.json",
                  run_id: Optional[str] = None,
                  baseline: str = "chimera",
                  **executor_kwargs: Any) -> Path:
        from benchmarks.manifest import load_manifest
        from benchmarks.runner import Runner

        out = self.tmp / name
        Runner(
            load_manifest(manifest_path), output_path=out,
            trace_dir=self.tmp / "traces",
            executor=self._executor(**executor_kwargs),
            environment=self._environment(),
            baseline=baseline, run_id=run_id).run()
        return out

    def _fill_verdicts(self, plan_path: Path,
                       verdict_for: Any) -> Dict[str, Any]:
        plan_data = json.loads(plan_path.read_text(encoding="utf-8"))
        for cell in plan_data["cells"].values():
            for bundle in cell["sampled"]:
                cell["verdicts"][bundle["trial_id"]] = verdict_for(bundle)
        plan_path.write_text(json.dumps(plan_data), encoding="utf-8")
        return plan_data


def _agreeing(bundle: Dict[str, Any]) -> Dict[str, Any]:
    return {"checks": dict(bundle["verifier_checks"]), "note": "agree"}


class WilsonTests(unittest.TestCase):
    def test_reference_values_from_section_4_3(self) -> None:
        self.assertAlmostEqual(wilson_upper(0, 5) * 100, 43.4, places=1)  # type: ignore[operator]
        self.assertAlmostEqual(wilson_upper(0, 50) * 100, 7.1, places=1)  # type: ignore[operator]
        self.assertAlmostEqual(wilson_upper(0, 100) * 100, 3.7, places=1)  # type: ignore[operator]

    def test_no_denominator_no_bound(self) -> None:
        self.assertIsNone(wilson_upper(0, 0))
        self.assertIsNone(wilson_upper(0, -3))
        self.assertIsNone(wilson_upper(3, 2))
        self.assertIsNone(wilson_upper(-1, 5))

    def test_bound_sanity_for_nonzero_counts(self) -> None:
        bound = wilson_upper(1, 10)
        assert bound is not None
        self.assertGreater(bound, 0.1)
        self.assertLessEqual(bound, 1.0)
        wider = wilson_upper(0, 5)
        narrower = wilson_upper(0, 100)
        assert wider is not None and narrower is not None
        self.assertLess(narrower, wider)


class CompleteReportTests(ReportFixtureBase):
    def _render(self) -> str:
        manifest = self._write_manifest()
        run = self._run_file(
            manifest, run_id="run-complete-1",
            terminal_for={"S-DIS": "failed"})
        return render_report([run], manifest_paths=[manifest])

    def test_all_section_6_1_sections_present(self) -> None:
        report = self._render()
        for heading in ("## Runs", "## Summary by cell",
                        "## Not measurable in this report",
                        "## Verifier audit", "## Failure breakdown",
                        "## Exclusions", "## Limitations", "## Claim list",
                        "## Disclaimers", "## Artifacts"):
            self.assertIn(heading, report)
        self.assertIn(REPORT_FORMAT, report)
        self.assertTrue(report.endswith("\n"))
        self.assertFalse(report.endswith("\n\n"))

    def test_header_carries_identity_and_environment(self) -> None:
        report = self._render()
        self.assertIn("chimera-local", report)
        self.assertIn("run-complete-1", report)
        self.assertIn("fixture-report", report)
        self.assertIn("chromium", report)
        self.assertIn("demo_app_sha256", report)

    def test_expected_markers_both_directions(self) -> None:
        report = self._render()
        norm = [line for line in report.splitlines()
                if "| `S-NORM` / `I-PLAIN` |" in line]
        dis = [line for line in report.splitlines()
               if "| `S-DIS` / `I-PLAIN` |" in line]
        self.assertEqual(len(norm), 1)
        self.assertEqual(len(dis), 1)
        self.assertIn("3/3 (100%, expected)", norm[0])
        self.assertIn("0/3 (0%, expected)", dis[0])

    def test_zero_false_success_carries_wilson_bound(self) -> None:
        report = self._render()
        bound = wilson_upper(0, 3)
        assert bound is not None
        self.assertIn(f"0/3 (≤{bound * 100:.1f}%)", report)

    def test_baseline_b_is_a_null_row(self) -> None:
        report = self._render()
        rows = [line for line in report.splitlines()
                if "Baseline B — model" in line]
        self.assertEqual(len(rows), 1)
        self.assertIn("| development | B |", rows[0])
        self.assertIn("`null` (not implemented)", rows[0])

    def test_unaudited_run_is_provisional(self) -> None:
        report = self._render()
        self.assertIn("**Verdict: PROVISIONAL**", report)
        self.assertIn("no sample adjudicated", report)

    def test_warmups_excluded_and_counted(self) -> None:
        report = self._render()
        self.assertIn("1 warm-up episode(s) excluded", report)

    def test_failure_breakdown_lists_failed_episodes(self) -> None:
        report = self._render()
        breakdown = report.split("## Failure breakdown")[1]
        breakdown = breakdown.split("## Exclusions")[0]
        self.assertIn(
            "Uncategorized agent failures (`failure_category` null): 3",
            breakdown)


class MultiRunTests(ReportFixtureBase):
    def test_two_baselines_two_rows_per_cell(self) -> None:
        manifest = self._write_manifest()
        chimera = self._run_file(manifest, name="chimera.json",
                                 run_id="run-chimera-1", baseline="chimera")
        replay = self._run_file(manifest, name="replay.json",
                                run_id="run-replay-1",
                                baseline="baseline-a", replay=True)
        report = render_report([chimera, replay],
                               manifest_paths=[manifest])
        self.assertIn("run-chimera-1", report)
        self.assertIn("run-replay-1", report)
        self.assertIn("Chimera", report)
        self.assertIn("A — replay", report)

    def test_dev_and_eval_manifests_kept_apart(self) -> None:
        dev = self._write_manifest("dev.json", manifest_id="fixture-dev",
                                   split="development")
        evl = self._write_manifest("eval.json", manifest_id="fixture-eval",
                                   split="evaluation")
        dev_run = self._run_file(dev, name="dev-run.json",
                                 run_id="run-dev-1")
        eval_run = self._run_file(evl, name="eval-run.json",
                                  run_id="run-eval-1")
        report = render_report([dev_run, eval_run],
                               manifest_paths=[dev, evl])
        self.assertIn("| development |", report)
        self.assertIn("| evaluation |", report)
        b_rows = [line for line in report.splitlines()
                  if "Baseline B — model" in line]
        self.assertEqual(len(b_rows), 2)

    def test_input_order_does_not_change_output(self) -> None:
        manifest = self._write_manifest()
        first = self._run_file(manifest, name="a.json", run_id="run-a-1")
        second = self._run_file(manifest, name="b.json", run_id="run-b-1",
                                baseline="baseline-a", replay=True)
        one = render_report([first, second], manifest_paths=[manifest])
        two = render_report([second, first], manifest_paths=[manifest])
        self.assertEqual(one, two)

    def test_duplicate_baseline_manifest_refused(self) -> None:
        manifest = self._write_manifest()
        first = self._run_file(manifest, name="a.json", run_id="run-a-1")
        second = self._run_file(manifest, name="b.json", run_id="run-b-1")
        with self.assertRaises(ReportError) as ctx:
            render_report([first, second])
        self.assertIn("appears twice", str(ctx.exception))

    def test_cross_version_comparison_refused(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest, name="a.json", run_id="run-a-1")
        data = json.loads(run.read_text(encoding="utf-8"))
        data["benchmark_version"] = "2.0.0"
        other = self.tmp / "b.json"
        other.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(ReportError) as ctx:
            render_report([run, other])
        self.assertIn("not compared", str(ctx.exception))


class AuditStateTests(ReportFixtureBase):
    def _audited(self, verdict_for: Any,
                 sample_size: int = 2) -> Dict[str, Path]:
        manifest = self._write_manifest()
        run = self._run_file(manifest, run_id="run-audit-1")
        plan_path = self.tmp / "plan.json"
        plan_audit(run, manifest, sample_size, plan_path, auditor="human-1")
        self._fill_verdicts(plan_path, verdict_for)
        audited = self.tmp / "audited.json"
        apply_audit(run, plan_path, audited)
        return {"manifest": manifest, "run": audited, "plan": plan_path}

    def test_full_agreement_is_audited(self) -> None:
        paths = self._audited(_agreeing)
        report = render_report([paths["run"]],
                               manifest_paths=[paths["manifest"]],
                               audit_plan_paths=[paths["plan"]])
        self.assertIn("**Verdict: AUDITED**", report)
        self.assertIn("agreement 100.0%", report)
        self.assertNotIn("disagreement cases", report)

    def test_sub_95_agreement_is_provisional_with_cases(self) -> None:
        seen: List[str] = []

        def _one_disagreement(bundle: Dict[str, Any]) -> Dict[str, Any]:
            checks = dict(bundle["verifier_checks"])
            if not seen:
                seen.append(bundle["trial_id"])
                first = sorted(checks)[0]
                checks[first] = not checks[first]
            return {"checks": checks, "note": "fixture"}

        paths = self._audited(_one_disagreement)
        report = render_report([paths["run"]],
                               manifest_paths=[paths["manifest"]],
                               audit_plan_paths=[paths["plan"]])
        self.assertIn("**Verdict: PROVISIONAL**", report)
        self.assertIn("agreement 50.0%", report)
        self.assertIn(f"`{seen[0]}`", report)

    def test_missing_plans_state_the_count_not_the_cases(self) -> None:
        seen: List[str] = []

        def _one_disagreement(bundle: Dict[str, Any]) -> Dict[str, Any]:
            checks = dict(bundle["verifier_checks"])
            if not seen:
                seen.append(bundle["trial_id"])
                first = sorted(checks)[0]
                checks[first] = not checks[first]
            return {"checks": checks, "note": "fixture"}

        paths = self._audited(_one_disagreement)
        report = render_report([paths["run"]],
                               manifest_paths=[paths["manifest"]])
        self.assertIn("agreement 50.0%", report)
        self.assertIn("not supplied with this report", report)
        audit = report.split("## Verifier audit")[1]
        audit = audit.split("## Failure breakdown")[0]
        self.assertNotIn(seen[0], audit)

    def test_unauditable_episode_is_not_a_disagreement(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest, run_id="run-audit-2")
        plan_path = self.tmp / "plan.json"
        plan_audit(run, manifest, 2, plan_path, auditor="human-1")
        plan_data = json.loads(plan_path.read_text(encoding="utf-8"))
        first_key = sorted(plan_data["cells"])[0]
        target = plan_data["cells"][first_key]["sampled"][0]["trial_id"]
        for cell in plan_data["cells"].values():
            for bundle in cell["sampled"]:
                if bundle["trial_id"] == target:
                    cell["verdicts"][bundle["trial_id"]] = {
                        "verdict": "unauditable", "reason": "no basis"}
                else:
                    cell["verdicts"][bundle["trial_id"]] = _agreeing(bundle)
        plan_path.write_text(json.dumps(plan_data), encoding="utf-8")
        audited = self.tmp / "audited.json"
        apply_audit(run, plan_path, audited)
        report = render_report([audited], manifest_paths=[manifest],
                               audit_plan_paths=[plan_path])
        self.assertIn("agreement 100.0%", report)
        self.assertNotIn("disagreement cases", report)

    def test_stale_plan_cells_refused(self) -> None:
        paths = self._audited(_agreeing)
        data = json.loads(paths["plan"].read_text(encoding="utf-8"))
        data["cells"] = {key.rsplit("|", 1)[0]: cell
                         for key, cell in data["cells"].items()}
        paths["plan"].write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(ReportError) as ctx:
            render_report([paths["run"]],
                           manifest_paths=[paths["manifest"]],
                           audit_plan_paths=[paths["plan"]])
        self.assertIn("cells do not match", str(ctx.exception))

    def test_partial_audit_coverage_disclosed(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest, run_id="run-partial-1")
        target = cell_key("S-NORM", "I-PLAIN", "chimera",
                          {"slow_ms": 0, "disabled": False})
        plan_path = self.tmp / "mini-plan.json"
        plan_targeted_audit(run, manifest, [target], 1, plan_path)
        self._fill_verdicts(plan_path, _agreeing)
        audited = self.tmp / "audited.json"
        apply_audit(run, plan_path, audited)
        report = render_report([audited], manifest_paths=[manifest],
                               audit_plan_paths=[plan_path])
        self.assertIn(
            "**Coverage:** 1 of 2 cells audited (1 episode adjudicated).",
            report)
        self.assertIn("**Verdict: PROVISIONAL**", report)
        self.assertIn("agreement 100.0%", report)
        self.assertIn("no sample adjudicated", report)

    def test_full_audit_coverage_line(self) -> None:
        paths = self._audited(_agreeing)
        report = render_report([paths["run"]],
                               manifest_paths=[paths["manifest"]],
                               audit_plan_paths=[paths["plan"]])
        self.assertIn(
            "**Coverage:** 2 of 2 cells audited (4 episodes adjudicated).",
            report)

    def test_plan_for_another_run_refused(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest, name="a.json", run_id="run-a-1")
        other = self._run_file(manifest, name="b.json", run_id="run-b-1")
        plan_path = self.tmp / "plan.json"
        plan_audit(other, manifest, 2, plan_path, auditor="human-1")
        with self.assertRaises(ReportError) as ctx:
            render_report([run], audit_plan_paths=[plan_path])
        self.assertIn("not among the input runs", str(ctx.exception))


class UnavailableTests(ReportFixtureBase):
    def test_missing_snapshots_null_with_reasons(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest, run_id="run-null-1",
                             write_snapshot=False, write_actions=False)
        report = render_report([run], manifest_paths=[manifest])
        null_section = report.split("## Not measurable")[1]
        null_section = null_section.split("## Verifier audit")[0]
        self.assertIn("false_successes", null_section)
        self.assertIn("episode.verification", null_section)
        summary = report.split("## Summary by cell")[1]
        summary = summary.split("## Not measurable")[0]
        self.assertIn("null (", summary)
        self.assertNotIn("0/3", summary)

    def test_manifest_from_outside_refused(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest, run_id="run-null-2")
        other = self._write_manifest("other.json",
                                     manifest_id="fixture-other")
        with self.assertRaises(ReportError) as ctx:
            render_report([run], manifest_paths=[other])
        self.assertIn("matches no input run", str(ctx.exception))


class IntegrityTests(ReportFixtureBase):
    def test_empty_input_refused(self) -> None:
        with self.assertRaises(ReportError):
            render_report([])

    def test_missing_file_refused(self) -> None:
        with self.assertRaises(ReportError) as ctx:
            render_report([self.tmp / "absent.json"])
        self.assertIn("cannot read", str(ctx.exception))

    def test_malformed_json_refused(self) -> None:
        bad = self.tmp / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        with self.assertRaises(ReportError) as ctx:
            render_report([bad])
        self.assertIn("not valid JSON", str(ctx.exception))

    def test_invalid_run_result_refused(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest, run_id="run-bad-1")
        data = json.loads(run.read_text(encoding="utf-8"))
        data["status"] = "fictional"
        bad = self.tmp / "bad.json"
        bad.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(ReportError) as ctx:
            render_report([bad])
        self.assertIn("not a valid RunResult", str(ctx.exception))

    def test_shortfall_cells_are_disclosed(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest, run_id="run-short-1")
        data = json.loads(run.read_text(encoding="utf-8"))
        data["cells"][0]["trials"] = 1
        short = self.tmp / "short.json"
        short.write_text(json.dumps(data), encoding="utf-8")
        report = render_report([short], manifest_paths=[manifest])
        exclusions = report.split("## Exclusions")[1]
        exclusions = exclusions.split("## Limitations")[0]
        self.assertIn("vs 3 configured", exclusions)
        self.assertIn("ended early", exclusions)

    def test_harness_errors_reported_separately(self) -> None:
        from benchmarks.manifest import load_manifest
        from benchmarks.runner import Runner

        def _crash(**kwargs: Any) -> Any:
            raise RuntimeError("fixture capture failed")

        manifest = self._write_manifest()
        out = self.tmp / "broken.json"
        Runner(load_manifest(manifest), output_path=out,
               trace_dir=self.tmp / "traces", executor=_crash,
               environment=self._environment(),
               run_id="run-harness-1").run()
        report = render_report([out], manifest_paths=[manifest])
        breakdown = report.split("## Failure breakdown")[1]
        breakdown = breakdown.split("## Exclusions")[0]
        self.assertIn(
            "Harness errors (reported separately, never dropped): 6",
            breakdown)
        summary = report.split("## Summary by cell")[1]
        summary = summary.split("## Not measurable")[0]
        rows = [line for line in summary.splitlines()
                if line.startswith("| `S-")]
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertTrue(row.endswith("| 3 |"), row)


class DeterminismTests(ReportFixtureBase):
    def test_identical_inputs_identical_output(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest, run_id="run-det-1")
        first = render_report([run], manifest_paths=[manifest])
        second = render_report([run], manifest_paths=[manifest])
        self.assertEqual(first, second)


class PrivacyTests(ReportFixtureBase):
    def test_form_contents_and_descriptions_excluded(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest, run_id="run-priv-1")
        report = render_report([run], manifest_paths=[manifest])
        self.assertNotIn("Benchmark Project", report)
        self.assertNotIn("Report fixture", report)
        self.assertNotIn("project_name", report)


class VerbatimDriftTests(unittest.TestCase):
    def test_disclaimers_match_section_6_3(self) -> None:
        doc = EVALUATION_DOC.read_text(encoding="utf-8")
        start = doc.index("> The current test suite")
        end = (doc.index("> recovery baseline exist.")
               + len("> recovery baseline exist."))
        self.assertEqual(DISCLAIMERS, doc[start:end])

    def test_limitations_match_section_8(self) -> None:
        doc = EVALUATION_DOC.read_text(encoding="utf-8")
        start = doc.index("1. **Scale.**")
        end = (doc.index(
            "start-up overhead, which must be excluded or disclosed.")
            + len("start-up overhead, which must be excluded or disclosed."))
        self.assertEqual(LIMITATIONS_TEXT, doc[start:end])


class ProhibitedClaimsTests(ReportFixtureBase):
    #: evaluation.md §6.4 phrases that must never appear in a report.
    PROHIBITED = ("pass rate", "production-ready", "production ready",
                  "real-world", "real world", "scales", "outperforms",
                  "improvement over", "improved", "generalises to",
                  "generalizes to")

    def test_no_prohibited_claims_in_complete_report(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest, run_id="run-claims-1")
        report = render_report([run], manifest_paths=[manifest]).lower()
        for phrase in self.PROHIBITED:
            self.assertNotIn(phrase, report)


if __name__ == "__main__":
    unittest.main()
