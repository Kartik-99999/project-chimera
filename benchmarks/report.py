"""Benchmark report renderer (benchmark harness, final §13 item).

Renders persisted run files — optionally audited, optionally several
baselines — into the Markdown report specified by
``docs/benchmark_design.md`` §11 and ``docs/evaluation.md`` §6:

* §6.1.1 header (identity, manifests, configuration, environment);
* §6.1.2 summary table (one row per scenario × input × baseline cell);
* §6.1.3 "not measurable" table (every null with its reason);
* §6.1.4 verifier audit (size, rate, provisionality);
* §6.1.5 failure breakdown (by category, with artifact pointers);
* §6.1.6 limitations paragraph (reproduced, not paraphrased);
* §6.1.7 explicit claim list (supported vs. not supported);
* §6.1.8 artifacts (result files and every episode's trace path).

The renderer reports only what the evidence supports. Unavailable
metrics are never zero; zero false-success observations carry their
95% Wilson upper bound (§4.3); unaudited or sub-95%-agreement cells
make the run's rates provisional (§5). The §6.3 disclaimers are
carried verbatim, and the §6.4 prohibited claims are excluded by
construction (proven by test, not by review).

Inputs and honesty rules
------------------------
* One or more run files. All runs must share benchmark id and
  version — results from different manifest versions are never
  compared (§6.2) — and each (baseline, manifest) pair may appear at
  most once. Runs are rendered in sorted order, so output is
  independent of input order.
* Optional manifest files, used only to mark cells whose unanimous
  outcome matches the scenario's expected outcome ("expected"). Each
  manifest must match an input run's manifest id, or planning and
  measurement silently diverge.
* Optional audit-plan files, used only to list the trial IDs of
  disagreement cases (§5: disagreement cases are published). Each
  plan must target an input run.
* Malformed inputs fail the whole render with :class:`ReportError`;
  there is no partial report.

The renderer cannot tell fixture runs from real benchmark runs: it
renders what it is given. Fixture renders in tests are assertions
about shape, never performance results, and must never be presented
as measurements.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from benchmarks.audit import (
    HumanVerdict,
    cell_key,
    is_provisional,
    load_plan,
)
from benchmarks.manifest import Manifest, load_manifest
from benchmarks.results import (
    CellResult,
    EpisodeResult,
    Metric,
    ResultValidationError,
    RunResult,
)

#: Report schema marker (format version of this renderer's output).
REPORT_FORMAT = "chimera-report/1"

#: z for the two-sided 95% Wilson score interval.
WILSON_Z = 1.96

#: Display names for known baselines (§11 example spellings).
BASELINE_DISPLAY = {
    "chimera": "Chimera",
    "baseline-a": "A — replay",
}

#: Disclaimer block, evaluation.md §6.3, reproduced verbatim. Guarded
#: by a drift test against the document itself.
DISCLAIMERS = (
    "> The current test suite is a regression suite, not proof of general\n"
    "> browser-agent performance.\n"
    ">\n"
    "> These results are measured on one local workflow against one local target\n"
    "> with a two-parameter fault taxonomy. They do not generalise to other\n"
    "> websites, workflows, fault models, browsers, or to model-driven agents.\n"
    ">\n"
    "> Baseline A compares fixed-step replay against Chimera's waiting, retry,\n"
    "> and verification layers. It does not measure workflow learning, recovery,\n"
    "> or the value of a model.\n"
    ">\n"
    "> No recovery improvement is claimed: no recovery implementation and no\n"
    "> recovery baseline exist."
)

#: Limitations text, evaluation.md §8, reproduced verbatim. Guarded by
#: a drift test against the document itself. Note the numbering trap:
#: §6.1 item 6 cites "§7 of this document", but §7 is the acceptance
#: gates table — the limitations paragraph lives in §8 at this
#: revision, and that is what is reproduced here.
LIMITATIONS_TEXT = (
    "1. **Scale.** One workflow, one target, four fault scenarios, three input\n"
    "   variations. Roughly 10–30 episodes per run at the default trial count —\n"
    "   far below SRS §11.2's 100-episode minimum for a meaningful zero-rate\n"
    "   claim.\n"
    "2. **Fault taxonomy width.** Two parameters. The evaluation split varies\n"
    "   values, not types. No unseen-fault generalisation can be assessed.\n"
    "3. **Verifier risk.** The independent verifier is itself a component that\n"
    "   can be wrong, in both directions. The human audit mitigates this; it does\n"
    "   not eliminate it.\n"
    "4. **Baseline coverage.** Only Baseline A is specified; B is unavailable and\n"
    "   C lacks the recovery and observation layers SRS §11.3 assumes. The\n"
    "   attribution SRS §11.3 asks for is out of reach.\n"
    "5. **Metric gaps.** `INCONCLUSIVE` is not an observable category (§4.2),\n"
    '   which limits how precisely "could not tell" can be distinguished from\n'
    '   "failed".\n'
    "6. **No adversarial coverage.** None of the SRS §12.4 adversarial scenarios\n"
    "   are implementable against the current demo app.\n"
    "7. **Latency comparability.** Absolute latencies are machine-specific;\n"
    "   only same-machine before/after comparisons are meaningful, and the\n"
    "   measured baseline set (happy path ≈0.12 s) is small relative to\n"
    "   start-up overhead, which must be excluded or disclosed."
)


class ReportError(ValueError):
    """The report cannot be rendered honestly; no output is produced."""


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


def wilson_upper(successes: int, trials: int,
                 z: float = WILSON_Z) -> Optional[float]:
    """The upper end of the two-sided 95% Wilson score interval.

    Returns ``None`` when there is no denominator to bind. Reference
    values from evaluation.md §4.3: 0/5 → 43.4%, 0/50 → 7.1%,
    0/100 → 3.7%.
    """
    if trials <= 0 or successes < 0 or successes > trials:
        return None
    denominator = 1.0 + z * z / trials
    centre = (successes / trials + z * z / (2 * trials)) / denominator
    spread = (
        z
        * math.sqrt(
            (successes / trials) * (1 - successes / trials) / trials
            + z * z / (4 * trials * trials)
        )
        / denominator
    )
    return min(1.0, centre + spread)


def _percent(numerator: int, denominator: int) -> str:
    value = 100.0 * numerator / denominator
    if value == int(value):
        return f"{int(value)}%"
    return f"{value:.1f}%"


def _bound_percent(bound: float) -> str:
    return f"≤{bound * 100:.1f}%"


# ---------------------------------------------------------------------------
# Loading and compatibility
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _RunInput:
    path: str
    run: RunResult


def _load_runs(paths: Sequence[Path]) -> List[_RunInput]:
    if not paths:
        raise ReportError("at least one run file is required")
    runs: List[_RunInput] = []
    for path in paths:
        try:
            raw = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            raise ReportError(
                f"cannot read run file {path}: {exc}") from exc
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ReportError(
                f"run file {path} is not valid JSON: {exc}") from exc
        try:
            run = RunResult.from_dict(data)
        except (ResultValidationError, KeyError, TypeError,
                ValueError) as exc:
            raise ReportError(
                f"run file {path} is not a valid RunResult: {exc}") from exc
        runs.append(_RunInput(path=str(path), run=run))
    first = runs[0].run
    for candidate in runs[1:]:
        other = candidate.run
        if other.benchmark_id != first.benchmark_id \
                or other.benchmark_version != first.benchmark_version:
            raise ReportError(
                "results from different benchmark versions are not compared "
                f"(§6.2): {first.benchmark_id} v{first.benchmark_version} vs "
                f"{other.benchmark_id} v{other.benchmark_version} "
                f"({candidate.path})")
    seen: Dict[Tuple[str, str], str] = {}
    for candidate in runs:
        key = (candidate.run.config.get("baseline", "?"),
               candidate.run.manifest_id)
        if key in seen:
            raise ReportError(
                f"baseline {key[0]!r} for manifest {key[1]!r} appears twice "
                f"({seen[key]} and {candidate.path}); one run per "
                "baseline-manifest pair")
        seen[key] = candidate.path
    runs.sort(key=lambda r: (r.run.manifest_id,
                             str(r.run.config.get("baseline", "?")),
                             r.run.run_id))
    return runs


def _load_manifests(paths: Sequence[Path],
                    runs: List[_RunInput]) -> Dict[str, Manifest]:
    manifests: Dict[str, Manifest] = {}
    run_manifests = {r.run.manifest_id for r in runs}
    for path in paths:
        try:
            manifest = load_manifest(Path(path))
        except Exception as exc:  # noqa: BLE001 — any load failure refuses
            raise ReportError(
                f"cannot load manifest {path}: {exc}") from exc
        if manifest.manifest_id not in run_manifests:
            raise ReportError(
                f"manifest {path} ({manifest.manifest_id}) matches no input "
                "run; expected outcomes must come from a run's own manifest")
        manifests[manifest.manifest_id] = manifest
    return manifests


def _disagreements_by_cell(plan_paths: Sequence[Path],
                           runs: List[_RunInput]
                           ) -> Dict[Tuple[str, str], List[str]]:
    """Trial IDs where the human disagreed, per (run_id, cell key).

    Requires the audit plan files: the run file records only agreement
    counts, so without the plans the report states the count and
    points at the plans instead of listing cases.
    """
    by_run_id = {r.run.run_id: r.run for r in runs}
    disagreements: Dict[Tuple[str, str], List[str]] = {}
    for path in plan_paths:
        try:
            plan = load_plan(Path(path))
        except Exception as exc:  # noqa: BLE001 — plan errors refuse
            raise ReportError(
                f"cannot load audit plan {path}: {exc}") from exc
        if plan.run_id not in by_run_id:
            raise ReportError(
                f"audit plan {path} targets run {plan.run_id!r}, which is "
                "not among the input runs")
        expected = {cell_key(c.scenario_id, c.input_id, c.baseline,
                             c.fault_params)
                    for c in by_run_id[plan.run_id].cells}
        if set(plan.cells) != expected:
            raise ReportError(
                f"audit plan {path} cells do not match run "
                f"{plan.run_id!r}'s cells (stale or foreign plan?)")
        for key, sample in plan.cells.items():
            by_trial = {b.trial_id: b for b in sample.sampled}
            cases: List[str] = []
            for trial_id, verdict in sample.verdicts.items():
                if trial_id not in by_trial:
                    continue
                if isinstance(verdict, tuple):
                    # ("unauditable", reason): excluded from agreement,
                    # not a disagreement.
                    continue
                if isinstance(verdict, HumanVerdict) and not \
                        verdict.agrees_with(
                            by_trial[trial_id].verifier_checks):
                    cases.append(trial_id)
            disagreements[(plan.run_id, key)] = sorted(cases)
    return disagreements


# ---------------------------------------------------------------------------
# Cell rendering helpers
# ---------------------------------------------------------------------------


def _display_baseline(baseline: str) -> str:
    return BASELINE_DISPLAY.get(baseline, baseline)


def _metric_int(metric: Metric) -> Optional[int]:
    if not metric.is_available:
        return None
    try:
        return int(metric.value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _metric_mean(metric: Metric) -> Optional[float]:
    if not metric.is_available or not isinstance(metric.value, dict):
        return None
    try:
        return float(metric.value["mean_per_trial"])
    except (KeyError, TypeError, ValueError):
        return None


def _metric_total(metric: Metric) -> Optional[int]:
    if not metric.is_available:
        return None
    if isinstance(metric.value, dict):
        try:
            return int(metric.value["total"])
        except (KeyError, TypeError, ValueError):
            return None
    try:
        return int(metric.value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _null_cell(reason: Optional[str]) -> str:
    short = (reason or "no reason recorded").split(".")[0].strip()
    if len(short) > 80:
        short = short[:77] + "..."
    return f"null ({short})"


def _success_text(cell: CellResult, expected: Optional[str]) -> str:
    metric = cell.outcomes.get("succeeded",
                               Metric.unavailable("success count not recorded"))
    succeeded = _metric_int(metric)
    if succeeded is None or cell.trials <= 0:
        return _null_cell(metric.unavailable_reason
                          or "success count unavailable")
    # ", expected" iff every episode matches the manifest expectation:
    # unanimous success where success was expected, zero successes
    # where failure was expected (§11 example: "0/5 (0%, expected)").
    # Anything else earns no marker.
    marker = ""
    if expected == "succeeded" and succeeded == cell.trials:
        marker = ", expected"
    elif expected == "failed" and succeeded == 0:
        marker = ", expected"
    return (f"{succeeded}/{cell.trials} "
            f"({_percent(succeeded, cell.trials)}{marker})")


def _false_success_text(cell: CellResult) -> str:
    value = _metric_int(cell.false_successes)
    if value is None or cell.trials <= 0:
        return _null_cell(cell.false_successes.unavailable_reason)
    if value == 0:
        bound = wilson_upper(0, cell.trials)
        if bound is None:
            return f"0/{cell.trials}"
        return f"0/{cell.trials} ({_bound_percent(bound)})"
    return f"{value}/{cell.trials} ({_percent(value, cell.trials)})"


def _count_text(metric: Metric) -> str:
    total = _metric_total(metric)
    if total is None:
        return _null_cell(metric.unavailable_reason)
    return str(total)


def _mean_text(metric: Metric) -> str:
    mean = _metric_mean(metric)
    if mean is None:
        return _null_cell(metric.unavailable_reason)
    return f"{mean:.1f}"


def _latency_text(cell: CellResult, key: str) -> str:
    metric = cell.latency_ms.get(
        key, Metric.unavailable(f"latency {key} not recorded"))
    value = _metric_int(metric)
    if value is None:
        return _null_cell(metric.unavailable_reason)
    return f"{value} ms"


def _harness_errors(episodes: Sequence[EpisodeResult]) -> List[EpisodeResult]:
    return [e for e in episodes
            if (e.error or "").startswith("harness_error:")]


@dataclass(frozen=True)
class _CellRow:
    scenario_id: str
    input_id: str
    split: str
    baseline: str
    trials: int
    success: str
    false_success: str
    unauthorized: str
    safety: str
    retries_per_episode: str
    latency_p50: str
    latency_p95: str
    harness_errors: int


def _cell_rows(run: RunResult,
               manifests: Mapping[str, Manifest]) -> List[_CellRow]:
    manifest = manifests.get(run.manifest_id)
    rows: List[_CellRow] = []
    for cell in run.cells:
        expected: Optional[str] = None
        if manifest is not None:
            try:
                expected = manifest.scenario(cell.scenario_id).expected_outcome
            except KeyError:
                expected = None
        episodes = [e for e in run.episodes
                    if not e.trial_id.startswith("warmup:")
                    and e.scenario_id == cell.scenario_id
                    and e.input_id == cell.input_id
                    and e.baseline == cell.baseline]
        rows.append(_CellRow(
            scenario_id=cell.scenario_id,
            input_id=cell.input_id,
            split=str(run.config.get("split", "?")),
            baseline=_display_baseline(cell.baseline),
            trials=cell.trials,
            success=_success_text(cell, expected),
            false_success=_false_success_text(cell),
            unauthorized=_count_text(cell.unauthorized_actions),
            safety=_count_text(cell.safety_violations),
            retries_per_episode=_mean_text(cell.retries),
            latency_p50=_latency_text(cell, "p50"),
            latency_p95=_latency_text(cell, "p95"),
            harness_errors=len(_harness_errors(episodes)),
        ))
    rows.sort(key=lambda r: (r.split, r.scenario_id, r.input_id, r.baseline))
    return rows


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------


def _header_lines(runs: List[_RunInput]) -> List[str]:
    first = runs[0].run
    env = first.environment
    lines = [
        f"# {first.benchmark_id} v{first.benchmark_version} — benchmark report",
        "",
        f"agent `{first.agent_version}` · "
        f"Playwright {env.playwright_version} · "
        f"{env.browser} `{env.browser_build}` · "
        f"Python {env.python_version} · {env.platform}",
        f"demo_app_sha256: `{env.demo_app_sha256}`",
        f"manifests: dev `{env.dev_manifest_sha256}`, "
        f"eval `{env.eval_manifest_sha256}`",
        "",
        "## Runs",
        "",
        "| Run | Baseline | Manifest | Trials/cell | Warm-ups | Started | Completed |",
        "|---|---|---|---|---|---|---|",
    ]
    for entry in runs:
        run = entry.run
        lines.append(
            f"| `{run.run_id}` | {run.config.get('baseline', '?')} | "
            f"`{run.manifest_id}` (`{run.manifest_sha256[:12]}…`) | "
            f"{run.config.get('trials_per_cell', '?')} | "
            f"{run.config.get('warmup_episodes', '?')} | "
            f"{run.started_at} | {run.completed_at} |"
        )
    return lines


def _summary_table(runs: List[_RunInput],
                   manifests: Mapping[str, Manifest]) -> List[str]:
    lines = [
        "## Summary by cell",
        "",
        "| Scenario / input | Split | Baseline | n | Success | False success | "
        "Unauth. actions | Safety viol. | Retries/ep | Latency p50 | p95 | "
        "Harness errors |",
        "|---|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    splits: List[str] = []
    for entry in runs:
        for row in _cell_rows(entry.run, manifests):
            if row.split not in splits:
                splits.append(row.split)
            lines.append(
                f"| `{row.scenario_id}` / `{row.input_id}` | {row.split} | "
                f"{row.baseline} | {row.trials} | {row.success} | "
                f"{row.false_success} | {row.unauthorized} | {row.safety} | "
                f"{row.retries_per_episode} | {row.latency_p50} | "
                f"{row.latency_p95} | {row.harness_errors} |"
            )
    # One Baseline B null row per reported split, so the single-split
    # case matches the §11 example exactly.
    for split in sorted(splits):
        lines.append(
            f"| *Baseline B — model* | {split} | B | — | "
            "`null` (not implemented) | `null` | `null` | `null` | `null` | "
            "`null` | `null` | — |"
        )
    return lines


def _not_measurable(runs: List[_RunInput]) -> List[str]:
    rows: List[Tuple[str, str, str, str]] = []

    def _cell_metric(run: RunResult, cell: CellResult, name: str,
                     metric: Metric) -> None:
        if not metric.is_available:
            rows.append((
                "cell",
                f"`{cell.scenario_id}`/`{cell.input_id}`/"
                f"{cell.baseline}@{run.run_id[:8]}",
                f"`{name}`",
                metric.unavailable_reason or "no reason recorded",
            ))

    for entry in runs:
        run = entry.run
        for cell in run.cells:
            label = (f"`{cell.scenario_id}`/`{cell.input_id}`/"
                     f"{cell.baseline}@{run.run_id[:8]}")
            for name, metric in sorted(cell.outcomes.items()):
                _cell_metric(run, cell, f"outcomes.{name}", metric)
            for name, metric in sorted(cell.independent_verification.items()):
                _cell_metric(run, cell, f"verification.{name}", metric)
            for name in ("false_successes", "verifier_disagreements",
                         "unauthorized_actions", "safety_violations",
                         "retries", "actions", "model_calls",
                         "model_cost_usd", "human_interventions"):
                _cell_metric(run, cell, name, getattr(cell, name))
            for name, metric in sorted(cell.latency_ms.items()):
                _cell_metric(run, cell, f"latency.{name}", metric)
            # Episode-level gaps, aggregated by metric and reason so one
            # row stands for any number of identical gaps.
            episode_gaps: Dict[Tuple[str, str], int] = {}
            for episode in run.episodes:
                if episode.trial_id.startswith("warmup:"):
                    continue
                if (episode.scenario_id != cell.scenario_id
                        or episode.input_id != cell.input_id
                        or episode.baseline != cell.baseline):
                    continue
                checks = [
                    ("episode.verification",
                     episode.verification.status != "verified",
                     episode.verification.unavailable_reason),
                    ("episode.retries", not episode.retries.is_available,
                     episode.retries.unavailable_reason),
                    ("episode.actions_executed",
                     not episode.actions_executed.is_available,
                     episode.actions_executed.unavailable_reason),
                    ("episode.unauthorized_actions",
                     not episode.unauthorized_actions.is_available,
                     episode.unauthorized_actions.unavailable_reason),
                    ("episode.safety_violations",
                     not episode.safety_violations.is_available,
                     episode.safety_violations.unavailable_reason),
                ]
                for name, missing, reason in checks:
                    if missing:
                        key = (name, reason or "no reason recorded")
                        episode_gaps[key] = episode_gaps.get(key, 0) + 1
            for (name, reason), count in sorted(episode_gaps.items()):
                rows.append(("episode", label,
                             f"`{name}` × {count}", reason))
        totals = run.totals
        for name in ("false_success_rate", "unauthorized_actions"):
            metric = getattr(totals, name)
            if not metric.is_available:
                rows.append(("run", f"totals@{run.run_id[:8]}", f"`{name}`",
                             metric.unavailable_reason or "no reason recorded"))
    lines = [
        "## Not measurable in this report",
        "",
        "Every `null` with its blocking reason:",
        "",
        "| Scope | Where | Metric | Reason |",
        "|---|---|---|---|",
    ]
    for scope, where, metric, reason in sorted(rows):
        safe_reason = reason.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {scope} | {where} | {metric} | {safe_reason} |")
    if not rows:
        lines.append("_None — every metric in every run is measured._")
    return lines


def _audit_section(
        runs: List[_RunInput],
        disagreements: Mapping[Tuple[str, str], List[str]],
        plans_supplied: bool) -> Tuple[List[str], bool]:
    lines = ["## Verifier audit", ""]
    provisional = False
    audited_cells = 0
    total_cells = 0
    adjudicated_episodes = 0
    for entry in runs:
        run = entry.run
        for cell in run.cells:
            total_cells += 1
            where = (f"`{cell.scenario_id}`/`{cell.input_id}`/"
                     f"{cell.baseline}@{run.run_id[:8]}")
            audit = cell.verifier_audit
            if audit is None:
                provisional = True
                lines.append(
                    f"- {where}: `null` (no sample adjudicated) — "
                    "figures provisional.")
                continue
            audited_cells += 1
            adjudicated_episodes += audit.sampled
            rate = audit.agreement_rate
            cell_provisional = is_provisional(rate)
            provisional = provisional or cell_provisional
            rate_text = "null" if rate is None else f"{rate * 100:.1f}%"
            lines.append(
                f"- {where}: sampled {audit.sampled}, agreed "
                f"{audit.agreed}, agreement {rate_text}"
                + (" — figures provisional." if cell_provisional
                   else "."))
            if audit.agreed < audit.sampled:
                key = cell_key(cell.scenario_id, cell.input_id,
                               cell.baseline, cell.fault_params)
                cases = disagreements.get((run.run_id, key))
                if cases is None and plans_supplied:
                    cases = []
                if cases:
                    lines.append("  disagreement cases: "
                                 + ", ".join(f"`{t}`" for t in cases))
                elif not plans_supplied:
                    lines.append("  disagreement cases: listed in the audit "
                                 "plan file (not supplied with this report).")
    cell_word = "cell" if total_cells == 1 else "cells"
    episode_word = ("episode" if adjudicated_episodes == 1 else "episodes")
    lines += [
        "",
        f"**Coverage:** {audited_cells} of {total_cells} {cell_word} "
        f"audited ({adjudicated_episodes} {episode_word} adjudicated).",
        "",
        ("**Verdict: PROVISIONAL** — at least one cell is unaudited or "
         "below 95% agreement."
         if provisional else
         "**Verdict: AUDITED** — every cell is audited at or above 95% "
         "agreement."),
    ]
    return lines, provisional


def _failure_breakdown(runs: List[_RunInput]) -> List[str]:
    groups: Dict[str, List[str]] = {}
    harness: List[str] = []
    uncategorized: List[str] = []
    for entry in runs:
        for episode in entry.run.episodes:
            if episode.trial_id.startswith("warmup:"):
                continue
            if episode.outcome.value == "succeeded":
                continue
            artifact = episode.trace_artifact or "(no artifact recorded)"
            if (episode.error or "").startswith("harness_error:"):
                harness.append(f"`{episode.trial_id}` → {artifact}")
            elif episode.failure_category:
                groups.setdefault(episode.failure_category, []).append(
                    f"`{episode.trial_id}` → {artifact}")
            else:
                uncategorized.append(f"`{episode.trial_id}` → {artifact}")
    lines = ["## Failure breakdown", ""]
    if harness:
        lines.append(f"Harness errors (reported separately, never dropped): "
                     f"{len(harness)}")
        lines += [f"- {item}" for item in sorted(harness)]
        lines.append("")
    for category in sorted(groups):
        items = sorted(groups[category])
        lines.append(f"{category}: {len(items)}")
        lines += [f"- {item}" for item in items]
        lines.append("")
    if uncategorized:
        lines.append(f"Uncategorized agent failures "
                     f"(`failure_category` null): {len(uncategorized)}")
        lines += [f"- {item}" for item in sorted(uncategorized)]
        lines.append("")
    if not harness and not groups and not uncategorized:
        lines.append("_No failed or cancelled episodes in these runs._")
        lines.append("")
    return lines


def _exclusions(runs: List[_RunInput]) -> List[str]:
    lines = ["## Exclusions", ""]
    for entry in runs:
        run = entry.run
        warmups = sum(1 for e in run.episodes
                      if e.trial_id.startswith("warmup:"))
        configured = run.config.get("trials_per_cell")
        shortfalls = [c for c in run.cells
                      if isinstance(configured, int)
                      and c.trials != configured]
        lines.append(
            f"- Run `{run.run_id}`: {warmups} warm-up episode(s) excluded "
            "from every aggregate (outside any cell, design §14.3).")
        for cell in shortfalls:
            lines.append(
                f"- Run `{run.run_id}`, cell `{cell.scenario_id}`/"
                f"`{cell.input_id}`/{cell.baseline}: {cell.trials} episode(s) "
                f"vs {configured} configured (the run ended early; see the "
                "run file's notes).")
    lines.append("")
    return lines


def _claim_list(runs: List[_RunInput], provisional: bool) -> List[str]:
    measured_false: List[str] = []
    measured_actions: List[str] = []
    audited_cells: List[str] = []
    cells: List[str] = []
    for entry in runs:
        for cell in entry.run.cells:
            where = (f"`{cell.scenario_id}`/`{cell.input_id}`/"
                     f"{cell.baseline}")
            cells.append(where)
            if cell.false_successes.is_available:
                measured_false.append(where)
            if cell.unauthorized_actions.is_available:
                measured_actions.append(where)
            if cell.verifier_audit is not None:
                audited_cells.append(where)
    lines = ["## Claim list", "", "What this report supports:", ""]
    lines.append(f"- Success counts with denominators for {len(cells)} "
                 f"reported cell(s), as listed above.")
    if measured_false:
        lines.append(f"- False-success counts with denominators and Wilson "
                     f"bounds for: {', '.join(sorted(set(measured_false)))}.")
    else:
        lines.append("- No false-success counts: verifier evidence is "
                     "incomplete in every cell (see null table).")
    if measured_actions:
        lines.append(f"- Unauthorised-action and safety-violation counts "
                     f"for: {', '.join(sorted(set(measured_actions)))}.")
    else:
        lines.append("- No action counts: action records are incomplete in "
                     "every cell (see null table).")
    if audited_cells:
        lines.append(f"- Audit agreement figures for: "
                     f"{', '.join(sorted(set(audited_cells)))}.")
    else:
        lines.append("- No audit agreement figures: no sample has been "
                     "adjudicated.")
    lines += ["", "What this report does not support:", "",
              "- Rates beyond their stated denominators and bounds.",
              "- Recovery, generalisation, or model claims of any kind.",
              "- Comparisons across benchmark versions (refused at render).",
              "- Any reading of a `null` as zero."]
    if provisional:
        lines.append("- Non-provisional rates: this report is provisional "
                     "(see audit section).")
    lines.append("")
    return lines


def _artifacts(run_paths: Sequence[str],
               manifest_paths: Sequence[str],
               plan_paths: Sequence[str],
               runs: List[_RunInput]) -> List[str]:
    lines = ["## Artifacts", "", "Inputs rendered:", ""]
    for path in run_paths:
        lines.append(f"- run file: `{path}`")
    for path in manifest_paths:
        lines.append(f"- manifest: `{path}`")
    for path in plan_paths:
        lines.append(f"- audit plan: `{path}`")
    lines += ["", "Episode evidence (every non-warm-up episode):", ""]
    for entry in runs:
        for episode in entry.run.episodes:
            if episode.trial_id.startswith("warmup:"):
                continue
            lines.append(f"- `{episode.trial_id}` "
                         f"({episode.scenario_id}/{episode.input_id}/"
                         f"{episode.baseline}): "
                         f"{episode.trace_artifact or '(no artifact)'}")
    lines.append("")
    return lines


def render_report(
    run_paths: Sequence[Path],
    *,
    manifest_paths: Sequence[Path] = (),
    audit_plan_paths: Sequence[Path] = (),
) -> str:
    """Render run files into the §6.1 benchmark report (Markdown).

    ``run_paths`` names one or more persisted run files (one baseline
    per file); ``manifest_paths`` optionally supplies the runs' own
    manifests for expected-outcome marking; ``audit_plan_paths``
    optionally supplies the runs' audit plans so disagreement cases
    can be listed. Any incompatibility or malformation raises
    :class:`ReportError` instead of producing a partial report.
    """
    runs = _load_runs(run_paths)
    manifests = _load_manifests(manifest_paths, runs)
    disagreements = _disagreements_by_cell(audit_plan_paths, runs)

    sections: List[str] = _header_lines(runs)
    sections += ["", "---", ""]
    sections += _summary_table(runs, manifests)
    sections += ["", "---", ""]
    sections += _not_measurable(runs)
    sections += ["", "---", ""]
    audit_lines, provisional = _audit_section(
        runs, disagreements, bool(audit_plan_paths))
    sections += audit_lines
    sections += ["", "---", ""]
    sections += _failure_breakdown(runs)
    sections += ["", "---", ""]
    sections += _exclusions(runs)
    sections += ["", "---", ""]
    sections += [
        "## Limitations",
        "",
        ("(Evaluation.md §6.1 cites “§7 of this document”; the "
         "limitations paragraph lives in §8 at this revision and is "
         "reproduced verbatim below.)"),
        "",
        LIMITATIONS_TEXT,
        "",
    ]
    sections += ["", "---", ""]
    sections += _claim_list(runs, provisional)
    sections += ["", "---", ""]
    sections += [
        "## Disclaimers",
        "",
        DISCLAIMERS,
        "",
    ]
    sections += ["", "---", ""]
    sections += _artifacts([r.path for r in runs],
                           [str(p) for p in manifest_paths],
                           [str(p) for p in audit_plan_paths], runs)
    sections.append(f"<!-- rendered by {REPORT_FORMAT} -->")
    return "\n".join(sections).rstrip("\n") + "\n"


__all__ = [
    "BASELINE_DISPLAY",
    "DISCLAIMERS",
    "LIMITATIONS_TEXT",
    "REPORT_FORMAT",
    "WILSON_Z",
    "ReportError",
    "render_report",
    "wilson_upper",
]
