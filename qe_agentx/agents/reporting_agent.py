"""
agents/reporting_agent.py
==========================
Agent 8 — Reporting Agent

Responsibilities:
- Compose executive summary and detailed QA report
- Assemble the Final Report Bundle (FRB)
- Trigger all export formats
- Write test cases back to Xray/Jira via integration clients
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from agents.base_agent import BaseAgent
from models.report import FinalReportBundle, ReviewReport
from models.testcase import TestCaseSet
from models.testdata import TestDataManifest
from models.coverage import CoverageMap
from models.rtm import RTMArtefact

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a QA engineering lead writing a concise executive summary for a test design report.

Write a professional 3-4 sentence summary covering:
1. What story was analysed and its risk level
2. How many test cases were generated and at what coverage percentage
3. Key quality findings or gaps
4. Recommendation: ready for execution or needs refinement

Keep it factual, under 100 words. No bullet points. Plain prose.

Return ONLY valid JSON:
{"executive_summary": "<prose summary>", "recommendations": ["<rec 1>", "<rec 2>"]}
"""

HUMAN_TEMPLATE = """\
Story: {story_id} — {summary}
Risk: {risk_level}
Test Cases: {tc_count} ({high_risk} HIGH, {medium_risk} MEDIUM, {low_risk} LOW risk)
Coverage: {coverage_pct}% ({covered} covered, {partial} partial, {uncovered} uncovered ACs)
Quality Score: {quality_score}/100
Gaps Detected: {gaps}
Findings: {findings_count} ({errors} errors, {warnings} warnings)
"""


class ReportingAgent(BaseAgent):
    agent_name = "reporting_agent"

    def run(self, state: dict) -> dict:
        return self._safe_run(state, self._execute)

    def _execute(self, state: dict) -> dict:
        sro = state.get("structured_requirement", {})
        test_cases_raw = state.get("test_cases", [])
        test_data_raw = state.get("test_data", {})
        coverage_raw = state.get("coverage_map", {})
        rtm_raw = state.get("rtm", {})
        review_raw = state.get("review_report", {})
        story_id = sro.get("story_id", "")
        run_id = state.get("run_id", str(uuid.uuid4()))

        logger.info("[ReportingAgent] Composing final report for: %s", story_id)

        findings = review_raw.get("findings", [])
        errors_count = sum(1 for f in findings if f.get("severity") == "ERROR")
        warnings_count = sum(1 for f in findings if f.get("severity") == "WARNING")

        # Generate summary (or use mock in demo mode)
        if self.is_mock_mode:
            from core.mock_llm import MockLLM
            summary_result = MockLLM()._mock_reporting_agent({"story_id": story_id})
        else:
            chain = self._build_chain(SYSTEM_PROMPT, HUMAN_TEMPLATE)
            summary_result = chain.invoke({
            "story_id": story_id,
            "summary": sro.get("summary", ""),
            "risk_level": sro.get("overall_risk", "MEDIUM"),
            "tc_count": len(test_cases_raw),
            "high_risk": sum(1 for tc in test_cases_raw if tc.get("risk_level") == "HIGH"),
            "medium_risk": sum(1 for tc in test_cases_raw if tc.get("risk_level") == "MEDIUM"),
            "low_risk": sum(1 for tc in test_cases_raw if tc.get("risk_level") == "LOW"),
            "coverage_pct": coverage_raw.get("overall_coverage_pct", 0),
            "covered": coverage_raw.get("covered_acs", 0),
            "partial": coverage_raw.get("partially_covered_acs", 0),
            "uncovered": coverage_raw.get("uncovered_acs", 0),
            "quality_score": review_raw.get("quality_score", 0),
            "gaps": "; ".join(review_raw.get("gaps_detected", [])[:3]) or "None",
            "findings_count": len(findings),
            "errors": errors_count,
            "warnings": warnings_count,
        })

        tcs = TestCaseSet(
            story_id=story_id,
            total=len(test_cases_raw),
            test_cases=test_cases_raw,
        )

        frb = FinalReportBundle(
            run_id=run_id,
            story_id=story_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            test_case_set=tcs,
            test_data_manifest=TestDataManifest(**test_data_raw) if test_data_raw else None,
            coverage_map=CoverageMap(**coverage_raw) if coverage_raw else None,
            rtm=RTMArtefact(**rtm_raw) if rtm_raw else None,
            review_report=ReviewReport(**review_raw) if review_raw else None,
            executive_summary=summary_result.get("executive_summary", ""),
            recommendations=summary_result.get("recommendations", []),
            key_metrics={
                "test_cases_generated": len(test_cases_raw),
                "coverage_pct": coverage_raw.get("overall_coverage_pct", 0),
                "quality_score": review_raw.get("quality_score", 0),
                "gaps_detected": len(review_raw.get("gaps_detected", [])),
                "rtm_rows": rtm_raw.get("total_rows", 0),
            },
        )

        logger.info("[ReportingAgent] Final report bundle assembled for run: %s", run_id)
        final_report = frb.model_dump()
        final_report["release_traceability"] = state.get("release_traceability") or {}
        return {"final_report": final_report}
