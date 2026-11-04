"""Baseline B experiment driver: Muse Spark episodes via the stock runner.

Usage:
    .venv/bin/python experiments/model-baseline-v1/run_experiment.py --smoke
    .venv/bin/python experiments/model-baseline-v1/run_experiment.py --main

--smoke runs ONE live episode (S-NORM/I-PLAIN, real browser + real API)
into a scratch directory. --main runs the full model-v1 manifest
(30 episodes + 1 warm-up) through ``run_manifest`` with
baseline="baseline-b". Refuses to run without MODEL_API_KEY and
refuses to overwrite existing outputs.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

EXP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EXP_DIR.parent.parent))

from benchmarks.baseline_b import MODEL_BASELINE_ID, model_executor  # noqa: E402
from benchmarks.manifest import load_manifest  # noqa: E402
from benchmarks.runner import run_manifest  # noqa: E402
from chimera.llm import api_key_available  # noqa: E402
from chimera.safety import CancellationToken  # noqa: E402

MANIFEST = EXP_DIR.parent.parent / "benchmarks" / "manifests" / "model-v1.json"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _require_key() -> None:
    if not api_key_available():
        raise SystemExit(
            "no Meta Model API key: set MODEL_API_KEY in the environment "
            "or in .env (git-ignored; see .env.example), then re-run.")


def smoke() -> None:
    _require_key()
    manifest = load_manifest(MANIFEST)
    cell = manifest.cells(MODEL_BASELINE_ID)[0]
    scenario = manifest.scenario(cell.scenario_id)
    task_input = next(i for i in scenario.inputs
                      if i.id == cell.input_id)
    traces = EXP_DIR / "runs" / f"traces-smoke-{_now()}"
    execution = model_executor(
        scenario=scenario, task_input=task_input, fault=cell.fault,
        trace_dir=traces, token=CancellationToken(),
        timeout_seconds=600.0,
    )
    print(f"terminal: {execution.reported_status}", flush=True)
    print(f"error: {execution.error}", flush=True)
    print(f"trace: {execution.trace_path}", flush=True)


def main_run() -> None:
    _require_key()
    out = EXP_DIR / "runs" / "model-b.json"
    traces = EXP_DIR / "runs" / "traces-model-b"
    if out.exists():
        raise SystemExit(f"refusing to overwrite existing {out}")
    (EXP_DIR / "runs").mkdir(exist_ok=True)
    started = _now()
    result = run_manifest(
        MANIFEST, out, trace_dir=traces, baseline=MODEL_BASELINE_ID,
        run_id="model-b",
    )
    cfg = {
        "baseline": MODEL_BASELINE_ID, "manifest": str(MANIFEST),
        "manifest_sha256": load_manifest(MANIFEST).sha256(),
        "run_id": "model-b", "started_at": started,
        "completed_at": _now(), "episodes": len(result.episodes),
    }
    (EXP_DIR / "runs" / "model-b.config.json").write_text(
        json.dumps(cfg, indent=1), encoding="utf-8")
    print(f"model-b: {len(result.episodes)} episodes -> {out.name}",
          flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--smoke", action="store_true")
    g.add_argument("--main", action="store_true")
    args = ap.parse_args()
    if args.smoke:
        smoke()
    else:
        main_run()


if __name__ == "__main__":
    main()
