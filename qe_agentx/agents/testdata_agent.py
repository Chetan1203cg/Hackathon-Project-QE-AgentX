"""
agents/testdata_agent.py
=========================
Agent 4 — Test Data Agent

Responsibilities:
- For each test case, synthesise domain-aware test data sets
- Categories: valid, boundary, invalid, null_empty, special_chars
- Use domain keywords and AC context to generate realistic values
- Flag datasets that require environment provisioning
"""

from __future__ import annotations

import logging

from agents.base_agent import BaseAgent
from models.testdata import TestDataManifest

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a test data engineer specialising in equivalence partitioning and boundary value analysis.

For each test case provided, generate test data sets covering these categories:
- valid:         well-formed, in-range input that should succeed
- boundary:      values at the exact edge of valid ranges (min, max, min-1, max+1)
- invalid:       malformed, out-of-range, or logically incorrect input
- null_empty:    null, empty string, zero, missing required fields
- special_chars: SQL injection, XSS payloads, unicode, emoji (for string fields)

RULES:
- Derive field names and value constraints from the test case description and preconditions.
- Keep values realistic for the domain (automotive CMS, web content management).
- Mark requires_provisioning=true if the dataset needs DB records, user accounts, or env config.
- Dataset IDs: DS-001, DS-002 ... (global counter across all TCs).

Return ONLY valid JSON — no markdown:
{
  "story_id": "<story id>",
  "datasets": [
    {
      "dataset_id": "DS-001",
      "tc_ref": "TC-001",
      "category": "valid|boundary|invalid|null_empty|special_chars",
      "description": "<what this dataset tests>",
      "data": {
        "<field_name>": "<value>",
        "...": "..."
      },
      "notes": "<any provisioning or setup notes or null>",
      "requires_provisioning": false
    }
  ]
}
"""

HUMAN_TEMPLATE = """\
Story ID: {story_id}
Domain Context: {domain_keywords}

Test Cases requiring data:
{test_cases_summary}
"""


class TestDataAgent(BaseAgent):
    agent_name = "testdata_agent"

    def run(self, state: dict) -> dict:
        return self._safe_run(state, self._execute)

    def _execute(self, state: dict) -> dict:
        sro = state.get("structured_requirement", {})
        test_cases = state.get("test_cases", [])
        logger.info(
            "[TestDataAgent] Synthesising data for %d test cases", len(test_cases)
        )

        # In mock mode, skip LLM call entirely
        if self.is_mock_mode:
            from core.mock_llm import MockLLM
            result = MockLLM()._mock_testdata_agent({"story_id": sro.get("story_id", "")})
        else:
            tc_summary = self._format_test_cases(test_cases)

            chain = self._build_chain(SYSTEM_PROMPT, HUMAN_TEMPLATE)

            result = chain.invoke({
                "story_id": sro.get("story_id", ""),
                "domain_keywords": ", ".join(sro.get("domain_keywords", [])),
                "test_cases_summary": tc_summary,
            })

        manifest = TestDataManifest(**result)

        logger.info(
            "[TestDataAgent] Generated %d data sets across %d TCs",
            len(manifest.datasets),
            len(test_cases),
        )

        return {"test_data": manifest.model_dump()}

    def _format_test_cases(self, test_cases: list) -> str:
        lines = []
        for tc in test_cases:
            lines.append(f"TC ID: {tc['tc_id']} | {tc['title']}")
            lines.append(f"  Description: {tc['description']}")
            if tc.get("preconditions"):
                lines.append(f"  Preconditions: {'; '.join(tc['preconditions'])}")
            lines.append("")
        return "\n".join(lines)
