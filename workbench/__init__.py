"""Chimera Workbench: practical browser-automation workbench.

This package turns the research harness into a usable application: run
real supported browser workflows, watch them execute, verify the result
against independent postcondition checks, and analyse current and
historical executions.

Honesty boundary: the drivers here are fixed scripts (a retrying agent
and a single-attempt replay driver), not a general-purpose AI model.
Only registered workflows may run; arbitrary natural-language tasks
are not supported and are never claimed.
"""

from workbench.workflows import WorkflowDefinition, WorkflowParameter, get_workflow, list_workflows

__all__ = [
    "WorkflowDefinition",
    "WorkflowParameter",
    "get_workflow",
    "list_workflows",
]
