"""
exports/json_exporter.py
=========================
Exports test cases in Xray Cloud import-compatible JSON format.
"""

from __future__ import annotations

import json


class JsonExporter:
    def export(self, state: dict) -> str:
        story_id = state.get("story_id", "")
        test_cases = state.get("test_cases") or []
        test_data = state.get("test_data") or {}
        rtm = state.get("rtm") or {}
        release = state.get("release_traceability") or {}

        dataset_map: dict[str, list[dict]] = {}
        for ds in (test_data.get("datasets") or []):
            dataset_map.setdefault(ds["tc_ref"], []).append(ds)

        xray_tests = []
        for tc in test_cases:
            tc_id = tc.get("tc_id", "")
            steps = [
                {
                    "action": s.get("action", ""),
                    "result": s.get("expected_result") or "",
                    "data": "",
                }
                for s in tc.get("steps", [])
            ]
            xray_tests.append({
                "testtype": "Manual",
                "summary": tc.get("title", ""),
                "description": tc.get("description", ""),
                "labels": tc.get("tags", []),
                "priority": tc.get("risk_level", "Medium").title(),
                "steps": steps,
                "requirements": [story_id],
                "xray_metadata": {
                    "internal_id": tc_id,
                    "ac_ref": tc.get("ac_ref", ""),
                    "scenario_node_ref": tc.get("scenario_node_ref", ""),
                    "gherkin": tc.get("gherkin"),
                    "release_traceability": release,
                },
                "datasets": dataset_map.get(tc_id, []),
            })

        payload = {
            "story_id": story_id,
            "release_information": release,
            "test_cycle": state.get("test_cycle") or {},
            "test_count": len(xray_tests),
            "tests": xray_tests,
            "rtm_summary": {
                "total_rows": rtm.get("total_rows", 0),
                "generated_at": rtm.get("generated_at", ""),
            },
        }

        return json.dumps(payload, indent=2, ensure_ascii=False)
