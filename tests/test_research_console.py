"""Browser tests for the Chimera research console.

Serves the repository root over local HTTP and drives every workspace
in Chromium: routes render, console stays clean, displayed figures
match the run files (read independently in Python), filters and
deep links work, the constellation navigates, and the mobile layout
holds together.
"""

import functools
import http.server
import json
import threading
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
RUN_FILES = {
    "dev-20261028-chimera": "artifacts/dev-20261028/run-chimera.json",
    "dev-20261028-baseline-a": "artifacts/dev-20261028/run-baseline-a.json",
    "eval-20261028-chimera": "artifacts/eval-20261028/run-chimera.json",
    "eval-20261028-baseline-a": "artifacts/eval-20261028/run-baseline-a.json",
}


def _read_run(run_id):
    with open(ROOT / RUN_FILES[run_id], encoding="utf-8") as fh:
        return json.load(fh)


def _measured(run_id):
    run = _read_run(run_id)
    return [e for e in run["episodes"] if not e["trial_id"].startswith("warmup:")]


@pytest.fixture(scope="module")
def server():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}/research/"
    httpd.shutdown()
    thread.join(timeout=5)


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        handle = p.chromium.launch()
        yield handle
        handle.close()


@pytest.fixture()
def page(browser, server):
    pg = browser.new_page(viewport={"width": 1400, "height": 900})
    pg.goto(server, wait_until="networkidle")
    pg.wait_for_selector("#main h1", timeout=15000)
    yield pg
    pg.close()


ROUTES = {
    "command": "Command Center",
    "map": "Constellation",
    "atlas": "Experiment Atlas",
    "observatory": "Evaluation Observatory",
    "failures": "Failure Cartography",
    "recovery": "Recovery Studio",
    "audit": "Audit & Reproducibility",
    "archive": "Research Archive",
    "terrain": "Outcome Terrain",
    "river": "Evidence River",
    "lineage": "Provenance Graph",
    "review": "Mini-review queue",
}


@pytest.mark.parametrize("route,title", sorted(ROUTES.items()))
def test_route_renders_cleanly(page, server, route, title):
    problems = []

    def on_console(msg):
        if msg.type == "error":
            problems.append(msg.text)

    def on_pageerror(err):
        problems.append(str(err))

    page.on("console", on_console)
    page.on("pageerror", on_pageerror)
    page.goto(f"{server}#/{route}", wait_until="networkidle")
    page.wait_for_selector("#main h1", timeout=15000)
    assert title in page.title()
    assert title in (page.text_content("#main h1") or "")
    assert problems == [], f"console/page errors on #/{route}: {problems[:3]}"


def test_unknown_route_shows_not_found(page, server):
    page.goto(f"{server}#/nope", wait_until="networkidle")
    page.wait_for_selector("#main h1", timeout=15000)
    assert "Route not found" in (page.text_content("#main h1") or "")


def test_command_figures_match_run_files(page, server):
    expected_measured = sum(len(_measured(r)) for r in RUN_FILES)
    expected_succ = sum(1 for r in RUN_FILES for e in _measured(r) if e["outcome"] == "succeeded")
    page.goto(f"{server}#/command", wait_until="networkidle")
    page.wait_for_selector(".stat-value", timeout=15000)
    body = page.text_content("#main") or ""
    assert str(expected_measured) in body
    assert f"{expected_succ}/{expected_measured}" in body
    # Provisional status must be visible, never a final claim.
    assert "provisional" in body.lower()
    assert "Production ready" not in body


def test_observatory_numbers_match_run_files(page, server):
    got = {}
    for e in _measured("eval-20261028-chimera"):
        got.setdefault(e["scenario_id"], [0, 0])[1] += 1
        if e["outcome"] == "succeeded":
            got[e["scenario_id"]][0] += 1
    page.goto(f"{server}#/observatory", wait_until="networkidle")
    page.wait_for_selector(".chart", timeout=15000)
    body = page.text_content("#main") or ""
    for sc, (k, n) in sorted(got.items()):
        assert f"{k}/{n}" in body, f"missing pooled {sc} figure {k}/{n}"


def test_atlas_filter_deep_link_and_row_navigation(page, server):
    page.goto(f"{server}#/atlas?scenario=S-SLOW&outcome=failed", wait_until="networkidle")
    page.wait_for_selector("#episodes tbody tr", timeout=15000)
    expected = [e for r in RUN_FILES for e in _measured(r)
                if e["scenario_id"] == "S-SLOW" and e["outcome"] == "failed"]
    assert f"{len(expected)} row(s)" in (page.text_content("#main") or "")
    first = page.query_selector("#episodes tbody tr.rowlink")
    assert first is not None
    trial = first.query_selector("a").text_content().strip()
    first.click()
    page.wait_for_function(
        f"document.querySelector('#main h1') && document.querySelector('#main h1').textContent.includes('{trial}')",
        timeout=15000)


def test_evidence_shows_trace_verdict_and_human_review(page, server):
    plan = json.loads((ROOT / "artifacts/dev-20261028/run-chimera.audit-plan.json").read_text(encoding="utf-8"))
    trial = next(iter(next(iter(plan["cells"].values()))["verdicts"]))
    page.goto(f"{server}#/evidence/dev-20261028-chimera/{trial}", wait_until="networkidle")
    page.wait_for_selector("#ev-trace li, #ev-trace .banner", timeout=15000)
    body = page.text_content("#main") or ""
    for token in ("P1", "P2", "P3", "agrees with verifier", "confirmation_visible"):
        assert token in body, f"missing evidence token: {token}"


def test_constellation_node_opens_workspace(page, server):
    page.goto(f"{server}#/map", wait_until="networkidle")
    page.wait_for_selector(".const-node", timeout=15000)
    page.click('.const-node[data-node="sc:S-SLOW"]')
    panel = page.text_content("[data-panel]") or ""
    assert "S-SLOW" in panel
    page.click("[data-panel] a.btn")
    page.wait_for_function(
        "document.querySelector('#main h1') && document.querySelector('#main h1').textContent.includes('Evaluation Observatory')",
        timeout=15000)
    assert "scenario=S-SLOW" in page.url


def test_mobile_layout_and_nav(browser, server):
    pg = browser.new_page(viewport={"width": 390, "height": 844})
    try:
        pg.goto(f"{server}#/command", wait_until="networkidle")
        pg.wait_for_selector("#main h1", timeout=15000)
        assert pg.is_visible("#menu-btn")
        pg.click("#menu-btn")
        assert pg.is_visible('#nav-list a[data-route="audit"]')
        pg.click('#nav-list a[data-route="audit"]')
        pg.wait_for_function(
            "document.querySelector('#main h1') && document.querySelector('#main h1').textContent.includes('Audit')",
            timeout=15000)
        pg.goto(f"{server}#/map", wait_until="networkidle")
        pg.wait_for_selector(".node-list li a", timeout=15000)
    finally:
        pg.close()


def test_keyboard_navigation_reaches_workspaces(page, server):
    page.goto(f"{server}#/command", wait_until="networkidle")
    page.wait_for_selector("#main h1", timeout=15000)
    page.evaluate("document.querySelector('.skip-link').focus()")
    page.keyboard.press("Enter")
    page.wait_for_function("document.activeElement && document.activeElement.id === 'main'", timeout=5000)
    page.keyboard.press("Tab")
    tag = page.evaluate("document.activeElement && document.activeElement.tagName")
    assert tag in ("A", "BUTTON", "INPUT", "SELECT", "SUMMARY"), f"Tab stopped on {tag}"
    page.evaluate("document.querySelector('#nav-list a[data-route=\"failures\"]').focus()")
    page.keyboard.press("Enter")
    page.wait_for_function(
        "document.querySelector('#main h1') && document.querySelector('#main h1').textContent.includes('Failure Cartography')",
        timeout=15000)


def _cell_trials(run_id):
    """Positional cell->episode mapping, mirroring benchmarks/audit.py."""
    run = _read_run(run_id)
    measured = [e for e in run["episodes"] if not e["trial_id"].startswith("warmup:")]
    out, cursor = [], 0
    for cell in run["cells"]:
        owned = measured[cursor:cursor + cell["trials"]]
        assert all(e["scenario_id"] == cell["scenario_id"] and e["input_id"] == cell["input_id"]
                   for e in owned), f"run order inconsistent in {run_id}"
        out.append((cell, owned))
        cursor += cell["trials"]
    assert cursor == len(measured), f"trial counts do not sum in {run_id}"
    return out


def test_terrain_tiles_match_run_files(page, server):
    cells = _cell_trials("eval-20261028-chimera")
    page.goto(f"{server}#/terrain", wait_until="networkidle")
    page.wait_for_selector(".terrain-cell", timeout=15000)
    assert page.query_selector_all(".terrain-cell").__len__() == len(cells) == 36
    assert "180" in (page.text_content("#main") or "")
    first_cell, first_eps = cells[0]
    k = sum(1 for e in first_eps if e["outcome"] == "succeeded")
    assert f"{k}/{len(first_eps)}" in (page.text_content(".terrain-cell") or "")
    # Clicking a tile opens its inspection card with trial rows.
    page.click(".terrain-cell >> nth=0")
    page.wait_for_selector("#terrain-detail", timeout=15000)
    detail = page.text_content("#terrain-detail") or ""
    assert first_eps[0]["trial_id"] in detail
    assert "mirror baseline" in detail
    # Deep link to the same cell renders the same card.
    import json as _json
    import urllib.parse as _url
    key = f"{first_cell['scenario_id']}|{first_cell['input_id']}|{_json.dumps(first_cell.get('fault_params') or {}, sort_keys=True)}"
    page.goto(f"{server}#/terrain?cell={_url.quote(key, safe='')}", wait_until="networkidle")
    page.wait_for_selector("#terrain-detail", timeout=15000)
    assert first_eps[0]["trial_id"] in (page.text_content("#terrain-detail") or "")


def test_river_flows_match_run_files(page, server):
    expected = len(_measured("eval-20261028-chimera")) + len(_measured("eval-20261028-baseline-a"))
    page.goto(f"{server}#/river", wait_until="networkidle")
    page.wait_for_selector(".flow-link", timeout=15000)
    body = page.text_content("#main") or ""
    assert str(expected) in body  # every measured episode counted once per transition
    # The list alternative covers every rendered link.
    assert page.query_selector_all("table.data tbody tr").__len__() == \
        page.query_selector_all(".flow-link").__len__()
    # Clicking a flow segment filters the Atlas to those records.
    page.click(".flow-link >> nth=0")
    page.wait_for_function(
        "document.querySelector('#main h1') && document.querySelector('#main h1').textContent.includes('Experiment Atlas')",
        timeout=15000)
    assert "scenario=" in page.url or "baseline=" in page.url or "outcome=" in page.url


def test_signal_rows_match_run_files(page, server):
    page.goto(f"{server}#/observatory?scenario=S-SLOW", wait_until="networkidle")
    page.wait_for_selector("#signal-card svg", timeout=15000)
    rows = page.query_selector_all("#signal-card a[href*='#/atlas']")
    assert len(rows) == 30  # 15 S-SLOW cells x 2 baselines
    tip = rows[0].get_attribute("data-tip") or ""
    assert "95% Wilson" in tip
    # Pooled scope cards restate exact k/n from the run files.
    body = page.text_content("#signal-card") or ""
    for run_id in ("eval-20261028-chimera", "eval-20261028-baseline-a"):
        eps = [e for e in _measured(run_id) if e["scenario_id"] == "S-SLOW"]
        k = sum(1 for e in eps if e["outcome"] == "succeeded")
        assert f"{k}/{len(eps)}" in body
    assert "not a significance test" in body


def test_failure_topography_soundings(page, server):
    page.goto(f"{server}#/failures", wait_until="networkidle")
    page.wait_for_selector(".sounding", timeout=15000)
    assert page.query_selector_all(".sounding").__len__() == 24
    assert "24 soundings" in (page.text_content("#main") or "")
    # Sounding links open the scenario x baseline pool (fault filter disclosed).
    assert "cannot filter by fault level" in (page.text_content("#main") or "")
    page.click(".sounding >> nth=0")
    page.wait_for_function(
        "document.querySelector('#main h1') && document.querySelector('#main h1').textContent.includes('Experiment Atlas')",
        timeout=15000)
    assert "scenario=" in page.url and "baseline=" in page.url


def _scope_fixture():
    run = _read_run("eval-20261028-chimera")
    ep = next(e for e in run["episodes"] if e["trial_id"] == "trial-0001")
    trace = json.loads((ROOT / ep["trace_artifact"]).read_text(encoding="utf-8"))
    base = ep["trace_artifact"].rsplit("/", 1)[1].split(".")[0]
    acts = json.loads((ROOT / f"artifacts/eval-20261028/traces-chimera/{base}.actions.json").read_text(encoding="utf-8"))
    return trace, acts, ep


def test_episode_oscilloscope(page, server):
    trace, acts, ep = _scope_fixture()
    expected = len(trace["events"]) + len(acts["records"]) + len(ep["verification"]["checks"]) + 1
    page.goto(f"{server}#/evidence/eval-20261028-chimera/trial-0001", wait_until="networkidle")
    page.wait_for_selector(".scope-event", timeout=15000)
    assert page.query_selector_all(".scope-event").__len__() == expected
    # Zoom widens the strip instead of rescaling it.
    before = page.eval_on_selector("#ev-scope svg", "el => el.style.width")
    page.click("[data-zoom='in']")
    after = page.eval_on_selector("#ev-scope svg", "el => el.style.width")
    assert float(after.replace("px", "")) > float(before.replace("px", ""))
    # Selecting a mark shows its recorded fields and source link.
    page.click(".scope-event >> nth=0")
    page.wait_for_selector("#scope-detail h3", timeout=15000)
    assert "source:" in (page.text_content("#scope-detail") or "")


def test_provenance_graph(page, server):
    page.goto(f"{server}#/lineage", wait_until="networkidle")
    page.wait_for_selector(".lineage-node", timeout=15000)
    svg_nodes = page.query_selector_all(".lineage-node").__len__()
    assert svg_nodes > 15
    tables = page.text_content("#main") or ""
    assert "manifest_id" in tables and "run_id cited in report text" in tables
    # Selecting a node shows identifiers and dims non-neighbors.
    page.click(".lineage-node[data-node='run']")
    page.wait_for_function(
        "document.querySelector('#lineage-detail') && document.querySelector('#lineage-detail').textContent.includes('eval-20261028-chimera')",
        timeout=15000)
    assert page.query_selector_all(".lineage-node.dimmed").__len__() > 0
    # Search dims non-matching nodes without removing records.
    page.fill("#l-q", "trial-0001")
    page.press("#l-q", "Enter")
    # Poll until the post-navigation render lands: a bare selector
    # wait can match pre-navigation nodes while #main reloads.
    page.wait_for_function(
        "window.location.hash.includes('q=trial-0001')",
        timeout=15000)
    page.wait_for_function(
        "document.querySelector('.lineage-node.dimmed') && "
        "document.querySelector('#main').textContent.includes('trial-0001')",
        timeout=15000)
    assert "trial-0001" in (page.text_content("#main") or "")


def test_motion_toggle_persists(page, server):
    page.goto(f"{server}#/command", wait_until="networkidle")
    page.wait_for_selector("#motion-toggle", timeout=15000)
    assert (page.text_content("#motion-toggle") or "").strip() == "Motion: on"
    page.click("#motion-toggle")
    assert (page.text_content("#motion-toggle") or "").strip() == "Motion: off"
    assert page.evaluate("window.localStorage.getItem('chimera-motion')") == "off"
    page.reload(wait_until="networkidle")
    page.wait_for_selector("#motion-toggle", timeout=15000)
    assert (page.text_content("#motion-toggle") or "").strip() == "Motion: off"
    page.click("#motion-toggle")  # restore default for other tests


def test_reduced_motion_renders_static_frame(browser, server):
    ctx = browser.new_context(reduced_motion="reduce", viewport={"width": 1400, "height": 900})
    pg = ctx.new_page()
    try:
        problems = []
        pg.on("pageerror", lambda err: problems.append(str(err)))
        pg.goto(f"{server}#/terrain", wait_until="networkidle")
        pg.wait_for_selector(".terrain-cell", timeout=15000)
        assert pg.query_selector("#ambient") is not None
        assert problems == []
    finally:
        pg.close()
        ctx.close()


def test_viz_keyboard_activation(page, server):
    page.goto(f"{server}#/river", wait_until="networkidle")
    page.wait_for_selector(".flow-link", timeout=15000)
    page.evaluate("document.querySelector('.flow-link').focus()")
    page.keyboard.press("Enter")
    page.wait_for_function(
        "document.querySelector('#main h1') && document.querySelector('#main h1').textContent.includes('Experiment Atlas')",
        timeout=15000)
    page.goto(f"{server}#/evidence/eval-20261028-chimera/trial-0001", wait_until="networkidle")
    page.wait_for_selector(".scope-event", timeout=15000)
    page.evaluate("document.querySelector('.scope-event').focus()")
    page.keyboard.press("Enter")
    page.wait_for_selector("#scope-detail h3", timeout=15000)


def test_mini_review_queue_flow(page, server):
    page.goto(f"{server}#/review", wait_until="networkidle")
    page.wait_for_selector(".finding", timeout=15000)
    assert page.query_selector_all(".finding").__len__() == 8
    body = page.text_content("#main") or ""
    assert "0/8" in body and "IN PROGRESS" in body
    assert "no reliability claim" in body
    # Summary masks recorded verdicts until each episode is revealed.
    assert "•••" in body
    # Reviewer name is required before recording.
    page.fill("#rv-name", "browser-tester")
    page.evaluate("document.querySelector('#rv-name').dispatchEvent(new Event('change'))")
    page.click(".finding a >> nth=0")
    page.wait_for_selector("[data-testid='recorded-masked']", timeout=15000)
    assert page.query_selector("[data-testid='recorded-values']") is None
    # Reveal is gated: no reveal control exists before assessment is saved.
    assert page.query_selector("#rv-reveal") is None
    assert page.query_selector("#rv-reveal2") is None
    # First packet item is baseline-a trial-0009: a replay driver report.
    assert "trial-0009" in (page.text_content("#main") or "")
    assert "Replay steps" in (page.text_content("#main") or "")
    # Step 1: blinded assessment.
    page.select_option("#rv-assessment", "verified-success")
    page.select_option("#rv-sufficiency", "sufficient")
    page.fill("#rv-reason", "snapshot shows confirmation with the exact name")
    page.click("#rv-save-assessment")
    page.wait_for_selector("#rv-complete", timeout=15000)
    # Step 2: reveal, then judge agreement.
    page.click("#rv-reveal2")
    page.wait_for_selector("[data-testid='recorded-values']", timeout=15000)
    page.select_option("#rv-agreement", "agrees")
    page.click("#rv-complete")
    page.wait_for_selector("text=Recorded decision", timeout=15000)
    assert "assessed before reveal" in (page.text_content("#main") or "")
    # Queue reflects the recorded decision and survives reload.
    page.goto(f"{server}#/review", wait_until="networkidle")
    page.wait_for_selector(".finding", timeout=15000)
    assert "1/8" in (page.text_content("#main") or "")
    assert "verified success" in (page.text_content("#main") or "")
    page.reload(wait_until="networkidle")
    page.wait_for_selector(".finding", timeout=15000)
    assert "1/8" in (page.text_content("#main") or "")


def test_tooltip_does_not_survive_route_change(page, server):
    page.goto(f"{server}#/terrain", wait_until="networkidle")
    page.wait_for_selector(".terrain-cell", timeout=15000)
    page.hover(".terrain-cell >> nth=0")
    page.wait_for_selector(".viz-tip:not([hidden])", timeout=5000)
    page.goto(f"{server}#/observatory?scenario=S-SLOW", wait_until="networkidle")
    page.wait_for_selector("#signal-card svg", timeout=15000)
    assert page.eval_on_selector_all(
        ".viz-tip", "els => els.filter(e => !e.hidden).length") == 0


def test_archive_pdf_download(page, server):
    pdf = ROOT / "research" / "assets" / "research-archive.pdf"
    meta_path = ROOT / "research" / "assets" / "research-archive.meta.json"
    assert pdf.exists() and pdf.stat().st_size > 100_000
    assert pdf.read_bytes()[:5] == b"%PDF-"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["counts"]["episodes"] == sum(
        len(_read_run(r)["episodes"]) for r in RUN_FILES)
    assert meta["pdf_bytes"] == pdf.stat().st_size
    page.goto(f"{server}#/archive", wait_until="networkidle")
    page.wait_for_selector("#archive-pdf", timeout=15000)
    link = page.locator("#archive-pdf a[download]")
    assert link.count() == 1
    href = link.first.get_attribute("href")
    assert href.endswith("research-archive.pdf")
    origin = server.split("/research/")[0]
    resp = page.request.get(origin + href if href.startswith("/") else server + href)
    assert resp.status == 200
    assert resp.headers.get("content-type", "").startswith("application/pdf")
    assert len(resp.body()) == pdf.stat().st_size
    page.wait_for_function(
        "() => !document.querySelector('#archive-pdf-meta')"
        ".textContent.includes('in one document')", timeout=10000)
