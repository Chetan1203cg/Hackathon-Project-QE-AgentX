"""Build deterministic enterprise coverage view data from pipeline artifacts."""

from __future__ import annotations


def coverage_status(score: float) -> str:
    if score >= 90:
        return "Covered"
    if score > 0:
        return "Partial"
    return "Uncovered"


def coverage_badge(status: str) -> str:
    colors = {"Covered": "green", "Partial": "orange", "Uncovered": "red"}
    return f":{colors.get(status, 'gray')}-badge[{status}]"


def jira_status_badge(status: str) -> str:
    normalized = str(status or "Unknown").strip()
    lowered = normalized.lower()
    if lowered in {"done", "closed", "resolved", "complete", "completed"}:
        color = "green"
    elif lowered in {"blocked", "failed", "rejected"}:
        color = "red"
    elif lowered in {"in progress", "active", "pending", "open"}:
        color = "orange"
    else:
        color = "gray"
    return f":{color}-badge[{normalized}]"


def risk_level(coverage: dict, review: dict, cycle: dict) -> str:
    readiness = cycle.get("readiness_summary") or {}
    if readiness.get("risk_assessment"):
        return str(readiness["risk_assessment"]).title()
    error_count = sum(
        finding.get("severity") == "ERROR" for finding in review.get("findings", [])
    )
    if error_count or coverage.get("uncovered_acs", 0):
        return "High"
    if coverage.get("partially_covered_acs", 0) or review.get("flagged_count", 0):
        return "Medium"
    return "Low"


def traceability_rows(coverage: dict, test_cases: list[dict]) -> list[dict]:
    risk_by_ac: dict[str, str] = {}
    for test_case in test_cases:
        ac_ref = test_case.get("ac_ref", "")
        if test_case.get("risk_level") == "HIGH":
            risk_by_ac[ac_ref] = "High"
        elif ac_ref not in risk_by_ac:
            risk_by_ac[ac_ref] = str(test_case.get("risk_level", "Medium")).title()

    rows = []
    for item in coverage.get("ac_coverage", []):
        percentage = round(float(item.get("coverage_score", 0)) * 100, 1)
        status = coverage_status(percentage)
        rows.append({
            "Requirement ID": item.get("ac_id", ""),
            "Requirement": item.get("ac_text", ""),
            "Coverage": percentage,
            "Tests": len(item.get("covered_by", [])),
            "Test cases": ", ".join(item.get("covered_by", [])) or "None",
            "Risk": risk_by_ac.get(item.get("ac_id", ""), "Medium"),
            "Status": coverage_badge(status),
            "Gap notes": " ".join(item.get("gap_notes", [])),
        })
    return rows


def recommendation_rows(final_report: dict, review: dict) -> list[dict]:
    rows = []
    for finding in review.get("findings", []):
        if not finding.get("suggestion"):
            continue
        severity = finding.get("severity", "INFO")
        rows.append({
            "Priority": "High" if severity == "ERROR" else "Medium" if severity == "WARNING" else "Low",
            "Recommendation": finding["suggestion"],
            "Source": finding.get("category", "AgentX review"),
        })
    for recommendation in final_report.get("recommendations", []):
        if recommendation not in {row["Recommendation"] for row in rows}:
            rows.append({"Priority": "Medium", "Recommendation": recommendation, "Source": "AgentX"})
    return rows