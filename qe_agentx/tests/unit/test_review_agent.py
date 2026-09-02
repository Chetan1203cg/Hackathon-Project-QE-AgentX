"""
tests/unit/test_review_agent.py
=================================
Unit tests for ReviewAgent rule-based checks (no LLM needed).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from agents.review_agent import ReviewAgent
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


MOCK_LLM_REVIEW = {
    "story_id": "TEST-001",
    "quality_score": 85.0,
    "passed_count": 2,
    "flagged_count": 0,
    "auto_fixed_count": 0,
    "findings": [],
    "gaps_detected": [],
    "duplicate_pairs": [],
}


def _make_state(test_cases: list) -> dict:
    return {
        "structured_requirement": {"story_id": "TEST-001"},
        "test_cases": test_cases,
        "coverage_map": {"overall_coverage_pct": 80.0, "uncovered_acs": 0},
        "errors": [],
    }


@pytest.mark.unit
def test_detects_empty_expected_result(settings):
    state = _make_state([
        {
            "tc_id": "TC-001",
            "title": "TC-001 – Login Happy Path",
            "description": "Test login",
            "preconditions": ["User exists"],
            "steps": [{"step_number": 1, "action": "Click login", "expected_result": None}],
            "expected_result": "",  # ← empty
            "tags": ["regression"],
            "risk_level": "HIGH",
        }
    ])
    agent = ReviewAgent(settings)
    with patch.object(agent, "_build_chain") as mock_chain_builder:
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = MOCK_LLM_REVIEW
        mock_chain_builder.return_value = mock_chain
        result = agent.run(state)

    findings = result["review_report"]["findings"]
    error_findings = [f for f in findings if f["severity"] == "ERROR"]
    assert any("Missing expected result" in f["description"] for f in error_findings)


@pytest.mark.unit
def test_detects_vague_expected_result(settings):
    state = _make_state([
        {
            "tc_id": "TC-001",
            "title": "TC-001 – Submit Form",
            "description": "Test form submission",
            "preconditions": [],
            "steps": [],
            "expected_result": "Form should work correctly",  # ← vague
            "tags": [],
            "risk_level": "LOW",
        }
    ])
    agent = ReviewAgent(settings)
    with patch.object(agent, "_build_chain") as mock_chain_builder:
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = MOCK_LLM_REVIEW
        mock_chain_builder.return_value = mock_chain
        result = agent.run(state)

    findings = result["review_report"]["findings"]
    assert any("Vague expected result" in f["description"] for f in findings)


@pytest.mark.unit
def test_detects_duplicate_titles(settings):
    dupe_tc = {
        "tc_id": "TC-002",
        "title": "tc-001 – login happy path",  # same as TC-001 after lower()
        "description": "Another test",
        "preconditions": [],
        "steps": [],
        "expected_result": "User is logged in",
        "tags": [],
        "risk_level": "LOW",
    }
    state = _make_state([
        {
            "tc_id": "TC-001",
            "title": "TC-001 – Login Happy Path",
            "description": "Test login",
            "preconditions": [],
            "steps": [],
            "expected_result": "User is logged in",
            "tags": [],
            "risk_level": "HIGH",
        },
        dupe_tc,
    ])
    agent = ReviewAgent(settings)
    with patch.object(agent, "_build_chain") as mock_chain_builder:
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = MOCK_LLM_REVIEW
        mock_chain_builder.return_value = mock_chain
        result = agent.run(state)

    findings = result["review_report"]["findings"]
    assert any("duplicate" in f["category"] for f in findings)
