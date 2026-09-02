"""
agents/requirement_agent.py
============================
Agent 1 — Requirement Agent

Responsibilities:
- Parse raw Jira story into a StructuredRequirementObject (SRO)
- Detect ambiguous or incomplete acceptance criteria
- Identify implicit assumptions and NFR hints
- Generate clarifying questions for the HITL gate
"""

from __future__ import annotations

import logging

from agents.base_agent import BaseAgent
from models.requirement import (
    AcceptanceCriterion,
    RiskLevel,
    StructuredRequirementObject,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a senior QA architect specialising in requirements analysis.
Your task is to parse a Jira user story and extract a structured requirement object.

RULES:
- Before deciding that clarification is needed, review all supplied Jira information:
    description, acceptance criteria, comments, attachment metadata, linked issues, labels,
    and any additional requirements documented in those sources.
- Extract every explicit acceptance criterion and give it a unique ID (AC-01, AC-02 ...).
- Flag any AC that is ambiguous, missing expected state, or uses vague language
  (e.g. "should work", "properly", "as expected").
- Identify non-functional requirement hints (performance, security, accessibility, SEO).
- Infer answers from the complete ticket context when possible.
- List clarifying questions only when information remains incomplete, ambiguous, or
    conflicting after the complete review. If the ticket is sufficient, return no questions.
- Assign an overall risk level: HIGH if safety/payment/auth involved, LOW if cosmetic/copy.

Return ONLY valid JSON matching this schema — no markdown, no explanation:
{
  "story_id": "<jira key>",
  "summary": "<story summary>",
  "component": "<component name or null>",
  "priority": "<priority>",
  "sprint": "<sprint name or null>",
  "acceptance_criteria": [
    {
      "id": "AC-01",
      "text": "<full AC text>",
      "is_ambiguous": true|false,
      "ambiguity_note": "<explanation or null>",
      "implicit_assumption": "<assumption or null>"
    }
  ],
  "nfr_hints": ["<nfr 1>", "..."],
  "domain_keywords": ["<keyword 1>", "..."],
  "clarifying_questions": ["<question 1>", "..."],
  "overall_risk": "HIGH|MEDIUM|LOW",
  "confidence_score": 0.0-1.0
}
"""

HUMAN_TEMPLATE = """\
Jira Story ID: {story_id}
Summary: {summary}
Component: {component}
Priority: {priority}
Sprint: {sprint}
Status: {status}

Description / Acceptance Criteria:
{description}

Comments:
{comments}

Attachments:
{attachments}

Related Issues:
{related_issues}

Labels:
{labels}
"""


class RequirementAgent(BaseAgent):
    agent_name = "requirement_agent"

    def run(self, state: dict) -> dict:
        return self._safe_run(state, self._execute)

    def _execute(self, state: dict) -> dict:
        raw = state.get("raw_story", {})
        logger.info("[RequirementAgent] Parsing story: %s", raw.get("key", "unknown"))

        # In mock mode, skip LLM call entirely
        if self.is_mock_mode:
            from core.mock_llm import MockLLM
            result = MockLLM()._mock_requirement_agent({"story_id": raw.get("key", "")})
        else:
            chain = self._build_chain(SYSTEM_PROMPT, HUMAN_TEMPLATE)
            result = chain.invoke({
                "story_id": raw.get("key", ""),
                "summary": raw.get("summary", ""),
                "component": raw.get("component", ""),
                "priority": raw.get("priority", ""),
                "sprint": raw.get("sprint", ""),
                "status": raw.get("status", ""),
                "description": raw.get("description", ""),
                "comments": raw.get("comments", []),
                "attachments": raw.get("attachments", []),
                "related_issues": raw.get("related_issues", []),
                "labels": raw.get("labels", []),
            })

        sro = StructuredRequirementObject(**result)

        # Surface ambiguities as HITL questions
        clarifying_questions = sro.clarifying_questions
        ambiguous_acs = [ac for ac in sro.acceptance_criteria if ac.is_ambiguous]
        for ac in ambiguous_acs:
            if ac.ambiguity_note:
                clarifying_questions.append(
                    f"[{ac.id}] {ac.ambiguity_note}"
                )

        logger.info(
            "[RequirementAgent] Extracted %d ACs, %d ambiguous, %d questions",
            len(sro.acceptance_criteria),
            len(ambiguous_acs),
            len(clarifying_questions),
        )

        return {
            "structured_requirement": sro.model_dump(),
            "ambiguities": clarifying_questions,
            "hitl_pending": (
                bool(clarifying_questions) and state.get("hitl_response") is None
            ),
        }
