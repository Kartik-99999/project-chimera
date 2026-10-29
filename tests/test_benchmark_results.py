"""Tests for the benchmark result schema (harness Stage 1).

Covers: metric representation (measured vs. unavailable), the four
episode outcomes, verification evidence, false-success detection, and
serialisation round-trips.

These are schema tests. They assert nothing about the agent's
performance — the regression suite and the benchmark are separate
kinds of evidence (``docs/evaluation.md`` §1).
"""

from __future__ import annotations

import json
import unittest
from typing import Any, Dict

from benchmarks.results import (
    RESULT_SCHEMA_VERSION,
    CellResult,
    EnvironmentInfo,
    EpisodeOutcome,
    EpisodeResult,
    Metric,
    PostconditionCheck,
    ResultValidationError,
    RunResult,
    RunTotals,
    VerificationEvidence,
    VerifierAudit,
    false_success_set,
)


def _environment() -> EnvironmentInfo:
    return EnvironmentInfo(
        python_version="3.9.6",
        playwright_version="1.60.0",
        browser="chromium",
        browser_build="1223",
        platform="darwin",
        demo_app_sha256="a" * 64,
        dev_manifest_sha256="b" * 64,
        eval_manifest_sha256="c" * 64,
    )


def _episode(**overrides: Any) -> EpisodeResult:
    base: Dict[str, Any] = dict(
        trial_id="trial-0001",
        run_id="11111111-2222-3333-4444-555555555555",
        scenario_id="S-SLOW",
        input_id="I-PLAIN",
        baseline="chimera",
        manifest_id="eval-v1",
        manifest_version="1.0.0",
        manifest_schema_version=1,
        outcome=EpisodeOutcome.SUCCEEDED,
        agent_terminal_status="succeeded",
        started_at="2026-10-24T10:00:00.000Z",
        completed_at="2026-10-24T10:00:01.250Z",
        duration_ms=1250,
        trace_artifact="data/traces/11111111-2222-3333-4444-555555555555.json",
        verification=VerificationEvidence(
            status=VerificationEvidence.VERIFIED,
            all_satisfied=True,
            checks=(
                PostconditionCheck("P1", True, "dom:#confirmation", "visible"),
                PostconditionCheck("P2", True, "dom:#project-list li[0]", "exact match"),
                PostconditionCheck("P3", True, "dom:#project-list", "count == 1"),
            ),
            verifier_version="verifier-0.1.0",
        ),
        safety_violations=Metric.measured(0),
        unauthorized_actions=Metric.measured(0),
        retries=Metric.measured(0),
        actions_executed=Metric.measured(3),
    )
    base.update(overrides)
    return EpisodeResult(**base)


def _cell(**overrides: Any) -> CellResult:
    base: Dict[str, Any] = dict(
        scenario_id="S-SLOW",
        input_id="I-PLAIN",
        baseline="chimera",
        fault_params={"slow_ms": 1350, "disabled": False},
        trials=5,
        outcomes={
            "succeeded": Metric.measured(5),
            "failed": Metric.measured(0),
            "cancelled": Metric.measured(0),
            "inconclusive": Metric.unavailable(
                "not an observable category until ADR-004 Q4 is resolved"
            ),
        },
        independent_verification={
            "P1_confirmation_visible": Metric.measured(5),
            "P2_exact_name_in_list": Metric.measured(5),
            "P3_no_unexpected_entries": Metric.measured(5),
        },
        false_successes=Metric.measured(0),
        verifier_disagreements=Metric.measured(0),
        unauthorized_actions=Metric.measured(0),
        safety_violations=Metric.measured(0),
        retries=Metric.measured(0),
        actions=Metric.measured(15),
        latency_ms={
            "p50": Metric.measured(1200.0),
            "p95": Metric.measured(1500.0),
            "min": Metric.measured(1100.0),
            "max": Metric.measured(1500.0),
        },
        model_calls=Metric.unavailable("no model adapter exists (SRS 7.4)"),
        model_cost_usd=Metric.unavailable("no model adapter exists (SRS 7.4)"),
        human_interventions=Metric.unavailable("no operator interface exists"),
        failure_categories={},
        trace_artifacts=("data/traces/one.json",),
    )
    base.update(overrides)
    return CellResult(**base)


def _run(**overrides: Any) -> RunResult:
    base: Dict[str, Any] = dict(
        schema_version=RESULT_SCHEMA_VERSION,
        benchmark_id="chimera-local",
        benchmark_version="1.0.0",
        run_id="99999999-8888-7777-6666-555555555555",
        started_at="2026-10-24T10:00:00.000Z",
        completed_at="2026-10-24T10:05:00.000Z",
        status="proposed",
        agent_version="milestone-1-foundation",
        srs_mapping="adr-004",
        manifest_id="eval-v1",
        manifest_version="1.0.0",
        manifest_schema_version=1,
        manifest_sha256="c" * 64,
        environment=_environment(),
        config={"trials_per_cell": 5, "warmup_episodes": 1},
        cells=(_cell(),),
        episodes=(_episode(),),
        totals=RunTotals(
            episodes=1,
            by_baseline={"chimera": 1},
            false_success_rate=Metric.unavailable("denominator is 0: no verified episode"),
            unauthorized_actions=Metric.measured(0),
        ),
        notes="Design illustration. No run has been performed.",
    )
    base.update(overrides)
    return RunResult(**base)


class MetricTests(unittest.TestCase):
    """A missing metric is unavailable-with-a-reason, never zero."""

    def test_measured_zero_is_distinct_from_unavailable(self) -> None:
        measured = Metric.measured(0)
        unavailable = Metric.unavailable("no observer")
        self.assertTrue(measured.is_available)
        self.assertFalse(unavailable.is_available)
        self.assertEqual(measured.value, 0)
        self.assertIsNone(unavailable.value)

    def test_metric_cannot_be_both_measured_and_unavailable(self) -> None:
        with self.assertRaises(ResultValidationError):
            Metric(value=1, unavailable_reason="why")

    def test_measured_metric_with_a_none_value_is_permitted(self) -> None:
        """A null measurement is still a measurement."""
        metric = Metric.measured(None)
        self.assertTrue(metric.is_available)
        self.assertIsNone(metric.value)
        self.assertIsNone(metric.unavailable_reason)

    def test_availability_is_driven_by_the_reason_not_the_value(self) -> None:
        """A measured null is available; an unavailable metric is not."""
        self.assertTrue(Metric.measured(None).is_available)
        self.assertFalse(Metric.unavailable("blocked").is_available)

    def test_empty_reason_is_rejected(self) -> None:
        with self.assertRaises(ResultValidationError):
            Metric.unavailable("   ")

    def test_unavailable_metric_must_not_also_carry_a_value(self) -> None:
        with self.assertRaises(ResultValidationError):
            Metric(value=3, unavailable_reason="why")

    def test_unavailable_serialises_with_the_reason(self) -> None:
        payload = Metric.unavailable("blocked on the action observer").to_dict()
        self.assertIsNone(payload["value"])
        self.assertEqual(payload["unavailable_reason"], "blocked on the action observer")

    def test_measured_zero_serialises_as_zero_not_null(self) -> None:
        payload = Metric.measured(0).to_dict()
        self.assertEqual(payload["value"], 0)
        self.assertIsNone(payload["unavailable_reason"])

    def test_round_trip_preserves_availability(self) -> None:
        for metric in (Metric.measured(0), Metric.measured(7), Metric.unavailable("n/a")):
            self.assertEqual(Metric.from_dict(metric.to_dict()), metric)

    def test_round_trip_preserves_a_measured_numeric_value(self) -> None:
        metric = Metric.measured(42)
        restored = Metric.from_dict(metric.to_dict())
        self.assertEqual(restored.value, 42)
        self.assertIsNone(restored.unavailable_reason)
        self.assertTrue(restored.is_available)

    def test_round_trip_preserves_a_measured_none_value(self) -> None:
        metric = Metric.measured(None)
        restored = Metric.from_dict(metric.to_dict())
        self.assertEqual(restored, metric)
        self.assertTrue(restored.is_available)
        self.assertIsNone(restored.value)

    def test_round_trip_preserves_an_unavailable_metric(self) -> None:
        metric = Metric.unavailable("the action observer is not built yet")
        restored = Metric.from_dict(metric.to_dict())
        self.assertEqual(restored, metric)
        self.assertFalse(restored.is_available)
        self.assertIsNone(restored.value)
        self.assertEqual(restored.unavailable_reason, "the action observer is not built yet")

    def test_serialised_measured_metric_still_carries_the_reason_key(self) -> None:
        """The key is always present; only its value discriminates."""
        payload = Metric.measured(5).to_dict()
        self.assertIn("unavailable_reason", payload)
        self.assertIsNone(payload["unavailable_reason"])
        self.assertTrue(Metric.from_dict(payload).is_available)

    def test_serialised_unavailable_metric_is_not_mistaken_for_measured(self) -> None:
        """The defect this guards: key presence must not decide the state."""
        payload = Metric.unavailable("blocked").to_dict()
        self.assertIn("value", payload)
        self.assertIsNone(payload["value"])
        restored = Metric.from_dict(payload)
        self.assertFalse(restored.is_available)
        self.assertEqual(restored.unavailable_reason, "blocked")

    def test_document_with_neither_key_is_rejected(self) -> None:
        with self.assertRaises(ResultValidationError):
            Metric.from_dict({})


class OutcomeTests(unittest.TestCase):
    def test_all_four_outcomes_exist(self) -> None:
        self.assertEqual(
            {o.value for o in EpisodeOutcome},
            {"succeeded", "failed", "cancelled", "inconclusive"},
        )

    def test_outcome_round_trips(self) -> None:
        for outcome in EpisodeOutcome:
            self.assertEqual(EpisodeOutcome(outcome.value), outcome)

    def test_inconclusive_is_representable_but_not_measured(self) -> None:
        """Design §8.3: inconclusive is not an observable category today."""
        cell = _cell()
        self.assertFalse(cell.outcomes["inconclusive"].is_available)
        self.assertIn("ADR-004", cell.outcomes["inconclusive"].unavailable_reason)


class VerificationEvidenceTests(unittest.TestCase):
    def test_verified_evidence_requires_a_verdict(self) -> None:
        with self.assertRaises(ResultValidationError):
            VerificationEvidence(status=VerificationEvidence.VERIFIED)

    def test_unavailable_evidence_requires_a_reason(self) -> None:
        with self.assertRaises(ResultValidationError):
            VerificationEvidence(status=VerificationEvidence.UNAVAILABLE)

    def test_unavailable_evidence_carries_no_verdict(self) -> None:
        with self.assertRaises(ResultValidationError):
            VerificationEvidence(
                status=VerificationEvidence.UNAVAILABLE,
                all_satisfied=True,
                unavailable_reason="verifier not built yet",
            )

    def test_checks_survive_a_round_trip(self) -> None:
        evidence = _episode().verification
        restored = VerificationEvidence.from_dict(evidence.to_dict())
        self.assertEqual(restored, evidence)
        self.assertEqual(len(restored.checks), 3)

    def test_audit_round_trips(self) -> None:
        audit = VerifierAudit(sampled=10, agreed=9, agreement_rate=0.9)
        self.assertEqual(VerifierAudit.from_dict(audit.to_dict()), audit)

    def test_audit_with_no_rate_is_allowed(self) -> None:
        audit = VerifierAudit(sampled=10, agreed=9)
        self.assertIsNone(audit.agreement_rate)


class EpisodeResultTests(unittest.TestCase):
    def test_round_trip_preserves_every_field(self) -> None:
        episode = _episode()
        restored = EpisodeResult.from_dict(episode.to_dict())
        self.assertEqual(restored, episode)

    def test_round_trip_through_json(self) -> None:
        episode = _episode()
        restored = EpisodeResult.from_dict(json.loads(json.dumps(episode.to_dict())))
        self.assertEqual(restored, episode)

    def test_trial_and_run_ids_are_carried(self) -> None:
        episode = _episode()
        self.assertEqual(episode.trial_id, "trial-0001")
        self.assertEqual(episode.run_id, "11111111-2222-3333-4444-555555555555")

    def test_manifest_and_scenario_versions_are_carried(self) -> None:
        episode = _episode()
        self.assertEqual(episode.manifest_id, "eval-v1")
        self.assertEqual(episode.manifest_version, "1.0.0")
        self.assertEqual(episode.manifest_schema_version, 1)
        self.assertEqual(episode.scenario_id, "S-SLOW")

    def test_unavailable_metric_is_not_serialised_as_zero(self) -> None:
        episode = _episode(retries=Metric.unavailable("no trace artifact"))
        payload = episode.to_dict()
        self.assertIsNone(payload["retries"]["value"])
        self.assertEqual(payload["retries"]["unavailable_reason"], "no trace artifact")

    def test_evidence_reference_is_preserved(self) -> None:
        episode = _episode()
        payload = episode.to_dict()
        self.assertEqual(
            payload["verification"]["checks"][1]["evidence_reference"],
            "dom:#project-list li[0]",
        )


class CellResultTests(unittest.TestCase):
    def test_round_trip_preserves_every_field(self) -> None:
        cell = _cell()
        restored = CellResult.from_dict(cell.to_dict())
        self.assertEqual(restored, cell)

    def test_blocked_metrics_keep_their_reasons(self) -> None:
        cell = _cell()
        payload = cell.to_dict()
        self.assertIsNone(payload["model_calls"]["value"])
        self.assertIn("no model adapter", payload["model_calls"]["unavailable_reason"])
        self.assertIsNone(payload["human_interventions"]["value"])


class RunResultTests(unittest.TestCase):
    def test_round_trip_preserves_every_field(self) -> None:
        run = _run()
        restored = RunResult.from_dict(run.to_dict())
        self.assertEqual(restored, run)

    def test_round_trip_through_json(self) -> None:
        run = _run()
        restored = RunResult.from_dict(json.loads(run.to_json()))
        self.assertEqual(restored, run)

    def test_serialised_form_is_valid_json(self) -> None:
        payload = json.loads(_run().to_json())
        self.assertEqual(payload["schema_version"], RESULT_SCHEMA_VERSION)
        self.assertEqual(payload["status"], "proposed")

    def test_unsupported_schema_version_is_rejected(self) -> None:
        payload = _run().to_dict()
        payload["schema_version"] = 99
        with self.assertRaises(ResultValidationError) as ctx:
            RunResult.from_dict(payload)
        self.assertIn("unsupported result schema_version", str(ctx.exception))

    def test_invalid_status_is_rejected(self) -> None:
        payload = _run().to_dict()
        payload["status"] = "measured-ish"
        with self.assertRaises(ResultValidationError) as ctx:
            RunResult.from_dict(payload)
        self.assertIn("status", str(ctx.exception))

    def test_false_success_rate_with_no_denominator_is_unavailable(self) -> None:
        run = _run()
        self.assertFalse(run.totals.false_success_rate.is_available)
        self.assertIn("denominator is 0", run.totals.false_success_rate.unavailable_reason)


class FalseSuccessTests(unittest.TestCase):
    """``false_success := (agent said succeeded) AND NOT (P1 AND P2 AND P3)``."""

    def test_agent_succeeded_but_verifier_failed_is_a_false_success(self) -> None:
        episode = _episode(
            verification=VerificationEvidence(
                status=VerificationEvidence.VERIFIED,
                all_satisfied=False,
                checks=(PostconditionCheck("P2", False, "dom:#project-list li[0]", "no match"),),
                verifier_version="verifier-0.1.0",
            )
        )
        self.assertEqual(false_success_set([episode]), (episode,))

    def test_agent_succeeded_and_verifier_confirmed_is_not_a_false_success(self) -> None:
        episode = _episode()
        self.assertEqual(false_success_set([episode]), ())

    def test_agent_failed_is_not_a_false_success(self) -> None:
        episode = _episode(
            outcome=EpisodeOutcome.FAILED,
            agent_terminal_status="failed",
            verification=VerificationEvidence(
                status=VerificationEvidence.VERIFIED,
                all_satisfied=False,
                verifier_version="verifier-0.1.0",
            ),
        )
        self.assertEqual(false_success_set([episode]), ())

    def test_unverified_evidence_is_neither_success_nor_false_success(self) -> None:
        episode = _episode(
            verification=VerificationEvidence.not_yet_verified("verifier not built yet")
        )
        self.assertEqual(false_success_set([episode]), ())

    def test_a_cancelled_episode_is_not_a_false_success(self) -> None:
        episode = _episode(
            outcome=EpisodeOutcome.CANCELLED,
            agent_terminal_status="cancelled",
            verification=VerificationEvidence.not_yet_verified("cancelled before verification"),
        )
        self.assertEqual(false_success_set([episode]), ())

    def test_only_the_flagged_episodes_are_returned(self) -> None:
        good = _episode(trial_id="t-good")
        bad = _episode(
            trial_id="t-bad",
            verification=VerificationEvidence(
                status=VerificationEvidence.VERIFIED,
                all_satisfied=False,
                verifier_version="verifier-0.1.0",
            ),
        )
        self.assertEqual(false_success_set([good, bad]), (bad,))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
