"""
agents/coverage_agent.py
=========================
Agent 5 — Coverage Agent

Responsibilities:
- Map every test case to its source acceptance criterion
- Calculate coverage percentage per AC and overall
- Detect coverage gaps (uncovered ACs, missing flow types)
- Output a CoverageMap (CM)
"""

from __future__ import annotations

import logging
from collections import defaultdict

from agents.base_agent import BaseAgent
from models.coverage import ACCoverage, CoverageMap

logger = logging.getLogger(__name__)


class CoverageAgent(BaseAgent):
    """
    Coverage calculation is algorithmic — no LLM call needed for the core mapping.
    LLM is used only for gap analysis narrative.
    """
    agent_name = "coverage_agent"

    def run(self, state: dict) -> dict:
        return self._safe_run(state, self._execute)

    def _execute(self, state: dict) -> dict:
        sro = state.get("structured_requirement", {})
        test_cases = state.get("test_cases", [])
        story_id = sro.get("story_id", "")

        logger.info("[CoverageAgent] Calculating coverage for: %s", story_id)

        acceptance_criteria = sro.get("acceptance_criteria", [])

        # Build AC -> [tc_id] mapping
        ac_to_tcs: dict[str, list[str]] = defaultdict(list)
        for tc in test_cases:
            ac_ref = tc.get("ac_ref", "")
            if ac_ref:
                ac_to_tcs[ac_ref].append(tc["tc_id"])

        # Build covered flow type map
        ac_to_flows: dict[str, set[str]] = defaultdict(set)
        for tc in test_cases:
            # Flow type is embedded in the scenario node; use tags as proxy
            for tag in tc.get("tags", []):
                ac_to_flows[tc.get("ac_ref", "")].add(tag)

        ac_coverage_list: list[ACCoverage] = []
        covered = 0
        partial = 0
        uncovered = 0

        for ac in acceptance_criteria:
            ac_id = ac["id"]
            covered_tcs = ac_to_tcs.get(ac_id, [])
            gap_notes = []

            if not covered_tcs:
                score = 0.0
                uncovered += 1
                gap_notes.append(f"{ac_id} has no test cases at all")
            else:
                # Score by how many flow types are covered (max 5 types)
                covered_flows = ac_to_flows.get(ac_id, set())
                required_flows = {"happy_path", "negative", "boundary"}
                missing = required_flows - covered_flows
                if missing:
                    score = round(len(covered_tcs) / (len(covered_tcs) + len(missing)), 2)
                    partial += 1
                    gap_notes.extend([
                        f"Missing flow type coverage: {ft}" for ft in missing
                    ])
                else:
                    score = 1.0
                    covered += 1

            ac_coverage_list.append(
                ACCoverage(
                    ac_id=ac_id,
                    ac_text=ac["text"],
                    covered_by=covered_tcs,
                    coverage_score=score,
                    gap_notes=gap_notes,
                )
            )

        total = len(acceptance_criteria)
        overall_pct = round((covered + 0.5 * partial) / total * 100, 1) if total else 0.0

        coverage_map = CoverageMap(
            story_id=story_id,
            overall_coverage_pct=overall_pct,
            total_acs=total,
            covered_acs=covered,
            partially_covered_acs=partial,
            uncovered_acs=uncovered,
            desktop_coverage_pct=round(
                sum(bool(tc.get("browser_coverage")) for tc in test_cases) / len(test_cases) * 100,
                1,
            ) if test_cases else 0.0,
            mobile_coverage_pct=round(
                sum(bool(tc.get("mobile_coverage")) for tc in test_cases) / len(test_cases) * 100,
                1,
            ) if test_cases else 0.0,
            ac_coverage=ac_coverage_list,
        )

        logger.info(
            "[CoverageAgent] Coverage: %.1f%% (%d covered, %d partial, %d uncovered)",
            overall_pct, covered, partial, uncovered,
        )

        return {"coverage_map": coverage_map.model_dump()}
