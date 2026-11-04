"""Tests for the saucedemo-order workbench workflow (fake store).

Covers: registry/validation, the executor run spec (cases, presets,
mutations, fixed approved URL), end-to-end execution through both
real drivers against the scripted fake, S-check verdicts persisted
to history under the external origin, the legacy-DB origin
migration, and the stages artifact endpoint.
"""

import json
import sqlite3
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from adapters import saucedemo as adapter
from benchmarks.observer import ALLOWED
from tests.fake_saucedemo import (
    FakeSauceBrowser,
    FakeSauceContext,
    FakeSaucePage,
)
from workbench.executor import Executor, _run_spec
from workbench.server import WorkbenchState, create_server
from workbench.store import SCHEMA, Store
from workbench.workflows import (
    SAUCEDEMO_ORDER,
    SAUCEDEMO_STRESS,
    WorkflowValidationError,
    get_workflow,
    list_workflows,
)


def _params(**overrides):
    base = {
        "login_case": "standard",
        "cart_preset": "backpack+bike-light",
        "sort": "az",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "postal_code": "12345",
        "checkout_case": "complete",
        "action_timeout_ms": 0,
    }
    base.update(overrides)
    return base


def _sauce_chimera_factory(page):
    from benchmarks.observer import RecordingPage
    from workbench.executor import _ShotOnClose

    def make(log, shot_path):
        def factory(pw):
            browser = FakeSauceBrowser()
            context = FakeSauceContext()
            shot = _ShotOnClose(context, page, shot_path)
            factory.holder["shot"] = shot
            return browser, shot, RecordingPage(page, log)

        factory.holder = {}
        return factory

    return make


def _sauce_baseline_factory(page):
    from benchmarks.observer import RecordingPage
    from workbench.executor import _ShotOnClose

    def make(log, shot_path, holder):
        def factory():
            browser = FakeSauceBrowser()
            context = FakeSauceContext()
            shot = _ShotOnClose(context, page, shot_path)
            holder.update(shot=shot, browser=browser)
            return browser, shot, RecordingPage(page, log)

        return factory

    return make


def _wait_terminal(store, exec_id, timeout=30.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        record = store.get_execution(exec_id)
        if record and record["status"] not in ("queued", "running"):
            return record
        time.sleep(0.05)
    raise AssertionError(f"{exec_id} never finished")


def _check_satisfied(store, exec_id):
    return {r["check_id"]: r["satisfied"] for r in store.query(
        "SELECT check_id, satisfied FROM verification WHERE exec_id = ?",
        (exec_id,))}


def test_registry_lists_sauce_workflow_with_external_origin():
    ids = [w.workflow_id for w in list_workflows()]
    assert "saucedemo-order" in ids
    assert get_workflow("saucedemo-order") is SAUCEDEMO_ORDER
    assert SAUCEDEMO_ORDER.origin == "external"
    assert SAUCEDEMO_ORDER.to_dict()["origin"] == "external"
    assert get_workflow("create-project").origin == "local"


def test_sauce_params_validate():
    cleaned = SAUCEDEMO_ORDER.validate(_params())
    assert cleaned["login_case"] == "standard"
    assert cleaned["cart_preset"] == "backpack+bike-light"
    with pytest.raises(WorkflowValidationError):
        SAUCEDEMO_ORDER.validate(_params(login_case="root"))
    with pytest.raises(WorkflowValidationError):
        SAUCEDEMO_ORDER.validate(_params(cart_preset="everything"))
    with pytest.raises(WorkflowValidationError):
        SAUCEDEMO_ORDER.validate({**_params(), "password": "x"})


def test_run_spec_builds_order_and_mutations():
    spec = _run_spec("saucedemo-order", _params())
    assert spec["url"] == adapter.LOGIN_URL
    assert spec["verify"] == "sauce"
    assert spec["expected"]["items"] == [
        "Sauce Labs Backpack", "Sauce Labs Bike Light"]
    assert spec["scenario_id"] == (
        "sauce:standard/backpack+bike-light/complete")
    assert "password" not in json.dumps(spec["submitted"])
    assert "password" not in json.dumps(spec["expected"])
    missing = _run_spec(
        "saucedemo-order", _params(checkout_case="missing-postal"))
    assert missing["submitted"]["info"]["postalCode"] == ""
    blank = _run_spec(
        "saucedemo-order", _params(checkout_case="blank-info"))
    assert blank["submitted"]["info"] == {
        "firstName": "", "lastName": "", "postalCode": ""}
    locked = _run_spec(
        "saucedemo-order", _params(login_case="locked-out"))
    assert locked["expected"]["username"] == "locked_out_user"
    assert locked["scenario_id"].startswith("sauce:locked-out/")
    # The spec policy permits the store's own controls.
    decision, _ = spec["policy"].judge(
        "select", {"by": "css", "selector": adapter.SEL_SORT,
                   "value": "az"})
    assert decision == ALLOWED


def test_chimera_sauce_order_end_to_end(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(
            store, tmp_path / "wb",
            chimera_factory=_sauce_chimera_factory(FakeSaucePage()),
            baseline_factory=_sauce_baseline_factory(FakeSaucePage()))
        exec_id = ex.submit("saucedemo-order", "chimera", _params())
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "succeeded"
        assert record["verdict"] == "verified-success"
        assert record["origin"] == "external"
        assert record["scenario_id"] == (
            "sauce:standard/backpack+bike-light/complete")
        assert [c["check_id"] for c in record["checks"]] == [
            "S1", "S2", "S3", "S4", "S5"]
        assert all(c["satisfied"] == 1 for c in record["checks"])
        kinds = [a["action_type"] for a in record["actions"]]
        assert "navigate" in kinds and "select" in kinds
        assert "click" in kinds and "fill" in kinds
        assert record["screenshot_path"] is not None
        assert Path(record["screenshot_path"]).read_bytes() == b"fake-png"
        assert record["snapshot_path"] is not None
        stages_path = adapter.stages_path_for_trace(record["trace_path"])
        assert stages_path is not None
        stages = adapter.read_stages_file(stages_path)
        assert [s["stage"] for s in stages] == [
            "login", "inventory", "cart", "info", "info", "overview",
            "complete"]
        blob = json.dumps(record["progress"])
        assert "secret_sauce" not in blob
        assert "wrong-password" not in blob
        assert record["progress"]["params"]["login_case"] == "standard"
        assert record["progress"]["params"]["cart_preset"] == \
            "backpack+bike-light"
    finally:
        store.close()


def test_baseline_sauce_invalid_login_is_verified_failure(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(
            store, tmp_path / "wb",
            chimera_factory=_sauce_chimera_factory(FakeSaucePage()),
            baseline_factory=_sauce_baseline_factory(
                FakeSaucePage(login_ok=False)))
        exec_id = ex.submit("saucedemo-order", "baseline-a",
                            _params(login_case="locked-out"))
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "failed"
        assert record["verdict"] == "verified-failure"
        assert record["origin"] == "external"
        by_id = {c["check_id"]: c for c in record["checks"]}
        assert by_id["S1"]["satisfied"] == 0
        assert "sadface" in (by_id["S1"]["detail"] or "")
    finally:
        store.close()


def test_baseline_sauce_empty_cart_refuses_checkout(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(
            store, tmp_path / "wb",
            chimera_factory=_sauce_chimera_factory(FakeSaucePage()),
            baseline_factory=_sauce_baseline_factory(FakeSaucePage()))
        exec_id = ex.submit("saucedemo-order", "baseline-a",
                            _params(cart_preset="empty-cart"))
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "failed"
        assert "empty cart" in (record["error"] or "")
        by_id = {c["check_id"]: c for c in record["checks"]}
        assert by_id["S3"]["satisfied"] == 1
        assert by_id["S5"]["satisfied"] == 0
    finally:
        store.close()


def test_chimera_rejects_timeout_override_for_sauce(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_sauce_chimera_factory(
                          FakeSaucePage()))
        with pytest.raises(WorkflowValidationError):
            ex.submit("saucedemo-order", "chimera",
                      _params(action_timeout_ms=500))
    finally:
        store.close()


def test_origin_migration_backfills_legacy_rows(tmp_path):
    db_path = tmp_path / "legacy.db"
    legacy_schema = SCHEMA.replace(
        "    origin TEXT NOT NULL DEFAULT 'local', -- 'local' | 'external'\n",
        "")
    assert "origin" not in legacy_schema
    conn = sqlite3.connect(str(db_path))
    conn.executescript(legacy_schema)
    conn.execute(
        "INSERT INTO executions (id, created_at, source, workflow_id, "
        "driver, scenario_id, trial_kind, status, verdict) "
        "VALUES ('r1', 't', 'workbench', 'create-project', 'chimera', "
        "'S-NORM', 'adhoc', 'succeeded', 'verified-success')")
    conn.commit()
    conn.close()
    store = Store(db_path)
    try:
        record = store.get_execution("r1")
        assert record is not None
        assert record["origin"] == "local"
        assert store.list_executions(
            filters={"origin": "local"})["total"] == 1
        assert store.list_executions(
            filters={"origin": "external"})["total"] == 0
    finally:
        store.close()


def _seed_sauce_analytics(store):
    def row(exec_id, status, verdict, duration, checks, error=None):
        store.create_execution({
            "id": exec_id, "workflow_id": "saucedemo-order",
            "origin": "external", "driver": "chimera",
            "scenario_id": "sauce:x", "trial_kind": "adhoc",
            "status": status, "verdict": verdict,
            "duration_ms": duration, "error": error,
        })
        store.replace_verification(exec_id, checks)

    full = [{"check_id": c, "satisfied": True, "detail": ""}
            for c in ("S1", "S2", "S3", "S4", "S5")]
    row("e1", "succeeded", "verified-success", 1000, full)
    row("e2", "failed", "verified-failure", 2000, [
        {"check_id": "S1", "satisfied": False, "detail": "locked"},
        {"check_id": "S3", "satisfied": False, "detail": "no cart"},
        {"check_id": "S4", "satisfied": False, "detail": "no info"},
        {"check_id": "S5", "satisfied": False, "detail": "no order"},
    ])
    row("e3", "failed", "verified-failure", 3000, [
        {"check_id": "S1", "satisfied": True, "detail": ""},
        {"check_id": "S3", "satisfied": True, "detail": ""},
        {"check_id": "S4", "satisfied": False, "detail": "rejected"},
        {"check_id": "S5", "satisfied": False, "detail": "no order"},
    ])
    row("e4", "succeeded", "verified-failure", 4000, [
        {"check_id": "S1", "satisfied": True, "detail": ""},
        {"check_id": "S3", "satisfied": False, "detail": "wrong items"},
        {"check_id": "S4", "satisfied": False, "detail": "no info"},
        {"check_id": "S5", "satisfied": False, "detail": "no order"},
    ])
    row("e5", "failed", "insufficient-evidence", None, [])
    row("e6", "failed", "verified-failure", 900, [
        {"check_id": "S1", "satisfied": True, "detail": ""},
        {"check_id": "S2", "satisfied": True, "detail": ""},
        {"check_id": "S3", "satisfied": True, "detail": "empty confirmed"},
        {"check_id": "S4", "satisfied": False, "detail": "never attempted"},
        {"check_id": "S5", "satisfied": False, "detail": "no order"},
    ], error="empty cart: refusing checkout with no items")
    # A local-workflow row must not leak into the sauce scope.
    store.create_execution({
        "id": "other", "workflow_id": "create-project",
        "driver": "chimera", "scenario_id": "S-NORM",
        "trial_kind": "adhoc", "status": "succeeded",
        "verdict": "verified-success", "duration_ms": 10,
    })


def test_sauce_analytics_funnel_stages_and_accuracy(tmp_path):
    from workbench import analytics

    store = Store(tmp_path / "w.db")
    try:
        _seed_sauce_analytics(store)
        got = analytics.sauce(store, {})
        assert got["total"] == 6
        assert got["verified"] == 5
        by_check = {c["check_id"]: c for c in got["checks"]}
        assert by_check["S1"]["rate"] == pytest.approx(4 / 5)
        assert by_check["S2"]["n"] == 2  # own denominator
        assert by_check["S2"]["rate"] == 1.0
        assert [(f["stage"], f["n"]) for f in got["funnel"]] == [
            ("login", 4), ("cart", 3), ("checkout information", 1),
            ("order complete", 1)]
        stages = {s["stage"]: s["n"] for s in got["failure_stages"]}
        # e6's gate error attributes it to cart, not checkout.
        assert stages == {"login": 1, "cart": 2,
                          "checkout information": 1,
                          "none (order completed)": 1, "unverified": 1}
        acc = got["verification_accuracy"]
        assert (acc["agree_success"], acc["agree_failure"],
                acc["false_success"], acc["false_failure"],
                acc["unadjudicated"]) == (1, 3, 1, 0, 1)
        assert acc["denominator"] == 5
        assert acc["accuracy"] == pytest.approx(0.8)
        assert got["durations"]["n"] == 5
        assert got["durations"]["missing"] == 1
        assert got["durations"]["p50"] == 2000
    finally:
        store.close()


def test_every_analytics_endpoint_runs_on_sauce_rows(tmp_path):
    from workbench import analytics

    store = Store(tmp_path / "w.db")
    try:
        _seed_sauce_analytics(store)
        store.replace_actions("e1", [
            {"seq": 1, "action_type": "navigate", "outcome": "ok",
             "elapsed_ms": 100},
            {"seq": 2, "action_type": "click", "outcome": "error",
             "elapsed_ms": None},
        ])
        assert analytics.overview(store, {})["total"] == 7
        assert analytics.outcome_matrix(store, {})["cells"]
        assert analytics.latency(store, {})["overall"]["n"] == 6
        assert analytics.failures(store, {})["total_failures"] == 4
        assert analytics.trends(store, {})["days"]
        got = analytics.stages(store, {})
        assert [s["action"] for s in got["stages"]] == [
            "click", "navigate"]
        assert analytics.drivers(store, {})["drivers"]
        assert analytics.workflows(store, {})["workflows"]
        assert analytics.verification_coverage(store, {})["checks"]
    finally:
        store.close()


def test_sauce_analytics_empty_scope_has_none_rates(tmp_path):
    from workbench import analytics

    store = Store(tmp_path / "w.db")
    try:
        got = analytics.sauce(store, {})
        assert got["total"] == 0
        assert got["verified"] == 0
        assert all(c["rate"] is None for c in got["checks"])
        assert got["verification_accuracy"]["accuracy"] is None
        assert got["durations"]["n"] == 0
    finally:
        store.close()


def _stress_params(**overrides):
    base = {
        "account": "standard",
        "cart_preset": "backpack+bike-light",
        "remove_item": "last-added",
        "sort": "az",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "postal_code": "12345",
        "settle_timeout_ms": 5000,
        "action_timeout_ms": 0,
    }
    base.update(overrides)
    return base


def test_stress_registry_and_params_validate():
    ids = [w.workflow_id for w in list_workflows()]
    assert "saucedemo-stress" in ids
    assert get_workflow("saucedemo-stress") is SAUCEDEMO_STRESS
    assert SAUCEDEMO_STRESS.origin == "external"
    cleaned = SAUCEDEMO_STRESS.validate(_stress_params())
    assert cleaned["account"] == "standard"
    assert cleaned["settle_timeout_ms"] == 5000
    with pytest.raises(WorkflowValidationError):
        SAUCEDEMO_STRESS.validate(_stress_params(account="root"))
    with pytest.raises(WorkflowValidationError):
        SAUCEDEMO_STRESS.validate(_stress_params(cart_preset="empty-cart"))
    with pytest.raises(WorkflowValidationError):
        SAUCEDEMO_STRESS.validate(_stress_params(settle_timeout_ms=50))
    with pytest.raises(WorkflowValidationError):
        SAUCEDEMO_STRESS.validate({**_stress_params(), "password": "x"})


def test_stress_run_spec_builds_flow_and_expected():
    spec = _run_spec("saucedemo-stress", _stress_params())
    assert spec["url"] == adapter.LOGIN_URL
    assert spec["verify"] == "sauce-stress"
    assert spec["expected"]["added"] == [
        "Sauce Labs Backpack", "Sauce Labs Bike Light"]
    assert spec["expected"]["remaining"] == ["Sauce Labs Backpack"]
    assert spec["expected"]["username"] == "standard_user"
    assert spec["scenario_id"] == (
        "sauce-stress:standard/backpack+bike-light/az/remove")
    assert "password" not in json.dumps(spec["submitted"])
    assert "password" not in json.dumps(spec["expected"])
    glitch = _run_spec("saucedemo-stress",
                       _stress_params(account="glitch"))
    assert glitch["expected"]["username"] == "performance_glitch_user"
    problem = _run_spec("saucedemo-stress",
                        _stress_params(account="problem"))
    assert problem["expected"]["username"] == "problem_user"
    keep = _run_spec("saucedemo-stress",
                     _stress_params(remove_item="none"))
    assert keep["expected"]["remaining"] is None
    assert keep["scenario_id"].endswith("/keep")


def test_stress_chimera_end_to_end(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_sauce_chimera_factory(
                          FakeSaucePage()),
                      baseline_factory=_sauce_baseline_factory(
                          FakeSaucePage()))
        exec_id = ex.submit("saucedemo-stress", "chimera",
                            _stress_params())
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "succeeded"
        assert record["verdict"] == "verified-success"
        assert record["origin"] == "external"
        assert record["scenario_id"] == (
            "sauce-stress:standard/backpack+bike-light/az/remove")
        checks = _check_satisfied(store, exec_id)
        assert checks == {"T1": 1, "T2": 1, "T3": 1, "T4": 1,
                          "T5": 1, "T6": 1}
        stages = adapter.stages_for_trace(record["trace_path"])
        login = adapter.stage_states(stages)["login"]
        assert isinstance(login.get("login_ms"), int)
        blob = json.dumps(record) + json.dumps(checks)
        assert "secret_sauce" not in blob
    finally:
        store.close()


def test_stress_baseline_problem_user_is_verified_failure(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_sauce_chimera_factory(
                          FakeSaucePage()),
                      baseline_factory=_sauce_baseline_factory(
                          FakeSaucePage(images_404=True, sort_broken=True,
                                        info_reject=True)))
        exec_id = ex.submit("saucedemo-stress", "baseline-a",
                            _stress_params(account="problem", sort="za"))
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "failed"
        assert record["verdict"] == "verified-failure"
        assert "checkout blocked" in (record["error"] or "")
        checks = _check_satisfied(store, exec_id)
        assert checks == {"T1": 1, "T2": 0, "T3": 0, "T4": 1,
                          "T5": 1, "T6": 0}
    finally:
        store.close()


def _seed_stress_analytics(store, traces):
    def row(exec_id, driver, scenario, status, verdict, duration,
            checks, login_ms=None):
        trace = str(traces / f"{exec_id}.replay.json")
        store.create_execution({
            "id": exec_id, "workflow_id": "saucedemo-stress",
            "origin": "external", "driver": driver,
            "scenario_id": scenario, "trial_kind": "campaign",
            "status": status, "verdict": verdict,
            "duration_ms": duration, "trace_path": trace,
        })
        store.replace_verification(exec_id, checks)
        if login_ms is not None:
            (traces / f"{exec_id}.stages.json").write_text(
                json.dumps({"run_id": exec_id, "stages": [{
                    "stage": "login", "url": "", "captured_at": "",
                    "state": {"logged_in": True, "login_ms": login_ms}}]}),
                encoding="utf-8")

    full = [{"check_id": c, "satisfied": True, "detail": ""}
            for c in ("T1", "T2", "T3", "T4", "T5", "T6")]
    row("s1", "chimera", "sauce-stress:standard/x/az/remove",
        "succeeded", "verified-success", 8000, full, login_ms=120)
    row("s2", "baseline-a", "sauce-stress:standard/x/az/remove",
        "succeeded", "verified-success", 6000, full, login_ms=90)
    row("s3", "chimera", "sauce-stress:glitch/x/az/remove",
        "succeeded", "verified-success", 12000, full, login_ms=5100)
    row("s4", "baseline-a", "sauce-stress:glitch/x/az/remove",
        "succeeded", "verified-success", 11000, full,
        login_ms=None)  # stages file lost: readiness unmeasured
    row("s5", "chimera", "sauce-stress:problem/x/za/remove",
        "failed", "verified-failure", 9000, [
            {"check_id": "T1", "satisfied": True, "detail": ""},
            {"check_id": "T2", "satisfied": False, "detail": "404"},
            {"check_id": "T3", "satisfied": False, "detail": "order"},
            {"check_id": "T4", "satisfied": True, "detail": ""},
            {"check_id": "T5", "satisfied": True, "detail": ""},
            {"check_id": "T6", "satisfied": False, "detail": "rejected"},
        ], login_ms=150)
    row("s6", "baseline-a", "sauce-stress:problem/x/za/remove",
        "failed", "verified-failure", 8500, [
            {"check_id": "T1", "satisfied": True, "detail": ""},
            {"check_id": "T2", "satisfied": False, "detail": "404"},
            {"check_id": "T3", "satisfied": False, "detail": "order"},
            {"check_id": "T4", "satisfied": True, "detail": ""},
            {"check_id": "T5", "satisfied": True, "detail": ""},
            {"check_id": "T6", "satisfied": False, "detail": "rejected"},
        ], login_ms=140)
    # s6's gate error must NOT override its earlier genuine T2 defect.
    store.update_execution(
        "s6", {"error": "checkout blocked: Error: Last Name is required"})
    # A sort-step timeout kills the flow before inventory capture.
    row("s7", "chimera", "sauce-stress:glitch/x/za/remove",
        "failed", "verified-failure", 10500, [
            {"check_id": "T1", "satisfied": True, "detail": ""},
            {"check_id": "T2", "satisfied": False,
             "detail": "no product images observed"},
            {"check_id": "T3", "satisfied": False,
             "detail": "inventory not captured"},
            {"check_id": "T4", "satisfied": False,
             "detail": "cart page not reached"},
            {"check_id": "T5", "satisfied": False,
             "detail": "cart page not reached"},
            {"check_id": "T6", "satisfied": False,
             "detail": "no order confirmation"},
        ], login_ms=5200)
    store.update_execution(
        "s7", {"error": "TimeoutError: Locator.select_option: "
                        "Timeout 5000ms exceeded."})


def test_stress_analytics_checks_readiness_and_disagreement(tmp_path):
    from workbench import analytics

    store = Store(tmp_path / "w.db")
    traces = tmp_path / "wb" / "traces"
    traces.mkdir(parents=True, exist_ok=True)
    try:
        _seed_stress_analytics(store, traces)
        got = analytics.sauce_stress(store, {})
        assert got["total"] == 7
        assert got["verified"] == 7
        by_check = {c["check_id"]: c for c in got["checks"]}
        assert by_check["T1"]["rate"] == 1.0
        assert by_check["T2"]["rate"] == pytest.approx(4 / 7)
        assert [(f["stage"], f["n"]) for f in got["funnel"]] == [
            ("login", 7), ("cart", 6), ("order complete", 4)]
        stages = {s["stage"]: s["n"] for s in got["failure_stages"]}
        assert stages == {"none (flow completed)": 4,
                          "product images": 2, "sort": 1}
        ready = {(r["account"], r["driver"]): r
                 for r in got["readiness"]}
        assert ready[("glitch", "chimera")]["p50"] == 5100
        assert ready[("glitch", "baseline-a")]["n"] == 0
        assert ready[("glitch", "baseline-a")]["missing"] == 1
        assert ready[("glitch", "baseline-a")]["p50"] is None
        by_account = {(r["account"], r["driver"]): r
                      for r in got["by_account"]}
        assert by_account[("problem", "chimera")]["success_rate"] == 0.0
        assert by_account[("standard", "chimera")]["success_rate"] == 1.0
        disagree = {d["check_id"]: d
                    for d in got["check_disagreement"]}
        assert disagree["T1"]["delta"] == 0.0
        assert disagree["T2"]["chimera"]["n"] == 4
        assert disagree["T2"]["baseline"]["n"] == 3
        empty = analytics.sauce_stress(store, {"driver": "nobody"})
        assert empty["total"] == 0
        assert all(c["rate"] is None for c in empty["checks"])
        assert empty["readiness"] == []
    finally:
        store.close()


def test_stress_analytics_route_is_registered(tmp_path):
    from workbench import analytics
    from workbench.server import ANALYTICS

    assert ANALYTICS["sauce-stress"] is analytics.sauce_stress
    store = Store(tmp_path / "w.db")
    traces = tmp_path / "wb" / "traces"
    traces.mkdir(parents=True, exist_ok=True)
    try:
        _seed_stress_analytics(store, traces)
        doc = ANALYTICS["sauce-stress"](store, {})
        assert doc["total"] == 7
        assert doc["verified"] == 7
    finally:
        store.close()


def test_stages_artifact_served_and_missing_is_404(tmp_path):
    store = Store(tmp_path / "w.db")
    traces = tmp_path / "wb" / "traces"
    traces.mkdir(parents=True, exist_ok=True)
    exec_id = store.create_execution({
        "workflow_id": "saucedemo-order", "origin": "external",
        "driver": "baseline-a", "scenario_id": "sauce:x",
        "trial_kind": "adhoc", "status": "succeeded",
        "verdict": "verified-success",
        "trace_path": str(traces / "r9.replay.json"),
    })
    (traces / "r9.stages.json").write_text(
        json.dumps({"run_id": "r9", "stages": []}), encoding="utf-8")
    bare_id = store.create_execution({
        "workflow_id": "create-project", "driver": "chimera",
        "scenario_id": "S-NORM", "trial_kind": "adhoc",
        "status": "succeeded", "verdict": "verified-success",
    })
    state = WorkbenchState(tmp_path, store=store,
                           executor=Executor(store, tmp_path / "wb"))
    httpd = create_server(tmp_path, 0, state)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{httpd.server_address[1]}"
        with urllib.request.urlopen(
                f"{base}/api/workbench/executions/{exec_id}/artifact"
                f"?kind=stages") as res:
            assert res.status == 200
            assert json.loads(res.read().decode())["run_id"] == "r9"
        with pytest.raises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(
                f"{base}/api/workbench/executions/{bare_id}/artifact"
                f"?kind=stages")
        assert ctx.value.code == 404
    finally:
        httpd.shutdown()
        store.close()
