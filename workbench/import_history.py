"""Import frozen benchmark episodes into workbench history.

Every imported row is labelled ``source='benchmark'`` with a
``source_ref`` naming the run file and run id, so historical records
are never confused with new workbench executions. Imports are
idempotent (deterministic ids, ``INSERT OR IGNORE``).

Actions come from sibling ``.actions.json`` observer logs when
present, else from trace events carrying an ``action_type``. Nothing
is zero-filled: missing numerics stay NULL.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from workbench.store import Store

# manifest_id -> human run label is derived per file; arms that share a
# baseline name are disambiguated from the run filename.
_REPLAY_PREFIX = "main-mb-v1-replay-"


def _parse_ts(value: Any) -> Optional[float]:
    if not isinstance(value, str) or not value:
        return None
    try:
        from datetime import datetime
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _error_type(error: Any) -> Optional[str]:
    if not error:
        return None
    text = error if isinstance(error, str) else json.dumps(error)
    head = text.split(":", 1)[0].strip()
    return head.split(".")[-1] or None


def _metric(node: Any) -> Optional[int]:
    if isinstance(node, dict):
        value = node.get("value")
        return value if isinstance(value, int) else None
    return node if isinstance(node, int) else None


def _verdict(verification: Any) -> str:
    if not isinstance(verification, dict):
        return "insufficient-evidence"
    if verification.get("status") != "verified":
        return "insufficient-evidence"
    if verification.get("all_satisfied"):
        return "verified-success"
    return "verified-failure"


def _checks(verification: Any) -> List[Dict[str, Any]]:
    if not isinstance(verification, dict):
        return []
    rows = []
    for check in verification.get("checks") or []:
        if not isinstance(check, dict):
            continue
        rows.append({
            "check_id": check.get("postcondition_id", "?"),
            "satisfied": check.get("satisfied"),
            "detail": check.get("detail"),
        })
    return rows


def _snapshot_ref(verification: Any) -> Optional[str]:
    if not isinstance(verification, dict):
        return None
    for check in verification.get("checks") or []:
        ref = (check or {}).get("evidence_reference") or ""
        if "#" in ref:
            return ref.split("#", 1)[0]
    return None


def _actions_for_trace(trace_path: Optional[str]) -> List[Dict[str, Any]]:
    if not trace_path:
        return []
    path = Path(trace_path)
    if not path.is_file():
        return []
    stem = str(path)
    if stem.endswith(".replay.json"):
        stem = stem[: -len(".replay.json")]
    elif stem.endswith(".json"):
        stem = stem[: -len(".json")]
    actions_file = Path(stem + ".actions.json")
    if actions_file.is_file():
        try:
            doc = json.loads(actions_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            doc = None
        if doc is not None:
            return [{
                "seq": r.get("seq", i),
                "action_type": r.get("action_type", "?"),
                "target_summary": r.get("target_summary"),
                "outcome": r.get("outcome", "ok"),
                "elapsed_ms": r.get("elapsed_ms"),
                "error_type": r.get("error_type"),
            } for i, r in enumerate(doc.get("records", []))]
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    rows = []
    prev: Optional[float] = None
    for event in doc.get("events", []):
        action = event.get("action_type")
        if not action:
            continue
        stamp = _parse_ts(event.get("timestamp"))
        elapsed = (int((stamp - prev) * 1000)
                   if stamp is not None and prev is not None else None)
        if stamp is not None:
            prev = stamp
        err = event.get("error_details")
        rows.append({
            "seq": event.get("sequence_number", len(rows)),
            "ts": event.get("timestamp"),
            "action_type": action,
            "target_summary": event.get("event_type"),
            "outcome": ("error"
                        if event.get("action_outcome") == "failure"
                        else "ok"),
            "elapsed_ms": elapsed,
            "error_type": _error_type(err) if err else None,
        })
    return rows


def _driver_for(run_path: Path, episode: Dict[str, Any]) -> str:
    stem = run_path.stem
    if stem.startswith(_REPLAY_PREFIX):
        return f"replay-{stem[len(_REPLAY_PREFIX):]}"
    return str(episode.get("baseline") or "unknown")


def _source_for(manifest_id: str, run_path: Path) -> str:
    """Origin label: matched-budget runs are their own population."""
    if manifest_id.startswith("mb") or \
            run_path.stem.startswith("main-mb-v1-"):
        return "matched-budget"
    return "benchmark"


def import_run_file(store: Store, run_path: Path | str) -> Dict[str, int]:
    """Import one benchmark run file; return counts. Idempotent."""
    run_path = Path(run_path)
    doc = json.loads(run_path.read_text(encoding="utf-8"))
    run_id = doc.get("run_id", run_path.stem)
    manifest_id = doc.get("manifest_id", "?")
    imported = skipped = 0
    for episode in doc.get("episodes", []):
        if not isinstance(episode, dict):
            skipped += 1
            continue
        trial_id = str(episode.get("trial_id", ""))
        exec_id = f"bm:{run_id}:{trial_id}"
        if store.exists(exec_id):
            skipped += 1
            continue
        outcome = episode.get("outcome")
        status = outcome if outcome in ("succeeded", "failed",
                                        "cancelled") else "failed"
        verification = episode.get("verification")
        trace_path = episode.get("trace_artifact")
        actions = _actions_for_trace(trace_path)
        error = episode.get("error")
        store.create_execution({
            "id": exec_id,
            "created_at": episode.get("started_at"),
            "completed_at": episode.get("completed_at"),
            "source": _source_for(manifest_id, run_path),
            "source_ref": f"{manifest_id}:{run_path.name}:{run_id}",
            "workflow_id": "create-project",
            "driver": _driver_for(run_path, episode),
            "scenario_id": str(episode.get("scenario_id", "?")),
            "trial_kind": ("warmup" if trial_id.startswith("warmup")
                           else "measured"),
            "input_id": episode.get("input_id"),
            "project_name": None,
            "status": status,
            "verdict": _verdict(verification),
            "duration_ms": episode.get("duration_ms"),
            "error": error,
            "error_type": _error_type(error),
            "failure_category": episode.get("failure_category"),
            "retries": _metric(episode.get("retries")),
            "actions_count": (len(actions) if actions else _metric(
                episode.get("actions_executed"))),
            "trace_path": trace_path,
            "snapshot_path": _snapshot_ref(verification),
        })
        if actions:
            store.replace_actions(exec_id, actions)
        checks = _checks(verification)
        if checks:
            store.replace_verification(exec_id, checks)
        imported += 1
    return {"imported": imported, "skipped": skipped}


def import_paths(store: Store, paths: List[Path | str]) -> Dict[str, int]:
    total = {"imported": 0, "skipped": 0, "files": 0}
    for path in paths:
        result = import_run_file(store, path)
        total["imported"] += result["imported"]
        total["skipped"] += result["skipped"]
        total["files"] += 1
    return total


def default_run_files(root: Path | str) -> List[Path]:
    """Frozen benchmark run files, excluding audited copies and configs."""
    root = Path(root)
    files: List[Path] = []
    files += sorted((root / "artifacts" / "dev-20261028").glob(
        "run-*.json"))
    files += sorted((root / "artifacts" / "eval-20261028").glob(
        "run-*.json"))
    files += sorted((root / "experiments" / "matched-budget-v1" / "runs")
                    .glob("main-*.json"))
    return [f for f in files
            if ".audit-plan" not in f.name and ".audited" not in f.name
            and ".config" not in f.name]
