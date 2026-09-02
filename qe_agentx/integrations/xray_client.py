"""
integrations/xray_client.py
============================
Xray Cloud REST API client for test case export and RTM linking.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from config.settings import Settings

logger = logging.getLogger(__name__)


class XrayClient:
    """Xray Cloud API v2 client (OAuth2 client credentials flow)."""

    TOKEN_URL = "https://xray.cloud.getxray.app/api/v2/authenticate"

    def __init__(self, settings: Settings):
        self._client_id = settings.xray_client_id
        self._client_secret = settings.xray_client_secret
        self._base_url = settings.xray_base_url.rstrip("/")
        self._token: str | None = None
        self._http = httpx.Client(timeout=30.0)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def export_test_cases(self, test_cases: list[dict], project_key: str) -> list[str]:
        """
        Create test cases in Xray and return a list of created issue keys.
        test_cases: list of TestCase.model_dump() dicts
        """
        token = self._get_token()
        created_keys: list[str] = []

        for tc in test_cases:
            payload = self._to_xray_format(tc, project_key)
            resp = self._http.post(
                f"{self._base_url}/api/v2/import/test",
                json=payload,
                headers=self._auth_headers(token),
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                key = data.get("key", "")
                created_keys.append(key)
                logger.info("[XrayClient] Created test: %s → %s", tc.get("tc_id"), key)
            else:
                logger.warning(
                    "[XrayClient] Failed to create %s: %s %s",
                    tc.get("tc_id"), resp.status_code, resp.text,
                )

        return created_keys

    def link_to_requirement(self, test_key: str, requirement_key: str) -> None:
        """Link a test issue to its Jira requirement issue."""
        token = self._get_token()
        payload = {"update": {"issuelinks": [{"add": {"type": {"name": "Tests"}, "outwardIssue": {"key": requirement_key}}}]}}
        resp = self._http.put(
            f"{self._base_url}/api/v2/issues/{test_key}",
            json=payload,
            headers=self._auth_headers(token),
        )
        if resp.status_code not in (200, 204):
            logger.warning("[XrayClient] Link failed: %s → %s", test_key, requirement_key)

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    def _get_token(self) -> str:
        if self._token:
            return self._token
        resp = self._http.post(
            self.TOKEN_URL,
            json={"client_id": self._client_id, "client_secret": self._client_secret},
        )
        resp.raise_for_status()
        self._token = resp.json()
        return self._token  # type: ignore[return-value]

    def _auth_headers(self, token: str) -> dict:
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def _to_xray_format(self, tc: dict, project_key: str) -> dict[str, Any]:
        """Convert internal TestCase dict to Xray import format."""
        steps = []
        for step in tc.get("steps", []):
            steps.append({
                "action": step.get("action", ""),
                "result": step.get("expected_result") or "",
                "data": "",
            })

        return {
            "fields": {
                "project": {"key": project_key},
                "summary": tc.get("title", ""),
                "description": tc.get("description", ""),
                "issuetype": {"name": "Test"},
                "priority": {"name": tc.get("risk_level", "Medium").title()},
                "labels": tc.get("tags", []),
            },
            "xray_test_type": "Manual",
            "steps": steps,
        }

    def close(self) -> None:
        self._http.close()
