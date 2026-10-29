"""Tests for the guided human-audit review tool.

Covers: verdict recording with strict JSON booleans, the verifier's
checks staying hidden until the human judges, unauditable reasons,
input validation, skip/quit/resume progress, evidence files left
untouched, saved plans reloading through the real audit parser, and
tamper/missing-evidence warnings.

All sessions run against plan copies in a temporary directory with
scripted answers. These tests invent no human judgments for any real
audit: they assert the tool's *mechanics* only.
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from benchmarks.audit import HumanVerdict, load_plan
from tools.audit_review import ReviewSession, main


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ScriptedIO:
    """Canned answers in, captured lines out."""

    def __init__(self, answers: List[str]) -> None:
        self._answers = list(answers)
        self.lines: List[str] = []

    def ask(self, prompt: str) -> str:
        self.lines.append(prompt)
        if not self._answers:
            raise AssertionError("scripted answers exhausted at: "
                                 + prompt)
        return self._answers.pop(0)

    def show(self, *parts: Any) -> None:
        self.lines.append(" ".join(str(p) for p in parts))

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


class ReviewFixtureBase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def _bundle(self, trial_id: str,
                confirmation: bool = True,
                items: Any = None,
                verifier: Any = None) -> Dict[str, Any]:
        items = ["Benchmark Project"] if items is None else items
        verifier = {"P1": True, "P2": True, "P3": True} \
            if verifier is None else verifier
        trace_path = self.tmp / f"{trial_id}.json"
        trace_path.write_text(json.dumps(
            {"terminal_status": "succeeded", "event_count": 6}),
            encoding="utf-8")
        snap_path = self.tmp / f"{trial_id}.snapshot.json"
        snap_path.write_text(json.dumps(
            {"confirmation_visible": confirmation, "items": items}),
            encoding="utf-8")
        actions_path = self.tmp / f"{trial_id}.actions.json"
        actions_path.write_text(json.dumps({"records": []}),
                                encoding="utf-8")
        return {
            "trial_id": trial_id,
            "run_id": f"run-{trial_id}",
            "manifest_id": "dev-v1",
            "scenario_id": "S-NORM",
            "input_id": "I-PLAIN",
            "baseline": "chimera",
            "expected_stored_name": "Benchmark Project",
            "agent_terminal_status": "succeeded",
            "outcome": "succeeded",
            "trace_path": str(trace_path),
            "snapshot_path": str(snap_path),
            "actions_path": str(actions_path),
            "verifier_checks": dict(verifier),
            "digests": {"trace": _sha256(trace_path),
                        "snapshot": _sha256(snap_path),
                        "actions": _sha256(actions_path)},
        }

    def _write_plan(self, name: str,
                    bundles: List[Dict[str, Any]]) -> Path:
        plan = {
            "schema": "chimera-audit-plan/1",
            "run_id": "run-1",
            "manifest_id": "dev-v1",
            "manifest_sha256": "abc",
            "sample_size": len(bundles),
            "auditor": "",
            "created_at": "",
            "cells": {
                "S-NORM|I-PLAIN|chimera": {
                    "scenario_id": "S-NORM",
                    "input_id": "I-PLAIN",
                    "baseline": "chimera",
                    "seed": "seed-1",
                    "sampled": bundles,
                    "skipped": [],
                    "verdicts": {},
                }
            },
        }
        path = self.tmp / name
        path.write_text(json.dumps(plan, sort_keys=True,
                                   ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        return path

    def _run_session(self, plan: Path, answers: List[str],
                     redo: bool = False) -> ScriptedIO:
        io = ScriptedIO(answers)
        session = ReviewSession([plan], input_fn=io.ask,
                                print_fn=io.show)
        session.run(redo=redo)
        return io


class VerdictRecordingTests(ReviewFixtureBase):
    def test_checks_saved_with_strict_booleans(self) -> None:
        plan = self._write_plan("p.json", [self._bundle("trial-0001")])
        self._run_session(plan, ["y", "n", "y", ""])
        verdicts = json.loads(plan.read_text(encoding="utf-8"))[
            "cells"]["S-NORM|I-PLAIN|chimera"]["verdicts"]
        self.assertEqual(verdicts, {
            "trial-0001": {"checks": {"P1": True, "P2": False,
                                      "P3": True}}})
        for value in verdicts["trial-0001"]["checks"].values():
            self.assertIs(type(value), bool)

    def test_only_verdicts_change_in_the_file(self) -> None:
        plan = self._write_plan("p.json", [self._bundle("trial-0001")])
        before = json.loads(plan.read_text(encoding="utf-8"))
        self._run_session(plan, ["n", "n", "n", ""])
        after = json.loads(plan.read_text(encoding="utf-8"))
        after["cells"]["S-NORM|I-PLAIN|chimera"]["verdicts"] = {}
        self.assertEqual(after, before)

    def test_note_recorded_when_given(self) -> None:
        plan = self._write_plan("p.json", [self._bundle("trial-0001")])
        self._run_session(plan, ["y", "y", "y", "clear snapshot"])
        verdicts = json.loads(plan.read_text(encoding="utf-8"))[
            "cells"]["S-NORM|I-PLAIN|chimera"]["verdicts"]
        self.assertEqual(verdicts["trial-0001"]["note"], "clear snapshot")

    def test_saved_verdicts_parse_as_human_verdicts(self) -> None:
        plan = self._write_plan("p.json", [self._bundle("trial-0001")])
        self._run_session(plan, ["y", "y", "n", ""])
        loaded = load_plan(plan)
        verdict = loaded.cells["S-NORM|I-PLAIN|chimera"].verdicts[
            "trial-0001"]
        self.assertIsInstance(verdict, HumanVerdict)
        assert isinstance(verdict, HumanVerdict)
        self.assertEqual(dict(verdict.checks),
                         {"P1": True, "P2": True, "P3": False})


class BlindReviewTests(ReviewFixtureBase):
    def test_verifier_checks_hidden_until_recorded(self) -> None:
        bundle = self._bundle("trial-0001",
                              verifier={"P1": False, "P2": False,
                                        "P3": True})
        plan = self._write_plan("p.json", [bundle])
        io = self._run_session(plan, ["y", "y", "y", ""])
        receipt = "The verifier's checks were"
        self.assertIn(receipt, io.text)
        before = io.text.split(receipt)[0]
        self.assertNotIn("verifier_checks", before)
        self.assertNotIn("'P1': False", before)
        self.assertIn("{'P1': False, 'P2': False, 'P3': True}",
                      io.text.split(receipt)[1])

    def test_evidence_shown_for_each_check(self) -> None:
        bundle = self._bundle("trial-0001", confirmation=True,
                              items=["Benchmark Project"])
        plan = self._write_plan("p.json", [bundle])
        io = self._run_session(plan, ["y", "y", "y", ""])
        for expected in ("Benchmark Project",
                         str(Path(bundle["snapshot_path"])),
                         str(Path(bundle["trace_path"])),
                         "confirmation_visible: True",
                         "P1: Is confirmation_visible true",
                         "P2: Does items contain exactly one entry",
                         "P3: Does items contain exactly one entry?"):
            self.assertIn(expected, io.text)


class InputValidationTests(ReviewFixtureBase):
    def test_invalid_answers_reprompt_without_recording(self) -> None:
        plan = self._write_plan("p.json", [self._bundle("trial-0001")])
        io = self._run_session(plan, ["maybe", "y", "n", "n", ""])
        self.assertIn("Please answer y or n", io.text)
        verdicts = json.loads(plan.read_text(encoding="utf-8"))[
            "cells"]["S-NORM|I-PLAIN|chimera"]["verdicts"]
        self.assertEqual(verdicts["trial-0001"]["checks"],
                         {"P1": True, "P2": False, "P3": False})

    def test_unauditable_requires_a_reason(self) -> None:
        plan = self._write_plan("p.json", [self._bundle("trial-0001")])
        io = self._run_session(plan, ["u", "   ", "snapshot is empty"])
        self.assertIn("A reason is required", io.text)
        verdicts = json.loads(plan.read_text(encoding="utf-8"))[
            "cells"]["S-NORM|I-PLAIN|chimera"]["verdicts"]
        self.assertEqual(verdicts["trial-0001"],
                         {"verdict": "unauditable",
                          "reason": "snapshot is empty"})


class ProgressTests(ReviewFixtureBase):
    def test_quit_saves_and_resume_skips_recorded(self) -> None:
        plan = self._write_plan("p.json", [self._bundle("trial-0001"),
                                           self._bundle("trial-0002")])
        first = self._run_session(plan, ["y", "y", "y", "", "q"])
        self.assertIn("Progress saved: 1/2", first.text)
        verdicts = json.loads(plan.read_text(encoding="utf-8"))[
            "cells"]["S-NORM|I-PLAIN|chimera"]["verdicts"]
        self.assertEqual(sorted(verdicts), ["trial-0001"])
        second = self._run_session(plan, ["n", "n", "n", ""])
        self.assertIn("1 already have verdicts", second.text)
        self.assertIn("Done: 2/2", second.text)
        verdicts = json.loads(plan.read_text(encoding="utf-8"))[
            "cells"]["S-NORM|I-PLAIN|chimera"]["verdicts"]
        self.assertEqual(sorted(verdicts), ["trial-0001", "trial-0002"])

    def test_skip_revisits_the_episode_later(self) -> None:
        plan = self._write_plan("p.json", [self._bundle("trial-0001"),
                                           self._bundle("trial-0002")])
        self._run_session(plan, ["s",
                                 "y", "y", "y", "",
                                 "n", "n", "n", ""])
        verdicts = json.loads(plan.read_text(encoding="utf-8"))[
            "cells"]["S-NORM|I-PLAIN|chimera"]["verdicts"]
        self.assertEqual(verdicts["trial-0001"]["checks"],
                         {"P1": False, "P2": False, "P3": False})
        self.assertEqual(verdicts["trial-0002"]["checks"],
                         {"P1": True, "P2": True, "P3": True})


class TargetedPlanTests(ReviewFixtureBase):
    def test_untargeted_cells_contribute_no_episodes(self) -> None:
        plan = self._write_plan("p.json", [self._bundle("trial-0001")])
        data = json.loads(plan.read_text(encoding="utf-8"))
        data["cells"]["S-SLOW|I-PLAIN|chimera|disabled=False,slow_ms=800"] = {
            "scenario_id": "S-SLOW", "input_id": "I-PLAIN",
            "baseline": "chimera", "seed": "seed-2",
            "sampled": [], "skipped": [], "verdicts": {},
        }
        plan.write_text(json.dumps(data), encoding="utf-8")
        io = self._run_session(plan, ["y", "y", "y", ""])
        self.assertIn("1 sampled episode(s)", io.text)
        self.assertIn("Done: 1/1", io.text)


class EvidenceSafetyTests(ReviewFixtureBase):
    def test_evidence_bytes_untouched_by_a_session(self) -> None:
        bundle = self._bundle("trial-0001")
        plan = self._write_plan("p.json", [bundle])
        paths = [Path(bundle["trace_path"]),
                 Path(bundle["snapshot_path"]),
                 Path(bundle["actions_path"])]
        before = {p: p.read_bytes() for p in paths}
        self._run_session(plan, ["y", "y", "y", ""])
        for path in paths:
            self.assertEqual(path.read_bytes(), before[path])

    def test_changed_evidence_warns(self) -> None:
        bundle = self._bundle("trial-0001")
        bundle["digests"]["snapshot"] = "0" * 64
        plan = self._write_plan("p.json", [bundle])
        io = self._run_session(plan, ["y", "y", "y", ""])
        self.assertIn("CHANGED since planning", io.text)

    def test_missing_evidence_warns(self) -> None:
        bundle = self._bundle("trial-0001")
        bundle["snapshot_path"] = str(self.tmp / "absent.snapshot.json")
        plan = self._write_plan("p.json", [bundle])
        io = self._run_session(plan, ["u", "no snapshot file"])
        self.assertIn("MISSING", io.text)
        verdicts = json.loads(plan.read_text(encoding="utf-8"))[
            "cells"]["S-NORM|I-PLAIN|chimera"]["verdicts"]
        self.assertEqual(verdicts["trial-0001"]["verdict"], "unauditable")


class EntrypointTests(unittest.TestCase):
    def test_help_and_missing_plan(self) -> None:
        self.assertEqual(main(["--help"]), 0)
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                main([str(Path(tmp) / "absent.audit-plan.json")]), 1)


if __name__ == "__main__":
    unittest.main()
