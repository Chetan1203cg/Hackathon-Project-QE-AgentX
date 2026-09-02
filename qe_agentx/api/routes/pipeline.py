"""
api/routes/pipeline.py
=======================
Pipeline trigger and status endpoints.
"""

from __future__ import annotations

import uuid
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from config.settings import get_settings
from core.test_cycle import create_test_cycle
from integrations.jira_client import JiraClient
from orchestrator.graph import build_graph
from orchestrator.state import AgentXState

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory run store (replace with Redis/DB in production)
_runs: dict[str, dict[str, Any]] = {}


class RunRequest(BaseModel):
    story_id: str
    release_version: str = ""
    target_environment: str = "test"
    project_key: str = "QA"
    export_to_xray: bool = False


class HITLResponse(BaseModel):
    response: str


@router.post("/run", status_code=202)
async def trigger_pipeline(req: RunRequest, background_tasks: BackgroundTasks):
    """Trigger the QE AgentX pipeline for a Jira story."""
    run_id = str(uuid.uuid4())
    settings = get_settings()

    # Fetch story from Jira
    try:
        with JiraClient(settings) as jira:
            raw_story = jira.get_story(req.story_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Jira fetch failed: {exc}") from exc

    release_traceability = raw_story.get("release_traceability") or {}
    jira_fa_release = release_traceability.get("fa_release_version", "")
    effective_release_version = (
        jira_fa_release
        if jira_fa_release and not jira_fa_release.startswith("Release Information Not Available")
        else req.release_version
    )

    initial_state: AgentXState = {
        "run_id": run_id,
        "story_id": req.story_id,
        "raw_story": raw_story,
        "release_version": effective_release_version,
        "target_environment": req.target_environment,
        "project_key": req.project_key,
        "release_traceability": release_traceability,
        "structured_requirement": None,
        "behaviour_tree": None,
        "test_cases": [],
        "test_data": None,
        "coverage_map": None,
        "rtm": None,
        "review_report": None,
        "final_report": None,
        "deployment_report": None,
        "vector_validation_report": None,
        "health_check": None,
        "automation_execution": None,
        "schema_validation_report": None,
        "release_decision": None,
        "manual_qa": {
            "status": "PENDING_HUMAN_EXECUTION",
            "results": [],
            "release_traceability": release_traceability,
        },
        "test_cycle": None,
        "ambiguities": [],
        "hitl_pending": False,
        "hitl_response": None,
        "errors": [],
        "current_stage": "Queued",
        "messages": [],
    }

    _runs[run_id] = {"status": "running", "state": initial_state}

    graph = build_graph(settings)
    config = {"configurable": {"thread_id": run_id}}

    background_tasks.add_task(_run_pipeline, graph, initial_state, config, run_id)

    return {"run_id": run_id, "story_id": req.story_id, "status": "accepted"}


@router.get("/{run_id}/status")
async def get_status(run_id: str):
    """Get the current pipeline status and stage."""
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    state = run["state"]
    raw_story = state.get("raw_story") or {}
    requirement = state.get("structured_requirement") or {}
    return {
        "run_id": run_id,
        "status": run["status"],
        "current_stage": state.get("current_stage", ""),
        "release_traceability": state.get("release_traceability", {}),
        "hitl_pending": state.get("hitl_pending", False),
        "ambiguities": state.get("ambiguities", []),
        "errors": state.get("errors", []),
        "copilot_context": {
            "jira": {
                "key": state.get("story_id"),
                "summary": raw_story.get("summary"),
                "description": raw_story.get("description"),
                "acceptance_criteria": requirement.get("acceptance_criteria", []),
            },
            "test_cases": state.get("test_cases", []),
            "coverage_map": state.get("coverage_map"),
            "review_report": state.get("review_report"),
            "final_report": state.get("final_report"),
        },
    }


@router.post("/{run_id}/hitl")
async def submit_hitl_response(
    run_id: str, response: HITLResponse, background_tasks: BackgroundTasks
):
    """Submit a human clarification response to resume a paused pipeline."""
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if not run["state"].get("hitl_pending"):
        raise HTTPException(status_code=400, detail="Pipeline is not awaiting HITL input")

    settings = get_settings()
    graph = build_graph(settings)
    config = {"configurable": {"thread_id": run_id}}

    # Inject the human response and resume
    run["state"]["hitl_response"] = response.response
    run["state"]["hitl_pending"] = False
    run["status"] = "running"

    background_tasks.add_task(_run_pipeline, graph, run["state"], config, run_id)

    return {"run_id": run_id, "status": "resumed"}


@router.post("/{run_id}/cancel")
async def cancel_pipeline(run_id: str):
    """Cancel a pipeline that is paused for human clarification."""
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run["status"] != "awaiting_hitl":
        raise HTTPException(
            status_code=409,
            detail="Only a pipeline awaiting human input can be cancelled",
        )

    run["status"] = "cancelled"
    run["state"]["hitl_pending"] = False
    run["state"]["current_stage"] = "Cancelled by user"
    return {"run_id": run_id, "status": "cancelled"}


# ------------------------------------------------------------------ #
# Background task
# ------------------------------------------------------------------ #

async def _run_pipeline(graph, initial_state: dict, config: dict, run_id: str):
    try:
        async for chunk in graph.astream(initial_state, config=config):
            # Update run state with latest chunk
            for node_name, node_output in chunk.items():
                if isinstance(node_output, dict):
                    _runs[run_id]["state"].update(node_output)

            # Check for HITL interrupt
            if _runs[run_id]["state"].get("hitl_pending"):
                _runs[run_id]["status"] = "awaiting_hitl"
                return

        state = _runs[run_id]["state"]
        state["test_cycle"] = create_test_cycle(state)
        _runs[run_id]["status"] = "completed"
        logger.info("[Pipeline] Run %s completed", run_id)

    except Exception as exc:
        logger.error("[Pipeline] Run %s failed: %s", run_id, exc, exc_info=True)
        _runs[run_id]["status"] = "failed"
        _runs[run_id]["state"]["errors"].append(str(exc))
