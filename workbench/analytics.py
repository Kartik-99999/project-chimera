"""Analytics aggregates over executions.

Every function takes the same filter mapping as
:meth:`workbench.store.Store.list_executions` and returns plain JSON
structures with explicit denominators and missing-data counts. Rates
are computed over *adjudicated* subsets only (e.g. verified rows),
and percentile math samples at most :data:`PERCENTILE_SAMPLE_CAP`
durations, reporting when sampling kicked in — the shape that keeps
working at thousands or millions of rows.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional

from workbench.store import Store

PERCENTILE_SAMPLE_CAP = 50000

_LATENCY_EDGES = [0, 250, 500, 1000, 2000, 4000, 8000, 16000, 32000]


def _durations(store: Store, filters: Mapping[str, Any],
               extra: str = "", params: tuple = ()) -> List[int]:
    where, base = store._where(dict(filters))
    rows = store.query(
        f"SELECT duration_ms FROM executions {where} "
        f"{'AND' if where else 'WHERE'} duration_ms IS NOT NULL {extra} "
        f"ORDER BY duration_ms",
        (*base, *params))
    return [r["duration_ms"] for r in rows]


def _percentiles(sorted_values: List[int],
                 points: List[int]) -> Dict[str, Optional[int]]:
    result: Dict[str, Optional[int]] = {}
    n = len(sorted_values)
    for point in points:
        if not n:
            result[f"p{point}"] = None
            continue
        rank = math.ceil(point / 100 * n) - 1
        result[f"p{point}"] = sorted_values[max(0, min(rank, n - 1))]
    return result


def _sample_note(total: int) -> Dict[str, Any]:
    return {"sampled": total > PERCENTILE_SAMPLE_CAP,
            "sample_cap": PERCENTILE_SAMPLE_CAP}


def overview(store: Store,
             filters: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Totals, verdict/status splits, duration stats, coverage."""
    filters = dict(filters or {})
    where, params = store._where(filters)
    total = store.query(
        f"SELECT COUNT(*) AS n FROM executions {where}", params)[0]["n"]
    by_verdict = {
        r["verdict"]: r["n"] for r in store.query(
            f"SELECT verdict, COUNT(*) AS n FROM executions {where} "
            f"GROUP BY verdict", params)}
    by_status = {
        r["status"]: r["n"] for r in store.query(
            f"SELECT status, COUNT(*) AS n FROM executions {where} "
            f"GROUP BY status", params)}
    durations = _durations(store, filters)
    stats = _percentiles(durations, [50, 90, 95, 99])
    missing = store.query(
        f"SELECT COUNT(*) AS n FROM executions {where} "
        f"{'AND' if where else 'WHERE'} duration_ms IS NULL",
        params)[0]["n"]
    verified = sum(by_verdict.get(v, 0)
                   for v in ("verified-success", "verified-failure"))
    return {
        "total": total,
        "by_verdict": by_verdict,
        "by_status": by_status,
        "verified_success_rate": (
            by_verdict.get("verified-success", 0) / verified
            if verified else None),
        "verified_denominator": verified,
        "durations": {**stats,
                      "n": len(durations), "missing": missing,
                      **_sample_note(len(durations))},
        "date_range": store.query(
            f"SELECT MIN(created_at) AS lo, MAX(created_at) AS hi "
            f"FROM executions {where}", params)[0],
    }


def outcome_matrix(store: Store, filters: Optional[Mapping[str, Any]] = None
                   ) -> Dict[str, Any]:
    """Scenario × driver cells with verdict splits and median latency."""
    filters = dict(filters or {})
    where, params = store._where(filters)
    cells = store.query(
        f"SELECT scenario_id, driver, COUNT(*) AS n, "
        f"SUM(CASE WHEN verdict='verified-success' THEN 1 ELSE 0 END) "
        f"AS ok, "
        f"SUM(CASE WHEN verdict='verified-failure' THEN 1 ELSE 0 END) "
        f"AS bad, "
        f"SUM(CASE WHEN verdict='insufficient-evidence' THEN 1 ELSE 0 END) "
        f"AS unknown, "
        f"SUM(CASE WHEN verdict='pending' THEN 1 ELSE 0 END) AS pending "
        f"FROM executions {where} "
        f"GROUP BY scenario_id, driver "
        f"ORDER BY scenario_id, driver", params)
    for cell in cells:
        sub = {**filters, "scenario_id": cell["scenario_id"],
               "driver": cell["driver"]}
        durations = _durations(store, sub)
        cell["p50_ms"] = _percentiles(durations, [50])["p50"]
        cell["durations_n"] = len(durations)
    return {"cells": cells}


def latency(store: Store, filters: Optional[Mapping[str, Any]] = None
            ) -> Dict[str, Any]:
    """Duration histogram (fixed edges) plus overall/driver percentiles."""
    filters = dict(filters or {})
    durations = _durations(store, filters)
    edges = _LATENCY_EDGES + [None]
    buckets = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        count = sum(1 for d in durations
                    if d >= lo and (hi is None or d < hi))
        buckets.append({"lo_ms": lo, "hi_ms": hi, "n": count})
    drivers = store.query(
        "SELECT DISTINCT driver FROM executions "
        + store._where(filters)[0] + " ORDER BY driver",
        store._where(filters)[1])
    by_driver = []
    for row in drivers:
        sub = _durations(store, {**filters, "driver": row["driver"]})
        by_driver.append({"driver": row["driver"], "n": len(sub),
                          **_percentiles(sub, [50, 90, 95])})
    return {
        "buckets": buckets,
        "overall": {"n": len(durations),
                    **_percentiles(durations, [50, 90, 95, 99]),
                    **_sample_note(len(durations))},
        "by_driver": by_driver,
    }


def failures(store: Store, filters: Optional[Mapping[str, Any]] = None,
             limit: int = 12) -> Dict[str, Any]:
    """Failure-category and error-type breakdowns (failures only)."""
    filters = {**dict(filters or {}), "status": ["failed", "error",
                                                 "cancelled"]}
    where, params = store._where(filters)
    total = store.query(
        f"SELECT COUNT(*) AS n FROM executions {where}", params)[0]["n"]
    by_category = store.query(
        f"SELECT COALESCE(failure_category, '(uncategorized)') AS name, "
        f"COUNT(*) AS n FROM executions {where} "
        f"GROUP BY name ORDER BY n DESC LIMIT {int(limit)}", params)
    by_error = store.query(
        f"SELECT COALESCE(error_type, '(unknown)') AS name, COUNT(*) AS n "
        f"FROM executions {where} GROUP BY name "
        f"ORDER BY n DESC LIMIT {int(limit)}", params)
    by_scenario = store.query(
        f"SELECT scenario_id, COALESCE(failure_category, "
        f"'(uncategorized)') AS category, COUNT(*) AS n "
        f"FROM executions {where} GROUP BY scenario_id, category",
        params)
    return {"total_failures": total, "by_category": by_category,
            "by_error": by_error, "by_scenario": by_scenario}


def trends(store: Store, filters: Optional[Mapping[str, Any]] = None
           ) -> Dict[str, Any]:
    """Verdict counts per day plus rolling success rate over verified."""
    filters = dict(filters or {})
    where, params = store._where(filters)
    days = store.query(
        f"SELECT SUBSTR(created_at, 1, 10) AS day, "
        f"COUNT(*) AS n, "
        f"SUM(CASE WHEN verdict='verified-success' THEN 1 ELSE 0 END) "
        f"AS ok, "
        f"SUM(CASE WHEN verdict IN ('verified-success', "
        f"'verified-failure') THEN 1 ELSE 0 END) AS verified "
        f"FROM executions {where} GROUP BY day ORDER BY day", params)
    for day in days:
        day["success_rate"] = (day["ok"] / day["verified"]
                               if day["verified"] else None)
    return {"days": days}


def stages(store: Store, filters: Optional[Mapping[str, Any]] = None
           ) -> Dict[str, Any]:
    """Per-action-type outcomes and elapsed-time stats (measured only)."""
    filters = dict(filters or {})
    where, params = store._where(filters)
    # Map execution filters onto the join.
    join_where = where.replace("created_at", "e.created_at", 1) \
        if where else ""
    rows = store.query(
        f"SELECT a.action_type AS action, a.outcome AS outcome, "
        f"COUNT(*) AS n, AVG(a.elapsed_ms) AS avg_ms, "
        f"SUM(CASE WHEN a.elapsed_ms IS NULL THEN 1 ELSE 0 END) "
        f"AS missing_ms "
        f"FROM actions a JOIN executions e ON e.id = a.exec_id "
        f"{join_where} GROUP BY action, outcome "
        f"ORDER BY action, outcome", params)
    totals: Dict[str, Any] = {}
    for row in rows:
        slot = totals.setdefault(row["action"], {
            "action": row["action"], "n": 0, "errors": 0,
            "avg_ms": None, "missing_ms": 0, "by_outcome": []})
        slot["n"] += row["n"]
        slot["missing_ms"] += row["missing_ms"]
        if row["outcome"] == "error":
            slot["errors"] += row["n"]
        slot["by_outcome"].append(
            {"outcome": row["outcome"], "n": row["n"],
             "avg_ms": (round(row["avg_ms"], 1)
                        if row["avg_ms"] is not None else None)})
    measured = [r for r in rows if r["avg_ms"] is not None]
    for slot in totals.values():
        parts = [r for r in measured if r["action"] == slot["action"]]
        if parts:
            weighted = sum(r["avg_ms"] * r["n"] for r in parts)
            slot["avg_ms"] = round(
                weighted / sum(r["n"] for r in parts), 1)
    return {"stages": sorted(totals.values(), key=lambda s: s["action"])}


def drivers(store: Store, filters: Optional[Mapping[str, Any]] = None
            ) -> Dict[str, Any]:
    """Head-to-head driver comparison over the same filter set."""
    filters = dict(filters or {})
    where, params = store._where(filters)
    rows = store.query(
        f"SELECT driver, COUNT(*) AS n, "
        f"SUM(CASE WHEN verdict='verified-success' THEN 1 ELSE 0 END) "
        f"AS ok, "
        f"SUM(CASE WHEN verdict IN ('verified-success', "
        f"'verified-failure') THEN 1 ELSE 0 END) AS verified, "
        f"SUM(CASE WHEN verdict='insufficient-evidence' THEN 1 ELSE 0 END) "
        f"AS unknown, AVG(retries) AS avg_retries "
        f"FROM executions {where} GROUP BY driver ORDER BY driver",
        params)
    for row in rows:
        row["success_rate"] = (row["ok"] / row["verified"]
                               if row["verified"] else None)
        sub = _durations(store, {**filters, "driver": row["driver"]})
        row.update(_percentiles(sub, [50, 95]))
        row["durations_n"] = len(sub)
        row["avg_retries"] = (round(row["avg_retries"], 2)
                              if row["avg_retries"] is not None else None)
    return {"drivers": rows}


def workflows(store: Store, filters: Optional[Mapping[str, Any]] = None
              ) -> Dict[str, Any]:
    """Per-workflow comparison over the same filter set."""
    filters = dict(filters or {})
    where, params = store._where(filters)
    rows = store.query(
        f"SELECT workflow_id, COUNT(*) AS n, "
        f"SUM(CASE WHEN verdict='verified-success' THEN 1 ELSE 0 END) "
        f"AS ok, "
        f"SUM(CASE WHEN verdict IN ('verified-success', "
        f"'verified-failure') THEN 1 ELSE 0 END) AS verified, "
        f"SUM(CASE WHEN verdict='insufficient-evidence' THEN 1 ELSE 0 END) "
        f"AS unknown "
        f"FROM executions {where} GROUP BY workflow_id "
        f"ORDER BY workflow_id", params)
    for row in rows:
        row["success_rate"] = (row["ok"] / row["verified"]
                               if row["verified"] else None)
        sub = _durations(store, {**filters,
                                 "workflow_id": row["workflow_id"]})
        row.update(_percentiles(sub, [50, 95]))
        row["durations_n"] = len(sub)
    return {"workflows": rows}


#: SauceDemo funnel stages: (stage label, check id). S2 (sort) is
#: excluded from the cumulative funnel because it exists only when
#: sorting was requested; it is reported with its own denominator.
SAUCE_FUNNEL = (
    ("login", "S1"),
    ("cart", "S3"),
    ("checkout information", "S4"),
    ("order complete", "S5"),
)

SAUCE_CHECK_STAGES = {
    "S1": "login",
    "S2": "sort",
    "S3": "cart",
    "S4": "checkout information",
    "S5": "order complete",
}

#: Driver gate errors attribute a failure to the stage that refused
#: to proceed (e.g. an empty cart never attempts checkout, so its
#: first failed check alone would blame checkout information). Only
#: refusals refine the attribution: a rejected attempt (such as a
#: site-blocked checkout) is already the verdict of its own stage,
#: so an earlier failed check keeps the blame. A select timeout
#: kills the flow before the inventory is captured, so it refines
#: to sort rather than the never-observed images.
SAUCE_GATE_ERROR_STAGES = (
    ("empty cart:", "cart"),
    ("cart contents mismatch:", "cart"),
    ("unknown catalog slugs:", "cart"),
    ("login failed:", "login"),
    ("select_option", "sort"),
)


def sauce(store: Store,
          filters: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """SauceDemo order funnel, failure stages, and report accuracy.

    Scoped to ``saucedemo-order`` executions. The funnel counts
    verified rows cumulatively (a row past checkout also passed
    login); failure stages name the first failed check per verified
    row, refined by driver gate errors to the stage that refused to
    proceed; verification accuracy compares the driver's reported
    outcome (status) against the independent verdict. Rates divide
    by adjudicated rows only; empty scopes return None rates.
    """
    filters = {**dict(filters or {}),
               "workflow_id": "saucedemo-order"}
    where, params = store._where(filters)
    join_where = where.replace("created_at", "e.created_at", 1) \
        if where else ""
    rows = store.query(
        f"SELECT e.id AS id, e.status AS status, e.verdict AS verdict, "
        f"e.error AS error, v.check_id AS check_id, v.satisfied AS satisfied "
        f"FROM executions e LEFT JOIN verification v "
        f"ON v.exec_id = e.id {join_where} "
        f"ORDER BY e.id, v.check_id", params)
    by_exec: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        slot = by_exec.setdefault(row["id"], {
            "status": row["status"], "verdict": row["verdict"],
            "error": row["error"], "checks": {}})
        if row["check_id"] is not None:
            slot["checks"][row["check_id"]] = row["satisfied"]
    execs = list(by_exec.values())
    verified = [e for e in execs
                if e["verdict"] in ("verified-success", "verified-failure")]

    check_ids = ["S1", "S2", "S3", "S4", "S5"]
    checks = []
    for check_id in check_ids:
        have = [e for e in verified if check_id in e["checks"]]
        ok = sum(1 for e in have if e["checks"][check_id] == 1)
        bad = sum(1 for e in have if e["checks"][check_id] == 0)
        checks.append({
            "check_id": check_id,
            "stage": SAUCE_CHECK_STAGES[check_id],
            "satisfied": ok, "failed": bad, "n": len(have),
            "rate": (ok / len(have)) if have else None,
        })

    funnel = []
    survivors = list(verified)
    for stage, check_id in SAUCE_FUNNEL:
        survivors = [e for e in survivors
                     if e["checks"].get(check_id) == 1]
        funnel.append({"stage": stage, "check_id": check_id,
                       "n": len(survivors)})

    failure_stages: Dict[str, int] = {}
    for e in verified:
        first = next(
            (c for c in check_ids
             if c in e["checks"] and e["checks"][c] == 0),
            None)
        if first is None:
            key = "none (order completed)"
        else:
            key = SAUCE_CHECK_STAGES[first]
            error = e.get("error") or ""
            for token, stage in SAUCE_GATE_ERROR_STAGES:
                if token in error:
                    key = stage
                    break
        failure_stages[key] = failure_stages.get(key, 0) + 1
    unverified = len(execs) - len(verified)
    if unverified:
        failure_stages["unverified"] = unverified

    agree_ok = agree_bad = false_ok = false_bad = unadj = 0
    for e in execs:
        actual = {"verified-success": True,
                  "verified-failure": False}.get(e["verdict"])
        if actual is None or e["status"] not in ("succeeded", "failed",
                                                 "error"):
            unadj += 1
        elif e["status"] == "succeeded" and actual:
            agree_ok += 1
        elif e["status"] != "succeeded" and not actual:
            agree_bad += 1
        elif e["status"] == "succeeded":
            false_ok += 1
        else:
            false_bad += 1
    adjudicated = agree_ok + agree_bad + false_ok + false_bad

    durations = _durations(store, filters)
    missing = store.query(
        f"SELECT COUNT(*) AS n FROM executions {where} "
        f"{'AND' if where else 'WHERE'} duration_ms IS NULL",
        params)[0]["n"]
    return {
        "total": len(execs),
        "verified": len(verified),
        "checks": checks,
        "funnel": funnel,
        "failure_stages": [
            {"stage": stage, "n": n}
            for stage, n in sorted(failure_stages.items(),
                                   key=lambda kv: (-kv[1], kv[0]))],
        "verification_accuracy": {
            "agree_success": agree_ok,
            "agree_failure": agree_bad,
            "false_success": false_ok,
            "false_failure": false_bad,
            "unadjudicated": unadj,
            "denominator": adjudicated,
            "accuracy": ((agree_ok + agree_bad) / adjudicated
                         if adjudicated else None),
        },
        "durations": {**_percentiles(durations, [50, 90, 95]),
                      "n": len(durations), "missing": missing,
                      **_sample_note(len(durations))},
    }


SAUCE_STRESS_FUNNEL = (
    ("login", "T1"),
    ("cart", "T4"),
    ("order complete", "T6"),
)

SAUCE_STRESS_CHECK_STAGES = {
    "T1": "login",
    "T2": "product images",
    "T3": "sort",
    "T4": "cart",
    "T5": "cart after remove",
    "T6": "order complete",
}

STRESS_ACCOUNT_LABELS = {
    "standard": "Standard (control)",
    "glitch": "Slow login",
    "problem": "Problem user",
}


def _stress_account(scenario_id: Any) -> str:
    """Account tag from a stress scenario id, defensively parsed."""
    if isinstance(scenario_id, str) \
            and scenario_id.startswith("sauce-stress:"):
        parts = scenario_id[len("sauce-stress:"):].split("/")
        if parts and parts[0] in STRESS_ACCOUNT_LABELS:
            return parts[0]
    return "(unknown)"


def _readiness_ms(trace_path: Any) -> Optional[int]:
    """Click-to-readiness login_ms from a run's stages file, if any."""
    from adapters import saucedemo as sauce_adapter

    try:
        stages = sauce_adapter.stages_for_trace(trace_path)
    except Exception:  # noqa: BLE001 — evidence best-effort
        return None
    login = sauce_adapter.stage_states(stages).get("login", {})
    value = login.get("login_ms")
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def sauce_stress(store: Store,
                 filters: Optional[Mapping[str, Any]] = None
                 ) -> Dict[str, Any]:
    """SauceDemo stress (T-check) funnel, stages, readiness, accounts.

    Scoped to ``saucedemo-stress`` executions. Per-check rates use
    each check's own denominator (T3 exists only when sorting was
    requested, T5 only when a removal ran); the cumulative funnel
    covers login → cart → order complete. Readiness reports
    measured login_ms by account × driver from the stages files,
    with explicit missing counts. ``check_disagreement`` compares
    per-check satisfied rates by driver over the filter set —
    unpaired, with both denominators shown; verdict-level pairing
    stays in :func:`paired_outcomes`.
    """
    filters = {**dict(filters or {}),
               "workflow_id": "saucedemo-stress"}
    where, params = store._where(filters)
    join_where = where.replace("created_at", "e.created_at", 1) \
        if where else ""
    rows = store.query(
        f"SELECT e.id AS id, e.driver AS driver, e.status AS status, "
        f"e.verdict AS verdict, e.error AS error, "
        f"e.scenario_id AS scenario_id, e.trace_path AS trace_path, "
        f"v.check_id AS check_id, v.satisfied AS satisfied "
        f"FROM executions e LEFT JOIN verification v "
        f"ON v.exec_id = e.id {join_where} "
        f"ORDER BY e.id, v.check_id", params)
    by_exec: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        slot = by_exec.setdefault(row["id"], {
            "driver": row["driver"], "status": row["status"],
            "verdict": row["verdict"], "error": row["error"],
            "scenario_id": row["scenario_id"],
            "trace_path": row["trace_path"], "checks": {}})
        if row["check_id"] is not None:
            slot["checks"][row["check_id"]] = row["satisfied"]
    execs = list(by_exec.values())
    verified = [e for e in execs
                if e["verdict"] in ("verified-success", "verified-failure")]

    check_ids = ["T1", "T2", "T3", "T4", "T5", "T6"]
    checks = []
    for check_id in check_ids:
        have = [e for e in verified if check_id in e["checks"]]
        ok = sum(1 for e in have if e["checks"][check_id] == 1)
        bad = sum(1 for e in have if e["checks"][check_id] == 0)
        checks.append({
            "check_id": check_id,
            "stage": SAUCE_STRESS_CHECK_STAGES[check_id],
            "satisfied": ok, "failed": bad, "n": len(have),
            "rate": (ok / len(have)) if have else None,
        })

    funnel = []
    survivors = list(verified)
    for stage, check_id in SAUCE_STRESS_FUNNEL:
        survivors = [e for e in survivors
                     if e["checks"].get(check_id) == 1]
        funnel.append({"stage": stage, "check_id": check_id,
                       "n": len(survivors)})

    failure_stages: Dict[str, int] = {}
    for e in verified:
        first = next(
            (c for c in check_ids
             if c in e["checks"] and e["checks"][c] == 0),
            None)
        if first is None:
            key = "none (flow completed)"
        else:
            key = SAUCE_STRESS_CHECK_STAGES[first]
            error = e.get("error") or ""
            for token, stage in SAUCE_GATE_ERROR_STAGES:
                if token in error:
                    key = stage
                    break
        failure_stages[key] = failure_stages.get(key, 0) + 1
    unverified = len(execs) - len(verified)
    if unverified:
        failure_stages["unverified"] = unverified

    agree_ok = agree_bad = false_ok = false_bad = unadj = 0
    for e in execs:
        actual = {"verified-success": True,
                  "verified-failure": False}.get(e["verdict"])
        if actual is None or e["status"] not in ("succeeded", "failed",
                                                 "error"):
            unadj += 1
        elif e["status"] == "succeeded" and actual:
            agree_ok += 1
        elif e["status"] != "succeeded" and not actual:
            agree_bad += 1
        elif e["status"] == "succeeded":
            false_ok += 1
        else:
            false_bad += 1
    adjudicated = agree_ok + agree_bad + false_ok + false_bad

    durations = _durations(store, filters)
    missing = store.query(
        f"SELECT COUNT(*) AS n FROM executions {where} "
        f"{'AND' if where else 'WHERE'} duration_ms IS NULL",
        params)[0]["n"]

    readiness_groups: Dict[tuple, List[int]] = {}
    readiness_missing: Dict[tuple, int] = {}
    accounts: Dict[tuple, Dict[str, int]] = {}
    for e in execs:
        account = _stress_account(e.get("scenario_id"))
        key = (account, e["driver"])
        slot = accounts.setdefault(
            key, {"n": 0, "verified": 0, "ok": 0})
        slot["n"] += 1
        if e["verdict"] in ("verified-success", "verified-failure"):
            slot["verified"] += 1
        if e["verdict"] == "verified-success":
            slot["ok"] += 1
        measured = _readiness_ms(e.get("trace_path"))
        if measured is None:
            readiness_missing[key] = readiness_missing.get(key, 0) + 1
        else:
            readiness_groups.setdefault(key, []).append(measured)
    readiness = []
    for key in sorted(set(readiness_groups) | set(readiness_missing)):
        values = sorted(readiness_groups.get(key, []))
        readiness.append({
            "account": key[0], "driver": key[1],
            "n": len(values),
            "missing": readiness_missing.get(key, 0),
            **_percentiles(values, [50, 90, 95]),
        })
    by_account = [{
        "account": key[0], "driver": key[1], **slot,
        "success_rate": (slot["ok"] / slot["verified"]
                         if slot["verified"] else None),
    } for key, slot in sorted(accounts.items())]

    disagreement = []
    for check_id in check_ids:
        per_driver = {}
        for driver in ("chimera", "baseline-a"):
            have = [e for e in verified
                    if e["driver"] == driver and check_id in e["checks"]]
            ok = sum(1 for e in have if e["checks"][check_id] == 1)
            per_driver[driver] = {
                "rate": (ok / len(have)) if have else None,
                "n": len(have),
            }
        chim = per_driver["chimera"]["rate"]
        base = per_driver["baseline-a"]["rate"]
        disagreement.append({
            "check_id": check_id,
            "stage": SAUCE_STRESS_CHECK_STAGES[check_id],
            "chimera": per_driver["chimera"],
            "baseline": per_driver["baseline-a"],
            "delta": ((chim - base)
                      if chim is not None and base is not None else None),
        })

    return {
        "total": len(execs),
        "verified": len(verified),
        "checks": checks,
        "funnel": funnel,
        "failure_stages": [
            {"stage": stage, "n": n}
            for stage, n in sorted(failure_stages.items(),
                                   key=lambda kv: (-kv[1], kv[0]))],
        "verification_accuracy": {
            "agree_success": agree_ok,
            "agree_failure": agree_bad,
            "false_success": false_ok,
            "false_failure": false_bad,
            "unadjudicated": unadj,
            "denominator": adjudicated,
            "accuracy": ((agree_ok + agree_bad) / adjudicated
                         if adjudicated else None),
        },
        "durations": {**_percentiles(durations, [50, 90, 95]),
                      "n": len(durations), "missing": missing,
                      **_sample_note(len(durations))},
        "readiness": readiness,
        "by_account": by_account,
        "check_disagreement": disagreement,
    }


PAIR_LIST_CAP = 5000
STAGE_VALUE_SAMPLE_CAP = 20000


def paired_outcomes(store: Store,
                    filters: Optional[Mapping[str, Any]] = None
                    ) -> Dict[str, Any]:
    """Chimera vs Baseline A agreement on matched trial pairs.

    Trials pair up within (campaign, scenario) by repetition order
    (trial_seq). Agreement divides by pairs where both sides
    adjudicated (verified success/failure); pairs with an
    unverified side are listed, never folded in. Unpaired trials
    are counted, never silently dropped.
    """
    filters = dict(filters or {})
    where, params = store._where(filters)
    scoped = f"{where} {'AND' if where else 'WHERE'} " \
        "campaign_id IS NOT NULL " \
        "AND driver IN ('chimera', 'baseline-a')"
    rows = store.query(
        f"SELECT campaign_id, scenario_id, driver, verdict, trial_seq, "
        f"ROW_NUMBER() OVER (PARTITION BY campaign_id, scenario_id, "
        f"driver ORDER BY trial_seq, created_at) AS rep "
        f"FROM executions {scoped} "
        f"ORDER BY campaign_id, scenario_id, rep, driver", params)
    pairs: Dict[tuple, Dict[str, Any]] = {}
    for row in rows:
        key = (row["campaign_id"], row["scenario_id"], row["rep"])
        slot = pairs.setdefault(
            key, {"campaign_id": row["campaign_id"],
                  "scenario_id": row["scenario_id"],
                  "rep": row["rep"], "chimera": None,
                  "baseline": None})
        side = "chimera" if row["driver"] == "chimera" else "baseline"
        slot[side] = row["verdict"]
    ordered = [pairs[k] for k in sorted(pairs)]
    summary = {"both_success": 0, "chimera_only": 0,
               "baseline_only": 0, "both_failure": 0,
               "unknown": 0, "unpaired": 0}
    for pair in ordered:
        sides = (pair["chimera"], pair["baseline"])
        if None in sides:
            summary["unpaired"] += 1
        elif set(sides) <= {"verified-success", "verified-failure"}:
            if sides == ("verified-success", "verified-success"):
                summary["both_success"] += 1
            elif sides == ("verified-failure", "verified-failure"):
                summary["both_failure"] += 1
            elif sides[0] == "verified-success":
                summary["chimera_only"] += 1
            else:
                summary["baseline_only"] += 1
        else:
            summary["unknown"] += 1
    adjudicated = (summary["both_success"] + summary["chimera_only"]
                   + summary["baseline_only"] + summary["both_failure"])
    agreed = summary["both_success"] + summary["both_failure"]
    return {
        "pairs": ordered[:PAIR_LIST_CAP],
        "pairs_truncated": len(ordered) > PAIR_LIST_CAP,
        "total_pairs": len(ordered),
        "summary": summary,
        "denominator": adjudicated,
        "agreement": (agreed / adjudicated) if adjudicated else None,
    }


def stage_durations(store: Store,
                    filters: Optional[Mapping[str, Any]] = None
                    ) -> Dict[str, Any]:
    """Per-stage durations by driver (measured stage ends only).

    A stage duration runs from its capture to the next capture; the
    final capture of each run has no measured end and counts as
    missing, never zero. Groups over the sample cap are
    deterministically downsampled and flagged.
    """
    filters = dict(filters or {})
    where, params = store._where(filters)
    rows = store.query(
        f"SELECT driver, stage_timings_json FROM executions {where} "
        f"{'AND' if where else 'WHERE'} "
        f"stage_timings_json IS NOT NULL", params)
    total = store.query(
        f"SELECT COUNT(*) AS n FROM executions {where}", params)[0]["n"]
    groups: Dict[tuple, Dict[str, Any]] = {}
    for row in rows:
        try:
            import json as _json
            doc = _json.loads(row["stage_timings_json"] or "{}")
            entries = doc.get("stages") or []
        except ValueError:
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            key = (str(entry.get("stage", "?")), row["driver"])
            slot = groups.setdefault(key, {"values": [], "missing": 0})
            duration = entry.get("duration_ms")
            if isinstance(duration, bool) or not isinstance(
                    duration, (int, float)):
                slot["missing"] += 1
            else:
                slot["values"].append(duration)
    stages = []
    for (stage, driver), slot in sorted(groups.items()):
        values = sorted(slot["values"])
        sampled = False
        if len(values) > STAGE_VALUE_SAMPLE_CAP:
            step = len(values) / STAGE_VALUE_SAMPLE_CAP
            values = sorted(values[int(i * step)]
                            for i in range(STAGE_VALUE_SAMPLE_CAP))
            sampled = True
        n = len(values)
        stages.append({
            "stage": stage, "driver": driver, "n": n,
            "missing_durations": slot["missing"],
            "avg_ms": (round(sum(values) / n, 1) if n else None),
            **_percentiles([int(v) for v in values], [50, 90, 95]),
            "sampled": sampled,
        })
    return {"stages": stages, "rows_with_timings": len(rows),
            "rows_without_timings": total - len(rows)}


def campaign_trends(store: Store,
                    filters: Optional[Mapping[str, Any]] = None
                    ) -> Dict[str, Any]:
    """Success rate and latency across trial order (one campaign).

    Trials split into at most twelve sequential buckets; each
    bucket reports its own denominator. Campaign trial order is
    repetition-major, so the series reads as performance across
    repetitions. Without a single-campaign filter there is no
    shared trial order, and the buckets come back empty with a
    reason instead of a misleading merge.
    """
    filters = dict(filters or {})
    campaign = filters.get("campaign_id")
    if isinstance(campaign, list):
        campaign = campaign[0] if len(campaign) == 1 else None
    if not campaign:
        return {"buckets": [], "reason":
                "select a single campaign: trial order is only "
                "comparable within one campaign"}
    where, params = store._where(filters)
    rows = store.query(
        f"SELECT trial_seq, verdict, duration_ms FROM executions "
        f"{where} ORDER BY trial_seq", params)
    rows = [r for r in rows if r["trial_seq"] is not None]
    if not rows:
        return {"buckets": [], "reason": "no trials recorded yet"}
    n_buckets = min(12, len(rows))
    size = max(1, (len(rows) + n_buckets - 1) // n_buckets)
    buckets = []
    for start in range(0, len(rows), size):
        chunk = rows[start:start + size]
        verified = sum(1 for r in chunk if r["verdict"] in (
            "verified-success", "verified-failure"))
        ok = sum(1 for r in chunk
                 if r["verdict"] == "verified-success")
        durations = sorted(r["duration_ms"] for r in chunk
                           if r["duration_ms"] is not None)
        buckets.append({
            "lo": chunk[0]["trial_seq"], "hi": chunk[-1]["trial_seq"],
            "n": len(chunk), "verified": verified,
            "success_rate": (ok / verified) if verified else None,
            **_percentiles(durations, [50]),
        })
    return {"buckets": buckets}


def verification_coverage(store: Store,
                          filters: Optional[Mapping[str, Any]] = None
                          ) -> Dict[str, Any]:
    """Per-check satisfied/failed/unavailable counts."""
    filters = dict(filters or {})
    where, params = store._where(filters)
    join_where = where.replace("created_at", "e.created_at", 1) \
        if where else ""
    rows = store.query(
        f"SELECT v.check_id AS check_id, "
        f"SUM(CASE WHEN v.satisfied = 1 THEN 1 ELSE 0 END) AS satisfied, "
        f"SUM(CASE WHEN v.satisfied = 0 THEN 1 ELSE 0 END) AS failed, "
        f"SUM(CASE WHEN v.satisfied IS NULL THEN 1 ELSE 0 END) "
        f"AS unavailable, COUNT(*) AS n "
        f"FROM verification v JOIN executions e ON e.id = v.exec_id "
        f"{join_where} GROUP BY v.check_id ORDER BY v.check_id", params)
    return {"checks": rows}
