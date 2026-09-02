"""Enterprise release-readiness and requirement coverage intelligence."""

from __future__ import annotations

import httpx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ui.coverage_view import (
    jira_status_badge,
    recommendation_rows,
    risk_level,
    traceability_rows,
)
from ui.http_errors import format_api_error
from ui.release_display import render_release_metadata_grid

API_BASE = "http://localhost:8000"
NOT_AVAILABLE = "Release Information Not Available in Jira Metadata"

st.set_page_config(
    page_title="Coverage intelligence - QE AgentX",
    page_icon=":material/analytics:",
    layout="wide",
)

run_id = st.session_state.get("run_id")
if not run_id:
    st.info("No completed analysis is available. Start a run from Generate.")
    st.stop()

response = httpx.get(f"{API_BASE}/artifacts/{run_id}", timeout=15.0)
if response.is_error:
    st.error(format_api_error(response))
    st.stop()

data = response.json()
coverage = data.get("coverage_map") or {}
if not coverage:
    st.warning("Coverage intelligence is not available for this run.")
    st.stop()

release = data.get("release_traceability") or {}
cycle = data.get("test_cycle") or {}
execution = cycle.get("metrics") or {}
readiness = cycle.get("readiness_summary") or {}
review = data.get("review_report") or {}
final_report = data.get("final_report") or {}
test_cases = data.get("test_cases") or []
related_items = data.get("related_jira_items") or []
traceability = traceability_rows(coverage, test_cases)
recommendations = recommendation_rows(final_report, review)
risk = risk_level(coverage, review, cycle)
open_defects = execution.get("defect_count", 0)
total_requirements = coverage.get("total_acs", len(traceability))
gaps = coverage.get("uncovered_acs", 0) + coverage.get("partially_covered_acs", 0)

st.title("Coverage analysis")
st.caption(
    f"Release readiness intelligence · {data.get('story_id', '')} · Run {run_id[:8]}"
)

st.subheader("Executive summary")
summary_top = st.columns(3, border=True)
summary_top[0].metric("Coverage", f"{coverage.get('overall_coverage_pct', 0):.1f}%", "Requirement coverage")
summary_top[1].metric("Requirements", total_requirements, "Total scope")
summary_top[2].metric("Test cases", len(test_cases), "Generated assets")
summary_bottom = st.columns(3, border=True)
summary_bottom[0].metric("Coverage gaps", gaps, "Needs action")
summary_bottom[1].metric("Risk level", risk, "Current assessment")
summary_bottom[2].metric("Open defects", open_defects, "Linked to executions")

recommendation = readiness.get("release_recommendation", "NOT READY")
badge_label = recommendation.replace("_", " ").title()
badge_color = "red" if recommendation == "NO GO" else "orange" if recommendation == "GO WITH RISK" else "green" if recommendation == "GO" else "gray"
with st.container(horizontal=True, vertical_alignment="center"):
    st.markdown("**Release recommendation**")
    st.badge(badge_label, color=badge_color)
    st.caption(
        f"Execution progress {execution.get('execution_progress_pct', 0):.1f}% · "
        f"Pass rate {execution.get('pass_rate_pct', 0):.1f}%"
    )

st.subheader("Release summary")
render_release_metadata_grid(release)
if release.get("jira_url"):
    st.link_button(
        "Open Jira",
        release["jira_url"],
        icon=":material/open_in_new:",
        type="tertiary",
        help="Open the source work item in Jira.",
    )

if release.get("missing_fields"):
    with st.container(border=True):
        st.markdown(":material/warning: **Missing release metadata**")
        st.write("The following release attributes could not be retrieved from Jira:")
        st.markdown("\n".join(f"- {field}" for field in release["missing_fields"]))
        st.caption("Update Jira release-planning fields or a linked parent/epic to complete traceability.")

st.subheader("Coverage analytics")
coverage_value = int(round(coverage.get("overall_coverage_pct", 0)))
st.progress(coverage_value, text=f"{coverage_value}% requirement coverage")
covered = coverage.get("covered_acs", 0)
partial = coverage.get("partially_covered_acs", 0)
uncovered = coverage.get("uncovered_acs", 0)
risk_counts = {
    level: sum(str(case.get("risk_level", "MEDIUM")).upper() == level for case in test_cases)
    for level in ("HIGH", "MEDIUM", "LOW")
}
analytics_left, analytics_right = st.columns(2)
with analytics_left, st.container(border=True):
    st.markdown("**Requirement coverage distribution**")
    coverage_chart = go.Figure()
    for label, value, color in (
        ("Covered", covered, "#16A34A"),
        ("Partial", partial, "#D97706"),
        ("Uncovered", uncovered, "#DC2626"),
    ):
        coverage_chart.add_bar(y=["Requirements"], x=[value], name=label, orientation="h", marker_color=color)
    coverage_chart.update_layout(
        barmode="stack", height=210, margin=dict(l=10, r=10, t=20, b=20),
        legend=dict(orientation="h", y=-0.25), xaxis_title="Requirement count",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(coverage_chart, width="stretch", config={"displayModeBar": False})
with analytics_right, st.container(border=True):
    st.markdown("**Test risk distribution**")
    risk_chart = go.Figure(go.Bar(
        x=list(risk_counts.values()), y=["High", "Medium", "Low"], orientation="h",
        marker_color=["#DC2626", "#D97706", "#16A34A"],
        text=list(risk_counts.values()), textposition="auto",
    ))
    risk_chart.update_layout(
        height=210, margin=dict(l=10, r=10, t=20, b=20), xaxis_title="Test case count",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(risk_chart, width="stretch", config={"displayModeBar": False})
st.caption("Coverage trend is unavailable until cross-sprint history persistence is enabled.")

st.subheader("Requirement traceability")
status_filter = st.multiselect(
    "Filter by coverage status", ["Covered", "Partial", "Uncovered"], placeholder="All statuses"
)
visible_rows = [
    row for row in traceability
    if not status_filter or any(status in row["Status"] for status in status_filter)
]
st.dataframe(
    pd.DataFrame(visible_rows), hide_index=True, width="stretch",
    column_config={
        "Requirement ID": st.column_config.TextColumn("Requirement ID", width="small"),
        "Requirement": st.column_config.TextColumn("Requirement", width="large"),
        "Coverage": st.column_config.ProgressColumn("Coverage", min_value=0, max_value=100, format="%.0f%%", width="medium"),
        "Tests": st.column_config.NumberColumn("Tests", width="small"),
        "Test cases": st.column_config.TextColumn("Mapped tests", width="medium"),
        "Risk": st.column_config.TextColumn("Risk", width="small"),
        "Status": st.column_config.MarkdownColumn("Status", width="small"),
        "Gap notes": st.column_config.TextColumn("Gap notes", width="large"),
    },
)
st.caption("Use the grid toolbar to search, sort, expand, or download requirement mappings.")

st.subheader("Risk and gap analysis")
risk_col, gap_col = st.columns(2)
with risk_col, st.container(border=True):
    st.markdown("**Quality findings**")
    findings = review.get("findings", [])
    if findings:
        for finding in findings:
            severity = finding.get("severity", "INFO")
            color = "red" if severity == "ERROR" else "orange" if severity == "WARNING" else "gray"
            st.badge(severity.title(), color=color)
            st.write(finding.get("description", ""))
    else:
        st.caption("No quality findings were reported.")
with gap_col, st.container(border=True):
    st.markdown("**Coverage gaps**")
    gap_rows = [row for row in traceability if "Covered" not in row["Status"]]
    review_gaps = review.get("gaps_detected", [])
    if gap_rows or review_gaps:
        for row in gap_rows:
            st.markdown(f"**{row['Requirement ID']}** · {row['Risk']} risk")
            st.caption(row["Gap notes"] or "Increase requirement-to-test coverage.")
        for gap in review_gaps:
            st.write(f"- {gap}")
    else:
        st.caption("No requirement coverage gaps were detected.")

st.subheader("AgentX recommendations")
if recommendations:
    recommendations_frame = pd.DataFrame(recommendations)
    recommendations_frame["Priority"] = recommendations_frame["Priority"].map(
        {"High": ":red-badge[High]", "Medium": ":orange-badge[Medium]", "Low": ":gray-badge[Low]"}
    )
    st.dataframe(
        recommendations_frame, hide_index=True, width="stretch",
        column_config={
            "Priority": st.column_config.MarkdownColumn("Priority", width="small"),
            "Recommendation": st.column_config.TextColumn("Recommended action", width="large"),
            "Source": st.column_config.TextColumn("Signal", width="medium"),
        },
    )
else:
    st.success("No additional AgentX actions are required for this run.")

st.subheader("Related Jira items")
if related_items:
    related_frame = pd.DataFrame(related_items)
    related_frame["status"] = related_frame["status"].map(jira_status_badge)
    st.dataframe(
        related_frame, hide_index=True, width="stretch",
        column_config={
            "key": st.column_config.TextColumn("Key", width="small"),
            "summary": st.column_config.TextColumn("Summary", width="large"),
            "type": st.column_config.TextColumn("Type", width="small"),
            "priority": st.column_config.TextColumn("Priority", width="small"),
            "status": st.column_config.MarkdownColumn("Status", width="small"),
            "assignee": st.column_config.TextColumn("Assignee", width="medium"),
            "url": st.column_config.LinkColumn("Jira", display_text="Open", width="small"),
        },
    )
else:
    st.caption("No directly related Jira work items were returned.")

with st.expander("Export analysis", icon=":material/download:"), st.container(horizontal=True):
    for label, endpoint, extension, mime in (
        ("Markdown", "markdown", "md", "text/markdown"),
        ("Xray JSON", "json", "json", "application/json"),
        ("RTM CSV", "csv", "csv", "text/csv"),
        ("Excel", "excel", "xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ("PDF", "pdf", "pdf", "application/pdf"),
    ):
        export_response = httpx.get(f"{API_BASE}/artifacts/{run_id}/export/{endpoint}", timeout=30.0)
        st.download_button(
            label, export_response.content,
            file_name=f"{data.get('story_id')}_analysis.{extension}", mime=mime,
            icon=":material/download:",
        )
