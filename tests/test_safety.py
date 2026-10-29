"""Stdlib-only tests for :mod:`chimera.safety`.

These tests deliberately use ``unittest`` (not pytest) so the foundation
milestone can be verified before the optional playwright/pytest
dependencies are installed. Run with::

    python -m unittest tests.test_safety -v
"""

import unittest

from chimera.safety import (
    ActionNotAllowedError,
    ActionType,
    ALLOWED_ACTIONS,
    BlindRetryRefusedError,
    RetryBudgetExhaustedError,
    RetryPolicy,
    execute_with_retry,
)


class AllowlistTests(unittest.TestCase):
    def test_all_action_types_are_allowlisted(self) -> None:
        for action in ActionType:
            self.assertIn(action.value, ALLOWED_ACTIONS)

    def test_unknown_action_is_rejected(self) -> None:
        with self.assertRaises(ActionNotAllowedError):
            execute_with_retry("drop_database", lambda: None)

    def test_empty_string_is_rejected(self) -> None:
        with self.assertRaises(ActionNotAllowedError):
            execute_with_retry("", lambda: None)


class RetryPolicyValidationTests(unittest.TestCase):
    def test_max_attempts_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            RetryPolicy(max_attempts=0)

    def test_max_delay_must_be_at_least_base_delay(self) -> None:
        with self.assertRaises(ValueError):
            RetryPolicy(base_delay_seconds=1.0, max_delay_seconds=0.1)

    def test_negative_base_delay_rejected(self) -> None:
        with self.assertRaises(ValueError):
            RetryPolicy(base_delay_seconds=-0.1)


class ExecuteWithRetryTests(unittest.TestCase):
    def test_success_first_try_does_not_retry(self) -> None:
        calls = []

        def action() -> str:
            calls.append(1)
            return "ok"

        result = execute_with_retry(ActionType.OBSERVE.value, action)
        self.assertEqual(result, "ok")
        self.assertEqual(len(calls), 1)

    def test_retries_until_success_within_budget(self) -> None:
        calls = {"n": 0}

        def flaky() -> str:
            calls["n"] += 1
            if calls["n"] < 3:
                raise RuntimeError("transient")
            return "done"

        result = execute_with_retry(
            ActionType.CLICK.value,
            flaky,
            policy=RetryPolicy(
                max_attempts=5, base_delay_seconds=0.0, max_delay_seconds=0.0
            ),
            is_effect_achieved=lambda: False,
        )
        self.assertEqual(result, "done")
        self.assertEqual(calls["n"], 3)

    def test_bounded_retry_raises_after_budget(self) -> None:
        def always_fail() -> None:
            raise RuntimeError("boom")

        with self.assertRaises(RetryBudgetExhaustedError):
            execute_with_retry(
                ActionType.FILL.value,
                always_fail,
                policy=RetryPolicy(
                    max_attempts=2,
                    base_delay_seconds=0.0,
                    max_delay_seconds=0.0,
                ),
                is_effect_achieved=lambda: False,
            )

    def test_no_blind_retry_without_state_check(self) -> None:
        """FR-028: a failing action must not be retried unless the caller can
        prove the effect has not already occurred."""

        def failing() -> None:
            raise RuntimeError("first try failed")

        with self.assertRaises(BlindRetryRefusedError) as ctx:
            # max_attempts > 1 with no is_effect_achieved => blind retry refused
            execute_with_retry(
                ActionType.CLICK.value,
                failing,
                policy=RetryPolicy(
                    max_attempts=3,
                    base_delay_seconds=0.0,
                    max_delay_seconds=0.0,
                ),
            )
        # The original failure must be preserved as the cause so the caller
        # still sees the real reason the action failed.
        self.assertIsInstance(ctx.exception.__cause__, RuntimeError)

    def test_state_check_short_circuits_retry(self) -> None:
        """If the state check says the effect is already achieved, the retry
        is skipped even if the action raised."""

        def failing() -> str:
            raise RuntimeError("but the click actually worked")

        def effect_already_achieved() -> bool:
            return True

        result = execute_with_retry(
            ActionType.CLICK.value,
            failing,
            policy=RetryPolicy(
                max_attempts=3,
                base_delay_seconds=0.0,
                max_delay_seconds=0.0,
            ),
            is_effect_achieved=effect_already_achieved,
        )
        self.assertIsNone(result)

    def test_state_check_allowing_retry_proceeds(self) -> None:
        calls = {"n": 0}

        def flaky() -> str:
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("transient")
            return "ok"

        def not_yet() -> bool:
            return False

        result = execute_with_retry(
            ActionType.CLICK.value,
            flaky,
            policy=RetryPolicy(
                max_attempts=3,
                base_delay_seconds=0.0,
                max_delay_seconds=0.0,
            ),
            is_effect_achieved=not_yet,
        )
        self.assertEqual(result, "ok")
        self.assertEqual(calls["n"], 2)

    def test_wall_clock_cap_halts_retries(self) -> None:
        import time as _time

        calls = {"n": 0}

        def slow_failing() -> None:
            calls["n"] += 1
            # Consume a measurable amount of wall-clock per attempt so the
            # cap can fire before max_attempts is reached.
            _time.sleep(0.02)
            raise RuntimeError("nope")

        def not_yet() -> bool:
            return False

        with self.assertRaises(RetryBudgetExhaustedError):
            execute_with_retry(
                ActionType.CLICK.value,
                slow_failing,
                policy=RetryPolicy(
                    max_attempts=20,
                    base_delay_seconds=0.0,
                    max_delay_seconds=0.0,
                    max_total_seconds=0.05,
                ),
                is_effect_achieved=not_yet,
            )
        # Should not have run all 20 attempts given the tiny wall-clock cap.
        self.assertLess(calls["n"], 20)

    def test_state_check_exception_is_surfaced_in_final_error(self) -> None:
        """A state check that itself errors must not be silently swallowed:
        the eventual RetryBudgetExhaustedError must mention both the broken
        state check and the original action failure."""

        def failing() -> None:
            raise RuntimeError("action boom")

        def broken_state_check() -> bool:
            raise LookupError("locator not found")

        with self.assertRaises(RetryBudgetExhaustedError) as ctx:
            execute_with_retry(
                ActionType.CLICK.value,
                failing,
                policy=RetryPolicy(
                    max_attempts=2,
                    base_delay_seconds=0.0,
                    max_delay_seconds=0.0,
                ),
                is_effect_achieved=broken_state_check,
            )
        self.assertIn("state check failed", str(ctx.exception))
        self.assertIn("locator not found", str(ctx.exception))
        self.assertIn("action boom", str(ctx.exception))
        # Proximate cause is the broken state check (we stopped because of it).
        self.assertIsInstance(ctx.exception.__cause__, LookupError)

    def test_broken_state_check_does_not_retry(self) -> None:
        """FR-028: a broken effect check must NOT cause retries. We cannot
        know if the effect already occurred, so we must stop on the first
        attempt and not burn the remaining budget."""

        calls = {"n": 0}

        def failing() -> None:
            calls["n"] += 1
            raise RuntimeError("action boom")

        def broken_state_check() -> bool:
            raise LookupError("locator not found")

        with self.assertRaises(RetryBudgetExhaustedError):
            execute_with_retry(
                ActionType.CLICK.value,
                failing,
                policy=RetryPolicy(
                    max_attempts=5,
                    base_delay_seconds=0.0,
                    max_delay_seconds=0.0,
                ),
                is_effect_achieved=broken_state_check,
            )
        # Action ran exactly once — the broken state check stopped the loop.
        self.assertEqual(calls["n"], 1)


class CancellationTokenTests(unittest.TestCase):
    """FR-021: cooperative cancellation flag."""

    def test_new_token_is_not_cancelled(self) -> None:
        from chimera.safety import CancellationToken

        token = CancellationToken()
        self.assertFalse(token.is_cancelled())
        # check() must be a no-op when not cancelled.
        token.check()

    def test_request_marks_cancelled(self) -> None:
        from chimera.safety import CancellationToken

        token = CancellationToken()
        token.request("user pressed stop")
        self.assertTrue(token.is_cancelled())
        self.assertEqual(token.reason, "user pressed stop")

    def test_request_is_idempotent(self) -> None:
        from chimera.safety import CancellationToken

        token = CancellationToken()
        token.request("first")
        token.request("second")
        # The first reason wins; later requests are ignored.
        self.assertEqual(token.reason, "first")

    def test_check_raises_run_cancelled_error(self) -> None:
        from chimera.safety import CancellationToken, RunCancelledError

        token = CancellationToken()
        token.request("user pressed stop")
        with self.assertRaises(RunCancelledError) as ctx:
            token.check()
        self.assertIn("user pressed stop", str(ctx.exception))

    def test_check_raises_with_default_message_when_no_reason(self) -> None:
        from chimera.safety import CancellationToken, RunCancelledError

        token = CancellationToken()
        token.request()
        with self.assertRaises(RunCancelledError) as ctx:
            token.check()
        self.assertEqual(str(ctx.exception), "Run cancelled")


class ExecuteWithRetryCancellationTests(unittest.TestCase):
    """FR-021: ``execute_with_retry`` honours the cancellation token at
    safe boundaries and inside the effect check."""

    def _policy(self) -> RetryPolicy:
        return RetryPolicy(
            max_attempts=5,
            base_delay_seconds=0.0,
            max_delay_seconds=0.0,
            max_total_seconds=5.0,
        )

    def test_cancel_before_start_aborts_without_calling_action(self) -> None:
        from chimera.safety import (
            CancellationToken,
            RunCancelledError,
        )

        token = CancellationToken()
        token.request("before-start")
        calls = {"n": 0}

        def action() -> None:
            calls["n"] += 1

        with self.assertRaises(RunCancelledError):
            execute_with_retry(
                ActionType.NAVIGATE.value,
                action,
                policy=self._policy(),
                cancellation_token=token,
            )
        # The action must NOT have been called at all.
        self.assertEqual(calls["n"], 0)

    def test_cancel_during_retry_aborts_before_next_attempt(self) -> None:
        from chimera.safety import (
            CancellationToken,
            RunCancelledError,
        )

        token = CancellationToken()
        calls = {"n": 0}

        def always_fails() -> None:
            calls["n"] += 1
            raise RuntimeError("browser down")

        def effect_achieved() -> bool:
            # The second time the retry loop asks us, cancel the run.
            if calls["n"] >= 2:
                token.request("during-retry")
            return False  # never short-circuit the retry

        with self.assertRaises(RunCancelledError):
            execute_with_retry(
                ActionType.CLICK.value,
                always_fails,
                policy=self._policy(),
                is_effect_achieved=effect_achieved,
                cancellation_token=token,
            )
        # The action ran at least once, but not for all 5 attempts.
        self.assertGreaterEqual(calls["n"], 1)
        self.assertLess(calls["n"], 5)

    def test_cancel_inside_effect_check_raises_promptly(self) -> None:
        from chimera.safety import (
            CancellationToken,
            RunCancelledError,
        )

        token = CancellationToken()

        def effect_achieved() -> bool:
            token.request("inside-effect")
            return False

        def always_fails() -> None:
            raise RuntimeError("boom")

        with self.assertRaises(RunCancelledError) as ctx:
            execute_with_retry(
                ActionType.CLICK.value,
                always_fails,
                policy=self._policy(),
                is_effect_achieved=effect_achieved,
                cancellation_token=token,
            )
        self.assertIn("inside-effect", str(ctx.exception))

    def test_no_token_means_no_cancellation_behavior_change(self) -> None:
        # Regression: callers that pass no token must see exactly the
        # previous behavior (no RunCancelledError ever raised).
        def always_fails() -> None:
            raise RuntimeError("boom")

        def effect_achieved() -> bool:
            return False

        with self.assertRaises(RetryBudgetExhaustedError):
            execute_with_retry(
                ActionType.CLICK.value,
                always_fails,
                policy=self._policy(),
                is_effect_achieved=effect_achieved,
            )

    def test_cancellation_is_distinct_from_budget_exhaustion(self) -> None:
        from chimera.safety import (
            CancellationToken,
            RunCancelledError,
        )

        token = CancellationToken()
        token.request()

        def ok() -> None:
            return None

        with self.assertRaises(RunCancelledError) as ctx:
            execute_with_retry(
                ActionType.NAVIGATE.value, ok, policy=self._policy(),
                cancellation_token=token,
            )
        # Must be RunCancelledError, NOT RetryBudgetExhaustedError.
        self.assertNotIsInstance(ctx.exception, RetryBudgetExhaustedError)


if __name__ == "__main__":
    unittest.main()
