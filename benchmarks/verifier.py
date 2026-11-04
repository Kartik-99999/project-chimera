"""Independent verification of benchmark episodes (harness Stage 3).

The agent's own verification is part of the system under test; using it
to grade the system would make the false-success metric a tautology
(``docs/benchmark_design.md`` §5). This module re-implements the
postcondition checks separately, against independently observed browser
state — never against the trace's ``verification_passed`` events.

Authority
---------
``docs/benchmark_design.md`` §2 (postconditions P1–P3 with exact-match
semantics) and §5 (the false-success mechanism):

* ``P1`` — ``#confirmation`` is visible.
* ``P2`` — exactly one ``#project-list li`` whose ``textContent``
  **equals** the expected stored name (no trimming, no case folding,
  no substring matching).
* ``P3`` — the count of ``#project-list li`` equals 1.
* ``false_success := (agent reported "succeeded") AND NOT (P1 AND P2
  AND P3)``, where the agent's report comes from the persisted trace
  artifact's ``terminal_status``.

Why a snapshot
--------------
The agent closes its browser context before ``create_project()``
returns, and the demo app keeps its state in memory per page load, so
no live page exists for a post-hoc verifier to inspect. The harness
therefore captures an independent state snapshot while the page is
still alive — via the agent's optional ``observe`` hook, which invokes
a harness-supplied callback before teardown — and persists it next to
the trace. This module evaluates P1–P3 from that snapshot file.

Independence
------------
This module imports only the standard library and
:mod:`benchmarks.results` (typed schemas). It never imports
``chimera.agent`` or any agent verification helper, and its checks use
strict equality where the agent uses Playwright's ``has_text``
substring match. ``tests/test_benchmark_verifier.py`` enforces this
with an import-hygiene test and a source scan.

Failure policy: fail closed. A missing, malformed, or mismatched
snapshot yields ``unavailable`` evidence with an explicit reason — the
episode is then excluded from false-success classification rather
than classified either way.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

from benchmarks.results import (
    PostconditionCheck,
    VerificationEvidence,
)

#: Version string recorded on evidence this module produces.
VERIFIER_VERSION = "independent-verifier-1.0"

#: Filename suffix for snapshot artifacts next to ``<run_id>.json`` traces.
SNAPSHOT_SUFFIX = ".snapshot.json"


class SnapshotValidationError(ValueError):
    """A state snapshot is malformed and cannot be evaluated."""


# ---------------------------------------------------------------------------
# Snapshot schema
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DOMSnapshot:
    """The independently observed page state for one episode.

    ``confirmation_visible`` is whether ``#confirmation`` was visible;
    ``items`` are the ``textContent`` of every ``#project-list li`` in
    document order, exactly as observed — the verifier never trims,
    folds, or substring-matches them.
    """

    run_id: str
    confirmation_visible: bool
    items: Tuple[str, ...]
    captured_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "confirmation_visible": self.confirmation_visible,
            "items": list(self.items),
            "captured_at": self.captured_at,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False) + "\n"

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DOMSnapshot":
        """Parse and strictly validate a snapshot, failing closed."""
        if not isinstance(data, Mapping):
            raise SnapshotValidationError(
                f"snapshot must be an object, got {type(data).__name__}"
            )
        run_id = data.get("run_id")
        if not isinstance(run_id, str) or not run_id.strip():
            raise SnapshotValidationError(
                f"snapshot run_id must be a non-empty string, got {run_id!r}"
            )
        visible = data.get("confirmation_visible")
        # Strictly bool: 0/1 or "false"/"true" are malformed, not false.
        if not isinstance(visible, bool):
            raise SnapshotValidationError(
                "snapshot confirmation_visible must be a boolean, "
                f"got {visible!r}"
            )
        items = data.get("items")
        if not isinstance(items, list):
            raise SnapshotValidationError(
                f"snapshot items must be a list, got {items!r}"
            )
        for index, item in enumerate(items):
            if not isinstance(item, str):
                raise SnapshotValidationError(
                    f"snapshot items[{index}] must be a string, got {item!r}"
                )
        captured_at = data.get("captured_at", "")
        if not isinstance(captured_at, str):
            raise SnapshotValidationError(
                f"snapshot captured_at must be a string, got {captured_at!r}"
            )
        return cls(run_id=run_id, confirmation_visible=visible,
                   items=tuple(items), captured_at=captured_at)

    @classmethod
    def from_json(cls, raw: str) -> "DOMSnapshot":
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SnapshotValidationError(
                f"snapshot is not valid JSON: {exc}") from exc
        return cls.from_dict(data)


def load_snapshot(path: Path) -> DOMSnapshot:
    """Load a snapshot artifact, failing closed on any problem."""
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise SnapshotValidationError(
            f"snapshot unreadable: {path}: {exc}") from exc
    try:
        return DOMSnapshot.from_json(raw)
    except SnapshotValidationError as exc:
        raise SnapshotValidationError(f"snapshot {path}: {exc}") from exc


def snapshot_path_for(trace_dir: Path, run_id: str) -> Path:
    """The snapshot artifact path for an episode's run."""
    return Path(trace_dir) / f"{run_id}{SNAPSHOT_SUFFIX}"


# ---------------------------------------------------------------------------
# Harness-side observation (runs while the page is alive)
# ---------------------------------------------------------------------------


PROJECT_LIST_SELECTOR = "#project-list li"
CONTACT_LIST_SELECTOR = "#submission-list li"


def capture_page_state(page: Any,
                       items_selector: str = PROJECT_LIST_SELECTOR
                       ) -> Dict[str, Any]:
    """Read the raw postcondition state from a live Playwright page.

    This is the harness's observation callback, passed to the agent's
    ``observe`` hook by the default executor. It reads visibility and
    ``textContent`` only — it performs no matching and shares no logic
    with the agent's ``has_text`` verification. Duck-typed on the page
    object, so this module imports nothing from Playwright.

    ``items_selector`` names the submitted-entry list; the default
    keeps the project workflow unchanged, while the contact workflow
    passes :data:`CONTACT_LIST_SELECTOR`.
    """
    confirmation = page.locator("#confirmation")
    project_items = page.locator(items_selector)
    return {
        "confirmation_visible": bool(confirmation.is_visible()),
        "items": list(project_items.all_text_contents()),
    }


# ---------------------------------------------------------------------------
# Postcondition evaluation
# ---------------------------------------------------------------------------


def verify_postconditions(
    *,
    snapshot: Optional[Mapping[str, Any]],
    expected_stored_name: str,
    snapshot_ref: str,
    run_id: str,
    observation_error: Optional[str] = None,
) -> VerificationEvidence:
    """Evaluate P1–P3 from an independent snapshot (design §2, §5).

    ``snapshot`` is the parsed snapshot object (or ``None`` when no
    snapshot was captured); ``expected_stored_name`` is the manifest's
    declared stored name for the episode's input; ``snapshot_ref`` names
    the evidence artifact for the references; ``run_id`` is the
    episode's run, which the snapshot must belong to.

    Any missing, malformed, or mismatched evidence yields
    ``unavailable`` evidence with an explicit reason — never a
    classification.
    """
    if snapshot is None:
        reason = (
            f"state snapshot missing for run {run_id!r}"
            + (f": {observation_error}" if observation_error else "")
        )
        return VerificationEvidence.not_yet_verified(reason)
    try:
        parsed = (snapshot if isinstance(snapshot, DOMSnapshot)
                  else DOMSnapshot.from_dict(snapshot))
    except SnapshotValidationError as exc:
        return VerificationEvidence.not_yet_verified(
            f"state snapshot malformed for run {run_id!r}: {exc}"
        )
    if parsed.run_id != run_id:
        return VerificationEvidence.not_yet_verified(
            f"state snapshot mismatch for run {run_id!r}: artifact belongs "
            f"to run {parsed.run_id!r}"
        )
    p1 = parsed.confirmation_visible
    matching = sum(1 for item in parsed.items if item == expected_stored_name)
    p2 = matching == 1
    p3 = len(parsed.items) == 1
    checks = (
        PostconditionCheck(
            postcondition_id="P1",
            satisfied=p1,
            evidence_reference=f"{snapshot_ref}#P1",
            detail=f"confirmation_visible={p1!r}",
        ),
        PostconditionCheck(
            postcondition_id="P2",
            satisfied=p2,
            evidence_reference=f"{snapshot_ref}#P2",
            detail=f"{matching} of {len(parsed.items)} items equal "
                   f"{expected_stored_name!r} (exact match)",
        ),
        PostconditionCheck(
            postcondition_id="P3",
            satisfied=p3,
            evidence_reference=f"{snapshot_ref}#P3",
            detail=f"project-list count={len(parsed.items)}, expected 1",
        ),
    )
    return VerificationEvidence(
        status=VerificationEvidence.VERIFIED,
        all_satisfied=(p1 and p2 and p3),
        checks=checks,
        verifier_version=VERIFIER_VERSION,
    )


# ---------------------------------------------------------------------------
# Classification (design §5)
# ---------------------------------------------------------------------------


def classify_false_success(
    agent_terminal_status: str,
    evidence: VerificationEvidence,
) -> Optional[bool]:
    """Apply the false-success formula, or ``None`` when unverifiable.

    ``false_success := (agent reported "succeeded") AND NOT (P1 AND P2
    AND P3)``. The agent's report must come from the persisted trace
    artifact's ``terminal_status``. An episode whose evidence is
    unavailable is **not** classified either way (``None``) — failing
    closed rather than guessing.
    """
    if evidence.status != VerificationEvidence.VERIFIED:
        return None
    return agent_terminal_status == "succeeded" and evidence.all_satisfied is False


def is_verifier_disagreement(
    agent_terminal_status: str,
    evidence: VerificationEvidence,
) -> bool:
    """Whether the verifier contradicts a non-success report (design §5).

    A **false negative**: the agent reported anything other than
    ``succeeded`` while the independent checks all hold. Reported
    separately, never merged into success. Unverifiable episodes are
    not disagreements.
    """
    return (
        evidence.status == VerificationEvidence.VERIFIED
        and evidence.all_satisfied is True
        and agent_terminal_status != "succeeded"
    )


def summarize_checks(
    evidence: VerificationEvidence,
) -> Dict[str, bool]:
    """Map postcondition ID to its verdict for aggregation.

    Raises :class:`SnapshotValidationError` when the evidence is not
    verified — callers must gate on verified status first, so an
    unverifiable episode can never silently contribute a zero.
    """
    if evidence.status != VerificationEvidence.VERIFIED:
        raise SnapshotValidationError(
            "cannot summarize unverified evidence: "
            f"{evidence.unavailable_reason!r}"
        )
    return {check.postcondition_id: check.satisfied for check in evidence.checks}


__all__ = [
    "CONTACT_LIST_SELECTOR",
    "DOMSnapshot",
    "PROJECT_LIST_SELECTOR",
    "SNAPSHOT_SUFFIX",
    "VERIFIER_VERSION",
    "SnapshotValidationError",
    "capture_page_state",
    "classify_false_success",
    "is_verifier_disagreement",
    "load_snapshot",
    "snapshot_path_for",
    "summarize_checks",
    "verify_postconditions",
]
