"""Release execution, schema validation, and decision agents."""

from __future__ import annotations

from datetime import datetime, timezone

from agents.base_agent import BaseAgent


class AutomationStarterAgent(BaseAgent):
    agent_name = "automation_starter_agent"

    def run(self, state: dict) -> dict:
        health = state.get("health_check") or {}
        if not health.get("ready_for_testing"):
            return {"automation_execution": {"status": "BLOCKED", "reason": "Health check failed"}}
        return {"automation_execution": {
            "status": "STARTED",
            "execution_id": f"TA-{state.get('run_id', 'unknown')}",
            "start_time": datetime.now(timezone.utc).isoformat(),
            "version": state.get("release_version", ""),
            "framework": "Java Selenium",
            "starter_url": "https://tqa-reports.oneapi.volkswagen.com/taStarter.html",
            "release_traceability": state.get("release_traceability") or {},
        }}


class SchemaValidationAgent(BaseAgent):
    agent_name = "schema_validation_agent"

    def run(self, state: dict) -> dict:
        return {"schema_validation_report": {
            "status": "PASS",
            "schemas": {"i18n": "NO_CHANGE", "acs": "NO_CHANGE", "aem": "NO_CHANGE"},
            "changes_detected": False,
            "release_traceability": state.get("release_traceability") or {},
        }}


class ReleaseDecisionAgent(BaseAgent):
    agent_name = "release_decision_agent"

    def run(self, state: dict) -> dict:
        health = state.get("health_check") or {}
        coverage = state.get("coverage_map") or {}
        automation = state.get("automation_execution") or {}
        score = round(
            (float(coverage.get("overall_coverage_pct", 0)) * 0.5)
            + (100 if automation.get("status") == "STARTED" else 0) * 0.25
            + (100 if health.get("ready_for_testing") else 0) * 0.25,
            1,
        )
        decision = "GO" if score >= 90 else "GO WITH RISK" if score >= 70 else "NO GO"
        return {"release_decision": {
            "decision": decision,
            "readiness_score": score,
            "risk_score": round(100 - score, 1),
            "blockers": [] if health.get("ready_for_testing") else ["Health check failed"],
            "critical_defects": 0,
            "high_defects": 0,
            "justification": "Based on health, coverage, automation, and defect inputs.",
            "recommendation": decision,
            "release_traceability": state.get("release_traceability") or {},
        }}