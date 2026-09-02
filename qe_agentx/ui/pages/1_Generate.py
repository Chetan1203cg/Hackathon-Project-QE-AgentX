"""
ui/pages/1_Generate.py
=======================
Pipeline trigger page — enter a Jira story ID and launch the agent pipeline.
"""

from __future__ import annotations

import time

import httpx
import streamlit as st

from ui.copilot_context import (
    build_copilot_context,
    microsoft_copilot_url,
    vscode_copilot_url,
)
from ui.http_errors import format_api_error
from ui.release_display import render_release_information

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Test generation - QE AgentX",
    page_icon=":material/auto_awesome:",
    layout="wide",
)
st.title("Test generation")
st.caption("Generate traceable QA assets from a Jira work item and release context.")


def render_copilot_actions(
    error: str,
    *,
    jira_key: str,
    release: str,
    environment: str,
    run_id: str | None = None,
    status_data: dict | None = None,
) -> None:
    """Render portable troubleshooting actions using all available run context."""
    status_data = status_data or {}
    available_context = status_data.get("copilot_context") or {}
    context = build_copilot_context(
        error=error,
        jira_key=jira_key,
        release_version=release,
        target_environment=environment,
        run_id=run_id,
        jira_context=available_context.get("jira"),
        status_data=status_data,
        artifacts={
            key: value
            for key, value in available_context.items()
            if key != "jira" and value
        },
    )

    with st.container(border=True):
        st.caption("Troubleshoot with Copilot")
        with st.container(horizontal=True):
            st.link_button(
                "Ask Microsoft Copilot",
                microsoft_copilot_url(context),
                icon=":material/auto_awesome:",
                help="Open Microsoft Copilot in a new tab with this error context.",
            )
            st.link_button(
                "Ask GitHub Copilot (VS Code)",
                vscode_copilot_url(context),
                icon=":material/code:",
                help="Open GitHub Copilot Chat in VS Code with this error context.",
            )
            st.download_button(
                "Export context",
                data=context,
                file_name=f"{jira_key or 'qe-agentx'}_copilot_context.md",
                mime="text/markdown",
                icon=":material/download:",
                help="Download the complete context for GitHub Copilot Chat.",
            )
        with st.expander("Context included"):
            st.code(context, language=None, wrap_lines=True, height=320)

# ------------------------------------------------------------------ #
# Input form
# ------------------------------------------------------------------ #
with st.form("run_form", border=True):
    story_id = st.text_input(
        "Jira work item",
        placeholder="e.g. NGWD6-50396",
        help="The Jira issue key of the user story to analyse",
    )
    release_version = st.text_input(
        "FA Release Version override",
        placeholder="Automatically detected from Jira",
        help="Leave blank to use Jira release metadata. Enter a value only to override it.",
    )
    target_environment = st.selectbox("Target environment", ["test", "staging", "production"])
    project_key = st.text_input("Xray project key", value="QA", help="Target Xray project")
    export_to_xray = st.checkbox("Export to Xray on completion", value=False)
    submitted = st.form_submit_button(
        "Run QE AgentX",
        icon=":material/play_arrow:",
        type="primary",
        width="stretch",
    )

if submitted and story_id:
    with st.spinner("Triggering pipeline..."):
        try:
            resp = httpx.post(
                f"{API_BASE}/pipeline/run",
                json={
                    "story_id": story_id.strip().upper(),
                    "release_version": release_version.strip(),
                    "target_environment": target_environment,
                    "project_key": project_key,
                    "export_to_xray": export_to_xray,
                },
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()
            run_id = data["run_id"]
            st.session_state["run_id"] = run_id
            st.session_state["story_id"] = story_id.strip().upper()
            st.session_state["release_version"] = release_version.strip()
            st.session_state["target_environment"] = target_environment
            st.success(f"Pipeline started · Run ID `{run_id}`", icon=":material/check_circle:")
        except httpx.HTTPStatusError as exc:
            error = format_api_error(exc.response)
            st.error(error)
            render_copilot_actions(
                error,
                jira_key=story_id.strip().upper(),
                release=release_version.strip(),
                environment=target_environment,
            )
            st.stop()
        except httpx.RequestError as exc:
            error = f"Cannot connect to QE AgentX API at {API_BASE}: {exc}"
            st.error(error)
            render_copilot_actions(
                error,
                jira_key=story_id.strip().upper(),
                release=release_version.strip(),
                environment=target_environment,
            )
            st.stop()

# ------------------------------------------------------------------ #
# Live status polling
# ------------------------------------------------------------------ #
if "run_id" in st.session_state:
    run_id = st.session_state["run_id"]
    st.subheader("Pipeline status")

    status_placeholder = st.empty()
    progress_bar = st.progress(0)
    release_placeholder = st.empty()
    hitl_placeholder = st.empty()

    STAGES = [
        "Analysing Requirements",
        "Building Scenario Tree",
        "Generating Test Cases",
        "Synthesising Test Data",
        "Calculating Coverage",
        "Building RTM",
        "Reviewing Quality",
        "Generating Report",
        "Validating i18n, ACS, and AEM Schemas",
        "Calculating Release Decision",
    ]

    while True:
        try:
            status_resp = httpx.get(f"{API_BASE}/pipeline/{run_id}/status", timeout=10.0)
            status_data = status_resp.json()
        except Exception:
            time.sleep(2)
            continue

        status = status_data.get("status", "")
        stage = status_data.get("current_stage", "")
        release_traceability = status_data.get("release_traceability") or {}
        if release_traceability:
            with release_placeholder.container():
                render_release_information(release_traceability)

        # Update progress
        stage_idx = next((i for i, s in enumerate(STAGES) if s in stage), 0)
        progress_bar.progress(int((stage_idx + 1) / len(STAGES) * 100))
        status_placeholder.info(f"**Stage:** {stage}  |  **Status:** {status}")

        # HITL gate
        if status == "awaiting_hitl":
            ambiguities = status_data.get("ambiguities", [])
            with hitl_placeholder.container():
                st.warning(
                    "The agent detected ambiguities and requires your input before proceeding.",
                    icon=":material/warning:",
                )
                if ambiguities:
                    st.markdown("**Detected questions**")
                for q in ambiguities:
                    st.markdown(f"- {q}")
                hitl_input = st.text_area(
                    "Your clarification",
                    key=f"hitl_input_{run_id}",
                    help=(
                        "Add requirements, assumptions, or preferences. Leave blank if "
                        "the Jira ticket already contains sufficient information."
                    ),
                )
                st.caption(
                    "If no additional input is required, leave the field blank and "
                    "select Submit and resume task."
                )
                with st.container(horizontal=True):
                    if st.button(
                        "Submit and resume task",
                        key=f"hitl_submit_{run_id}",
                        icon=":material/play_arrow:",
                        type="primary",
                        help="Continue using the Jira ticket and any clarification provided.",
                    ):
                        hitl_response = httpx.post(
                            f"{API_BASE}/pipeline/{run_id}/hitl",
                            json={"response": hitl_input},
                            timeout=10.0,
                        )
                        hitl_response.raise_for_status()
                        st.rerun()
                    if st.button(
                        "Cancel",
                        key=f"hitl_cancel_{run_id}",
                        icon=":material/close:",
                        help="Stop the current task without generating further results.",
                    ):
                        cancel_response = httpx.post(
                            f"{API_BASE}/pipeline/{run_id}/cancel",
                            timeout=10.0,
                        )
                        cancel_response.raise_for_status()
                        st.rerun()
            break

        elif status == "completed":
            progress_bar.progress(100)
            status_placeholder.success(
                "Pipeline completed. Continue to Test execution or Coverage intelligence.",
                icon=":material/check_circle:",
            )
            break

        elif status == "failed":
            errors = status_data.get("errors", [])
            error = f"Pipeline failed: {'; '.join(errors)}"
            status_placeholder.error(error)
            render_copilot_actions(
                error,
                jira_key=st.session_state.get("story_id", ""),
                release=st.session_state.get("release_version", ""),
                environment=st.session_state.get("target_environment", ""),
                run_id=run_id,
                status_data=status_data,
            )
            break

        elif status == "cancelled":
            status_placeholder.warning("Task cancelled. No further processing will run.")
            break

        time.sleep(3)
