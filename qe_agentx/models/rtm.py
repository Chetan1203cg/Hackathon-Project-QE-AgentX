"""
models/rtm.py
=============
Pydantic schemas for the Requirements Traceability Matrix (RTM).
Output of Agent 6 — RTM Agent.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RTMRow(BaseModel):
    row_id: str
    story_id: str
    story_summary: str
    ac_id: str
    ac_text: str
    scenario_node_id: str
    scenario_title: str
    tc_id: str
    tc_title: str
    tc_risk: str
    tc_status: str
    dataset_ids: list[str] = Field(default_factory=list)
    coverage_score: float = 0.0


class RTMArtefact(BaseModel):
    story_id: str
    generated_at: str = ""
    total_rows: int = 0
    rows: list[RTMRow] = Field(default_factory=list)

    def to_dict_list(self) -> list[dict]:
        return [row.model_dump() for row in self.rows]
