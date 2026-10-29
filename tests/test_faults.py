"""Tests for fault-injection URL builder and the demo app's HTML contract.

These tests deliberately use stdlib ``unittest`` so the Phase 1
fault-injection feature can be verified before ``playwright`` is
installed. They cover:

1. ``chimera.agent.get_demo_url_with_faults`` — pure-Python URL builder.
2. ``demo_app/index.html`` — string-level contract: the page contains
   the IDs, query-param names, and reset behaviour the agent relies on.

Browser-level scenarios (e.g. "with ``?slow=2000`` the Create button
stays disabled for ~2s") require Playwright. They are described in the
module docstring of ``tests/test_agent.py`` and are run only when
``playwright`` + ``pytest`` are installed.

Run with::

    python -m unittest tests.test_faults -v
"""

import re
import unittest
from pathlib import Path

from chimera.agent import (
    get_demo_url,
    get_demo_url_with_faults,
)


DEMO_HTML = Path(__file__).resolve().parent.parent / "demo_app" / "index.html"


class FaultUrlBuilderTests(unittest.TestCase):
    def test_default_url_matches_get_demo_url(self) -> None:
        # No faults: must produce the same URL the existing tests rely on.
        self.assertEqual(get_demo_url_with_faults(), get_demo_url())

    def test_default_explicit_kwargs_match_get_demo_url(self) -> None:
        self.assertEqual(
            get_demo_url_with_faults(slow_ms=0, disabled=False),
            get_demo_url(),
        )

    def test_slow_param_appended(self) -> None:
        url = get_demo_url_with_faults(slow_ms=2000)
        self.assertIn("slow=2000", url)
        self.assertTrue(url.startswith(get_demo_url() + "?"))

    def test_disabled_param_appended(self) -> None:
        url = get_demo_url_with_faults(disabled=True)
        self.assertIn("disabled=1", url)
        self.assertTrue(url.startswith(get_demo_url() + "?"))

    def test_both_params_combined(self) -> None:
        url = get_demo_url_with_faults(slow_ms=500, disabled=True)
        self.assertIn("slow=500", url)
        self.assertIn("disabled=1", url)
        # Both must be present.
        self.assertRegex(url, r"[?&](slow|disabled)=")
        self.assertRegex(url, r"[?&](slow|disabled)=.*[?&](slow|disabled)=")

    def test_zero_slow_is_omitted(self) -> None:
        url = get_demo_url_with_faults(slow_ms=0, disabled=True)
        self.assertNotIn("slow=", url)
        self.assertIn("disabled=1", url)

    def test_negative_slow_is_omitted(self) -> None:
        self.assertEqual(get_demo_url_with_faults(slow_ms=-10), get_demo_url())

    def test_only_slow_no_disabled(self) -> None:
        url = get_demo_url_with_faults(slow_ms=100, disabled=False)
        self.assertIn("slow=100", url)
        self.assertNotIn("disabled=", url)


class DemoHtmlContractTests(unittest.TestCase):
    """Static checks that the demo HTML exposes the fault-injection
    contract. These do NOT execute JavaScript; they verify the page is
    wired so a Playwright integration test (run when playwright is
    installed) can drive it deterministically.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.html = DEMO_HTML.read_text(encoding="utf-8")

    def test_fault_panel_present(self) -> None:
        self.assertIn('id="fault-panel"', self.html)
        self.assertIn('id="fault-slow"', self.html)
        self.assertIn('id="fault-disabled"', self.html)
        self.assertIn('id="apply-faults-btn"', self.html)

    def test_reset_button_present(self) -> None:
        self.assertIn('id="reset-btn"', self.html)

    def test_url_query_params_read(self) -> None:
        # The script must read the slow and disabled query params.
        self.assertIn("getParam", self.html)
        self.assertRegex(self.html, r"getParam\(\s*['\"]slow['\"]\s*\)")
        self.assertRegex(self.html, r"getParam\(\s*['\"]disabled['\"]\s*\)")

    def test_disabled_attr_enforced_in_submit(self) -> None:
        # The submit handler must refuse when the button is disabled,
        # even if the form is otherwise valid.
        self.assertRegex(
            self.html,
            r"getElementById\(\s*['\"]create-btn['\"]\s*\)\.disabled",
        )

    def test_reset_clears_projects(self) -> None:
        # The reset function must clear the project list and confirmation.
        self.assertIn("project-list", self.html)
        self.assertIn('innerHTML = ""', self.html)
        self.assertIn("confirmation", self.html)
        self.assertIn('classList.add("hidden")', self.html)

    def test_reset_strips_query_string(self) -> None:
        # After reset, the URL should no longer carry fault params.
        self.assertIn("history.replaceState", self.html)
        self.assertIn("window.location.pathname", self.html)

    def test_existing_aria_labels_preserved(self) -> None:
        """Sanity: the existing form/button contract used by the agent is
        untouched. Regression guard for the no-fault path."""
        self.assertIn('aria-label="Project Name"', self.html)
        self.assertIn(">Create Project<", self.html)
        self.assertIn('id="project-list"', self.html)
        self.assertIn('id="confirmation"', self.html)

    def test_slow_load_is_transient(self) -> None:
        """Intended slow-load behavior: the form is disabled for ``slow`` ms
        then re-enabled. Because Playwright auto-waits for enabled state, a
        ``create_project_with_faults(slow_ms=2000)`` run is expected to
        SUCCEED after the delay, not fail. The re-enable MUST honor
        ``activeFaults.disabled`` so that ``?disabled=1`` is sticky.
        """
        # The re-enable after setTimeout must consult activeFaults.disabled,
        # not unconditionally set the attribute to false. This is the only
        # way the "disabled is sticky after slow delay" semantic holds.
        self.assertIn("createBtn.disabled = activeFaults.disabled", self.html)
        self.assertIn("nameInput.disabled = activeFaults.disabled", self.html)
        # And the script must NEVER unconditionally re-enable the button:
        # the only way the disabled state clears is via Reset.
        self.assertNotIn("createBtn.disabled = false", self.html)
        self.assertNotIn("nameInput.disabled = false", self.html)
        # setTimeout is the sole mechanism that re-enables after a delay.
        self.assertIn("setTimeout", self.html)

    def test_persistent_disabled_has_no_self_clear(self) -> None:
        """Intended persistent-disabled behavior: ``?disabled=1`` with no
        ``slow`` value must yield a *persistent* disabled state that the
        agent cannot succeed through. The bound on the failure is the
        agent's per-action timeout (ACTION_TIMEOUT_MS) plus the FILL
        wrapper's BlindRetryRefusedError.

        The contract here is: there is no path in the script that sets
        ``createBtn.disabled`` to a falsy value without honouring
        ``activeFaults.disabled``. The only mutation sources for the
        attribute are the three lines already verified above.
        """
        # The else-branch (no slow) must use the sticky disabled flag.
        # It appears at least twice in the script (slow re-enable and the
        # no-slow branch), so we count to make sure both paths use it.
        occurrences = self.html.count("createBtn.disabled = activeFaults.disabled")
        self.assertGreaterEqual(occurrences, 2)
        # And the input is gated by the same flag in both paths.
        occurrences_input = self.html.count(
            "nameInput.disabled = activeFaults.disabled"
        )
        self.assertGreaterEqual(occurrences_input, 2)


if __name__ == "__main__":
    unittest.main()
