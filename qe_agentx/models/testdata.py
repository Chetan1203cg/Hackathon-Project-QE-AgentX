"""
models/testdata.py
==================
Pydantic schemas for the Test Data Manifest (TDM).
Output of Agent 4 — Test Data Agent.
"""

from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class DataCategory(str, Enum):
    VALID = "valid"
    BOUNDARY = "boundary"
    INVALID = "invalid"
    NULL_EMPTY = "null_empty"
    SPECIAL_CHARS = "special_chars"


class DataSet(BaseModel):
    dataset_id: str
    tc_ref: str = Field(description="References TestCase.tc_id")
    category: DataCategory
    description: str
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Field name -> value mapping for this dataset",
    )
    notes: str | None = None
    requires_provisioning: bool = Field(
        default=False,
        description="True if environment setup is required before use",
    )


class TestDataManifest(BaseModel):
    story_id: str
    datasets: list[DataSet] = Field(default_factory=list)

    def datasets_for(self, tc_id: str) -> list[DataSet]:
        return [d for d in self.datasets if d.tc_ref == tc_id]
