"""Tests for user-facing API error formatting."""

from __future__ import annotations

import httpx

from ui.http_errors import format_api_error


def test_format_api_error_uses_backend_detail():
    response = httpx.Response(
        502,
        json={"detail": "Jira fetch failed: 404 Not Found"},
    )

    assert format_api_error(response) == (
        "API error (502): Jira fetch failed: 404 Not Found"
    )


def test_format_api_error_falls_back_to_response_text():
    response = httpx.Response(503, text="Service unavailable")

    assert format_api_error(response) == "API error (503): Service unavailable"