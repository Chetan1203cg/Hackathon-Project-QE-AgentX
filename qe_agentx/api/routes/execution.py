"""Zephyr-style test execution, evidence, and Jira defect endpoints."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from api.routes.pipeline import _runs
from config.settings import get_settings
from core.file_preservation import available_path
from core.test_cycle import refresh_cycle_summary
from integrations.jira_client import JiraClient

router = APIRouter()
EVIDENCE_ROOT = Path(__file__).resolve().parents[2] / "demo_output" / "evidence"
MAX_EVIDENCE_BYTES = 20 * 1024 * 1024


class ExecutionUpdate(BaseModel):
    status: Literal["PASS", "FAIL", "BLOCKED", "NOT_EXECUTED"]
    execution_comments: str = ""
    existing_defect_key: str | None = None
    existing_defect_summary: str = ""


class NewDefectRequest(BaseModel):
    summary: str
    description: str = ""


@router.get("/{run_id}")
async def get_test_cycle(run_id: str):
    """Return the executable test cycle and current progress summary."""
    _, cycle = _get_cycle(run_id)
    return cycle


@router.put("/{run_id}/tests/{tc_id}")
async def update_execution(run_id: str, tc_id: str, update: ExecutionUpdate):
    """Record execution status, comments, and an optional existing Jira defect."""
    state, cycle = _get_cycle(run_id)
    execution = _get_execution(cycle, tc_id)
    if update.existing_defect_key and update.status != "FAIL":
        raise HTTPException(status_code=400, detail="Defects can only be linked to failed tests")

    execution["status"] = update.status
    execution["execution_comments"] = update.execution_comments
    execution["updated_at"] = datetime.now(UTC).isoformat()
    if update.existing_defect_key:
        defect_key = update.existing_defect_key.strip().upper()
        if not any(item.get("key") == defect_key for item in execution["defects"]):
            settings = get_settings()
            try:
                with JiraClient(settings) as jira:
                    jira.link_issues(state["story_id"], defect_key)
            except Exception as exc:
                raise HTTPException(status_code=502, detail=f"Jira defect linking failed: {exc}") from exc
            execution["defects"].append({
                "key": defect_key,
                "summary": update.existing_defect_summary,
                "source": "linked",
            })
    _refresh_state(state, cycle)
    return execution


@router.post("/{run_id}/tests/{tc_id}/defects", status_code=201)
async def create_defect(run_id: str, tc_id: str, request: NewDefectRequest):
    """Create and associate a Jira bug for a failed execution."""
    state, cycle = _get_cycle(run_id)
    execution = _get_execution(cycle, tc_id)
    if execution.get("status") != "FAIL":
        raise HTTPException(status_code=400, detail="Mark the test as FAIL before creating a defect")

    settings = get_settings()
    try:
        with JiraClient(settings) as jira:
            defect = jira.create_bug(
                state.get("project_key") or state["story_id"].split("-", 1)[0],
                request.summary,
                request.description,
                state["story_id"],
            )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Jira bug creation failed: {exc}") from exc
    execution["defects"].append(defect)
    _refresh_state(state, cycle)
    return defect


@router.post("/{run_id}/tests/{tc_id}/evidence", status_code=201)
async def upload_evidence(
    run_id: str,
    tc_id: str,
    evidence: Annotated[UploadFile, File()],
):
    """Persist a screenshot, log, or supporting evidence file for an execution."""
    state, cycle = _get_cycle(run_id)
    execution = _get_execution(cycle, tc_id)
    content = await evidence.read(MAX_EVIDENCE_BYTES + 1)
    if len(content) > MAX_EVIDENCE_BYTES:
        raise HTTPException(status_code=413, detail="Evidence files are limited to 20 MB")

    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", Path(evidence.filename or "evidence").name)
    target_dir = EVIDENCE_ROOT / run_id / tc_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target = available_path(target_dir / safe_name)
    target.write_bytes(content)
    metadata = {
        "filename": target.name,
        "content_type": evidence.content_type or "application/octet-stream",
        "size": len(content),
        "path": str(target.relative_to(EVIDENCE_ROOT.parent.parent)),
        "uploaded_at": datetime.now(UTC).isoformat(),
        "release_traceability": state.get("release_traceability") or {},
    }
    execution["evidence"].append(metadata)
    _refresh_state(state, cycle)
    return metadata


def _get_cycle(run_id: str) -> tuple[dict, dict]:
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    cycle = run["state"].get("test_cycle")
    if not cycle:
        raise HTTPException(status_code=409, detail="Test cycle is not available until generation completes")
    return run["state"], cycle


def _get_execution(cycle: dict, tc_id: str) -> dict:
    execution = next(
        (item for item in cycle.get("executions", []) if item.get("tc_id") == tc_id),
        None,
    )
    if not execution:
        raise HTTPException(status_code=404, detail="Test case not found in cycle")
    return execution


def _refresh_state(state: dict, cycle: dict) -> None:
    refresh_cycle_summary(cycle, state.get("coverage_map") or {})
    state["manual_qa"] = {
        "status": "COMPLETED" if cycle["metrics"]["not_executed"] == 0 else "IN_PROGRESS",
        "results": cycle["executions"],
        "metrics": cycle["metrics"],
        "release_traceability": state.get("release_traceability") or {},
    }
    decision = state.get("release_decision") or {}
    decision["test_execution_summary"] = cycle["metrics"]
    decision["recommendation"] = cycle["readiness_summary"]["release_recommendation"]
    state["release_decision"] = decision
