"""Eval mini-review packet builder and decisions validator (manual step).

Builds a self-contained human-review packet for the frozen 8-episode
evaluation mini-sample (4 Chimera + 4 Baseline A, one per scenario),
and validates the separately stored human decisions.

The frozen records (runs, plans, manifests, traces, snapshots, action
logs) are only ever READ. Review decisions live in
``mini-review/decisions.json`` — never in the plan files — carrying
reviewer identity, timestamps, and a corrections history. No
LLM-generated verdict counts as a human review: the packet ships with
all decisions pending, and nothing here invents judgments.

Usage::

    .venv/bin/python tools/mini_review.py build-packet
    .venv/bin/python tools/mini_review.py build-bundle
    .venv/bin/python tools/mini_review.py build-reviewer-packet
    .venv/bin/python tools/mini_review.py validate
    .venv/bin/python tools/mini_review.py validate path/to/decisions.json

``build-packet`` fails closed on any inconsistency (wrong episode
count, ID/outcome/verifier mismatch between plan and run, artifact
digest mismatch, unreadable evidence) instead of producing a packet
that misrepresents the evidence. ``validate`` checks a decisions
file's schema, episode resolution, blinding-protocol consistency, and
artifact freshness, then prints a human-vs-verifier comparison with
an explicit n=8 no-reliability-claim caveat. Exit status 0 means the
file is *valid*; completeness (8/8 recorded) is reported, never
assumed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from benchmarks.audit import AuditError, load_plan  # noqa: E402
from benchmarks.manifest import load_manifest  # noqa: E402

DEFAULT_MANIFEST = "benchmarks/manifests/eval-v1.json"
DEFAULT_PAIRS = (
    ("artifacts/eval-20261028/run-chimera.audit-plan-mini.json",
     "artifacts/eval-20261028/run-chimera.json"),
    ("artifacts/eval-20261028/run-baseline-a.audit-plan-mini.json",
     "artifacts/eval-20261028/run-baseline-a.json"),
)
DEFAULT_OUT = "artifacts/eval-20261028/mini-review"

PACKET_SCHEMA = "chimera-mini-review-packet/1"
DECISIONS_SCHEMA = "chimera-mini-review-decisions/1"

ASSESSMENTS = ("verified-success", "verified-failure", "inconclusive")
AGREEMENTS = ("agrees", "disagrees", "undetermined")
SUFFICIENCY = ("sufficient", "insufficient")

# Task + postconditions, quoted from docs/benchmark_design.md §2.
TASK_TEXT = (
    "Create a project with a given name. The agent must navigate to the "
    "target, fill the name, click \"Create Project\", and satisfy the "
    "postconditions."
)
POSTCONDITIONS = [
    {"id": "P1", "name": "Confirmation is visible",
     "check": "`#confirmation` is visible",
     "judge": "Is confirmation_visible true in the snapshot?"},
    {"id": "P2", "name": "The project appears in the list, exactly once",
     "check": "exactly one `#project-list li` whose `textContent` equals "
              "the expected trimmed name",
     "judge": "Does items contain exactly one entry whose text equals "
              "the expected stored name?"},
    {"id": "P3", "name": "The list contains no unexpected entries",
     "check": "the count of `#project-list li` equals 1",
     "judge": "Does items contain exactly one entry?"},
]
P4_NOTE = ("P4 (list empty before the agent's click) is harness-only "
           "context; the audit judges the verifier's P1–P3.")


class PacketError(ValueError):
    """Any inconsistency that must stop packet construction."""


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise PacketError(f"cannot read {path}: {exc}") from exc


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise PacketError(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise PacketError(f"{path} is not valid JSON: {exc}") from exc


def _dump_canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def _parse_iso(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value:
        return None
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if stamp.tzinfo is None:
        return None
    return stamp


# -- packet construction ---------------------------------------------

def _episode_key(run_id: str, trial_id: str) -> str:
    return f"{run_id}::{trial_id}"


def _rel(path: Path) -> str:
    """Repo-relative display path (portable across checkouts)."""
    try:
        return str(Path(path).relative_to(PROJECT_DIR))
    except ValueError:
        return str(path)


def _summarize_trace(trace: Any) -> Tuple[str, List[Dict[str, Any]], List[str]]:
    """Return (kind, steps, screenshot_paths) for a trace/driver report."""
    shots: List[str] = []
    if isinstance(trace, dict) and isinstance(trace.get("events"), list):
        steps = [{
            "seq": e.get("sequence_number"), "timestamp": e.get("timestamp"),
            "event": e.get("event_type"), "action": e.get("action_type"),
            "outcome": e.get("action_outcome"),
            "error": e.get("error_details"),
        } for e in trace["events"]]
        for e in trace["events"]:
            for ref in e.get("evidence_references", []) or []:
                if str(ref).startswith("screenshot="):
                    shots.append(str(ref).split("=", 1)[1])
        return "trace", steps, shots
    if isinstance(trace, dict) and isinstance(trace.get("steps"), list):
        steps = [{
            "seq": i + 1, "step": s.get("step"), "target": s.get("target"),
            "outcome": s.get("outcome"), "error_type": s.get("error_type"),
        } for i, s in enumerate(trace["steps"])]
        return "replay", steps, shots
    raise PacketError("trace artifact is neither an event trace nor a "
                      "replay report")


def _summarize_actions(actions: Any) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if not isinstance(actions, dict) or not isinstance(actions.get("records"), list):
        raise PacketError("action log has no records list")
    meta = {"attached": actions.get("attached"),
            "complete": actions.get("complete"),
            "run_id": actions.get("run_id")}
    records = [{
        "seq": r.get("seq"), "action": r.get("action_type"),
        "target": r.get("target_summary") or r.get("target"),
        "outcome": r.get("outcome"), "error_type": r.get("error_type"),
        "policy": r.get("policy"), "policy_reason": r.get("policy_reason"),
        "elapsed_ms": r.get("elapsed_ms"),
    } for r in actions["records"]]
    return records, meta


def _build_episode(run_id: str, run: Dict[str, Any], plan_path: Path,
                   cell_key: str, bundle: Dict[str, Any]) -> Dict[str, Any]:
    trial_id = bundle.get("trial_id")
    episode = next((e for e in run.get("episodes", [])
                    if e.get("trial_id") == trial_id), None)
    if episode is None:
        raise PacketError(f"{trial_id}: sampled by {plan_path.name} but "
                          f"absent from the run file")
    for field in ("outcome", "agent_terminal_status"):
        if bundle.get(field) != episode.get(field):
            raise PacketError(
                f"{trial_id}: plan {field} {bundle.get(field)!r} != run "
                f"{episode.get(field)!r}")
    run_checks = {c.get("postcondition_id"): c.get("satisfied")
                  for c in (episode.get("verification") or {}).get("checks", [])}
    if dict(bundle.get("verifier_checks") or {}) != run_checks:
        raise PacketError(f"{trial_id}: plan verifier_checks differ from "
                          f"the run record")
    artifacts = {}
    for kind, field in (("trace", "trace_path"), ("snapshot", "snapshot_path"),
                        ("actions", "actions_path")):
        rel = bundle.get(field)
        if not rel:
            raise PacketError(f"{trial_id}: plan names no {field}")
        data = _read_bytes(PROJECT_DIR / rel)
        digest = _sha256_bytes(data)
        if digest != (bundle.get("digests") or {}).get(kind):
            raise PacketError(f"{trial_id}: {kind} bytes differ from the "
                              f"plan digest — evidence changed since planning")
        try:
            parsed = json.loads(data.decode("utf-8"))
        except ValueError as exc:
            raise PacketError(f"{trial_id}: {kind} artifact is not valid "
                              f"JSON: {exc}") from exc
        artifacts[kind] = {"path": rel, "sha256": digest,
                           "bytes": len(data), "data": parsed}
    kind, steps, shots = _summarize_trace(artifacts["trace"]["data"])
    records, actions_meta = _summarize_actions(artifacts["actions"]["data"])
    snapshot = artifacts["snapshot"]["data"]
    if not isinstance(snapshot, dict):
        raise PacketError(f"{trial_id}: snapshot artifact is not an object")
    shot_status = [{"path": s, "exists": (PROJECT_DIR / s).is_file()
                    if not Path(s).is_absolute() else Path(s).is_file()}
                   for s in shots]
    verification = episode.get("verification") or {}
    gaps = []
    if not shots:
        gaps.append("no screenshots attached (expected: the harness "
                    "captures one only on action failure)")
    if kind == "replay":
        gaps.append("replay driver report carries step indexes only — no "
                    "timestamps or trace sequence numbers")
    if verification.get("status") != "verified":
        gaps.append("independent verification status is "
                    f"{verification.get('status')!r} rather than 'verified'")
    return {
        "key": _episode_key(run_id, trial_id),
        "run_id": run_id, "trial_id": trial_id,
        "plan": _rel(plan_path), "plan_cell": cell_key,
        "baseline": bundle.get("baseline"),
        "scenario_id": bundle.get("scenario_id"),
        "input_id": bundle.get("input_id"),
        "expected_stored_name": bundle.get("expected_stored_name"),
        "recorded": {
            "outcome": episode.get("outcome"),
            "agent_terminal_status": episode.get("agent_terminal_status"),
            "error": episode.get("error"),
            "duration_ms": episode.get("duration_ms"),
            "started_at": episode.get("started_at"),
            "completed_at": episode.get("completed_at"),
        },
        "verifier": {
            "status": verification.get("status"),
            "all_satisfied": verification.get("all_satisfied"),
            "checks": verification.get("checks"),
            "unavailable_reason": verification.get("unavailable_reason"),
            "verifier_version": verification.get("verifier_version"),
        },
        "evidence": {
            "kind": kind,
            "steps": steps,
            "actions": records,
            "actions_meta": actions_meta,
            "snapshot": {
                "confirmation_visible": snapshot.get("confirmation_visible"),
                "items": snapshot.get("items"),
                "captured_at": snapshot.get("captured_at"),
                "run_id": snapshot.get("run_id"),
            },
            "screenshots": shot_status,
        },
        "artifacts": {k: {f: v[f] for f in ("path", "sha256", "bytes")}
                      for k, v in artifacts.items()},
        "gaps": gaps,
    }


def build_packet(plan_run_pairs: List[Tuple[Path, Path]], manifest_path: Path,
                 out_dir: Path, expect: int = 8,
                 created_at: Optional[str] = None) -> Dict[str, Any]:
    """Verify the frozen selection and write the review packet."""
    manifest = load_manifest(manifest_path)
    manifest_sha = manifest.sha256()
    episodes: List[Dict[str, Any]] = []
    plan_infos = []
    for plan_path, run_path in plan_run_pairs:
        load_plan(plan_path)  # validates shape, incl. empty verdict maps
        plan = _read_json(plan_path)
        run = _read_json(run_path)
        if plan.get("run_id") != run.get("run_id"):
            raise PacketError(f"{plan_path.name} names run "
                              f"{plan.get('run_id')} but was paired with "
                              f"{run.get('run_id')}")
        for label, value in (("plan", plan.get("manifest_sha256")),
                             ("run", run.get("manifest_sha256"))):
            if value != manifest_sha:
                raise PacketError(
                    f"{plan_path.name}: {label} manifest sha does not match "
                    f"the frozen {manifest_path} ({manifest_sha[:12]}…)")
        plan_infos.append({
            "path": _rel(plan_path),
            "sha256": _sha256_bytes(_read_bytes(plan_path)),
            "run_id": plan.get("run_id"),
            "sample_size": plan.get("sample_size"),
        })
        for cell_key in sorted(plan.get("cells", {})):
            for bundle in plan["cells"][cell_key].get("sampled", []):
                episodes.append(_build_episode(
                    plan["run_id"], run, plan_path, cell_key, bundle))
    if len(episodes) != expect:
        raise PacketError(f"expected exactly {expect} sampled episodes, "
                          f"found {len(episodes)} — refusing to repackage a "
                          f"different selection")
    episodes.sort(key=lambda e: (e["run_id"], e["trial_id"]))
    packet = {
        "schema": PACKET_SCHEMA,
        "created_at": created_at or _utcnow(),
        "manifest": {"path": _rel(manifest_path),
                     "manifest_id": manifest.manifest_id,
                     "sha256": manifest_sha},
        "plans": plan_infos,
        "task": TASK_TEXT,
        "postconditions": POSTCONDITIONS,
        "p4_note": P4_NOTE,
        "blinding_note": ("Recorded outcomes and verifier checks are masked "
                          "during initial assessment in the review queue. "
                          "Blinding is partial: trace structure differs "
                          "between the Chimera driver (event trace) and "
                          "Baseline A (replay report), so a knowledgeable "
                          "reviewer may infer the driver from the evidence "
                          "shape."),
        "episodes": episodes,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "packet.json").write_text(_dump_canonical(packet),
                                         encoding="utf-8")
    (out_dir / "PACKET.md").write_text(render_packet_markdown(packet),
                                       encoding="utf-8")
    _write_initial_decisions(out_dir)
    return packet


def _write_initial_decisions(out_dir: Path) -> None:
    target = out_dir / "decisions.json"
    packet_sha = _sha256_bytes((out_dir / "packet.json").read_bytes())
    initial = {
        "schema": DECISIONS_SCHEMA,
        "packet": "packet.json",
        "packet_sha256": packet_sha,
        "reviewer": "",
        "exported_at": None,
        "decisions": {},
    }
    text = _dump_canonical(initial)
    if target.is_file():
        current = _read_json(target)
        recorded = [k for k, v in (current.get("decisions") or {}).items()
                    if isinstance(v, dict) and v.get("assessment")]
        if recorded:
            raise PacketError(
                f"{target} already holds {len(recorded)} recorded "
                f"decision(s) — refusing to overwrite human judgments. "
                f"Move it aside explicitly to start over.")
        if current != json.loads(text):
            raise PacketError(
                f"{target} exists but differs from a fresh pending file — "
                f"refusing to overwrite silently. Move it aside explicitly "
                f"to regenerate.")
        return
    target.write_text(text, encoding="utf-8")


# -- packet markdown -------------------------------------------------

def _md_value(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    text = str(value)
    return text if len(text) <= 300 else text[:297] + "…"


def render_packet_markdown(packet: Dict[str, Any]) -> str:
    """Deterministic human-readable rendering of a built packet."""
    lines = [
        "# Eval mini-review packet (8 episodes)",
        "",
        f"Created: {packet['created_at']} · schema `{packet['schema']}`.",
        "This packet is a read-only view of frozen evidence plus empty "
        "decision slots. All judgments live in `decisions.json`, recorded "
        "only by a human reviewer.",
        "",
        f"Manifest: `{packet['manifest']['path']}` "
        f"({packet['manifest']['manifest_id']}, "
        f"sha256 `{packet['manifest']['sha256']}` — verified against the "
        "frozen file at packet build).",
        "",
        "## Task and postconditions (benchmark_design §2)",
        "",
        packet["task"],
        "",
    ]
    for pc in packet["postconditions"]:
        lines.append(f"- **{pc['id']}** — {pc['name']}: {pc['check']} "
                     f"(judge: {pc['judge']})")
    lines += ["", packet["p4_note"], "", packet["blinding_note"], "",
              "## Selection", ""]
    for i, ep in enumerate(packet["episodes"], 1):
        lines.append(
            f"{i}. `{ep['key']}` — {ep['scenario_id']}/{ep['input_id']} · "
            f"baseline `{ep['baseline']}` · expected "
            f"{ep['expected_stored_name']!r} · recorded "
            f"`{ep['recorded']['outcome']}` · plan `{ep['plan']}` "
            f"cell `{ep['plan_cell']}`")
    lines += ["", "## Episodes", ""]
    for ep in packet["episodes"]:
        lines += [
            f"### `{ep['key']}`",
            "",
            f"- Condition: {ep['scenario_id']} / {ep['input_id']} / "
            f"{ep['baseline']} · expected stored name: "
            f"{ep['expected_stored_name']!r}",
            f"- Recorded outcome: `{ep['recorded']['outcome']}` · agent "
            f"said `{ep['recorded']['agent_terminal_status']}` · error: "
            f"`{_md_value(ep['recorded']['error'])}`",
            f"- Verifier: status `{ep['verifier']['status']}`, "
            f"all_satisfied={_md_value(ep['verifier']['all_satisfied'])}, "
            f"checks `{_md_value(ep['verifier']['checks'])}` "
            f"({ep['verifier'].get('verifier_version') or 'unrecorded'})",
            f"- Evidence kind: `{ep['evidence']['kind']}` · "
            f"{len(ep['evidence']['steps'])} steps · "
            f"{len(ep['evidence']['actions'])} observed actions · "
            f"snapshot confirmation_visible="
            f"{_md_value(ep['evidence']['snapshot'].get('confirmation_visible'))} "
            f"items={_md_value(ep['evidence']['snapshot'].get('items'))}",
        ]
        for art in ("trace", "snapshot", "actions"):
            a = ep["artifacts"][art]
            lines.append(f"- {art}: `{a['path']}` ({a['bytes']} bytes, "
                         f"sha256 `{a['sha256'][:12]}…`, verified)")
        shots = ep["evidence"]["screenshots"]
        lines.append("- Screenshots: " + (", ".join(
            f"`{s['path']}` ({'present' if s['exists'] else 'MISSING'})"
            for s in shots) if shots else "none attached"))
        for gap in ep["gaps"]:
            lines.append(f"- Gap: {gap}")
        lines.append("")
    lines += [
        "## Review protocol",
        "",
        "1. Assess each episode blinded (recorded outcome and verifier "
        "checks masked): verified success, verified failure, or "
        "inconclusive — from the postconditions and the evidence above, "
        "never from success strings or the verifier's status.",
        "2. Reveal the recorded verdict and judge agreement: agrees, "
        "disagrees, or undetermined.",
        "3. Judge evidence sufficiency and record a reason tied to "
        "specific observations; describe missing evidence explicitly "
        "when a decision cannot be supported.",
        "4. Export `decisions.json` and validate it with "
        "`tools/mini_review.py validate`.",
        "",
        "Eight episodes describe only these eight episodes: agreement "
        "counts here support no reliability claim and the 95% "
        "provisional rule (user guide §15.1 step 4) applies to full "
        "audits, not to this mini-sample.",
        "",
    ]
    return "\n".join(lines)


# -- decisions validation --------------------------------------------

def _decision_errors(key: str, packet_keys: set,
                     decision: Any) -> List[str]:
    errors = []
    if key not in packet_keys:
        errors.append(f"{key}: not one of the 8 packet episodes")
        return errors
    if not isinstance(decision, dict):
        return [f"{key}: decision must be an object"]
    get = decision.get
    if get("assessment") not in ASSESSMENTS:
        errors.append(f"{key}: assessment must be one of {ASSESSMENTS}")
    if get("agreement") not in AGREEMENTS:
        errors.append(f"{key}: agreement must be one of {AGREEMENTS}")
    if get("sufficiency") not in SUFFICIENCY:
        errors.append(f"{key}: sufficiency must be one of {SUFFICIENCY}")
    if not isinstance(get("reason"), str) or not get("reason").strip():
        errors.append(f"{key}: reason is required")
    needs_missing = (get("assessment") == "inconclusive"
                     or get("sufficiency") == "insufficient")
    if needs_missing and (not isinstance(get("missing_evidence"), str)
                          or not get("missing_evidence").strip()):
        errors.append(f"{key}: missing_evidence is required when the "
                      f"assessment is inconclusive or the evidence is "
                      f"insufficient")
    assessed = _parse_iso(get("assessed_at"))
    if assessed is None:
        errors.append(f"{key}: assessed_at must be an ISO-8601 timestamp "
                      f"with timezone")
    revealed = _parse_iso(get("revealed_at")) if get("revealed_at") else None
    if get("revealed_at") and revealed is None:
        errors.append(f"{key}: revealed_at must be null or an ISO-8601 "
                      f"timestamp with timezone")
    if get("agreement") in ("agrees", "disagrees") and revealed is None:
        errors.append(f"{key}: agreement with the verifier requires "
                      f"revealing the recorded verdict first")
    expected_blind = revealed is None or (
        assessed is not None and assessed <= revealed)
    if get("blinded") is not expected_blind:
        errors.append(f"{key}: blinded flag is inconsistent with the "
                      f"assessment/reveal timestamps")
    corrections = get("corrections", [])
    if not isinstance(corrections, list):
        errors.append(f"{key}: corrections must be a list")
    else:
        for i, corr in enumerate(corrections):
            if not isinstance(corr, dict):
                errors.append(f"{key}: corrections[{i}] must be an object")
                continue
            if _parse_iso(corr.get("at")) is None:
                errors.append(f"{key}: corrections[{i}].at must be an "
                              f"ISO-8601 timestamp with timezone")
            if not isinstance(corr.get("previous"), dict):
                errors.append(f"{key}: corrections[{i}].previous must be "
                              f"an object")
            if (not isinstance(corr.get("reason"), str)
                    or not corr["reason"].strip()):
                errors.append(f"{key}: corrections[{i}].reason is required")
    return errors


def validate_decisions(packet: Dict[str, Any],
                       decisions: Dict[str, Any]) -> List[str]:
    """Schema + resolution + protocol validation. Returns error list."""
    errors = []
    if decisions.get("schema") != DECISIONS_SCHEMA:
        errors.append(f"schema must be {DECISIONS_SCHEMA}")
    packet_sha = _sha256_bytes(_dump_canonical(packet).encode("utf-8"))
    if decisions.get("packet_sha256") not in (None, packet_sha):
        errors.append("packet_sha256 does not match the loaded packet — "
                      "decisions were recorded against different bytes")
    packet_keys = {e["key"] for e in packet.get("episodes", [])}
    entries = decisions.get("decisions")
    if not isinstance(entries, dict):
        return errors + ["decisions must be an object keyed by episode"]
    for key, decision in entries.items():
        errors.extend(_decision_errors(key, packet_keys, decision))
    return errors


def _freshness_errors(packet: Dict[str, Any]) -> List[str]:
    """Re-verify that frozen bytes still match packet digests."""
    errors = []
    for ep in packet.get("episodes", []):
        for kind, art in ep.get("artifacts", {}).items():
            path = PROJECT_DIR / art["path"]
            try:
                current = _sha256_bytes(path.read_bytes())
            except OSError:
                errors.append(f"{ep['key']}: {kind} artifact unreadable: "
                              f"{art['path']}")
                continue
            if current != art["sha256"]:
                errors.append(f"{ep['key']}: {kind} bytes changed since "
                              f"packet build")
    return errors


def summarize(packet: Dict[str, Any],
              decisions: Dict[str, Any]) -> Dict[str, Any]:
    """Per-episode human-vs-recorded comparison (no reliability claim)."""
    by_key = {e["key"]: e for e in packet.get("episodes", [])}
    entries = decisions.get("decisions", {})
    rows = []
    for key in sorted(by_key):
        ep = by_key[key]
        dec = entries.get(key) if isinstance(entries, dict) else None
        recorded = ", ".join(
            f"{c.get('postcondition_id')}={'T' if c.get('satisfied') else 'F'}"
            for c in (ep["verifier"].get("checks") or [])) or "—"
        rows.append({
            "key": key,
            "recorded_outcome": ep["recorded"]["outcome"],
            "recorded_checks": recorded,
            "assessment": (dec or {}).get("assessment", "pending"),
            "agreement": (dec or {}).get("agreement", "pending"),
            "sufficiency": (dec or {}).get("sufficiency", "pending"),
        })
    recorded_n = sum(1 for r in rows if r["assessment"] != "pending")
    return {
        "reviewer": decisions.get("reviewer") or "(unrecorded)",
        "recorded": recorded_n, "total": len(rows),
        "complete": recorded_n == len(rows) and bool(decisions.get("reviewer")),
        "rows": rows,
    }


def render_summary(packet: Dict[str, Any], decisions: Dict[str, Any]) -> str:
    summary = summarize(packet, decisions)
    lines = [
        f"Mini-review: {summary['recorded']}/{summary['total']} recorded "
        f"· reviewer: {summary['reviewer']}",
        f"{'episode':<42}{'recorded':<11}{'checks':<17}{'human':<17}"
        f"{'agreement':<13}{'evidence'}",
    ]
    for r in summary["rows"]:
        lines.append(f"{r['key']:<42}{r['recorded_outcome']:<11}"
                     f"{r['recorded_checks']:<17}{r['assessment']:<17}"
                     f"{r['agreement']:<13}{r['sufficiency']}")
    lines += [
        "",
        "Status: " + ("COMPLETE — 8/8 human decisions recorded."
                      if summary["complete"] else
                      "IN PROGRESS — pending decisions remain; nothing is "
                      "complete until a human records all 8."),
        "Caveat: these 8 episodes describe only themselves. Agreement "
        "counts support no reliability claim; the 95% provisional rule "
        "(user guide §15.1 step 4) applies to full audits, not here.",
    ]
    return "\n".join(lines)


# -- evidence bundle -------------------------------------------------

BUNDLE_SCHEMA = "chimera-mini-review-bundle/1"
# Fixed zip entry timestamp so bundles are byte-reproducible.
_BUNDLE_DATE = (2026, 10, 29, 0, 0, 0)


def _collect_bundle_entries(packet: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Resolve + verify every bundlable file. Fails closed, loudly."""
    wanted: List[Tuple[str, Optional[str], Optional[int]]] = []
    for ep in packet.get("episodes", []):
        for kind, art in ep.get("artifacts", {}).items():
            wanted.append((art["path"], art["sha256"], art["bytes"]))
        for shot in ep.get("evidence", {}).get("screenshots", []):
            wanted.append((shot["path"], None, None))
    for plan in packet.get("plans", []):
        wanted.append((plan["path"], plan.get("sha256"), None))
    manifest = packet.get("manifest", {})
    manifest_bytes: Optional[bytes] = None
    manifest_disk: Optional[Path] = None
    manifest_problem: Optional[str] = None
    try:
        manifest_disk = PROJECT_DIR / manifest["path"]
        manifest_bytes = manifest_disk.read_bytes()
    except (OSError, KeyError, TypeError):
        manifest_problem = f"missing: {manifest.get('path')}"
    if manifest_bytes is not None and manifest_disk is not None:
        try:
            canonical = load_manifest(manifest_disk).sha256()
        except ValueError as exc:
            manifest_problem = f"manifest failed to load: {exc}"
            canonical = None
        if canonical is not None and canonical != manifest.get("sha256"):
            manifest_problem = (
                f"manifest canonical sha mismatch: {manifest['path']} "
                f"(packet {str(manifest.get('sha256'))[:12]}…, "
                f"loader {canonical[:12]}…)")
    entries = []
    problems = []
    if manifest_problem is not None:
        problems.append(manifest_problem)
    elif manifest_bytes is not None and manifest_disk is not None:
        # NOTE: the packet's manifest sha is the loader's canonical hash,
        # not a raw-bytes hash (verified above); the bundle records the
        # raw bytes + their sha for byte-exact reproduction.
        entries.append({"path": manifest["path"], "bytes": len(manifest_bytes),
                        "sha256": _sha256_bytes(manifest_bytes),
                        "disk": manifest_disk})
    for rel, want_sha, want_bytes in wanted:
        source = PROJECT_DIR / rel
        if not source.is_file():
            problems.append(f"missing: {rel}")
            continue
        data = source.read_bytes()
        digest = _sha256_bytes(data)
        if want_sha is not None and digest != want_sha:
            problems.append(f"sha256 mismatch: {rel} "
                            f"(packet {want_sha[:12]}…, disk {digest[:12]}…)")
            continue
        if want_bytes is not None and len(data) != want_bytes:
            problems.append(f"byte-count mismatch: {rel} (packet "
                            f"{want_bytes}, disk {len(data)})")
            continue
        try:
            arc = str(Path(rel).relative_to(PROJECT_DIR)) \
                if Path(rel).is_absolute() else rel
        except ValueError:
            problems.append(f"outside repository, cannot bundle: {rel}")
            continue
        entries.append({"path": arc, "bytes": len(data), "sha256": digest,
                        "disk": source})
    if problems:
        raise PacketError("evidence bundle refused:\n  - "
                          + "\n  - ".join(problems))
    entries.sort(key=lambda e: e["path"])
    return entries


def build_bundle(packet: Dict[str, Any], out_zip: Path) -> Dict[str, Any]:
    """Write a deterministic zip of the verified original artifacts."""
    entries = _collect_bundle_entries(packet)
    manifest = {
        "schema": BUNDLE_SCHEMA,
        "files": [{k: e[k] for k in ("path", "bytes", "sha256")}
                  for e in entries],
        "total_bytes": sum(e["bytes"] for e in entries),
    }
    manifest_text = _dump_canonical(manifest)
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for arc, data in [("BUNDLE_MANIFEST.json",
                            manifest_text.encode("utf-8"))
                          ] + [(e["path"], e["disk"].read_bytes())
                               for e in entries]:
            info = zipfile.ZipInfo(arc, date_time=_BUNDLE_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, data)
    return manifest


# -- reviewer-safe packet ----------------------------------------------

REVIEWER_SCHEMA = "chimera-mini-review-reviewer-packet/1"
ANSWER_SCHEMA = "chimera-mini-review-answer-key/1"
# Keys that must never appear in the reviewer packet, at any depth.
# (Action-level "outcome" fields are evidence and stay; the episode's
# recorded outcome and every verifier field go.)
_BANNED_KEYS = frozenset({
    "recorded", "verifier", "decisions", "verdicts", "assessment",
    "agreement", "all_satisfied", "satisfied", "agent_terminal_status",
})


def _assert_reviewer_safe(node: Any, trail: str = "$") -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in _BANNED_KEYS:
                raise PacketError(
                    f"reviewer packet would leak {trail}.{key} — refusing")
            if key == "gaps" and isinstance(value, list):
                for gap in value:
                    if "verification status" in str(gap):
                        raise PacketError(
                            f"reviewer packet gap reveals verifier status — "
                            f"refusing")
            _assert_reviewer_safe(value, f"{trail}.{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            _assert_reviewer_safe(value, f"{trail}[{i}]")


def build_reviewer_packet(packet: Dict[str, Any], packet_sha: str,
                          out_dir: Path,
                          created_at: Optional[str] = None) -> Dict[str, Any]:
    """Split the packet into a reviewer-safe bundle + separate answer key.

    The full packet is never modified. The reviewer packet keeps stable
    episode references and all P1–P3 evidence but excludes recorded
    terminal outcomes, verifier decisions, human verdicts, and any
    assessment. Answer information goes to answer-key.json only.
    """
    episodes = []
    answers = {}
    for ep in packet.get("episodes", []):
        episodes.append({
            "key": ep["key"], "run_id": ep["run_id"],
            "trial_id": ep["trial_id"], "plan": ep["plan"],
            "plan_cell": ep["plan_cell"], "baseline": ep["baseline"],
            "scenario_id": ep["scenario_id"], "input_id": ep["input_id"],
            "expected_stored_name": ep["expected_stored_name"],
            "evidence": ep["evidence"], "artifacts": ep["artifacts"],
            "gaps": [g for g in ep.get("gaps", [])
                     if "verification status" not in g],
        })
        answers[ep["key"]] = {
            "outcome": ep["recorded"]["outcome"],
            "agent_terminal_status": ep["recorded"]["agent_terminal_status"],
            "error": ep["recorded"]["error"],
            "verifier_status": ep["verifier"]["status"],
            "verifier_all_satisfied": ep["verifier"]["all_satisfied"],
            "verifier_checks": ep["verifier"]["checks"],
        }
    reviewer = {
        "schema": REVIEWER_SCHEMA,
        "created_at": created_at or _utcnow(),
        "packet_sha256": packet_sha,
        "manifest": packet["manifest"],
        "plans": packet["plans"],
        "task": packet["task"],
        "postconditions": packet["postconditions"],
        "p4_note": packet["p4_note"],
        "blinding_note": packet["blinding_note"],
        "episodes": episodes,
    }
    _assert_reviewer_safe(reviewer)
    key_doc = {"schema": ANSWER_SCHEMA, "packet_sha256": packet_sha,
               "warning": ("DO NOT distribute to the reviewer before their "
                           "initial decisions are locked."),
               "episodes": answers}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "reviewer-packet.json").write_text(
        _dump_canonical(reviewer), encoding="utf-8")
    (out_dir / "answer-key.json").write_text(
        _dump_canonical(key_doc), encoding="utf-8")
    return reviewer


# -- CLI ---------------------------------------------------------------

def _default_out() -> Path:
    return PROJECT_DIR / DEFAULT_OUT


def cmd_build_packet(args: argparse.Namespace) -> int:
    pairs = list(zip(args.plans, args.runs))
    try:
        packet = build_packet(
            [(PROJECT_DIR / p, PROJECT_DIR / r) for p, r in pairs],
            PROJECT_DIR / args.manifest, PROJECT_DIR / args.out,
            expect=args.expect, created_at=args.created_at)
    except (PacketError, AuditError, ValueError) as exc:
        print(f"mini_review: {exc}", file=sys.stderr)
        return 1
    print(f"packet: {len(packet['episodes'])} episodes verified, "
          f"manifest {packet['manifest']['sha256'][:12]}…")
    print(f"wrote {args.out}/packet.json, PACKET.md, decisions.json")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    packet_path = PROJECT_DIR / args.packet / "packet.json"
    decisions_path = Path(args.decisions)
    if not decisions_path.is_absolute():
        decisions_path = PROJECT_DIR / decisions_path
    try:
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
    except OSError as exc:
        print(f"mini_review: cannot read input: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"mini_review: invalid JSON: {exc}", file=sys.stderr)
        return 1
    errors = validate_decisions(packet, decisions)
    errors += _freshness_errors(packet)
    if decisions.get("packet_sha256") is None:
        print("warning: decisions carry no packet_sha256 (exporter could "
              "not hash); episode keys were still checked")
    if errors:
        print("INVALID:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print(render_summary(packet, decisions))
    return 0


def _load_packet_bytes(packet_dir: Path) -> Tuple[Dict[str, Any], str]:
    raw = (packet_dir / "packet.json").read_bytes()
    return json.loads(raw.decode("utf-8")), _sha256_bytes(raw)


def cmd_build_bundle(args: argparse.Namespace) -> int:
    try:
        packet, _ = _load_packet_bytes(PROJECT_DIR / args.packet)
        manifest = build_bundle(packet, PROJECT_DIR / args.out)
    except (PacketError, OSError, ValueError) as exc:
        print(f"mini_review: {exc}", file=sys.stderr)
        return 1
    print(f"bundle: {len(manifest['files'])} files, "
          f"{manifest['total_bytes']} bytes verified → {args.out}")
    for entry in manifest["files"]:
        print(f"  {entry['sha256'][:12]}… {entry['bytes']:>7}  {entry['path']}")
    return 0


def cmd_build_reviewer(args: argparse.Namespace) -> int:
    out_dir = PROJECT_DIR / args.packet
    before = _sha256_bytes((out_dir / "packet.json").read_bytes())
    try:
        packet, sha = _load_packet_bytes(out_dir)
        reviewer = build_reviewer_packet(packet, sha, out_dir,
                                         created_at=args.created_at)
    except (PacketError, OSError, ValueError) as exc:
        print(f"mini_review: {exc}", file=sys.stderr)
        return 1
    after = _sha256_bytes((out_dir / "packet.json").read_bytes())
    if before != after:  # defense in depth; builder never writes packet.json
        print("mini_review: packet.json changed during split — refusing",
              file=sys.stderr)
        return 1
    print(f"reviewer packet: {len(reviewer['episodes'])} episodes, "
          f"answers split to answer-key.json (packet bytes unchanged)")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mini_review.py",
        description="Build the 8-episode eval review packet; validate "
                    "human decisions.")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build-packet", help="verify + write the packet")
    build.add_argument("--plans", nargs=2, metavar=("PLAN1", "PLAN2"),
                       default=[p for p, _ in DEFAULT_PAIRS])
    build.add_argument("--runs", nargs=2, metavar=("RUN1", "RUN2"),
                       default=[r for _, r in DEFAULT_PAIRS])
    build.add_argument("--manifest", default=DEFAULT_MANIFEST)
    build.add_argument("--out", default=DEFAULT_OUT)
    build.add_argument("--expect", type=int, default=8)
    build.add_argument("--created-at", default=None)
    build.set_defaults(func=cmd_build_packet)
    val = sub.add_parser("validate", help="validate a decisions file")
    val.add_argument("decisions", nargs="?",
                     default=str(Path(DEFAULT_OUT) / "decisions.json"))
    val.add_argument("--packet", default=DEFAULT_OUT)
    val.set_defaults(func=cmd_validate)
    bundle = sub.add_parser("build-bundle",
                            help="zip the verified original artifacts")
    bundle.add_argument("--packet", default=DEFAULT_OUT)
    bundle.add_argument("--out", default=str(
        Path(DEFAULT_OUT) / "evidence-bundle.zip"))
    bundle.set_defaults(func=cmd_build_bundle)
    reviewer = sub.add_parser(
        "build-reviewer-packet",
        help="split off a reviewer-safe packet + separate answer key")
    reviewer.add_argument("--packet", default=DEFAULT_OUT)
    reviewer.add_argument("--created-at", default=None)
    reviewer.set_defaults(func=cmd_build_reviewer)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
