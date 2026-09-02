"""
orchestrator/graph.py
======================
LangGraph state machine definition for the QE AgentX pipeline.

Agent Execution Order:
  1. requirement_agent     → parse + ambiguity detect
  2. [HITL gate]           → clarification if ambiguities found
  3. scenario_agent        → behaviour tree
  4. testcase_agent   ─┐
  5. testdata_agent   ─┘  (parallel)
  6. coverage_agent        → coverage mapping
  7. rtm_agent             → traceability matrix
  8. review_agent          → quality review + gap detection
  9. [HITL gate]           → human approval if quality < threshold
 10. reporting_agent       → final report bundle
"""

from __future__ import annotations

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from orchestrator.state import AgentXState
from orchestrator.router import route_after_health_check, route_after_requirement, route_after_review
from config.settings import get_settings
from agents.requirement_agent import RequirementAgent
from agents.scenario_agent import ScenarioAgent
from agents.testcase_agent import TestCaseAgent
from agents.testdata_agent import TestDataAgent
from agents.coverage_agent import CoverageAgent
from agents.rtm_agent import RTMAgent
from agents.review_agent import ReviewAgent
from agents.reporting_agent import ReportingAgent
from agents.release_agents import AutomationStarterAgent, ReleaseDecisionAgent, SchemaValidationAgent
from agents.release_validation_agent import HealthCheckAgent, OneHubDeploymentAgent, VectorValidationAgent


def _stage(label: str):
    """Wrap an agent run with a stage label update."""
    def decorator(agent_run):
        def wrapper(state: AgentXState) -> dict:
            result = agent_run(state)
            result["current_stage"] = label
            return result
        wrapper.__name__ = agent_run.__name__
        return wrapper
    return decorator


def build_graph(settings=None) -> StateGraph:
    """Construct and compile the QE AgentX LangGraph pipeline."""
    if settings is None:
        settings = get_settings()

    # Instantiate agents
    req_agent = RequirementAgent(settings)
    scen_agent = ScenarioAgent(settings)
    tc_agent = TestCaseAgent(settings)
    td_agent = TestDataAgent(settings)
    cov_agent = CoverageAgent(settings)
    rtm_agent = RTMAgent(settings)
    rev_agent = ReviewAgent(settings)
    rep_agent = ReportingAgent(settings)
    deployment_agent = OneHubDeploymentAgent(settings)
    vector_agent = VectorValidationAgent(settings)
    health_agent = HealthCheckAgent(settings)
    automation_starter = AutomationStarterAgent(settings)
    schema_agent = SchemaValidationAgent(settings)
    decision_agent = ReleaseDecisionAgent(settings)

    # ------------------------------------------------------------------ #
    # Node functions (each delegates to agent.run())
    # ------------------------------------------------------------------ #

    @_stage("Analysing Requirements")
    def run_requirement_agent(state: AgentXState) -> dict:
        return req_agent.run(state)

    @_stage("OneHub Deployment")
    def run_deployment_agent(state: AgentXState) -> dict:
        return deployment_agent.run(state)

    @_stage("VECTor Version Validation")
    def run_vector_agent(state: AgentXState) -> dict:
        return vector_agent.run(state)

    @_stage("Health Check")
    def run_health_agent(state: AgentXState) -> dict:
        return health_agent.run(state)

    @_stage("Starting Java Selenium Automation")
    def run_automation_starter(state: AgentXState) -> dict:
        return automation_starter.run(state)

    @_stage("Validating i18n, ACS, and AEM Schemas")
    def run_schema_agent(state: AgentXState) -> dict:
        return schema_agent.run(state)

    @_stage("Calculating Release Decision")
    def run_decision_agent(state: AgentXState) -> dict:
        return decision_agent.run(state)

    def hitl_clarification(state: AgentXState) -> dict:
        """Interrupt node — execution pauses here until hitl_response is set."""
        return {"current_stage": "Awaiting Clarification"}

    @_stage("Building Scenario Tree")
    def run_scenario_agent(state: AgentXState) -> dict:
        return scen_agent.run(state)

    @_stage("Generating Test Cases")
    def run_testcase_agent(state: AgentXState) -> dict:
        return tc_agent.run(state)

    @_stage("Synthesising Test Data")
    def run_testdata_agent(state: AgentXState) -> dict:
        return td_agent.run(state)

    @_stage("Calculating Coverage")
    def run_coverage_agent(state: AgentXState) -> dict:
        return cov_agent.run(state)

    @_stage("Building RTM")
    def run_rtm_agent(state: AgentXState) -> dict:
        return rtm_agent.run(state)

    @_stage("Reviewing Quality")
    def run_review_agent(state: AgentXState) -> dict:
        return rev_agent.run(state)

    def hitl_review_approval(state: AgentXState) -> dict:
        """Second HITL gate — pauses for human approval of low-quality output."""
        return {"current_stage": "Awaiting Review Approval"}

    @_stage("Generating Report")
    def run_reporting_agent(state: AgentXState) -> dict:
        return rep_agent.run(state)

    # ------------------------------------------------------------------ #
    # Graph construction
    # ------------------------------------------------------------------ #

    builder = StateGraph(AgentXState)

    builder.add_node("onehub_deployment_agent", run_deployment_agent)
    builder.add_node("vector_validation_agent", run_vector_agent)
    builder.add_node("health_check_agent", run_health_agent)
    builder.add_node("automation_starter_agent", run_automation_starter)
    builder.add_node("schema_validation_agent", run_schema_agent)
    builder.add_node("release_decision_agent", run_decision_agent)
    builder.add_node("requirement_agent", run_requirement_agent)
    builder.add_node("hitl_clarification", hitl_clarification)
    builder.add_node("scenario_agent", run_scenario_agent)
    builder.add_node("testcase_agent", run_testcase_agent)
    builder.add_node("testdata_agent", run_testdata_agent)
    builder.add_node("coverage_agent", run_coverage_agent)
    builder.add_node("rtm_agent", run_rtm_agent)
    builder.add_node("review_agent", run_review_agent)
    builder.add_node("hitl_review_approval", hitl_review_approval)
    builder.add_node("reporting_agent", run_reporting_agent)

    # Entry point
    builder.set_entry_point("onehub_deployment_agent")
    builder.add_edge("onehub_deployment_agent", "vector_validation_agent")
    builder.add_edge("vector_validation_agent", "health_check_agent")
    builder.add_conditional_edges(
        "health_check_agent",
        route_after_health_check,
        {"automation_starter_agent": "automation_starter_agent", "health_check_failed": END},
    )
    builder.add_edge("automation_starter_agent", "requirement_agent")

    # Conditional: go to HITL if ambiguities found, else straight to scenario
    builder.add_conditional_edges(
        "requirement_agent",
        route_after_requirement,
        {
            "hitl_clarification": "hitl_clarification",
            "scenario_agent": "scenario_agent",
        },
    )

    # HITL clarification → scenario (pipeline resumes after human responds)
    builder.add_edge("hitl_clarification", "scenario_agent")

    # Scenario → test case generation (TC and TD run sequentially for MVP;
    # swap to Send() API for true parallel execution in production)
    builder.add_edge("scenario_agent", "testcase_agent")
    builder.add_edge("testcase_agent", "testdata_agent")
    builder.add_edge("testdata_agent", "coverage_agent")
    builder.add_edge("coverage_agent", "rtm_agent")
    builder.add_edge("rtm_agent", "review_agent")

    # Conditional: HITL approval gate for low-quality output
    builder.add_conditional_edges(
        "review_agent",
        route_after_review,
        {
            "hitl_review_approval": "hitl_review_approval",
            "reporting_agent": "reporting_agent",
        },
    )

    builder.add_edge("hitl_review_approval", "reporting_agent")
    builder.add_edge("reporting_agent", "schema_validation_agent")
    builder.add_edge("schema_validation_agent", "release_decision_agent")
    builder.add_edge("release_decision_agent", END)

    # Use in-memory checkpointer for MVP (swap for Redis-backed in production)
    checkpointer = MemorySaver()
    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["hitl_clarification", "hitl_review_approval"],
    )
