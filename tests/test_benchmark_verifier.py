"""Tests for the independent verifier (harness Stage 3).

Covers: the snapshot schema, exact-match P1–P3 evaluation (including
the whitespace/case/substring traps the agent's own ``has_text`` check
would miss), missing/malformed/mismatched evidence failing closed,
false-success and disagreement classification, runner wiring, the
agent's observation seam (via a fake Playwright module — no browser),
and verifier independence from agent verification logic.

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

from benchmarks.results import (
    EnvironmentInfo,
    EpisodeOutcome,
    VerificationEvidence,
)
from benchmarks.verifier import (
    DOMSnapshot,
    SnapshotValidationError,
    capture_page_state,
    classify_false_success,
    is_verifier_disagreement,
    load_snapshot,
    snapshot_path_for,
    summarize_checks,
    verify_postconditions,
)

PROJECT_DIR = Path(__file__).resolve().parent.parent


def _snapshot_dict(run_id: str = "run-1", **overrides: Any) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "run_id": run_id,
        "confirmation_visible": True,
        "items": ["Benchmark Project"],
        "captured_at": "2026-10-28T00:00:00.000Z",
    }
    base.update(overrides)
    return base


def _verified(all_satisfied: bool) -> VerificationEvidence:
    from benchmarks.results import PostconditionCheck

    return VerificationEvidence(
        status=VerificationEvidence.VERIFIED,
        all_satisfied=all_satisfied,
        checks=(
            PostconditionCheck("P1", all_satisfied, "ref#P1"),
            PostconditionCheck("P2", all_satisfied, "ref#P2"),
            PostconditionCheck("P3", all_satisfied, "ref#P3"),
        ),
        verifier_version="test",
    )


class SnapshotSchemaTests(unittest.TestCase):
    def test_valid_snapshot_round_trips(self) -> None:
        snapshot = DOMSnapshot.from_dict(_snapshot_dict())
        self.assertEqual(snapshot.run_id, "run-1")
        self.assertIs(snapshot.confirmation_visible, True)
        self.assertEqual(snapshot.items, ("Benchmark Project",))
        self.assertEqual(DOMSnapshot.from_dict(snapshot.to_dict()), snapshot)
        self.assertEqual(DOMSnapshot.from_json(snapshot.to_json()), snapshot)

    def test_malformed_snapshots_fail_closed(self) -> None:
        cases = {
            "missing items": {"run_id": "r", "confirmation_visible": True},
            "missing flag": {"run_id": "r", "items": []},
            "missing run_id": {"confirmation_visible": True, "items": []},
            "flag is 1": _snapshot_dict(confirmation_visible=1),
            "flag is 'true'": _snapshot_dict(confirmation_visible="true"),
            "flag is None": _snapshot_dict(confirmation_visible=None),
            "items is a string": _snapshot_dict(items="Benchmark Project"),
            "items hold non-strings": _snapshot_dict(items=["ok", 7]),
            "run_id empty": _snapshot_dict(run_id="  "),
            "captured_at non-string": _snapshot_dict(captured_at=5),
        }
        for label, raw in cases.items():
            with self.subTest(label):
                with self.assertRaises(SnapshotValidationError):
                    DOMSnapshot.from_dict(raw)  # type: ignore[arg-type]

    def test_non_object_snapshot_fails_closed(self) -> None:
        for raw in ("[]", "[1, 2]", '"x"', "42"):
            with self.subTest(raw):
                with self.assertRaises(SnapshotValidationError):
                    DOMSnapshot.from_json(raw)
        with self.assertRaises(SnapshotValidationError):
            DOMSnapshot.from_json("{invalid")

    def test_load_snapshot_missing_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SnapshotValidationError) as ctx:
                load_snapshot(Path(tmp) / "absent.snapshot.json")
            self.assertIn("unreadable", str(ctx.exception))

    def test_load_snapshot_round_trips_from_disk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = snapshot_path_for(Path(tmp), "run-9")
            self.assertTrue(str(path).endswith(".snapshot.json"))
            snapshot = DOMSnapshot.from_dict(_snapshot_dict("run-9"))
            path.write_text(snapshot.to_json(), encoding="utf-8")
            self.assertEqual(load_snapshot(path), snapshot)


class CaptureTests(unittest.TestCase):
    """The harness observer reads raw state with exact selectors."""

    class _Locator:
        def __init__(self, owner: "CaptureTests._Page", selector: str) -> None:
            self._owner = owner
            self._selector = selector

        def is_visible(self) -> bool:
            self._owner.calls.append(("is_visible", self._selector))
            return self._owner.visible

        def all_text_contents(self) -> List[str]:
            self._owner.calls.append(("all_text_contents", self._selector))
            return list(self._owner.items)

    class _Page:
        def __init__(self, visible: bool, items: List[str]) -> None:
            self.visible = visible
            self.items = items
            self.calls: List[Any] = []

        def locator(self, selector: str, **kwargs: Any) -> Any:
            assert not kwargs, "verifier must not pass match options"
            return CaptureTests._Locator(self, selector)

    def test_capture_reads_visibility_and_exact_text_contents(self) -> None:
        page = self._Page(True, ["  Padded  ", "other"])
        state = capture_page_state(page)
        self.assertEqual(
            state,
            {"confirmation_visible": True, "items": ["  Padded  ", "other"]},
        )
        self.assertIn(("is_visible", "#confirmation"), page.calls)
        self.assertIn(("all_text_contents", "#project-list li"), page.calls)

    def test_capture_performs_no_matching(self) -> None:
        page = self._Page(False, [])
        state = capture_page_state(page)
        self.assertEqual(
            state, {"confirmation_visible": False, "items": []})


class ExactMatchTests(unittest.TestCase):
    def _verify(self, expected_stored_name: str = "Benchmark Project",
                **snapshot: Any) -> VerificationEvidence:
        raw = _snapshot_dict("run-1")
        raw.update(snapshot)
        return verify_postconditions(
            snapshot=raw, expected_stored_name=expected_stored_name,
            snapshot_ref="snap.json", run_id="run-1")

    def _by_id(self, evidence: VerificationEvidence) -> Dict[str, bool]:
        return {c.postcondition_id: c.satisfied for c in evidence.checks}

    def test_success_when_all_postconditions_hold(self) -> None:
        evidence = self._verify()
        self.assertEqual(evidence.status, VerificationEvidence.VERIFIED)
        self.assertIs(evidence.all_satisfied, True)
        self.assertEqual(self._by_id(evidence),
                         {"P1": True, "P2": True, "P3": True})
        self.assertTrue(evidence.verifier_version)
        for check in evidence.checks:
            self.assertTrue(check.evidence_reference.startswith("snap.json#"))

    def test_hidden_confirmation_fails_p1_only(self) -> None:
        evidence = self._verify(confirmation_visible=False)
        self.assertEqual(self._by_id(evidence),
                         {"P1": False, "P2": True, "P3": True})
        self.assertIs(evidence.all_satisfied, False)

    def test_wrong_name_fails_p2_only(self) -> None:
        evidence = self._verify(items=["Something Else"])
        self.assertEqual(self._by_id(evidence),
                         {"P1": True, "P2": False, "P3": True})

    def test_two_items_fail_p3(self) -> None:
        evidence = self._verify(items=["Benchmark Project", "Other"])
        verdicts = self._by_id(evidence)
        self.assertIs(verdicts["P3"], False)
        # P2 still holds: the expected name appears exactly once.
        self.assertIs(verdicts["P2"], True)
        self.assertIs(evidence.all_satisfied, False)

    def test_duplicate_expected_name_fails_p2(self) -> None:
        evidence = self._verify(
            items=["Benchmark Project", "Benchmark Project"])
        verdicts = self._by_id(evidence)
        self.assertIs(verdicts["P2"], False)
        self.assertIs(verdicts["P3"], False)

    def test_unpadded_observation_of_padded_input_fails_p2(self) -> None:
        """Exact match means exact: surrounding whitespace matters."""
        evidence = self._verify(expected_stored_name="Padded Name",
                                items=["  Padded Name  "])
        self.assertIs(self._by_id(evidence)["P2"], False)

    def test_case_difference_fails_p2(self) -> None:
        evidence = self._verify(items=["benchmark project"])
        self.assertIs(self._by_id(evidence)["P2"], False)

    def test_substring_is_not_a_match(self) -> None:
        """The agent's ``has_text`` substring check would accept this;
        the independent verifier must not."""
        evidence = self._verify(expected_stored_name="Benchmark",
                                items=["Benchmark Project"])
        verdicts = self._by_id(evidence)
        self.assertIs(verdicts["P2"], False)
        self.assertIs(verdicts["P3"], True)

    def test_empty_list_fails_p2_and_p3(self) -> None:
        evidence = self._verify(items=[])
        verdicts = self._by_id(evidence)
        self.assertIs(verdicts["P2"], False)
        self.assertIs(verdicts["P3"], False)

    def test_accepts_a_parsed_snapshot(self) -> None:
        evidence = verify_postconditions(
            snapshot=DOMSnapshot.from_dict(_snapshot_dict("run-1")),
            expected_stored_name="Benchmark Project",
            snapshot_ref="snap.json", run_id="run-1")
        self.assertIs(evidence.all_satisfied, True)


class MissingEvidenceTests(unittest.TestCase):
    def test_missing_snapshot_is_unavailable_with_reason(self) -> None:
        evidence = verify_postconditions(
            snapshot=None, expected_stored_name="Benchmark Project",
            snapshot_ref="", run_id="run-1",
            observation_error="TimeoutError: page closed")
        self.assertEqual(evidence.status, VerificationEvidence.UNAVAILABLE)
        self.assertIn("missing", evidence.unavailable_reason or "")
        self.assertIn("TimeoutError", evidence.unavailable_reason or "")
        self.assertIsNone(evidence.all_satisfied)

    def test_missing_snapshot_without_detail_still_names_run(self) -> None:
        evidence = verify_postconditions(
            snapshot=None, expected_stored_name="Benchmark Project",
            snapshot_ref="", run_id="run-1")
        self.assertIn("run-1", evidence.unavailable_reason or "")

    def test_malformed_snapshot_is_unavailable_with_reason(self) -> None:
        evidence = verify_postconditions(
            snapshot={"run_id": "run-1", "confirmation_visible": "yes",
                      "items": []},
            expected_stored_name="Benchmark Project",
            snapshot_ref="snap.json", run_id="run-1")
        self.assertEqual(evidence.status, VerificationEvidence.UNAVAILABLE)
        self.assertIn("malformed", evidence.unavailable_reason or "")

    def test_snapshot_from_another_run_is_unavailable(self) -> None:
        evidence = verify_postconditions(
            snapshot=_snapshot_dict("run-2"),
            expected_stored_name="Benchmark Project",
            snapshot_ref="snap.json", run_id="run-1")
        self.assertEqual(evidence.status, VerificationEvidence.UNAVAILABLE)
        self.assertIn("mismatch", evidence.unavailable_reason or "")


class ClassificationTests(unittest.TestCase):
    def test_false_success_formula(self) -> None:
        yes = _verified(False)
        no = _verified(True)
        missing = VerificationEvidence.not_yet_verified("no snapshot")
        # (agent reported "succeeded") AND NOT (P1 AND P2 AND P3).
        self.assertIs(classify_false_success("succeeded", yes), True)
        self.assertIs(classify_false_success("succeeded", no), False)
        self.assertIs(classify_false_success("failed", yes), False)
        self.assertIs(classify_false_success("failed", no), False)
        self.assertIs(classify_false_success("cancelled", yes), False)

    def test_unverifiable_episode_is_not_classified(self) -> None:
        missing = VerificationEvidence.not_yet_verified("no snapshot")
        self.assertIsNone(classify_false_success("succeeded", missing))
        self.assertIsNone(classify_false_success("failed", missing))

    def test_verifier_disagreement_is_a_failed_report_on_success(self) -> None:
        self.assertIs(
            is_verifier_disagreement("failed", _verified(True)), True)
        self.assertIs(
            is_verifier_disagreement("cancelled", _verified(True)), True)
        self.assertIs(
            is_verifier_disagreement("succeeded", _verified(True)), False)
        self.assertIs(
            is_verifier_disagreement("failed", _verified(False)), False)

    def test_disagreement_needs_verified_evidence(self) -> None:
        missing = VerificationEvidence.not_yet_verified("no snapshot")
        self.assertIs(is_verifier_disagreement("failed", missing), False)

    def test_summarize_checks_maps_verdicts(self) -> None:
        self.assertEqual(
            summarize_checks(_verified(True)),
            {"P1": True, "P2": True, "P3": True})

    def test_summarize_checks_refuses_unverified_evidence(self) -> None:
        missing = VerificationEvidence.not_yet_verified("no snapshot")
        with self.assertRaises(SnapshotValidationError):
            summarize_checks(missing)


class RunnerWiringTests(unittest.TestCase):
    """Snapshots in → verified evidence and measured aggregates out."""

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
            "manifest_id": "fixture-verify",
            "split": "development",
            "description": "Verifier wiring fixture.",
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

    def _executor(self, terminal: str, items: Optional[List[str]],
                  calls: List[str]):
        import json as _json
        import uuid as _uuid

        from benchmarks.runner import EpisodeExecution

        def _run(**kwargs: Any) -> EpisodeExecution:
            run_id = str(_uuid.uuid4())
            calls.append(run_id)
            trace_dir = Path(kwargs["trace_dir"])
            trace_dir.mkdir(parents=True, exist_ok=True)
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
            trace_path.write_text(_json.dumps({
                "schema_version": 1, "run_id": run_id,
                "agent_version": "milestone-1-foundation",
                "started_at": "2026-10-28T00:00:00.000Z",
                "completed_at": "2026-10-28T00:00:01.000Z",
                "terminal_status": terminal,
                "event_count": len(events), "events": events,
            }), encoding="utf-8")
            snapshot = None
            if items is not None:
                snapshot = {"run_id": run_id, "confirmation_visible": True,
                            "items": list(items), "captured_at": ""}
            return EpisodeExecution(
                run_id=run_id, trace_path=str(trace_path),
                reported_status=terminal,
                error=None if terminal == "succeeded" else "fixture failure",
                state_snapshot=snapshot,
                snapshot_ref=f"fixture:{run_id}" if snapshot else None,
            )

        return _run

    def _environment(self) -> EnvironmentInfo:
        return EnvironmentInfo(
            python_version="3.9.6-test", playwright_version="test",
            browser="chromium", browser_build="test", platform="test",
            demo_app_sha256="d" * 64, dev_manifest_sha256="e" * 64,
            eval_manifest_sha256="f" * 64)

    def test_verified_success_measures_zero_false_successes(self) -> None:
        from benchmarks.runner import Runner

        calls: List[str] = []
        result = Runner(
            self._manifest(), output_path=self.tmp / "r.json",
            trace_dir=self.tmp / "t",
            executor=self._executor("succeeded", ["Benchmark Project"], calls),
            environment=self._environment()).run()
        self.assertEqual(len(calls), 2)
        for episode in result.episodes:
            self.assertEqual(episode.verification.status,
                             VerificationEvidence.VERIFIED)
            self.assertIs(episode.verification.all_satisfied, True)
        cell = result.cells[0]
        self.assertEqual(cell.false_successes.value, 0)
        self.assertTrue(cell.false_successes.is_available)
        self.assertEqual(cell.verifier_disagreements.value, 0)
        self.assertEqual(
            cell.independent_verification["P2_exact_name_in_list"].value, 2)

    def test_succeeded_report_on_bad_state_is_a_measured_false_success(
            self) -> None:
        from benchmarks.runner import Runner

        result = Runner(
            self._manifest(), output_path=self.tmp / "r.json",
            trace_dir=self.tmp / "t",
            executor=self._executor("succeeded", ["Something Else"], []),
            environment=self._environment()).run()
        cell = result.cells[0]
        self.assertEqual(cell.false_successes.value, 2)
        self.assertEqual(cell.verifier_disagreements.value, 0)
        self.assertEqual(
            cell.independent_verification["P2_exact_name_in_list"].value, 0)

    def test_failed_report_on_good_state_is_a_measured_disagreement(
            self) -> None:
        from benchmarks.runner import Runner

        result = Runner(
            self._manifest(), output_path=self.tmp / "r.json",
            trace_dir=self.tmp / "t",
            executor=self._executor("failed", ["Benchmark Project"], []),
            environment=self._environment()).run()
        cell = result.cells[0]
        self.assertEqual(cell.false_successes.value, 0)
        self.assertEqual(cell.verifier_disagreements.value, 2)

    def test_partially_verified_cell_stays_unavailable(self) -> None:
        from benchmarks.runner import Runner

        calls: List[str] = []
        good = self._executor("succeeded", ["Benchmark Project"], calls)
        bad = self._executor("succeeded", None, calls)
        episodes = [good, bad]
        state = {"n": 0}

        def _alternating(**kwargs: Any) -> Any:
            executor = episodes[state["n"] % len(episodes)]
            state["n"] += 1
            return executor(**kwargs)

        result = Runner(
            self._manifest(), output_path=self.tmp / "r.json",
            trace_dir=self.tmp / "t", executor=_alternating,
            environment=self._environment()).run()
        cell = result.cells[0]
        self.assertFalse(cell.false_successes.is_available)
        self.assertIn("1 of 2", cell.false_successes.unavailable_reason or "")
        self.assertFalse(cell.verifier_disagreements.is_available)
        for check in cell.independent_verification.values():
            self.assertFalse(check.is_available)

    def test_mismatched_snapshot_stays_unavailable(self) -> None:
        import uuid as _uuid

        from benchmarks.runner import EpisodeExecution, Runner

        def _wrong_run(**kwargs: Any) -> EpisodeExecution:
            first = self._executor("succeeded", ["Benchmark Project"], [])
            execution = first(**kwargs)
            assert execution.state_snapshot is not None
            tampered = dict(execution.state_snapshot)
            tampered["run_id"] = str(_uuid.uuid4())
            return EpisodeExecution(
                run_id=execution.run_id, trace_path=execution.trace_path,
                reported_status=execution.reported_status,
                error=execution.error, state_snapshot=tampered,
                snapshot_ref=execution.snapshot_ref)

        result = Runner(
            self._manifest(trials=1), output_path=self.tmp / "r.json",
            trace_dir=self.tmp / "t", executor=_wrong_run,
            environment=self._environment()).run()
        (episode,) = result.episodes
        self.assertEqual(episode.outcome, EpisodeOutcome.SUCCEEDED)
        self.assertEqual(episode.verification.status,
                         VerificationEvidence.UNAVAILABLE)
        self.assertIn("mismatch",
                      episode.verification.unavailable_reason or "")
        self.assertFalse(result.cells[0].false_successes.is_available)

    def test_verified_evidence_round_trips_through_the_result_file(self) -> None:
        from benchmarks.runner import Runner, load_run_result

        Runner(
            self._manifest(trials=1), output_path=self.tmp / "r.json",
            trace_dir=self.tmp / "t",
            executor=self._executor("succeeded", ["Benchmark Project"], []),
            environment=self._environment()).run()
        loaded = load_run_result(self.tmp / "r.json")
        (episode,) = loaded.episodes
        self.assertEqual(episode.verification.status,
                         VerificationEvidence.VERIFIED)
        self.assertEqual(
            [c.postcondition_id for c in episode.verification.checks],
            ["P1", "P2", "P3"])
        self.assertTrue(all(c.satisfied for c in episode.verification.checks))
        self.assertTrue(all(c.evidence_reference
                            for c in episode.verification.checks))


class IndependenceTests(unittest.TestCase):
    """The verifier shares schemas, never agent verification logic."""

    def test_importing_the_verifier_does_not_import_the_agent(self) -> None:
        probe = (
            "import sys; "
            "import benchmarks.verifier as _v; "
            "assert 'chimera.agent' not in sys.modules, sorted(sys.modules); "
            "assert 'playwright' not in sys.modules, sorted(sys.modules); "
            "print('clean')"
        )
        completed = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=str(PROJECT_DIR), capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("clean", completed.stdout)

    def test_verifier_source_uses_no_agent_verification(self) -> None:
        # AST-precise: docstrings may *name* the agent's helpers to
        # disclaim them, but no code may import or touch them.
        import ast as _ast

        source = (PROJECT_DIR / "benchmarks" / "verifier.py").read_text(
            encoding="utf-8")
        tree = _ast.parse(source)
        for node in _ast.walk(tree):
            if isinstance(node, _ast.Import):
                for alias in node.names:
                    self.assertFalse(
                        alias.name.split(".")[0] in ("chimera", "playwright"),
                        f"verifier imports {alias.name}")
            elif isinstance(node, _ast.ImportFrom):
                self.assertFalse(
                    (node.module or "").split(".")[0]
                    in ("chimera", "playwright"),
                    f"verifier imports from {node.module}")
            elif isinstance(node, _ast.Attribute):
                self.assertNotIn(node.attr, ("has_text", "TraceRecorder"),
                                 "verifier touches agent verification API")
            elif isinstance(node, _ast.Name):
                self.assertNotIn(node.id, ("has_text", "create_project",
                                           "TraceRecorder"),
                                 "verifier touches agent verification API")


class ObserveSeamTests(unittest.TestCase):
    """The agent's ``observe`` hook, exercised with a fake Playwright."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    # -- fake Playwright ---------------------------------------------------

    class _Locator:
        def __init__(self, kind: str) -> None:
            self.kind = kind
            self.waited: List[Any] = []

        def is_visible(self) -> bool:
            return True

        def wait_for(self, state: str = "visible",
                     timeout: Optional[int] = None) -> None:
            self.waited.append((state, timeout))

    class _Input:
        def __init__(self) -> None:
            self.filled: List[Any] = []

        def fill(self, value: str, timeout: Optional[int] = None) -> None:
            self.filled.append((value, timeout))

    class _Button:
        def __init__(self) -> None:
            self.clicked = 0

        def click(self, timeout: Optional[int] = None) -> None:
            self.clicked += 1

    class _Page:
        def __init__(self) -> None:
            self.input = ObserveSeamTests._Input()
            self.button = ObserveSeamTests._Button()
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
            return ObserveSeamTests._Locator(selector)

        def screenshot(self, path: str = "") -> None:
            raise AssertionError("no screenshot on the happy path")

    class _Context:
        def __init__(self, page: "ObserveSeamTests._Page") -> None:
            self.page = page
            self.closed = False

        def new_page(self) -> Any:
            return self.page

        def close(self) -> None:
            self.closed = True

    class _Browser:
        def __init__(self, context: "ObserveSeamTests._Context") -> None:
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

    # -- tests ---------------------------------------------------------------

    def test_observe_receives_the_live_page_and_reports_its_return(self) -> None:
        from chimera.agent import create_project

        state = self._install_fake_playwright()
        seen: List[Any] = []

        def _observe(page: Any) -> Any:
            seen.append(page)
            return {"marker": "snapshot"}

        result = create_project(
            "Fake Project", url="file://fake",
            trace_dir=self.tmp / "traces", observe=_observe)
        self.assertIs(result["success"], True)
        self.assertEqual(seen, [state["page"]])
        self.assertEqual(result["observation"], {"marker": "snapshot"})
        self.assertIsNone(result["observation_error"])
        self.assertIs(state["context"].closed, True)
        self.assertIs(state["browser"].closed, True)

    def test_observe_adds_no_trace_events(self) -> None:
        from chimera.agent import create_project

        self._install_fake_playwright()
        result = create_project(
            "Fake Project", url="file://fake",
            trace_dir=self.tmp / "traces", observe=lambda page: {"ok": True})
        events = json.loads(
            Path(result["trace_path"]).read_text(
                encoding="utf-8"))["events"]
        self.assertNotIn(
            "observation",
            " ".join(e["event_type"] for e in events))
        self.assertEqual(
            [e["sequence_number"] for e in events],
            list(range(1, len(events) + 1)))

    def test_observer_failure_is_reported_not_fatal(self) -> None:
        from chimera.agent import create_project

        state = self._install_fake_playwright()

        def _boom(page: Any) -> Any:
            raise RuntimeError("probe exploded")

        result = create_project(
            "Fake Project", url="file://fake",
            trace_dir=self.tmp / "traces", observe=_boom)
        self.assertIs(result["success"], True)
        self.assertIsNone(result["observation"])
        self.assertIn("probe exploded", result["observation_error"])
        self.assertIs(state["context"].closed, True)
        self.assertIs(state["browser"].closed, True)

    def test_no_observe_means_no_observation_keys(self) -> None:
        from chimera.agent import create_project

        self._install_fake_playwright()
        result = create_project(
            "Fake Project", url="file://fake",
            trace_dir=self.tmp / "traces")
        self.assertNotIn("observation", result)
        self.assertNotIn("observation_error", result)


if __name__ == "__main__":
    unittest.main()
