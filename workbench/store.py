"""SQLite storage for workbench executions and imported history.

Raw evidence (traces, snapshots, screenshots, action logs) stays as
files; this database holds the searchable index plus the per-action
and per-check rows that analytics aggregates without opening files.

Verdicts: ``verified-success`` (all P1–P3 satisfied),
``verified-failure`` (checks ran, at least one failed),
``insufficient-evidence`` (checks unavailable — never a success),
``pending`` (not finished). Missing numerics stay NULL, never zero.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

SCHEMA = """
CREATE TABLE IF NOT EXISTS executions (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    source TEXT NOT NULL,            -- 'workbench' | 'benchmark'
    source_ref TEXT,                 -- benchmark run id / file
    origin TEXT NOT NULL DEFAULT 'local', -- 'local' | 'external'
    session TEXT NOT NULL DEFAULT 'clean', -- 'clean' | 'user:<profile>'
    workflow_id TEXT NOT NULL,
    driver TEXT NOT NULL,            -- 'chimera' | 'baseline-a' | replay-* arms
    scenario_id TEXT NOT NULL,
    trial_kind TEXT NOT NULL,        -- 'measured' | 'warmup' | 'adhoc' | 'campaign'
    campaign_id TEXT,               -- campaign membership (NULL = standalone)
    trial_seq INTEGER,              -- 1-based trial order within a campaign
    sequence_id TEXT,               -- sequence membership (NULL = standalone)
    step_seq INTEGER,               -- 1-based step order within a sequence
    stage_timings_json TEXT,        -- per-stage durations (JSON, nullable)
    input_id TEXT,
    project_name TEXT,
    status TEXT NOT NULL,            -- queued|running|succeeded|failed|cancelled|error
    verdict TEXT NOT NULL,           -- verified-success|verified-failure|insufficient-evidence|pending
    duration_ms INTEGER,
    error TEXT,
    error_type TEXT,
    failure_category TEXT,
    retries INTEGER,
    actions_count INTEGER,
    trace_path TEXT,
    snapshot_path TEXT,
    screenshot_path TEXT,
    actions_path TEXT,
    progress_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_exec_source ON executions(source);
CREATE INDEX IF NOT EXISTS idx_exec_driver ON executions(driver);
CREATE INDEX IF NOT EXISTS idx_exec_scenario ON executions(scenario_id);
CREATE INDEX IF NOT EXISTS idx_exec_verdict ON executions(verdict);
CREATE INDEX IF NOT EXISTS idx_exec_created ON executions(created_at);
CREATE INDEX IF NOT EXISTS idx_exec_status ON executions(status);

CREATE TABLE IF NOT EXISTS campaigns (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    workflow_id TEXT NOT NULL,
    config_json TEXT NOT NULL,      -- validated campaign spec
    versions_json TEXT,             -- app + implementation versions
    status TEXT NOT NULL,           -- draft|running|paused|cancelled|completed|failed
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    total_trials INTEGER NOT NULL,
    finished_trials INTEGER NOT NULL DEFAULT 0,
    consecutive_errors INTEGER NOT NULL DEFAULT 0,
    current_exec_id TEXT,           -- live trial under execution
    stop_reason TEXT,
    error TEXT
);

CREATE TABLE IF NOT EXISTS sequences (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    spec_json TEXT NOT NULL,        -- validated sequence spec
    versions_json TEXT,             -- app + implementation versions
    status TEXT NOT NULL,           -- draft|running|paused|cancelled|completed|failed
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    total_steps INTEGER NOT NULL,
    finished_steps INTEGER NOT NULL DEFAULT 0,
    current_exec_id TEXT,           -- live step under execution
    stop_reason TEXT,
    error TEXT
);

CREATE TABLE IF NOT EXISTS actions (
    exec_id TEXT NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    seq INTEGER NOT NULL,
    ts TEXT,
    action_type TEXT NOT NULL,
    target_summary TEXT,
    outcome TEXT NOT NULL,           -- ok|error|skipped
    elapsed_ms INTEGER,
    error_type TEXT,
    PRIMARY KEY (exec_id, seq)
);
CREATE INDEX IF NOT EXISTS idx_actions_exec ON actions(exec_id);

CREATE TABLE IF NOT EXISTS verification (
    exec_id TEXT NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    check_id TEXT NOT NULL,          -- P1|P2|P3|S1..S5
    satisfied INTEGER,               -- 1|0|NULL (NULL = unavailable)
    detail TEXT,
    PRIMARY KEY (exec_id, check_id)
);

CREATE TABLE IF NOT EXISTS studio_workflows (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    environment TEXT NOT NULL,       -- 'demo' | 'saucedemo'
    env_params_json TEXT NOT NULL DEFAULT '{}',
    current_version INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS studio_versions (
    workflow_id TEXT NOT NULL REFERENCES studio_workflows(id),
    version INTEGER NOT NULL,
    definition_json TEXT NOT NULL,   -- validated step/variable definition
    created_at TEXT NOT NULL,
    PRIMARY KEY (workflow_id, version)
);
"""

LIST_COLUMNS = {
    "created_at", "completed_at", "driver", "scenario_id", "verdict",
    "status", "duration_ms", "workflow_id", "source", "trial_kind",
    "origin", "session", "campaign_id", "trial_seq",
    "sequence_id", "step_seq",
}

FILTER_COLUMNS = {
    "source", "driver", "scenario_id", "verdict", "status",
    "workflow_id", "trial_kind", "input_id", "origin", "session",
    "campaign_id", "sequence_id",
}


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _locked(method):
    """Serialize Store access across server/worker/monitor threads."""
    def wrapper(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    wrapper.__name__ = method.__name__
    return wrapper


class Store:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # One connection shared by server, worker, and monitor threads;
        # all access is serialized through _lock.
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.path),
                                     check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.executescript(SCHEMA)
            # Idempotent migration: matched-budget rows imported as
            # 'benchmark' before the three-origin split move to their
            # own label. Frozen run files are untouched.
            self._conn.execute(
                "UPDATE executions SET source='matched-budget' "
                "WHERE source='benchmark' AND "
                "(source_ref LIKE 'mb-v1:%' OR driver LIKE 'replay-%')")
            # Idempotent migration: pre-existing databases lack the
            # origin column; existing rows are local-application
            # history by construction.
            columns = [r[1] for r in self._conn.execute(
                "PRAGMA table_info(executions)").fetchall()]
            if "origin" not in columns:
                self._conn.execute(
                    "ALTER TABLE executions ADD COLUMN origin TEXT "
                    "NOT NULL DEFAULT 'local'")
                self._conn.execute(
                    "UPDATE executions SET origin='external' "
                    "WHERE workflow_id='saucedemo-order'")
            # Idempotent migration: campaign membership + stage
            # timings. Nullable: standalone history stays NULL.
            for column, ddl in (
                    ("campaign_id", "TEXT"),
                    ("trial_seq", "INTEGER"),
                    ("stage_timings_json", "TEXT"),
                    ("sequence_id", "TEXT"),
                    ("step_seq", "INTEGER")):
                if column not in columns:
                    self._conn.execute(
                        f"ALTER TABLE executions ADD COLUMN {column} {ddl}")
                    columns.append(column)
            # Idempotent migration: user sessions. Pre-existing rows
            # ran on clean sessions by construction (profiles did not
            # exist), so the backfilled default is exactly right.
            if "session" not in columns:
                self._conn.execute(
                    "ALTER TABLE executions ADD COLUMN session TEXT "
                    "NOT NULL DEFAULT 'clean'")
                columns.append("session")
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_exec_campaign "
                "ON executions(campaign_id)")
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_exec_sequence "
                "ON executions(sequence_id)")
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # -- writes --------------------------------------------------------

    @_locked
    def create_execution(self, record: Mapping[str, Any]) -> str:
        exec_id = str(record.get("id") or uuid.uuid4())
        row = {
            "id": exec_id,
            "created_at": record.get("created_at") or utcnow(),
            "completed_at": record.get("completed_at"),
            "source": record.get("source", "workbench"),
            "source_ref": record.get("source_ref"),
            "origin": record.get("origin", "local"),
            "session": record.get("session", "clean"),
            "workflow_id": record["workflow_id"],
            "driver": record["driver"],
            "scenario_id": record["scenario_id"],
            "trial_kind": record.get("trial_kind", "adhoc"),
            "campaign_id": record.get("campaign_id"),
            "trial_seq": record.get("trial_seq"),
            "sequence_id": record.get("sequence_id"),
            "step_seq": record.get("step_seq"),
            "stage_timings_json": record.get("stage_timings_json"),
            "input_id": record.get("input_id"),
            "project_name": record.get("project_name"),
            "status": record.get("status", "queued"),
            "verdict": record.get("verdict", "pending"),
            "duration_ms": record.get("duration_ms"),
            "error": record.get("error"),
            "error_type": record.get("error_type"),
            "failure_category": record.get("failure_category"),
            "retries": record.get("retries"),
            "actions_count": record.get("actions_count"),
            "trace_path": record.get("trace_path"),
            "snapshot_path": record.get("snapshot_path"),
            "screenshot_path": record.get("screenshot_path"),
            "actions_path": record.get("actions_path"),
            "progress_json": record.get("progress_json"),
        }
        cols = ", ".join(row)
        self._conn.execute(
            f"INSERT INTO executions ({cols}) "
            f"VALUES ({', '.join('?' for _ in row)})",
            list(row.values()),
        )
        self._conn.commit()
        return exec_id

    @_locked
    def update_execution(self, exec_id: str,
                         fields: Mapping[str, Any]) -> None:
        allowed = {
            "completed_at", "status", "verdict", "duration_ms", "error",
            "error_type", "failure_category", "retries", "actions_count",
            "trace_path", "snapshot_path", "screenshot_path",
            "actions_path", "progress_json", "project_name",
            "stage_timings_json",
        }
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return
        self._conn.execute(
            f"UPDATE executions SET {', '.join(f'{k}=?' for k in updates)} "
            f"WHERE id=?",
            [*updates.values(), exec_id],
        )
        self._conn.commit()

    @_locked
    def replace_actions(self, exec_id: str,
                        actions: Sequence[Mapping[str, Any]]) -> None:
        self._conn.execute("DELETE FROM actions WHERE exec_id=?", (exec_id,))
        self._conn.executemany(
            "INSERT INTO actions (exec_id, seq, ts, action_type, "
            "target_summary, outcome, elapsed_ms, error_type) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [(exec_id, a.get("seq", i), a.get("ts"),
              a.get("action_type", "?"), a.get("target_summary"),
              a.get("outcome", "ok"), a.get("elapsed_ms"),
              a.get("error_type"))
             for i, a in enumerate(actions)],
        )
        self._conn.commit()

    @_locked
    def replace_verification(
            self, exec_id: str,
            checks: Sequence[Mapping[str, Any]]) -> None:
        self._conn.execute(
            "DELETE FROM verification WHERE exec_id=?", (exec_id,))
        self._conn.executemany(
            "INSERT INTO verification (exec_id, check_id, satisfied, detail) "
            "VALUES (?, ?, ?, ?)",
            [(exec_id, c["check_id"],
              None if c.get("satisfied") is None else int(c["satisfied"]),
              c.get("detail"))
             for c in checks],
        )
        self._conn.commit()

    @_locked
    def delete_execution(self, exec_id: str) -> bool:
        cur = self._conn.execute(
            "DELETE FROM executions WHERE id=?", (exec_id,))
        self._conn.execute("DELETE FROM actions WHERE exec_id=?", (exec_id,))
        self._conn.execute(
            "DELETE FROM verification WHERE exec_id=?", (exec_id,))
        self._conn.commit()
        return cur.rowcount > 0

    # -- studio workflows ----------------------------------------------

    @_locked
    def create_studio_workflow(self, record: Mapping[str, Any]) -> str:
        workflow_id = str(record.get("id") or uuid.uuid4())
        now = utcnow()
        self._conn.execute(
            "INSERT INTO studio_workflows (id, name, description, "
            "environment, env_params_json, current_version, created_at, "
            "updated_at) VALUES (?, ?, ?, ?, ?, 0, ?, ?)",
            (workflow_id, record["name"],
             record.get("description", ""),
             record["environment"],
             json.dumps(record.get("env_params") or {}),
             now, now),
        )
        self._conn.commit()
        return workflow_id

    @_locked
    def save_studio_version(self, workflow_id: str,
                            definition: Mapping[str, Any]) -> int:
        row = self._conn.execute(
            "SELECT current_version FROM studio_workflows WHERE id=?",
            (workflow_id,)).fetchone()
        if row is None:
            raise KeyError(f"unknown studio workflow {workflow_id!r}")
        version = int(row["current_version"]) + 1
        self._conn.execute(
            "INSERT INTO studio_versions (workflow_id, version, "
            "definition_json, created_at) VALUES (?, ?, ?, ?)",
            (workflow_id, version, json.dumps(definition), utcnow()),
        )
        self._conn.execute(
            "UPDATE studio_workflows SET current_version=?, "
            "updated_at=? WHERE id=?",
            (version, utcnow(), workflow_id),
        )
        self._conn.commit()
        return version

    @_locked
    def get_studio_workflow(
            self, workflow_id: str,
            version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        row = self._conn.execute(
            "SELECT * FROM studio_workflows WHERE id=?",
            (workflow_id,)).fetchone()
        if row is None:
            return None
        record = dict(row)
        record["env_params"] = json.loads(
            record.get("env_params_json") or "{}")
        want = version if version is not None else record[
            "current_version"]
        ver = self._conn.execute(
            "SELECT version, definition_json, created_at "
            "FROM studio_versions WHERE workflow_id=? AND version=?",
            (workflow_id, want)).fetchone()
        versions = [r["version"] for r in self._conn.execute(
            "SELECT version FROM studio_versions WHERE workflow_id=? "
            "ORDER BY version", (workflow_id,)).fetchall()]
        record["versions"] = versions
        if ver is None:
            record["version"] = None
            record["definition"] = None
        else:
            record["version"] = ver["version"]
            record["definition"] = json.loads(ver["definition_json"])
            record["version_created_at"] = ver["created_at"]
        return record

    @_locked
    def list_studio_workflows(self) -> List[Dict[str, Any]]:
        return [dict(r) for r in self._conn.execute(
            "SELECT id, name, description, environment, current_version, "
            "created_at, updated_at FROM studio_workflows "
            "ORDER BY updated_at DESC").fetchall()]

    @_locked
    def clone_studio_workflow(self, workflow_id: str) -> str:
        source = self.get_studio_workflow(workflow_id)
        if source is None:
            raise KeyError(f"unknown studio workflow {workflow_id!r}")
        new_id = self.create_studio_workflow({
            "name": f"{source['name']} (copy)",
            "description": source.get("description", ""),
            "environment": source["environment"],
            "env_params": source.get("env_params") or {},
        })
        if source.get("definition") is not None:
            self.save_studio_version(new_id, source["definition"])
        return new_id

    # -- campaigns -----------------------------------------------------

    @_locked
    def create_campaign(self, record: Mapping[str, Any]) -> str:
        campaign_id = str(record.get("id") or uuid.uuid4())
        row = {
            "id": campaign_id,
            "name": record["name"],
            "workflow_id": record["workflow_id"],
            "config_json": record["config_json"],
            "versions_json": record.get("versions_json"),
            "status": record.get("status", "draft"),
            "created_at": record.get("created_at") or utcnow(),
            "started_at": record.get("started_at"),
            "completed_at": record.get("completed_at"),
            "total_trials": record["total_trials"],
            "finished_trials": record.get("finished_trials", 0),
            "consecutive_errors": record.get("consecutive_errors", 0),
            "current_exec_id": record.get("current_exec_id"),
            "stop_reason": record.get("stop_reason"),
            "error": record.get("error"),
        }
        cols = ", ".join(row)
        self._conn.execute(
            f"INSERT INTO campaigns ({cols}) "
            f"VALUES ({', '.join('?' for _ in row)})",
            list(row.values()),
        )
        self._conn.commit()
        return campaign_id

    @_locked
    def get_campaign(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        row = self._conn.execute(
            "SELECT * FROM campaigns WHERE id=?", (campaign_id,)).fetchone()
        if row is None:
            return None
        record = dict(row)
        for key in ("config_json", "versions_json"):
            if record.get(key):
                try:
                    record[key[0:-5]] = json.loads(record[key])
                except ValueError:
                    record[key[0:-5]] = None
            else:
                record[key[0:-5]] = None
        return record

    @_locked
    def list_campaigns(self) -> List[Dict[str, Any]]:
        return [dict(r) for r in self._conn.execute(
            "SELECT * FROM campaigns ORDER BY created_at DESC").fetchall()]

    @_locked
    def update_campaign(self, campaign_id: str,
                        fields: Mapping[str, Any]) -> None:
        allowed = {
            "status", "started_at", "completed_at", "finished_trials",
            "consecutive_errors", "current_exec_id", "stop_reason",
            "error", "config_json", "versions_json",
        }
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return
        self._conn.execute(
            f"UPDATE campaigns SET {', '.join(f'{k}=?' for k in updates)} "
            f"WHERE id=?",
            [*updates.values(), campaign_id],
        )
        self._conn.commit()

    @_locked
    def campaign_trial_counts(self, campaign_id: str) -> Dict[str, int]:
        rows = self._conn.execute(
            "SELECT status, COUNT(*) AS n FROM executions "
            "WHERE campaign_id=? GROUP BY status",
            (campaign_id,)).fetchall()
        return {r["status"]: r["n"] for r in rows}

    # -- sequences -----------------------------------------------------

    @_locked
    def create_sequence(self, record: Mapping[str, Any]) -> str:
        sequence_id = str(record.get("id") or uuid.uuid4())
        row = {
            "id": sequence_id,
            "name": record["name"],
            "spec_json": record["spec_json"],
            "versions_json": record.get("versions_json"),
            "status": record.get("status", "draft"),
            "created_at": record.get("created_at") or utcnow(),
            "started_at": record.get("started_at"),
            "completed_at": record.get("completed_at"),
            "total_steps": record["total_steps"],
            "finished_steps": record.get("finished_steps", 0),
            "current_exec_id": record.get("current_exec_id"),
            "stop_reason": record.get("stop_reason"),
            "error": record.get("error"),
        }
        cols = ", ".join(row)
        self._conn.execute(
            f"INSERT INTO sequences ({cols}) "
            f"VALUES ({', '.join('?' for _ in row)})",
            list(row.values()),
        )
        self._conn.commit()
        return sequence_id

    @_locked
    def get_sequence(self, sequence_id: str) -> Optional[Dict[str, Any]]:
        row = self._conn.execute(
            "SELECT * FROM sequences WHERE id=?", (sequence_id,)).fetchone()
        if row is None:
            return None
        record = dict(row)
        for key in ("spec_json", "versions_json"):
            if record.get(key):
                try:
                    record[key[0:-5]] = json.loads(record[key])
                except ValueError:
                    record[key[0:-5]] = None
            else:
                record[key[0:-5]] = None
        return record

    @_locked
    def list_sequences(self) -> List[Dict[str, Any]]:
        return [dict(r) for r in self._conn.execute(
            "SELECT * FROM sequences ORDER BY created_at DESC").fetchall()]

    @_locked
    def update_sequence(self, sequence_id: str,
                        fields: Mapping[str, Any]) -> None:
        allowed = {
            "status", "started_at", "completed_at", "finished_steps",
            "current_exec_id", "stop_reason", "error",
            "spec_json", "versions_json",
        }
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return
        self._conn.execute(
            f"UPDATE sequences SET {', '.join(f'{k}=?' for k in updates)} "
            f"WHERE id=?",
            [*updates.values(), sequence_id],
        )
        self._conn.commit()

    @_locked
    def sequence_step_counts(self, sequence_id: str) -> Dict[str, int]:
        rows = self._conn.execute(
            "SELECT status, COUNT(*) AS n FROM executions "
            "WHERE sequence_id=? GROUP BY status",
            (sequence_id,)).fetchall()
        return {r["status"]: r["n"] for r in rows}

    # -- reads ---------------------------------------------------------

    @_locked
    def get_execution(self, exec_id: str) -> Optional[Dict[str, Any]]:
        row = self._conn.execute(
            "SELECT * FROM executions WHERE id=?", (exec_id,)).fetchone()
        if row is None:
            return None
        record = dict(row)
        record["actions"] = [
            dict(r) for r in self._conn.execute(
                "SELECT seq, ts, action_type, target_summary, outcome, "
                "elapsed_ms, error_type FROM actions WHERE exec_id=? "
                "ORDER BY seq", (exec_id,))]
        record["checks"] = [
            dict(r) for r in self._conn.execute(
                "SELECT check_id, satisfied, detail FROM verification "
                "WHERE exec_id=? ORDER BY check_id", (exec_id,))]
        if record.get("progress_json"):
            try:
                record["progress"] = json.loads(record["progress_json"])
            except ValueError:
                record["progress"] = None
        else:
            record["progress"] = None
        return record

    @_locked
    def list_executions(
        self,
        *,
        filters: Optional[Mapping[str, Any]] = None,
        sort: str = "-created_at",
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """Paginated, filterable execution index (never full-table)."""
        where, params = self._where(filters or {})
        total = self._conn.execute(
            f"SELECT COUNT(*) FROM executions {where}", params).fetchone()[0]
        column = sort.lstrip("+-")
        if column not in LIST_COLUMNS:
            raise ValueError(f"cannot sort by {column!r}")
        direction = "DESC" if sort.startswith("-") else "ASC"
        page = max(1, int(page))
        page_size = min(500, max(1, int(page_size)))
        offset = (page - 1) * page_size
        rows = self._conn.execute(
            f"SELECT id, created_at, completed_at, source, source_ref, "
            f"origin, session, workflow_id, driver, scenario_id, "
            f"trial_kind, campaign_id, trial_seq, "
            f"sequence_id, step_seq, "
            f"input_id, project_name, status, verdict, duration_ms, "
            f"error_type, failure_category, retries, actions_count "
            f"FROM executions {where} "
            f"ORDER BY {column} {direction} LIMIT ? OFFSET ?",
            [*params, page_size, offset],
        ).fetchall()
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
            "rows": [dict(r) for r in rows],
        }

    @_locked
    def distinct(self, column: str,
               filters: Optional[Mapping[str, Any]] = None) -> List[Any]:
        if column not in FILTER_COLUMNS:
            raise ValueError(f"cannot facet by {column!r}")
        where, params = self._where(filters or {})
        return [r[0] for r in self._conn.execute(
            f"SELECT DISTINCT {column} FROM executions {where} "
            f"ORDER BY {column}", params).fetchall()]

    @_locked
    def exists(self, exec_id: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM executions WHERE id=?", (exec_id,)).fetchone()
        return row is not None

    @_locked
    def count(self, filters: Optional[Mapping[str, Any]] = None) -> int:
        where, params = self._where(filters or {})
        return self._conn.execute(
            f"SELECT COUNT(*) FROM executions {where}", params).fetchone()[0]

    def _where(self, filters: Mapping[str, Any]
               ) -> Tuple[str, List[Any]]:
        clauses: List[str] = []
        params: List[Any] = []
        for key, value in filters.items():
            if key in ("created_from", "created_to", "q"):
                continue
            if key not in FILTER_COLUMNS:
                raise ValueError(f"cannot filter by {key!r}")
            if value is None:
                continue
            values = list(value) if isinstance(value, (list, tuple)) else [value]
            values = [v for v in values if v is not None]
            if not values:
                continue
            clauses.append(
                f"{key} IN ({', '.join('?' for _ in values)})")
            params.extend(values)
        if "created_from" in filters and filters["created_from"]:
            clauses.append("created_at >= ?")
            params.append(filters["created_from"])
        if "created_to" in filters and filters["created_to"]:
            clauses.append("created_at <= ?")
            params.append(filters["created_to"])
        if "q" in filters and filters["q"]:
            clauses.append(
                "(project_name LIKE ? OR error LIKE ? OR id LIKE ?)")
            like = f"%{filters['q']}%"
            params.extend([like, like, like])
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        return where, params

    @_locked
    def query(self, sql: str, params: Sequence[Any] = ()) -> List[Dict]:
        """Read-only helper for the analytics layer."""
        return [dict(r) for r in
                self._conn.execute(sql, list(params)).fetchall()]
