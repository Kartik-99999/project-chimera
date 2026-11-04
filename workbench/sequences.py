"""Ordered multi-workflow sequences: N tasks, one strict order.

A sequence chains different registered workflows — e.g. look up a
Wikipedia article, then search arXiv, then file the outcome as a
project — running each step to a terminal verdict before the next
begins. Every step is a real execution with independent
verification; nothing is simulated.

Unlike campaigns (one workflow x drivers x conditions), a sequence
holds one ordered step list. By default the first step that fails
to reach ``verified-success`` halts the chain (``stop_on_failure``);
the remaining steps never start. Pause/resume/cancel persist in
the database, so a new runner on the same database can resume an
interrupted sequence.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Dict, List, Mapping, Optional

from workbench.campaigns import TERMINAL_STATUSES, collect_versions
from workbench.store import Store, utcnow
from workbench.workflows import WorkflowValidationError, get_workflow

STEP_KIND = "sequence"

#: Hard ceiling on steps per sequence (protects public sites).
MAX_STEPS = 100


class SequenceError(WorkflowValidationError):
    """Sequence spec or transition invalid."""


def validate_spec(raw: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate a sequence spec; return the cleaned spec."""
    if not isinstance(raw, Mapping):
        raise SequenceError("sequence spec must be an object")
    name = raw.get("name")
    if not isinstance(name, str) or not name.strip():
        raise SequenceError("sequence name is required")
    if len(name.strip()) > 120:
        raise SequenceError("sequence name must be at most 120 characters")
    steps = raw.get("steps")
    if not isinstance(steps, list) or not steps:
        raise SequenceError("at least one step is required")
    if len(steps) > MAX_STEPS:
        raise SequenceError(
            f"{len(steps)} steps exceeds the {MAX_STEPS}-step ceiling")
    cleaned_steps = []
    for index, step in enumerate(steps):
        if not isinstance(step, Mapping):
            raise SequenceError(f"step {index + 1} must be an object")
        try:
            workflow = get_workflow(step.get("workflow_id", ""))
        except WorkflowValidationError as exc:
            raise SequenceError(f"step {index + 1}: {exc}") from None
        driver = step.get("driver", "chimera")
        if driver not in workflow.drivers:
            raise SequenceError(
                f"step {index + 1}: driver {driver!r} is not supported "
                f"for {workflow.workflow_id!r}")
        label = step.get("label") or f"step {index + 1}"
        if not isinstance(label, str) or not label.strip():
            raise SequenceError(f"step {index + 1} needs a label")
        params = step.get("params") or {}
        if not isinstance(params, Mapping):
            raise SequenceError(
                f"step {index + 1} params must be an object")
        try:
            cleaned = workflow.validate(params)
        except WorkflowValidationError as exc:
            raise SequenceError(f"step {index + 1}: {exc}") from None
        cleaned_steps.append({
            "label": label.strip(),
            "workflow_id": workflow.workflow_id,
            "driver": driver,
            "params": cleaned,
        })
    pacing_ms = raw.get("pacing_ms", 2000)
    if (isinstance(pacing_ms, bool) or not isinstance(pacing_ms, int)
            or not 0 <= pacing_ms <= 120000):
        raise SequenceError("pacing_ms must be 0..120000")
    stop_on_failure = raw.get("stop_on_failure", True)
    if not isinstance(stop_on_failure, bool):
        raise SequenceError("stop_on_failure must be true or false")
    return {
        "name": name.strip(),
        "steps": cleaned_steps,
        "pacing_ms": pacing_ms,
        "stop_on_failure": stop_on_failure,
        "total_steps": len(cleaned_steps),
    }


def build_steps(spec: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Steps in run order with 1-based sequence numbers."""
    ordered = []
    for seq, step in enumerate(spec["steps"], start=1):
        ordered.append({
            "step_seq": seq,
            "label": step["label"],
            "workflow_id": step["workflow_id"],
            "driver": step["driver"],
            "params": step["params"],
        })
    return ordered


def _step_succeeded(record: Mapping[str, Any]) -> bool:
    return (record.get("status") == "succeeded"
            and record.get("verdict") == "verified-success")


class SequenceRunner:
    """Owns sequence worker threads; state lives in the database."""

    def __init__(self, store: Store, executor: Any,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        self._store = store
        self._executor = executor
        self._sleep = sleep
        self._lock = threading.Lock()
        self._threads: Dict[str, threading.Thread] = {}

    # -- lifecycle --------------------------------------------------------

    def create(self, raw_spec: Mapping[str, Any]) -> str:
        import json

        spec = validate_spec(raw_spec)
        return self._store.create_sequence({
            "name": spec["name"],
            "spec_json": json.dumps(spec),
            "versions_json": json.dumps(collect_versions()),
            "status": "draft",
            "total_steps": spec["total_steps"],
        })

    def start(self, sequence_id: str) -> Dict[str, Any]:
        with self._lock:
            sequence = self._require(sequence_id)
            if sequence["status"] not in ("draft", "paused"):
                raise SequenceError(
                    f"sequence is {sequence['status']}; only draft or "
                    f"paused sequences can start")
            for other in self._store.list_sequences():
                if (other["id"] != sequence_id
                        and other["status"] == "running"):
                    raise SequenceError(
                        "another sequence is already running; "
                        "concurrency is limited to one browser")
            for other in self._store.list_campaigns():
                if other["status"] == "running":
                    raise SequenceError(
                        "a campaign is already running; "
                        "concurrency is limited to one browser")
            if sequence_id in self._threads and self._threads[
                    sequence_id].is_alive():
                raise SequenceError("sequence worker already running")
            fields: Dict[str, Any] = {"status": "running",
                                      "stop_reason": None, "error": None}
            if not sequence.get("started_at"):
                fields["started_at"] = utcnow()
            self._store.update_sequence(sequence_id, fields)
            thread = threading.Thread(
                target=self._run_sequence, args=(sequence_id,),
                name=f"sequence-{sequence_id[:8]}", daemon=True)
            self._threads[sequence_id] = thread
            thread.start()
            result = self._store.get_sequence(sequence_id)
            assert result is not None
            return result

    def pause(self, sequence_id: str) -> Dict[str, Any]:
        with self._lock:
            sequence = self._require(sequence_id)
            if sequence["status"] != "running":
                raise SequenceError(
                    f"sequence is {sequence['status']}; only a running "
                    f"sequence can pause")
            self._store.update_sequence(
                sequence_id, {"status": "paused",
                              "stop_reason": "paused by user"})
            result = self._store.get_sequence(sequence_id)
            assert result is not None
            return result

    def resume(self, sequence_id: str) -> Dict[str, Any]:
        with self._lock:
            sequence = self._require(sequence_id)
            if sequence["status"] != "paused":
                raise SequenceError(
                    f"sequence is {sequence['status']}; only a paused "
                    f"sequence can resume")
        return self.start(sequence_id)

    def cancel(self, sequence_id: str) -> Dict[str, Any]:
        with self._lock:
            sequence = self._require(sequence_id)
            if sequence["status"] not in ("running", "paused", "draft"):
                raise SequenceError(
                    f"sequence is {sequence['status']}; nothing to cancel")
            current = sequence.get("current_exec_id")
            self._store.update_sequence(
                sequence_id, {"status": "cancelled",
                              "completed_at": utcnow(),
                              "current_exec_id": None,
                              "stop_reason": "cancelled by user"})
        if current:
            try:
                self._executor.cancel(current)
            except Exception:  # noqa: BLE001 — cancel best-effort
                pass
        result = self._store.get_sequence(sequence_id)
        assert result is not None
        return result

    def recover(self) -> int:
        """Pause sequences left 'running' by an unclean shutdown."""
        count = 0
        with self._lock:
            for sequence in self._store.list_sequences():
                if sequence["status"] != "running":
                    continue
                thread = self._threads.get(sequence["id"])
                if thread is not None and thread.is_alive():
                    continue
                self._store.update_sequence(sequence["id"], {
                    "status": "paused",
                    "current_exec_id": None,
                    "stop_reason": "runner restarted; resume to continue",
                })
                count += 1
        return count

    def running(self) -> List[str]:
        with self._lock:
            return [sid for sid, thread in self._threads.items()
                    if thread.is_alive()]

    def _require(self, sequence_id: str) -> Dict[str, Any]:
        sequence = self._store.get_sequence(sequence_id)
        if sequence is None:
            raise SequenceError(f"unknown sequence {sequence_id!r}")
        return sequence

    # -- worker -----------------------------------------------------------

    def _run_sequence(self, sequence_id: str) -> None:
        try:
            sequence = self._store.get_sequence(sequence_id)
            assert sequence is not None
            spec = sequence["spec"]
            if not isinstance(spec, dict):
                raise SequenceError("sequence spec unreadable")
            steps = build_steps(spec)
            pacing = float(spec.get("pacing_ms", 0)) / 1000.0
            stop_on_failure = bool(spec.get("stop_on_failure", True))
            while True:
                live = self._store.get_sequence(sequence_id)
                assert live is not None
                if live["status"] != "running":
                    return
                finished = int(live.get("finished_steps", 0) or 0)
                if finished >= len(steps):
                    self._store.update_sequence(sequence_id, {
                        "status": "completed",
                        "completed_at": utcnow(),
                        "current_exec_id": None})
                    return
                if finished > 0 and pacing > 0:
                    if not self._paced_wait(sequence_id, pacing):
                        return
                    live = self._store.get_sequence(sequence_id)
                    assert live is not None
                    if live["status"] != "running":
                        return
                    finished = int(live.get("finished_steps", 0) or 0)
                step = steps[finished]
                try:
                    exec_id = self._executor.submit(
                        step["workflow_id"], step["driver"],
                        step["params"], sequence_id=sequence_id,
                        step_seq=step["step_seq"],
                        trial_kind=STEP_KIND)
                except Exception as exc:  # noqa: BLE001 — spec-level fault
                    self._store.update_sequence(sequence_id, {
                        "status": "failed",
                        "completed_at": utcnow(),
                        "current_exec_id": None,
                        "error": f"step submit failed: {exc}"})
                    return
                self._store.update_sequence(
                    sequence_id, {"current_exec_id": exec_id})
                record = self._wait_terminal(exec_id)
                self._store.update_sequence(sequence_id, {
                    "finished_steps": finished + 1,
                    "current_exec_id": None,
                })
                if stop_on_failure and not _step_succeeded(record or {}):
                    status = (record or {}).get("status", "error")
                    verdict = (record or {}).get("verdict", "pending")
                    self._store.update_sequence(sequence_id, {
                        "status": "failed",
                        "completed_at": utcnow(),
                        "stop_reason": (
                            f"step {step['step_seq']} "
                            f"({step['label']}) ended "
                            f"{status}/{verdict}; chain halted"),
                    })
                    return
        except Exception as exc:  # noqa: BLE001 — worker must not die silent
            try:
                self._store.update_sequence(sequence_id, {
                    "status": "failed",
                    "completed_at": utcnow(),
                    "current_exec_id": None,
                    "error": f"sequence worker failed: {exc}"})
            except Exception:  # noqa: BLE001
                pass
        finally:
            with self._lock:
                self._threads.pop(sequence_id, None)

    def _paced_wait(self, sequence_id: str, seconds: float) -> bool:
        """Sleep between steps; False when no longer running."""
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            sequence = self._store.get_sequence(sequence_id)
            if sequence is None or sequence["status"] != "running":
                return False
            self._sleep(min(0.2, max(0.0, deadline - time.monotonic())))
        sequence = self._store.get_sequence(sequence_id)
        return sequence is not None and sequence["status"] == "running"

    def _wait_terminal(self, exec_id: str,
                       timeout: float = 1800.0) -> Optional[Dict[str, Any]]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            record = self._store.get_execution(exec_id)
            if record is not None and record["status"] in TERMINAL_STATUSES:
                return record
            self._sleep(0.5)
        return self._store.get_execution(exec_id)
