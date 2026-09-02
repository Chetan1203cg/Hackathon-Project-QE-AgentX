"""
models/coverage.py
==================
Pydantic schemas for the Coverage Map (CM).
Output of Agent 5 — Coverage Agent.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ACCoverage(BaseModel):
    ac_id: str
    ac_text: str
    covered_by: list[str] = Field(
        default_factory=list,
        description="List of TestCase.tc_id values covering this AC",
    )
    coverage_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="0.0 = not covered, 1.0 = fully covered",
    )
    gap_notes: list[str] = Field(
        default_factory=list,
        description="Descriptions of detected coverage gaps",
    )


class CoverageMap(BaseModel):
    story_id: str
    overall_coverage_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    total_acs: int = 0
    covered_acs: int = 0
    partially_covered_acs: int = 0
    uncovered_acs: int = 0
    desktop_coverage_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    mobile_coverage_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    ac_coverage: list[ACCoverage] = Field(default_factory=list)
    uncovered_flows: list[str] = Field(
        default_factory=list,
        description="Flow types with zero test case coverage",
    )
