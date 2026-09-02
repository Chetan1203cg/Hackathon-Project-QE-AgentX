"""
exports/csv_exporter.py
========================
Exports the RTM as a flat CSV file for spreadsheet tools.
"""

from __future__ import annotations

import csv
import io


class CsvExporter:
    HEADERS = [
        "Row ID", "Story ID", "Story Summary",
        "AC ID", "AC Text",
        "Scenario Node ID", "Scenario Title",
        "TC ID", "TC Title", "TC Risk", "TC Status",
        "Sprint", "Sprint Status", "CW Release", "FA Release Version",
        "Fix Version", "Planned Release Date", "Environment",
        "Execution Status", "Execution Comments", "Linked Defects", "Evidence",
        "Dataset IDs", "Coverage Score",
    ]

    def export(self, state: dict) -> str:
        rtm = state.get("rtm") or {}
        rows = rtm.get("rows") or []
        release = state.get("release_traceability") or {}
        executions = {
            item.get("tc_id"): item
            for item in ((state.get("test_cycle") or {}).get("executions") or [])
        }

        buffer = io.StringIO()
        writer = csv.writer(buffer, quoting=csv.QUOTE_ALL)
        writer.writerow(self.HEADERS)

        for row in rows:
            execution = executions.get(row.get("tc_id"), {})
            writer.writerow([
                row.get("row_id", ""),
                row.get("story_id", ""),
                row.get("story_summary", ""),
                row.get("ac_id", ""),
                row.get("ac_text", ""),
                row.get("scenario_node_id", ""),
                row.get("scenario_title", ""),
                row.get("tc_id", ""),
                row.get("tc_title", ""),
                row.get("tc_risk", ""),
                row.get("tc_status", ""),
                release.get("sprint", ""),
                release.get("sprint_status", ""),
                release.get("cw_release", ""),
                release.get("fa_release_version", ""),
                release.get("fix_version", ""),
                release.get("planned_release_date", ""),
                release.get("environment", ""),
                execution.get("status", "NOT_EXECUTED"),
                execution.get("execution_comments", ""),
                "; ".join(item.get("key", "") for item in execution.get("defects", [])),
                "; ".join(item.get("filename", "") for item in execution.get("evidence", [])),
                "; ".join(row.get("dataset_ids", [])),
                f"{row.get('coverage_score', 0):.2f}",
            ])

        return buffer.getvalue()
