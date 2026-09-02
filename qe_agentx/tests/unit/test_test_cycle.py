"""Tests for Zephyr-style test cycle execution calculations."""

from __future__ import annotations

from core.test_cycle import create_test_cycle, refresh_cycle_summary


def _state() -> dict:
    return {
        "run_id": "12345678-abcd",
        "story_id": "ABC-123",
        "target_environment": "QA",
        "raw_story": {"type": "User Story", "summary": "Login enhancement"},
        "structured_requirement": {"acceptance_criteria": [{"id": "AC-01"}]},
        "release_traceability": {"sprint": "Sprint 24", "fa_release_version": "FA 1"},
        "coverage_map": {"overall_coverage_pct": 100},
        "test_cases": [
            {"tc_id": "TC-001", "title": "Successful login", "ac_ref": "AC-01", "tags": ["smoke"]},
            {"tc_id": "TC-002", "title": "Invalid password", "ac_ref": "AC-01", "tags": []},
        ],
    }


def test_create_test_cycle_organizes_generated_assets():
    cycle = create_test_cycle(_state())

    assert cycle["name"] == "Sprint 24 - ABC-123 Validation"
    assert cycle["execution_type"] == "Smoke Testing"
    assert cycle["requirement"]["key"] == "ABC-123"
    assert cycle["executions"][0]["ac_ref"] == "AC-01"
    assert cycle["metrics"]["not_executed"] == 2
    assert cycle["readiness_summary"]["release_recommendation"] == "NOT READY"


def test_refresh_cycle_summary_tracks_failures_and_defects():
    cycle = create_test_cycle(_state())
    cycle["executions"][0].update({
        "status": "PASS",
        "defects": [],
    })
    cycle["executions"][1].update({
        "status": "FAIL",
        "execution_comments": "HTTP 500",
        "defects": [{"key": "BUG-456", "summary": "Login API fails"}],
    })

    refresh_cycle_summary(cycle, {"overall_coverage_pct": 100})

    assert cycle["metrics"]["executed"] == 2
    assert cycle["metrics"]["pass_rate_pct"] == 50.0
    assert cycle["metrics"]["defect_count"] == 1
    assert cycle["readiness_summary"]["release_recommendation"] == "NO GO"
    assert cycle["readiness_summary"]["failure_analysis"][0]["tc_id"] == "TC-002"
