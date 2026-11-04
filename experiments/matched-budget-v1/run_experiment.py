"""Matched-budget experiment driver: run arms via the stock benchmark runner.

Usage:
    .venv/bin/python experiments/matched-budget-v1/run_experiment.py --pilot
    .venv/bin/python experiments/matched-budget-v1/run_experiment.py --main [--arm NAME]

Each arm is one ``run_manifest`` invocation with its own run_id,
output file, and trace directory. Replay arms set
CHIMERA_REPLAY_ACTION_TIMEOUT_MS; the chimera arm runs with the
variable unset (agent budget is fixed in code). Refuses to
overwrite existing outputs.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

EXP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EXP_DIR.parent.parent))

from benchmarks.baseline_a import REPLAY_ACTION_TIMEOUT_ENV_VAR  # noqa: E402
from benchmarks.runner import run_manifest  # noqa: E402

ARMS = [
    ("mb-v1-chimera", "chimera", None),
    ("mb-v1-replay-100", "baseline-a", 100),
    ("mb-v1-replay-1000", "baseline-a", 1000),
    ("mb-v1-replay-2500", "baseline-a", 2500),
    ("mb-v1-replay-5000", "baseline-a", 5000),
]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def run_arm(arm: str, baseline: str, budget_ms, manifest: Path, tag: str) -> Path:
    out = EXP_DIR / "runs" / f"{tag}-{arm}.json"
    traces = EXP_DIR / "runs" / f"traces-{tag}-{arm}"
    if out.exists():
        raise SystemExit(f"refusing to overwrite existing {out} (delete it to re-run)")
    if budget_ms is None:
        os.environ.pop(REPLAY_ACTION_TIMEOUT_ENV_VAR, None)
    else:
        if not isinstance(budget_ms, int) or budget_ms <= 0:
            raise SystemExit(f"invalid budget_ms={budget_ms!r}: must be a positive int")
        os.environ[REPLAY_ACTION_TIMEOUT_ENV_VAR] = str(budget_ms)
    started = _now()
    result = run_manifest(
        manifest, out, trace_dir=traces, baseline=baseline,
        run_id=f"{tag}-{arm}",
    )
    cfg = {
        "arm": arm, "tag": tag, "baseline": baseline,
        "replay_action_timeout_ms": budget_ms,
        "manifest": str(manifest), "run_id": f"{tag}-{arm}",
        "started_at": started, "completed_at": _now(),
        "episodes": len(result.episodes),
    }
    (EXP_DIR / "runs" / f"{tag}-{arm}.config.json").write_text(
        json.dumps(cfg, indent=1), encoding="utf-8")
    print(f"{tag}-{arm}: {len(result.episodes)} episodes -> {out.name}", flush=True)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--pilot", action="store_true")
    g.add_argument("--main", action="store_true")
    ap.add_argument("--arm", default=None, help="run only this arm")
    args = ap.parse_args()
    tag = "pilot" if args.pilot else "main"
    manifest = EXP_DIR / ("manifest-mb-v1-pilot.json" if args.pilot else "manifest-mb-v1.json")
    arms = [a for a in ARMS if args.arm is None or a[0] == args.arm]
    if not arms:
        raise SystemExit(f"unknown arm {args.arm!r}")
    (EXP_DIR / "runs").mkdir(exist_ok=True)
    for arm, baseline, budget in arms:
        run_arm(arm, baseline, budget, manifest, tag)
    os.environ.pop(REPLAY_ACTION_TIMEOUT_ENV_VAR, None)


if __name__ == "__main__":
    main()
