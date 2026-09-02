"""Tests for portable Copilot troubleshooting context."""

from __future__ import annotations

from urllib.parse import parse_qs, unquote, urlparse

from ui.copilot_context import (
    build_copilot_context,
    microsoft_copilot_url,
    vscode_copilot_url,
)


def test_build_copilot_context_includes_available_jira_and_run_data():
    context = build_copilot_context(
        error="Jira fetch failed: 403 Forbidden",
        jira_key="NGWD6-50396",
        release_version="Version_V2026.09.01",
        target_environment="test",
        run_id="run-123",
        jira_context={
            "summary": "Feature cluster update",
            "description": "Update component styling.",
            "acceptance_criteria": ["Matches FIGMA"],
        },
        status_data={"status": "failed", "current_stage": "Analysing Requirements"},
        artifacts={"test_cases": [{"id": "TC-001"}]},
    )

    assert "NGWD6-50396" in context
    assert "Feature cluster update" in context
    assert "Matches FIGMA" in context
    assert "Version_V2026.09.01" in context
    assert "TC-001" in context


def test_copilot_urls_preserve_encoded_context():
    context = "Error: Jira key NGWD6-50396 & environment=test"

    microsoft_query = parse_qs(urlparse(microsoft_copilot_url(context)).query)
    vscode_prompt = parse_qs(urlparse(vscode_copilot_url(context)).query)["prompt"][0]

    assert microsoft_query["q"] == [context]
    assert unquote(vscode_prompt) == context