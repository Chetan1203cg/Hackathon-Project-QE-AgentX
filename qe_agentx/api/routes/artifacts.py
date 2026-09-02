"""
api/routes/artifacts.py
========================
Endpoints for retrieving and downloading pipeline artefacts.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from api.routes.pipeline import _runs
from exports.markdown_exporter import MarkdownExporter
from exports.json_exporter import JsonExporter
from exports.csv_exporter import CsvExporter
from exports.excel_exporter import ExcelExporter
from exports.pdf_exporter import PdfExporter

router = APIRouter()


@router.get("/{run_id}")
async def get_artifacts(run_id: str):
    """Return all generated artefacts for a completed run."""
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run["status"] != "completed":
        raise HTTPException(status_code=409, detail=f"Run status: {run['status']}")

    state = run["state"]
    raw_story = state.get("raw_story") or {}
    return {
        "run_id": run_id,
        "story_id": state.get("story_id"),
        "release_version": state.get("release_version"),
        "release_traceability": state.get("release_traceability", {}),
        "test_cycle": state.get("test_cycle"),
        "deployment_report": state.get("deployment_report"),
        "vector_validation_report": state.get("vector_validation_report"),
        "health_check": state.get("health_check"),
        "automation_execution": state.get("automation_execution"),
        "schema_validation_report": state.get("schema_validation_report"),
        "release_decision": state.get("release_decision"),
        "manual_qa": state.get("manual_qa"),
        "final_report": state.get("final_report"),
        "behaviour_tree": state.get("behaviour_tree"),
        "test_cases": state.get("test_cases", []),
        "coverage_map": state.get("coverage_map"),
        "rtm": state.get("rtm"),
        "review_report": state.get("review_report"),
        "related_jira_items": [
            {
                "key": item.get("key", ""),
                "summary": item.get("summary", ""),
                "type": item.get("type", ""),
                "priority": item.get("priority", ""),
                "status": item.get("status", ""),
                "assignee": item.get("assignee", ""),
                "url": item.get("link", ""),
            }
            for item in (raw_story.get("related_work_items") or [])
        ],
    }


@router.get("/{run_id}/export/markdown")
async def export_markdown(run_id: str):
    """Export the complete test suite as Markdown."""
    state = _get_completed_state(run_id)
    content = MarkdownExporter().export(state)
    return Response(
        content=content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{state["story_id"]}_testcases.md"'},
    )


@router.get("/{run_id}/export/json")
async def export_json(run_id: str):
    """Export test cases as Xray-compatible JSON."""
    state = _get_completed_state(run_id)
    content = JsonExporter().export(state)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{state["story_id"]}_xray.json"'},
    )


@router.get("/{run_id}/export/csv")
async def export_csv(run_id: str):
    """Export the RTM as CSV."""
    state = _get_completed_state(run_id)
    content = CsvExporter().export(state)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{state["story_id"]}_rtm.csv"'},
    )


@router.get("/{run_id}/export/excel")
async def export_excel(run_id: str):
    """Export release traceability and test cases as Excel."""
    state = _get_completed_state(run_id)
    return Response(
        content=ExcelExporter().export(state),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{state["story_id"]}_testcases.xlsx"'},
    )


@router.get("/{run_id}/export/pdf")
async def export_pdf(run_id: str):
    """Export release traceability and test cases as PDF."""
    state = _get_completed_state(run_id)
    return Response(
        content=PdfExporter().export(state),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{state["story_id"]}_testcases.pdf"'},
    )


def _get_completed_state(run_id: str) -> dict:
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run["status"] != "completed":
        raise HTTPException(status_code=409, detail=f"Run not complete: {run['status']}")
    return run["state"]
