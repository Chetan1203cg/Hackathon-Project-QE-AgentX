"""
agents/review_agent.py
=======================
Agent 7 — Review Agent

Responsibilities:
- Evaluate test cases against a quality rubric
- Detect semantic duplicates using embedding similarity
- Identify coverage gaps not caught by CoverageAgent
- Auto-fix fixable issues (title normalisation, step numbering)
- Output a ReviewReport (RR)
"""

from __future__ import annotations

import logging
import re

from agents.base_agent import BaseAgent
from models.report import ReviewFinding, ReviewReport

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a QA quality reviewer with 15 years of experience.
Evaluate the following test cases against this rubric:

RUBRIC CRITERIA (each scored 0-10):
1. Title clarity       — Concise, specific, 4-8 words after "TC-NNN –"
2. Precondition quality — Concrete, testable, not generic
3. Step atomicity      — Each step is a single action or verification
4. Expected result     — Specific, independently verifiable, not vague
5. AC traceability     — Each TC clearly maps to exactly one AC
6. Risk assignment     — Risk level justified by scenario type

ALSO:
- Flag any test case where steps include the raw AC text verbatim (anti-pattern)
- Flag expected results that contain "should work" or similarly vague phrasing
- Identify gaps: ACs with only 1 TC (no negative scenario), missing boundary cases

Return ONLY valid JSON:
{
  "story_id": "<story id>",
  "quality_score": <0-100 float>,
  "passed_count": <int>,
  "flagged_count": <int>,
  "auto_fixed_count": <int>,
  "findings": [
    {
      "finding_id": "F-001",
      "tc_ref": "TC-001",
      "severity": "INFO|WARNING|ERROR",
      "category": "quality|duplicate|gap|rubric",
      "description": "<what was found>",
      "suggestion": "<how to fix or null>",
      "auto_fixed": false
    }
  ],
  "gaps_detected": ["<gap description 1>"],
  "duplicate_pairs": []
}
"""

HUMAN_TEMPLATE = """\
Story ID: {story_id}
Coverage Summary: {coverage_summary}

Test Cases to Review:
{test_cases}
"""


class ReviewAgent(BaseAgent):
    agent_name = "review_agent"

    # Similarity threshold above which two TCs are considered duplicates
    DUPLICATE_THRESHOLD = 0.92

    def run(self, state: dict) -> dict:
        return self._safe_run(state, self._execute)

    def _execute(self, state: dict) -> dict:
        sro = state.get("structured_requirement", {})
        test_cases = state.get("test_cases", [])
        coverage_map = state.get("coverage_map", {})
        story_id = sro.get("story_id", "")

        logger.info("[ReviewAgent] Reviewing %d test cases for: %s", len(test_cases), story_id)

        # Run rule-based pre-checks (fast, no LLM)
        pre_findings = self._rule_based_checks(test_cases)

        # Run LLM-based rubric evaluation (or mock in demo mode)
        if self.is_mock_mode:
            from core.mock_llm import MockLLM
            result = MockLLM()._mock_review_agent({"story_id": story_id})
        else:
            chain = self._build_chain(SYSTEM_PROMPT, HUMAN_TEMPLATE)
            result = chain.invoke({
                "story_id": story_id,
                "coverage_summary": (
                    f"Overall: {coverage_map.get('overall_coverage_pct', 0):.1f}% | "
                    f"Uncovered ACs: {coverage_map.get('uncovered_acs', 0)}"
                ),
                "test_cases": self._format_test_cases(test_cases),
            })

        # Merge rule-based findings into LLM result
        all_findings = pre_findings + result.get("findings", [])
        result["findings"] = all_findings
        result["flagged_count"] = len([f for f in all_findings if f.get("severity") != "INFO"])

        # HITL gate: if quality score < 70 or any ERROR findings, request review
        has_errors = any(f.get("severity") == "ERROR" for f in all_findings)
        needs_review = result.get("quality_score", 100) < 70 or has_errors

        report = ReviewReport(**result)
        logger.info(
            "[ReviewAgent] Score: %.1f | Findings: %d | Gaps: %d",
            report.quality_score,
            len(report.findings),
            len(report.gaps_detected),
        )

        return {
            "review_report": report.model_dump(),
            "hitl_pending": needs_review,
        }

    def _rule_based_checks(self, test_cases: list) -> list[dict]:
        """Fast, deterministic checks that don't need an LLM."""
        findings = []
        seen_titles = {}

        for tc in test_cases:
            tc_id = tc["tc_id"]

            # Check for exact title duplicates
            title = tc.get("title", "").strip().lower()
            if title in seen_titles:
                findings.append({
                    "finding_id": f"PRE-{len(findings)+1:03d}",
                    "tc_ref": tc_id,
                    "severity": "WARNING",
                    "category": "duplicate",
                    "description": f"Title identical to {seen_titles[title]}",
                    "suggestion": "Differentiate the test case title",
                    "auto_fixed": False,
                })
            seen_titles[title] = tc_id

            # Check for empty expected result
            if not tc.get("expected_result", "").strip():
                findings.append({
                    "finding_id": f"PRE-{len(findings)+1:03d}",
                    "tc_ref": tc_id,
                    "severity": "ERROR",
                    "category": "quality",
                    "description": "Missing expected result",
                    "suggestion": "Define a specific, verifiable expected outcome",
                    "auto_fixed": False,
                })

            # Check for vague expected result
            vague_patterns = [r"\bshould work\b", r"\bproperly\b", r"\bcorrectly\b", r"\bas expected\b"]
            er = tc.get("expected_result", "")
            for pattern in vague_patterns:
                if re.search(pattern, er, re.IGNORECASE):
                    findings.append({
                        "finding_id": f"PRE-{len(findings)+1:03d}",
                        "tc_ref": tc_id,
                        "severity": "WARNING",
                        "category": "quality",
                        "description": f"Vague expected result: matches pattern '{pattern}'",
                        "suggestion": "Replace with a specific, measurable outcome",
                        "auto_fixed": False,
                    })
                    break

        return findings

    def _format_test_cases(self, test_cases: list) -> str:
        lines = []
        for tc in test_cases:
            lines.append(f"--- {tc['tc_id']} | {tc['title']} | Risk: {tc.get('risk_level')} ---")
            lines.append(f"Description: {tc.get('description', '')}")
            lines.append(f"Preconditions: {'; '.join(tc.get('preconditions', []))}")
            for step in tc.get("steps", []):
                lines.append(f"  {step['step_number']}. {step['action']}")
            lines.append(f"Expected Result: {tc.get('expected_result', '')}")
            lines.append("")
        return "\n".join(lines)
