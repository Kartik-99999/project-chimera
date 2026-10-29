"""Stdlib-only tests for :mod:`chimera.tracing`.

These tests verify the trace schema, event ordering, required fields,
persistence to disk, and FR-034's guarantee that a trace-write failure
cannot turn an unverified action into a reported success. No browser
or playwright is required.

Run with::

    python -m unittest tests.test_tracing -v
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from chimera.tracing import (
    AGENT_VERSION,
    TRACE_SCHEMA_VERSION,
    TraceRecorder,
    TraceWriteError,
)


class TraceSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmpdir = Path(self._tmp.name)
        self.rec = TraceRecorder(trace_dir=self.tmpdir)

    def _finish_succeeded(self) -> Path:
        return self.rec.finish("succeeded")

    def test_run_id_is_uuid4_string(self) -> None:
        import uuid

        # Should parse as a UUID.
        uuid.UUID(self.rec.run_id)
        # And the version should be 4.
        self.assertEqual(uuid.UUID(self.rec.run_id).version, 4)

    def test_start_event_recorded_on_first_record(self) -> None:
        self.rec.record("run_started")
        self.assertEqual(self.rec.events[0]["event_type"], "run_started")
        self.assertEqual(self.rec.events[0]["sequence_number"], 1)

    def test_required_event_fields_present(self) -> None:
        self.rec.record("run_started", action_type="navigate")
        ev = self.rec.events[0]
        for key in (
            "sequence_number",
            "event_type",
            "timestamp",
            "action_type",
            "action_outcome",
            "error_details",
            "evidence_references",
        ):
            self.assertIn(key, ev, f"missing key: {key}")

    def test_timestamps_are_utc_iso_with_z_suffix(self) -> None:
        self.rec.record("run_started")
        ts = self.rec.events[0]["timestamp"]
        self.assertTrue(ts.endswith("Z"), f"timestamp not UTC-Z: {ts!r}")
        # Must contain a T separator and at least millisecond precision.
        self.assertIn("T", ts)
        self.assertRegex(ts, r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z")

    def test_sequence_numbers_are_monotonic_and_one_indexed(self) -> None:
        for i in range(5):
            self.rec.record(f"evt_{i}")
        seqs = [e["sequence_number"] for e in self.rec.events]
        self.assertEqual(seqs, [1, 2, 3, 4, 5])

    def test_terminal_event_uses_run_succeeded_type(self) -> None:
        self._finish_succeeded()
        self.assertEqual(self.rec.events[-1]["event_type"], "run_succeeded")
        self.assertEqual(self.rec.terminal_status, "succeeded")

    def test_terminal_event_uses_run_failed_type(self) -> None:
        self.rec.record("action_failed", action_type="click")
        self.rec.finish("failed", error_details={"type": "X", "message": "y"})
        self.assertEqual(self.rec.events[-1]["event_type"], "run_failed")
        self.assertEqual(self.rec.terminal_status, "failed")

    def test_terminal_event_uses_run_cancelled_type(self) -> None:
        # FR-021: cancellation is a third, distinct terminal status.
        self.rec.record("action_attempted", action_type="navigate")
        self.rec.finish(
            "cancelled",
            error_details={"type": "RunCancelledError", "message": "stop"},
        )
        last = self.rec.events[-1]
        self.assertEqual(last["event_type"], "run_cancelled")
        # The outcome on the terminal event must be "cancelled", not
        # "failure" — a separate signal so consumers can filter cleanly.
        self.assertEqual(last["action_outcome"], "cancelled")
        self.assertEqual(self.rec.terminal_status, "cancelled")
        # And the artifact's top-level terminal_status agrees.
        data = json.loads(self.rec.artifact_path.read_text(encoding="utf-8"))
        self.assertEqual(data["terminal_status"], "cancelled")

    def test_finish_is_idempotent(self) -> None:
        path = self._finish_succeeded()
        # A second finish() should not add a new terminal event.
        again = self.rec.finish("succeeded")
        self.assertEqual(path, again)
        # Exactly one terminal event present.
        terms = [e for e in self.rec.events if e["event_type"].startswith("run_")]
        self.assertEqual(len(terms), 1)


class TraceArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmpdir = Path(self._tmp.name)
        self.rec = TraceRecorder(trace_dir=self.tmpdir)
        self.rec.record("run_started")
        self.rec.action_attempted("navigate")
        self.rec.action_succeeded("navigate")
        self.rec.action_attempted("fill")
        self.rec.action_succeeded("fill")
        self.rec.action_attempted("click")
        self.rec.action_succeeded("click")
        self.rec.verification_passed("confirmation_message_visible")

    def test_finish_writes_json_artifact(self) -> None:
        path = self.rec.finish("succeeded")
        self.assertTrue(path.exists())
        self.assertEqual(path.suffix, ".json")
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], TRACE_SCHEMA_VERSION)
        self.assertEqual(data["agent_version"], AGENT_VERSION)
        self.assertEqual(data["run_id"], self.rec.run_id)
        self.assertEqual(data["terminal_status"], "succeeded")
        self.assertEqual(data["event_count"], len(self.rec.events))

    def test_artifact_contains_all_recorded_events(self) -> None:
        path = self.rec.finish("succeeded")
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(len(data["events"]), len(self.rec.events))
        for i, ev in enumerate(data["events"]):
            self.assertEqual(ev["sequence_number"], i + 1)

    def test_artifact_path_uses_run_id_filename(self) -> None:
        path = self.rec.finish("succeeded")
        self.assertEqual(path.name, f"{self.rec.run_id}.json")

    def test_artifact_write_is_atomic_no_tmp_left(self) -> None:
        path = self.rec.finish("succeeded")
        # No leftover .tmp file in the trace dir.
        leftovers = list(self.tmpdir.glob("*.tmp"))
        self.assertEqual(leftovers, [])

    def test_evidence_references_preserved(self) -> None:
        self.rec.record("custom", evidence=["file://a", "selector=#x"])
        path = self.rec.finish("succeeded")
        data = json.loads(path.read_text(encoding="utf-8"))
        custom = data["events"][-2]  # before terminal
        self.assertIn("file://a", custom["evidence_references"])
        self.assertIn("selector=#x", custom["evidence_references"])


class TraceWriteFailureTests(unittest.TestCase):
    """FR-034: a trace-write failure MUST NOT silently turn an
    unverified action into a reported success."""

    def test_finish_raises_trace_write_error_on_oserror(self) -> None:
        _tmp = tempfile.TemporaryDirectory()
        self.addCleanup(_tmp.cleanup)
        tmpdir = Path(_tmp.name)
        rec = TraceRecorder(trace_dir=tmpdir)
        rec.record("run_started")

        # Make the trace dir a regular file so mkdir(parent, exist_ok=True)
        # inside finish() will fail with NotADirectoryError (an OSError).
        blocker = tmpdir / "blocker"
        blocker.write_text("not a directory", encoding="utf-8")
        rec.trace_dir = blocker

        with self.assertRaises(TraceWriteError) as ctx:
            rec.finish("succeeded")
        self.assertIn("trace_write_failed", str(ctx.exception))
        self.assertIsNotNone(rec.write_error)

    def test_write_error_message_surfaces_cause(self) -> None:
        _tmp = tempfile.TemporaryDirectory()
        self.addCleanup(_tmp.cleanup)
        tmpdir = Path(_tmp.name)
        rec = TraceRecorder(trace_dir=tmpdir)
        rec.record("run_started")
        # Force a permission failure on the artifact file open. Patch
        # Path.open (the bound method used by the recorder) so that
        # Path.mkdir's internal existence check still works.
        real_open = Path.open
        def fake_open(self, *args, **kwargs):  # noqa: ANN001
            if self.name.endswith(".tmp"):
                raise PermissionError("denied")
            return real_open(self, *args, **kwargs)
        with mock.patch.object(Path, "open", fake_open):
            with self.assertRaises(TraceWriteError) as ctx:
                rec.finish("succeeded")
        # The original cause must be preserved on the raised TraceWriteError
        # so a caller can see exactly what filesystem operation failed.
        self.assertIsInstance(ctx.exception.__cause__, PermissionError)
        self.assertIn("denied", str(ctx.exception.__cause__))
        self.assertIsNotNone(rec.write_error)


class ActionHelperTests(unittest.TestCase):
    """The convenience helpers must populate the same event schema."""

    def setUp(self) -> None:
        _tmp = tempfile.TemporaryDirectory()
        self.addCleanup(_tmp.cleanup)
        self.tmpdir = Path(_tmp.name)
        self.rec = TraceRecorder(trace_dir=self.tmpdir)

    def test_action_attempted_emits_correct_event(self) -> None:
        self.rec.action_attempted("fill")
        ev = self.rec.events[-1]
        self.assertEqual(ev["event_type"], "action_attempted")
        self.assertEqual(ev["action_type"], "fill")
        self.assertEqual(ev["action_outcome"], "ok")

    def test_action_failed_includes_exception_details(self) -> None:
        try:
            raise RuntimeError("inner")
        except RuntimeError as exc:
            self.rec.action_failed("fill", exc)
        ev = self.rec.events[-1]
        self.assertEqual(ev["event_type"], "action_failed")
        self.assertEqual(ev["action_outcome"], "failure")
        self.assertEqual(ev["error_details"]["type"], "RuntimeError")
        self.assertEqual(ev["error_details"]["message"], "inner")

    def test_action_failed_preserves_cause_chain(self) -> None:
        try:
            try:
                raise ValueError("root cause")
            except ValueError as inner:
                raise RuntimeError("wrapper") from inner
        except RuntimeError as exc:
            self.rec.action_failed("click", exc)
        ev = self.rec.events[-1]
        self.assertEqual(ev["error_details"]["cause_type"], "ValueError")
        self.assertEqual(ev["error_details"]["cause_message"], "root cause")

    def test_verification_passed_carries_postcondition_evidence(self) -> None:
        self.rec.verification_passed("project_in_list")
        ev = self.rec.events[-1]
        self.assertEqual(ev["event_type"], "verification_passed")
        # The recorder schema exposes outcome via ``action_outcome``;
        # the postcondition itself is attached as an evidence reference.
        self.assertEqual(ev["action_outcome"], "ok")
        self.assertIn("project_in_list", ev["evidence_references"])


if __name__ == "__main__":
    unittest.main()
