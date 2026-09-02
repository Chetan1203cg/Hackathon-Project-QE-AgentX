"""
tests/unit/test_coverage_agent.py
===================================
Unit tests for CoverageAgent (no LLM — pure algorithmic logic).
"""

from __future__ import annotations

import pytest

from agents.coverage_agent import CoverageAgent
from config.settings import Settings


@pytest.fixture
def settings():
    return Settings(
        azure_openai_endpoint="https://mock.openai.azure.com/",
        azure_openai_key="mock-key",
        jira_base_url="https://mock.atlassian.net",
        jira_email="test@test.com",
        jira_api_token="mock-token",
    )


@pytest.fixture
def state_full_coverage():
    return {
        "structured_requirement": {
            "story_id": "TEST-001",
            "acceptance_criteria": [
                {"id": "AC-01", "text": "User can log in with valid credentials"},
                {"id": "AC-02", "text": "User sees error on invalid credentials"},
            ],
        },
        "test_cases": [
            {"tc_id": "TC-001", "ac_ref": "AC-01", "tags": ["happy_path", "regression"], "risk_level": "HIGH"},
            {"tc_id": "TC-002", "ac_ref": "AC-01", "tags": ["negative", "boundary"], "risk_level": "MEDIUM"},
            {"tc_id": "TC-003", "ac_ref": "AC-02", "tags": ["negative", "happy_path", "boundary"], "risk_level": "HIGH"},
        ],
        "errors": [],
    }


@pytest.fixture
def state_partial_coverage():
    return {
        "structured_requirement": {
            "story_id": "TEST-002",
            "acceptance_criteria": [
                {"id": "AC-01", "text": "Feature works correctly"},
                {"id": "AC-02", "text": "Feature handles errors"},
            ],
        },
        "test_cases": [
            {"tc_id": "TC-001", "ac_ref": "AC-01", "tags": ["happy_path"], "risk_level": "MEDIUM"},
            # AC-02 has no test cases
        ],
        "errors": [],
    }


@pytest.mark.unit
def test_full_coverage_calculation(settings, state_full_coverage):
    agent = CoverageAgent(settings)
    result = agent.run(state_full_coverage)

    assert "coverage_map" in result
    cm = result["coverage_map"]
    assert cm["overall_coverage_pct"] > 0
    assert cm["total_acs"] == 2
    assert cm["uncovered_acs"] == 0


@pytest.mark.unit
def test_partial_coverage_detects_uncovered_ac(settings, state_partial_coverage):
    agent = CoverageAgent(settings)
    result = agent.run(state_partial_coverage)

    cm = result["coverage_map"]
    assert cm["uncovered_acs"] == 1
    assert cm["overall_coverage_pct"] < 100.0


@pytest.mark.unit
def test_coverage_map_has_gap_notes_for_missing_flows(settings, state_partial_coverage):
    agent = CoverageAgent(settings)
    result = agent.run(state_partial_coverage)

    cm = result["coverage_map"]
    ac01_coverage = next(a for a in cm["ac_coverage"] if a["ac_id"] == "AC-01")
    # AC-01 has only happy_path — negative and boundary are missing
    assert len(ac01_coverage["gap_notes"]) > 0


@pytest.mark.unit
def test_empty_story_returns_zero_coverage(settings):
    agent = CoverageAgent(settings)
    state = {
        "structured_requirement": {"story_id": "TEST-EMPTY", "acceptance_criteria": []},
        "test_cases": [],
        "errors": [],
    }
    result = agent.run(state)
    assert result["coverage_map"]["overall_coverage_pct"] == 0.0
