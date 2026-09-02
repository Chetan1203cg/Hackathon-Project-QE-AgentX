"""Helpers for presenting API failures in the Streamlit UI."""

from __future__ import annotations

import httpx


def format_api_error(response: httpx.Response) -> str:
    """Return the backend error detail with a concise HTTP status prefix."""
    try:
        payload = response.json()
    except ValueError:
        payload = None

    detail = payload.get("detail") if isinstance(payload, dict) else None
    if not detail:
        detail = response.text.strip() or response.reason_phrase

    return f"API error ({response.status_code}): {detail}"