"""Safety primitives for the browser agent.

Provides:

- ``ActionType`` and ``ALLOWED_ACTIONS``: an allowlist of permitted browser
  operations (NFR-016).
- ``RetryPolicy``: bounded retry configuration (FR-022, FR-027).
- ``execute_with_retry``: runs an action under the allowlist with bounded
  retries that refuse to repeat blindly (FR-028 — the caller must report
  whether the intended effect already occurred before a retry is granted).
- ``CancellationToken``: cooperative cancellation flag (FR-021). A caller
  in another thread (or a timer) sets the token; the agent observes it
  at safe execution boundaries and raises :class:`RunCancelledError`.

This module is pure-Python and has no third-party dependencies so it can be
unit-tested with the standard library alone.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional


class ActionType(str, Enum):
    """The closed set of browser operations Chimera is permitted to perform."""

    NAVIGATE = "navigate"
    FILL = "fill"
    CLICK = "click"
    WAIT = "wait"
    OBSERVE = "observe"


# Closed allowlist. Any action not present here MUST be rejected before it
# reaches Playwright. This satisfies NFR-016.
ALLOWED_ACTIONS: frozenset[str] = frozenset(a.value for a in ActionType)


class ActionNotAllowedError(PermissionError):
    """Raised when an action type is not on the allowlist (NFR-016)."""


class RetryBudgetExhaustedError(RuntimeError):
    """Raised when the bounded retry budget is exhausted (FR-027)."""


class BlindRetryRefusedError(RuntimeError):
    """Raised when a retry is requested but the caller cannot show that the
    intended effect has not already occurred (FR-028)."""


class RunCancelledError(RuntimeError):
    """Raised when a run is cancelled by a :class:`CancellationToken`.

    Distinct from :class:`RetryBudgetExhaustedError` and ordinary action
    errors so the trace and the caller can classify the outcome
    unambiguously (FR-021).
    """


class CancellationToken:
    """Cooperative cancellation flag for an in-flight run (FR-021).

    A single writer (typically a timer or a sibling thread) calls
    :meth:`request` to ask for cancellation. The agent's own thread calls
    :meth:`is_cancelled` (or :meth:`check`) at safe execution boundaries
    and aborts the run by raising :class:`RunCancelledError`.

    Design notes:

    - The token is a thin wrapper around a flag plus a
      :class:`threading.Event`. It is safe to call :meth:`request` from
      any thread; the agent only reads it from its own thread, so there
      is no cross-thread mutation of Playwright state.
    - Cancellation is **cooperative**: it does NOT interrupt an
      in-flight Playwright action. The agent observes the flag inside
      ``is_effect_achieved`` and at the top of each retry iteration, so
      the worst-case delay between ``request()`` and stop is bounded by
      the action's own timeout (FR-022's ``max_total_seconds``).
    """

    def __init__(self) -> None:
        self._event = threading.Event()
        self._reason: Optional[str] = None

    def request(self, reason: Optional[str] = None) -> None:
        """Mark the run as cancelled. Idempotent.

        The first reason wins; subsequent calls update nothing. This
        keeps the reason a stable "who asked first" signal even if
        multiple writers race.
        """
        if self._event.is_set():
            return
        self._reason = reason
        self._event.set()

    def is_cancelled(self) -> bool:
        """Return ``True`` if :meth:`request` has been called."""
        return self._event.is_set()

    def check(self) -> None:
        """Raise :class:`RunCancelledError` if cancellation has been requested."""
        if self._event.is_set():
            raise RunCancelledError(self._reason or "Run cancelled")

    @property
    def reason(self) -> Optional[str]:
        return self._reason


@dataclass(frozen=True)
class RetryPolicy:
    """Bounded retry configuration.

    Attributes
    ----------
    max_attempts:
        Total attempts including the first try. Must be >= 1.
    base_delay_seconds:
        Delay before the first retry. Doubles each subsequent retry.
    max_delay_seconds:
        Upper bound on the per-retry delay.
    max_total_seconds:
        Overall wall-clock cap. Once exceeded, further attempts are
        refused even if attempts remain (FR-022).
    """

    max_attempts: int = 3
    base_delay_seconds: float = 0.1
    max_delay_seconds: float = 1.0
    max_total_seconds: float = 5.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.base_delay_seconds < 0:
            raise ValueError("base_delay_seconds must be >= 0")
        if self.max_delay_seconds < self.base_delay_seconds:
            raise ValueError("max_delay_seconds must be >= base_delay_seconds")
        if self.max_total_seconds <= 0:
            raise ValueError("max_total_seconds must be > 0")


def _sleep(duration: float) -> None:
    if duration > 0:
        time.sleep(duration)


def execute_with_retry(
    action_type: str,
    action: Callable[[], Any],
    *,
    policy: Optional[RetryPolicy] = None,
    is_effect_achieved: Optional[Callable[[], bool]] = None,
    cancellation_token: Optional[CancellationToken] = None,
) -> Any:
    """Run ``action`` under the allowlist with bounded, non-blind retries.

    Parameters
    ----------
    action_type:
        Must be a member of :data:`ALLOWED_ACTIONS`. Anything else raises
        :class:`ActionNotAllowedError` (NFR-016).
    action:
        Zero-argument callable performing the browser operation. Its return
        value is forwarded on success.
    policy:
        Retry policy. Defaults to a conservative :class:`RetryPolicy`.
    is_effect_achieved:
        Optional zero-argument callable that, when provided, is consulted
        before every retry. If it returns ``True``, the retry is skipped and
        the previous return value (if any) is returned. This is the hook used
        to satisfy FR-028 (no blind retries) — the caller is responsible for
        actually checking state, not just the absence of an exception.
    cancellation_token:
        Optional :class:`CancellationToken`. When supplied, the token is
        checked at the top of every retry iteration and inside
        ``is_effect_achieved``. If cancellation has been requested,
        :class:`RunCancelledError` is raised promptly (FR-021).
        Cancellation is cooperative: an action that is already running when
        ``request()`` is called will run to completion (or its own
        timeout) before the cancel is observed. The token does NOT
        interrupt a synchronous Playwright call from another thread.
    """

    if action_type not in ALLOWED_ACTIONS:
        raise ActionNotAllowedError(
            f"Action {action_type!r} is not on the allowlist. "
            f"Allowed: {sorted(ALLOWED_ACTIONS)}"
        )

    cfg = policy or RetryPolicy()
    started = time.monotonic()
    last_error: Optional[BaseException] = None
    last_value: Any = None

    for attempt in range(1, cfg.max_attempts + 1):
        # FR-021: check cancellation at the safe boundary before each
        # attempt. The first iteration catches cancel-before-start;
        # subsequent iterations catch cancel-during-retry-sleep.
        if cancellation_token is not None:
            cancellation_token.check()

        try:
            value = action()
            last_value = value
            return value
        except Exception as exc:  # noqa: BLE001 — we re-raise below after budget
            last_error = exc

        # Do not retry past the wall-clock cap (FR-022).
        if time.monotonic() - started >= cfg.max_total_seconds:
            break

        if attempt >= cfg.max_attempts:
            break

        # FR-028: never retry blindly. If the caller can tell us whether the
        # effect already happened, trust that signal.
        if is_effect_achieved is not None:
            try:
                # FR-021: also check cancellation inside the state check
                # so a long click that is waiting on a slow effect bails
                # out promptly when cancel is requested.
                if cancellation_token is not None:
                    cancellation_token.check()
                if is_effect_achieved():
                    return last_value
            except RunCancelledError:
                # Propagate cancellation as-is so the caller can
                # distinguish it from a state-check failure.
                raise
            except Exception as exc:
                # The state check is broken: we cannot know whether the
                # intended effect already occurred, so per FR-028 we refuse
                # to retry. Surface the state-check error as the proximate
                # cause and the action error in the message so the operator
                # can diagnose both signals without burning the retry budget
                # on a permanently broken check.
                msg = f"Action {action_type!r} aborted: state check failed ({exc})"
                if last_error is not None:
                    msg += f"; action also failing: {last_error}"
                raise RetryBudgetExhaustedError(msg) from exc
        else:
            raise BlindRetryRefusedError(
                "Retry requested without an is_effect_achieved() check "
                "(FR-028: never retry blindly)."
            ) from last_error

        delay = min(
            cfg.max_delay_seconds,
            cfg.base_delay_seconds * (2 ** (attempt - 1)),
        )
        # Sleep is also a safe boundary for cancellation.
        if cancellation_token is not None:
            cancellation_token.check()
        _sleep(delay)

    if last_error is not None:
        raise RetryBudgetExhaustedError(
            f"Action {action_type!r} failed after {cfg.max_attempts} attempt(s)"
        ) from last_error

    raise RetryBudgetExhaustedError(
        f"Action {action_type!r} exhausted retry budget without a result"
    )


__all__ = [
    "ActionType",
    "ALLOWED_ACTIONS",
    "ActionNotAllowedError",
    "RetryBudgetExhaustedError",
    "BlindRetryRefusedError",
    "RunCancelledError",
    "CancellationToken",
    "RetryPolicy",
    "execute_with_retry",
]
