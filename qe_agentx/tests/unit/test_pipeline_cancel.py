"""Tests for cancelling a pipeline at the human clarification gate."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from api.routes.pipeline import _runs, cancel_pipeline


@pytest.mark.unit
async def test_cancel_pipeline_stops_awaiting_run():
    run_id = "cancel-test"
    _runs[run_id] = {
        "status": "awaiting_hitl",
        "state": {"hitl_pending": True, "current_stage": "Analysing Requirements"},
    }

    try:
        result = await cancel_pipeline(run_id)

        assert result["status"] == "cancelled"
        assert _runs[run_id]["state"]["hitl_pending"] is False
        assert _runs[run_id]["state"]["current_stage"] == "Cancelled by user"
    finally:
        _runs.pop(run_id, None)


@pytest.mark.unit
async def test_cancel_pipeline_rejects_running_run():
    run_id = "running-test"
    _runs[run_id] = {"status": "running", "state": {"hitl_pending": False}}

    try:
        with pytest.raises(HTTPException) as exc_info:
            await cancel_pipeline(run_id)

        assert exc_info.value.status_code == 409
    finally:
        _runs.pop(run_id, None)