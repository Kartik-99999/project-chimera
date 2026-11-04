"""Tests for user browser sessions (profiles, never the live web).

Covers profile validation, the session column migration, submit
guards, session labeling, and the sessions CLI. All profile paths
are redirected to tmp dirs; nothing touches the real home.
"""

import os
import sqlite3
import stat
import time

import pytest

from tests.fake_lookup import (
    FakeSoPage,
    _StubBrowser,
    _StubContext,
)
from workbench import sessions as sessions_module
from workbench.executor import Executor, _run_spec
from workbench.sessions import (
    ProfileMissingError,
    ProfileNameError,
)
from workbench.store import SCHEMA, Store
from workbench.workflows import (
    SO_SEARCH,
    WorkflowValidationError,
    get_workflow,
)


@pytest.fixture()
def profiles_home(tmp_path, monkeypatch):
    root = tmp_path / "profiles"
    monkeypatch.setenv(sessions_module.ENV_PROFILES_DIR, str(root))
    return root


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


def test_default_sessions_clean_only():
    assert get_workflow("create-project").sessions == ("clean",)
    assert SO_SEARCH.sessions == ("clean", "user")
    assert get_workflow("create-project").to_dict()["sessions"] == ["clean"]


def test_profile_names_validate():
    assert sessions_module.check_profile_name("me") == "me"
    assert sessions_module.check_profile_name("work-2") == "work-2"
    for bad in ("", "  ", "Bad", "a/b", "..", "../evil", "a" * 65,
                "-lead", "trail-", "with space"):
        with pytest.raises(ProfileNameError):
            sessions_module.check_profile_name(bad)


def test_profile_path_stays_inside_root(profiles_home):
    path = sessions_module.profile_path("me")
    assert str(path).startswith(str(profiles_home.resolve())
                                if profiles_home.exists()
                                else str(profiles_home))
    assert path.name == "me"


def test_list_prepare_remove_roundtrip(profiles_home):
    assert sessions_module.list_profiles() == []
    path = sessions_module.prepare_profile_dir("me")
    assert path.is_dir()
    assert stat.S_IMODE(path.stat().st_mode) == 0o700
    assert sessions_module.list_profiles() == ["me"]
    assert sessions_module.remove_profile("me") is True
    assert sessions_module.remove_profile("me") is False
    assert sessions_module.list_profiles() == []


def test_require_missing_profile_points_at_login(profiles_home):
    with pytest.raises(ProfileMissingError) as info:
        sessions_module.require_profile("ghost")
    assert "sessions login ghost" in str(info.value)


def test_profiles_dir_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv(sessions_module.ENV_PROFILES_DIR,
                       str(tmp_path / "elsewhere"))
    assert sessions_module.profiles_dir() == tmp_path / "elsewhere"


def test_session_column_migrates_legacy_db(tmp_path):
    legacy = SCHEMA.replace(
        "    session TEXT NOT NULL DEFAULT 'clean', "
        "-- 'clean' | 'user:<profile>'\n", "")
    assert legacy != SCHEMA
    db = tmp_path / "legacy.db"
    con = sqlite3.connect(str(db))
    con.executescript(legacy)
    con.execute(
        "INSERT INTO executions (id, created_at, source, workflow_id, "
        "driver, scenario_id, trial_kind, status, verdict) "
        "VALUES ('r1','t','workbench','create-project','chimera','s',"
        "'adhoc','succeeded','verified-success')")
    con.commit()
    con.close()
    store = Store(db)
    try:
        assert store.get_execution("r1")["session"] == "clean"
    finally:
        store.close()


def test_submit_profile_rejected_for_clean_only(tmp_path, profiles_home):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb")
        with pytest.raises(WorkflowValidationError):
            ex.submit("create-project", "chimera",
                      {"project_name": "x", "scenario": "normal"},
                      profile="me")
        with pytest.raises(WorkflowValidationError):
            ex.submit("studio:whatever", "chimera", {}, profile="me")
    finally:
        store.close()


def test_submit_profile_requires_existing_profile(tmp_path, profiles_home):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb")
        with pytest.raises(ProfileMissingError):
            ex.submit("stackoverflow-search", "chimera",
                      {"query": "q"}, profile="ghost")
        with pytest.raises(ProfileNameError):
            ex.submit("stackoverflow-search", "chimera",
                      {"query": "q"}, profile="../evil")
    finally:
        store.close()


def test_submit_profile_labels_run_and_uses_fake(tmp_path, profiles_home):
    sessions_module.prepare_profile_dir("me")
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(FakeSoPage()))
        exec_id = ex.submit("stackoverflow-search", "chimera",
                            {"query": "pytest"}, profile="me")
        record = _wait_terminal(store, exec_id)
        assert record["session"] == "user:me"
        assert record["verdict"] == "verified-success"
    finally:
        store.close()


def test_submit_clean_session_label(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        ex = Executor(store, tmp_path / "wb",
                      chimera_factory=_fake_factory(FakeSoPage()))
        exec_id = ex.submit("stackoverflow-search", "chimera",
                            {"query": "pytest"})
        record = _wait_terminal(store, exec_id)
        assert record["session"] == "clean"
    finally:
        store.close()


def test_run_spec_carries_no_session_factory_by_default():
    spec = _run_spec("stackoverflow-search", {"query": "q"})
    assert "session_factory" not in spec


def test_cli_list_and_usage(profiles_home, capsys):
    assert sessions_module.main(["list"]) == 0
    assert sessions_module.main([]) == 2
    assert sessions_module.main(["bogus"]) == 2
    assert sessions_module.main(["login"]) == 2
    assert sessions_module.main(["login", "x", "--url"]) == 2
    assert sessions_module.main(["remove"]) == 2
    out = capsys.readouterr()
    assert "usage" in out.err


def test_cli_remove_roundtrip(profiles_home, capsys):
    assert sessions_module.main(["remove", "ghost"]) == 0
    assert "no such profile" in capsys.readouterr().out
    sessions_module.prepare_profile_dir("me")
    assert sessions_module.main(["remove", "me"]) == 0
    assert "removed profile" in capsys.readouterr().out
