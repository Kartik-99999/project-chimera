"""Tests for the workbench store and workflow registry (no browser)."""

import pytest

from workbench.store import Store
from workbench.workflows import (
    WorkflowValidationError,
    get_workflow,
    list_workflows,
)


def _record(**kw):
    base = {
        "workflow_id": "create-project",
        "driver": "chimera",
        "scenario_id": "S-NORM",
        "project_name": "Demo",
    }
    base.update(kw)
    return base


def test_create_get_round_trip(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        exec_id = store.create_execution(_record(status="running"))
        store.replace_actions(exec_id, [
            {"seq": 0, "action_type": "navigate", "outcome": "ok",
             "elapsed_ms": 120},
            {"seq": 1, "action_type": "click", "outcome": "error",
             "error_type": "TimeoutError"},
        ])
        store.replace_verification(exec_id, [
            {"check_id": "P1", "satisfied": True, "detail": "visible"},
            {"check_id": "P2", "satisfied": False, "detail": "0 of 1"},
        ])
        store.update_execution(exec_id, {"status": "failed",
                                        "verdict": "verified-failure"})
        got = store.get_execution(exec_id)
        assert got["status"] == "failed"
        assert got["verdict"] == "verified-failure"
        assert [a["action_type"] for a in got["actions"]] == [
            "navigate", "click"]
        assert got["actions"][1]["elapsed_ms"] is None  # never zero-filled
        assert got["checks"][0]["satisfied"] == 1
        assert store.get_execution("missing") is None
    finally:
        store.close()


def test_list_filters_sort_paginate(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        for i in range(5):
            store.create_execution(_record(
                driver="chimera" if i % 2 else "baseline-a",
                verdict="verified-success" if i % 2 else "verified-failure",
                created_at=f"2026-10-3{i}T10:00:00.000+00:00"))
        page = store.list_executions(
            filters={"driver": "chimera"}, sort="-created_at",
            page=1, page_size=2)
        assert page["total"] == 2
        assert len(page["rows"]) == 2
        assert page["rows"][0]["created_at"] > page["rows"][1]["created_at"]
        assert store.count({"verdict": "verified-failure"}) == 3
        assert store.distinct("driver") == ["baseline-a", "chimera"]
        with pytest.raises(ValueError):
            store.list_executions(sort="-error")
        with pytest.raises(ValueError):
            store.list_executions(filters={"nope": 1})
    finally:
        store.close()


def test_update_rejects_unknown_fields(tmp_path):
    store = Store(tmp_path / "w.db")
    try:
        exec_id = store.create_execution(_record())
        store.update_execution(exec_id, {"driver": "x", "status": "failed"})
        assert store.get_execution(exec_id)["driver"] == "chimera"
        assert store.delete_execution(exec_id) is True
        assert store.delete_execution(exec_id) is False
    finally:
        store.close()


def test_workflow_registry_and_validation():
    assert [w.workflow_id for w in list_workflows()] == [
        "create-project", "fill-contact-form", "saucedemo-order",
        "saucedemo-stress", "flipkart-add-to-cart",
        "wikipedia-article-lookup", "wiktionary-word-lookup",
        "pypi-package-lookup", "bbc-headlines", "github-profile",
        "crates-lookup", "bbc-weather", "github-search",
        "steam-price-check", "arxiv-search", "stackoverflow-search",
        "amazon-price-check", "third-party-sites"]
    assert [w.future for w in list_workflows()].count(False) == 17
    wf = get_workflow("create-project")
    cleaned = wf.validate({"project_name": "  Acme  ", "scenario": "slow",
                           "slow_ms": 500, "action_timeout_ms": 0})
    assert cleaned["project_name"] == "Acme"
    assert cleaned["slow_ms"] == 500
    with pytest.raises(WorkflowValidationError):
        wf.validate({"project_name": "  ", "scenario": "normal"})
    with pytest.raises(WorkflowValidationError):
        wf.validate({"project_name": "x", "scenario": "nope"})
    with pytest.raises(WorkflowValidationError):
        wf.validate({"project_name": "x", "scenario": "slow",
                     "slow_ms": 999999})
    contact = get_workflow("fill-contact-form")
    good = {"full_name": "Ann Lee", "email": "ann@example.com",
            "subject": "Hi", "message": "Hello", "submission_case": "complete",
            "scenario": "normal"}
    assert contact.validate(good)["email"] == "ann@example.com"
    assert contact.validate({**good, "subject": ""})["subject"] == ""
    with pytest.raises(WorkflowValidationError):
        contact.validate({**good, "email": "  "})
    with pytest.raises(WorkflowValidationError):
        contact.validate({**good, "submission_case": "bogus"})
    with pytest.raises(WorkflowValidationError):
        contact.validate({**good, "extra": 1})
    with pytest.raises(WorkflowValidationError):
        get_workflow("third-party-sites")
    with pytest.raises(WorkflowValidationError):
        get_workflow("do-anything")
