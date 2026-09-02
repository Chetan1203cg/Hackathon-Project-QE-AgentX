"""
models/testcase.py
==================
Pydantic schemas for Test Cases and the Test Case Set (TCS).
Output of Agent 3 — Test Case Agent.
"""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class TestCaseStatus(str, Enum):
    DRAFT = "DRAFT"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    OBSOLETE = "OBSOLETE"


class TestStep(BaseModel):
    step_number: int
    action: str
    expected_result: str | None = None


class TestCase(BaseModel):
    tc_id: str = Field(description="Unique TC identifier, e.g. TC-001")
    scenario_node_ref: str = Field(description="References ScenarioNode.node_id")
    ac_ref: str = Field(description="References AcceptanceCriterion.id")
    title: str
    description: str
    preconditions: list[str] = Field(default_factory=list)
    steps: list[TestStep] = Field(default_factory=list)
    expected_result: str
    risk_level: str = "MEDIUM"
    tags: list[str] = Field(default_factory=list)
    status: TestCaseStatus = TestCaseStatus.DRAFT
    gherkin: str | None = Field(
        default=None, description="Optional BDD Gherkin representation"
    )
    browser_coverage: list[str] = Field(
        default_factory=lambda: ["Chrome", "Edge", "Firefox"],
    )
    mobile_coverage: list[str] = Field(
        default_factory=lambda: ["Android Chrome", "iPhone Safari"],
    )
    evidence_required: list[str] = Field(default_factory=lambda: ["Screenshot", "Video"])


class TestCaseSet(BaseModel):
    story_id: str
    total: int = 0
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0
    test_cases: list[TestCase] = Field(default_factory=list)
