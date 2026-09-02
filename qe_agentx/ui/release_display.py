"""Compact Streamlit presentation for normalized Jira release traceability."""

from __future__ import annotations

from html import escape

import streamlit as st

NOT_AVAILABLE = "Release Information Not Available in Jira Metadata"
RELEASE_FIELDS = (
    ("Jira key", "jira_key"),
    ("Sprint", "sprint"),
    ("Sprint status", "sprint_status"),
    ("CW release", "cw_release"),
    ("FA release version", "fa_release_version"),
    ("Fix version", "fix_version"),
    ("Planned release", "planned_release_date"),
    ("Environment", "environment"),
)


def _display_value(value: object) -> str:
    text = str(value or "Unavailable")
    if text.startswith(NOT_AVAILABLE):
        return "Unavailable"
    return text


def release_metadata_html(release: dict) -> str:
    """Return a compact, wrapping metadata grid with complete values."""
    cards = []
    for label, key in RELEASE_FIELDS:
        value = _display_value(release.get(key))
        status_class = ""
        if key == "sprint_status":
            normalized = value.lower()
            if normalized == "active":
                status_class = " release-metadata__value--success"
            elif normalized in {"blocked", "failed"}:
                status_class = " release-metadata__value--critical"
            else:
                status_class = " release-metadata__value--neutral"
            value = value.title()
        cards.append(
            '<div class="release-metadata__card">'
            f'<dt class="release-metadata__label">{escape(label)}</dt>'
            f'<dd class="release-metadata__value{status_class}">{escape(value)}</dd>'
            "</div>"
        )

    return f"""
    <style>
      .release-metadata {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(175px, 1fr));
        gap: 10px;
        margin: 0 0 10px;
      }}
      .release-metadata__card {{
        box-sizing: border-box;
        min-width: 0;
        min-height: 72px;
        padding: 10px 12px;
        border: 1px solid #D1D5DB;
        border-radius: 6px;
        background: #FFFFFF;
        box-shadow: 0 1px 2px rgba(17, 24, 39, 0.04);
      }}
      .release-metadata__label {{
        margin: 0 0 5px;
        color: #6B7280;
        font-family: "IBM Plex Sans", "Source Sans", sans-serif;
        font-size: 11px;
        font-weight: 500;
        line-height: 1.25;
      }}
      .release-metadata__value {{
        margin: 0;
        color: #111827;
        font-family: "IBM Plex Sans", "Source Sans", sans-serif;
        font-size: 16px;
        font-weight: 600;
        line-height: 1.3;
        overflow-wrap: anywhere;
        white-space: normal;
      }}
      .release-metadata__value--success::before,
      .release-metadata__value--critical::before,
      .release-metadata__value--neutral::before {{
        content: "";
        display: inline-block;
        width: 7px;
        height: 7px;
        margin: 0 7px 2px 0;
        border-radius: 50%;
        background: #6B7280;
      }}
      .release-metadata__value--success::before {{ background: #16A34A; }}
      .release-metadata__value--critical::before {{ background: #DC2626; }}
      @media (max-width: 520px) {{
        .release-metadata {{
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 8px;
        }}
        .release-metadata__card {{
          min-height: 66px;
          padding: 9px 10px;
        }}
        .release-metadata__value {{ font-size: 14px; }}
      }}
    </style>
    <dl class="release-metadata">{"".join(cards)}</dl>
    """


def render_release_metadata_grid(release: dict) -> None:
    """Render complete release values in a compact responsive grid."""
    if release:
        st.html(release_metadata_html(release))


def render_release_information(release: dict) -> None:
    """Display release traceability with compact metadata and actions."""
    if not release:
        return

    st.subheader("Release information")
    render_release_metadata_grid(release)

    if release.get("availability_message"):
        st.warning(release["availability_message"], icon=":material/info:")
    if release.get("jira_url"):
        st.link_button(
            "Open Jira work item",
            release["jira_url"],
            icon=":material/open_in_new:",
            type="tertiary",
            help="Open the source Jira work item in a new tab.",
        )
