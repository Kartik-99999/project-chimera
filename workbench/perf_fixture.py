"""Synthetic large-table performance fixture (NOT real results).

Builds a separate SQLite database full of clearly labelled
synthetic execution rows (``source='synthetic'``,
``project_name`` prefixed ``[synthetic]``) for measuring
analytics query performance at scale. The builder refuses to
touch any database that already holds non-synthetic rows, and
nothing here is ever imported into real benchmark or
application history.

Usage:
    python -m workbench.perf_fixture --db /tmp/perf.db --executions 100000
"""

from __future__ import annotations

import argparse
import random
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

from workbench.store import SCHEMA

SOURCE = "synthetic"
NAME_PREFIX = "[synthetic] "

SCENARIOS = [
    "S-NORM", "S-SLOW", "S-DIS", "S-SLOWDIS",
    "sauce:standard/backpack+bike-light/complete",
    "sauce:locked-out/backpack+bike-light/complete",
]
DRIVERS = ["chimera", "baseline-a"]
ACTIONS = ["navigate", "fill", "click", "select", "wait", "observe"]
CHECKS = ["P1", "P2", "P3", "S1", "S2", "S3", "S4", "S5"]


def _guard(cursor: sqlite3.Cursor) -> None:
    tables = {r[0] for r in cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    if "executions" not in tables:
        return
    foreign = cursor.execute(
        "SELECT COUNT(*) FROM executions WHERE source != ?",
        (SOURCE,)).fetchone()[0]
    if foreign:
        raise ValueError(
            f"refusing: database already holds {foreign} non-synthetic "
            f"execution rows")


def build_synthetic_db(path: str, n_executions: int,
                       actions_per_exec: int = 6,
                       seed: int = 20261030) -> Dict[str, Any]:
    """Create a synthetic perf database; returns build stats."""
    started = time.monotonic()
    rng = random.Random(seed)
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        _guard(conn.cursor())
        conn.executescript(SCHEMA)
        base_day = 1761700000  # fixed epoch: deterministic timestamps
        exec_rows: List[tuple] = []
        for i in range(n_executions):
            driver = DRIVERS[i % 2]
            scenario = SCENARIOS[i % len(SCENARIOS)]
            roll = rng.random()
            if roll < 0.62:
                status, verdict = "succeeded", "verified-success"
            elif roll < 0.90:
                status, verdict = "failed", "verified-failure"
            elif roll < 0.96:
                status, verdict = "failed", "insufficient-evidence"
            else:
                status, verdict = "error", "insufficient-evidence"
            created = base_day + (i * 37) % (14 * 86400)
            exec_rows.append((
                f"synth-{i:07d}",
                time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(created)),
                time.strftime("%Y-%m-%dT%H:%M:%SZ",
                              time.gmtime(created + 5)),
                SOURCE, None, "external"
                if scenario.startswith("sauce:") else "local",
                "saucedemo-order"
                if scenario.startswith("sauce:") else "create-project",
                driver, scenario,
                "measured" if i % 3 else "adhoc",
                None, None, None, None,
                f"{NAME_PREFIX}perf-{i}",
                status, verdict,
                int(rng.lognormvariate(7.2, 0.7)),
                "TimeoutError" if status == "error" else None,
                "action-error" if status == "error" else None,
                rng.randint(0, 3) if status != "succeeded" else 0,
                actions_per_exec,
                None, None, None, None, None,
            ))
        conn.executemany(
            "INSERT INTO executions (id, created_at, completed_at, "
            "source, source_ref, origin, workflow_id, driver, "
            "scenario_id, trial_kind, campaign_id, trial_seq, "
            "stage_timings_json, input_id, project_name, status, "
            "verdict, duration_ms, error_type, failure_category, "
            "retries, actions_count, trace_path, snapshot_path, "
            "screenshot_path, actions_path, progress_json) "
            f"VALUES ({', '.join('?' * 27)})", exec_rows)
        action_rows: List[tuple] = []
        for i in range(n_executions):
            for seq in range(1, actions_per_exec + 1):
                outcome = "error" if rng.random() < 0.04 else "ok"
                action_rows.append((
                    f"synth-{i:07d}", seq,
                    ACTIONS[(i + seq) % len(ACTIONS)],
                    f"synthetic target {seq}", outcome,
                    int(rng.lognormvariate(4.5, 0.9))
                    if outcome == "ok" else None,
                    "TimeoutError" if outcome == "error" else None,
                ))
        conn.executemany(
            "INSERT INTO actions (exec_id, seq, action_type, "
            "target_summary, outcome, elapsed_ms, error_type) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)", action_rows)
        check_rows: List[tuple] = []
        for i in range(n_executions):
            checks = CHECKS[3:] if i % len(SCENARIOS) >= 4 else CHECKS[:3]
            for check in checks:
                check_rows.append((
                    f"synth-{i:07d}", check,
                    1 if rng.random() < 0.7 else 0,
                    "synthetic check",
                ))
        conn.executemany(
            "INSERT INTO verification (exec_id, check_id, satisfied, "
            "detail) VALUES (?, ?, ?, ?)", check_rows)
        conn.commit()
        actions_n = len(action_rows)
        checks_n = len(check_rows)
    finally:
        conn.close()
    return {"executions": n_executions, "actions": actions_n,
            "checks": checks_n,
            "build_seconds": round(time.monotonic() - started, 1)}


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Build a synthetic analytics performance database.")
    parser.add_argument("--db", required=True)
    parser.add_argument("--executions", type=int, default=100000)
    parser.add_argument("--actions-per-exec", type=int, default=6)
    args = parser.parse_args(argv)
    stats = build_synthetic_db(args.db, args.executions,
                               args.actions_per_exec)
    print(f"built {stats['executions']} executions, "
          f"{stats['actions']} actions, {stats['checks']} checks "
          f"in {stats['build_seconds']}s -> {args.db}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
