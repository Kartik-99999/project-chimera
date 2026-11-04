"""Tests for the eval mini-review packet builder and validator.

The generator reads only frozen evidence; tests write packet output
to tmp_path, never to artifacts/. Failure-mode tests use tmp copies
of the real plans with single-field mutations.
"""

import json
from pathlib import Path

import pytest

from tools.mini_review import (
    AGREEMENTS,
    ASSESSMENTS,
    DECISIONS_SCHEMA,
    SUFFICIENCY,
    PacketError,
    build_bundle,
    build_packet,
    build_reviewer_packet,
    render_summary,
    summarize,
    validate_decisions,
)

ROOT = Path(__file__).resolve().parent.parent
CHIMERA_PLAN = ROOT / "artifacts/eval-20261028/run-chimera.audit-plan-mini.json"
CHIMERA_RUN = ROOT / "artifacts/eval-20261028/run-chimera.json"
BASELINE_PLAN = ROOT / "artifacts/eval-20261028/run-baseline-a.audit-plan-mini.json"
BASELINE_RUN = ROOT / "artifacts/eval-20261028/run-baseline-a.json"
MANIFEST = ROOT / "benchmarks/manifests/eval-v1.json"
FROZEN_SHA = "b23580c8c07c3528a33f10f25780138cd58455a1f334c48e4fd889125c038cf5"

FIXED_AT = "2026-10-29T00:00:00.000+00:00"


def _build(out, **kw):
    kw.setdefault("created_at", FIXED_AT)
    return build_packet(
        [(CHIMERA_PLAN, CHIMERA_RUN), (BASELINE_PLAN, BASELINE_RUN)],
        MANIFEST, out, **kw)


def _good_decision(**kw):
    dec = {
        "assessment": "verified-success", "agreement": "agrees",
        "sufficiency": "sufficient", "reason": "snapshot matches P1-P3",
        "missing_evidence": "", "blinded": True,
        "assessed_at": "2026-10-29T10:00:00.000+00:00",
        "revealed_at": "2026-10-29T10:05:00.000+00:00",
        "corrections": [],
    }
    dec.update(kw)
    return dec


def test_build_packet_verifies_frozen_selection(tmp_path):
    packet = _build(tmp_path)
    assert packet["manifest"]["sha256"] == FROZEN_SHA
    assert [(e["run_id"], e["trial_id"]) for e in packet["episodes"]] == sorted(
        (e["run_id"], e["trial_id"]) for e in packet["episodes"])
    keys = {e["key"] for e in packet["episodes"]}
    assert len(keys) == 8
    assert {e["run_id"] for e in packet["episodes"]} == {
        "eval-20261028-chimera", "eval-20261028-baseline-a"}
    # One episode per scenario per baseline (the frozen stratification).
    combos = {(e["run_id"], e["scenario_id"]) for e in packet["episodes"]}
    assert len(combos) == 8
    # Recorded fields resolve to the run files with digests attached.
    for ep in packet["episodes"]:
        assert ep["recorded"]["outcome"] in ("succeeded", "failed")
        assert set(ep["artifacts"]) == {"trace", "snapshot", "actions"}
        for art in ep["artifacts"].values():
            assert len(art["sha256"]) == 64 and art["bytes"] > 0
    assert (tmp_path / "packet.json").is_file()
    assert (tmp_path / "PACKET.md").is_file()
    initial = json.loads((tmp_path / "decisions.json").read_text())
    assert initial["schema"] == DECISIONS_SCHEMA
    assert initial["decisions"] == {} and initial["reviewer"] == ""
    assert validate_decisions(packet, initial) == []
    assert "IN PROGRESS" in render_summary(packet, initial)


def test_build_packet_is_deterministic(tmp_path):
    _build(tmp_path / "a")
    _build(tmp_path / "b")
    assert (tmp_path / "a" / "packet.json").read_bytes() == (
        tmp_path / "b" / "packet.json").read_bytes()
    assert (tmp_path / "a" / "PACKET.md").read_text() == (
        tmp_path / "b" / "PACKET.md").read_text()


def test_build_packet_fails_closed(tmp_path):
    with pytest.raises(PacketError, match="exactly 7"):
        _build(tmp_path, expect=7)
    # Plan paired with the wrong run.
    with pytest.raises(PacketError, match="paired with"):
        build_packet([(CHIMERA_PLAN, BASELINE_RUN)], MANIFEST, tmp_path,
                     expect=8, created_at=FIXED_AT)
    # Tampered digest in a tmp plan copy.
    bad = json.loads(CHIMERA_PLAN.read_text())
    cell = next(c for c in bad["cells"].values() if c["sampled"])
    cell["sampled"][0]["digests"]["trace"] = "0" * 64
    bad_path = tmp_path / "tampered-plan.json"
    bad_path.write_text(json.dumps(bad))
    with pytest.raises(PacketError, match="differ from the plan digest"):
        build_packet([(bad_path, CHIMERA_RUN),
                      (BASELINE_PLAN, BASELINE_RUN)],
                     MANIFEST, tmp_path, expect=8, created_at=FIXED_AT)


def test_build_packet_never_overwrites_recorded_decisions(tmp_path):
    _build(tmp_path)
    target = tmp_path / "decisions.json"
    current = json.loads(target.read_text())
    current["decisions"] = {"eval-20261028-chimera::trial-0006":
                            _good_decision()}
    target.write_text(json.dumps(current))
    with pytest.raises(PacketError, match="refusing to overwrite"):
        _build(tmp_path)
    # A pristine pending file rebuilds identically without complaint.
    _build(tmp_path / "fresh")
    target.write_text((tmp_path / "fresh" / "decisions.json").read_text())
    _build(tmp_path)


def test_validate_decisions_rules(tmp_path):
    packet = _build(tmp_path)
    keys = sorted(e["key"] for e in packet["episodes"])
    packet_sha = json.loads((tmp_path / "packet.json").read_text())
    import hashlib
    sha = hashlib.sha256(
        (tmp_path / "packet.json").read_bytes()).hexdigest()
    assert packet_sha  # packet file exists for the sha binding check

    def doc(decisions, **kw):
        base = {"schema": DECISIONS_SCHEMA, "packet_sha256": sha,
                "reviewer": "ann", "decisions": decisions}
        base.update(kw)
        return base

    full = {k: _good_decision() for k in keys}
    assert validate_decisions(packet, doc(full)) == []
    summary = summarize(packet, doc(full))
    assert summary["complete"] is True and summary["recorded"] == 8
    assert "COMPLETE" in render_summary(packet, doc(full))

    bad_enum = {keys[0]: _good_decision(assessment="maybe")}
    assert validate_decisions(packet, doc(bad_enum))
    unknown = {"nope::t": _good_decision()}
    assert validate_decisions(packet, doc(unknown))
    empty_reason = {keys[0]: _good_decision(reason="  ")}
    assert validate_decisions(packet, doc(empty_reason))
    inconclusive = {keys[0]: _good_decision(assessment="inconclusive",
                                            agreement="undetermined")}
    assert validate_decisions(packet, doc(inconclusive))
    supported = {keys[0]: _good_decision(
        assessment="inconclusive", agreement="undetermined",
        sufficiency="insufficient", missing_evidence="snapshot unreadable")}
    assert validate_decisions(packet, doc(supported)) == []
    unrevealed_agree = {keys[0]: _good_decision(revealed_at=None)}
    assert validate_decisions(packet, doc(unrevealed_agree))
    inconsistent = {keys[0]: _good_decision(
        assessed_at="2026-10-29T10:06:00.000+00:00", blinded=True)}
    assert validate_decisions(packet, doc(inconsistent))
    assert validate_decisions(packet, doc(full, packet_sha256="0" * 64))
    assert validate_decisions(packet, doc(full, schema="wrong"))
    # Corrections require timestamps, previous values, and reasons.
    revised = _good_decision(corrections=[{
        "at": "2026-10-29T11:00:00.000+00:00",
        "previous": {"assessment": "inconclusive"}, "reason": "re-read"}])
    assert validate_decisions(packet, doc({keys[0]: revised})) == []
    broken = _good_decision(corrections=[{"at": "soon"}])
    assert validate_decisions(packet, doc({keys[0]: broken}))
    # Summary never claims reliability and gates completion on reviewer.
    anon = doc(full, reviewer="")
    assert summarize(packet, anon)["complete"] is False
    assert "no reliability claim" in render_summary(packet, anon)


def test_validate_detects_evidence_drift(tmp_path):
    from tools.mini_review import _freshness_errors
    packet = _build(tmp_path)
    assert _freshness_errors(packet) == []
    drifted = json.loads((tmp_path / "packet.json").read_text())
    drifted["episodes"][0]["artifacts"]["trace"]["sha256"] = "0" * 64
    assert _freshness_errors(drifted)


def test_build_bundle_zips_verified_originals_deterministically(tmp_path):
    import hashlib
    import zipfile
    packet = _build(tmp_path)
    out_a = tmp_path / "a.zip"
    out_b = tmp_path / "b.zip"
    manifest = build_bundle(packet, out_a)
    build_bundle(packet, out_b)
    assert out_a.read_bytes() == out_b.read_bytes()
    # 24 episode artifacts + 2 screenshots + manifest + 2 plans.
    assert len(manifest["files"]) == 29
    paths = [f["path"] for f in manifest["files"]]
    assert "benchmarks/manifests/eval-v1.json" in paths
    assert sum(p.endswith(".audit-plan-mini.json") for p in paths) == 2
    assert sum(p.endswith(".png") for p in paths) == 2
    assert sum(p.endswith((".json",)) and "/traces-" in p for p in paths) == 24
    with zipfile.ZipFile(out_a) as zf:
        assert sorted(zf.namelist()) == sorted(
            ["BUNDLE_MANIFEST.json"] + paths)
        for entry in manifest["files"]:
            data = zf.read(entry["path"])
            assert len(data) == entry["bytes"]
            assert hashlib.sha256(data).hexdigest() == entry["sha256"]
        assert json.loads(zf.read("BUNDLE_MANIFEST.json"))["files"] == \
            manifest["files"]


def test_collect_bundle_reroots_absolute_paths(tmp_path, monkeypatch):
    """Absolute evidence paths from another machine resolve here.

    Regression (clone portability): frozen evidence records absolute
    paths, so at any other checkout they escape PROJECT_DIR. The
    bundle re-roots the repo-relative suffix; the recorded sha still
    has to match, so a wrong file fails closed.
    """
    import hashlib
    import shutil

    import tools.mini_review as mr

    root = tmp_path / "checkout"
    trace_rel = "artifacts/eval-20261028/run-x.json"
    (root / "artifacts" / "eval-20261028").mkdir(parents=True)
    payload = b'{"evidence": true}'
    (root / trace_rel).write_bytes(payload)
    (root / "benchmarks" / "manifests").mkdir(parents=True)
    shutil.copy(MANIFEST, root / "benchmarks" / "manifests"
                / "eval-v1.json")
    monkeypatch.setattr(mr, "PROJECT_DIR", root)
    other_root = "/some/other/machine/project-chimera"
    packet = {
        "episodes": [{"artifacts": {"trace": {
            "path": f"{other_root}/{trace_rel}",
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload)}}, "evidence": {"screenshots": []}}],
        "plans": [],
        "manifest": {"path": "benchmarks/manifests/eval-v1.json",
                     "sha256": FROZEN_SHA},
    }
    entries = mr._collect_bundle_entries(packet)
    assert sorted(e["path"] for e in entries) == sorted(
        ["benchmarks/manifests/eval-v1.json", trace_rel])
    bad = json.loads(json.dumps(packet))
    (root / trace_rel).write_bytes(b'{"tampered": true}')
    with pytest.raises(PacketError, match="sha256 mismatch"):
        mr._collect_bundle_entries(bad)


def test_build_bundle_fails_closed_on_damage(tmp_path):
    import copy
    packet = _build(tmp_path)
    bad = copy.deepcopy(packet)
    bad["episodes"][0]["artifacts"]["trace"]["path"] = "no/such/file.json"
    with pytest.raises(PacketError, match="missing: no/such/file.json"):
        build_bundle(bad, tmp_path / "x.zip")
    bad = copy.deepcopy(packet)
    bad["episodes"][0]["artifacts"]["trace"]["sha256"] = "0" * 64
    with pytest.raises(PacketError, match="sha256 mismatch"):
        build_bundle(bad, tmp_path / "x.zip")
    assert not (tmp_path / "x.zip").is_file()


def test_build_reviewer_packet_excludes_answers(tmp_path):
    import hashlib
    packet = _build(tmp_path)
    packet_bytes = (tmp_path / "packet.json").read_bytes()
    reviewer = build_reviewer_packet(
        packet, hashlib.sha256(packet_bytes).hexdigest(), tmp_path,
        created_at=FIXED_AT)
    # Original packet and pending decisions untouched.
    assert (tmp_path / "packet.json").read_bytes() == packet_bytes
    assert json.loads((tmp_path / "decisions.json").read_text())["decisions"] == {}
    assert [e["key"] for e in reviewer["episodes"]] == [
        e["key"] for e in packet["episodes"]]
    text = (tmp_path / "reviewer-packet.json").read_text()
    for banned in ('"recorded"', '"verifier"', '"decisions"',
                   '"verdicts"', '"assessment"', '"agreement"',
                   '"all_satisfied"', '"satisfied"',
                   '"agent_terminal_status"'):
        assert banned not in text, banned
    # Evidence survives: excerpts, refs, digests, gaps, postconditions.
    for got, want in zip(reviewer["episodes"], packet["episodes"]):
        assert got["evidence"] == want["evidence"]
        assert got["artifacts"] == want["artifacts"]
        assert got["expected_stored_name"] == want["expected_stored_name"]
    key = json.loads((tmp_path / "answer-key.json").read_text())
    assert set(key["episodes"]) == {e["key"] for e in packet["episodes"]}
    assert key["packet_sha256"] == reviewer["packet_sha256"]
    assert "DO NOT distribute" in key["warning"]
