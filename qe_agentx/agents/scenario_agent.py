"""
agents/scenario_agent.py
=========================
Agent 2 — Scenario Agent

Responsibilities:
- Build a Scenario Behaviour Tree (SBT) from the SRO
- Cover: happy paths, alternate flows, boundary conditions,
  negative scenarios, and NFR-driven scenarios
- Each tree node maps to exactly one AC
"""

from __future__ import annotations

import json
import logging

from agents.base_agent import BaseAgent
from models.scenario import ScenarioBehaviourTree

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a senior QA architect specialising in test scenario design.
Given a structured requirement object, build a behaviour tree of test scenarios.

COVERAGE RULES (minimum per story):
- At least 1 happy path per acceptance criterion
- At least 1 alternate flow per AC with conditional logic
- At least 1 boundary condition per AC with numeric or length constraints
- At least 1 negative scenario per AC (invalid input, missing data, error state)
- NFR scenarios for any performance, security, or accessibility hints

FLOW TYPE VALUES: happy_path | alternate_flow | boundary | negative | nfr
RISK LEVEL VALUES: HIGH | MEDIUM | LOW

Return ONLY valid JSON — no markdown:
{
  "story_id": "<story id>",
  "total_nodes": <int>,
  "happy_path_count": <int>,
  "alternate_flow_count": <int>,
  "boundary_count": <int>,
  "negative_count": <int>,
  "nfr_count": <int>,
  "root_nodes": [
    {
      "node_id": "SN-001",
      "ac_ref": "AC-01",
      "flow_type": "happy_path",
      "title": "<short scenario title>",
      "description": "<what this scenario tests>",
      "precondition": "<precondition or null>",
      "trigger_condition": "<what triggers this flow or null>",
      "expected_state": "<expected system state after scenario>",
      "risk_level": "HIGH|MEDIUM|LOW",
      "children": []
    }
  ]
}
"""

HUMAN_TEMPLATE = """\
Story ID: {story_id}
Summary: {summary}

Acceptance Criteria:
{acceptance_criteria}

NFR Hints: {nfr_hints}
Domain Keywords: {domain_keywords}
HITL Clarifications received: {hitl_response}
"""


class ScenarioAgent(BaseAgent):
    agent_name = "scenario_agent"

    def run(self, state: dict) -> dict:
        return self._safe_run(state, self._execute)

    def _execute(self, state: dict) -> dict:
        sro = state.get("structured_requirement", {})
        logger.info("[ScenarioAgent] Building behaviour tree for: %s", sro.get("story_id"))

        # In mock mode, skip LLM call entirely
        if self.is_mock_mode:
            from core.mock_llm import MockLLM
            result = MockLLM()._mock_scenario_agent({"story_id": sro.get("story_id", "")})
        else:
            # Format ACs for prompt
            acs_text = "\n".join(
                f"  {ac['id']}: {ac['text']}"
                + (f"\n    [NOTE: {ac['ambiguity_note']}]" if ac.get("ambiguity_note") else "")
                for ac in sro.get("acceptance_criteria", [])
            )

            chain = self._build_chain(SYSTEM_PROMPT, HUMAN_TEMPLATE)

            result = chain.invoke({
                "story_id": sro.get("story_id", ""),
                "summary": sro.get("summary", ""),
                "acceptance_criteria": acs_text,
                "nfr_hints": ", ".join(sro.get("nfr_hints", [])),
                "domain_keywords": ", ".join(sro.get("domain_keywords", [])),
                "hitl_response": state.get("hitl_response") or "None",
            })

        sbt = ScenarioBehaviourTree(**result)

        logger.info(
            "[ScenarioAgent] Tree built: %d nodes (%d happy, %d alt, %d boundary, %d negative, %d nfr)",
            sbt.total_nodes,
            sbt.happy_path_count,
            sbt.alternate_flow_count,
            sbt.boundary_count,
            sbt.negative_count,
            sbt.nfr_count,
        )

        return {"behaviour_tree": sbt.model_dump()}
