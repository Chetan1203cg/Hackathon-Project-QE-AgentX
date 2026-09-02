"""
exports/markdown_exporter.py
=============================
Renders the pipeline state into a Markdown test suite document.
Compatible with the existing output format in output/Archive/*.md
"""

from __future__ import annotations

from datetime import UTC, datetime


class MarkdownExporter:
    def export(self, state: dict) -> str:
        story_id = state.get("story_id", "")
        sro = state.get("structured_requirement") or {}
        test_cases = state.get("test_cases") or []
        coverage = state.get("coverage_map") or {}
        review = state.get("review_report") or {}
        final_report = state.get("final_report") or {}
        release = state.get("release_traceability") or {}
        cycle = state.get("test_cycle") or {}
        executions = {
            item.get("tc_id"): item for item in (cycle.get("executions") or [])
        }

        lines = [
            "# Release Information",
            "",
            f"- **Jira Key:** {release.get('jira_key', story_id)}",
            f"- **Jira Type:** {release.get('jira_type', '')}",
            f"- **Sprint:** {release.get('sprint', '')}",
            f"- **Sprint Status:** {release.get('sprint_status', '')}",
            f"- **CW Release:** {release.get('cw_release', '')}",
            f"- **FA Release Version:** {release.get('fa_release_version', '')}",
            f"- **Fix Version:** {release.get('fix_version', '')}",
            f"- **Planned Release Date:** {release.get('planned_release_date', '')}",
            f"- **Environment / Deployment:** {release.get('environment', '')}",
            "",
        ]
        if release.get("availability_message"):
            lines += [f"> **{release['availability_message']}**", ""]
        lines += [
            "## User Story",
            "",
            f"{story_id} - {release.get('jira_summary') or sro.get('summary', '')}",
            "",
            "## URL",
            "",
            release.get("jira_url", ""),
            "",
            "---",
            "",
            "# Test Cycle",
            "",
            f"- **Cycle:** {cycle.get('name', '')}",
            f"- **Cycle ID:** {cycle.get('cycle_id', '')}",
            f"- **Environment:** {cycle.get('environment', '')}",
            f"- **Execution Type:** {cycle.get('execution_type', '')}",
            "",
            f"# Test Cases — {story_id}",
            "",
            f"> **Story:** {sro.get('summary', '')}  ",
            f"> **Component:** {sro.get('component', '')}  ",
            f"> **Priority:** {sro.get('priority', '')}  ",
            f"> **Sprint:** {sro.get('sprint', '')}  ",
            f"> **Generated:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}  ",
            f"> **Coverage:** {coverage.get('overall_coverage_pct', 0):.1f}%  ",
            f"> **Quality Score:** {review.get('quality_score', 0):.0f}/100  ",
            "",
            "---",
            "",
        ]

        # Executive summary
        if final_report.get("executive_summary"):
            lines += ["## Executive Summary", "", final_report["executive_summary"], "", "---", ""]

        # Test cases
        lines += [f"## Test Cases ({len(test_cases)} total)", ""]

        for tc in test_cases:
            execution = executions.get(tc.get("tc_id"), {})
            lines += [
                f"### {tc.get('tc_id', '')} — {tc.get('title', '')}",
                "",
                f"**Risk:** {tc.get('risk_level', 'MEDIUM')}  ",
                f"**AC Reference:** {tc.get('ac_ref', '')}  ",
                f"**Tags:** {', '.join(tc.get('tags', []))}  ",
                f"**Desktop:** {', '.join(tc.get('browser_coverage', []))}  ",
                f"**Mobile:** {', '.join(tc.get('mobile_coverage', []))}  ",
                f"**Evidence:** {', '.join(tc.get('evidence_required', []))}  ",
                f"**Sprint:** {release.get('sprint', '')}  ",
                f"**CW Release:** {release.get('cw_release', '')}  ",
                f"**FA Release Version:** {release.get('fa_release_version', '')}  ",
                f"**Execution Status:** {execution.get('status', 'NOT_EXECUTED')}  ",
                f"**Execution Comments:** {execution.get('execution_comments', '') or 'None'}  ",
                f"**Linked Defects:** {', '.join(item.get('key', '') for item in execution.get('defects', [])) or 'None'}  ",
                f"**Captured Evidence:** {', '.join(item.get('filename', '') for item in execution.get('evidence', [])) or 'None'}  ",
                "",
                f"**Description:** {tc.get('description', '')}",
                "",
                "**Preconditions:**",
            ]
            for pre in tc.get("preconditions", []):
                lines.append(f"- {pre}")
            lines += ["", "**Test Steps:**", ""]
            lines.append("| Step | Action | Expected Result |")
            lines.append("|------|--------|----------------|")
            for step in tc.get("steps", []):
                action = step.get("action", "").replace("|", "\\|")
                er = (step.get("expected_result") or "—").replace("|", "\\|")
                lines.append(f"| {step.get('step_number', '')} | {action} | {er} |")
            lines += [
                "",
                f"**Overall Expected Result:** {tc.get('expected_result', '')}",
                "",
                "**Test Evidence Traceability:** ",
                f"Sprint: {release.get('sprint', '')}; "
                f"CW Release: {release.get('cw_release', '')}; "
                f"FA Release: {release.get('fa_release_version', '')}",
                "",
            ]
            if tc.get("gherkin"):
                lines += ["**Gherkin:**", "```gherkin", tc["gherkin"], "```", ""]
            lines.append("---")
            lines.append("")

        # Coverage summary
        lines += ["## Coverage Summary", ""]
        lines += [
            f"Desktop coverage: **{coverage.get('desktop_coverage_pct', 0):.1f}%**  ",
            f"Mobile coverage: **{coverage.get('mobile_coverage_pct', 0):.1f}%**  ",
            "",
        ]
        lines.append("| Acceptance Criterion | Coverage | Test Cases |")
        lines.append("|---------------------|----------|------------|")
        for ac_cov in (coverage.get("ac_coverage") or []):
            pct = f"{ac_cov.get('coverage_score', 0) * 100:.0f}%"
            tcs = ", ".join(ac_cov.get("covered_by", []))
            ac_text = ac_cov.get("ac_text", "").replace("|", "\\|")
            lines.append(f"| {ac_cov.get('ac_id')} — {ac_text} | {pct} | {tcs} |")
        lines.append("")

        # Recommendations
        recs = final_report.get("recommendations", [])
        if recs:
            lines += ["## Recommendations", ""]
            for rec in recs:
                lines.append(f"- {rec}")
            lines.append("")

        metrics = cycle.get("metrics") or {}
        readiness = cycle.get("readiness_summary") or {}
        lines += [
            "## Test Execution Summary",
            "",
            f"- **Total:** {metrics.get('total', 0)}",
            f"- **Executed:** {metrics.get('executed', 0)}",
            f"- **Passed:** {metrics.get('passed', 0)}",
            f"- **Failed:** {metrics.get('failed', 0)}",
            f"- **Blocked:** {metrics.get('blocked', 0)}",
            f"- **Not Executed:** {metrics.get('not_executed', 0)}",
            f"- **Execution Progress:** {metrics.get('execution_progress_pct', 0):.1f}%",
            f"- **Pass Rate:** {metrics.get('pass_rate_pct', 0):.1f}%",
            f"- **Defect Count:** {metrics.get('defect_count', 0)}",
            "",
            "## Release Readiness Summary",
            "",
            f"- **Requirement Coverage:** {readiness.get('requirement_coverage_pct', 0):.1f}%",
            f"- **Risk Assessment:** {readiness.get('risk_assessment', '')}",
            f"- **Release Recommendation:** {readiness.get('release_recommendation', 'NOT READY')}",
            f"- **Linked Defects:** {', '.join(readiness.get('linked_defects', [])) or 'None'}",
            "",
        ]

        return "\n".join(lines)
