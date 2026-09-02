"""Tests for Coverage Analysis view-model calculations."""

from ui.coverage_view import (
    coverage_status,
    jira_status_badge,
    recommendation_rows,
    risk_level,
    traceability_rows,
)


def test_traceability_rows_include_status_tests_and_risk():
    coverage = {"ac_coverage": [{
        "ac_id": "AC-01", "ac_text": "Login works", "coverage_score": 0.5,
        "covered_by": ["TC-001"], "gap_notes": ["Negative path missing"],
    }]}
    rows = traceability_rows(coverage, [{"ac_ref": "AC-01", "risk_level": "HIGH"}])

    assert rows[0]["Coverage"] == 50.0
    assert rows[0]["Tests"] == 1
    assert rows[0]["Risk"] == "High"
    assert "Partial" in rows[0]["Status"]


def test_risk_and_recommendations_use_real_artifacts():
    review = {"flagged_count": 1, "findings": [{
        "severity": "WARNING", "category": "gap", "suggestion": "Add a negative test",
    }]}

    assert risk_level({}, review, {}) == "Medium"
    assert recommendation_rows({}, review)[0]["Recommendation"] == "Add a negative test"
    assert coverage_status(0) == "Uncovered"
    assert jira_status_badge("Closed") == ":green-badge[Closed]"
    assert jira_status_badge("Blocked") == ":red-badge[Blocked]"