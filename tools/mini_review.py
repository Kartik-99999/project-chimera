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
# Check-level decisions for full-audit packets: the human records
# their own P1-P3 booleans (appliable to plan verdicts), never an
# assessment label. Separate schema so the two can never mix.
AUDIT_DECISIONS_SCHEMA = "chimera-audit-decisions/1"
AUDIT_CHECKS = ("P1", "P2", "P3")
# Seed for the reviewer-facing driver-code shuffle. Fixed and
# recorded so the mapping is reproducible; the mapping itself lives
# in the packet (answer-side, like recorded verdicts) and is masked
# in the review UI until each episode is revealed.
DRIVER_CODE_SEED = "audit-full-v1-driver-codes"

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
                   cell_key: str, bundle: Dict[str, Any],
                   neutral_gaps: bool = False,
                   manifest_ref: Optional[Dict[str, str]] = None,
                   population: Optional[str] = None,
                   driver_code: Optional[str] = None) -> Dict[str, Any]:
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
        gaps.append(("step report carries step indexes only — no "
                     "timestamps or trace sequence numbers"
                     if neutral_gaps else
                     "replay driver report carries step indexes only — no "
                     "timestamps or trace sequence numbers"))
    if verification.get("status") != "verified":
        gaps.append("independent verification status is "
                    f"{verification.get('status')!r} rather than 'verified'")
    episode = {
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
    # Optional full-audit fields — omitted entirely when unset so the
    # frozen 8-episode mini packet shape is unchanged.
    if manifest_ref is not None:
        episode["manifest"] = dict(manifest_ref)
    if population is not None:
        episode["population"] = population
    if driver_code is not None:
        episode["driver_code"] = driver_code
    return episode


def _driver_codes(run_ids: List[str]) -> Dict[str, str]:
    """Map run ids to neutral Driver A/B/… codes in seeded-shuffle order.

    The shuffle hides the packet's presentation order (which groups
    episodes by population and run, as the review queue requires) from
    the reviewer-facing label. Deterministic and documented; the
    mapping is recorded in the packet (answer-side) and masked in the
    review UI until each episode is revealed.
    """
    ordered = sorted(run_ids,
                     key=lambda r: _sha256_bytes(
                         f"{DRIVER_CODE_SEED}:{r}".encode()))
    return {run_id: f"Driver {chr(ord('A') + i)}"
            for i, run_id in enumerate(ordered)}


def build_packet(plan_run_pairs: List[Tuple[Path, Path]], manifest_path: Path,
                 out_dir: Path, expect: int = 8,
                 created_at: Optional[str] = None,
                 manifests: Optional[List[Path]] = None,
                 run_order: Optional[List[str]] = None,
                 populations: Optional[List[str]] = None,
                 neutral_gaps: bool = False,
                 assign_driver_codes: bool = False,
                 title: Optional[str] = None,
                 check_level: bool = False) -> Dict[str, Any]:
    """Verify the frozen selection and write the review packet.

    All parameters after ``created_at`` are optional extensions for
    consolidated full-audit packets; omitting them reproduces the
    original 8-episode mini packet shape exactly.
    """
    manifest_paths = ([manifest_path] * len(plan_run_pairs)
                      if manifests is None else list(manifests))
    if len(manifest_paths) != len(plan_run_pairs):
        raise PacketError(
            f"need one manifest per plan/run pair "
            f"({len(plan_run_pairs)} pairs, "
            f"{len(manifest_paths)} manifests)")
    if populations is not None and len(populations) != len(plan_run_pairs):
        raise PacketError(
            f"need one population label per plan/run pair "
            f"({len(plan_run_pairs)} pairs, "
            f"{len(populations)} labels)")
    primary_manifest: Optional[Manifest] = None
    primary_sha = ""
    manifest_blocks: List[Dict[str, str]] = []
    manifest_refs: List[Dict[str, str]] = []
    for manifest_path_i in manifest_paths:
        manifest = load_manifest(manifest_path_i)
        ref = {"path": _rel(manifest_path_i),
               "manifest_id": manifest.manifest_id,
               "sha256": manifest.sha256()}
        manifest_blocks.append(ref)
        manifest_refs.append(ref)
        if primary_manifest is None:
            primary_manifest, primary_sha = manifest, manifest.sha256()
    assert primary_manifest is not None
    run_ids = [str(_read_json(p).get("run_id")) for p, _ in plan_run_pairs]
    codes = _driver_codes(run_ids) if assign_driver_codes else {}
    episodes: List[Dict[str, Any]] = []
    plan_infos = []
    for i, (plan_path, run_path) in enumerate(plan_run_pairs):
        load_plan(plan_path)  # validates shape, incl. empty verdict maps
        plan = _read_json(plan_path)
        run = _read_json(run_path)
        if plan.get("run_id") != run.get("run_id"):
            raise PacketError(f"{plan_path.name} names run "
                              f"{plan.get('run_id')} but was paired with "
                              f"{run.get('run_id')}")
        for label, value in (("plan", plan.get("manifest_sha256")),
                             ("run", run.get("manifest_sha256"))):
            if value != manifest_blocks[i]["sha256"]:
                raise PacketError(
                    f"{plan_path.name}: {label} manifest sha does not match "
                    f"the frozen {manifest_paths[i]} "
                    f"({manifest_blocks[i]['sha256'][:12]}…)")
        plan_infos.append({
            "path": _rel(plan_path),
            "sha256": _sha256_bytes(_read_bytes(plan_path)),
            "run_id": plan.get("run_id"),
            "sample_size": plan.get("sample_size"),
        })
        for cell_key in sorted(plan.get("cells", {})):
            for bundle in plan["cells"][cell_key].get("sampled", []):
                episodes.append(_build_episode(
                    plan["run_id"], run, plan_path, cell_key, bundle,
                    neutral_gaps=neutral_gaps,
                    manifest_ref=(manifest_refs[i]
                                  if manifests is not None else None),
                    population=(populations[i]
                                if populations is not None else None),
                    driver_code=codes.get(plan["run_id"])))
    if len(episodes) != expect:
        raise PacketError(f"expected exactly {expect} sampled episodes, "
                          f"found {len(episodes)} — refusing to repackage a "
                          f"different selection")
    if run_order is not None:
        rank = {run_id: n for n, run_id in enumerate(run_order)}
        unknown = [e["run_id"] for e in episodes
                   if e["run_id"] not in rank]
        if unknown:
            raise PacketError(
                f"run_order omits episodes from run(s) "
                f"{sorted(set(unknown))} — refusing a partial order")
        episodes.sort(key=lambda e: (rank[e["run_id"]], e["trial_id"]))
    else:
        episodes.sort(key=lambda e: (e["run_id"], e["trial_id"]))
    packet = {
        "schema": PACKET_SCHEMA,
        "created_at": created_at or _utcnow(),
        "manifest": manifest_blocks[0],
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
    # Optional full-audit keys — absent from the mini packet entirely.
    if title is not None:
        packet["title"] = title
    if manifests is not None:
        packet["manifests"] = manifest_blocks
    if populations is not None:
        packet["populations"] = [
            {"run_id": run_id, "label": populations[i]}
            for i, run_id in enumerate(run_ids)]
    if codes:
        packet["driver_codes"] = [
            {"run_id": run_id, "code": codes[run_id]}
            for run_id in run_ids]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "packet.json").write_text(_dump_canonical(packet),
                                         encoding="utf-8")
    (out_dir / "PACKET.md").write_text(render_packet_markdown(packet),
                                       encoding="utf-8")
    _write_initial_decisions(
        out_dir, AUDIT_DECISIONS_SCHEMA if check_level else DECISIONS_SCHEMA)
    return packet


def _decision_is_recorded(decision: Any) -> bool:
    if not isinstance(decision, dict):
        return False
    return bool(decision.get("assessment") or decision.get("checks") or
                decision.get("verdict"))


def _write_initial_decisions(out_dir: Path,
                             schema: str = DECISIONS_SCHEMA) -> None:
    target = out_dir / "decisions.json"
    packet_sha = _sha256_bytes((out_dir / "packet.json").read_bytes())
    initial = {
        "schema": schema,
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
                    if _decision_is_recorded(v)]
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
    n = len(packet["episodes"])
    titled = bool(packet.get("title"))
    lines = [
        f"# {packet['title']}" if titled
        else "# Eval mini-review packet (8 episodes)",
        "",
        (f"Created: {packet['created_at']} · schema `{packet['schema']}` · "
         f"{n} episode{'s' if n != 1 else ''}." if titled else
         f"Created: {packet['created_at']} · schema `{packet['schema']}`."),
        "This packet is a read-only view of frozen evidence plus empty "
        "decision slots. All judgments live in `decisions.json`, recorded "
        "only by a human reviewer.",
        "",
    ]
    for m in packet.get("manifests", [packet["manifest"]]):
        lines += [
            f"Manifest: `{m['path']}` ({m['manifest_id']}, "
            f"sha256 `{m['sha256']}` — verified against the "
            "frozen file at packet build).",
            "",
        ]
    if packet.get("populations"):
        lines += ["Populations (separate denominators — never pooled):", ""]
        for pop in packet["populations"]:
            pop_n = sum(1 for e in packet["episodes"]
                        if e.get("population") == pop["label"] and
                        e["run_id"] == pop["run_id"])
            lines.append(f"- **{pop['label']}** — run `{pop['run_id']}` · "
                         f"{pop_n} episode{'s' if pop_n != 1 else ''}")
        lines += [""]
    lines += [
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
        tag = ""
        if titled and (ep.get("population") or ep.get("driver_code")):
            tag = (f"[{ep.get('population', '?')} · "
                   f"{ep.get('driver_code', '?')}] ")
        lines.append(
            f"{i}. {tag}`{ep['key']}` — {ep['scenario_id']}/{ep['input_id']} · "
            f"baseline `{ep['baseline']}` · expected "
            f"{ep['expected_stored_name']!r} · recorded "
            f"`{ep['recorded']['outcome']}` · plan `{ep['plan']}` "
            f"cell `{ep['plan_cell']}`")
    lines += ["", "## Episodes", ""]
    for ep in packet["episodes"]:
        lines += [
            f"### `{ep['key']}`",
            "",
        ]
        if titled and ep.get("population"):
            m = ep.get("manifest") or {}
            lines.append(
                f"- Population: {ep['population']} · "
                f"{ep.get('driver_code', '?')} · manifest "
                f"`{m.get('path', '?')}` "
                f"(`{m.get('manifest_id', '?')}`)")
        lines += [
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
    if titled:
        lines += [
            "## Review protocol",
            "",
            "1. Assess each episode blinded (driver identity, recorded "
            "outcome, and verifier checks masked): record your own "
            "true/false judgment for P1, P2, and P3 from the "
            "postconditions and the evidence above — never from success "
            "strings or the verifier's status.",
            "2. If the evidence cannot support a judgment, mark the "
            "episode unauditable with an explicit reason tied to specific "
            "observations.",
            "3. Reveal the recorded verdict only after saving your own "
            "decision.",
            "4. Export `decisions.json` and validate it with "
            "`tools/mini_review.py validate --dir <packet-dir>`.",
            "5. Apply validated decisions to the audit plans with "
            "`tools/mini_review.py apply-verdicts --packet <packet-dir>` "
            "(dry-run first; `--write` only after review is complete).",
            "",
            "Populations stay separate: agreement is computed per "
            "population and per run, never pooled across experiments. The "
            "95% provisional rule (user guide §15.1 step 4) applies per "
            "population once its required sample is fully adjudicated.",
            "",
        ]
    else:
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


def _audit_decision_errors(key: str, packet_keys: set,
                           decision: Any, n: int) -> List[str]:
    """Check-level decision validation (full-audit packets)."""
    errors = []
    if key not in packet_keys:
        errors.append(f"{key}: not one of the {n} packet episodes")
        return errors
    if not isinstance(decision, dict):
        return [f"{key}: decision must be an object"]
    get = decision.get
    if get("verdict") == "unauditable":
        if (not isinstance(get("reason"), str)
                or not get("reason").strip()):
            errors.append(f"{key}: unauditable verdicts need a non-empty "
                          f"reason")
        if "checks" in decision:
            errors.append(f"{key}: unauditable verdicts must not carry "
                          f"checks")
    else:
        checks = get("checks")
        if not isinstance(checks, dict):
            errors.append(f"{key}: checks must be an object keyed by "
                          f"{list(AUDIT_CHECKS)}")
        else:
            if set(checks) != set(AUDIT_CHECKS):
                errors.append(
                    f"{key}: checks must cover exactly {list(AUDIT_CHECKS)}, "
                    f"got {sorted(checks)}")
            for cid in AUDIT_CHECKS:
                if cid in checks and not isinstance(checks[cid], bool):
                    errors.append(f"{key}: checks.{cid} must be a JSON "
                                  f"boolean, got {checks[cid]!r}")
    if "note" in decision and not isinstance(get("note"), str):
        errors.append(f"{key}: note must be a string")
    assessed = _parse_iso(get("assessed_at"))
    if assessed is None:
        errors.append(f"{key}: assessed_at must be an ISO-8601 timestamp "
                      f"with timezone")
    revealed = _parse_iso(get("revealed_at")) if get("revealed_at") else None
    if get("revealed_at") and revealed is None:
        errors.append(f"{key}: revealed_at must be null or an ISO-8601 "
                      f"timestamp with timezone")
    expected_blind = revealed is None or (
        assessed is not None and assessed <= revealed)
    if get("blinded") is not expected_blind:
        errors.append(f"{key}: blinded flag is inconsistent with the "
                      f"assessment/reveal timestamps")
    return errors


def validate_decisions(packet: Dict[str, Any],
                       decisions: Dict[str, Any]) -> List[str]:
    """Schema + resolution + protocol validation. Returns error list."""
    errors = []
    audit_mode = decisions.get("schema") == AUDIT_DECISIONS_SCHEMA
    if decisions.get("schema") not in (DECISIONS_SCHEMA,
                                       AUDIT_DECISIONS_SCHEMA):
        errors.append(f"schema must be {DECISIONS_SCHEMA} or "
                      f"{AUDIT_DECISIONS_SCHEMA}")
    packet_sha = _sha256_bytes(_dump_canonical(packet).encode("utf-8"))
    if decisions.get("packet_sha256") not in (None, packet_sha):
        errors.append("packet_sha256 does not match the loaded packet — "
                      "decisions were recorded against different bytes")
    packet_keys = {e["key"] for e in packet.get("episodes", [])}
    entries = decisions.get("decisions")
    if not isinstance(entries, dict):
        return errors + ["decisions must be an object keyed by episode"]
    for key, decision in entries.items():
        if audit_mode:
            errors.extend(_audit_decision_errors(
                key, packet_keys, decision, len(packet_keys)))
        else:
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


def _recorded_check_map(ep: Dict[str, Any]) -> Optional[Dict[str, bool]]:
    """Verifier checks from the packet as {P1..P3: bool}, or None."""
    raw = (ep.get("verifier") or {}).get("checks")
    if not isinstance(raw, list):
        return None
    mapped = {}
    for c in raw:
        if not isinstance(c, dict):
            return None
        pid, sat = c.get("postcondition_id"), c.get("satisfied")
        if pid not in AUDIT_CHECKS or not isinstance(sat, bool):
            return None
        mapped[pid] = sat
    return mapped if set(mapped) == set(AUDIT_CHECKS) else None


def summarize_audit(packet: Dict[str, Any],
                    decisions: Dict[str, Any]) -> Dict[str, Any]:
    """Per-episode human-vs-recorded comparison, grouped by population.

    Agreement is strict per-check equality of the human's own P1–P3
    booleans against the recorded verifier checks. Counts are kept
    per population and per run — never pooled across experiments.
    """
    by_key = {e["key"]: e for e in packet.get("episodes", [])}
    entries = decisions.get("decisions", {})
    rows = []
    for key in sorted(by_key):
        ep = by_key[key]
        dec = entries.get(key) if isinstance(entries, dict) else None
        recorded_map = _recorded_check_map(ep)
        recorded = (", ".join(
            f"{c}={'T' if recorded_map[c] else 'F'}"
            for c in AUDIT_CHECKS) if recorded_map else "—")
        human_checks = (dec or {}).get("checks")
        if not isinstance(dec, dict) or (
                not isinstance(human_checks, dict)
                and dec.get("verdict") != "unauditable"):
            agreement, human = "pending", "pending"
        elif dec.get("verdict") == "unauditable":
            agreement, human = "unauditable", "unauditable"
        elif recorded_map is None:
            agreement = "undetermined"
            human = ", ".join(f"{c}={'T' if human_checks.get(c) else 'F'}"
                              for c in AUDIT_CHECKS)
        else:
            same = all(human_checks.get(c) == recorded_map[c]
                       for c in AUDIT_CHECKS)
            agreement = "agrees" if same else "disagrees"
            human = ", ".join(f"{c}={'T' if human_checks.get(c) else 'F'}"
                              for c in AUDIT_CHECKS)
        rows.append({
            "key": key,
            "population": ep.get("population") or "(unlabeled)",
            "driver_code": ep.get("driver_code") or ep.get("run_id"),
            "run_id": ep["run_id"],
            "recorded_checks": recorded,
            "human": human,
            "agreement": agreement,
            "blinded": (dec or {}).get("blinded", "pending"),
        })
    pops: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        pop = pops.setdefault(r["population"], {"runs": {}})
        run = pop["runs"].setdefault(r["run_id"], {
            "total": 0, "recorded": 0, "agrees": 0, "disagrees": 0,
            "undetermined": 0, "unauditable": 0})
        run["total"] += 1
        if r["agreement"] != "pending":
            run["recorded"] += 1
            run[r["agreement"]] += 1
    recorded_n = sum(1 for r in rows if r["agreement"] != "pending")
    return {
        "reviewer": decisions.get("reviewer") or "(unrecorded)",
        "recorded": recorded_n, "total": len(rows),
        "complete": recorded_n == len(rows) and bool(decisions.get("reviewer")),
        "populations": [
            {"label": label,
             "runs": [{"run_id": rid, **counts}
                      for rid, counts in sorted(data["runs"].items())]}
            for label, data in sorted(pops.items())],
        "rows": rows,
    }


def render_audit_summary(packet: Dict[str, Any],
                         decisions: Dict[str, Any]) -> str:
    summary = summarize_audit(packet, decisions)
    n = summary["total"]
    title = packet.get("title") or "Audit review"
    lines = [
        f"{title}: {summary['recorded']}/{n} recorded · "
        f"reviewer: {summary['reviewer']}",
        "",
        "Agreement is strict per-check equality, kept per population "
        "and per run — never pooled across experiments.",
        "",
    ]
    for pop in summary["populations"]:
        lines.append(f"## {pop['label']}")
        for run in pop["runs"]:
            lines.append(
                f"- `{run['run_id']}`: {run['recorded']}/{run['total']} "
                f"recorded · agrees {run['agrees']} · disagrees "
                f"{run['disagrees']} · undetermined {run['undetermined']} · "
                f"unauditable {run['unauditable']}")
        lines.append("")
    flagged = [r for r in summary["rows"]
               if r["agreement"] in ("disagrees", "undetermined",
                                     "unauditable")]
    if flagged:
        lines.append("Episodes needing attention (disagree / undetermined / "
                     "unauditable):")
        for r in flagged:
            lines.append(f"- `{r['key']}` [{r['population']} · "
                         f"{r['driver_code']}] {r['agreement']}: human "
                         f"{r['human']} vs recorded {r['recorded_checks']}")
        lines.append("")
    lines += [
        "Status: " + (f"COMPLETE — {n}/{n} human decisions recorded."
                      if summary["complete"] else
                      "IN PROGRESS — pending decisions remain; nothing is "
                      "complete until a human records all "
                      f"{n}."),
        "Caveat: do not run this summary until your own decisions are "
        "saved — it prints the recorded verifier checks. The 95% "
        "provisional rule (user guide §15.1 step 4) applies per "
        "population once its required sample is fully adjudicated.",
    ]
    return "\n".join(lines)


def render_summary(packet: Dict[str, Any], decisions: Dict[str, Any]) -> str:
    if decisions.get("schema") == AUDIT_DECISIONS_SCHEMA:
        return render_audit_summary(packet, decisions)
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

#: Top-level repo dirs used to re-root absolute evidence paths.
_REPO_TOP_DIRS = ("artifacts", "data", "benchmarks", "demo_app", "docs",
                  "experiments", "research", "site", "workbench",
                  "adapters", "chimera", "tests", "tools")


def _resolve_evidence_path(rel: str):
    """Resolve a packet path to a file in THIS checkout.

    Frozen evidence records absolute paths from the machine that ran
    it. On another checkout those paths escape ``PROJECT_DIR``; re-root
    the stable repo-relative suffix instead. Integrity never comes
    from the path: the caller's sha/bytes check still has to match.
    Returns ``None`` when no file resolves.
    """
    candidate = Path(rel)
    if not candidate.is_absolute():
        source = PROJECT_DIR / candidate
        return source if source.is_file() else None
    parts = candidate.parts
    for i, part in enumerate(parts):
        if part in _REPO_TOP_DIRS:
            source = PROJECT_DIR.joinpath(*parts[i:])
            return source if source.is_file() else None
    return None


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
        source = _resolve_evidence_path(rel)
        if source is None:
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
            arc = str(source.relative_to(PROJECT_DIR))
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
    scrub_ids = bool(packet.get("populations"))
    for ep in packet.get("episodes", []):
        evidence = ep["evidence"]
        if scrub_ids:
            # Snapshot run_id is driver identity with no mapping role
            # (the episode key/run_id already maps decisions back), so
            # audit reviewer files drop it. Mini packets keep evidence
            # byte-identical.
            evidence = dict(evidence)
            snap = dict(evidence.get("snapshot") or {})
            snap.pop("run_id", None)
            evidence["snapshot"] = snap
        rep = {
            "key": ep["key"], "run_id": ep["run_id"],
            "trial_id": ep["trial_id"], "plan": ep["plan"],
            "plan_cell": ep["plan_cell"], "baseline": ep["baseline"],
            "scenario_id": ep["scenario_id"], "input_id": ep["input_id"],
            "expected_stored_name": ep["expected_stored_name"],
            "evidence": evidence, "artifacts": ep["artifacts"],
            "gaps": [g for g in ep.get("gaps", [])
                     if "verification status" not in g],
        }
        # Optional full-audit fields — present-only, so the mini
        # reviewer packet is unchanged.
        for extra in ("manifest", "population", "driver_code"):
            if extra in ep:
                rep[extra] = ep[extra]
        episodes.append(rep)
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
    for extra in ("title", "manifests", "populations", "driver_codes"):
        if extra in packet:
            reviewer[extra] = packet[extra]
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


# -- applying verdicts -------------------------------------------------

def plan_verdict_updates(
        packet: Dict[str, Any],
        decisions: Dict[str, Any]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Map validated audit decisions to plan verdicts.

    Returns ``{plan_relpath: {cell_key: {trial_id: verdict_json}}}``
    in the exact shapes :func:`benchmarks.audit.apply_audit` consumes.
    Callers must run :func:`validate_decisions` first and refuse on
    any error; this function re-checks episode membership defensively.
    """
    if decisions.get("schema") != AUDIT_DECISIONS_SCHEMA:
        raise PacketError(
            f"apply-verdicts needs {AUDIT_DECISIONS_SCHEMA} decisions, got "
            f"{decisions.get('schema')}")
    by_key = {e["key"]: e for e in packet.get("episodes", [])}
    updates: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for key, dec in (decisions.get("decisions") or {}).items():
        ep = by_key.get(key)
        if ep is None:
            raise PacketError(f"{key}: not a packet episode — refusing")
        if not isinstance(dec, dict):
            raise PacketError(f"{key}: decision must be an object — refusing")
        if dec.get("verdict") == "unauditable":
            verdict: Dict[str, Any] = {"verdict": "unauditable",
                                       "reason": dec.get("reason", "")}
        else:
            checks = dec.get("checks") or {}
            verdict = {"checks": {c: checks[c] for c in AUDIT_CHECKS},
                       "note": dec.get("note", "")}
        cell = updates.setdefault(ep["plan"], {}).setdefault(
            ep["plan_cell"], {})
        if ep["trial_id"] in cell:
            raise PacketError(
                f"{key}: duplicate trial {ep['trial_id']} in plan cell "
                f"{ep['plan_cell']} — refusing")
        cell[ep["trial_id"]] = verdict
    return updates


# -- CLI ---------------------------------------------------------------

def _default_out() -> Path:
    return PROJECT_DIR / DEFAULT_OUT


def cmd_build_packet(args: argparse.Namespace) -> int:
    if len(args.plans) != len(args.runs):
        print(f"mini_review: {len(args.plans)} plans but {len(args.runs)} "
              f"runs — refusing", file=sys.stderr)
        return 1
    pairs = list(zip(args.plans, args.runs))
    manifests = ([PROJECT_DIR / m for m in args.manifests]
                 if args.manifests else None)
    try:
        packet = build_packet(
            [(PROJECT_DIR / p, PROJECT_DIR / r) for p, r in pairs],
            PROJECT_DIR / args.manifest, PROJECT_DIR / args.out,
            expect=args.expect, created_at=args.created_at,
            manifests=manifests, run_order=args.order,
            populations=args.populations, neutral_gaps=args.neutral_gaps,
            assign_driver_codes=args.driver_codes, title=args.title,
            check_level=args.check_level)
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


def cmd_apply_verdicts(args: argparse.Namespace) -> int:
    packet_dir = PROJECT_DIR / args.packet
    decisions_path = Path(args.decisions) if args.decisions else None
    if decisions_path is None:
        decisions_path = packet_dir / "decisions.json"
    elif not decisions_path.is_absolute():
        decisions_path = PROJECT_DIR / decisions_path
    try:
        packet = json.loads(
            (packet_dir / "packet.json").read_text(encoding="utf-8"))
        decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
    except OSError as exc:
        print(f"mini_review: cannot read input: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"mini_review: invalid JSON: {exc}", file=sys.stderr)
        return 1
    errors = validate_decisions(packet, decisions)
    if errors:
        print("INVALID — refusing to apply:")
        for err in errors:
            print(f"  - {err}")
        return 1
    try:
        updates = plan_verdict_updates(packet, decisions)
    except PacketError as exc:
        print(f"mini_review: {exc}", file=sys.stderr)
        return 1
    total = sum(len(trials)
                for cells in updates.values() for trials in cells.values())
    if not total:
        print("mini_review: no decisions recorded — nothing to apply",
              file=sys.stderr)
        return 1
    for rel in sorted(updates):
        n = sum(len(t) for t in updates[rel].values())
        cells = len(updates[rel])
        print(f"  {rel}: {n} verdict(s) across {cells} cell(s)")
    if not args.write:
        print(f"dry run: {total} verdict(s) would merge into "
              f"{len(updates)} plan(s) — no files written. Re-run with "
              f"--write to merge.")
        return 0
    # Check every conflict before writing anything.
    staged: List[Tuple[Path, Dict[str, Any]]] = []
    conflicts = []
    for rel in sorted(updates):
        plan_path = PROJECT_DIR / rel
        try:
            load_plan(plan_path)
            raw = _read_json(plan_path)
        except (AuditError, PacketError, ValueError) as exc:
            print(f"mini_review: cannot load {rel}: {exc}", file=sys.stderr)
            return 1
        for cell_key, trials in updates[rel].items():
            if cell_key not in (raw.get("cells") or {}):
                print(f"mini_review: {rel} has no cell {cell_key} — refusing",
                      file=sys.stderr)
                return 1
            have = raw["cells"][cell_key].get("verdicts") or {}
            for trial_id, verdict in trials.items():
                if trial_id in have and have[trial_id] != verdict:
                    conflicts.append(f"{rel} {cell_key} {trial_id}")
        staged.append((plan_path, raw))
    if conflicts:
        print("mini_review: refusing to overwrite existing verdicts:",
              file=sys.stderr)
        for c in conflicts:
            print(f"  - {c}", file=sys.stderr)
        return 1
    for (plan_path, raw), rel in zip(staged, sorted(updates)):
        for cell_key, trials in updates[rel].items():
            raw["cells"][cell_key].setdefault("verdicts", {}).update(trials)
        plan_path.write_text(_dump_canonical(raw), encoding="utf-8")
        load_plan(plan_path)  # re-validates incl. verdict shapes
    print(f"merged {total} verdict(s) into {len(staged)} plan(s)")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mini_review.py",
        description="Build eval review packets; validate human "
                    "decisions; apply verdicts to audit plans.")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build-packet", help="verify + write the packet")
    build.add_argument("--plans", nargs="+", metavar="PLAN",
                       default=[p for p, _ in DEFAULT_PAIRS])
    build.add_argument("--runs", nargs="+", metavar="RUN",
                       default=[r for _, r in DEFAULT_PAIRS])
    build.add_argument("--manifest", default=DEFAULT_MANIFEST)
    build.add_argument("--manifests", nargs="+", metavar="MANIFEST",
                       default=None,
                       help="one manifest per plan/run pair (multi-manifest "
                            "packets); overrides --manifest")
    build.add_argument("--order", nargs="+", metavar="RUN_ID", default=None,
                       help="run ids in presentation order")
    build.add_argument("--populations", nargs="+", metavar="LABEL",
                       default=None,
                       help="one population label per plan/run pair")
    build.add_argument("--neutral-gaps", action="store_true",
                       help="neutralize driver-revealing gap wording")
    build.add_argument("--driver-codes", action="store_true",
                       help="assign neutral Driver A/B/… codes")
    build.add_argument("--title", default=None)
    build.add_argument("--check-level", action="store_true",
                       help="check-level decisions (appliable to plans)")
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
    apply = sub.add_parser("apply-verdicts",
                           help="merge decisions into plan verdicts "
                                "(dry run unless --write)")
    apply.add_argument("decisions", nargs="?",
                       default=None,
                       help="decisions file (default: <packet>/decisions.json)")
    apply.add_argument("--packet", default=DEFAULT_OUT)
    apply.add_argument("--write", action="store_true",
                       help="merge into the plan files (default is dry run)")
    apply.set_defaults(func=cmd_apply_verdicts)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
