"""Analyze matched-budget v1 runs: figures from evidence, SVG charts.

Reads experiments/matched-budget-v1/runs/main-*.json (never the
pilot), writes RESULTS.json + figures/*.svg. Every number in
REPORT.md must match RESULTS.json exactly.
"""

import json
import math
from pathlib import Path

EXP = Path(__file__).resolve().parent
RUNS = EXP / "runs"
FIGS = EXP / "figures"
ARMS = ["mb-v1-chimera", "mb-v1-replay-100", "mb-v1-replay-1000",
        "mb-v1-replay-2500", "mb-v1-replay-5000"]
SCENS = ["S-NORM", "S-SLOW", "S-DIS", "S-SLOWDIS"]
COLORS = {"mb-v1-chimera": "#39d0d8", "mb-v1-replay-100": "#8b96ad",
          "mb-v1-replay-1000": "#6ea8fe", "mb-v1-replay-2500": "#a78bfa",
          "mb-v1-replay-5000": "#4cc38a"}


def wilson(k, n, z=1.96):
    if n <= 0 or k < 0 or k > n:
        return None
    d = 1 + z * z / n
    c = (k / n + z * z / (2 * n)) / d
    s = z * math.sqrt((k / n) * (1 - k / n) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - s), 4), round(min(1.0, c + s), 4)]


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    m = min(b, c)
    p = sum(math.comb(n, i) for i in range(m + 1)) / 2 ** n
    return round(min(1.0, 2 * p), 4)


def load(arm):
    return json.loads((RUNS / f"main-{arm}.json").read_text(encoding="utf-8"))


def measured(run):
    return [e for e in run["episodes"] if not e["trial_id"].startswith("warmup:")]


def main():
    runs = {a: load(a) for a in ARMS}
    res = {"arms": {}, "paired": {}, "mcnemar": {}, "evidence": {}}
    for arm, run in runs.items():
        eps = measured(run)
        assert len(eps) == 20, (arm, len(eps))
        by_sc = {}
        for sc in SCENS:
            cell = [e for e in eps if e["scenario_id"] == sc]
            assert len(cell) == 5, (arm, sc, len(cell))
            k = sum(1 for e in cell if e["outcome"] == "succeeded")
            by_sc[sc] = {"k": k, "n": 5, "wilson95": wilson(k, 5)}
        durs = sorted(e["duration_ms"] for e in eps)
        res["arms"][arm] = {
            "by_scenario": by_sc,
            "timeouts": sum(1 for e in eps if "Timeout" in (e.get("error") or "")),
            "retries_values": sorted((e.get("retries") or {}).get("value") for e in eps),
            "terminals": {t: sum(1 for e in eps if e.get("agent_terminal_status") == t)
                          for t in set(e.get("agent_terminal_status") for e in eps)},
            "false_successes": sum(1 for e in eps if e["agent_terminal_status"] == "succeeded"
                                   and (e.get("verification") or {}).get("status") == "verified"
                                   and (e.get("verification") or {}).get("all_satisfied") is False),
            "durations_ms": {"min": durs[0], "p50": durs[9], "p95": durs[18], "max": durs[-1]},
            "outcomes": {o: sum(1 for e in eps if e["outcome"] == o)
                         for o in set(e["outcome"] for e in eps)},
        }
        res["evidence"][arm] = {
            "traces": sum(1 for e in eps if e.get("trace_artifact")),
            "verified": sum(1 for e in eps if (e.get("verification") or {}).get("status") == "verified"),
            "n": len(eps),
        }
    # Paired chimera vs replay-5000 (same cell + trial index).
    ceps = {(e["scenario_id"], e["trial_id"]): e for e in measured(runs["mb-v1-chimera"])}
    reps = {(e["scenario_id"], e["trial_id"]): e for e in measured(runs["mb-v1-replay-5000"])}
    assert set(ceps) == set(reps) and len(ceps) == 20
    def _zero():
        return {"both_succeed": 0, "both_fail": 0, "chimera_only": 0, "replay_only": 0}
    table = _zero()
    per_sc = {}
    for key in sorted(ceps):
        cs = ceps[key]["outcome"] == "succeeded"
        rs = reps[key]["outcome"] == "succeeded"
        cell = ("both_succeed" if cs and rs else "both_fail" if not cs and not rs
                else "chimera_only" if cs else "replay_only")
        table[cell] += 1
        per_sc.setdefault(key[0], _zero())
        per_sc[key[0]][cell] += 1
    res["paired"] = {"overall": table, "per_scenario": per_sc}
    res["mcnemar"] = {
        "b_chimera_only": table["chimera_only"], "c_replay_only": table["replay_only"],
        "exact_two_sided_p": mcnemar_exact(table["chimera_only"], table["replay_only"]),
        "note": "Exact McNemar on 20 pooled matched pairs; pooling mixes heterogeneous scenarios.",
    }
    (EXP / "RESULTS.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    fig_outcomes(res)
    fig_budget_response(res)
    fig_durations(res)
    print(json.dumps({
        "paired": table, "mcnemar_p": res["mcnemar"]["exact_two_sided_p"],
        "chimera_slow": res["arms"]["mb-v1-chimera"]["by_scenario"]["S-SLOW"],
        "r5000_slow": res["arms"]["mb-v1-replay-5000"]["by_scenario"]["S-SLOW"],
    }, indent=1))


def _svg_open(w, h, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" '
            f'aria-label="{title}" font-family="sans-serif">'
            f'<rect width="{w}" height="{h}" fill="#0c1119"/>')


def fig_outcomes(res):
    W, H, padL, padB, padT = 720, 360, 120, 80, 30
    plotW, plotH = W - padL - 20, H - padT - padB
    s = [_svg_open(W, H, "Successes out of 5 trials by scenario and arm")]
    s.append(f'<text x="12" y="20" fill="#e8ecf3" font-size="13" font-weight="bold">Successes / 5 trials by scenario and arm</text>')
    gw = plotW / len(SCENS)
    bw = min(34, (gw - 30) / len(ARMS))
    for i, sc in enumerate(SCENS):
        x0 = padL + i * gw + 10
        s.append(f'<text x="{x0 + gw / 2 - 10}" y="{padT + plotH + 18}" fill="#8b96ad" font-size="11" text-anchor="middle">{sc}</text>')
        for j, arm in enumerate(ARMS):
            r = res["arms"][arm]["by_scenario"][sc]
            h = plotH * r["k"] / 5
            x = x0 + j * bw
            y = padT + plotH - h
            s.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{bw - 3:.0f}" height="{max(h, 2):.0f}" fill="{COLORS[arm]}">'
                     f'<title>{arm} {sc}: {r["k"]}/5</title></rect>')
            inside = h > plotH - 34
            ly = y + 15 if inside else y - 5
            lc = "#0b0e14" if inside else "#e8ecf3"
            s.append(f'<text x="{x + (bw - 3) / 2:.0f}" y="{ly:.0f}" fill="{lc}" font-size="10" text-anchor="middle">{r["k"]}/5</text>')
    for j, arm in enumerate(ARMS):
        s.append(f'<rect x="{padL + j * 130}" y="{H - 24}" width="10" height="10" fill="{COLORS[arm]}"/>'
                 f'<text x="{padL + j * 130 + 14}" y="{H - 15}" fill="#a6b0c2" font-size="10">{arm.replace("mb-v1-", "")}</text>')
    (FIGS / "fig1_outcomes_by_scenario.svg").write_text("".join(s) + "</svg>", encoding="utf-8")


def fig_budget_response(res):
    W, H, padL, padB, padT = 640, 320, 60, 50, 30
    budgets = [100, 1000, 2500, 5000]
    arms = [f"mb-v1-replay-{b}" for b in budgets]
    s = [_svg_open(W, H, "Replay S-SLOW success rate versus per-action timeout budget")]
    s.append('<text x="12" y="20" fill="#e8ecf3" font-size="13" font-weight="bold">Replay success rate vs per-action budget (fault: slow 2100 ms)</text>')
    plotW, plotH = W - padL - 30, H - padT - padB
    import math as _m
    lx = lambda b: padL + plotW * (_m.log10(b) - 2) / (_m.log10(5000) - 2)
    for f in (0, 0.5, 1.0):
        y = padT + plotH * (1 - f)
        s.append(f'<line x1="{padL}" y1="{y:.0f}" x2="{W - 30}" y2="{y:.0f}" stroke="#20293d"/>'
                 f'<text x="{padL - 8}" y="{y + 4:.0f}" fill="#8b96ad" font-size="10" text-anchor="end">{f:.0%}</text>')
    for b in budgets:
        s.append(f'<text x="{lx(b):.0f}" y="{H - 28}" fill="#8b96ad" font-size="10" text-anchor="middle">{b} ms</text>')
    for sc, color, dash in (("S-SLOW", "#4cc38a", ""), ("S-SLOWDIS", "#e5606e", ' stroke-dasharray="5 4"')):
        pts = []
        for b, a in zip(budgets, arms):
            r = res["arms"][a]["by_scenario"][sc]
            pts.append((lx(b), padT + plotH * (1 - r["k"] / 5), r["k"]))
        s.append('<polyline points="' + " ".join(f"{x:.0f},{y:.0f}" for x, y, _ in pts)
                 + f'" fill="none" stroke="{color}" stroke-width="2.5"{dash}/>')
        for x, y, k in pts:
            s.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="5" fill="{color}"><title>{sc} replay {k}/5</title></circle>'
                     f'<text x="{x:.0f}" y="{y - 10:.0f}" fill="#e8ecf3" font-size="10" text-anchor="middle">{k}/5</text>')
    # Chimera reference lines (5000 ms fixed budget).
    for sc, color in (("S-SLOW", "#39d0d8"), ("S-SLOWDIS", "#8b96ad")):
        r = res["arms"]["mb-v1-chimera"]["by_scenario"][sc]
        y = padT + plotH * (1 - r["k"] / 5)
        s.append(f'<line x1="{padL}" y1="{y:.0f}" x2="{W - 30}" y2="{y:.0f}" stroke="{color}" stroke-width="1" stroke-dasharray="2 4" opacity="0.8"/>')
    s.append(f'<text x="{padL}" y="{H - 8}" fill="#a6b0c2" font-size="10">Dotted horizontals: chimera at its fixed 5000 ms budget. n=5 per point; no interpolation between budgets.</text>')
    (FIGS / "fig2_budget_response.svg").write_text("".join(s) + "</svg>", encoding="utf-8")


def fig_durations(res):
    W, H, padL, padB, padT = 640, 300, 150, 40, 30
    arms = ARMS
    s = [_svg_open(W, H, "Episode duration medians with min-max range by arm")]
    s.append('<text x="12" y="20" fill="#e8ecf3" font-size="13" font-weight="bold">Episode durations by arm (median, min–max; n=20 each)</text>')
    vmax = max(res["arms"][a]["durations_ms"]["max"] for a in arms)
    plotW = W - padL - 30
    rowH = (H - padT - padB) / len(arms)
    for i, arm in enumerate(arms):
        d = res["arms"][arm]["durations_ms"]
        y = padT + i * rowH + rowH / 2
        x0, x1, xm = (padL + plotW * d[k] / vmax for k in ("min", "max", "p50"))
        s.append(f'<text x="{padL - 8}" y="{y + 4:.0f}" fill="#a6b0c2" font-size="10" text-anchor="end">{arm.replace("mb-v1-", "")}</text>')
        s.append(f'<line x1="{x0:.0f}" y1="{y:.0f}" x2="{x1:.0f}" y2="{y:.0f}" stroke="{COLORS[arm]}" stroke-width="2" opacity="0.5"/>')
        s.append(f'<circle cx="{xm:.0f}" cy="{y:.0f}" r="5" fill="{COLORS[arm]}"><title>{arm}: median {d["p50"]} ms, range {d["min"]}–{d["max"]} ms</title></circle>')
        lx = x1 + 6
        anchor = "start"
        if lx + 62 > W - 8:
            lx, anchor = x1 - 8, "end"
        s.append(f'<text x="{lx:.0f}" y="{y + 4:.0f}" fill="#e8ecf3" font-size="10" text-anchor="{anchor}">med {d["p50"]}</text>')
    (FIGS / "fig3_durations.svg").write_text("".join(s) + "</svg>", encoding="utf-8")


if __name__ == "__main__":
    FIGS.mkdir(exist_ok=True)
    main()
