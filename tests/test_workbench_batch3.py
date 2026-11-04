"""Tests for batch-3 read-only workflows (scripted fakes).

crates.io lookup, BBC Weather, GitHub search, and Steam price check
run end to end against the fakes in tests/fake_lookup.py with the
real Executor, so no test touches the live web.
"""

import time

import pytest

from adapters import crates as crates
from adapters import weather as weather
from adapters import github_search as gsearch
from adapters import steam as steam
from benchmarks.observer import ActionPolicy
from tests.fake_lookup import (
    FakeCratesPage,
    FakeGsearchPage,
    FakeSteamPage,
    FakeWeatherPage,
    _StubBrowser,
    _StubContext,
)
from workbench.executor import Executor, _run_spec
from workbench.store import Store
from workbench.workflows import (
    BBC_WEATHER,
    CRATES_LOOKUP,
    GITHUB_SEARCH,
    STEAM_PRICE,
    WorkflowValidationError,
    get_workflow,
    list_workflows,
)


def _fake_factory(page):
    def make(log, shot_path):
        from benchmarks.observer import RecordingPage
        from workbench.executor import _ShotOnClose

        def factory(pw):
            shot = _ShotOnClose(_StubContext(), page, shot_path)
            return _StubBrowser(), shot, RecordingPage(page, log)

        return factory

    return make


def _wait_terminal(store, exec_id, timeout=30.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        record = store.get_execution(exec_id)
        if record and record["status"] not in ("queued", "running"):
            return record
        time.sleep(0.05)
    raise AssertionError(f"{exec_id} never finished")


# ---------------------------------------------------------------------------
# crates.io lookup
# ---------------------------------------------------------------------------

def _crates_params(**overrides):
    base = {"crate": "serde"}
    base.update(overrides)
    return base


def test_registry_lists_crates_chimera_only():
    assert get_workflow("crates-lookup") is CRATES_LOOKUP
    assert CRATES_LOOKUP.origin == "external"
    assert CRATES_LOOKUP.drivers == ("chimera",)
    assert "crates-lookup" in [w.workflow_id for w in list_workflows()]


def test_crates_params_validate():
    cleaned = CRATES_LOOKUP.validate(_crates_params())
    assert cleaned["crate"] == "serde"
    with pytest.raises(WorkflowValidationError):
        CRATES_LOOKUP.validate(_crates_params(crate="  "))
    with pytest.raises(WorkflowValidationError):
        CRATES_LOOKUP.validate(_crates_params(crate="x" * 65))
    with pytest.raises(WorkflowValidationError):
        _run_spec("crates-lookup", _crates_params(crate="bad name!"))


def test_crates_baseline_rejected(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb")
        with pytest.raises(WorkflowValidationError):
            ex.submit("crates-lookup", "baseline-a", _crates_params())
    finally:
        store.close()


def test_crates_run_spec():
    spec = _run_spec("crates-lookup", _crates_params(crate="tokio"))
    assert spec["verify"] == "crates"
    assert spec["expected"] == {"crate": "tokio"}
    assert spec["url"] == crates.crate_url("tokio")
    assert isinstance(spec["policy"], ActionPolicy)


def test_crates_url_guard():
    assert crates.assert_approved_url("https://crates.io/")
    assert crates.assert_approved_url(crates.crate_url("serde"))
    for bad in ("https://evil.com/",
                "https://crates.io/crates/a/b",
                "http://crates.io/",
                "",
                None):
        with pytest.raises(crates.UnapprovedURLError):
            crates.assert_approved_url(bad)
    with pytest.raises(ValueError):
        crates.crate_url("a b")


def test_crates_policy_allows_crate_denies_deep():
    from workbench.executor import _crates_policy

    policy = _crates_policy()
    for url in (crates.HOME_URL, crates.crate_url("serde")):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "allowed", url
    for url in ("https://crates.io/crates/a/b",
                "https://evil.com/"):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "denied", url


def _crates_stages(**states):
    return [{"stage": name, "url": "https://crates.io/x",
             "captured_at": "t", "state": state}
            for name, state in states.items()]


def test_crates_verify_success():
    report = crates.verify_crates_lookup(
        {"url": "x"}, _crates_stages(
            crate={"name": "serde", "version": "1.2.3",
                   "summary": "x" * 50, "missing": False}),
        {"crate": "serde"})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("CR1", True), ("CR2", True)]


def test_crates_verify_failures():
    report = crates.verify_crates_lookup(
        {"url": "x"}, _crates_stages(
            crate={"name": "", "version": "", "summary": "",
                   "missing": True}),
        {"crate": "qqqzzz"})
    assert [c["satisfied"] for c in report["checks"]] == [False, False]
    report = crates.verify_crates_lookup(
        {"url": "x"}, _crates_stages(
            crate={"name": "serde", "version": "", "summary": "",
                   "missing": False}),
        {"crate": "serde"})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("CR1", True), ("CR2", False)]
    assert crates.verify_crates_lookup(
        None, [], {"crate": "x"})["status"] == "unavailable"


def test_crates_end_to_end_success(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(FakeCratesPage()))
        exec_id = ex.submit("crates-lookup", "chimera", _crates_params())
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "succeeded"
        assert record["verdict"] == "verified-success"
        assert [c["check_id"] for c in record["checks"]] == ["CR1", "CR2"]
        stages = crates.stages_for_trace(record["trace_path"])
        assert [s["stage"] for s in stages] == ["crate"]
    finally:
        store.close()


def test_crates_end_to_end_missing_crate(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(
                          FakeCratesPage(missing=True)))
        exec_id = ex.submit("crates-lookup", "chimera",
                            _crates_params(crate="qqqzzz"))
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "failed"
        assert record["verdict"] == "verified-failure"
        assert "no crates.io crate" in (record["error"] or "")
    finally:
        store.close()


# ---------------------------------------------------------------------------
# BBC Weather
# ---------------------------------------------------------------------------

def _weather_params(**overrides):
    base = {"city": "london"}
    base.update(overrides)
    return base


def test_registry_lists_weather_chimera_only():
    assert get_workflow("bbc-weather") is BBC_WEATHER
    assert BBC_WEATHER.origin == "external"
    assert BBC_WEATHER.drivers == ("chimera",)
    assert "bbc-weather" in [w.workflow_id for w in list_workflows()]


def test_weather_params_validate():
    cleaned = BBC_WEATHER.validate(_weather_params())
    assert cleaned["city"] == "london"
    assert BBC_WEATHER.validate(_weather_params(city="tokyo"))[
        "city"] == "tokyo"
    with pytest.raises(WorkflowValidationError):
        BBC_WEATHER.validate(_weather_params(city="berlin"))
    with pytest.raises(WorkflowValidationError):
        _run_spec("bbc-weather", _weather_params(city="berlin"))


def test_weather_baseline_rejected(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb")
        with pytest.raises(WorkflowValidationError):
            ex.submit("bbc-weather", "baseline-a", _weather_params())
    finally:
        store.close()


def test_weather_run_spec():
    spec = _run_spec("bbc-weather", _weather_params(city="tokyo"))
    assert spec["verify"] == "weather"
    assert spec["expected"] == {"city": "tokyo"}
    assert spec["url"] == weather.city_url("tokyo")
    assert isinstance(spec["policy"], ActionPolicy)


def test_weather_url_guard():
    assert weather.assert_approved_url("https://www.bbc.com/")
    assert weather.assert_approved_url(weather.city_url("london"))
    for bad in ("https://evil.com/",
                "https://www.bbc.com/weather/",
                "https://www.bbc.com/weather/abc",
                "https://www.bbc.com/news",
                "http://www.bbc.com/",
                "",
                None):
        with pytest.raises(weather.UnapprovedURLError):
            weather.assert_approved_url(bad)
    with pytest.raises(ValueError):
        weather.city_url("berlin")


def test_weather_policy_allows_city_denies_news():
    from workbench.executor import _weather_policy

    policy = _weather_policy()
    for url in (weather.HOME_URL, weather.city_url("london")):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "allowed", url
    for url in ("https://www.bbc.com/news",
                "https://www.bbc.com/weather/abc",
                "https://evil.com/"):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "denied", url


def _weather_stages(**states):
    return [{"stage": name, "url": "https://www.bbc.com/weather/2643743",
             "captured_at": "t", "state": state}
            for name, state in states.items()]


def test_weather_verify_success():
    report = weather.verify_bbc_weather(
        {"url": "x"}, _weather_stages(
            forecast={"url": "https://www.bbc.com/weather/2643743",
                      "heading": "London - Fake forecast", "count": 4,
                      "temps": ["12°", "11°"]}),
        {"city": "london"})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("BW1", True), ("BW2", True)]


def test_weather_verify_failures():
    report = weather.verify_bbc_weather(
        {"url": "x"}, _weather_stages(
            forecast={"url": "https://www.bbc.com/weather/2643743",
                      "heading": "Something else", "count": 4,
                      "temps": ["12°"]}),
        {"city": "london"})
    assert [c["satisfied"] for c in report["checks"]] == [False, False]
    report = weather.verify_bbc_weather(
        {"url": "x"}, _weather_stages(
            forecast={"url": "https://www.bbc.com/weather/2643743",
                      "heading": "London - Fake forecast", "count": 0,
                      "temps": []}),
        {"city": "london"})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("BW1", True), ("BW2", False)]
    assert weather.verify_bbc_weather(
        None, [], {"city": "london"})["status"] == "unavailable"


def test_weather_end_to_end_success(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(FakeWeatherPage()))
        exec_id = ex.submit("bbc-weather", "chimera", _weather_params())
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "succeeded"
        assert record["verdict"] == "verified-success"
        assert [c["check_id"] for c in record["checks"]] == ["BW1", "BW2"]
        stages = weather.stages_for_trace(record["trace_path"])
        assert [s["stage"] for s in stages] == ["forecast"]
        assert len(stages[0]["state"]["temps"]) == 4
    finally:
        store.close()


def test_weather_end_to_end_empty_forecast(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(
                          FakeWeatherPage(empty=True)))
        exec_id = ex.submit("bbc-weather", "chimera", _weather_params())
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "failed"
        assert record["verdict"] == "verified-failure"
        assert "recorded no temperatures" in (record["error"] or "")
    finally:
        store.close()


# ---------------------------------------------------------------------------
# GitHub search
# ---------------------------------------------------------------------------

def _gsearch_params(**overrides):
    base = {"query": "playwright"}
    base.update(overrides)
    return base


def test_registry_lists_gsearch_chimera_only():
    assert get_workflow("github-search") is GITHUB_SEARCH
    assert GITHUB_SEARCH.origin == "external"
    assert GITHUB_SEARCH.drivers == ("chimera",)
    assert "github-search" in [w.workflow_id for w in list_workflows()]


def test_gsearch_params_validate():
    cleaned = GITHUB_SEARCH.validate(_gsearch_params())
    assert cleaned["query"] == "playwright"
    with pytest.raises(WorkflowValidationError):
        GITHUB_SEARCH.validate(_gsearch_params(query="  "))
    with pytest.raises(WorkflowValidationError):
        GITHUB_SEARCH.validate(_gsearch_params(query="x" * 101))
    with pytest.raises(WorkflowValidationError):
        _run_spec("github-search", _gsearch_params(query="  "))


def test_gsearch_baseline_rejected(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb")
        with pytest.raises(WorkflowValidationError):
            ex.submit("github-search", "baseline-a", _gsearch_params())
    finally:
        store.close()


def test_gsearch_run_spec():
    spec = _run_spec("github-search", _gsearch_params(query="serde"))
    assert spec["verify"] == "gsearch"
    assert spec["expected"] == {"query": "serde"}
    assert spec["url"] == gsearch.search_url("serde")
    assert isinstance(spec["policy"], ActionPolicy)


def test_gsearch_url_guard():
    assert gsearch.assert_approved_url("https://github.com/")
    assert gsearch.assert_approved_url(gsearch.search_url("playwright"))
    for bad in ("https://evil.com/",
                "https://github.com/search",
                "https://github.com/search?q=",
                "https://github.com/torvalds",
                "http://github.com/",
                "",
                None):
        with pytest.raises(gsearch.UnapprovedURLError):
            gsearch.assert_approved_url(bad)
    with pytest.raises(ValueError):
        gsearch.search_url("  ")


def test_gsearch_policy_allows_search_denies_profile():
    from workbench.executor import _gsearch_policy

    policy = _gsearch_policy()
    for url in (gsearch.HOME_URL, gsearch.search_url("playwright")):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "allowed", url
    for url in ("https://github.com/torvalds",
                "https://evil.com/"):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "denied", url


def _gsearch_stages(**states):
    return [{"stage": name, "url": "https://github.com/search?q=x",
             "captured_at": "t", "state": state}
            for name, state in states.items()]


def test_gsearch_verify_success():
    report = gsearch.verify_github_search(
        {"url": "x"}, _gsearch_stages(
            search={"url": "https://github.com/search?q=playwright",
                    "served": True, "count": 3,
                    "titles": ["microsoft / playwright",
                               "fake-org / demo"]}),
        {"query": "playwright"})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("GS1", True), ("GS2", True)]


def test_gsearch_verify_failures():
    report = gsearch.verify_github_search(
        {"url": "x"}, _gsearch_stages(
            search={"url": "https://github.com/search?q=qqqzzz",
                    "served": True, "count": 0, "titles": []}),
        {"query": "qqqzzz"})
    assert [c["satisfied"] for c in report["checks"]] == [False, False]
    report = gsearch.verify_github_search(
        {"url": "x"}, _gsearch_stages(
            search={"url": "https://github.com/search?q=x",
                    "served": True, "count": 2, "titles": []}),
        {"query": "x"})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("GS1", True), ("GS2", False)]
    assert gsearch.verify_github_search(
        None, [], {"query": "x"})["status"] == "unavailable"


def test_gsearch_end_to_end_success(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(FakeGsearchPage()))
        exec_id = ex.submit("github-search", "chimera", _gsearch_params())
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "succeeded"
        assert record["verdict"] == "verified-success"
        assert [c["check_id"] for c in record["checks"]] == ["GS1", "GS2"]
        stages = gsearch.stages_for_trace(record["trace_path"])
        assert [s["stage"] for s in stages] == ["search"]
        assert len(stages[0]["state"]["titles"]) == 3
    finally:
        store.close()


def test_gsearch_end_to_end_no_matches(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(
                          FakeGsearchPage(empty=True)))
        exec_id = ex.submit("github-search", "chimera",
                            _gsearch_params(query="qqqzzz"))
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "failed"
        assert record["verdict"] == "verified-failure"
        assert "returned no repositories" in (record["error"] or "")
    finally:
        store.close()


# ---------------------------------------------------------------------------
# Steam price check
# ---------------------------------------------------------------------------

def _steam_params(**overrides):
    base = {"query": "portal", "pick": 1}
    base.update(overrides)
    return base


def test_registry_lists_steam_chimera_only():
    assert get_workflow("steam-price-check") is STEAM_PRICE
    assert STEAM_PRICE.origin == "external"
    assert STEAM_PRICE.drivers == ("chimera",)
    assert "steam-price-check" in [w.workflow_id for w in list_workflows()]


def test_steam_params_validate():
    cleaned = STEAM_PRICE.validate(_steam_params())
    assert (cleaned["query"], cleaned["pick"]) == ("portal", 1)
    with pytest.raises(WorkflowValidationError):
        STEAM_PRICE.validate(_steam_params(query="  "))
    with pytest.raises(WorkflowValidationError):
        STEAM_PRICE.validate(_steam_params(pick=0))
    with pytest.raises(WorkflowValidationError):
        STEAM_PRICE.validate(_steam_params(pick=6))


def test_steam_baseline_rejected(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb")
        with pytest.raises(WorkflowValidationError):
            ex.submit("steam-price-check", "baseline-a", _steam_params())
    finally:
        store.close()


def test_steam_run_spec():
    spec = _run_spec("steam-price-check",
                     _steam_params(query="q", pick=2))
    assert spec["verify"] == "steam"
    assert spec["expected"] == {"query": "q", "pick": 2}
    assert spec["url"] == steam.HOME_URL
    assert isinstance(spec["policy"], ActionPolicy)
    with pytest.raises(WorkflowValidationError):
        _run_spec("steam-price-check", _steam_params(query="  "))


def test_steam_url_guard():
    assert steam.assert_approved_url("https://store.steampowered.com/")
    assert steam.assert_approved_url(steam.search_url("portal"))
    assert steam.assert_approved_url(
        "https://store.steampowered.com/app/620/Portal_2/")
    for bad in ("https://evil.com/",
                "https://store.steampowered.com/app/",
                "https://store.steampowered.com/app/abc",
                "http://store.steampowered.com/",
                "",
                None):
        with pytest.raises(steam.UnapprovedURLError):
            steam.assert_approved_url(bad)
    with pytest.raises(ValueError):
        steam.search_url("  ")


def test_steam_policy_allows_store_denies_off_origin():
    from workbench.executor import _steam_policy

    policy = _steam_policy()
    for url in (steam.HOME_URL, steam.search_url("portal"),
                "https://store.steampowered.com/app/620/Portal_2/"):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "allowed", url
    for url in ("https://store.steampowered.com/login/",
                "https://store.steampowered.com/app/abc",
                "https://evil.com/"):
        decision, _ = policy.judge("navigate", {"url": url})
        assert decision == "denied", url


def _steam_stages(**states):
    return [{"stage": name, "url": "https://store.steampowered.com/x",
             "captured_at": "t", "state": state}
            for name, state in states.items()]


def test_steam_verify_success():
    report = steam.verify_steam_price(
        {"url": "x"}, _steam_stages(
            search={"count": 3, "results": [
                {"name": "Portal", "href": "/app/400/Portal/"}]},
            game={"url": "https://store.steampowered.com/app/400/",
                  "name": "Portal", "price": "$19.99"}),
        {"query": "portal", "pick": 1})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("ST1", True), ("ST2", True)]


def test_steam_verify_failures():
    report = steam.verify_steam_price(
        {"url": "x"}, _steam_stages(
            search={"count": 0, "results": []},
            game={"url": "", "name": "", "price": ""}),
        {"query": "q", "pick": 1})
    assert [c["satisfied"] for c in report["checks"]] == [False, False]
    report = steam.verify_steam_price(
        {"url": "x"}, _steam_stages(
            search={"count": 3, "results": [
                {"name": "Portal", "href": "/app/400/"}]},
            game={"url": "https://store.steampowered.com/app/400/",
                  "name": "Something Else", "price": "$19.99"}),
        {"query": "portal", "pick": 1})
    assert [(c["check_id"], c["satisfied"]) for c in report["checks"]] == [
        ("ST1", True), ("ST2", False)]
    assert steam.verify_steam_price(
        None, [], {"pick": 1})["status"] == "unavailable"


def test_steam_end_to_end_success(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(FakeSteamPage()))
        exec_id = ex.submit("steam-price-check", "chimera",
                            _steam_params(pick=2))
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "succeeded"
        assert record["verdict"] == "verified-success"
        assert [c["check_id"] for c in record["checks"]] == ["ST1", "ST2"]
        stages = steam.stages_for_trace(record["trace_path"])
        assert [s["stage"] for s in stages] == ["search", "game"]
        assert stages[1]["state"]["price"] == "$19.99"
    finally:
        store.close()


def test_steam_end_to_end_pick_out_of_range(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(FakeSteamPage()))
        exec_id = ex.submit("steam-price-check", "chimera",
                            _steam_params(pick=5))
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "failed"
        assert record["verdict"] == "verified-failure"
        assert "cannot pick #5" in (record["error"] or "")
    finally:
        store.close()


def test_steam_end_to_end_gated_game(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(
                          FakeSteamPage(empty_game=True)))
        exec_id = ex.submit("steam-price-check", "chimera",
                            _steam_params())
        record = _wait_terminal(store, exec_id)
        assert record["status"] == "failed"
        assert record["verdict"] == "verified-failure"
        assert "does not name the picked game" in (record["error"] or "")
    finally:
        store.close()
