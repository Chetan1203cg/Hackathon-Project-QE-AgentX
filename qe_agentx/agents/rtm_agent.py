"""
agents/rtm_agent.py
====================
Agent 6 — RTM Agent

Responsibilities:
- Build a complete Requirements Traceability Matrix
- Link: Story → AC → Scenario Node → Test Case → Test Data
- Output an RTMArtefact ready for export
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from agents.base_agent import BaseAgent
from models.rtm import RTMArtefact, RTMRow

logger = logging.getLogger(__name__)


class RTMAgent(BaseAgent):
    """Purely algorithmic — assembles RTM from existing state; no LLM call."""
    agent_name = "rtm_agent"

    def run(self, state: dict) -> dict:
        return self._safe_run(state, self._execute)

    def _execute(self, state: dict) -> dict:
        sro = state.get("structured_requirement", {})
        sbt = state.get("behaviour_tree", {})
        test_cases = state.get("test_cases", [])
        test_data = state.get("test_data", {})
        coverage_map = state.get("coverage_map", {})
        story_id = sro.get("story_id", "")

        logger.info("[RTMAgent] Building RTM for: %s", story_id)

        # Build lookup maps
        node_map = {
            node["node_id"]: node
            for node in self._flatten_nodes(sbt.get("root_nodes", []))
        }
        ac_map = {
            ac["id"]: ac for ac in sro.get("acceptance_criteria", [])
        }
        coverage_score_map = {
            cov["ac_id"]: cov["coverage_score"]
            for cov in coverage_map.get("ac_coverage", [])
        }
        dataset_map: dict[str, list[str]] = {}
        for ds in (test_data.get("datasets") or []):
            dataset_map.setdefault(ds["tc_ref"], []).append(ds["dataset_id"])

        rows: list[RTMRow] = []
        for idx, tc in enumerate(test_cases, start=1):
            node = node_map.get(tc.get("scenario_node_ref", ""), {})
            ac = ac_map.get(tc.get("ac_ref", ""), {})

            row = RTMRow(
                row_id=f"RTM-{idx:04d}",
                story_id=story_id,
                story_summary=sro.get("summary", ""),
                ac_id=tc.get("ac_ref", ""),
                ac_text=ac.get("text", ""),
                scenario_node_id=tc.get("scenario_node_ref", ""),
                scenario_title=node.get("title", ""),
                tc_id=tc["tc_id"],
                tc_title=tc["title"],
                tc_risk=tc.get("risk_level", "MEDIUM"),
                tc_status=tc.get("status", "DRAFT"),
                dataset_ids=dataset_map.get(tc["tc_id"], []),
                coverage_score=coverage_score_map.get(tc.get("ac_ref", ""), 0.0),
            )
            rows.append(row)

        rtm = RTMArtefact(
            story_id=story_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_rows=len(rows),
            rows=rows,
        )

        logger.info("[RTMAgent] RTM built with %d rows", rtm.total_rows)
        return {"rtm": rtm.model_dump()}

    def _flatten_nodes(self, nodes: list) -> list:
        result = []
        for node in nodes:
            result.append(node)
            result.extend(self._flatten_nodes(node.get("children", [])))
        return result
