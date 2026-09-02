"""
models/requirement.py
=====================
Pydantic schema for the Structured Requirement Object (SRO).
Output of Agent 1 — Requirement Agent.
"""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AcceptanceCriterion(BaseModel):
    id: str = Field(description="Unique AC identifier, e.g. AC-01")
    text: str = Field(description="Full AC statement")
    is_ambiguous: bool = Field(default=False)
    ambiguity_note: str | None = Field(default=None)
    implicit_assumption: str | None = Field(default=None)


class StructuredRequirementObject(BaseModel):
    story_id: str
    summary: str
    component: str | None = None
    priority: str | None = None
    sprint: str | None = None
    acceptance_criteria: list[AcceptanceCriterion] = Field(default_factory=list)
    nfr_hints: list[str] = Field(
        default_factory=list,
        description="Non-functional requirements detected in story text",
    )
    domain_keywords: list[str] = Field(default_factory=list)
    clarifying_questions: list[str] = Field(
        default_factory=list,
        description="Questions to surface to the QA engineer via HITL",
    )
    overall_risk: RiskLevel = RiskLevel.MEDIUM
    confidence_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Agent confidence in the parsed output (0–1)",
    )
