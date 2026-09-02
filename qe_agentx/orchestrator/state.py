"""
orchestrator/state.py
======================
Shared pipeline state for the LangGraph state machine.
All agents read from and write to this typed dictionary.
"""

from __future__ import annotations

from typing import Annotated, Any
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentXState(TypedDict):
    # ------------------------------------------------------------------ #
    # Input
    # ------------------------------------------------------------------ #
    run_id: str
    story_id: str
    raw_story: dict[str, Any]
    release_version: str
    target_environment: str
    project_key: str
    release_traceability: dict[str, Any]

    # ------------------------------------------------------------------ #
    # Agent outputs (populated sequentially through the pipeline)
    # ------------------------------------------------------------------ #
    structured_requirement: dict | None   # Agent 1 — SRO
    behaviour_tree: dict | None           # Agent 2 — SBT
    test_cases: list[dict]                # Agent 3 — TCS
    test_data: dict | None                # Agent 4 — TDM
    coverage_map: dict | None             # Agent 5 — CM
    rtm: dict | None                      # Agent 6 — RTMA
    review_report: dict | None            # Agent 7 — RR
    final_report: dict | None             # Agent 8 — FRB
    deployment_report: dict | None
    vector_validation_report: dict | None
    health_check: dict | None
    automation_execution: dict | None
    schema_validation_report: dict | None
    release_decision: dict | None
    manual_qa: dict | None
    test_cycle: dict | None

    # ------------------------------------------------------------------ #
    # HITL (Human-in-the-Loop) state
    # ------------------------------------------------------------------ #
    ambiguities: list[str]        # Questions surfaced to QA engineer
    hitl_pending: bool             # True = pipeline paused, awaiting human
    hitl_response: str | None      # Human's clarification text

    # ------------------------------------------------------------------ #
    # Pipeline metadata
    # ------------------------------------------------------------------ #
    errors: list[str]              # Per-agent error accumulator
    current_stage: str             # Human-readable current stage label
    messages: Annotated[list, add_messages]  # Conversational history (HITL chat)
