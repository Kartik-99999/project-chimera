"""Tests for the Chimera agent's browser automation."""

from chimera.agent import (create_project, run_github_profile,
                           run_github_search)
from workbench.executor import _ShotOnClose


def test_create_project_succeeds():
    """Verify that creating a project returns success and no errors."""
    result = create_project("Test Project Alpha")
    assert result["success"] is True, f"Expected success but got error: {result['error']}"
    assert result["project_name"] == "Test Project Alpha"
    assert result["error"] is None


def test_create_project_with_special_characters():
    """Verify the agent handles project names with special characters."""
    result = create_project("Project & Co. (2026)")
    assert result["success"] is True, f"Expected success but got error: {result['error']}"
    assert result["project_name"] == "Project & Co. (2026)"


def test_teardown_closes_on_owning_thread_with_final_screenshot(tmp_path):
    """Teardown must close on the creating thread and capture the shot.

    Regression: _close_browser used to run context.close() on a helper
    thread, so Playwright raised "Cannot switch to a different thread"
    on every real run; the _ShotOnClose final screenshot never fired
    (screenshot_path NULL) and a .teardown.json sidecar was written.
    This replicates the executor's real-Chromium path end to end.
    """
    shot_path = tmp_path / "shots" / "final.png"
    holder = {}

    def factory(playwright):
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        raw_page = context.new_page()
        holder["shot"] = _ShotOnClose(context, raw_page, shot_path)
        return browser, holder["shot"], raw_page

    result = create_project("Teardown Regression", trace_dir=tmp_path,
                            browser_factory=factory)
    assert result["success"] is True, f"run failed: {result['error']}"
    assert holder["shot"].taken is True, (
        f"final screenshot not taken: {holder['shot'].error}")
    assert shot_path.exists()
    assert list(tmp_path.glob("*.teardown.json")) == []


def test_github_drivers_navigate_on_domcontentloaded(tmp_path):
    """GitHub navigation must not wait for the full `load` event.

    Regression: page.goto() with the default `load` wait hangs on
    GitHub's avatar CDN and times out with the content already
    present (false verified-failure). domcontentloaded plus the
    stage readers' auto-waiting locators is sufficient: the content
    is server-rendered.
    """
    from adapters import github as github_adapter
    from adapters import github_search as gsearch_adapter

    gotos = []

    class _First:
        def __init__(self, text):
            self._text = text

        @property
        def first(self):
            return self

        def text_content(self, timeout=None):
            return self._text

    class _Items:
        def __init__(self, texts):
            self._texts = texts

        @property
        def first(self):
            return self

        def count(self):
            return len(self._texts)

        def nth(self, i):
            return _First(self._texts[i])

    class _Page:
        def __init__(self):
            self.url = "https://github.com/"

        def goto(self, url, **kwargs):
            gotos.append(kwargs)
            self.url = url

        def locator(self, selector):
            if selector == github_adapter.SEL_NICKNAME:
                return _First("torvalds")
            if selector == github_adapter.SEL_NAME:
                return _First("Linus Torvalds")
            if selector == gsearch_adapter.SEL_LIST:
                return _Items(["x"])
            return _Items(["microsoft/playwright"])

    class _Ctx:
        def close(self):
            pass

    class _Browser:
        def close(self):
            pass

    def factory(pw):
        return _Browser(), _Ctx(), _Page()

    profile = run_github_profile("torvalds", trace_dir=tmp_path,
                                 browser_factory=factory)
    assert profile["success"] is True, profile["error"]
    search = run_github_search("playwright", trace_dir=tmp_path,
                               browser_factory=factory)
    assert search["success"] is True, search["error"]
    assert gotos and all(
        k.get("wait_until") == "domcontentloaded" for k in gotos), gotos
