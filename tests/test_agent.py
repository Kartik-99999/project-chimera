"""Tests for the Chimera agent's browser automation."""

from chimera.agent import create_project


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
