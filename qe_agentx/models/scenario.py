"""
models/scenario.py
==================
Pydantic schema for the Scenario Behaviour Tree (SBT).
Output of Agent 2 — Scenario Agent.
"""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class FlowType(str, Enum):
    HAPPY_PATH = "happy_path"
    ALTERNATE_FLOW = "alternate_flow"
    BOUNDARY = "boundary"
    NEGATIVE = "negative"
    NFR = "nfr"


class ScenarioNode(BaseModel):
    node_id: str = Field(description="Unique node ID, e.g. SN-001")
    ac_ref: str = Field(description="References AcceptanceCriterion.id")
    flow_type: FlowType
    title: str
    description: str
    precondition: str | None = None
    trigger_condition: str | None = None
    expected_state: str | None = None
    risk_level: str = "MEDIUM"
    children: list["ScenarioNode"] = Field(default_factory=list)


class ScenarioBehaviourTree(BaseModel):
    story_id: str
    total_nodes: int = 0
    happy_path_count: int = 0
    alternate_flow_count: int = 0
    boundary_count: int = 0
    negative_count: int = 0
    nfr_count: int = 0
    root_nodes: list[ScenarioNode] = Field(default_factory=list)

    def all_nodes(self) -> list[ScenarioNode]:
        """Flatten tree into a list of all nodes (BFS)."""
        result: list[ScenarioNode] = []
        queue = list(self.root_nodes)
        while queue:
            node = queue.pop(0)
            result.append(node)
            queue.extend(node.children)
        return result
