"""Large-table performance tests on synthetic data (separate DB).

Builds a clearly labelled synthetic database (never mixed with
real history) and asserts the analytics queries behind Campaign
Lab stay fast and correct at scale, with server-side pagination.
"""

import time

import pytest

from workbench import analytics
from workbench.perf_fixture import NAME_PREFIX, SOURCE, build_synthetic_db
from workbench.store import Store

N_EXEC = 5000
BUDGET_SECONDS = 15.0


@pytest.fixture(scope="module")
def perf_db(tmp_path_factory):
    path = str(tmp_path_factory.mktemp("perf") / "perf.db")
    stats = build_synthetic_db(path, N_EXEC)
    assert stats["executions"] == N_EXEC
    store = Store(path)
    yield store
    store.close()


def _timed(label, func, *args):
    started = time.monotonic()
    result = func(*args)
    elapsed = time.monotonic() - started
    print(f"\nperf: {label} {elapsed:.2f}s")
    assert elapsed < BUDGET_SECONDS, f"{label} took {elapsed:.1f}s"
    return result


def test_synthetic_rows_are_labelled_and_counted(perf_db):
    assert perf_db.count() == N_EXEC
    rows = perf_db.list_executions(page_size=3)["rows"]
    assert all(r["source"] == SOURCE for r in rows)
    assert all(r["project_name"].startswith(NAME_PREFIX) for r in rows)
    assert perf_db.list_executions(
        filters={"source": "workbench"})["total"] == 0


def test_builder_refuses_non_synthetic_database(tmp_path):
    store = Store(tmp_path / "real.db")
    try:
        store.create_execution({
            "workflow_id": "create-project", "driver": "chimera",
            "scenario_id": "S-NORM", "trial_kind": "adhoc",
            "status": "succeeded", "verdict": "verified-success"})
    finally:
        store.close()
    with pytest.raises(ValueError, match="non-synthetic"):
        build_synthetic_db(str(tmp_path / "real.db"), 10)


def test_analytics_endpoints_stay_fast_at_scale(perf_db):
    assert _timed("overview", analytics.overview, perf_db, {})["total"] \
        == N_EXEC
    matrix = _timed("matrix", analytics.outcome_matrix, perf_db, {})
    assert sum(c["n"] for c in matrix["cells"]) == N_EXEC
    latency = _timed("latency", analytics.latency, perf_db, {})
    assert latency["overall"]["n"] == N_EXEC
    failures = _timed("failures", analytics.failures, perf_db, {})
    assert failures["total_failures"] > 0
    assert _timed("drivers", analytics.drivers, perf_db, {})["drivers"]
    stages = _timed("stages", analytics.stages, perf_db, {})
    assert sum(s["n"] for s in stages["stages"]) == N_EXEC * 6
    coverage = _timed("verification", analytics.verification_coverage,
                      perf_db, {})
    assert coverage["checks"]
    sauce = _timed("sauce", analytics.sauce, perf_db, {})
    assert sauce["total"] > 0
    paired = _timed("paired", analytics.paired_outcomes, perf_db, {})
    assert paired["total_pairs"] == 0  # no campaigns: nothing paired
    trends = _timed("trends", analytics.campaign_trends, perf_db, {})
    assert trends["buckets"] == []


def test_pagination_serves_slices_not_dumps(perf_db):
    first = perf_db.list_executions(sort="-created_at", page=1,
                                    page_size=50)
    assert first["total"] == N_EXEC
    assert len(first["rows"]) == 50
    assert first["pages"] == 100
    second = perf_db.list_executions(sort="-created_at", page=2,
                                     page_size=50)
    assert [r["id"] for r in first["rows"]] != [
        r["id"] for r in second["rows"]]
