"""Tests for mandatory Jira release traceability enrichment."""

from __future__ import annotations

from integrations.release_traceability import NOT_AVAILABLE, build_release_traceability


def test_release_traceability_prefers_selected_issue_metadata():
    stories = [
        {
            "key": "NGWD6-1",
            "type": "User Story",
            "summary": "Accessible search",
            "link": "https://jira.example/browse/NGWD6-1",
            "sprints": [{"name": "Sprint 124", "state": "active"}],
            "fix_versions": [
                {"id": "8", "name": "8.14.0", "released": False, "release_date": "2026-08-20"}
            ],
            "release_fields": [
                {"name": "CW Release", "value": "CW34"},
                {"name": "FA Release Version", "value": "FA 2026.08.1"},
                {"name": "Environment", "value": "Test"},
            ],
            "component": "CMS",
            "labels": ["a11y"],
        },
        {
            "key": "NGWD6-2",
            "sprints": [{"name": "Sprint 120", "state": "closed"}],
            "fix_versions": [],
            "release_fields": [],
        },
    ]

    result = build_release_traceability(stories)

    assert result["sprint"] == "Sprint 124"
    assert result["sprint_status"] == "active"
    assert result["cw_release"] == "CW34"
    assert result["fa_release_version"] == "FA 2026.08.1"
    assert result["fix_version"] == "8.14.0"
    assert result["planned_release_date"] == "2026-08-20"
    assert result["availability_message"] == ""


def test_release_traceability_marks_missing_core_metadata():
    result = build_release_traceability(
        [{"key": "NGWD6-1", "type": "Task", "summary": "Task", "link": "", "release_fields": []}]
    )

    assert result["sprint"] == NOT_AVAILABLE
    assert result["cw_release"] == NOT_AVAILABLE
    assert result["fa_release_version"] == NOT_AVAILABLE
    assert result["availability_message"].startswith(NOT_AVAILABLE)
