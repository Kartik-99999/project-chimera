"""Tests for the verifier audit procedure.

Covers: seeded sample selection and reproducibility, evidence-bundle
completeness, strict agreement/disagreement outcomes, malformed and
missing verdicts, tamper-evident apply, cell integration and
persistence, development/evaluation separation, and import hygiene.

The human adjudication in these tests is simulated with fixtures of
known verdicts: agreement computed here proves the audit *machinery*,
never the accuracy of the verifier on real episodes.

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

from benchmarks.audit import (
    AGREEMENT_THRESHOLD,
    AuditError,
    HumanVerdict,
    apply_audit,
    build_bundle,
    cell_key,
    default_seed,
    draw_order,
    is_provisional,
    load_plan,
    plan_audit,
)

PROJECT_DIR = Path(__file__).resolve().parent.parent
MANIFEST_DIR = PROJECT_DIR / "benchmarks" / "manifests"


class AuditFixtureBase(unittest.TestCase):
    """Real runner output (fake executors) as audit input."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def _manifest_dict(self, manifest_id: str = "fixture-audit",
                       split: str = "development") -> Dict[str, Any]:
        import chimera.agent as _agent

        def _scenario(sid: str, slow_ms: int) -> Dict[str, Any]:
            return {
                "id": sid,
                "description": "Fixture.",
                "fault_variants": [{"slow_ms": slow_ms, "disabled": False}],
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
            }

        return {
            "schema_version": 1,
            "benchmark_id": "chimera-local",
            "benchmark_version": "1.0.0",
            "manifest_id": manifest_id,
            "split": split,
            "description": "Audit fixture.",
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
            "scenarios": [_scenario("S-NORM", 0),
                          _scenario("S-SLOW", 2000)],
        }

    def _write_manifest(self, name: str = "m.json",
                        **kwargs: Any) -> Path:
        path = self.tmp / name
        path.write_text(json.dumps(self._manifest_dict(**kwargs)),
                        encoding="utf-8")
        return path

    def _executor(self, *, write_snapshot: bool = True,
                  write_actions: bool = True,
                  snapshot_ref: str = "sibling",
                  snapshot_items: Optional[List[str]] = None):
        import uuid as _uuid

        from benchmarks.runner import EpisodeExecution

        def _run(**kwargs: Any) -> EpisodeExecution:
            run_id = str(_uuid.uuid4())
            trace_dir = Path(kwargs["trace_dir"])
            trace_dir.mkdir(parents=True, exist_ok=True)
            events = [
                {"sequence_number": 1, "event_type": "run_started",
                 "timestamp": "2026-10-28T00:00:00.000Z", "action_type": None,
                 "action_outcome": "ok", "error_details": None,
                 "evidence_references": []},
                {"sequence_number": 2, "event_type": "run_succeeded",
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
                "terminal_status": "succeeded",
                "event_count": len(events), "events": events,
            }), encoding="utf-8")
            items = (["Benchmark Project"] if snapshot_items is None
                     else list(snapshot_items))
            snapshot = {"run_id": run_id, "confirmation_visible": True,
                        "items": items, "captured_at": ""}
            snap_path = trace_dir / f"{run_id}.snapshot.json"
            if write_snapshot:
                snap_path.write_text(json.dumps(snapshot), encoding="utf-8")
            ref = str(snap_path) if snapshot_ref == "sibling" else snapshot_ref
            if write_actions:
                (trace_dir / f"{run_id}.actions.json").write_text(
                    json.dumps({"run_id": run_id, "attached": True,
                                "complete": True, "records": []}),
                    encoding="utf-8")
            return EpisodeExecution(
                run_id=run_id, trace_path=str(trace_path),
                reported_status="succeeded", error=None,
                state_snapshot=dict(snapshot), snapshot_ref=ref,
                episode_url="file://demo",
                action_log={
                    "run_id": run_id, "attached": True, "complete": True,
                    "records": [{
                        "seq": 1, "action_type": "navigate",
                        "target": {"url": "file://demo"},
                        "target_summary": "goto", "outcome": "ok",
                        "policy": "allowed", "policy_reason": "",
                        "error_type": None, "elapsed_ms": 0,
                    }]},
            )

        return _run

    def _environment(self) -> Any:
        from benchmarks.results import EnvironmentInfo

        return EnvironmentInfo(
            python_version="test", playwright_version="test",
            browser="chromium", browser_build="test", platform="test",
            demo_app_sha256="d" * 64, dev_manifest_sha256="e" * 64,
            eval_manifest_sha256="f" * 64)

    def _run_file(self, manifest_path: Path, name: str = "run.json",
                  **executor_kwargs: Any) -> Path:
        from benchmarks.manifest import load_manifest
        from benchmarks.runner import Runner

        out = self.tmp / name
        Runner(
            load_manifest(manifest_path), output_path=out,
            trace_dir=self.tmp / "traces",
            executor=self._executor(**executor_kwargs),
            environment=self._environment()).run()
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


class SamplingTests(AuditFixtureBase):
    def test_draw_order_is_a_reproducible_permutation(self) -> None:
        ids = [f"trial-{n:04d}" for n in range(1, 6)]
        first = draw_order(ids, "seed-1")
        self.assertEqual(draw_order(ids, "seed-1"), first)
        self.assertEqual(sorted(first), sorted(ids))
        self.assertNotEqual(draw_order(ids, "seed-2"), first)

    def test_default_seed_derives_from_run_and_cell(self) -> None:
        self.assertEqual(default_seed("run-1", "S-NORM|I-PLAIN|chimera"),
                         "run-1:S-NORM|I-PLAIN|chimera")

    def test_plan_samples_per_cell_and_excludes_warmups(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest)
        plan = plan_audit(run, manifest, 2, self.tmp / "plan.json",
                          auditor="human-1")
        self.assertEqual(len(plan.cells), 2)
        for key, sample in plan.cells.items():
            self.assertEqual(len(sample.sampled), 2)
            self.assertEqual(sample.skipped, [])
            for bundle in sample.sampled:
                self.assertFalse(
                    bundle.trial_id.startswith("warmup:"))
                self.assertEqual(sample.seed, default_seed(plan.run_id, key))
        self.assertEqual(plan.sample_size, 2)
        self.assertEqual(plan.auditor, "human-1")
        self.assertEqual(plan.manifest_id, "fixture-audit")

    def test_plan_is_reproducible_from_persisted_info(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest)
        first = plan_audit(run, manifest, 2, self.tmp / "p1.json")
        second = plan_audit(run, manifest, 2, self.tmp / "p2.json")
        for key in first.cells:
            self.assertEqual(
                [b.trial_id for b in first.cells[key].sampled],
                [b.trial_id for b in second.cells[key].sampled])

    def test_explicit_seed_is_recorded(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest)
        plan = plan_audit(run, manifest, 1, self.tmp / "plan.json",
                          seed="explicit-seed")
        for sample in plan.cells.values():
            self.assertEqual(sample.seed, "explicit-seed")

    def test_oversubscription_fails_closed(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest)
        with self.assertRaises(AuditError) as ctx:
            plan_audit(run, manifest, 99, self.tmp / "plan.json")
        self.assertIn("auditable", str(ctx.exception))
        self.assertFalse((self.tmp / "plan.json").exists())

    def test_zero_sample_size_plans_nothing(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest)
        plan = plan_audit(run, manifest, 0, self.tmp / "plan.json")
        for sample in plan.cells.values():
            self.assertEqual(sample.sampled, [])

    def test_incomplete_bundles_are_skipped_with_reasons(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest, write_snapshot=False)
        with self.assertRaises(AuditError) as ctx:
            plan_audit(run, manifest, 1, self.tmp / "plan.json")
        self.assertIn("snapshot missing", str(ctx.exception))


class BundleTests(AuditFixtureBase):
    def _first_episode(self) -> Any:
        from benchmarks.results import RunResult

        manifest = self._write_manifest()
        run_path = self._run_file(manifest)
        run = RunResult.from_dict(
            json.loads(run_path.read_text(encoding="utf-8")))
        return run, manifest

    def test_complete_bundle_carries_evidence_and_digests(self) -> None:
        from benchmarks.manifest import load_manifest

        run, manifest_path = self._first_episode()
        manifest = load_manifest(manifest_path)
        episode = next(e for e in run.episodes
                       if not e.trial_id.startswith("warmup:"))
        bundle, reason = build_bundle(episode, manifest)
        self.assertIsNone(reason)
        assert bundle is not None
        self.assertEqual(bundle.expected_stored_name, "Benchmark Project")
        self.assertEqual(bundle.verifier_checks,
                         {"P1": True, "P2": True, "P3": True})
        self.assertEqual(bundle.agent_terminal_status, "succeeded")
        self.assertIn("trace", bundle.digests)
        self.assertIn("snapshot", bundle.digests)
        self.assertIn("actions", bundle.digests)

    def test_missing_actions_file_does_not_block(self) -> None:
        from benchmarks.manifest import load_manifest
        from benchmarks.results import RunResult

        manifest_path = self._write_manifest()
        run_path = self._run_file(manifest_path, write_actions=False)
        run = RunResult.from_dict(
            json.loads(run_path.read_text(encoding="utf-8")))
        manifest = load_manifest(manifest_path)
        episode = next(e for e in run.episodes
                       if not e.trial_id.startswith("warmup:"))
        bundle, reason = build_bundle(episode, manifest)
        self.assertIsNone(reason)
        assert bundle is not None
        self.assertNotIn("actions", bundle.digests)

    def test_reference_mismatch_blocks(self) -> None:
        from benchmarks.manifest import load_manifest
        from benchmarks.results import RunResult

        manifest_path = self._write_manifest()
        run_path = self._run_file(
            manifest_path, snapshot_ref="/elsewhere/snap.json")
        run = RunResult.from_dict(
            json.loads(run_path.read_text(encoding="utf-8")))
        manifest = load_manifest(manifest_path)
        episode = next(e for e in run.episodes
                       if not e.trial_id.startswith("warmup:"))
        bundle, reason = build_bundle(episode, manifest)
        self.assertIsNone(bundle)
        assert reason is not None
        self.assertIn("mismatch", reason)

    def test_missing_verifier_verdict_blocks(self) -> None:
        import dataclasses as _dataclasses

        from benchmarks.manifest import load_manifest
        from benchmarks.results import VerificationEvidence

        run, manifest_path = self._first_episode()
        manifest = load_manifest(manifest_path)
        episode = next(e for e in run.episodes
                       if not e.trial_id.startswith("warmup:"))
        unverified = _dataclasses.replace(
            episode, verification=VerificationEvidence.not_yet_verified(
                "no snapshot"))
        bundle, reason = build_bundle(unverified, manifest)
        self.assertIsNone(bundle)
        assert reason is not None
        self.assertIn("no verifier verdict", reason)

    def test_unknown_scenario_blocks(self) -> None:
        import dataclasses as _dataclasses

        from benchmarks.manifest import load_manifest

        run, manifest_path = self._first_episode()
        manifest = load_manifest(manifest_path)
        episode = next(e for e in run.episodes
                       if not e.trial_id.startswith("warmup:"))
        foreign = _dataclasses.replace(episode, scenario_id="S-NOPE")
        bundle, reason = build_bundle(foreign, manifest)
        self.assertIsNone(bundle)
        assert reason is not None
        self.assertIn("S-NOPE", reason)

    def test_plan_copies_no_snapshot_contents(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest, snapshot_items=["Canary XYZ Secret"])
        plan_path = self.tmp / "plan.json"
        plan_audit(run, manifest, 2, plan_path)
        self.assertNotIn("Canary XYZ", plan_path.read_text(encoding="utf-8"))


class VerdictTests(AuditFixtureBase):
    def test_strict_per_check_agreement(self) -> None:
        self.assertTrue(HumanVerdict(
            {"P1": True, "P2": True, "P3": True}).agrees_with(
                {"P1": True, "P2": True, "P3": True}))
        # Same conjunction, differing check: still a disagreement.
        self.assertFalse(HumanVerdict(
            {"P1": False, "P2": False, "P3": True}).agrees_with(
                {"P1": True, "P2": False, "P3": True}))
        self.assertFalse(HumanVerdict(
            {"P1": True, "P2": True}).agrees_with(
                {"P1": True, "P2": True, "P3": True}))

    def test_malformed_verdicts_rejected_at_load(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest)
        plan_path = self.tmp / "plan.json"
        plan_audit(run, manifest, 1, plan_path)
        bad_verdicts = [
            "agree",
            {"checks": {}},
            {"checks": {"P1": "yes", "P2": True, "P3": True}},
            {"verdict": "unauditable"},
            {"verdict": "unauditable", "reason": "  "},
            {"note": "no checks"},
        ]
        for index, bad in enumerate(bad_verdicts):
            with self.subTest(bad=bad):
                data = json.loads(plan_path.read_text(encoding="utf-8"))
                key = sorted(data["cells"])[0]
                trial = data["cells"][key]["sampled"][0]["trial_id"]
                data["cells"][key]["verdicts"] = {trial: bad}
                probe = self.tmp / f"bad-{index}.json"
                probe.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaises(AuditError):
                    load_plan(probe)

    def test_incomplete_and_extra_verdicts_refused_at_apply(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest)
        plan_path = self.tmp / "plan.json"
        plan_audit(run, manifest, 1, plan_path)
        out = self.tmp / "out.json"
        # No verdicts at all.
        with self.assertRaises(AuditError) as ctx:
            apply_audit(run, plan_path, out)
        self.assertIn("missing=", str(ctx.exception))
        self.assertFalse(out.exists())
        # An extra verdict for an unsampled episode.
        data = json.loads(plan_path.read_text(encoding="utf-8"))
        key = sorted(data["cells"])[0]
        trial = data["cells"][key]["sampled"][0]["trial_id"]
        data["cells"][key]["verdicts"] = {
            trial: {"checks": {"P1": True, "P2": True, "P3": True}},
            "trial-9999": {"checks": {"P1": True}},
        }
        other = sorted(data["cells"])[1]
        other_trial = data["cells"][other]["sampled"][0]["trial_id"]
        data["cells"][other]["verdicts"] = {
            other_trial: {"checks": {"P1": True, "P2": True, "P3": True}}}
        plan_path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(AuditError) as ctx:
            apply_audit(run, plan_path, out)
        self.assertIn("extra=", str(ctx.exception))
        self.assertFalse(out.exists())

    def test_partial_verdict_refused_at_apply(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest)
        plan_path = self.tmp / "plan.json"
        plan_audit(run, manifest, 1, plan_path)
        data = json.loads(plan_path.read_text(encoding="utf-8"))
        for cell in data["cells"].values():
            trial = cell["sampled"][0]["trial_id"]
            cell["verdicts"] = {trial: {"checks": {"P1": True}}}
        plan_path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(AuditError) as ctx:
            apply_audit(run, plan_path, self.tmp / "out.json")
        self.assertIn("do not match the verifier's checks",
                      str(ctx.exception))

    def test_changed_bytes_refused_at_apply(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest)
        plan_path = self.tmp / "plan.json"
        plan_audit(run, manifest, 1, plan_path)
        self._fill_verdicts(plan_path, _agreeing)
        data = json.loads(plan_path.read_text(encoding="utf-8"))
        key = sorted(data["cells"])[0]
        snap = data["cells"][key]["sampled"][0]["snapshot_path"]
        with open(snap, "a", encoding="utf-8") as handle:
            handle.write(" ")
        with self.assertRaises(AuditError) as ctx:
            apply_audit(run, plan_path, self.tmp / "out.json")
        self.assertIn("changed since the plan", str(ctx.exception))

    def test_run_and_manifest_mismatch_refused(self) -> None:
        dev_manifest = self._write_manifest("dev.json")
        dev_run = self._run_file(dev_manifest, name="dev-run.json")
        eval_manifest = self._write_manifest(
            "eval.json", manifest_id="fixture-eval", split="evaluation")
        plan_path = self.tmp / "plan.json"
        plan_audit(dev_run, dev_manifest, 1, plan_path)
        self._fill_verdicts(plan_path, _agreeing)
        # Same verdicts, different run file.
        other_run = self._run_file(dev_manifest, name="other.json")
        with self.assertRaises(AuditError) as ctx:
            apply_audit(other_run, plan_path, self.tmp / "out.json")
        self.assertIn("targets run", str(ctx.exception))
        # Eval plan cannot apply to a dev run (checked at plan time too).
        with self.assertRaises(AuditError) as ctx:
            plan_audit(dev_run, eval_manifest, 1, self.tmp / "evil.json")
        self.assertIn("never be mixed", str(ctx.exception))


class ApplyTests(AuditFixtureBase):
    def test_agreement_computed_per_cell(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest)
        plan_path = self.tmp / "plan.json"
        plan_audit(run, manifest, 2, plan_path, auditor="human-1")

        def _verdict(bundle: Dict[str, Any]) -> Dict[str, Any]:
            if bundle["scenario_id"] == "S-NORM":
                return {"checks": dict(bundle["verifier_checks"]),
                        "note": "agree"}
            checks = dict(bundle["verifier_checks"])
            checks["P2"] = not checks["P2"]
            return {"checks": checks, "note": "P2 differs"}

        self._fill_verdicts(plan_path, _verdict)
        result = apply_audit(run, plan_path, self.tmp / "audited.json")
        by_scenario = {c.scenario_id: c for c in result.cells}
        norm = by_scenario["S-NORM"].verifier_audit
        assert norm is not None
        self.assertEqual((norm.sampled, norm.agreed), (2, 2))
        self.assertEqual(norm.agreement_rate, 1.0)
        self.assertIn("human-1", norm.note)
        slow = by_scenario["S-SLOW"].verifier_audit
        assert slow is not None
        self.assertEqual((slow.sampled, slow.agreed), (2, 0))
        self.assertEqual(slow.agreement_rate, 0.0)

    def test_human_unauditable_excluded_from_fraction(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest)
        plan_path = self.tmp / "plan.json"
        plan_audit(run, manifest, 2, plan_path)

        def _verdict(bundle: Dict[str, Any]) -> Dict[str, Any]:
            if bundle["trial_id"].endswith("1"):
                return {"verdict": "unauditable",
                        "reason": "snapshot illegible to the human"}
            return {"checks": dict(bundle["verifier_checks"])}

        data = self._fill_verdicts(plan_path, _verdict)
        result = apply_audit(run, plan_path, self.tmp / "audited.json")
        for cell in result.cells:
            audit = cell.verifier_audit
            assert audit is not None
            key = cell_key(cell.scenario_id, cell.input_id,
                            cell.baseline, cell.fault_params)
            flagged = sum(
                1 for v in data["cells"][key]["verdicts"].values()
                if isinstance(v, dict) and v.get("verdict") == "unauditable")
            self.assertEqual(audit.sampled, 2 - flagged)
            self.assertEqual(audit.agreed, 2 - flagged)
            if flagged:
                self.assertIn("unauditable", audit.note)

    def test_all_unauditable_cell_stays_null(self) -> None:
        manifest = self._write_manifest()
        run = self._run_file(manifest)
        plan_path = self.tmp / "plan.json"
        plan_audit(run, manifest, 1, plan_path)
        self._fill_verdicts(
            plan_path,
            lambda bundle: {"verdict": "unauditable", "reason": "no basis"})
        result = apply_audit(run, plan_path, self.tmp / "audited.json")
        for cell in result.cells:
            self.assertIsNone(cell.verifier_audit)

    def test_apply_preserves_everything_else_byte_identical(self) -> None:
        import hashlib as _hashlib

        manifest = self._write_manifest()
        run = self._run_file(manifest)
        before = run.read_bytes()
        plan_path = self.tmp / "plan.json"
        plan_audit(run, manifest, 1, plan_path)
        self._fill_verdicts(plan_path, _agreeing)
        out = self.tmp / "audited.json"
        apply_audit(run, plan_path, out)
        # The input file is untouched; only verifier_audit differs.
        self.assertEqual(run.read_bytes(), before)
        self.assertEqual(
            _hashlib.sha256(run.read_bytes()).hexdigest(),
            _hashlib.sha256(before).hexdigest())
        original = json.loads(before.decode("utf-8"))
        audited = json.loads(out.read_text(encoding="utf-8"))
        for cell in audited["cells"]:
            cell["verifier_audit"] = None
        self.assertEqual(audited, original)
        # And the output is a valid run file.
        from benchmarks.runner import load_run_result

        loaded = load_run_result(out)
        self.assertTrue(all(c.verifier_audit is not None
                            for c in loaded.cells))

    def test_provisional_rule(self) -> None:
        self.assertEqual(AGREEMENT_THRESHOLD, 0.95)
        self.assertIs(is_provisional(None), True)
        self.assertIs(is_provisional(0.94), True)
        self.assertIs(is_provisional(0.95), False)
        self.assertIs(is_provisional(1.0), False)


class SeparationTests(AuditFixtureBase):
    def test_plan_records_manifest_identity(self) -> None:
        from benchmarks.manifest import load_manifest

        manifest_path = self._write_manifest(
            manifest_id="fixture-eval", split="evaluation")
        run = self._run_file(manifest_path)
        plan = plan_audit(run, manifest_path, 1, self.tmp / "plan.json")
        manifest = load_manifest(manifest_path)
        self.assertEqual(plan.manifest_id, "fixture-eval")
        self.assertEqual(plan.manifest_sha256, manifest.sha256())
        for sample in plan.cells.values():
            for bundle in sample.sampled:
                self.assertEqual(bundle.manifest_id, "fixture-eval")


class HygieneTests(unittest.TestCase):
    def test_importing_audit_pulls_no_browser_or_agent(self) -> None:
        probe = (
            "import sys; "
            "import benchmarks.audit as _a; "
            "loaded = [m for m in sys.modules "
            "if m.split('.')[0] in ('chimera', 'playwright') "
            "or m in ('benchmarks.runner', 'benchmarks.verifier', "
            "'benchmarks.observer', 'benchmarks.baseline_a')]; "
            "assert not loaded, loaded; "
            "print('clean')"
        )
        completed = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=str(PROJECT_DIR), capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("clean", completed.stdout)

    def test_audit_source_imports_only_stdlib_and_contracts(self) -> None:
        import ast as _ast

        allowed = {"json", "hashlib", "dataclasses", "datetime", "pathlib",
                   "typing", "benchmarks.manifest", "benchmarks.results",
                   "__future__"}
        source = (PROJECT_DIR / "benchmarks" / "audit.py").read_text(
            encoding="utf-8")
        for node in _ast.walk(_ast.parse(source)):
            if isinstance(node, _ast.Import):
                for alias in node.names:
                    self.assertIn(alias.name.split(".")[0],
                                  {a.split(".")[0] for a in allowed},
                                  f"audit imports {alias.name}")
            elif isinstance(node, _ast.ImportFrom):
                self.assertIn(node.module, allowed,
                              f"audit imports from {node.module}")


class MultiVariantTests(AuditFixtureBase):
    """One scenario/input pair with several fault variants.

    Regression coverage for the eval-v1 shape (S-SLOW carries five
    slow values): each variant is its own cell with its own sample
    drawn from its own episodes — variant cells must neither share
    a plan entry nor pool their episodes.
    """

    def _variant_manifest(self) -> Path:
        import chimera.agent as _agent

        def _scenario(sid: str, variants: List[Dict[str, Any]],
                      expected: str) -> Dict[str, Any]:
            return {
                "id": sid,
                "description": "Variant fixture.",
                "fault_variants": variants,
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

        manifest = {
            "schema_version": 1,
            "benchmark_id": "chimera-local",
            "benchmark_version": "1.0.0",
            "manifest_id": "fixture-variants",
            "split": "development",
            "description": "Variant fixture.",
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
            "scenarios": [
                _scenario("S-NORM", [{"slow_ms": 0, "disabled": False}],
                          "succeeded"),
                _scenario("S-SLOW", [{"slow_ms": 800, "disabled": False},
                                     {"slow_ms": 3000, "disabled": False}],
                          "succeeded"),
            ],
        }
        path = self.tmp / "variant-manifest.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path

    def test_cell_key_distinguishes_fault_variants(self) -> None:
        slow = cell_key("S-SLOW", "I-PLAIN", "chimera",
                        {"slow_ms": 800, "disabled": False})
        slower = cell_key("S-SLOW", "I-PLAIN", "chimera",
                          {"slow_ms": 3000, "disabled": False})
        self.assertNotEqual(slow, slower)
        self.assertIn("slow_ms=800", slow)
        self.assertIn("slow_ms=3000", slower)
        self.assertEqual(slow, cell_key("S-SLOW", "I-PLAIN", "chimera",
                                        {"disabled": False,
                                         "slow_ms": 800}))

    def test_variant_cells_sampled_from_own_episodes(self) -> None:
        from benchmarks.runner import load_run_result

        manifest = self._variant_manifest()
        run_path = self._run_file(manifest, name="variants.json")
        plan_path = self.tmp / "plan.json"
        plan = plan_audit(run_path, manifest, 2, plan_path,
                          auditor="human-1")
        self.assertEqual(len(plan.cells), 3)
        run = load_run_result(run_path)
        measured = [e.trial_id for e in run.episodes
                    if not e.trial_id.startswith("warmup:")]
        cursor = 0
        seen: List[str] = []
        for cell in run.cells:
            owned = measured[cursor:cursor + cell.trials]
            cursor += cell.trials
            key = cell_key(cell.scenario_id, cell.input_id,
                           cell.baseline, cell.fault_params)
            sample = plan.cells[key]
            drawn = [b.trial_id for b in sample.sampled]
            self.assertEqual(len(drawn), 2)
            for trial_id in drawn:
                self.assertIn(trial_id, owned)
            seen.extend(drawn)
        # Disjoint pools, so no trial is sampled twice.
        self.assertEqual(len(seen), len(set(seen)))
        seeds = {s.seed for s in plan.cells.values()}
        self.assertEqual(len(seeds), 3)

    def test_variant_cells_apply_independently(self) -> None:
        manifest = self._variant_manifest()
        run_path = self._run_file(manifest, name="variants.json")
        plan_path = self.tmp / "plan.json"
        plan_audit(run_path, manifest, 2, plan_path, auditor="human-1")
        data = json.loads(plan_path.read_text(encoding="utf-8"))
        target = next(k for k in data["cells"] if "slow_ms=3000" in k)
        for key, cell in data["cells"].items():
            for bundle in cell["sampled"]:
                checks = dict(bundle["verifier_checks"])
                if key == target and bundle == cell["sampled"][0]:
                    first = sorted(checks)[0]
                    checks[first] = not checks[first]
                cell["verdicts"][bundle["trial_id"]] = {"checks": checks}
        plan_path.write_text(json.dumps(data), encoding="utf-8")
        result = apply_audit(run_path, plan_path,
                             self.tmp / "audited.json")
        for cell in result.cells:
            key = cell_key(cell.scenario_id, cell.input_id,
                           cell.baseline, cell.fault_params)
            audit = cell.verifier_audit
            assert audit is not None
            if key == target:
                self.assertEqual((audit.sampled, audit.agreed), (2, 1))
            else:
                self.assertEqual((audit.sampled, audit.agreed), (2, 2))


class TargetedSamplingTests(AuditFixtureBase):
    """Sampling selected cells only (reduced human workload).

    Untargeted cells ride as empty samples so the plan still covers
    every run cell exactly; apply maps them to ``verifier_audit``
    None (unaudited), never to agreement.
    """

    def _two_cell_run(self) -> Any:
        manifest = self._write_manifest()
        return self._run_file(manifest), manifest

    def test_draws_only_listed_cells(self) -> None:
        from benchmarks.audit import plan_targeted_audit

        run, manifest = self._two_cell_run()
        target = cell_key("S-NORM", "I-PLAIN", "chimera",
                          {"slow_ms": 0, "disabled": False})
        plan = plan_targeted_audit(run, manifest, [target], 1,
                                   self.tmp / "mini-plan.json")
        self.assertEqual(len(plan.cells), 2)
        self.assertEqual(plan.sample_size, 1)
        hit = plan.cells[target]
        self.assertEqual(len(hit.sampled), 1)
        self.assertEqual(hit.verdicts, {})
        other_key = next(k for k in plan.cells if k != target)
        other = plan.cells[other_key]
        self.assertEqual(other.sampled, [])
        self.assertEqual(other.skipped, [])
        self.assertEqual(other.verdicts, {})

    def test_apply_leaves_untargeted_unaudited(self) -> None:
        from benchmarks.audit import plan_targeted_audit

        run, manifest = self._two_cell_run()
        target = cell_key("S-NORM", "I-PLAIN", "chimera",
                          {"slow_ms": 0, "disabled": False})
        plan_path = self.tmp / "mini-plan.json"
        plan_targeted_audit(run, manifest, [target], 1, plan_path)
        self._fill_verdicts(plan_path, _agreeing)
        result = apply_audit(run, plan_path, self.tmp / "audited.json")
        for cell in result.cells:
            key = cell_key(cell.scenario_id, cell.input_id,
                           cell.baseline, cell.fault_params)
            if key == target:
                audit = cell.verifier_audit
                assert audit is not None
                self.assertEqual((audit.sampled, audit.agreed), (1, 1))
                self.assertEqual(audit.agreement_rate, 1.0)
            else:
                self.assertIsNone(cell.verifier_audit)

    def test_rejects_unknown_empty_and_bad_sizes(self) -> None:
        from benchmarks.audit import plan_targeted_audit

        run, manifest = self._two_cell_run()
        out = self.tmp / "mini-plan.json"
        with self.assertRaises(AuditError) as ctx:
            plan_targeted_audit(run, manifest, ["S-NOPE|X|chimera|"], 1,
                                out)
        self.assertIn("not in run", str(ctx.exception))
        with self.assertRaises(AuditError):
            plan_targeted_audit(run, manifest, [], 1, out)
        target = cell_key("S-NORM", "I-PLAIN", "chimera",
                          {"slow_ms": 0, "disabled": False})
        for bad in (0, -1, True, "1"):
            with self.assertRaises(AuditError, msg=f"size={bad!r}"):
                plan_targeted_audit(run, manifest, [target], bad, out)
        self.assertFalse(out.exists())

    def test_shortfall_fails_closed(self) -> None:
        from benchmarks.audit import plan_targeted_audit

        run, manifest = self._two_cell_run()
        target = cell_key("S-NORM", "I-PLAIN", "chimera",
                          {"slow_ms": 0, "disabled": False})
        with self.assertRaises(AuditError) as ctx:
            plan_targeted_audit(run, manifest, [target], 5,
                                self.tmp / "mini-plan.json")
        self.assertIn("only 3 of 5", str(ctx.exception))

    def test_targeted_draw_is_deterministic(self) -> None:
        from benchmarks.audit import plan_targeted_audit

        run, manifest = self._two_cell_run()
        target = cell_key("S-NORM", "I-PLAIN", "chimera",
                          {"slow_ms": 0, "disabled": False})
        first = plan_targeted_audit(run, manifest, [target], 1,
                                    self.tmp / "a.json")
        second = plan_targeted_audit(run, manifest, [target], 1,
                                     self.tmp / "b.json")
        self.assertEqual(
            [b.trial_id for b in first.cells[target].sampled],
            [b.trial_id for b in second.cells[target].sampled])


if __name__ == "__main__":
    unittest.main()
