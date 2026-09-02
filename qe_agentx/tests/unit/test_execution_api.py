"""Tests for test execution status and evidence API operations."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from api.main import app
from api.routes import execution as execution_routes
from api.routes.pipeline import _runs
from core.test_cycle import create_test_cycle

client = TestClient(app)


def _completed_run(run_id: str) -> dict:
    state = {
        "run_id": run_id,
        "story_id": "ABC-123",
        "project_key": "ABC",
        "target_environment": "QA",
        "raw_story": {"type": "Story", "summary": "Login"},
        "structured_requirement": {"acceptance_criteria": [{"id": "AC-01"}]},
        "release_traceability": {"sprint": "Sprint 24"},
        "coverage_map": {"overall_coverage_pct": 100},
        "release_decision": {},
        "test_cases": [{"tc_id": "TC-001", "title": "Login", "ac_ref": "AC-01"}],
    }
    state["test_cycle"] = create_test_cycle(state)
    return {"status": "completed", "state": state}


def test_update_execution_recalculates_progress_and_readiness():
    run_id = "execution-update"
    _runs[run_id] = _completed_run(run_id)
    try:
        response = client.put(
            f"/execution/{run_id}/tests/TC-001",
            json={"status": "PASS", "execution_comments": "Verified"},
        )

        assert response.status_code == 200
        cycle = client.get(f"/execution/{run_id}").json()
        assert cycle["metrics"]["execution_progress_pct"] == 100.0
        assert cycle["metrics"]["pass_rate_pct"] == 100.0
        assert cycle["readiness_summary"]["release_recommendation"] == "GO"
    finally:
        _runs.pop(run_id, None)


def test_defect_link_is_rejected_for_non_failed_test():
    run_id = "execution-defect"
    _runs[run_id] = _completed_run(run_id)
    try:
        response = client.put(
            f"/execution/{run_id}/tests/TC-001",
            json={"status": "PASS", "existing_defect_key": "BUG-1"},
        )

        assert response.status_code == 400
    finally:
        _runs.pop(run_id, None)


def test_upload_evidence_persists_file(tmp_path, monkeypatch):
    run_id = "execution-evidence"
    _runs[run_id] = _completed_run(run_id)
    monkeypatch.setattr(execution_routes, "EVIDENCE_ROOT", tmp_path)
    try:
        response = client.post(
            f"/execution/{run_id}/tests/TC-001/evidence",
            files={"evidence": ("result.log", b"successful run", "text/plain")},
        )

        assert response.status_code == 201
        assert (tmp_path / run_id / "TC-001" / "result.log").read_bytes() == b"successful run"
        assert response.json()["release_traceability"]["sprint"] == "Sprint 24"
    finally:
        _runs.pop(run_id, None)


def test_upload_evidence_preserves_existing_file(tmp_path, monkeypatch):
    run_id = "execution-evidence-copy"
    _runs[run_id] = _completed_run(run_id)
    monkeypatch.setattr(execution_routes, "EVIDENCE_ROOT", tmp_path)
    target_dir = tmp_path / run_id / "TC-001"
    target_dir.mkdir(parents=True)
    (target_dir / "result.log").write_bytes(b"original")
    try:
        response = client.post(
            f"/execution/{run_id}/tests/TC-001/evidence",
            files={"evidence": ("result.log", b"new evidence", "text/plain")},
        )

        assert response.status_code == 201
        assert (target_dir / "result.log").read_bytes() == b"original"
        assert (target_dir / "result_2.log").read_bytes() == b"new evidence"
        assert response.json()["filename"] == "result_2.log"
    finally:
        _runs.pop(run_id, None)


def test_failed_execution_links_existing_jira_bug():
    run_id = "execution-link-defect"
    _runs[run_id] = _completed_run(run_id)
    jira = MagicMock()
    jira.__enter__.return_value = jira
    try:
        with patch("api.routes.execution.JiraClient", return_value=jira):
            response = client.put(
                f"/execution/{run_id}/tests/TC-001",
                json={
                    "status": "FAIL",
                    "existing_defect_key": "bug-456",
                    "existing_defect_summary": "Login API fails",
                },
            )

        assert response.status_code == 200
        jira.link_issues.assert_called_once_with("ABC-123", "BUG-456")
        assert response.json()["defects"][0]["key"] == "BUG-456"
    finally:
        _runs.pop(run_id, None)


def test_failed_execution_creates_and_associates_jira_bug():
    run_id = "execution-create-defect"
    _runs[run_id] = _completed_run(run_id)
    _runs[run_id]["state"]["test_cycle"]["executions"][0]["status"] = "FAIL"
    jira = MagicMock()
    jira.__enter__.return_value = jira
    jira.create_bug.return_value = {
        "key": "ABC-456",
        "summary": "Login API fails",
        "source": "created",
    }
    try:
        with patch("api.routes.execution.JiraClient", return_value=jira):
            response = client.post(
                f"/execution/{run_id}/tests/TC-001/defects",
                json={"summary": "Login API fails", "description": "HTTP 500"},
            )

        assert response.status_code == 201
        jira.create_bug.assert_called_once_with(
            "ABC", "Login API fails", "HTTP 500", "ABC-123"
        )
        assert response.json()["key"] == "ABC-456"
    finally:
        _runs.pop(run_id, None)
