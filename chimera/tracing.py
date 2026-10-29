"""Execution tracing for Project Chimera (FR-018).

A :class:`TraceRecorder` captures a chronological list of structured
events for a single run and persists them to a JSON artifact. The
artifact is the source of truth for what the agent observed, attempted,
and observed again — and is the only evidence that the verification
postconditions actually held.

Design constraints (from the SRS and this session's brief):

- Events are append-only and ordered by a monotonic
  ``sequence_number`` so they can be replayed deterministically.
- A trace-write failure MUST NOT silently turn an unverified browser
  action into a reported success (FR-034). If a write fails, the
  recorder exposes :attr:`write_error` and the caller must treat the
  run as failed.
- Screenshots are taken only when the caller supplies a
  ``screenshot`` callable and only on failure (NFR-019: avoid
  unnecessary captures). The path is recorded as evidence on the
  ``action_failed`` event; if the screenshot itself fails, the
  failure is recorded as ``screenshot_capture_failed`` so the
  evidence gap is visible.
- No external dependencies. Pure stdlib.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, List, Optional


TRACE_SCHEMA_VERSION = 1
AGENT_VERSION = "milestone-1-foundation"


def _now_utc_iso() -> str:
    """Return an RFC 3339 UTC timestamp with millisecond precision."""
    return (
        datetime.now(timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%S.")
        + f"{datetime.now(timezone.utc).microsecond // 1000:03d}Z"
    )


class TraceWriteError(RuntimeError):
    """Raised when the trace artifact cannot be persisted to disk."""


@dataclass
class TraceRecorder:
    """Capture events for one run, persist on :meth:`finish`.

    Parameters
    ----------
    trace_dir:
        Directory where ``<run_id>.json`` will be written. Created
        on :meth:`finish` if it does not exist.
    run_id:
        Optional pre-assigned run id. Defaults to a fresh UUID4.
    """

    trace_dir: Path
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    events: List[dict] = field(default_factory=list)
    started_at: str = field(default_factory=_now_utc_iso)
    completed_at: Optional[str] = None
    terminal_status: Optional[str] = None
    write_error: Optional[str] = None
    artifact_path: Optional[Path] = None
    _sequence: int = 0
    _finished: bool = False

    def record(
        self,
        event_type: str,
        *,
        action_type: Optional[str] = None,
        outcome: str = "ok",
        error_details: Optional[dict] = None,
        evidence: Optional[List[str]] = None,
    ) -> None:
        """Append one event to the trace. No-op after :meth:`finish`."""
        if self._finished:
            return
        self._sequence += 1
        event = {
            "sequence_number": self._sequence,
            "event_type": event_type,
            "timestamp": _now_utc_iso(),
            "action_type": action_type,
            "action_outcome": outcome,
            "error_details": error_details,
            "evidence_references": list(evidence) if evidence else [],
        }
        self.events.append(event)

    def finish(
        self,
        terminal_status: str,
        *,
        error_details: Optional[dict] = None,
    ) -> Path:
        """Persist the trace and return the artifact path.

        Always records a terminal event (``run_succeeded``,
        ``run_failed``, or ``run_cancelled``). The ``action_outcome`` on
        the terminal event is derived from the terminal status: ``"ok"``
        for ``succeeded``, ``"cancelled"`` for ``cancelled``, and
        ``"failure"`` for ``failed``. If writing the artifact fails,
        sets :attr:`write_error` and raises :class:`TraceWriteError`.
        The caller MUST treat the run as failed in that case (FR-034).
        """
        if self._finished:
            return self.artifact_path  # type: ignore[return-value]
        self.completed_at = _now_utc_iso()
        self.terminal_status = terminal_status
        if terminal_status == "succeeded":
            outcome = "ok"
        elif terminal_status == "cancelled":
            outcome = "cancelled"
        else:
            outcome = "failure"
        self.record(
            f"run_{terminal_status}",
            outcome=outcome,
            error_details=error_details,
        )

        artifact = {
            "schema_version": TRACE_SCHEMA_VERSION,
            "run_id": self.run_id,
            "agent_version": AGENT_VERSION,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "terminal_status": terminal_status,
            "event_count": len(self.events),
            "events": self.events,
        }

        path = self._artifact_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            # Write to a temp file in the same dir then atomically rename,
            # so a partial write never leaves a corrupted artifact.
            tmp = path.with_suffix(path.suffix + ".tmp")
            with tmp.open("w", encoding="utf-8") as fh:
                json.dump(artifact, fh, indent=2, sort_keys=True)
            tmp.replace(path)
        except OSError as exc:
            self.write_error = (
                f"trace_write_failed: {type(exc).__name__}: {exc}"
            )
            self._finished = True
            raise TraceWriteError(self.write_error) from exc

        self.artifact_path = path
        self._finished = True
        return path

    def _artifact_path(self) -> Path:
        return Path(self.trace_dir) / f"{self.run_id}.json"

    # --- Convenience helpers for the common cases. ---

    def action_attempted(self, action_type: str) -> None:
        self.record("action_attempted", action_type=action_type)

    def action_succeeded(self, action_type: str) -> None:
        self.record("action_succeeded", action_type=action_type)

    def action_failed(
        self,
        action_type: str,
        exc: BaseException,
    ) -> None:
        self.record(
            "action_failed",
            action_type=action_type,
            outcome="failure",
            error_details={
                "type": type(exc).__name__,
                "message": str(exc),
                "cause_type": (
                    type(exc.__cause__).__name__ if exc.__cause__ else None
                ),
                "cause_message": (
                    str(exc.__cause__) if exc.__cause__ else None
                ),
            },
        )

    def verification_passed(self, postcondition: str) -> None:
        self.record(
            "verification_passed",
            outcome="ok",
            evidence=[postcondition],
        )

    def verification_failed(
        self,
        postcondition: str,
        exc: BaseException,
    ) -> None:
        self.record(
            "verification_failed",
            outcome="failure",
            error_details={
                "postcondition": postcondition,
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )


def capture_failure_screenshot(
    page: Any, run_id: str, out_dir: Path
) -> Optional[Path]:
    """Best-effort failure screenshot. Returns the path or ``None``.

    Designed to be passed to :class:`TraceRecorder` via a wrapper that
    only invokes it on error. Errors here are NOT raised; they are
    returned as ``None`` so the calling site can attach a
    ``screenshot_capture_failed`` evidence note instead.
    """
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{run_id}.png"
        page.screenshot(path=str(path))
        return path
    except Exception:  # noqa: BLE001 — best effort
        return None


__all__ = [
    "AGENT_VERSION",
    "TRACE_SCHEMA_VERSION",
    "TraceRecorder",
    "TraceWriteError",
    "capture_failure_screenshot",
]
