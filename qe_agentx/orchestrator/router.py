"""
orchestrator/router.py
=======================
Conditional edge routing logic for the LangGraph state machine.
Each router function returns a string key that LangGraph maps to a node name.
"""

from __future__ import annotations

from orchestrator.state import AgentXState


def route_after_health_check(state: AgentXState) -> str:
    """Automation is allowed to start only after every health check passes."""
    if (state.get("health_check") or {}).get("ready_for_testing"):
        return "automation_starter_agent"
    return "health_check_failed"


def route_after_requirement(state: AgentXState) -> str:
    """
    After RequirementAgent:
    - If ambiguities were detected AND no HITL response yet → pause for clarification
    - Otherwise → proceed to ScenarioAgent
    """
    has_ambiguities = bool(state.get("ambiguities"))
    has_response = state.get("hitl_response") is not None

    if has_ambiguities and not has_response:
        return "hitl_clarification"
    return "scenario_agent"


def route_after_review(state: AgentXState) -> str:
    """
    After ReviewAgent:
    - If quality score < 70 or ERROR findings present → pause for human approval
    - Otherwise → proceed to ReportingAgent
    """
    review = state.get("review_report") or {}
    quality_score = review.get("quality_score", 100.0)
    findings = review.get("findings", [])
    has_errors = any(f.get("severity") == "ERROR" for f in findings)

    if quality_score < 70.0 or has_errors:
        return "hitl_review_approval"
    return "reporting_agent"
