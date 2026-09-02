"""Zephyr Scale-inspired test cycle planning and execution page."""

from __future__ import annotations

import httpx
import pandas as pd
import streamlit as st

from ui.http_errors import format_api_error
from ui.release_display import render_release_information

API_BASE = "http://localhost:8000"
STATUS_OPTIONS = ["NOT_EXECUTED", "PASS", "FAIL", "BLOCKED"]
STATUS_LABELS = {
    "NOT_EXECUTED": "Not executed ⚪",
    "PASS": "Pass ✅",
    "FAIL": "Fail ❌",
    "BLOCKED": "Blocked ⛔",
}

st.set_page_config(
    page_title="Test execution - QE AgentX",
    page_icon=":material/play_circle:",
    layout="wide",
)
st.title("Test cycle execution")
st.caption("Plan, execute, evidence, and assess reusable test assets.")

run_id = st.session_state.get("run_id")
if not run_id:
    st.info("No generated test cycle is available. Start a run from Generate first.")
    st.stop()


def api_error(response: httpx.Response) -> None:
    st.error(format_api_error(response))
    st.stop()


response = httpx.get(f"{API_BASE}/execution/{run_id}", timeout=15.0)
if response.is_error:
    api_error(response)
cycle = response.json()
metrics = cycle.get("metrics") or {}
summary = cycle.get("readiness_summary") or {}
requirement = cycle.get("requirement") or {}

with st.container(border=True):
    st.subheader(cycle.get("name", "Test cycle"))
    st.caption(
        f"{cycle.get('cycle_id', '')} · {cycle.get('environment', '')} · "
        f"{cycle.get('execution_type', '')}"
    )
render_release_information(cycle.get("release_traceability") or {})

st.subheader("Requirement traceability")
traceability_rows = [
    {
        "Requirement": requirement.get("key", ""),
        "Test case": execution.get("tc_id", ""),
        "Title": execution.get("title", ""),
        "Acceptance criteria": execution.get("ac_ref", ""),
        "Status": STATUS_LABELS.get(execution.get("status", "NOT_EXECUTED"), "Not executed"),
    }
    for execution in (cycle.get("executions") or [])
]
st.dataframe(
    pd.DataFrame(traceability_rows),
    hide_index=True,
    width="stretch",
    column_config={
        "Requirement": st.column_config.TextColumn("Requirement", width="small"),
        "Test case": st.column_config.TextColumn("Test case", width="small"),
        "Title": st.column_config.TextColumn("Title", width="large"),
        "Acceptance criteria": st.column_config.TextColumn("AC reference", width="small"),
        "Status": st.column_config.TextColumn("Status", width="medium"),
    },
)

st.subheader("Execution progress")
first_metrics = st.columns(4, border=True)
first_metrics[0].metric("Total tests", metrics.get("total", 0))
first_metrics[1].metric("Executed", metrics.get("executed", 0))
first_metrics[2].metric("Passed", metrics.get("passed", 0))
first_metrics[3].metric("Failed", metrics.get("failed", 0))
second_metrics = st.columns(4, border=True)
second_metrics[0].metric("Blocked", metrics.get("blocked", 0))
second_metrics[1].metric("Not executed", metrics.get("not_executed", 0))
second_metrics[2].metric("Progress", f"{metrics.get('execution_progress_pct', 0):.1f}%")
second_metrics[3].metric("Pass rate", f"{metrics.get('pass_rate_pct', 0):.1f}%")
st.progress(int(metrics.get("execution_progress_pct", 0)))
st.caption(f"Linked defects: {metrics.get('defect_count', 0)}")

st.subheader("Test executions")
for execution in cycle.get("executions") or []:
    tc_id = execution.get("tc_id", "")
    current_status = execution.get("status", "NOT_EXECUTED")
    label = (
        f"{STATUS_LABELS.get(current_status, current_status)} | {tc_id} | "
        f"{execution.get('title', '')} | {execution.get('ac_ref', '')}"
    )
    with st.expander(label):
        status = st.selectbox(
            "Execution status",
            STATUS_OPTIONS,
            index=STATUS_OPTIONS.index(current_status),
            format_func=lambda value: STATUS_LABELS[value],
            key=f"status_{run_id}_{tc_id}",
        )
        comments = st.text_area(
            "Execution comments",
            value=execution.get("execution_comments", ""),
            key=f"comments_{run_id}_{tc_id}",
        )
        evidence_files = st.file_uploader(
            "Screenshots, logs, and supporting evidence",
            accept_multiple_files=True,
            key=f"evidence_{run_id}_{tc_id}",
            help="Each file is stored with this test execution. Maximum 20 MB per file.",
        )

        existing_defect_key = ""
        existing_defect_summary = ""
        defect_action = "None"
        new_defect_summary = ""
        new_defect_description = ""
        if status == "FAIL":
            defect_action = st.selectbox(
                "Defect action",
                ["None", "Link existing Jira bug", "Create new Jira bug"],
                key=f"defect_action_{run_id}_{tc_id}",
            )
            if defect_action == "Link existing Jira bug":
                existing_defect_key = st.text_input(
                    "Existing Jira bug key", key=f"defect_key_{run_id}_{tc_id}"
                )
                existing_defect_summary = st.text_input(
                    "Defect summary", key=f"defect_summary_{run_id}_{tc_id}"
                )
            elif defect_action == "Create new Jira bug":
                new_defect_summary = st.text_input(
                    "New bug summary", key=f"new_bug_summary_{run_id}_{tc_id}"
                )
                new_defect_description = st.text_area(
                    "New bug description", key=f"new_bug_description_{run_id}_{tc_id}"
                )

        if execution.get("defects"):
            st.markdown("**Linked defects:**")
            for defect in execution["defects"]:
                st.markdown(f"- `{defect.get('key', '')}` {defect.get('summary', '')}")
        if execution.get("evidence"):
            st.markdown("**Evidence:**")
            for evidence in execution["evidence"]:
                st.markdown(f"- {evidence.get('filename', '')} ({evidence.get('size', 0)} bytes)")

        if st.button(
            "Save execution",
            key=f"save_{run_id}_{tc_id}",
            type="primary",
            icon=":material/save:",
        ):
            if defect_action == "Link existing Jira bug" and not existing_defect_key.strip():
                st.error("Enter an existing Jira bug key.")
                st.stop()
            if defect_action == "Create new Jira bug" and not new_defect_summary.strip():
                st.error("Enter a summary for the new Jira bug.")
                st.stop()

            update = httpx.put(
                f"{API_BASE}/execution/{run_id}/tests/{tc_id}",
                json={
                    "status": status,
                    "execution_comments": comments,
                    "existing_defect_key": existing_defect_key or None,
                    "existing_defect_summary": existing_defect_summary,
                },
                timeout=30.0,
            )
            if update.is_error:
                api_error(update)

            for evidence_file in evidence_files:
                upload = httpx.post(
                    f"{API_BASE}/execution/{run_id}/tests/{tc_id}/evidence",
                    files={
                        "evidence": (
                            evidence_file.name,
                            evidence_file.getvalue(),
                            evidence_file.type,
                        )
                    },
                    timeout=30.0,
                )
                if upload.is_error:
                    api_error(upload)

            if defect_action == "Create new Jira bug":
                defect = httpx.post(
                    f"{API_BASE}/execution/{run_id}/tests/{tc_id}/defects",
                    json={
                        "summary": new_defect_summary,
                        "description": new_defect_description,
                    },
                    timeout=30.0,
                )
                if defect.is_error:
                    api_error(defect)
            st.rerun()

st.subheader("Release readiness")
with st.container(border=True):
    recommendation = summary.get("release_recommendation", "NOT READY")
    st.badge(
        recommendation.replace("_", " ").title(),
        color="red" if recommendation == "NO GO" else "orange" if recommendation in {"GO WITH RISK", "NOT READY"} else "green",
    )
    st.write(f"Requirement coverage: **{summary.get('requirement_coverage_pct', 0):.1f}%**")
    st.write(f"Risk assessment: **{summary.get('risk_assessment', 'MEDIUM')}**")
    if summary.get("failure_analysis"):
        st.markdown("**Failure analysis**")
        for failure in summary["failure_analysis"]:
            st.markdown(
                f"- `{failure.get('tc_id', '')}` {failure.get('title', '')}: "
                f"{failure.get('comments') or 'No execution comments'}"
            )
    if summary.get("linked_defects"):
        st.markdown("**Linked defects:** " + ", ".join(summary["linked_defects"]))
