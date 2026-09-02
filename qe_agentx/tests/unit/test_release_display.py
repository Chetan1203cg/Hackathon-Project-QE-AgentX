"""Tests for compact, complete release metadata rendering."""

from ui.release_display import release_metadata_html


def test_release_metadata_html_preserves_full_values_and_escapes_markup():
    output = release_metadata_html({
        "jira_key": "NGWD6-52184",
        "sprint": "CMS Sprint 278 - Accessibility delivery",
        "sprint_status": "active",
        "fix_version": "IDHUB 3.200.278.x <candidate>",
    })

    assert "NGWD6-52184" in output
    assert "CMS Sprint 278 - Accessibility delivery" in output
    assert "IDHUB 3.200.278.x &lt;candidate&gt;" in output
    assert "text-overflow" not in output
    assert "white-space: normal" in output
    assert "min-height: 72px" in output