"""Tests for the benchmark manifest schema (harness Stage 1).

Covers: valid manifests, invalid manifests, schema-version handling,
content hashing, and the dev/eval split discipline described in
``docs/benchmark_design.md`` §4.

These are schema tests. They assert nothing about the agent's
performance — the regression suite and the benchmark are separate
kinds of evidence (``docs/evaluation.md`` §1).
"""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from benchmarks.manifest import (
    MANIFEST_SCHEMA_VERSION,
    Manifest,
    ManifestValidationError,
    load_manifest,
    parse_manifest,
)

MANIFEST_DIR = Path(__file__).resolve().parent.parent / "benchmarks" / "manifests"
DEV_PATH = MANIFEST_DIR / "dev-v1.json"
EVAL_PATH = MANIFEST_DIR / "eval-v1.json"


def _raw(path: Path = DEV_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class ValidManifestTests(unittest.TestCase):
    """The shipped manifests are valid and carry the documented content."""

    def test_dev_manifest_loads(self) -> None:
        manifest = load_manifest(DEV_PATH)
        self.assertEqual(manifest.schema_version, MANIFEST_SCHEMA_VERSION)
        self.assertEqual(manifest.split, "development")
        self.assertEqual(manifest.manifest_id, "dev-v1")
        self.assertEqual(manifest.benchmark_id, "chimera-local")
        self.assertEqual(len(manifest.scenarios), 4)

    def test_eval_manifest_loads(self) -> None:
        manifest = load_manifest(EVAL_PATH)
        self.assertEqual(manifest.split, "evaluation")
        self.assertEqual(manifest.manifest_id, "eval-v1")
        self.assertEqual(len(manifest.scenarios), 4)

    def test_scenario_ids_match_the_design_catalogue(self) -> None:
        expected = {"S-NORM", "S-SLOW", "S-DIS", "S-SLOWDIS"}
        for path in (DEV_PATH, EVAL_PATH):
            manifest = load_manifest(path)
            self.assertEqual({s.id for s in manifest.scenarios}, expected)

    def test_persistent_fault_scenarios_expect_failure(self) -> None:
        """S-DIS and S-SLOWDIS expect failure; a success there is a bug."""
        for path in (DEV_PATH, EVAL_PATH):
            manifest = load_manifest(path)
            for scenario in manifest.scenarios:
                if scenario.id in ("S-DIS", "S-SLOWDIS"):
                    self.assertEqual(scenario.expected_outcome, "failed")
                else:
                    self.assertEqual(scenario.expected_outcome, "succeeded")

    def test_manifest_declares_postconditions(self) -> None:
        manifest = load_manifest(DEV_PATH)
        for scenario in manifest.scenarios:
            ids = {p.id for p in scenario.postconditions}
            self.assertEqual(ids, {"P1", "P2", "P3"})
            self.assertIn("P4", {p.id for p in scenario.preconditions})

    def test_trimmed_input_states_its_expected_stored_name(self) -> None:
        """The demo app stores the trimmed name; the manifest says so."""
        manifest = load_manifest(DEV_PATH)
        scenario = manifest.scenario("S-NORM")
        by_id = {i.id: i for i in scenario.inputs}
        self.assertEqual(by_id["I-SPACE"].project_name, "  Padded Name  ")
        self.assertEqual(by_id["I-SPACE"].stored_name(), "Padded Name")
        self.assertEqual(by_id["I-PLAIN"].stored_name(), "Benchmark Project")

    def test_cell_order_is_deterministic_and_manifest_declared(self) -> None:
        manifest = load_manifest(DEV_PATH)
        first = manifest.cells()
        second = manifest.cells()
        self.assertEqual(first, second)
        self.assertEqual([c.scenario_id for c in first][:4], ["S-NORM"] * 4)
        self.assertEqual(len(first), 16)

    def test_total_episodes_follows_trials_per_cell(self) -> None:
        manifest = load_manifest(DEV_PATH)
        self.assertEqual(manifest.total_episodes(), len(manifest.cells()) * 5)

    def test_eval_manifest_meets_the_srs_episode_minimum(self) -> None:
        """SRS §11.2 asks for at least 100 task episodes."""
        manifest = load_manifest(EVAL_PATH)
        self.assertGreaterEqual(manifest.total_episodes(), 100)

    def test_slow_band_is_declared_and_respected(self) -> None:
        for path in (DEV_PATH, EVAL_PATH):
            manifest = load_manifest(path)
            for scenario in manifest.scenarios:
                for fault in scenario.fault_variants:
                    if fault.slow_ms:
                        self.assertTrue(manifest.slow_band_ms.contains(fault.slow_ms))


class SplitDisciplineTests(unittest.TestCase):
    """The design's §4 split rules, expressed as assertions."""

    def test_scenario_ids_are_the_same_in_both_manifests(self) -> None:
        dev = load_manifest(DEV_PATH)
        ev = load_manifest(EVAL_PATH)
        self.assertEqual({s.id for s in dev.scenarios}, {s.id for s in ev.scenarios})

    def test_fault_types_are_the_same_in_both_manifests(self) -> None:
        """The split varies parameter *values*, not fault *types*."""
        def kinds(manifest: Manifest) -> set:
            return {
                (s.id, bool(f.slow_ms), bool(f.disabled))
                for s in manifest.scenarios
                for f in s.fault_variants
            }

        self.assertEqual(kinds(load_manifest(DEV_PATH)), kinds(load_manifest(EVAL_PATH)))

    def test_slow_values_do_not_overlap(self) -> None:
        """The evaluation manifest's slow values must be unseen values."""
        def slow_values(manifest: Manifest) -> set:
            return {f.slow_ms for s in manifest.scenarios for f in s.fault_variants if f.slow_ms}

        self.assertEqual(slow_values(load_manifest(DEV_PATH)) & slow_values(load_manifest(EVAL_PATH)), set())

    def test_dev_manifest_uses_the_testsuite_slow_value(self) -> None:
        """The dev manifest is debugged against, so it reuses 2000 ms."""
        manifest = load_manifest(DEV_PATH)
        slow = {f.slow_ms for s in manifest.scenarios for f in s.fault_variants if f.slow_ms}
        self.assertEqual(slow, {2000})

    def test_eval_input_variations_are_a_strict_subset(self) -> None:
        dev = load_manifest(DEV_PATH)
        ev = load_manifest(EVAL_PATH)

        def input_ids(manifest: Manifest) -> set:
            return {i.id for s in manifest.scenarios for i in s.inputs}

        self.assertTrue(input_ids(ev) < input_ids(dev))

    def test_manifests_have_different_content_hashes(self) -> None:
        self.assertNotEqual(load_manifest(DEV_PATH).sha256(), load_manifest(EVAL_PATH).sha256())


class ContentHashTests(unittest.TestCase):
    def test_hash_is_stable_across_reloads(self) -> None:
        self.assertEqual(load_manifest(DEV_PATH).sha256(), load_manifest(DEV_PATH).sha256())

    def test_hash_is_independent_of_key_order_in_the_file(self) -> None:
        raw = _raw()
        reordered = {k: raw[k] for k in sorted(raw, reverse=True)}
        self.assertEqual(parse_manifest(raw).sha256(), parse_manifest(reordered).sha256())

    def test_hash_changes_when_a_parameter_value_changes(self) -> None:
        raw = _raw()
        raw["scenarios"][1]["fault_variants"][0]["slow_ms"] = 2500
        self.assertNotEqual(parse_manifest(raw).sha256(), load_manifest(DEV_PATH).sha256())


class InvalidManifestTests(unittest.TestCase):
    """Malformed and invalid manifests must be rejected, with reasons."""

    def _expect_rejection(self, raw: dict, fragment: str) -> ManifestValidationError:
        with self.assertRaises(ManifestValidationError) as ctx:
            parse_manifest(raw)
        joined = " | ".join(ctx.exception.issues)
        self.assertIn(fragment, joined)
        return ctx.exception

    def test_duplicate_scenario_ids_are_rejected(self) -> None:
        raw = _raw()
        raw["scenarios"].append(copy.deepcopy(raw["scenarios"][0]))
        self._expect_rejection(raw, "duplicate scenario id")

    def test_duplicate_input_ids_are_rejected(self) -> None:
        raw = _raw()
        raw["scenarios"][0]["inputs"].append(copy.deepcopy(raw["scenarios"][0]["inputs"][0]))
        self._expect_rejection(raw, "repeats input id")

    def test_duplicate_postcondition_ids_are_rejected(self) -> None:
        raw = _raw()
        raw["scenarios"][0]["postconditions"].append(copy.deepcopy(raw["scenarios"][0]["postconditions"][0]))
        self._expect_rejection(raw, "repeats postcondition id")

    def test_non_positive_scenario_timeout_is_rejected(self) -> None:
        raw = _raw()
        raw["scenarios"][0]["timeout_seconds"] = 0
        self._expect_rejection(raw, "timeout_seconds must be a positive number")

    def test_negative_scenario_timeout_is_rejected(self) -> None:
        raw = _raw()
        raw["scenarios"][0]["timeout_seconds"] = -1.0
        self._expect_rejection(raw, "timeout_seconds must be a positive number")

    def test_non_positive_episode_timeout_is_rejected(self) -> None:
        raw = _raw()
        raw["config"]["episode_timeout_seconds"] = 0
        self._expect_rejection(raw, "episode_timeout_seconds must be a positive number")

    def test_non_positive_action_timeout_is_rejected(self) -> None:
        raw = _raw()
        raw["config"]["action_timeout_ms"] = 0
        self._expect_rejection(raw, "action_timeout_ms must be a positive integer")

    def test_zero_trial_count_is_rejected(self) -> None:
        raw = _raw()
        raw["config"]["trials_per_cell"] = 0
        self._expect_rejection(raw, "trials_per_cell must be an integer >= 1")

    def test_negative_trial_count_is_rejected(self) -> None:
        raw = _raw()
        raw["config"]["trials_per_cell"] = -3
        self._expect_rejection(raw, "trials_per_cell must be an integer >= 1")

    def test_non_integer_trial_count_is_rejected(self) -> None:
        """A wrong *type* is malformed; a wrong *value* is invalid."""
        raw = _raw()
        raw["config"]["trials_per_cell"] = 2.5
        error = self._expect_rejection(raw, "config.trials_per_cell must be an integer")
        self.assertTrue(any(i.startswith("malformed:") for i in error.issues))

    def test_negative_warmup_count_is_rejected(self) -> None:
        raw = _raw()
        raw["config"]["warmup_episodes"] = -1
        self._expect_rejection(raw, "warmup_episodes must be an integer >= 0")

    def test_slow_value_outside_the_declared_band_is_rejected(self) -> None:
        raw = _raw()
        raw["scenarios"][1]["fault_variants"][0]["slow_ms"] = 9000
        self._expect_rejection(raw, "outside the declared slow band")

    def test_band_wider_than_the_action_timeout_is_rejected(self) -> None:
        raw = _raw()
        raw["slow_band_ms"]["max_ms"] = 9000
        self._expect_rejection(raw, "must be <")

    def test_invalid_expected_outcome_is_rejected(self) -> None:
        raw = _raw()
        raw["scenarios"][0]["expected_outcome"] = "inconclusive"
        self._expect_rejection(raw, "expected_outcome")

    def test_invalid_split_is_rejected(self) -> None:
        raw = _raw()
        raw["split"] = "holdout"
        self._expect_rejection(raw, "split")

    def test_scenario_without_inputs_is_rejected(self) -> None:
        raw = _raw()
        raw["scenarios"][0]["inputs"] = []
        self._expect_rejection(raw, "must declare at least one input")

    def test_scenario_without_postconditions_is_rejected(self) -> None:
        raw = _raw()
        raw["scenarios"][0]["postconditions"] = []
        self._expect_rejection(raw, "must declare at least one postcondition")

    def test_empty_scenario_list_is_rejected(self) -> None:
        raw = _raw()
        raw["scenarios"] = []
        self._expect_rejection(raw, "at least one scenario")

    def test_inconsistent_retry_policy_is_rejected(self) -> None:
        raw = _raw()
        raw["config"]["policy"]["max_delay_seconds"] = 0.01
        self._expect_rejection(raw, "max_delay_seconds")

    def test_missing_required_key_is_malformed(self) -> None:
        raw = _raw()
        del raw["benchmark_id"]
        self._expect_rejection(raw, "missing required key 'benchmark_id'")

    def test_wrong_type_is_malformed(self) -> None:
        raw = _raw()
        raw["scenarios"] = "not-a-list"
        self._expect_rejection(raw, "malformed")

    def test_not_a_json_object_is_malformed(self) -> None:
        with self.assertRaises(ManifestValidationError):
            parse_manifest([])  # type: ignore[arg-type]

    def test_invalid_json_file_is_malformed(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text("{not json", encoding="utf-8")
            with self.assertRaises(ManifestValidationError) as ctx:
                load_manifest(bad)
            self.assertIn("not valid JSON", " ".join(ctx.exception.issues))


class SchemaVersionTests(unittest.TestCase):
    """An unsupported schema version is rejected, not guessed at."""

    def test_unsupported_schema_version_is_rejected(self) -> None:
        raw = _raw()
        raw["schema_version"] = 99
        with self.assertRaises(ManifestValidationError) as ctx:
            parse_manifest(raw)
        joined = " ".join(ctx.exception.issues)
        self.assertIn("unsupported schema_version", joined)
        self.assertIn("99", joined)

    def test_schema_version_zero_is_rejected(self) -> None:
        raw = _raw()
        raw["schema_version"] = 0
        with self.assertRaises(ManifestValidationError) as ctx:
            parse_manifest(raw)
        self.assertIn("unsupported schema_version", " ".join(ctx.exception.issues))

    def test_shipped_manifests_declare_the_supported_version(self) -> None:
        for path in (DEV_PATH, EVAL_PATH):
            self.assertEqual(_raw(path)["schema_version"], MANIFEST_SCHEMA_VERSION)

    def test_schema_version_appears_first_in_the_serialised_form(self) -> None:
        """The version must be visible without parsing the whole file."""
        manifest = load_manifest(DEV_PATH)
        serialised = json.loads(manifest.to_json())
        self.assertIn("schema_version", serialised)
        self.assertEqual(serialised["schema_version"], MANIFEST_SCHEMA_VERSION)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
