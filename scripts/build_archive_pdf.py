#!/usr/bin/env python3
"""Build the Research Archive PDF: the whole archive dataset in one document.

Reads the same sources the console reads (mirrors research/js/data.js),
renders a print HTML file, then prints it to PDF with Playwright Chromium.
No new dependencies: stdlib + the Playwright already used by the tests.

Regenerate after any evidence change:
    .venv/bin/python scripts/build_archive_pdf.py

Outputs:
    research/assets/research-archive.pdf
    research/assets/research-archive.meta.json
"""

import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "research" / "assets"
PDF_PATH = OUT_DIR / "research-archive.pdf"
META_PATH = OUT_DIR / "research-archive.meta.json"

RUNS = [
    {"run_id": "dev-20261028-chimera", "file": "artifacts/dev-20261028/run-chimera.json",
     "baseline": "chimera", "split": "development"},
    {"run_id": "dev-20261028-baseline-a", "file": "artifacts/dev-20261028/run-baseline-a.json",
     "baseline": "baseline-a", "split": "development"},
    {"run_id": "eval-20261028-chimera", "file": "artifacts/eval-20261028/run-chimera.json",
     "baseline": "chimera", "split": "evaluation"},
    {"run_id": "eval-20261028-baseline-a", "file": "artifacts/eval-20261028/run-baseline-a.json",
     "baseline": "baseline-a", "split": "evaluation"},
]
PLANS = [
    {"run_id": "dev-20261028-chimera", "kind": "full", "file": "artifacts/dev-20261028/run-chimera.audit-plan.json"},
    {"run_id": "dev-20261028-baseline-a", "kind": "full", "file": "artifacts/dev-20261028/run-baseline-a.audit-plan.json"},
    {"run_id": "eval-20261028-chimera", "kind": "full", "file": "artifacts/eval-20261028/run-chimera.audit-plan.json"},
    {"run_id": "eval-20261028-baseline-a", "kind": "full", "file": "artifacts/eval-20261028/run-baseline-a.audit-plan.json"},
    {"run_id": "eval-20261028-chimera", "kind": "mini", "file": "artifacts/eval-20261028/run-chimera.audit-plan-mini.json"},
    {"run_id": "eval-20261028-baseline-a", "kind": "mini", "file": "artifacts/eval-20261028/run-baseline-a.audit-plan-mini.json"},
]
REPORTS = [
    {"id": "dev", "title": "Development report (initial)", "file": "artifacts/dev-20261028/report.md"},
    {"id": "dev-audited", "title": "Development report (audited)", "file": "artifacts/dev-20261028/report-audited.md"},
    {"id": "eval", "title": "Held-out evaluation report (provisional)", "file": "artifacts/eval-20261028/report.md"},
]
MANIFESTS = ["benchmarks/manifests/dev-v1.json", "benchmarks/manifests/eval-v1.json"]


def sha256(path):
    h = hashlib.sha256()
    with open(ROOT / path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def esc(t):
    return html.escape("" if t is None else str(t), quote=False)


def inline(t):
    t = esc(t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    return t


def md(src):
    """Mirror of the console md() in research/js/components.js."""
    out, in_list, in_code, table = [], False, False, []

    def flush_table():
        nonlocal table
        if not table:
            return
        rows = [r for r in table if not re.match(r"^\|[\s:-]+\|", r)]
        rows = [[c.strip() for c in r.split("|")[1:-1]] for r in rows]
        if rows:
            th = "".join(f"<th>{inline(c)}</th>" for c in rows[0])
            tr = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
                         for r in rows[1:])
            out.append(f"<table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>")
        table = []

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for line in str(src or "").split("\n"):
        if line.startswith("```"):
            close_list()
            flush_table()
            out.append("</code></pre>" if in_code else '<pre class="code"><code>')
            in_code = not in_code
            continue
        if in_code:
            out.append(esc(line) + "\n")
            continue
        if re.match(r"^\|.*\|$", line.strip()):
            close_list()
            table.append(line.strip())
            continue
        flush_table()
        m = re.match(r"^(#{1,3})\s+(.*)", line)
        if m:
            close_list()
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            continue
        if re.match(r"^---+$", line.strip()):
            close_list()
            out.append("<hr>")
            continue
        if re.match(r"^>\s?", line):
            close_list()
            quoted = re.sub(r"^>\s?", "", line)
            out.append(f"<blockquote>{inline(quoted)}</blockquote>")
            continue
        m = re.match(r"^[-*]\s+(.*)", line)
        if m:
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(m.group(1))}</li>")
            continue
        close_list()
        if line.strip():
            out.append(f"<p>{inline(line.strip())}</p>")
    close_list()
    flush_table()
    if in_code:
        out.append("</code></pre>")
    return '<div class="doc">' + "".join(out) + "</div>"


def val(x):
    """Unwrap {value, unavailable_reason} metric cells to a short string."""
    if isinstance(x, dict) and "value" in x and "unavailable_reason" in x:
        v = x["value"]
        if v is None:
            return "n/a"
        return val(v)
    if isinstance(x, dict):
        bits = []
        for k in ("mean_per_trial", "total", "p50", "p95", "mean", "value"):
            if k in x and x[k] is not None:
                bits.append(f"{k}={val(x[k])}")
        return "; ".join(bits) if bits else json.dumps(x)[:80]
    if isinstance(x, list):
        return f"{len(x)} items"
    return str(x)


def p3(ep):
    """Per-postcondition satisfied flags for one episode."""
    out = {}
    ver = (ep.get("verification") or {})
    for c in ver.get("checks") or []:
        pid = c.get("postcondition_id")
        if pid:
            out[pid] = c.get("satisfied")
    return out


def outcomes_compact(o):
    if not isinstance(o, dict):
        return String(o)
    return "; ".join(f"{k}={val(v)}" for k, v in o.items())


def tick(v):
    if v is True:
        return "yes"
    if v is False:
        return "no"
    return "—"


CSS = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { font-family: -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif;
  font-size: 9.5pt; line-height: 1.45; color: #111; margin: 0; }
@page { size: A4; margin: 16mm 13mm 16mm 13mm; }
h1 { font-size: 22pt; margin: 0 0 4px; letter-spacing: -0.01em; }
h2 { font-size: 14pt; margin: 26px 0 8px; border-bottom: 2px solid #111; padding-bottom: 4px; }
h3 { font-size: 11pt; margin: 18px 0 6px; }
.doc h1 { font-size: 16pt; } .doc h2 { font-size: 12pt; }
p, li { orphans: 3; widows: 3; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 12px;
  font-size: 7.6pt; line-height: 1.35; }
thead { display: table-header-group; }
tr { page-break-inside: avoid; }
th, td { border: 1px solid #bbb; padding: 2.5px 4px; text-align: left;
  vertical-align: top; word-break: break-word; }
th { background: #f0f0ee; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
code, pre.code { font-family: ui-monospace, Menlo, Consolas, monospace; }
pre.code, pre.json { font-size: 7.2pt; line-height: 1.4; background: #f6f6f4;
  border: 1px solid #ddd; padding: 8px; white-space: pre-wrap; word-break: break-word; }
blockquote { border-left: 3px solid #0e7490; margin: 8px 0; padding: 2px 10px; color: #333; }
hr { border: 0; border-top: 1px solid #ccc; margin: 14px 0; }
.cover { page-break-after: always; padding-top: 60px; }
.cover .sub { font-size: 12pt; color: #444; margin: 0 0 18px; }
.kv { display: grid; grid-template-columns: 170px 1fr; gap: 3px 12px; margin: 12px 0; }
.kv dt { font-weight: 600; } .kv dd { margin: 0; }
.sect { page-break-before: always; }
.badge { display: inline-block; border: 1px solid #999; border-radius: 20px;
  padding: 1px 10px; font-size: 8pt; margin: 0 6px 6px 0; }
.mono { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 7.6pt; }
ul { padding-left: 20px; }
"""


def cover_html(generated, counts, sources):
    rows = "".join(
        f"<tr><td class='mono'>{esc(p)}</td><td class='mono'>{sources[p][:16]}…</td></tr>"
        for p in sorted(sources))
    return f"""<div class="cover">
<h1>Chimera Research Archive</h1>
<p class="sub">The complete dataset behind the Research Console — every report,
every run, every episode, every audit plan, every manifest.</p>
<dl class="kv">
<dt>Generated</dt><dd>{esc(generated)} (UTC)</dd>
<dt>Reports</dt><dd>{counts['reports']} full texts</dd>
<dt>Runs</dt><dd>{counts['runs']} run files · {counts['episodes']} episodes
({counts['measured']} measured + {counts['warmups']} warm-ups)</dd>
<dt>Audit plans</dt><dd>{counts['plans']} plans · {counts['sampled']} sampled ·
{counts['verdicts']} verdicts</dd>
<dt>Manifests</dt><dd>{counts['manifests']}</dd>
</dl>
<p>Source files live in the repository; this PDF is a generated snapshot.
Regenerate with <code>.venv/bin/python scripts/build_archive_pdf.py</code>.
SHA-256 below pins the exact bytes this snapshot was built from.</p>
<table><thead><tr><th>Source file</th><th>SHA-256 (prefix)</th></tr></thead>
<tbody>{rows}</tbody></table>
</div>"""


def reports_html():
    parts = ['<div class="sect"><h2>1 · Reports (full text)</h2>']
    for i, r in enumerate(REPORTS):
        text = (ROOT / r["file"]).read_text(encoding="utf-8")
        lines = len(text.split("\n"))
        parts.append(f"<h3>1.{i + 1} · {esc(r['title'])}</h3>")
        parts.append(f"<p class='mono'>{esc(r['file'])} · {lines} lines</p>")
        parts.append(md(text))
    parts.append("</div>")
    return "".join(parts)


def run_identity_table(d):
    rows = [
        ("Run", d.get("run_id")), ("Benchmark", f"{d.get('benchmark_id')} v{d.get('benchmark_version')}"),
        ("Window", f"{d.get('started_at')} → {d.get('completed_at')}"),
        ("Status", d.get("status")),
        ("Manifest", f"{d.get('manifest_id')} v{d.get('manifest_version')} · sha {String(d.get('manifest_sha256'))[:16]}…"),
        ("Agent", d.get("agent_version")), ("Notes", d.get("notes")),
    ]
    body = "".join(f"<tr><th style='width:130px'>{esc(k)}</th><td class='mono'>{esc(v)}</td></tr>"
                   for k, v in rows)
    return f"<table><tbody>{body}</tbody></table>"


def String(v):
    return "" if v is None else str(v)


def cells_html(cells):
    head = ("<tr><th>Scenario</th><th>Input</th><th>Fault</th>"
            "<th class='num'>n</th><th>Outcomes</th><th class='num'>False&nbsp;succ</th>"
            "<th>Retries</th><th>Latency&nbsp;ms</th><th class='num'>Safety</th>"
            "<th class='num'>Unauth</th></tr>")
    rows = []
    for c in cells:
        fp = c.get("fault_params") or {}
        fault = f"slow={fp.get('slow_ms')} dis={fp.get('disabled')}"
        rows.append("<tr>"
                    f"<td class='mono'>{esc(c.get('scenario_id'))}</td>"
                    f"<td class='mono'>{esc(c.get('input_id'))}</td>"
                    f"<td class='mono'>{esc(fault)}</td>"
                    f"<td class='num'>{c.get('trials') if isinstance(c.get('trials'), int) else len(c.get('trials') or [])}</td>"
                    f"<td class='mono'>{esc(outcomes_compact(c.get('outcomes')))}</td>"
                    f"<td class='num'>{esc(val(c.get('false_successes')))}</td>"
                    f"<td class='mono'>{esc(val(c.get('retries')))}</td>"
                    f"<td class='mono'>{esc(val(c.get('latency_ms')))}</td>"
                    f"<td class='num'>{esc(val(c.get('safety_violations')))}</td>"
                    f"<td class='num'>{esc(val(c.get('unauthorized_actions')))}</td></tr>")
    return f"<table><thead>{head}</thead><tbody>{''.join(rows)}</tbody></table>"


def episodes_html(episodes):
    head = ("<tr><th>Trial</th><th>Scenario / input</th><th>Outcome</th>"
            "<th>P1</th><th>P2</th><th>P3</th>"
            "<th class='num'>ms</th><th class='num'>R</th><th>Fail / error</th><th>Trace</th></tr>")
    rows = []
    for e in episodes:
        flags = p3(e)
        fail = e.get("failure_category") or e.get("error") or ""
        rows.append("<tr>"
                    f"<td class='mono'>{esc(e.get('trial_id'))}</td>"
                    f"<td class='mono'>{esc(e.get('scenario_id'))} / {esc(e.get('input_id'))}</td>"
                    f"<td>{esc(e.get('outcome'))}</td>"
                    f"<td>{tick(flags.get('P1'))}</td><td>{tick(flags.get('P2'))}</td>"
                    f"<td>{tick(flags.get('P3'))}</td>"
                    f"<td class='num'>{esc(val(e.get('duration_ms')))}</td>"
                    f"<td class='num'>{esc(val(e.get('retries')))}</td>"
                    f"<td class='mono'>{esc(String(fail)[:90])}</td>"
                    f"<td class='mono'>{esc(String(e.get('trace_artifact')))}</td></tr>")
    return f"<table><thead>{head}</thead><tbody>{''.join(rows)}</tbody></table>"


def runs_html():
    parts = ['<div class="sect"><h2>2 · Run files (every episode)</h2>']
    for i, r in enumerate(RUNS):
        d = json.loads((ROOT / r["file"]).read_text(encoding="utf-8"))
        eps = d.get("episodes") or []
        cells = d.get("cells") or []
        parts.append(f"<h3>2.{i + 1} · {esc(r['run_id'])}</h3>")
        parts.append(f"<p><span class='badge'>{esc(r['split'])}</span>"
                     f"<span class='badge'>{esc(r['baseline'])}</span>"
                     f"<span class='badge'>{len(cells)} cells</span>"
                     f"<span class='badge'>{len(eps)} episodes</span></p>")
        parts.append(run_identity_table(d))
        for key in ("totals", "config", "environment"):
            if d.get(key) is not None:
                parts.append(f"<h3>{esc(key)}</h3>")
                parts.append(f"<pre class='json'>{esc(json.dumps(d[key], indent=2))}</pre>")
        parts.append(f"<h3>Cells ({len(cells)})</h3>")
        parts.append(cells_html(cells))
        parts.append(f"<h3>Episodes ({len(eps)})</h3>")
        parts.append(episodes_html(eps))
    parts.append("</div>")
    return "".join(parts)


def plans_html():
    parts = ['<div class="sect"><h2>3 · Audit plans</h2>']
    for i, p in enumerate(PLANS):
        d = json.loads((ROOT / p["file"]).read_text(encoding="utf-8"))
        cells = d.get("cells") or {}
        sampled = sum(len(c.get("sampled") or []) for c in cells.values())
        verdicts = sum(len((c.get("verdicts") or {})) for c in cells.values())
        parts.append(f"<h3>3.{i + 1} · {esc(p['file'].split('/')[-1])}</h3>")
        parts.append(f"<p><span class='badge'>{esc(p['run_id'])}</span>"
                     f"<span class='badge'>{esc(p['kind'])}</span>"
                     f"<span class='badge'>sample {esc(d.get('sample_size'))}</span>"
                     f"<span class='badge'>{sampled} sampled</span>"
                     f"<span class='badge'>{verdicts} verdicts</span></p>")
        rows = []
        for key in sorted(cells):
            c = cells[key]
            sms = c.get("sampled") or []
            v = c.get("verdicts") or {}
            sm_txt = "; ".join(
                f"{s.get('trial_id', s.get('trial', '?'))} [{s.get('agent_terminal_status', '?')}]"
                for s in sms) or "—"
            rows.append(f"<tr><td class='mono'>{esc(key)}</td>"
                        f"<td class='mono'>{esc(sm_txt)}</td>"
                        f"<td class='mono'>{esc(json.dumps(v)) if v else '—'}</td></tr>")
        parts.append("<table><thead><tr><th>Cell</th><th>Sampled trials</th><th>Verdicts</th></tr></thead>"
                     f"<tbody>{''.join(rows)}</tbody></table>")
    parts.append("</div>")
    return "".join(parts)


def manifests_html():
    parts = ['<div class="sect"><h2>4 · Manifests (verbatim)</h2>']
    for i, path in enumerate(MANIFESTS):
        d = json.loads((ROOT / path).read_text(encoding="utf-8"))
        parts.append(f"<h3>4.{i + 1} · {esc(path)}</h3>")
        parts.append(f"<pre class='json'>{esc(json.dumps(d, indent=2))}</pre>")
    parts.append("</div>")
    return "".join(parts)


def provenance_html(sources):
    rows = "".join(f"<tr><td class='mono'>{esc(p)}</td><td class='mono'>{h}</td></tr>"
                   for p, h in sorted(sources.items()))
    return (f'<div class="sect"><h2>5 · Provenance</h2>'
            f"<p>Full SHA-256 of every source file this snapshot was built from.</p>"
            f"<table><thead><tr><th>Source file</th><th>SHA-256</th></tr></thead>"
            f"<tbody>{rows}</tbody></table></div>")


def pdf_page_count(path):
    """Resolve the PDF catalog /Pages /Count without any PDF library."""
    raw = path.read_bytes()
    trailer = raw[raw.rfind(b"trailer"):]
    m = re.search(rb"/Root\s+(\d+)", trailer)
    root = re.search(rb"%s 0 obj(.*?)endobj" % m.group(1), raw, re.S).group(1)
    pages_id = re.search(rb"/Pages\s+(\d+)", root).group(1)
    pages = re.search(rb"%s 0 obj(.*?)endobj" % pages_id, raw, re.S).group(1)
    return int(re.search(rb"/Count\s+(\d+)", pages).group(1))


def build():
    from playwright.sync_api import sync_playwright

    sources = {}
    for r in RUNS:
        sources[r["file"]] = sha256(r["file"])
    for p in PLANS:
        sources[p["file"]] = sha256(p["file"])
    for r in REPORTS:
        sources[r["file"]] = sha256(r["file"])
    for m in MANIFESTS:
        sources[m] = sha256(m)

    n_eps = n_warm = 0
    for r in RUNS:
        d = json.loads((ROOT / r["file"]).read_text(encoding="utf-8"))
        for e in d.get("episodes") or []:
            n_eps += 1
            if str(e.get("trial_id", "")).startswith("warmup:"):
                n_warm += 1
    n_samp = n_ver = 0
    for p in PLANS:
        d = json.loads((ROOT / p["file"]).read_text(encoding="utf-8"))
        for c in (d.get("cells") or {}).values():
            n_samp += len(c.get("sampled") or [])
            n_ver += len((c.get("verdicts") or {}))
    counts = {"reports": len(REPORTS), "runs": len(RUNS), "episodes": n_eps,
              "measured": n_eps - n_warm, "warmups": n_warm,
              "plans": len(PLANS), "sampled": n_samp, "verdicts": n_ver,
              "manifests": len(MANIFESTS)}
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    doc = ("<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
           f"<title>Chimera Research Archive — complete data</title><style>{CSS}</style></head><body>"
           + cover_html(generated, counts, sources)
           + reports_html() + runs_html() + plans_html()
           + manifests_html() + provenance_html(sources)
           + "</body></html>")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = OUT_DIR / "_print.html"
    tmp.write_text(doc, encoding="utf-8")
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=["--no-sandbox"])
            pg = browser.new_page()
            pg.goto(tmp.as_uri(), wait_until="load")
            pg.pdf(path=str(PDF_PATH), format="A4", print_background=True,
                   margin={"top": "16mm", "bottom": "16mm", "left": "13mm", "right": "13mm"})
            browser.close()
    finally:
        tmp.unlink(missing_ok=True)

    meta = {"generated_at_utc": generated, "counts": counts,
            "pdf_bytes": PDF_PATH.stat().st_size,
            "pdf_pages": pdf_page_count(PDF_PATH), "sources": sources}
    META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    mb = meta["pdf_bytes"] / 1048576
    print(f"wrote {PDF_PATH} ({mb:.2f} MB) + {META_PATH}")
    print(f"counts: {json.dumps(counts)}")


if __name__ == "__main__":
    import sys
    keep = "--keep-html" in sys.argv
    if keep:
        _real_unlink = Path.unlink

        def _keep(self, *a, **k):
            if self.name == "_print.html":
                print(f"kept {self}")
                return
            return _real_unlink(self, *a, **k)

        Path.unlink = _keep
    build()


