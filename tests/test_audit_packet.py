"""Tests for consolidated full-audit packets (multi-manifest, blinded,
check-level) and the verdict applier.

Builds go to tmp_path using the frozen 8-episode mini plans/runs as a
fast stand-in selection; the real 184-episode packet is only read, never
rebuilt or modified, by the inventory test. Failure-mode tests use tmp
copies of plans with single-field mutations.
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from tools.mini_review import (
    AUDIT_CHECKS,
    AUDIT_DECISIONS_SCHEMA,
    DECISIONS_SCHEMA,
    PacketError,
    build_packet,
    build_reviewer_packet,
    cmd_apply_verdicts,
    plan_verdict_updates,
    render_packet_markdown,
    render_summary,
    summarize_audit,
    validate_decisions,
)

ROOT = Path(__file__).resolve().parent.parent
CHIMERA_PLAN = ROOT / "artifacts/eval-20261028/run-chimera.audit-plan-mini.json"
CHIMERA_RUN = ROOT / "artifacts/eval-20261028/run-chimera.json"
BASELINE_PLAN = ROOT / "artifacts/eval-20261028/run-baseline-a.audit-plan-mini.json"
BASELINE_RUN = ROOT / "artifacts/eval-20261028/run-baseline-a.json"
MANIFEST = ROOT / "benchmarks/manifests/eval-v1.json"
FULL_PACKET = ROOT / "artifacts/audit-full-v1/review/packet.json"

FIXED_AT = "2026-10-29T00:00:00.000+00:00"
POPS = ["primary evaluation (eval-20261028)",
        "matched-budget follow-up (mb-v1)"]
ORDER = ["eval-20261028-baseline-a", "eval-20261028-chimera"]


def _audit_build(out, **kw):
    kw.setdefault("created_at", FIXED_AT)
    kw.setdefault("manifests", [MANIFEST, MANIFEST])
    kw.setdefault("run_order", ORDER)
    kw.setdefault("populations", POPS)
    kw.setdefault("neutral_gaps", True)
    kw.setdefault("assign_driver_codes", True)
    kw.setdefault("title", "Audit packet test")
    kw.setdefault("check_level", True)
    return build_packet(
        [(CHIMERA_PLAN, CHIMERA_RUN), (BASELINE_PLAN, BASELINE_RUN)],
        MANIFEST, out, expect=8, **kw)


def _good_checks(**kw):
    dec = {"checks": {"P1": True, "P2": True, "P3": True}, "note": "",
           "blinded": True,
           "assessed_at": "2026-10-30T10:00:00.000+00:00",
           "revealed_at": None}
    dec.update(kw)
    return dec


def _decisions(packet, entries, reviewer="ann"):
    sha = hashlib.sha256(json.dumps(
        packet, sort_keys=True, ensure_ascii=False, indent=2
    ).encode() + b"\n").hexdigest()
    return {"schema": AUDIT_DECISIONS_SCHEMA, "packet": "packet.json",
            "packet_sha256": sha, "reviewer": reviewer,
            "exported_at": None, "decisions": entries}


def test_build_audit_packet_multi_manifest(tmp_path):
    packet = _audit_build(tmp_path)
    assert len(packet["episodes"]) == 8
    assert packet["title"] == "Audit packet test"
    # Presentation order follows run_order, not run-id sort.
    assert [e["run_id"] for e in packet["episodes"]] == (
        ["eval-20261028-baseline-a"] * 4 + ["eval-20261028-chimera"] * 4)
    assert [m["manifest_id"] for m in packet["manifests"]] == [
        "eval-v1", "eval-v1"]
    assert packet["manifest"] == packet["manifests"][0]
    assert [(p["run_id"], p["label"]) for p in packet["populations"]] == [
        ("eval-20261028-chimera", POPS[0]),
        ("eval-20261028-baseline-a", POPS[1])]
    codes = {c["run_id"]: c["code"] for c in packet["driver_codes"]}
    assert sorted(codes.values()) == ["Driver A", "Driver B"]
    for ep in packet["episodes"]:
        assert ep["manifest"]["manifest_id"] == "eval-v1"
        assert ep["population"] in POPS
        assert ep["driver_code"] == codes[ep["run_id"]]
        for gap in ep["gaps"]:
            assert "replay driver" not in gap.lower()
    assert any("step report carries step indexes" in g
               for e in packet["episodes"] for g in e["gaps"])
    initial = json.loads((tmp_path / "decisions.json").read_text())
    assert initial["schema"] == AUDIT_DECISIONS_SCHEMA
    assert initial["decisions"] == {}


def test_driver_codes_deterministic(tmp_path):
    first = _audit_build(tmp_path / "a")["driver_codes"]
    second = _audit_build(tmp_path / "b")["driver_codes"]
    assert first == second


def test_build_packet_rejects_bad_run_order(tmp_path):
    try:
        _audit_build(tmp_path, run_order=["eval-20261028-chimera"])
    except PacketError as exc:
        assert "omits episodes" in str(exc)
    else:
        raise AssertionError("partial run_order accepted")


def test_audit_decision_validation(tmp_path):
    packet = _audit_build(tmp_path)
    keys = [e["key"] for e in packet["episodes"]]
    good = _decisions(packet, {keys[0]: _good_checks()})
    assert validate_decisions(packet, good) == []
    missing = dict(_good_checks())
    del missing["checks"]["P3"]
    assert validate_decisions(
        packet, _decisions(packet, {keys[0]: missing}))
    nonbool = _good_checks(checks={"P1": True, "P2": "yes", "P3": False})
    errs = validate_decisions(packet, _decisions(packet, {keys[0]: nonbool}))
    assert any("must be a JSON boolean" in e for e in errs)
    noreason = {"verdict": "unauditable", "reason": "  ",
                "blinded": True,
                "assessed_at": "2026-10-30T10:00:00.000+00:00",
                "revealed_at": None}
    errs = validate_decisions(packet, _decisions(packet, {keys[0]: noreason}))
    assert any("non-empty reason" in e for e in errs)
    both = _good_checks()
    both["verdict"] = "unauditable"
    both["reason"] = "x"
    errs = validate_decisions(packet, _decisions(packet, {keys[0]: both}))
    assert any("must not carry checks" in e for e in errs)
    errs = validate_decisions(
        packet, _decisions(packet, {"nope::t": _good_checks()}))
    assert any("not one of the 8 packet episodes" in e for e in errs)
    wrong_schema = _decisions(packet, {keys[0]: _good_checks()})
    wrong_schema["schema"] = DECISIONS_SCHEMA
    errs = validate_decisions(packet, wrong_schema)
    assert any("checks" in e or "assessment" in e for e in errs)


def test_summarize_audit_never_pools(tmp_path):
    packet = _audit_build(tmp_path)
    by_run = {}
    for e in packet["episodes"]:
        by_run.setdefault(e["run_id"], []).append(e["key"])
    chim_keys = by_run["eval-20261028-chimera"]
    base_keys = by_run["eval-20261028-baseline-a"]
    by_key = {e["key"]: e for e in packet["episodes"]}
    rec = {c["postcondition_id"]: c["satisfied"]
           for c in by_key[chim_keys[0]]["verifier"]["checks"]}
    agree = _good_checks(checks=dict(rec))
    disagree_checks = dict(rec)
    disagree_checks["P1"] = not disagree_checks["P1"]
    disagree = _good_checks(checks=disagree_checks)
    unaud = {"verdict": "unauditable", "reason": "trace unreadable",
             "blinded": True,
             "assessed_at": "2026-10-30T10:00:00.000+00:00",
             "revealed_at": None}
    decisions = _decisions(packet, {chim_keys[0]: agree,
                                    base_keys[0]: disagree,
                                    base_keys[1]: unaud})
    assert validate_decisions(packet, decisions) == []
    summary = summarize_audit(packet, decisions)
    assert summary["recorded"] == 3 and summary["total"] == 8
    assert [p["label"] for p in summary["populations"]] == sorted(POPS)
    pops = {p["label"]: p for p in summary["populations"]}
    assert pops[POPS[0]]["runs"][0]["agrees"] == 1
    assert pops[POPS[1]]["runs"][0]["disagrees"] == 1
    assert pops[POPS[1]]["runs"][0]["unauditable"] == 1
    text = render_summary(packet, decisions)
    for pop in POPS:
        assert pop in text
    assert "never pooled" in text
    assert base_keys[0] in text  # disagreements are listed explicitly


def test_plan_verdict_updates_shapes(tmp_path):
    from benchmarks.audit import load_plan
    packet = _audit_build(tmp_path)
    by_run = {}
    for e in packet["episodes"]:
        by_run.setdefault(e["run_id"], []).append(e)
    chim_ep = by_run["eval-20261028-chimera"][0]
    base_ep = by_run["eval-20261028-baseline-a"][0]
    unaud = {"verdict": "unauditable", "reason": "snapshot missing",
             "blinded": True,
             "assessed_at": "2026-10-30T10:00:00.000+00:00",
             "revealed_at": None}
    decisions = _decisions(packet, {chim_ep["key"]: _good_checks(note="ok"),
                                    base_ep["key"]: unaud})
    updates = plan_verdict_updates(packet, decisions)
    assert set(updates) == {
        "artifacts/eval-20261028/run-chimera.audit-plan-mini.json",
        "artifacts/eval-20261028/run-baseline-a.audit-plan-mini.json",
    }
    flat = [v for cells in updates.values()
            for trials in cells.values() for v in trials.values()]
    assert len(flat) == 2
    checks_v = [v for v in flat if "checks" in v][0]
    assert set(checks_v["checks"]) == set(AUDIT_CHECKS)
    assert all(isinstance(x, bool) for x in checks_v["checks"].values())
    assert checks_v["note"] == "ok"
    unaud_v = [v for v in flat if v.get("verdict") == "unauditable"][0]
    assert unaud_v["reason"] == "snapshot missing"
    # Shapes must parse as plan verdicts.
    plan_path = tmp_path / "probe-plan.json"
    shutil.copy(CHIMERA_PLAN, plan_path)
    raw = json.loads(plan_path.read_text())
    raw["cells"][chim_ep["plan_cell"]]["verdicts"][
        chim_ep["trial_id"]] = checks_v
    plan_path.write_text(json.dumps(raw, indent=2))
    assert load_plan(plan_path).cells  # parses incl. verdict shapes


def _apply_ns(packet_dir, write):
    return argparse.Namespace(packet=str(packet_dir), decisions=None,
                              write=write)


def test_apply_verdicts_write_and_conflicts(tmp_path, capsys):
    chim_copy = tmp_path / "chimera.plan.json"
    base_copy = tmp_path / "baseline.plan.json"
    shutil.copy(CHIMERA_PLAN, chim_copy)
    shutil.copy(BASELINE_PLAN, base_copy)
    packet = build_packet(
        [(chim_copy, CHIMERA_RUN), (base_copy, BASELINE_RUN)],
        MANIFEST, tmp_path, expect=8, created_at=FIXED_AT,
        manifests=[MANIFEST, MANIFEST], run_order=ORDER,
        populations=POPS, neutral_gaps=True, assign_driver_codes=True,
        title="Audit packet test", check_level=True)
    keys = sorted(e["key"] for e in packet["episodes"])
    decisions = _decisions(packet, {keys[0]: _good_checks(note="first")})
    (tmp_path / "decisions.json").write_text(
        json.dumps(decisions, indent=2, sort_keys=True))
    assert cmd_apply_verdicts(_apply_ns(tmp_path, False)) == 0
    out = capsys.readouterr().out
    assert "dry run" in out and "no files written" in out
    assert json.loads(chim_copy.read_text())["cells"]
    assert cmd_apply_verdicts(_apply_ns(tmp_path, True)) == 0
    chim_got = [v for c in json.loads(chim_copy.read_text())["cells"].values()
                for v in c["verdicts"].values()]
    base_got = [v for c in json.loads(base_copy.read_text())["cells"].values()
                for v in c["verdicts"].values()]
    want = [{"checks": {"P1": True, "P2": True, "P3": True}, "note": "first"}]
    assert chim_got + base_got == want
    assert len(chim_got) + len(base_got) == 1  # exactly one plan touched
    # Re-applying identical verdicts is idempotent.
    assert cmd_apply_verdicts(_apply_ns(tmp_path, True)) == 0
    # Conflicting verdicts refuse without touching either plan.
    changed = _good_checks(
        checks={"P1": False, "P2": True, "P3": True}, note="changed")
    (tmp_path / "decisions.json").write_text(json.dumps(
        _decisions(packet, {keys[0]: changed}), indent=2, sort_keys=True))
    snap = (chim_copy.read_bytes(), base_copy.read_bytes())
    assert cmd_apply_verdicts(_apply_ns(tmp_path, True)) == 1
    assert (chim_copy.read_bytes(), base_copy.read_bytes()) == snap
    assert "refusing to overwrite" in capsys.readouterr().err


def test_reviewer_split_scrubs_snapshot_ids(tmp_path):
    packet = _audit_build(tmp_path)
    reviewer = build_reviewer_packet(
        packet, "0" * 64, tmp_path / "r", created_at=FIXED_AT)
    assert len(reviewer["episodes"]) == 8
    assert reviewer["populations"] and reviewer["driver_codes"]
    for ep in reviewer["episodes"]:
        assert "run_id" not in ep["evidence"]["snapshot"]
        assert ep["population"] in POPS and ep["driver_code"]
    text = (tmp_path / "r" / "reviewer-packet.json").read_text()
    for banned in ('"recorded"', '"verifier"', '"satisfied"'):
        assert banned not in text


def test_render_packet_markdown_audit_sections(tmp_path):
    packet = _audit_build(tmp_path)
    text = render_packet_markdown(packet)
    assert text.startswith("# Audit packet test")
    assert "Populations (separate denominators" in text
    for pop in POPS:
        assert pop in text
    assert "apply-verdicts" in text
    assert "[primary evaluation (eval-20261028) · Driver " in text


def test_full_packet_inventory_readonly():
    packet = json.loads(FULL_PACKET.read_text())
    eps = packet["episodes"]
    assert len(eps) == 184
    counts = {}
    for e in eps:
        counts[e["run_id"]] = counts.get(e["run_id"], 0) + 1
    assert counts == {"eval-20261028-chimera": 72,
                      "eval-20261028-baseline-a": 72,
                      "main-mb-v1-chimera": 8,
                      "main-mb-v1-replay-100": 8,
                      "main-mb-v1-replay-1000": 8,
                      "main-mb-v1-replay-2500": 8,
                      "main-mb-v1-replay-5000": 8}
    pops = {e["population"] for e in eps}
    assert pops == {"primary evaluation (eval-20261028)",
                    "matched-budget follow-up (mb-v1)"}
    assert len({e["driver_code"] for e in eps}) == 7
    mini = json.loads(
        (ROOT / "artifacts/eval-20261028/mini-review/packet.json")
        .read_text())
    assert {e["key"] for e in mini["episodes"]} <= {
        e["key"] for e in eps}
