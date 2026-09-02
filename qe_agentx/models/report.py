"""
models/report.py
================
Pydantic schema for the Final Report Bundle (FRB).
Output of Agent 8 — Reporting Agent.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from models.testcase import TestCaseSet
from models.testdata import TestDataManifest
from models.coverage import CoverageMap
from models.rtm import RTMArtefact


class ReviewFinding(BaseModel):
    finding_id: str
    tc_ref: str | None = None
    severity: str = "INFO"  # INFO | WARNING | ERROR
    category: str           # duplicate | quality | gap | rubric
    description: str
    suggestion: str | None = None
    auto_fixed: bool = False


class ReviewReport(BaseModel):
    story_id: str
    quality_score: float = Field(default=0.0, ge=0.0, le=100.0)
    passed_count: int = 0
    flagged_count: int = 0
    auto_fixed_count: int = 0
    findings: list[ReviewFinding] = Field(default_factory=list)
    gaps_detected: list[str] = Field(default_factory=list)
    duplicate_pairs: list[tuple[str, str]] = Field(default_factory=list)


class FinalReportBundle(BaseModel):
    run_id: str
    story_id: str
    generated_at: str = ""
    pipeline_duration_seconds: float = 0.0

    # Core artefacts
    test_case_set: TestCaseSet | None = None
    test_data_manifest: TestDataManifest | None = None
    coverage_map: CoverageMap | None = None
    rtm: RTMArtefact | None = None
    review_report: ReviewReport | None = None

    # Summary
    executive_summary: str = ""
    key_metrics: dict = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)

    # Export paths (populated after export)
    export_paths: dict[str, str] = Field(default_factory=dict)
