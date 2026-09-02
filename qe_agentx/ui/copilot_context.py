"""Build portable troubleshooting context for Copilot experiences."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote, urlencode

MICROSOFT_COPILOT_URL = "https://copilot.microsoft.com/"
VSCODE_COPILOT_CHAT_URL = "vscode://GitHub.Copilot-Chat/chat"


def build_copilot_context(
    *,
    error: str,
    jira_key: str,
    release_version: str,
    target_environment: str,
    run_id: str | None = None,
    jira_context: dict[str, Any] | None = None,
    status_data: dict[str, Any] | None = None,
    artifacts: dict[str, Any] | None = None,
) -> str:
    """Create a Markdown troubleshooting prompt from all available run context."""
    jira_context = jira_context or {}
    status_data = status_data or {}
    artifacts = artifacts or {}

    lines = [
        "Help troubleshoot this QE AgentX test-generation failure.",
        "",
        "## Error details",
        error,
        "",
        "## Jira context",
        f"- Issue key: {jira_key or 'Unavailable'}",
        f"- Summary: {jira_context.get('summary') or 'Unavailable'}",
        f"- Description: {jira_context.get('description') or 'Unavailable'}",
        "- Acceptance criteria:",
        _format_value(jira_context.get("acceptance_criteria")),
        "",
        "## Environment",
        f"- Release version: {release_version or 'Unavailable'}",
        f"- Target environment: {target_environment or 'Unavailable'}",
        f"- Run ID: {run_id or 'Unavailable'}",
        f"- Pipeline status: {status_data.get('status') or 'Unavailable'}",
        f"- Current stage: {status_data.get('current_stage') or 'Unavailable'}",
        "",
        "## Error logs and stack trace",
        _format_value(status_data.get("errors")) if status_data.get("errors") else error,
        "",
        "## Generated test artifacts",
        _format_value(artifacts) if artifacts else "Unavailable because generation did not complete.",
    ]
    return "\n".join(lines)


def microsoft_copilot_url(context: str) -> str:
    """Return Microsoft Copilot with the troubleshooting prompt prepopulated."""
    return f"{MICROSOFT_COPILOT_URL}?{urlencode({'q': context})}"


def vscode_copilot_url(context: str) -> str:
    """Return the VS Code URI that opens GitHub Copilot Chat with a prompt."""
    return f"{VSCODE_COPILOT_CHAT_URL}?prompt={quote(context, safe='')}"


def _format_value(value: Any) -> str:
    if value in (None, "", []):
        return "Unavailable"
    if isinstance(value, str):
        return value
    return json.dumps(value, indent=2, default=str)