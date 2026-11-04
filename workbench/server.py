"""Workbench server: one process serving the app, the API, and history.

``.venv/bin/python -m workbench.server`` serves the repository root
(so the Research Console, demo app, and frozen evidence keep their
URLs), the Workbench UI at ``/workbench/``, and a JSON API under
``/api/workbench/``. Standard library only: ``http.server`` +
``sqlite3``. On first start with an empty database, frozen benchmark
runs are imported as labelled history.
"""

from __future__ import annotations

import functools
import http.server
import json
import threading
import urllib.parse
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional

from workbench import analytics
from workbench.executor import Executor
from workbench.import_history import default_run_files, import_paths
from workbench.store import Store
from workbench.workflows import (
    WorkflowValidationError,
    get_workflow,
    list_workflows,
)

ROOT = Path(__file__).resolve().parent.parent
API_PREFIX = "/api/workbench"

#: Static files: only these public prefixes (and _STATIC_EXACT) are
#: served. Everything else — .git, data/, workbench sources, the
#: orphaned chimera-website/ clone — is a 404.
_STATIC_PREFIXES = (
    "/site/", "/research/", "/workbench/web/", "/demo_app/",
    "/artifacts/", "/docs/", "/experiments/",
    "/benchmarks/manifests/", "/data/screenshots/",
    "/product/", "/demo/", "/evidence/", "/results/", "/workflows/",
)
_STATIC_EXACT = (
    "/", "/index.html", "/favicon.ico",
    "/product", "/demo", "/evidence", "/results", "/workflows",
    "/site", "/research", "/workbench/web", "/demo_app",
    "/artifacts", "/docs", "/experiments",
)

ANALYTICS: Dict[str, Callable] = {
    "overview": analytics.overview,
    "matrix": analytics.outcome_matrix,
    "latency": analytics.latency,
    "failures": analytics.failures,
    "trends": analytics.trends,
    "stages": analytics.stages,
    "drivers": analytics.drivers,
    "workflows": analytics.workflows,
    "verification": analytics.verification_coverage,
    "sauce": analytics.sauce,
    "sauce-stress": analytics.sauce_stress,
    "paired": analytics.paired_outcomes,
    "stage-durations": analytics.stage_durations,
    "campaign-trends": analytics.campaign_trends,
}

_FACET_COLUMNS = ("source", "origin", "driver", "scenario_id", "verdict",
                  "status", "workflow_id", "trial_kind", "input_id",
                  "campaign_id")


class WorkbenchState:
    def __init__(self, root: Path, store: Optional[Store] = None,
                 executor: Optional[Executor] = None,
                 campaigns: Optional[Any] = None,
                 sequences: Optional[Any] = None):
        from workbench.campaigns import CampaignRunner
        from workbench.sequences import SequenceRunner

        self.root = root
        self.store = store or Store(root / "data" / "workbench.db")
        self.executor = executor or Executor(
            self.store, root / "data" / "workbench")
        self.campaigns = campaigns or CampaignRunner(
            self.store, self.executor)
        self.campaigns.recover()
        self.sequences = sequences or SequenceRunner(
            self.store, self.executor)
        self.sequences.recover()

    def ensure_history(self) -> Dict[str, int]:
        if self.store.count() > 0:
            return {"imported": 0, "skipped": 0, "files": 0}
        return import_paths(self.store, default_run_files(self.root))


def _filters(query: Mapping[str, list]) -> Dict[str, Any]:
    filters: Dict[str, Any] = {}
    for key in _FACET_COLUMNS:
        values = [v for v in query.get(key, []) if v != ""]
        if values:
            filters[key] = values[0] if len(values) == 1 else values
    for key in ("created_from", "created_to", "q"):
        if query.get(key, [""])[0]:
            filters[key] = query[key][0]
    return filters


class Handler(http.server.SimpleHTTPRequestHandler):
    state: WorkbenchState  # set by serve()

    def log_message(self, *args: Any) -> None:  # quieter than default
        pass

    def end_headers(self) -> None:  # noqa: N802 — stdlib naming
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        if not urllib.parse.urlparse(self.path).path.startswith(
                "/demo_app/"):
            # The toy demo app is the only page with inline scripts;
            # everything else runs external scripts + inline styles.
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: blob:; object-src 'none'; "
                "base-uri 'self'; frame-ancestors 'none'")
        super().end_headers()

    # -- routing --------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802 — stdlib naming
        if not self._boundary_ok():
            return
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ("/workbench", "/workbench/"):
            return self._redirect("/workbench/web/")
        if parsed.path.startswith(API_PREFIX + "/"):
            return self._api_get(parsed)
        if not self._static_allowed(parsed.path):
            return self._send(404, {"error": "unknown endpoint"})
        super().do_GET()

    def do_HEAD(self) -> None:  # noqa: N802
        if not self._boundary_ok():
            return
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith(API_PREFIX + "/") \
                or not self._static_allowed(parsed.path):
            self.send_response(404)
            self.end_headers()
            return
        super().do_HEAD()

    def list_directory(self, path: str) -> None:  # noqa: N802,ARG002
        """Directory listings are disabled; index.html still resolves."""
        self._send(404, {"error": "unknown endpoint"})
        return None

    @staticmethod
    def _static_allowed(path: str) -> bool:
        if path in _STATIC_EXACT or path.startswith(_STATIC_PREFIXES):
            for segment in path.split("/"):
                if segment.startswith("."):
                    return False
            lowered = path.lower()
            if lowered.endswith((".db", ".db-wal", ".db-shm",
                                 ".db-journal")):
                return False
            return True
        return False

    def do_POST(self) -> None:  # noqa: N802
        if not self._boundary_ok():
            return
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith(API_PREFIX + "/"):
            return self._api_post(parsed)
        self._send(404, {"error": "unknown endpoint"})

    def do_DELETE(self) -> None:  # noqa: N802
        if not self._boundary_ok():
            return
        parsed = urllib.parse.urlparse(self.path)
        if not parsed.path.startswith(API_PREFIX + "/"):
            return self._send(404, {"error": "unknown endpoint"})
        parts = parsed.path[len(API_PREFIX) + 1:].split("/")
        if len(parts) == 2 and parts[0] == "executions" and parts[1]:
            record = self.state.store.get_execution(parts[1])
            if record is None:
                return self._send(404, {"error": "unknown execution"})
            if record["source"] != "workbench":
                return self._send(403, {"error":
                    "benchmark history rows cannot be deleted"})
            if record["status"] in ("queued", "running"):
                return self._send(409, {"error":
                    "cannot delete a running execution"})
            self.state.store.delete_execution(parts[1])
            return self._send(200, {"deleted": parts[1]})
        self._send(404, {"error": "unknown endpoint"})

    # -- API ------------------------------------------------------------

    def _api_get(self, parsed: Any) -> None:
        parts = [p for p in parsed.path[len(API_PREFIX) + 1:].split("/")
                 if p]
        query = urllib.parse.parse_qs(parsed.query)
        store = self.state.store
        if parts == ["health"]:
            return self._send(200, {"ok": True,
                                    "executions": store.count()})
        if parts == ["workflows"]:
            return self._send(200, {"workflows": [
                w.to_dict() for w in list_workflows()]})
        if parts == ["facets"]:
            return self._send(200, {"facets": {
                column: store.distinct(column)
                for column in _FACET_COLUMNS}})
        if parts == ["executions"]:
            try:
                page = store.list_executions(
                    filters=_filters(query),
                    sort=query.get("sort", ["-created_at"])[0],
                    page=int(query.get("page", ["1"])[0]),
                    page_size=int(query.get("page_size", ["50"])[0]))
            except ValueError as exc:
                return self._send(400, {"error": str(exc)})
            return self._send(200, page)
        if len(parts) == 2 and parts[0] == "executions":
            record = store.get_execution(parts[1])
            if record is None:
                return self._send(404, {"error": "unknown execution"})
            record["stages_available"] = self._has_stages(record)
            record["steps_available"] = self._has_steps(record)
            return self._send(200, {"execution": record})
        if len(parts) == 3 and parts[0] == "executions" \
                and parts[2] == "artifact":
            kind = query.get("kind", [""])[0]
            if kind == "stepshot":
                return self._stepshot(parts[1],
                                      query.get("ref", [""])[0])
            return self._artifact(parts[1], kind)
        if len(parts) == 2 and parts[0] == "analytics" \
                and parts[1] in ANALYTICS:
            try:
                return self._send(200, ANALYTICS[parts[1]](
                    store, _filters(query)))
            except ValueError as exc:
                return self._send(400, {"error": str(exc)})
        if parts == ["campaigns"]:
            return self._send(200, {"campaigns":
                                    store.list_campaigns()})
        if len(parts) == 2 and parts[0] == "campaigns":
            record = store.get_campaign(parts[1])
            if record is None:
                return self._send(404, {"error": "unknown campaign"})
            record["trial_counts"] = store.campaign_trial_counts(
                parts[1])
            return self._send(200, {"campaign": record})
        if parts == ["sequences"]:
            return self._send(200, {"sequences":
                                    store.list_sequences()})
        if len(parts) == 2 and parts[0] == "sequences":
            record = store.get_sequence(parts[1])
            if record is None:
                return self._send(404, {"error": "unknown sequence"})
            record["step_counts"] = store.sequence_step_counts(
                parts[1])
            return self._send(200, {"sequence": record})
        if parts == ["export.csv"]:
            return self._export_csv(_filters(query))
        if parts == ["studio", "workflows"]:
            return self._send(200, {"workflows":
                                    store.list_studio_workflows()})
        if parts == ["studio", "meta"]:
            from workbench import studio as studio_module

            return self._send(200, {
                "step_types": list(studio_module.STEP_TYPES),
                "environments": list(studio_module.ENVIRONMENTS),
                "defaults": {
                    "timeout_ms": studio_module.DEFAULT_TIMEOUT_MS,
                    "max_attempts":
                        studio_module.DEFAULT_CHIMERA_ATTEMPTS,
                },
                "bounds": {
                    "timeout_ms": [studio_module.MIN_TIMEOUT_MS,
                                   studio_module.MAX_TIMEOUT_MS],
                    "max_attempts": [studio_module.MIN_ATTEMPTS,
                                     studio_module.MAX_ATTEMPTS],
                    "max_steps": studio_module.MAX_STEPS,
                },
            })
        if len(parts) == 3 and parts[0] == "studio" \
                and parts[1] == "workflows":
            version = query.get("version", [None])[0]
            try:
                pinned = int(version) if version is not None else None
            except ValueError:
                return self._send(400, {"error":
                                        "version must be a whole number"})
            record = store.get_studio_workflow(parts[2], pinned)
            if record is None:
                return self._send(404, {"error":
                                        "unknown studio workflow"})
            return self._send(200, {"workflow": record})
        self._send(404, {"error": "unknown endpoint"})

    def _api_post(self, parsed: Any) -> None:
        parts = [p for p in parsed.path[len(API_PREFIX) + 1:].split("/")
                 if p]
        if parts == ["executions"]:
            try:
                body = self._read_json()
            except ValueError as exc:
                return self._send(400, {"error": str(exc)})
            try:
                exec_id = self.state.executor.submit(
                    body.get("workflow_id", ""),
                    body.get("driver", ""),
                    body.get("params", {}),
                    profile=body.get("profile"))
            except WorkflowValidationError as exc:
                return self._send(400, {"error": str(exc)})
            return self._send(201, {"id": exec_id})
        if len(parts) == 3 and parts[0] == "executions" \
                and parts[2] == "cancel":
            if self.state.store.get_execution(parts[1]) is None:
                return self._send(404, {"error": "unknown execution"})
            cancelled = self.state.executor.cancel(parts[1])
            return self._send(200, {"cancelled": cancelled})
        if parts == ["import"]:
            try:
                result = import_paths(
                    self.state.store, default_run_files(self.state.root))
            except (OSError, ValueError) as exc:
                return self._send(500, {"error": str(exc)})
            result["total"] = self.state.store.count()
            return self._send(200, result)
        if parts == ["campaigns"]:
            try:
                body = self._read_json()
            except ValueError as exc:
                return self._send(400, {"error": str(exc)})
            try:
                campaign_id = self.state.campaigns.create(body)
            except WorkflowValidationError as exc:
                return self._send(400, {"error": str(exc)})
            return self._send(201, {"id": campaign_id})
        if parts == ["sequences"]:
            try:
                body = self._read_json()
            except ValueError as exc:
                return self._send(400, {"error": str(exc)})
            try:
                sequence_id = self.state.sequences.create(body)
            except WorkflowValidationError as exc:
                return self._send(400, {"error": str(exc)})
            return self._send(201, {"id": sequence_id})
        if parts == ["studio", "validate"]:
            from workbench import studio as studio_module

            try:
                body = self._read_json()
            except ValueError as exc:
                return self._send(400, {"error": str(exc)})
            definition = body.get("definition", body)
            if not isinstance(definition, dict):
                return self._send(400, {"error":
                                        "definition must be an object"})
            if body.get("environment") is not None:
                definition = {**definition,
                              "environment": body["environment"]}
            return self._send(200, {"errors":
                                    studio_module.validate_definition(
                                        definition)})
        if parts == ["studio", "workflows"]:
            from workbench import studio as studio_module

            try:
                body = self._read_json()
            except ValueError as exc:
                return self._send(400, {"error": str(exc)})
            name = (body.get("name") or "").strip()
            environment = body.get("environment")
            if not name:
                return self._send(400, {"error":
                                        "studio workflow name is required"})
            if len(name) > 120:
                return self._send(400, {"error":
                                        "name must be at most 120 "
                                        "characters"})
            if environment not in studio_module.ENVIRONMENTS:
                return self._send(400, {"error":
                                        "environment must be one of "
                                        f"{list(studio_module.ENVIRONMENTS)}"})
            param_errors = studio_module.validate_env_params(
                body.get("env_params"))
            if param_errors:
                return self._send(400, {"error": "; ".join(param_errors)})
            workflow_id = self.state.store.create_studio_workflow({
                "name": name,
                "description": body.get("description", ""),
                "environment": environment,
                "env_params": body.get("env_params") or {},
            })
            return self._send(201, {"id": workflow_id})
        if len(parts) == 3 and parts[0] == "studio" \
                and parts[1] == "workflows":
            from workbench import studio as studio_module

            try:
                body = self._read_json()
            except ValueError as exc:
                return self._send(400, {"error": str(exc)})
            record = self.state.store.get_studio_workflow(parts[2])
            if record is None:
                return self._send(404, {"error":
                                        "unknown studio workflow"})
            definition = body.get("definition")
            if not isinstance(definition, dict):
                return self._send(400, {"error":
                                        "definition must be an object"})
            definition = {**definition,
                          "environment": record["environment"],
                          "env_params": record.get("env_params") or {}}
            errors = studio_module.validate_definition(definition)
            if errors:
                return self._send(400, {"error": "definition invalid",
                                        "errors": errors})
            version = self.state.store.save_studio_version(
                parts[2], definition)
            return self._send(200, {"id": parts[2], "version": version})
        if len(parts) == 4 and parts[0] == "studio" \
                and parts[1] == "workflows" and parts[3] == "clone":
            try:
                new_id = self.state.store.clone_studio_workflow(parts[2])
            except KeyError:
                return self._send(404, {"error":
                                        "unknown studio workflow"})
            return self._send(201, {"id": new_id})
        if len(parts) == 3 and parts[0] == "campaigns" \
                and parts[2] in ("start", "pause", "resume", "cancel"):
            action = getattr(self.state.campaigns, parts[2])
            try:
                record = action(parts[1])
            except WorkflowValidationError as exc:
                message = str(exc)
                if message.startswith("unknown campaign"):
                    return self._send(404, {"error": message})
                return self._send(400, {"error": message})
            return self._send(200, {"campaign": record})
        if len(parts) == 3 and parts[0] == "sequences" \
                and parts[2] in ("start", "pause", "resume", "cancel"):
            action = getattr(self.state.sequences, parts[2])
            try:
                record = action(parts[1])
            except WorkflowValidationError as exc:
                message = str(exc)
                if message.startswith("unknown sequence"):
                    return self._send(404, {"error": message})
                return self._send(400, {"error": message})
            return self._send(200, {"sequence": record})
        self._send(404, {"error": "unknown endpoint"})

    def _stepshot(self, exec_id: str, ref: str) -> None:
        record = self.state.store.get_execution(exec_id)
        if record is None:
            return self._send(404, {"error": "unknown execution"})
        if not ref or "/" in ref or "\\" in ref or ".." in ref \
                or not ref.endswith(".png"):
            return self._send(400, {"error": "invalid shot reference"})
        shots = Path(self.state.executor.shots_dir)
        try:
            resolved = (shots / ref).resolve()
            resolved.relative_to(shots.resolve())
            data = resolved.read_bytes()
        except (OSError, ValueError):
            return self._send(404, {"error": "artifact unreadable"})
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _has_steps(self, record: Mapping[str, Any]) -> bool:
        from workbench import studio as studio_module

        sibling = studio_module.steps_path_for_trace(
            record.get("trace_path"))
        if not sibling:
            return False
        path = Path(sibling)
        if not path.is_absolute():
            path = self.state.root / path
        try:
            resolved = path.resolve()
            resolved.relative_to(self.state.root.resolve())
            return resolved.is_file()
        except (OSError, ValueError):
            return False

    def _has_stages(self, record: Mapping[str, Any]) -> bool:
        from adapters import saucedemo as sauce_adapter

        sibling = sauce_adapter.stages_path_for_trace(
            record.get("trace_path"))
        if not sibling:
            return False
        path = Path(sibling)
        if not path.is_absolute():
            path = self.state.root / path
        try:
            resolved = path.resolve()
            resolved.relative_to(self.state.root.resolve())
            return resolved.is_file()
        except (OSError, ValueError):
            return False

    def _artifact(self, exec_id: str, kind: str) -> None:
        from adapters import saucedemo as sauce_adapter

        record = self.state.store.get_execution(exec_id)
        if record is None:
            return self._send(404, {"error": "unknown execution"})
        mapping = {"trace": ("trace_path", "application/json"),
                   "snapshot": ("snapshot_path", "application/json"),
                   "actions": ("actions_path", "application/json"),
                   "screenshot": ("screenshot_path", "image/png")}
        raw: Optional[str]
        if kind == "stages":
            raw = sauce_adapter.stages_path_for_trace(
                record.get("trace_path"))
            content_type = "application/json"
        elif kind == "steps":
            from workbench import studio as studio_module

            raw = studio_module.steps_path_for_trace(
                record.get("trace_path"))
            content_type = "application/json"
        elif kind in mapping:
            column, content_type = mapping[kind]
            raw = record.get(column)
        else:
            return self._send(400, {"error":
                f"unknown artifact kind {kind!r}"})
        if not raw:
            return self._send(404, {"error": f"no {kind} for execution"})
        path = Path(raw)
        if not path.is_absolute():
            path = self.state.root / path
        try:
            resolved = path.resolve()
            resolved.relative_to(self.state.root.resolve())
            data = resolved.read_bytes()
        except (OSError, ValueError):
            return self._send(404, {"error": "artifact unreadable"})
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _export_csv(self, filters: Dict[str, Any]) -> None:
        import csv
        import io
        store = self.state.store
        output = io.StringIO()
        writer: Optional[Any] = None
        page = 1
        columns: list = []
        while True:
            chunk = store.list_executions(filters=filters, sort="created_at",
                                          page=page, page_size=500)
            if writer is None:
                columns = list(chunk["rows"][0].keys()) if chunk["rows"] \
                    else ["id"]
                writer = csv.DictWriter(output, fieldnames=columns,
                                        extrasaction="ignore")
                writer.writeheader()
            for row in chunk["rows"]:
                writer.writerow(row)
            if page >= chunk["pages"] or not chunk["rows"]:
                break
            page += 1
        data = output.getvalue().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/csv")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Content-Disposition",
                         "attachment; filename=chimera-executions.csv")
        self.end_headers()
        self.wfile.write(data)

    # -- helpers --------------------------------------------------------

    def _boundary_ok(self) -> bool:
        """Reject rebound hosts and cross-origin requests (403)."""
        host = (self.headers.get("Host") or "").strip().lower()
        name = host.split(":", 1)[0].strip("[]")
        if name not in ("127.0.0.1", "localhost"):
            self._send(403, {"error":
                "refusing request for non-loopback host"})
            return False
        origin = self.headers.get("Origin")
        if origin is not None:
            try:
                parts = urllib.parse.urlparse(origin)
            except Exception:  # noqa: BLE001 — fail closed
                parts = None
            if parts is None or parts.scheme != "http" \
                    or (parts.netloc or "").lower() != host:
                self._send(403, {"error":
                    "refusing cross-origin request"})
                return False
        site = (self.headers.get("Sec-Fetch-Site") or "").lower()
        if site and site not in ("same-origin", "none"):
            self._send(403, {"error": "refusing cross-site request"})
            return False
        return True

    def _read_json(self) -> Dict[str, Any]:
        ctype = (self.headers.get("Content-Type") or "").split(";")[0]
        if ctype.strip().lower() != "application/json":
            raise ValueError(
                "request body must be JSON "
                "(Content-Type: application/json)")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length < 0 or length > 1_000_000:
            raise ValueError("request body too large")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError):
            raise ValueError("request body must be JSON") from None
        if not isinstance(body, dict):
            raise ValueError("request body must be a JSON object")
        return body

    def _send(self, status: int, payload: Any) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _redirect(self, target: str) -> None:
        self.send_response(302)
        self.send_header("Location", target)
        self.end_headers()


def create_server(root: Path, port: int = 0,
                  state: Optional[WorkbenchState] = None,
                  static_dir: Optional[Path] = None
                  ) -> http.server.ThreadingHTTPServer:
    # ``root`` is the STATE root (database, traces, artifacts).
    # Static files always come from the package directory (or the
    # explicit ``static_dir`` in tests) — never from CWD or --root.
    handler = type("WorkbenchHandler", (Handler,), {})
    handler.state = state or WorkbenchState(root)
    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", port),
        functools.partial(handler,
                          directory=str(static_dir or ROOT)))
    server.daemon_threads = True
    return server


def main(argv: Optional[list] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="Chimera Workbench server")
    parser.add_argument("--port", type=int, default=8130)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--no-import", action="store_true",
                        help="skip the first-start history import")
    args = parser.parse_args(argv)
    root = Path(args.root)
    state = WorkbenchState(root)
    if not args.no_import:
        result = state.ensure_history()
        if result["files"]:
            print(f"imported {result['imported']} benchmark episodes "
                  f"as labelled history")
    server = create_server(root, args.port, state)
    port = server.server_address[1]
    print(f"Chimera Workbench: http://127.0.0.1:{port}/workbench/")
    print(f"Research Console:  http://127.0.0.1:{port}/research/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        state.store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
