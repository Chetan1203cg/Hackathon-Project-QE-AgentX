"""
tests/unit/test_requirement_agent.py
=====================================
Unit tests for RequirementAgent using mocked LLM responses.
Uses the real story fixture from data/NGWD6-50396_story.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agents.requirement_agent import RequirementAgent
from config.settings import Settings


FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "story_simple.json"

MOCK_LLM_RESPONSE = {
    "story_id": "NGWD6-50396",
    "summary": "S127 Feature Cluster Section - Update as per new design",
    "component": "CMS",
    "priority": "Major",
    "sprint": "CMS Sprint 273",
    "acceptance_criteria": [
        {
            "id": "AC-01",
            "text": "Named items, section match the NBD'26 specifications from FIGMA",
            "is_ambiguous": False,
            "ambiguity_note": None,
            "implicit_assumption": "NBD'26 FIGMA designs are available to the tester",
        },
        {
            "id": "AC-02",
            "text": "NBD changes are hidden behind the feature activation toggle",
            "is_ambiguous": True,
            "ambiguity_note": "Toggle behaviour when inactive is not specified",
            "implicit_assumption": None,
        },
    ],
    "nfr_hints": ["Storybook documentation update", "SysDoc update"],
    "domain_keywords": ["CMS", "NBD'26", "FIGMA", "feature toggle", "tablet view"],
    "clarifying_questions": [
        "What should happen when the feature toggle is disabled — should NBD'26 styles revert completely?"
    ],
    "overall_risk": "MEDIUM",
    "confidence_score": 0.88,
}


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
def raw_story():
    if FIXTURE_PATH.exists():
        return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    # Fallback minimal story
    return {
        "key": "NGWD6-50396",
        "summary": "S127 Feature Cluster Section update",
        "component": "CMS",
        "priority": "Major",
        "sprint": "CMS Sprint 273",
        "status": "Development Done",
        "description": "AC: Named items match FIGMA. NBD changes hidden behind toggle.",
    }


@pytest.mark.unit
def test_requirement_agent_returns_sro(settings, raw_story):
    """RequirementAgent should return a structured_requirement dict."""
    agent = RequirementAgent(settings)

    with patch.object(agent, "_build_chain") as mock_chain_builder:
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = MOCK_LLM_RESPONSE
        mock_chain_builder.return_value = mock_chain

        state = {"raw_story": raw_story, "errors": []}
        result = agent.run(state)

    assert "structured_requirement" in result
    sro = result["structured_requirement"]
    assert sro["story_id"] == "NGWD6-50396"
    assert len(sro["acceptance_criteria"]) == 2


@pytest.mark.unit
def test_requirement_agent_detects_ambiguities(settings, raw_story):
    """Agent should set hitl_pending=True when ambiguities are found."""
    agent = RequirementAgent(settings)

    with patch.object(agent, "_build_chain") as mock_chain_builder:
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = MOCK_LLM_RESPONSE
        mock_chain_builder.return_value = mock_chain

        state = {"raw_story": raw_story, "errors": []}
        result = agent.run(state)

    assert result["hitl_pending"] is True
    assert len(result["ambiguities"]) >= 1


@pytest.mark.unit
def test_requirement_agent_accepts_hitl_response(settings, raw_story):
    """Agent should not pause again after ambiguities have been answered."""
    agent = RequirementAgent(settings)

    with patch.object(agent, "_build_chain") as mock_chain_builder:
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = MOCK_LLM_RESPONSE
        mock_chain_builder.return_value = mock_chain

        state = {
            "raw_story": raw_story,
            "errors": [],
            "hitl_response": "Cover both feature toggle states.",
        }
        result = agent.run(state)

    assert result["hitl_pending"] is False
    assert len(result["ambiguities"]) >= 1


@pytest.mark.unit
def test_requirement_agent_accepts_blank_hitl_response(settings, raw_story):
    """An explicitly blank response means the ticket needs no added clarification."""
    agent = RequirementAgent(settings)

    with patch.object(agent, "_build_chain") as mock_chain_builder:
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = MOCK_LLM_RESPONSE
        mock_chain_builder.return_value = mock_chain

        state = {"raw_story": raw_story, "errors": [], "hitl_response": ""}
        result = agent.run(state)

    assert result["hitl_pending"] is False


@pytest.mark.unit
def test_requirement_agent_error_handling(settings):
    """Agent should append to errors dict on LLM failure, not raise."""
    agent = RequirementAgent(settings)

    with patch.object(agent, "_build_chain") as mock_chain_builder:
        mock_chain = MagicMock()
        mock_chain.invoke.side_effect = RuntimeError("LLM timeout")
        mock_chain_builder.return_value = mock_chain

        state = {"raw_story": {"key": "TEST-1"}, "errors": []}
        result = agent.run(state)

    assert "errors" in result
    assert any("LLM timeout" in e for e in result["errors"])
