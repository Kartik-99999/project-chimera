"""Browser tests for Baseline A, the deterministic replay driver.

Exercises the design §6 prediction against the real demo app in
Chromium: replay succeeds on `S-NORM` and fails on `S-SLOW`, `S-DIS`,
and `S-SLOWDIS` — then runs a two-cell fixture manifest through the
runner end to end. These are the only Baseline A tests that launch a
browser; they establish no performance rates.
"""

from benchmarks.baseline_a import BASELINE_ID, replay_executor
from benchmarks.manifest import FaultConfig, parse_manifest
from benchmarks.runner import Runner, load_run_result
from benchmarks.verifier import verify_postconditions


def _env():
    from benchmarks.results import EnvironmentInfo

    return EnvironmentInfo(
        python_version="test", playwright_version="test",
        browser="chromium", browser_build="test", platform="test",
        demo_app_sha256="d" * 64, dev_manifest_sha256="e" * 64,
        eval_manifest_sha256="f" * 64)


def _task_input(name="Baseline Project"):
    from benchmarks.manifest import TaskInput

    return TaskInput(id="I-PLAIN", project_name=name,
                     expected_stored_name=name)


def _run_replay(tmp_path, name, slow_ms=0, disabled=False):
    from benchmarks.manifest import Scenario

    execution = replay_executor(
        scenario=Scenario(id="S-X", description="", fault_variants=(),
                         expected_outcome="succeeded", timeout_seconds=30.0,
                         postconditions=()),
        task_input=_task_input(name),
        fault=FaultConfig(slow_ms=slow_ms, disabled=disabled),
        trace_dir=tmp_path, token=None, timeout_seconds=30.0)
    return execution


def _verify(execution, name):
    return verify_postconditions(
        snapshot=execution.state_snapshot,
        expected_stored_name=name,
        snapshot_ref=execution.snapshot_ref or "",
        run_id=execution.run_id,
        observation_error=execution.observation_error)


def test_replay_succeeds_on_normal(tmp_path):
    execution = _run_replay(tmp_path, "Baseline Project")
    assert execution.reported_status == "succeeded"
    evidence = _verify(execution, "Baseline Project")
    assert evidence.status == "verified"
    assert evidence.all_satisfied is True


def test_replay_fails_on_slow(tmp_path):
    execution = _run_replay(tmp_path, "Baseline Project", slow_ms=2000)
    assert execution.reported_status == "failed"
    assert "TimeoutError" in (execution.error or "")


def test_replay_fails_on_disabled(tmp_path):
    execution = _run_replay(tmp_path, "Baseline Project", disabled=True)
    assert execution.reported_status == "failed"


def test_replay_fails_on_slow_disabled(tmp_path):
    execution = _run_replay(
        tmp_path, "Baseline Project", slow_ms=2000, disabled=True)
    assert execution.reported_status == "failed"


def test_runner_end_to_end_baseline_a(tmp_path):
    import chimera.agent as agent_module

    manifest = parse_manifest({
        "schema_version": 1,
        "benchmark_id": "chimera-local",
        "benchmark_version": "1.0.0",
        "manifest_id": "fixture-a",
        "split": "development",
        "description": "Baseline A end-to-end fixture.",
        "slow_band_ms": {"min_ms": 500, "max_ms": 4000},
        "config": {
            "trials_per_cell": 1,
            "warmup_episodes": 0,
            "episode_timeout_seconds": 30.0,
            "action_timeout_ms": agent_module.ACTION_TIMEOUT_MS,
            "policy": {
                "max_attempts":
                    agent_module.DEFAULT_POLICY.max_attempts,
                "base_delay_seconds":
                    agent_module.DEFAULT_POLICY.base_delay_seconds,
                "max_delay_seconds":
                    agent_module.DEFAULT_POLICY.max_delay_seconds,
                "max_total_seconds":
                    agent_module.DEFAULT_POLICY.max_total_seconds,
            },
        },
        "scenarios": [
            {
                "id": "S-NORM",
                "description": "No fault.",
                "fault_variants": [{"slow_ms": 0, "disabled": False}],
                "expected_outcome": "succeeded",
                "timeout_seconds": 30.0,
                "preconditions": [],
                "postconditions": [
                    {"id": "P1", "kind": "confirmation_visible",
                     "description": "P1",
                     "verified_by": "independent_verifier"},
                    {"id": "P2", "kind": "exact_stored_name_in_list",
                     "description": "P2",
                     "verified_by": "independent_verifier"},
                    {"id": "P3", "kind": "no_unexpected_entries",
                     "description": "P3",
                     "verified_by": "independent_verifier"},
                ],
                "inputs": [{
                    "id": "I-PLAIN",
                    "project_name": "Benchmark Project",
                    "expected_stored_name": "Benchmark Project",
                }],
            },
            {
                "id": "S-SLOW",
                "description": "Transient fault.",
                "fault_variants": [{"slow_ms": 2000, "disabled": False}],
                "expected_outcome": "succeeded",
                "timeout_seconds": 30.0,
                "preconditions": [],
                "postconditions": [
                    {"id": "P1", "kind": "confirmation_visible",
                     "description": "P1",
                     "verified_by": "independent_verifier"},
                    {"id": "P2", "kind": "exact_stored_name_in_list",
                     "description": "P2",
                     "verified_by": "independent_verifier"},
                    {"id": "P3", "kind": "no_unexpected_entries",
                     "description": "P3",
                     "verified_by": "independent_verifier"},
                ],
                "inputs": [{
                    "id": "I-PLAIN",
                    "project_name": "Benchmark Project",
                    "expected_stored_name": "Benchmark Project",
                }],
            },
        ],
    })
    result = Runner(
        manifest, output_path=tmp_path / "r.json",
        trace_dir=tmp_path / "t", environment=_env(),
        baseline=BASELINE_ID).run()
    assert result.totals.episodes == 2
    assert [e.baseline for e in result.episodes] == [BASELINE_ID] * 2
    norm, slow = result.episodes
    assert norm.scenario_id == "S-NORM"
    assert norm.outcome.value == "succeeded"
    assert norm.verification.all_satisfied is True
    assert norm.retries.value == 0
    assert slow.scenario_id == "S-SLOW"
    assert slow.outcome.value == "failed"
    assert result.cells[0].false_successes.value == 0
    assert (tmp_path / "r.json").is_file()
    assert load_run_result(tmp_path / "r.json").run_id == result.run_id
