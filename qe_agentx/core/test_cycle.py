"""Zephyr Scale-inspired test cycle and execution calculations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

EXECUTION_STATUSES = ("PASS", "FAIL", "BLOCKED", "NOT_EXECUTED")


def create_test_cycle(state: dict[str, Any]) -> dict[str, Any]:
    """Organize generated test assets into an executable test cycle."""
    release = state.get("release_traceability") or {}
    story = state.get("raw_story") or {}
    story_id = state.get("story_id", "")
    sprint = _available(release.get("sprint"))
    release_name = _available(release.get("fa_release_version"))
    planning_label = sprint or release_name or "Unscheduled"
    testing_type = _testing_type(state.get("test_cases") or [])

    cycle = {
        "cycle_id": f"TCY-{state.get('run_id', '')[:8].upper()}",
        "name": f"{planning_label} - {story_id} Validation",
        "environment": state.get("target_environment") or release.get("environment") or "QA",
        "execution_type": testing_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "release_traceability": release,
        "requirement": {
            "key": story_id,
            "type": story.get("type", "Requirement"),
            "summary": story.get("summary", ""),
            "acceptance_criteria": (state.get("structured_requirement") or {}).get(
                "acceptance_criteria", []
            ),
        },
        "executions": [
            {
                "tc_id": test_case.get("tc_id", ""),
                "title": test_case.get("title", ""),
                "ac_ref": test_case.get("ac_ref", ""),
                "risk_level": test_case.get("risk_level", "MEDIUM"),
                "status": "NOT_EXECUTED",
                "execution_comments": "",
                "defects": [],
                "evidence": [],
                "release_traceability": release,
                "updated_at": None,
            }
            for test_case in (state.get("test_cases") or [])
        ],
    }
    refresh_cycle_summary(cycle, state.get("coverage_map") or {})
    return cycle


def refresh_cycle_summary(cycle: dict[str, Any], coverage: dict[str, Any]) -> None:
    """Recalculate execution metrics and release readiness in place."""
    executions = cycle.get("executions") or []
    counts = {
        status: sum(item.get("status") == status for item in executions)
        for status in EXECUTION_STATUSES
    }
    total = len(executions)
    executed = total - counts["NOT_EXECUTED"]
    defect_ids = {
        defect.get("key")
        for execution in executions
        for defect in (execution.get("defects") or [])
        if defect.get("key")
    }
    metrics = {
        "total": total,
        "executed": executed,
        "passed": counts["PASS"],
        "failed": counts["FAIL"],
        "blocked": counts["BLOCKED"],
        "not_executed": counts["NOT_EXECUTED"],
        "execution_progress_pct": round(executed / total * 100, 1) if total else 0.0,
        "pass_rate_pct": round(counts["PASS"] / executed * 100, 1) if executed else 0.0,
        "defect_count": len(defect_ids),
    }
    coverage_pct = float(coverage.get("overall_coverage_pct", 0))
    if executed < total:
        recommendation = "NOT READY"
    elif counts["FAIL"]:
        recommendation = "NO GO"
    elif counts["BLOCKED"] or coverage_pct < 90:
        recommendation = "GO WITH RISK"
    else:
        recommendation = "GO"

    cycle["metrics"] = metrics
    cycle["readiness_summary"] = {
        "requirement_coverage_pct": coverage_pct,
        "test_execution_summary": metrics,
        "failure_analysis": [
            {
                "tc_id": item.get("tc_id"),
                "title": item.get("title"),
                "comments": item.get("execution_comments", ""),
            }
            for item in executions
            if item.get("status") == "FAIL"
        ],
        "linked_defects": sorted(defect_ids),
        "risk_assessment": _risk_assessment(counts, executed, total, coverage_pct),
        "release_recommendation": recommendation,
    }


def _testing_type(test_cases: list[dict[str, Any]]) -> str:
    tags = {str(tag).lower() for test_case in test_cases for tag in test_case.get("tags", [])}
    for name in ("smoke", "regression", "integration", "uat"):
        if name in tags:
            return f"{name.upper() if name == 'uat' else name.title()} Testing"
    return "Functional Testing"


def _risk_assessment(
    counts: dict[str, int], executed: int, total: int, coverage_pct: float
) -> str:
    if counts["FAIL"]:
        return "HIGH"
    if counts["BLOCKED"] or executed < total or coverage_pct < 90:
        return "MEDIUM"
    return "LOW"


def _available(value: Any) -> str:
    text = str(value or "")
    if text.startswith("Release Information Not Available"):
        return ""
    return text
