# Chimera Workbench

Practical browser automation: run a supported workflow in a real
browser, watch it execute, get a verified result with evidence, and
analyse current and historical executions.

## Launch

```bash
cd /Users/kartikbhardwaj/project-chimera
.venv/bin/python -m workbench.server
# Workbench: http://127.0.0.1:8130/workbench/
# Research Console (unchanged): http://127.0.0.1:8130/research/
```

First start imports frozen benchmark episodes as labelled history
(~630 rows, under a second). Standard library only — no new
dependencies. Chromium is launched headless per execution.

## Honest boundaries

- Drivers are **fixed scripts** (retrying agent, single-attempt
  replay), not a general AI. Only registered workflows run.
- Supported today: **Create a project** and **Fill a contact form**
  in the bundled Demo Task Manager (normal / slow-load /
  broken-submit conditions, plus complete / missing-field /
  invalid-email submission cases for the contact form), and
  **Order from SauceDemo** on the external practice store
  (login / cart-preset / sort / checkout cases), and
  **Stress the SauceDemo store** (challenging demo accounts,
  add/remove consistency, T1–T6 checks, login-readiness timing).
- `studio.py` — Workflow Studio: user-composed step workflows (navigate,
  click, fill, select, wait, verify, capture) with per-step contracts,
  evidence-based recovery, variables/secrets, validation, both drivers,
  step records, and an independent verifier. Only the Demo Task Manager
  and SauceDemo environments are supported.
- Third-party websites are **not** supported beyond the one
  approved external origin (`https://www.saucedemo.com/`, a demo
  shop with no payment); arbitrary sites stay roadmap-only so the
  boundary stays visible. Drivers refuse any URL outside the
  approved origin and paths.
- Verdicts come from independent postcondition checks (P1–P3) read
  after the run — never from the driver's own claims. Missing
  evidence reports `insufficient-evidence`, never success. The
  SauceDemo workflow is judged from mid-run stage states (S1–S5)
  instead, persisted to `<run>.stages.json` next to the trace.

## Layout

- `workflows.py` — workflow registry + parameter validation
- `executor.py` — real browser execution, live progress, verify
- `store.py` — SQLite index (`data/workbench.db`, gitignored).
  `origin` (`local`/`external`) separates bundled-app history from
  external-application runs; pre-existing databases migrate
  idempotently on open.
- `import_history.py` — benchmark-episode import (labelled, idempotent)
- `analytics.py` — SQL aggregates with denominators + sampling notes
- `campaigns.py` — repeatable campaigns: validated specs, sequential
  runner (one browser, fresh contexts, pacing, stop-on-error),
  pause/resume/cancel persisted in the database
- `perf_fixture.py` — synthetic large-table fixture (separate DB,
  `source='synthetic'`); refuses non-synthetic databases
- `server.py` — HTTP server + JSON API
- `web/` — the browser app (workspace, run detail, history,
  analytics, campaign lab)

## Campaign Lab

Define a campaign (workflow, drivers, labelled conditions,
repetitions, pacing, stop threshold), start it, and watch trials
execute sequentially with live progress. Campaign trials are
ordinary executions tagged `trial_kind='campaign'` plus
`campaign_id`/`trial_seq`, so campaigns, benchmark history, and
adhoc runs stay distinguishable but share one evidence model.

- Pause waits for the live trial, then stops between trials;
  resume continues; cancel stops the live trial too.
- Stop-on-error counts only infrastructure failures
  (`status='error'`); `verified-failure` verdicts are legitimate
  outcomes and never stop a campaign.
- Every trial records stage timings (sauce), action timings,
  checks, verdict, and trace/screenshot references; passwords
  are never stored.
- The Lab view adds paired-driver agreement, stage-duration
  comparison, failure heatmaps, trial-order trends, and a
  paginated trial table — all drillable to executions.
- Analytics stay server-side aggregated and paginated; the
  synthetic fixture proves 100k-execution scale
  (all endpoints < 0.5 s) without touching real data.

Runtime data (`data/workbench.db*`, `data/workbench/`) is gitignored.
Frozen research artifacts are only ever read, never written.
