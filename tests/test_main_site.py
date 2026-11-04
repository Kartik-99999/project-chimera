"""Browser tests for the Chimera multipage site.

Serves the repository root over local HTTP and drives the six-page
experience in Chromium: every page loads direct + refresh-safe, the
console stays clean, every displayed figure matches the frozen
run/manifest/plan/decision files (read independently in Python),
deep links into the Research Console resolve, and the mobile layout
holds together.
"""

import functools
import http.server
import json
import math
import threading
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
RUN_FILES = {
    "dev-20261028-chimera": "artifacts/dev-20261028/run-chimera.json",
    "dev-20261028-baseline-a": "artifacts/dev-20261028/run-baseline-a.json",
    "eval-20261028-chimera": "artifacts/eval-20261028/run-chimera.json",
    "eval-20261028-baseline-a": "artifacts/eval-20261028/run-baseline-a.json",
}
PAGES = {
    "/": "Chimera — a browser agent you can check up on",
    "/product/": "Product — how Chimera works",
    "/workflows/": "Workflows — what Chimera can run",
    "/demo/": "Demo — recorded executions",
    "/results/": "Results — what was measured",
    "/evidence/": "Evidence — where every result comes from",
}
# Selector proving each page's settled state (live figures painted).
SETTLED = {
    "/": '[data-fig="episodes"]',
    "/product/": "#portalStageNarrative",
    "/workflows/": ".wf-grid",
    "/demo/": '[data-journey="success"] svg',
    "/results/": '#matrix tbody tr th[scope="row"]',
    "/evidence/": "#coverage strong",
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
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()
    thread.join(timeout=5)


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        handle = p.chromium.launch()
        yield handle
        handle.close()


@pytest.fixture()
def errors():
    return []


def _open(browser, server, path, errs, width=1400, height=900):
    pg = browser.new_page(viewport={"width": width, "height": height})
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(f"{server}{path}", wait_until="networkidle")
    pg.wait_for_selector(SETTLED[path], timeout=20000)
    if path in ("/", "/product/", "/evidence/", "/results/"):
        pg.wait_for_function(
            "!document.querySelector('[data-fig=\"episodes\"]') "
            "|| !document.querySelector('[data-fig=\"episodes\"]').textContent.includes('…')",
            timeout=10000)
    return pg


@pytest.fixture()
def home(browser, server, errors):
    pg = _open(browser, server, "/", errors)
    yield pg
    assert not errors, f"console errors on /: {errors[:3]}"
    pg.close()


@pytest.fixture()
def results(browser, server, errors):
    pg = _open(browser, server, "/results/", errors)
    yield pg
    assert not errors, f"console errors on /results/: {errors[:3]}"
    pg.close()


@pytest.fixture()
def demo(browser, server, errors):
    pg = _open(browser, server, "/demo/", errors)
    yield pg
    assert not errors, f"console errors on /demo/: {errors[:3]}"
    pg.close()


@pytest.fixture()
def evidence(browser, server, errors):
    pg = _open(browser, server, "/evidence/", errors)
    yield pg
    assert not errors, f"console errors on /evidence/: {errors[:3]}"
    pg.close()


@pytest.fixture()
def product(browser, server, errors):
    pg = _open(browser, server, "/product/", errors)
    yield pg
    assert not errors, f"console errors on /product/: {errors[:3]}"
    pg.close()


# ---------- behavioral coverage (adapted from the single-page suite) ----------

def test_hero_figures_match_run_files(home):
    eps = [e for r in RUN_FILES for e in _measured(r)]
    fs = sum(1 for e in eps if e["agent_terminal_status"] == "succeeded"
             and (e.get("verification") or {}).get("status") == "verified"
             and (e.get("verification") or {}).get("all_satisfied") is False)
    home.wait_for_function(
        f"document.querySelector('[data-fig=\"episodes\"]').textContent.trim() === '{len(eps)}'",
        timeout=5000)
    assert (home.text_content('[data-fig="conditions"]') or "").strip() == "4"
    assert (home.text_content('[data-fig="falsesucc"]') or "").strip() == str(fs)
    assert str(len(eps)) in (home.text_content('[data-fig="falsesucc-den"]') or "")


def test_matrix_matches_run_files(results):
    for sc, n_chim, n_rep in (("S-NORM", 15, 15), ("S-SLOW", 75, 75),
                              ("S-DIS", 15, 15), ("S-SLOWDIS", 75, 75)):
        ceps = [e for e in _measured("eval-20261028-chimera") if e["scenario_id"] == sc]
        reps = [e for e in _measured("eval-20261028-baseline-a") if e["scenario_id"] == sc]
        assert len(ceps) == n_chim and len(reps) == n_rep
        ck = sum(1 for e in ceps if e["outcome"] == "succeeded")
        rk = sum(1 for e in reps if e["outcome"] == "succeeded")
        body = results.text_content("#matrix") or ""
        assert f"{ck}/{len(ceps)}" in body and f"{rk}/{len(reps)}" in body
    # Split toggle repaints from the dev runs.
    results.click('[data-split="development"]')
    results.wait_for_function(
        "document.querySelector('#matrix-interp').textContent.includes('S-NORM') "
        "|| document.querySelector('#matrix').textContent.includes('20/20')",
        timeout=5000)
    assert "20/20" in (results.text_content("#matrix") or "")


def test_terminal_and_latency_match_run_files(results):
    for run_id in ("eval-20261028-chimera", "eval-20261028-baseline-a"):
        failed = [e for e in _measured(run_id) if e["outcome"] != "succeeded"]
        correct = sum(1 for e in failed if e["agent_terminal_status"] == "failed")
        assert f"{correct}/{len(failed)}" in (results.text_content("#terminal-grid") or "")
    durs = sorted(e["duration_ms"] for e in _measured("eval-20261028-chimera"))
    p50 = durs[min(len(durs) - 1, max(0, math.ceil(0.5 * len(durs)) - 1))]
    assert f"p50 {p50} ms" in (results.text_content("#heldout") or "")


def test_matched_budget_and_sauce_match_files(results):
    mb = json.loads((ROOT / "experiments/matched-budget-v1/RESULTS.json").read_text(encoding="utf-8"))
    slow = mb["arms"]["mb-v1-chimera"]["by_scenario"]["S-SLOW"]
    assert slow["k"] == 5 and slow["n"] == 5
    body = results.text_content("#mb-table") or ""
    assert "5/5" in body and "0/5" in body
    assert "20/20" in (results.text_content("#mb-agree") or "")
    import csv as _csv
    with open(ROOT / "artifacts/sauce-stress-v2/trials.csv", newline="", encoding="utf-8") as fh:
        rows = list(_csv.DictReader(fh))
    assert len(rows) == 40
    succ = sum(1 for r in rows if r["verdict"] == "verified-success")
    checks = results.text_content("#sauce-checks") or ""
    assert "40" in checks  # T1 40/40
    summary = results.text_content("#sauce-summary") or ""
    assert f"{succ}" in summary and "40" in summary
    funnel = results.text_content("#sauce-funnel") or ""
    assert "40/40" in funnel and "16/40" in funnel


def test_journeys_follow_real_traces(demo):
    for trial, host in (("trial-0055", '[data-journey="success"]'),
                        ("trial-0100", '[data-journey="failure"]')):
        ep = next(e for e in _measured("eval-20261028-chimera") if e["trial_id"] == trial)
        trace = json.loads((ROOT / ep["trace_artifact"]).read_text(encoding="utf-8"))
        nodes = demo.query_selector_all(f"{host} .j-node")
        assert len(nodes) == len(trace["events"])
        label = demo.text_content(host) or ""
        assert ("done ✓" in label) != ("failed ✗" in label)


def test_coverage_and_review_match_evidence(evidence):
    cells = sum(len(_read_run(r)["cells"]) for r in RUN_FILES)
    eps = sum(len(_measured(r)) for r in RUN_FILES)
    body = evidence.text_content("#coverage") or ""
    assert str(cells) in body and str(eps) in body
    dec = json.loads((ROOT / "artifacts/eval-20261028/mini-review/decisions.json").read_text(encoding="utf-8"))
    vs = list(dec["decisions"].values())
    agree = sum(1 for v in vs if v["agreement"] == "agrees")
    facts = evidence.text_content("#review-facts") or ""
    assert f"{agree}/{len(vs)}" in facts
    assert "0 plan verdicts" in facts


def test_audit_status_matches_decisions(evidence):
    dec = json.loads((ROOT / "artifacts/audit-full-v1/review/decisions.json").read_text(encoding="utf-8"))
    n = len(dec.get("decisions") or {})
    body = evidence.text_content("#audit-status") or ""
    assert f"{n}/184" in body
    assert "in progress" in body.lower()


def test_research_deep_links_resolve(demo, server):
    demo.click("[data-trace-link] >> nth=0")
    demo.wait_for_selector("#main h1", timeout=15000)
    assert "trial-0055" in (demo.text_content("#main") or "")
    demo.goto(f"{server}/", wait_until="networkidle")
    demo.wait_for_selector('[data-fig="episodes"]', timeout=15000)
    demo.click('.site-foot a[href="/research/#/command"]')
    demo.wait_for_selector("#main h1", timeout=15000)
    assert "Command Center" in (demo.text_content("#main") or "")


def test_skip_link_lands_on_main(home):
    home.keyboard.press("Tab")
    assert home.evaluate("document.activeElement.className") == "skip-link"
    home.keyboard.press("Enter")
    assert home.evaluate("document.activeElement.id") == "main"


def test_page_titles_and_single_h1(browser, server):
    for path, title in PAGES.items():
        pg = browser.new_page()
        try:
            pg.goto(f"{server}{path}", wait_until="networkidle")
            pg.wait_for_selector(SETTLED[path], timeout=20000)
            assert pg.title() == title, path
            assert pg.query_selector_all("main h1").__len__() == 1, path
        finally:
            pg.close()


def test_mobile_layout(browser, server):
    pg = browser.new_page(viewport={"width": 390, "height": 844})
    try:
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(f"{server}/", wait_until="networkidle")
        pg.wait_for_selector('[data-fig="episodes"]', timeout=15000)
        # Narrow viewports collapse the center nav into a drawer.
        assert pg.is_visible("#menuBtn")
        assert not pg.is_visible(".site-nav")
        pg.click("#menuBtn")
        pg.wait_for_selector("#mobileDrawer .drawer-nav", timeout=5000)
        assert pg.is_visible('#mobileDrawer a[href="/results/"]')
        pg.click('#mobileDrawer a[href="/results/"]')
        pg.wait_for_selector('#matrix tbody tr th[scope="row"]', timeout=15000)
        assert "held-out episodes" in (pg.text_content("#main") or "")
        assert not errs
    finally:
        pg.close()


def test_reduced_motion_static_frame(browser, server):
    ctx = browser.new_context(viewport={"width": 1400, "height": 900}, reduced_motion="reduce")
    try:
        pg = ctx.new_page()
        pg.goto(f"{server}/", wait_until="networkidle")
        pg.wait_for_selector('[data-fig="episodes"]', timeout=15000)
        assert pg.eval_on_selector(".band", "el => getComputedStyle(el).opacity") == "1"
        pg.wait_for_function(
            "document.querySelector('[data-fig=\"episodes\"]').textContent.trim() === '520'",
            timeout=10000)
    finally:
        ctx.close()


def _pause_hero(page):
    if (page.get_attribute("#playPauseBtn", "aria-label") or "") == "Pause stage sequence":
        page.click("#playPauseBtn")


def test_demo_inspector_switches_real_traces(demo):
    for trial, key, passed in (("trial-0055", "success", True),
                               ("trial-0100", "failure", False)):
        ep = next(e for e in _measured("eval-20261028-chimera") if e["trial_id"] == trial)
        demo.click(f'[data-demo="{key}"]')
        demo.wait_for_function(
            f"document.querySelector('#demoTraceId').textContent.includes('{trial}')",
            timeout=5000)
        checks = (ep.get("verification") or {}).get("checks", [])
        met = sum(1 for c in checks if c["satisfied"])
        assert f"{met}/{len(checks)}" in (demo.text_content("#demoVerifierBadge") or "")
        preds = demo.text_content("#demoPredicatesList") or ""
        for c in checks:
            assert c["postcondition_id"] in preds
            assert (c["detail"] or "")[:24] in preds
        title = demo.text_content("#demoVerdictTitle") or ""
        assert ("VERIFIED PASS" in title) == passed
        obs = demo.text_content("#demoObservationBox") or ""
        assert str(ep["duration_ms"]) in obs
        assert ep["scenario_id"] in (demo.text_content("#demoTraceId") or "")
        assert "[object Object]" not in (demo.text_content("#demoInspector") or "")


def test_portal_stage_inspection(product):
    product.click("#portalBtn-3")
    assert "P1" in (product.text_content("#portalCodeSnippet") or "")
    assert "04" in (product.text_content("#portalStepTag") or "")
    assert "Threshold 04 / 05" in (product.text_content("#portalStageIndicator") or "")
    product.click("#portalBtn-1")
    product.wait_for_function(
        "document.querySelector('#portalStageNarrative').textContent.includes('520')",
        timeout=5000)


def test_dossier_modal_opens_tabs_and_closes(home):
    home.click("[data-open-dossier] >> nth=0")
    home.wait_for_selector("#dossierPane-studies", state="visible", timeout=5000)
    assert home.is_visible("#dossierPane-studies")
    home.click("#dossierTab-tokens")
    assert home.is_visible("#dossierPane-tokens")
    home.click("#dossierTab-evidence")
    home.wait_for_selector("#dossierFigures dl", timeout=10000)
    body = home.text_content("#dossierPane-evidence") or ""
    assert "520" in body and "104" in body and "72" in body
    home.keyboard.press("Escape")
    assert not home.is_visible("#dossierModal")


def test_no_horizontal_overflow(browser, server):
    for path in PAGES:
        for width, height in ((390, 844), (1024, 768), (1440, 900)):
            pg = browser.new_page(viewport={"width": width, "height": height})
            try:
                pg.goto(f"{server}{path}", wait_until="networkidle")
                pg.wait_for_selector(SETTLED[path], timeout=20000)
                pg.wait_for_timeout(800)
                assert pg.evaluate(
                    "document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"
                ), f"horizontal overflow at {width}px on {path}"
            finally:
                pg.close()


def test_white_foundation_and_stage_keyboard(home):
    assert home.evaluate("getComputedStyle(document.body).backgroundColor") == "rgb(255, 255, 255)"
    _pause_hero(home)
    home.click("#stageTab-0")
    home.keyboard.press("ArrowRight")
    assert home.get_attribute("#stageTab-1", "aria-selected") == "true"
    assert "STAGE 02/05" in (home.text_content("#stage-note") or "")


# ---------- multipage navigation coverage ----------

def test_every_page_loads_direct_and_refresh(browser, server):
    for path in PAGES:
        pg = browser.new_page(viewport={"width": 1400, "height": 900})
        try:
            errs = []
            pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            pg.on("pageerror", lambda e: errs.append(str(e)))
            # Direct GET with no prior navigation (fresh context each page).
            pg.goto(f"{server}{path}", wait_until="networkidle")
            pg.wait_for_selector(SETTLED[path], timeout=20000)
            assert (pg.text_content("main h1") or "").strip(), path
            pg.reload(wait_until="networkidle")
            pg.wait_for_selector(SETTLED[path], timeout=20000)
            assert (pg.text_content("main h1") or "").strip(), path
            assert not errs, f"console errors on {path}: {errs[:3]}"
        finally:
            pg.close()
    # Bare directory URLs redirect with a trailing slash (refresh-safe).
    pg = browser.new_page()
    try:
        resp = pg.goto(f"{server}/product", wait_until="networkidle")
        assert resp is not None and resp.ok
        assert pg.url.rstrip("/").endswith("/product") or pg.url.endswith("/product/")
        pg.wait_for_selector("#portalStageNarrative", timeout=20000)
    finally:
        pg.close()


def test_nav_dropdowns_and_app_links_resolve(browser, server):
    pg = browser.new_page(viewport={"width": 1400, "height": 900})
    try:
        pg.goto(f"{server}/", wait_until="networkidle")
        pg.wait_for_selector('[data-fig="episodes"]', timeout=15000)
        menus = pg.query_selector_all(".nav-drop")
        assert len(menus) == 5  # product, workflows, results, evidence, applications
        hrefs = pg.eval_on_selector_all(".nav-menu a", "els => els.map(e => e.getAttribute('href'))")
        assert len(hrefs) >= 15
        # Application surfaces use the TRUE hash URLs only.
        apps = [h for h in hrefs if h.startswith("/workbench/") or h.startswith("/research/")]
        assert "/workbench/web/#/workspace" in apps
        assert "/workbench/web/#/studio" in apps
        assert "/workbench/web/#/lab" in apps
        assert "/research/#/command" in apps
        assert not any(h in ("/workbench", "/studio", "/campaigns", "/research") for h in hrefs)
        # Every dropdown target resolves: page part 200, anchor part exists.
        for href in hrefs:
            part = urlsplit(href)
            with urllib.request.urlopen(f"{server}{part.path}") as resp:
                assert resp.status == 200, href
            if part.fragment and not part.path.startswith(("/workbench/", "/research/")):
                pg.goto(f"{server}{href}", wait_until="networkidle")
                assert pg.query_selector(f"#{part.fragment}"), href
        # Dropdowns open on hover and keyboard (ArrowDown from trigger).
        trigger = pg.query_selector('.site-nav .nav-drop > a[href="/product/"]')
        trigger.hover()
        pg.wait_for_selector('.nav-drop > a[href="/product/"][aria-expanded="true"]', timeout=5000)
        assert pg.is_visible('.nav-menu a[href="/product/#verify"]')
        trigger.focus()
        pg.keyboard.press("ArrowDown")
        assert pg.evaluate("document.activeElement.getAttribute('href')") == "/product/#arch"
        pg.keyboard.press("Escape")
        assert pg.evaluate("document.activeElement.getAttribute('href')") == "/product/"
        pg.goto(f"{server}/", wait_until="networkidle")
        pg.click(".site-nav >> text=Product")
        pg.wait_for_selector("#portalStageNarrative", timeout=15000)
        assert "How Chimera works" in (pg.text_content("#main") or "")
    finally:
        pg.close()


def _internal_refs(page):
    return page.evaluate("""() => {
      const out = [];
      document.querySelectorAll('a[href]').forEach(a => out.push(['a', a.getAttribute('href')]));
      document.querySelectorAll('img[src]').forEach(i => out.push(['img', i.getAttribute('src')]));
      document.querySelectorAll('link[href]').forEach(l => out.push(['link', l.getAttribute('href')]));
      document.querySelectorAll('script[src]').forEach(s => out.push(['script', s.getAttribute('src')]));
      return out;
    }""")


def test_no_broken_internal_links(browser, server):
    for path in PAGES:
        pg = browser.new_page()
        try:
            pg.goto(f"{server}{path}", wait_until="networkidle")
            pg.wait_for_selector(SETTLED[path], timeout=20000)
            for kind, href in _internal_refs(pg):
                assert href and not href.startswith("file://"), f"{path}: {kind} {href}"
                assert not href.startswith("http"), f"{path}: external {kind} {href}"
                if href.startswith("#") or href.startswith("mailto:"):
                    continue
                part = urlsplit(href)
                target = part.path or path
                with urllib.request.urlopen(f"{server}{target}") as resp:
                    assert resp.status == 200, f"{path}: {kind} {href}"
                    target_html = resp.read().decode("utf-8", "replace") \
                        if resp.headers.get_content_type() == "text/html" else ""
                if part.fragment and not target.startswith(("/workbench/", "/research/")) \
                        and not target.endswith((".md", ".json", ".svg", ".csv")):
                    if target.rstrip("/") == path.rstrip("/"):
                        assert pg.query_selector(f"#{part.fragment}"), f"{path}: missing #{part.fragment}"
                    else:
                        assert f'id="{part.fragment}"' in target_html, \
                            f"{path}: {target} missing #{part.fragment}"
        finally:
            pg.close()


def test_shared_footer_present(browser, server):
    for path in PAGES:
        pg = browser.new_page()
        try:
            pg.goto(f"{server}{path}", wait_until="networkidle")
            pg.wait_for_selector(SETTLED[path], timeout=20000)
            foot = pg.text_content(".site-foot") or ""
            for label in ("Application surfaces", "Sitemap", "Evidence", "chimera"):
                assert label in foot, f"{path} footer missing {label}"
            for dest in ("/workbench/web/#/workspace", "/workbench/web/#/studio",
                         "/workbench/web/#/lab", "/research/#/command"):
                assert pg.query_selector(f'.site-foot a[href="{dest}"]'), f"{path} missing {dest}"
            for dest in ("/", "/product/", "/workflows/", "/demo/", "/results/", "/evidence/"):
                assert pg.query_selector(f'.site-foot a[href="{dest}"]'), f"{path} missing {dest}"
        finally:
            pg.close()


def test_zero_console_errors_all_pages(browser, server):
    for path in PAGES:
        pg = browser.new_page(viewport={"width": 1400, "height": 900})
        try:
            errs = []
            pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(f"{server}{path}", wait_until="networkidle")
            pg.wait_for_selector(SETTLED[path], timeout=20000)
            pg.wait_for_timeout(1000)
            assert not errs, f"console errors on {path}: {errs[:3]}"
        finally:
            pg.close()
