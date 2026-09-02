"""QE AgentX Streamlit application shell and scalable module navigation."""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="QE AgentX",
    page_icon=":material/verified:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def overview() -> None:
    st.title("QE AgentX")
    st.caption("QA intelligence and release-readiness platform")
    st.subheader("Quality workspace")
    metrics = st.columns(3, border=True)
    metrics[0].metric("Coverage target", "90%+", "Per requirement")
    metrics[1].metric("Quality threshold", "85/100", "Review score")
    metrics[2].metric("Traceability", "End to end", "Jira to evidence")
    st.markdown(
        "Use **Test generation** to analyze a Jira work item, then continue through "
        "**Test execution** and **Coverage intelligence**."
    )


page = st.navigation(
    {
        "Workspace": [
            st.Page(overview, title="Overview", icon=":material/home:", default=True),
            st.Page(
                "pages/1_Generate.py",
                title="Test generation",
                icon=":material/auto_awesome:",
                url_path="Generate",
            ),
            st.Page(
                "pages/2_Execution.py",
                title="Test execution",
                icon=":material/play_circle:",
                url_path="Execution",
            ),
            st.Page(
                "pages/3_Coverage.py",
                title="Coverage intelligence",
                icon=":material/analytics:",
                url_path="Coverage",
            ),
        ]
    },
    position="sidebar",
)

with st.sidebar:
    st.markdown("**AgentX**")
    st.caption("Precision · Traceability · Readiness")

page.run()
