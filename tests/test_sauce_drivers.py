"""Tests for the SauceDemo drivers against a stateful fake store.

Covers: successful replay (login → sort → cart → checkout → order),
the replay report schema and stages artifacts, failure cases
(invalid login, empty cart, invalid checkout, step failure,
cancellation), the agent's order flow including its cart gate and
password hygiene, and SELECT policy judging.

These are harness tests with a scripted fake page (no browser, no
network); they assert nothing about the live site.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from adapters import saucedemo as adapter
from benchmarks.baseline_a import (
    SAUCE_REPORT_SCHEMA,
    run_saucedemo_replay,
    run_saucedemo_stress_replay,
)
from benchmarks.observer import (
    ALLOWED,
    DENIED,
    UNKNOWN,
    ActionPolicy,
)
from chimera.agent import run_saucedemo_order
from chimera.safety import CancellationToken
from tests.fake_saucedemo import (
    FakeSauceBrowser,
    FakeSauceContext,
    FakeSaucePage,
    sauce_expected,
    sauce_order,
    sauce_stress_expected,
)

A = adapter  # short alias for selector constants


class SauceReplayTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def _run(self, page: FakeSaucePage, order: Dict[str, Any],
             **kwargs: Any):
        def _factory():
            return FakeSauceBrowser(), FakeSauceContext(), page

        kwargs.setdefault("settle_timeout_ms", 100)
        return run_saucedemo_replay(
            order=order, expected=sauce_expected(order), trace_dir=self.tmp,
            page_factory=_factory, **kwargs)

    def test_success_writes_report_stages_snapshot_and_judged_log(self) -> None:
        order = sauce_order()
        outcome = self._run(FakeSaucePage(), order, run_id="sauce-ok")
        self.assertEqual(outcome.terminal_status, "succeeded")
        self.assertIsNone(outcome.error)
        report = json.loads(Path(outcome.report_path).read_text())
        self.assertEqual(report["schema"], SAUCE_REPORT_SCHEMA)
        self.assertEqual(report["report_id"], "sauce-ok")
        self.assertTrue(report["steps"])
        self.assertTrue(all(s["outcome"] == "ok" for s in report["steps"]))
        self.assertIn("select", [s["step"] for s in report["steps"]])
        self.assertNotIn("secret_sauce", json.dumps(report))
        stages = adapter.read_stages_file(
            str(self.tmp / "sauce-ok.stages.json"))
        self.assertEqual([s["stage"] for s in stages],
                         ["login", "inventory", "cart", "info", "overview",
                          "complete"])
        verdict = adapter.verify_sauce_order(
            outcome.snapshot, stages, sauce_expected(order))
        self.assertEqual(verdict["status"], "verified")
        self.assertEqual(
            [c["check_id"] for c in verdict["checks"]],
            ["S1", "S2", "S3", "S4", "S5"])
        self.assertTrue(all(c["satisfied"] for c in verdict["checks"]))
        assert outcome.snapshot is not None
        self.assertTrue(outcome.snapshot["confirmation_visible"])
        decisions = [r["policy"]
                     for r in outcome.action_log["records"]]
        self.assertTrue(decisions)
        self.assertTrue(all(d == ALLOWED for d in decisions),
                        f"unexpected decisions: {decisions}")

    def test_sort_none_skips_select_and_s2(self) -> None:
        order = sauce_order(sort="none")
        outcome = self._run(FakeSaucePage(), order, run_id="sauce-none")
        self.assertEqual(outcome.terminal_status, "succeeded")
        report = json.loads(Path(outcome.report_path).read_text())
        self.assertNotIn("select", [s["step"] for s in report["steps"]])
        stages = adapter.read_stages_file(
            str(self.tmp / "sauce-none.stages.json"))
        verdict = adapter.verify_sauce_order(
            outcome.snapshot, stages, sauce_expected(order))
        self.assertEqual([c["check_id"] for c in verdict["checks"]],
                         ["S1", "S3", "S4", "S5"])

    def test_invalid_login_fails_verified(self) -> None:
        order = sauce_order()
        outcome = self._run(FakeSaucePage(login_ok=False), order,
                            run_id="sauce-bad-login")
        self.assertEqual(outcome.terminal_status, "failed")
        assert outcome.error is not None
        self.assertIn("login failed", outcome.error)
        report = json.loads(Path(outcome.report_path).read_text())
        targets = [s["target"] for s in report["steps"]]
        self.assertNotIn("sauce-checkout", targets)
        self.assertNotIn("sauce-finish", targets)
        stages = adapter.read_stages_file(
            str(self.tmp / "sauce-bad-login.stages.json"))
        self.assertEqual([s["stage"] for s in stages], ["login"])
        verdict = adapter.verify_sauce_order(
            outcome.snapshot, stages, sauce_expected(order))
        by_id = {c["check_id"]: c for c in verdict["checks"]}
        self.assertEqual(verdict["status"], "verified")
        self.assertFalse(by_id["S1"]["satisfied"])
        self.assertFalse(by_id["S5"]["satisfied"])

    def test_empty_cart_refuses_checkout(self) -> None:
        order = sauce_order(items=[])
        outcome = self._run(FakeSaucePage(), order, run_id="sauce-empty")
        self.assertEqual(outcome.terminal_status, "failed")
        assert outcome.error is not None
        self.assertIn("empty cart", outcome.error)
        report = json.loads(Path(outcome.report_path).read_text())
        self.assertNotIn("sauce-finish",
                         [s["target"] for s in report["steps"]])
        stages = adapter.read_stages_file(
            str(self.tmp / "sauce-empty.stages.json"))
        self.assertEqual([s["stage"] for s in stages],
                         ["login", "inventory", "cart"])
        verdict = adapter.verify_sauce_order(
            outcome.snapshot, stages, sauce_expected(order))
        by_id = {c["check_id"]: c for c in verdict["checks"]}
        self.assertTrue(by_id["S3"]["satisfied"])  # empty confirmed
        self.assertFalse(by_id["S4"]["satisfied"])  # never attempted
        self.assertFalse(by_id["S5"]["satisfied"])

    def test_invalid_checkout_blocks_at_info(self) -> None:
        order = sauce_order()
        outcome = self._run(FakeSaucePage(info_ok=False), order,
                            run_id="sauce-bad-info")
        self.assertEqual(outcome.terminal_status, "failed")
        assert outcome.error is not None
        self.assertIn("checkout blocked", outcome.error)
        report = json.loads(Path(outcome.report_path).read_text())
        self.assertNotIn("sauce-finish",
                         [s["target"] for s in report["steps"]])
        stages = adapter.read_stages_file(
            str(self.tmp / "sauce-bad-info.stages.json"))
        verdict = adapter.verify_sauce_order(
            outcome.snapshot, stages, sauce_expected(order))
        by_id = {c["check_id"]: c for c in verdict["checks"]}
        self.assertTrue(by_id["S1"]["satisfied"])
        self.assertTrue(by_id["S3"]["satisfied"])
        self.assertFalse(by_id["S4"]["satisfied"])
        self.assertFalse(by_id["S5"]["satisfied"])

    def test_step_failure_stops_sequence(self) -> None:
        page = FakeSaucePage(fail_clicks=frozenset({A.SEL_CHECKOUT}))
        outcome = self._run(page, sauce_order(), run_id="sauce-click-fail")
        self.assertEqual(outcome.terminal_status, "failed")
        assert outcome.error is not None
        self.assertIn("fake click failure", outcome.error)
        report = json.loads(Path(outcome.report_path).read_text())
        targets = [s["target"] for s in report["steps"]]
        self.assertIn("sauce-checkout", targets)
        self.assertNotIn("sauce-continue", targets)
        self.assertNotIn("sauce-finish", targets)

    def test_cancelled_before_start(self) -> None:
        token = CancellationToken()
        token.request()
        outcome = self._run(FakeSaucePage(), sauce_order(),
                            run_id="sauce-cancel", token=token)
        self.assertEqual(outcome.terminal_status, "cancelled")
        report = json.loads(Path(outcome.report_path).read_text())
        self.assertEqual(report["steps"], [])

    def test_bad_settle_timeout_fails_loudly(self) -> None:
        with self.assertRaises(ValueError):
            self._run(FakeSaucePage(), sauce_order(), settle_timeout_ms=0)

    def test_repeat_runs_are_deterministic(self) -> None:
        first = self._run(FakeSaucePage(), sauce_order(), run_id="sauce-det")
        stages_a = adapter.read_stages_file(
            str(self.tmp / "sauce-det.stages.json"))
        with tempfile.TemporaryDirectory() as other:
            other_tmp = Path(other)

            def _factory():
                return FakeSauceBrowser(), FakeSauceContext(), FakeSaucePage()

            second = run_saucedemo_replay(
                order=sauce_order(), expected=sauce_expected(sauce_order()),
                trace_dir=other_tmp, page_factory=_factory,
                settle_timeout_ms=100, run_id="sauce-det")
            stages_b = adapter.read_stages_file(
                str(other_tmp / "sauce-det.stages.json"))
            rep_b = json.loads(Path(second.report_path).read_text())
        rep_a = json.loads(Path(first.report_path).read_text())
        self.assertEqual(rep_a["steps"], rep_b["steps"])
        self.assertEqual(rep_a["terminal_status"], rep_b["terminal_status"])
        self.assertEqual([s["state"] for s in stages_a],
                         [s["state"] for s in stages_b])


class SauceStressReplayTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def _run(self, page: FakeSaucePage, order: Dict[str, Any],
             **kwargs: Any):
        def _factory():
            return FakeSauceBrowser(), FakeSauceContext(), page

        kwargs.setdefault("settle_timeout_ms", 100)
        return run_saucedemo_stress_replay(
            order=order, expected=sauce_stress_expected(order),
            trace_dir=self.tmp, page_factory=_factory, **kwargs)

    def test_stress_success_all_t_checks_pass(self) -> None:
        order = sauce_order(remove="sauce-labs-bike-light")
        outcome = self._run(FakeSaucePage(), order, run_id="stress-ok")
        self.assertEqual(outcome.terminal_status, "succeeded")
        report = json.loads(Path(outcome.report_path).read_text())
        self.assertEqual(report["schema"], SAUCE_REPORT_SCHEMA)
        self.assertEqual(report["order"]["remove"],
                         "sauce-labs-bike-light")
        self.assertIn("sauce-remove:sauce-labs-bike-light",
                      [s["target"] for s in report["steps"]])
        self.assertNotIn("secret_sauce", json.dumps(report))
        stages = adapter.read_stages_file(
            str(self.tmp / "stress-ok.stages.json"))
        self.assertEqual([s["stage"] for s in stages],
                         ["login", "inventory", "cart",
                          "cart_after_remove", "info", "overview",
                          "complete"])
        login_ms = adapter.stage_states(stages)["login"].get("login_ms")
        self.assertIsInstance(login_ms, int)
        verdict = adapter.verify_stress_order(
            outcome.snapshot, stages, sauce_stress_expected(order))
        self.assertEqual(verdict["status"], "verified")
        self.assertEqual([c["check_id"] for c in verdict["checks"]],
                         ["T1", "T2", "T3", "T4", "T5", "T6"])
        self.assertTrue(all(c["satisfied"] for c in verdict["checks"]))
        decisions = [r["policy"]
                     for r in outcome.action_log["records"]]
        self.assertTrue(decisions)
        self.assertTrue(all(d == ALLOWED for d in decisions),
                        f"unexpected decisions: {decisions}")

    def test_stress_no_remove_omits_t5(self) -> None:
        order = sauce_order()
        outcome = self._run(FakeSaucePage(), order,
                            run_id="stress-no-remove")
        self.assertEqual(outcome.terminal_status, "succeeded")
        stages = adapter.read_stages_file(
            str(self.tmp / "stress-no-remove.stages.json"))
        self.assertNotIn("cart_after_remove",
                         [s["stage"] for s in stages])
        verdict = adapter.verify_stress_order(
            outcome.snapshot, stages, sauce_stress_expected(order))
        self.assertEqual([c["check_id"] for c in verdict["checks"]],
                         ["T1", "T2", "T3", "T4", "T6"])
        self.assertTrue(all(c["satisfied"] for c in verdict["checks"]))

    def test_stress_problem_user_shape(self) -> None:
        order = sauce_order(remove="sauce-labs-bike-light", sort="za",
                            user="problem_user")
        page = FakeSaucePage(images_404=True, sort_broken=True,
                             info_reject=True)
        outcome = self._run(page, order, run_id="stress-problem")
        self.assertEqual(outcome.terminal_status, "failed")
        assert outcome.error is not None
        self.assertIn("checkout blocked", outcome.error)
        stages = adapter.read_stages_file(
            str(self.tmp / "stress-problem.stages.json"))
        verdict = adapter.verify_stress_order(
            outcome.snapshot, stages, sauce_stress_expected(order))
        by_id = {c["check_id"]: c for c in verdict["checks"]}
        self.assertEqual(verdict["status"], "verified")
        self.assertTrue(by_id["T1"]["satisfied"])
        self.assertFalse(by_id["T2"]["satisfied"])
        self.assertIn("placeholder", by_id["T2"]["detail"])
        self.assertFalse(by_id["T3"]["satisfied"])
        self.assertTrue(by_id["T4"]["satisfied"])
        self.assertTrue(by_id["T5"]["satisfied"])
        self.assertFalse(by_id["T6"]["satisfied"])
        self.assertIn("checkout rejected by site",
                      by_id["T6"]["detail"])

    def test_stress_login_failure(self) -> None:
        order = sauce_order(remove="sauce-labs-bike-light")
        outcome = self._run(FakeSaucePage(login_ok=False), order,
                            run_id="stress-bad-login")
        self.assertEqual(outcome.terminal_status, "failed")
        assert outcome.error is not None
        self.assertIn("login failed", outcome.error)
        stages = adapter.read_stages_file(
            str(self.tmp / "stress-bad-login.stages.json"))
        self.assertEqual([s["stage"] for s in stages], ["login"])
        verdict = adapter.verify_stress_order(
            outcome.snapshot, stages, sauce_stress_expected(order))
        by_id = {c["check_id"]: c for c in verdict["checks"]}
        self.assertFalse(by_id["T1"]["satisfied"])
        self.assertFalse(by_id["T6"]["satisfied"])

    def test_stress_repeat_runs_are_deterministic(self) -> None:
        order = sauce_order(remove="sauce-labs-bike-light")
        first = self._run(FakeSaucePage(), order, run_id="stress-det")
        stages_a = adapter.read_stages_file(
            str(self.tmp / "stress-det.stages.json"))
        with tempfile.TemporaryDirectory() as other:
            other_tmp = Path(other)

            def _factory():
                return (FakeSauceBrowser(), FakeSauceContext(),
                        FakeSaucePage())

            second = run_saucedemo_stress_replay(
                order=order, expected=sauce_stress_expected(order),
                trace_dir=other_tmp, page_factory=_factory,
                settle_timeout_ms=100, run_id="stress-det")
            stages_b = adapter.read_stages_file(
                str(other_tmp / "stress-det.stages.json"))
            rep_b = json.loads(Path(second.report_path).read_text())
        rep_a = json.loads(Path(first.report_path).read_text())
        self.assertEqual(rep_a["steps"], rep_b["steps"])
        self.assertEqual(rep_a["terminal_status"], rep_b["terminal_status"])

        def _states(stages):
            return [{k: v for k, v in s["state"].items()
                     if k != "login_ms"} for s in stages]

        self.assertEqual(_states(stages_a), _states(stages_b))


class SauceStressAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def _factory(self, page: FakeSaucePage):
        def _make(playwright: Any) -> Any:
            return FakeSauceBrowser(), FakeSauceContext(), page

        return _make

    def test_agent_remove_flow_all_t_checks_pass(self) -> None:
        result = run_saucedemo_order(
            "standard_user", "secret_sauce",
            ["sauce-labs-backpack", "sauce-labs-bike-light"], "az",
            "Ada", "Lovelace", "12345",
            trace_dir=self.tmp,
            browser_factory=self._factory(FakeSaucePage()),
            remove_slug="sauce-labs-bike-light",
            flow_label="sauce-stress")
        self.assertTrue(result["success"])
        stages = adapter.read_stages_file(
            str(self.tmp / f"{result['run_id']}.stages.json"))
        self.assertEqual([s["stage"] for s in stages],
                         ["login", "inventory", "cart",
                          "cart_after_remove", "info", "info",
                          "overview", "complete"])
        self.assertNotIn("secret_sauce", json.dumps(stages))
        verdict = adapter.verify_stress_order(
            None, stages,
            {"username": "standard_user",
             "added": ["Sauce Labs Backpack", "Sauce Labs Bike Light"],
             "remaining": ["Sauce Labs Backpack"],
             "sort": "az"})
        self.assertEqual([c["check_id"] for c in verdict["checks"]],
                         ["T1", "T2", "T3", "T4", "T5", "T6"])
        self.assertTrue(all(c["satisfied"] for c in verdict["checks"]))

    def test_agent_remove_absent_slug_is_skipped(self) -> None:
        result = run_saucedemo_order(
            "standard_user", "secret_sauce",
            ["sauce-labs-backpack"], "none",
            "Ada", "Lovelace", "12345",
            trace_dir=self.tmp,
            browser_factory=self._factory(FakeSaucePage()),
            remove_slug="sauce-labs-bike-light")
        self.assertTrue(result["success"])
        stages = adapter.read_stages_file(
            str(self.tmp / f"{result['run_id']}.stages.json"))
        self.assertNotIn("cart_after_remove",
                         [s["stage"] for s in stages])


class SauceAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def _factory(self, page: FakeSaucePage):
        def _make(playwright: Any) -> Any:
            return FakeSauceBrowser(), FakeSauceContext(), page

        return _make

    def test_agent_completes_order_and_hides_password(self) -> None:
        result = run_saucedemo_order(
            "standard_user", "secret_sauce",
            ["sauce-labs-backpack", "sauce-labs-bike-light"], "az",
            "Ada", "Lovelace", "12345",
            trace_dir=self.tmp,
            browser_factory=self._factory(FakeSaucePage()))
        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "succeeded")
        assert result["trace_path"] is not None
        trace_text = Path(result["trace_path"]).read_text()
        self.assertNotIn("secret_sauce", trace_text)
        stages = adapter.read_stages_file(
            str(self.tmp / f"{result['run_id']}.stages.json"))
        self.assertEqual([s["stage"] for s in stages],
                         ["login", "inventory", "cart", "info", "info",
                          "overview", "complete"])
        self.assertNotIn("secret_sauce", json.dumps(stages))
        verdict = adapter.verify_sauce_order(
            None, stages,
            {"username": "standard_user",
             "items": ["Sauce Labs Backpack", "Sauce Labs Bike Light"],
             "sort": "az"})
        self.assertTrue(all(c["satisfied"] for c in verdict["checks"]))

    def test_agent_invalid_login_fails(self) -> None:
        result = run_saucedemo_order(
            "locked_out_user", "secret_sauce", ["sauce-labs-backpack"],
            "none", "Ada", "Lovelace", "12345",
            trace_dir=self.tmp,
            browser_factory=self._factory(
                FakeSaucePage(login_ok=False)))
        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "failed")
        stages = adapter.read_stages_file(
            str(self.tmp / f"{result['run_id']}.stages.json"))
        login = adapter.stage_states(stages).get("login", {})
        self.assertIsNot(True, login.get("logged_in"))

    def test_agent_empty_cart_refuses_checkout(self) -> None:
        result = run_saucedemo_order(
            "standard_user", "secret_sauce", [], "none",
            "Ada", "Lovelace", "12345",
            trace_dir=self.tmp,
            browser_factory=self._factory(FakeSaucePage()))
        self.assertFalse(result["success"])
        assert result["error"] is not None
        self.assertIn("empty cart", result["error"])


class SaucePolicyTests(unittest.TestCase):
    def _policy(self) -> ActionPolicy:
        return ActionPolicy(
            permitted_urls=adapter.SAUCE_URLS,
            permitted_fill_targets=adapter.SAUCE_FILL_TARGETS,
            permitted_click_targets=adapter.SAUCE_CLICK_TARGETS,
            permitted_select_targets=adapter.SAUCE_SELECT_TARGETS,
        )

    def test_sauce_controls_are_allowed(self) -> None:
        policy = self._policy()
        decision, _ = policy.judge(
            "navigate", {"url": adapter.LOGIN_URL})
        self.assertEqual(decision, ALLOWED)
        decision, _ = policy.judge(
            "fill", {"by": "css", "selector": adapter.SEL_USERNAME,
                     "value_length": 13})
        self.assertEqual(decision, ALLOWED)
        decision, _ = policy.judge(
            "click", {"by": "css",
                      "selector": adapter.add_to_cart_selector(
                          "sauce-labs-backpack")})
        self.assertEqual(decision, ALLOWED)
        decision, _ = policy.judge(
            "select", {"by": "css", "selector": adapter.SEL_SORT,
                       "value": "az"})
        self.assertEqual(decision, ALLOWED)

    def test_off_policy_actions_are_denied(self) -> None:
        policy = self._policy()
        decision, _ = policy.judge(
            "navigate", {"url": "https://example.com/"})
        self.assertEqual(decision, DENIED)
        decision, _ = policy.judge(
            "select", {"by": "css", "selector": "#other",
                       "value": "az"})
        self.assertEqual(decision, DENIED)
        decision, _ = policy.judge("select", {"by": "derived"})
        self.assertEqual(decision, UNKNOWN)


if __name__ == "__main__":
    unittest.main()
