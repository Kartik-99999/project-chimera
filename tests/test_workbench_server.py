"""Tests for the workbench HTTP API (live server, fake browsers)."""

import json
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest

from tests.test_workbench_executor import (
    FakeBrowser,
    FakePage,
    _fake_baseline_factory,
    _fake_chimera_factory,
)
from workbench.executor import Executor
from workbench.server import WorkbenchState, create_server
from workbench.store import Store


def _client(base):
    def call(method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            base + path, data=data, method=method,
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as res:
                raw = res.read()
                ctype = res.headers.get("Content-Type", "")
                if ctype.startswith("application/json"):
                    return res.status, json.loads(raw.decode())
                return res.status, raw
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            try:
                return exc.code, json.loads(raw.decode())
            except ValueError:
                return exc.code, raw
    return call


@pytest.fixture()
def server(tmp_path, monkeypatch):
    store = Store(tmp_path / "w.db")

    def fake_create_project(name, url=None, trace_dir=None, cancel=None,
                            observe=None, browser_factory=None):
        browser, context, wrapped = browser_factory(object())
        wrapped.goto(url)
        wrapped.get_by_label("Project Name").fill(name)
        wrapped.get_by_role("button", name="Create Project").click()
        observation = observe(wrapped) if observe else None
        trace_dir = Path(trace_dir)
        trace_dir.mkdir(parents=True, exist_ok=True)
        trace_path = trace_dir / "agent.json"
        trace_path.write_text(json.dumps({"run_id": "r",
                                          "events": []}),
                              encoding="utf-8")
        context.close()
        browser.close()
        return {"success": True, "status": "succeeded",
                "project_name": name, "error": None,
                "trace_path": str(trace_path), "run_id": "r",
                "observation": observation}

    monkeypatch.setattr("workbench.executor.create_project",
                        fake_create_project)
    state = WorkbenchState(
        tmp_path, store=store,
        executor=Executor(store, tmp_path / "wb",
                          chimera_factory=_fake_chimera_factory,
                          baseline_factory=_fake_baseline_factory))
    httpd = create_server(tmp_path, 0, state, static_dir=tmp_path)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    client = _client(base)
    client.base = base  # for raw-socket security tests below
    client.root = tmp_path  # ditto (static files are served from root)
    try:
        yield client, store
    finally:
        httpd.shutdown()
        httpd.server_close()
        store.close()


def _wait(call, exec_id, timeout=10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        status, body = call("GET", f"/api/workbench/executions/{exec_id}")
        assert status == 200
        if body["execution"]["status"] not in ("queued", "running"):
            return body["execution"]
        time.sleep(0.05)
    raise AssertionError("execution never finished")


def test_health_and_workflows(server):
    call, _ = server
    status, body = call("GET", "/api/workbench/health")
    assert (status, body["ok"]) == (200, True)
    status, body = call("GET", "/api/workbench/workflows")
    assert status == 200
    runnable = [w for w in body["workflows"] if not w["future"]]
    assert [w["workflow_id"] for w in runnable] == [
        "create-project", "fill-contact-form", "saucedemo-order",
        "saucedemo-stress", "flipkart-add-to-cart",
        "wikipedia-article-lookup", "wiktionary-word-lookup",
        "pypi-package-lookup", "bbc-headlines", "github-profile",
        "crates-lookup", "bbc-weather", "github-search",
        "steam-price-check", "arxiv-search", "stackoverflow-search",
        "amazon-price-check"]
    assert body["workflows"][0]["parameters"][0]["name"] == "project_name"


def test_start_poll_cancel_and_validation(server):
    call, _ = server
    status, body = call("POST", "/api/workbench/executions", {
        "workflow_id": "create-project", "driver": "chimera",
        "params": {"project_name": "Acme", "scenario": "normal"}})
    assert status == 201
    record = _wait(call, body["id"])
    assert record["verdict"] == "verified-success"
    assert len(record["actions"]) >= 3
    assert record["checks"][0]["check_id"] == "P1"
    status, body = call(
        "POST", f"/api/workbench/executions/{body['id'] if False else record['id']}/cancel")
    assert body == {"cancelled": False}  # already finished
    for bad in ({"workflow_id": "nope", "driver": "chimera", "params": {}},
                {"workflow_id": "create-project", "driver": "hal",
                 "params": {"project_name": "x"}},
                {"workflow_id": "create-project", "driver": "chimera",
                 "params": {"project_name": "x", "scenario": "normal",
                           "action_timeout_ms": 50}}):
        status, body = call("POST", "/api/workbench/executions", bad)
        assert status == 400
        assert "error" in body
    status, _ = call("GET", "/api/workbench/executions/missing")
    assert status == 404
    status, _ = call("POST", "/api/workbench/executions/missing/cancel")
    assert status == 404


def test_list_analytics_facets_export(server):
    call, store = server
    store.create_execution({
        "workflow_id": "create-project", "driver": "chimera",
        "scenario_id": "S-NORM", "project_name": "Acme",
        "status": "succeeded", "verdict": "verified-success",
        "duration_ms": 900})
    status, body = call(
        "GET", "/api/workbench/executions?driver=chimera&sort=-created_at")
    assert status == 200 and body["total"] == 1
    status, body = call("GET", "/api/workbench/executions?sort=-nope")
    assert status == 400
    status, body = call("GET", "/api/workbench/analytics/overview")
    assert status == 200
    assert body["total"] == 1
    assert body["verified_success_rate"] == 1.0
    assert body["durations"]["p50"] == 900
    status, body = call("GET", "/api/workbench/analytics/bogus")
    assert status == 404
    status, body = call("GET", "/api/workbench/facets")
    assert status == 200 and body["facets"]["driver"] == ["chimera"]
    status, raw = call("GET", "/api/workbench/export.csv")
    assert status == 200
    text = raw.decode()
    assert text.splitlines()[0].startswith("id,")
    assert "verified-success" in text


def test_artifacts_and_delete_rules(server):
    call, store = server
    shot = store.path.parent / "s.png"
    shot.write_bytes(b"png-bytes")
    wid = store.create_execution({
        "workflow_id": "create-project", "driver": "chimera",
        "scenario_id": "S-NORM", "status": "succeeded",
        "verdict": "verified-success", "screenshot_path": str(shot)})
    status, raw = call(
        "GET", f"/api/workbench/executions/{wid}/artifact?kind=screenshot")
    assert status == 200 and raw == b"png-bytes"
    status, _ = call(
        "GET", f"/api/workbench/executions/{wid}/artifact?kind=trace")
    assert status == 404
    status, _ = call(
        "GET", f"/api/workbench/executions/{wid}/artifact?kind=nope")
    assert status == 400
    bid = store.create_execution({
        "workflow_id": "create-project", "driver": "chimera",
        "scenario_id": "S-NORM", "source": "benchmark",
        "status": "succeeded", "verdict": "verified-success"})
    status, body = call("DELETE", f"/api/workbench/executions/{bid}")
    assert status == 403
    status, body = call("DELETE", f"/api/workbench/executions/{wid}")
    assert body == {"deleted": wid}
    status, _ = call("GET", f"/api/workbench/executions/{wid}")
    assert status == 404


def _studio_definition():
    return {
        "steps": [
            {"key": "go", "type": "navigate", "label": "Open",
             "url": "demo"},
            {"key": "end", "type": "verify-state", "label": "End",
             "assertions": [{"kind": "visible",
                             "selector": "#confirm"}]},
        ],
        "variables": [],
    }


def test_studio_crud_validate_and_clone(server):
    call, _ = server
    status, body = call("GET", "/api/workbench/studio/meta")
    assert status == 200
    assert "navigate" in body["step_types"]
    status, body = call("POST", "/api/workbench/studio/workflows",
                        {"name": "  ", "environment": "demo"})
    assert status == 400
    status, body = call("POST", "/api/workbench/studio/workflows",
                        {"name": "Demo flow", "environment": "demo"})
    assert status == 201
    wid = body["id"]
    status, body = call("GET", "/api/workbench/studio/workflows")
    assert status == 200
    assert [w["id"] for w in body["workflows"]] == [wid]
    status, body = call("POST", "/api/workbench/studio/validate",
                        {"definition": {"steps": []},
                         "environment": "demo"})
    assert status == 200
    assert body["errors"] and body["errors"][0]["code"] == "no-steps"
    status, body = call(
        "POST", f"/api/workbench/studio/workflows/{wid}",
        {"definition": {"steps": []}})
    assert status == 400
    assert body["errors"]
    status, body = call(
        "POST", f"/api/workbench/studio/workflows/{wid}",
        {"definition": _studio_definition()})
    assert status == 200 and body["version"] == 1
    status, body = call(
        "GET", f"/api/workbench/studio/workflows/{wid}?version=1")
    assert status == 200
    assert body["workflow"]["version"] == 1
    assert len(body["workflow"]["definition"]["steps"]) == 2
    status, body = call(
        "POST", f"/api/workbench/studio/workflows/{wid}/clone")
    assert status == 201 and body["id"] != wid
    status, body = call(
        "GET", f"/api/workbench/studio/workflows/{body['id']}")
    assert status == 200
    assert body["workflow"]["version"] == 1
    status, _ = call("GET", "/api/workbench/studio/workflows/nope")
    assert status == 404


def test_studio_steps_artifact_and_stepshot(server):
    call, store = server
    traces = store.path.parent / "wb" / "traces"
    traces.mkdir(parents=True, exist_ok=True)
    trace = traces / "r1.json"
    trace.write_text(json.dumps({"run_id": "r1", "events": []}),
                     encoding="utf-8")
    (traces / "r1.steps.json").write_text(
        json.dumps({"run_id": "r1", "steps": []}), encoding="utf-8")
    shots = store.path.parent / "wb" / "screenshots"
    shots.mkdir(parents=True, exist_ok=True)
    (shots / "r1_s01.png").write_bytes(b"shot-bytes")
    eid = store.create_execution({
        "workflow_id": "studio:abc", "driver": "chimera",
        "scenario_id": "studio:demo:v1", "status": "succeeded",
        "verdict": "verified-success", "trace_path": str(trace)})
    status, raw = call(
        "GET", f"/api/workbench/executions/{eid}/artifact?kind=steps")
    assert status == 200 and raw["run_id"] == "r1"
    status, raw = call(
        "GET", f"/api/workbench/executions/{eid}/artifact"
               "?kind=stepshot&ref=r1_s01.png")
    assert status == 200 and raw == b"shot-bytes"
    status, _ = call(
        "GET", f"/api/workbench/executions/{eid}/artifact"
               "?kind=stepshot&ref=../w.db")
    assert status == 400
    status, _ = call(
        "GET", f"/api/workbench/executions/{eid}/artifact"
               "?kind=stepshot&ref=missing.png")
    assert status == 404
    status, body = call("GET", f"/api/workbench/executions/{eid}")
    assert status == 200
    assert body["execution"]["steps_available"] is True


def test_profile_rejected_for_clean_only_workflow(server, tmp_path,
                                                 monkeypatch):
    call, _ = server
    monkeypatch.setenv("CHIMERA_PROFILES_DIR", str(tmp_path / "profiles"))
    status, body = call("POST", "/api/workbench/executions", {
        "workflow_id": "create-project", "driver": "chimera",
        "params": {"project_name": "Acme", "scenario": "normal"},
        "profile": "me"})
    assert status == 400
    assert "user sessions" in body["error"]
    status, body = call("POST", "/api/workbench/executions", {
        "workflow_id": "stackoverflow-search", "driver": "chimera",
        "params": {"query": "q"}, "profile": "ghost-profile-xyz"})
    assert status == 400
    assert "sessions login" in body["error"]


# -- HTTP boundary: Host / Origin / Content-Type ---------------------------


def _raw_request(base, payload):
    """Send raw HTTP bytes; returns (status, body_text)."""
    parsed = urllib.parse.urlparse(base)
    sock = socket.create_connection((parsed.hostname, parsed.port),
                                    timeout=10)
    try:
        sock.sendall(payload)
        sock.shutdown(socket.SHUT_WR)
        data = b""
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            data += chunk
    finally:
        sock.close()
    head, _, body = data.partition(b"\r\n\r\n")
    return int(head.split(b" ", 2)[1]), body.decode("utf-8", "replace")


def test_post_rejects_non_json_content_type(server):
    """text/plain cross-site POSTs must not be parsed (CSRF)."""
    call, _ = server
    status, body = _raw_request(call.base,
        b"POST /api/workbench/executions HTTP/1.1\r\n"
        b"Host: 127.0.0.1\r\n"
        b"Content-Type: text/plain\r\n"
        b"Content-Length: 2\r\n"
        b"Connection: close\r\n\r\n{}")
    assert status == 400, body
    assert "application/json" in body


def test_rejects_foreign_host(server):
    """A rebound DNS name must not reach the API (DNS rebinding)."""
    call, _ = server
    status, _body = _raw_request(call.base,
        b"GET /api/workbench/health HTTP/1.1\r\n"
        b"Host: attacker-rebind.example\r\n"
        b"Connection: close\r\n\r\n")
    assert status == 403


def test_rejects_foreign_origin_on_post(server):
    """Cross-origin POSTs are refused; same-origin POSTs pass through."""
    call, _ = server
    evil = _raw_request(call.base,
        b"POST /api/workbench/executions HTTP/1.1\r\n"
        b"Host: 127.0.0.1\r\n"
        b"Origin: https://evil.example\r\n"
        b"Content-Type: application/json\r\n"
        b"Content-Length: 2\r\n"
        b"Connection: close\r\n\r\n{}")
    assert evil[0] == 403, evil[1]
    port = urllib.parse.urlparse(call.base).port
    same = _raw_request(call.base,
        b"POST /api/workbench/executions HTTP/1.1\r\n"
        + f"Host: 127.0.0.1:{port}\r\n".encode()
        + f"Origin: http://127.0.0.1:{port}\r\n".encode()
        + b"Content-Type: application/json\r\n"
        b"Content-Length: 2\r\n"
        b"Connection: close\r\n\r\n{}")
    assert same[0] == 400, same[1]  # reached validation, not blocked
    assert "application/json" not in same[1]


def test_negative_content_length_rejected(server):
    """A negative Content-Length must not bypass the body cap."""
    call, _ = server
    valid = json.dumps({"definition": {"steps": [
        {"type": "navigate", "url": "demo"}]},
        "environment": "demo"}).encode()
    status, body = _raw_request(call.base,
        b"POST /api/workbench/studio/validate HTTP/1.1\r\n"
        b"Host: 127.0.0.1\r\n"
        b"Content-Type: application/json\r\n"
        b"Content-Length: -1\r\n"
        b"Connection: close\r\n\r\n" + valid)
    assert status == 400, body
    assert "too large" in body


def test_delete_requires_api_prefix(server):
    """DELETE outside /api/workbench/ must not delete anything."""
    call, _ = server
    status, created = call("POST", "/api/workbench/executions", {
        "workflow_id": "create-project", "driver": "chimera",
        "params": {"project_name": "PrefixCheck"}})
    assert status == 201, created
    exec_id = created["id"]
    status, _ = call("DELETE", f"/totally/bogus/executions/{exec_id}")
    assert status == 404
    status, record = call(
        "GET", f"/api/workbench/executions/{exec_id}")
    assert status == 200  # still there
    assert record["execution"]["id"] == exec_id


# -- static files: serve only the public allowlist -------------------------


def test_static_serves_root_not_cwd_and_denies_private_paths(server):
    """Static files come from --root, and only from public prefixes."""
    call, _ = server
    root = Path(call.root)
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs" / "probe-xyz.md").write_text("ok", encoding="utf-8")
    status, body = call("GET", "/docs/probe-xyz.md")
    assert status == 200 and body == b"ok"  # from root, not CWD
    assert call("GET", "/.gitignore")[0] == 404  # dotfiles denied
    assert call("GET", "/data/workbench.db")[0] == 404
    assert call("GET", "/w.db")[0] == 404  # the live DB is not public
    assert call("GET", "/workbench/server.py")[0] == 404
    assert call("GET", "/chimera-website/index.html")[0] == 404


def test_static_disables_directory_listings(server):
    """Directories resolve index.html but never list their contents."""
    call, _ = server
    root = Path(call.root)
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs" / "a.md").write_text("a", encoding="utf-8")
    assert call("GET", "/docs/")[0] == 404
    (root / "docs" / "index.html").write_text("<h1>hi</h1>",
                                              encoding="utf-8")
    status, body = call("GET", "/docs/")
    assert status == 200 and b"hi" in body


def test_security_headers_present(server):
    """Framing/clickjacking and MIME-sniffing headers are always sent."""
    call, _ = server
    parsed = urllib.parse.urlparse(call.base)

    import http.client
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port,
                                      timeout=10)
    try:
        conn.request("GET", "/api/workbench/health")
        res = conn.getresponse()
        res.read()
        assert res.getheader("X-Frame-Options") == "DENY"
        assert res.getheader("X-Content-Type-Options") == "nosniff"
        csp = res.getheader("Content-Security-Policy") or ""
        assert "frame-ancestors 'none'" in csp
    finally:
        conn.close()
