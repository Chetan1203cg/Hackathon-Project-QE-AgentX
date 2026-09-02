"""
agents/testcase_agent.py
=========================
Agent 3 — Test Case Agent

Responsibilities:
- Generate atomic, step-level test cases for each Scenario Behaviour Tree node
- Produce both structured steps and optional Gherkin representation
- Assign risk scores and tags
- Output a complete TestCaseSet (TCS)
"""

from __future__ import annotations

import logging

from agents.base_agent import BaseAgent
from models.testcase import TestCase, TestCaseSet, TestStep, TestCaseStatus

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a senior QA engineer generating detailed, executable test cases.

RULES:
- One test case per scenario node (do NOT merge multiple nodes into one TC).
- Title format: "TC-NNN – <concise 4-6 word headline>"
- Preconditions must be concrete and testable (not "system is running").
- Steps must be atomic user actions or system observations.
- Steps that verify outcomes must start with "Verify that".
- Expected result must be specific and independently verifiable.
- Generate Gherkin (Given/When/Then) alongside the structured format.
- Tags: derive from flow_type and domain (e.g. "regression", "smoke", "negative", "boundary").

Return ONLY valid JSON — no markdown, no explanation:
{
  "story_id": "<story id>",
  "total": <int>,
  "high_risk_count": <int>,
  "medium_risk_count": <int>,
  "low_risk_count": <int>,
  "test_cases": [
    {
      "tc_id": "TC-001",
      "scenario_node_ref": "SN-001",
      "ac_ref": "AC-01",
      "title": "TC-001 – <Short Title>",
      "description": "<what this TC validates>",
      "preconditions": ["<precondition 1>"],
      "steps": [
        {"step_number": 1, "action": "<user action>", "expected_result": "<or null>"},
        {"step_number": 2, "action": "Verify that ...", "expected_result": "<observable outcome>"}
      ],
      "expected_result": "<overall expected outcome>",
      "risk_level": "HIGH|MEDIUM|LOW",
      "tags": ["regression", "smoke"],
      "status": "DRAFT",
      "gherkin": "Given ...\\nWhen ...\\nThen ..."
    }
  ]
}
"""

HUMAN_TEMPLATE = """\
Story ID: {story_id}
Story Summary: {summary}

Generate test cases for ALL of the following scenario nodes:

{scenario_nodes}
"""


class TestCaseAgent(BaseAgent):
    agent_name = "testcase_agent"

    def run(self, state: dict) -> dict:
        return self._safe_run(state, self._execute)

    def _execute(self, state: dict) -> dict:
        sro = state.get("structured_requirement", {})
        sbt = state.get("behaviour_tree", {})
        logger.info("[TestCaseAgent] Generating test cases for: %s", sro.get("story_id"))

        # In mock mode, skip LLM call entirely
        if self.is_mock_mode:
            from core.mock_llm import MockLLM
            result = MockLLM()._mock_testcase_agent({"story_id": sro.get("story_id", "")})
        else:
            # Flatten all nodes for the prompt
            nodes_text = self._format_nodes(sbt.get("root_nodes", []))

            chain = self._build_chain(SYSTEM_PROMPT, HUMAN_TEMPLATE)

            result = chain.invoke({
                "story_id": sro.get("story_id", ""),
                "summary": sro.get("summary", ""),
                "scenario_nodes": nodes_text,
            })

        tcs = TestCaseSet(**result)

        # Enforce the VW viewport policy even when an LLM omits metadata.
        for test_case in tcs.test_cases:
            test_case.browser_coverage = ["Chrome", "Edge", "Firefox"]
            test_case.mobile_coverage = ["Android Chrome", "iPhone Safari"]
            test_case.evidence_required = ["Screenshot", "Video"]

        logger.info(
            "[TestCaseAgent] Generated %d test cases (%d HIGH, %d MEDIUM, %d LOW risk)",
            tcs.total,
            tcs.high_risk_count,
            tcs.medium_risk_count,
            tcs.low_risk_count,
        )

        release_traceability = state.get("release_traceability") or {}
        test_cases = []
        for test_case in tcs.test_cases:
            test_case_data = test_case.model_dump()
            test_case_data["release_traceability"] = release_traceability
            test_case_data["test_evidence"] = {
                "required": test_case_data.get("evidence_required", []),
                "release_traceability": release_traceability,
            }
            test_cases.append(test_case_data)

        behaviour_tree = state.get("behaviour_tree") or {}
        behaviour_tree["release_traceability"] = release_traceability

        return {"test_cases": test_cases, "behaviour_tree": behaviour_tree}

    def _format_nodes(self, nodes: list, indent: int = 0) -> str:
        lines = []
        prefix = "  " * indent
        for node in nodes:
            lines.append(
                f"{prefix}Node: {node['node_id']} ({node['flow_type']}) | AC: {node['ac_ref']} | Risk: {node['risk_level']}"
            )
            lines.append(f"{prefix}  Title: {node['title']}")
            lines.append(f"{prefix}  Description: {node['description']}")
            if node.get("precondition"):
                lines.append(f"{prefix}  Precondition: {node['precondition']}")
            if node.get("expected_state"):
                lines.append(f"{prefix}  Expected State: {node['expected_state']}")
            lines.append("")
            if node.get("children"):
                lines.append(self._format_nodes(node["children"], indent + 1))
        return "\n".join(lines)
