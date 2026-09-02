"""Normalize sprint and release metadata collected from related Jira work items."""

from __future__ import annotations

import json
import re
from typing import Any

NOT_AVAILABLE = "Release Information Not Available in Jira Metadata"


def build_release_traceability(
    stories: list[dict[str, Any]],
    project_versions: list[dict[str, Any]] | None = None,
    *,
    traversal_truncated: bool = False,
) -> dict[str, Any]:
    """Build one traceability contract, preferring metadata on the selected issue."""
    primary = stories[0]
    ordered = [primary, *stories[1:]]

    sprint, sprint_source = _select_sprint(ordered)
    fix_version, fix_source = _select_fix_version(ordered)
    cw_release, cw_source = _find_named_value(
        ordered, r"(?:calendar\s*week|\bcw\b)", r"\bCW\s*[-_]?\s*\d{1,2}\b"
    )
    fa_release, fa_source = _find_named_value(
        ordered,
        r"(?:\bfa\b|feature\s*app).*release|release.*(?:\bfa\b|feature\s*app)",
        r"\bFA(?:\s+Release)?[\s:_-]+[A-Za-z0-9._-]+",
    )
    environment, environment_source = _find_named_value(
        ordered, r"environment|deployment", None
    )
    planned_date, date_source = _planned_release_date(
        ordered, fix_version, project_versions or []
    )

    missing = []
    values = {
        "sprint": sprint.get("name") if sprint else None,
        "cw_release": cw_release,
        "fa_release_version": fa_release,
    }
    labels = {
        "sprint": "Sprint",
        "cw_release": "CW Release",
        "fa_release_version": "FA Release Version",
    }
    for key, value in values.items():
        if not value:
            missing.append(labels[key])

    source_keys = sorted(
        {
            source
            for source in (
                sprint_source,
                fix_source,
                cw_source,
                fa_source,
                environment_source,
                date_source,
            )
            if source
        }
    )

    return {
        "jira_key": primary.get("key", ""),
        "jira_type": primary.get("type") or NOT_AVAILABLE,
        "jira_summary": primary.get("summary", ""),
        "jira_url": primary.get("link", ""),
        "sprint": values["sprint"] or NOT_AVAILABLE,
        "sprint_status": (sprint or {}).get("state") or NOT_AVAILABLE,
        "cw_release": cw_release or NOT_AVAILABLE,
        "fa_release_version": fa_release or NOT_AVAILABLE,
        "fix_version": (fix_version or {}).get("name") or NOT_AVAILABLE,
        "planned_release_date": planned_date or NOT_AVAILABLE,
        "environment": environment or NOT_AVAILABLE,
        "components": primary.get("component") or NOT_AVAILABLE,
        "labels": primary.get("labels") or [],
        "source_issue_keys": source_keys or [primary.get("key", "")],
        "related_issue_keys_checked": [story.get("key", "") for story in stories[1:]],
        "release_fields": _all_release_fields(ordered),
        "missing_fields": missing,
        "availability_message": (
            f"{NOT_AVAILABLE}: {', '.join(missing)}" if missing else ""
        ),
        "traversal_truncated": traversal_truncated,
    }


def _select_sprint(stories: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, str | None]:
    for story in stories:
        sprints = story.get("sprints") or []
        if sprints:
            active = next((item for item in sprints if item.get("state") == "active"), None)
            return active or sprints[-1], story.get("key")
    return None, None


def _select_fix_version(
    stories: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, str | None]:
    for story in stories:
        versions = story.get("fix_versions") or []
        if versions:
            unreleased = next((item for item in versions if not item.get("released")), None)
            return unreleased or versions[0], story.get("key")
    return None, None


def _find_named_value(
    stories: list[dict[str, Any]], name_pattern: str, value_pattern: str | None
) -> tuple[str | None, str | None]:
    name_regex = re.compile(name_pattern, re.IGNORECASE)
    value_regex = re.compile(value_pattern, re.IGNORECASE) if value_pattern else None
    for story in stories:
        for field in story.get("release_fields") or []:
            name = field.get("name", "")
            text = _value_text(field.get("value"))
            if not text:
                continue
            if name_regex.search(name):
                match = value_regex.search(text) if value_regex else None
                return (match.group(0) if match else text), story.get("key")
            if value_regex:
                match = value_regex.search(text)
                if match:
                    return match.group(0), story.get("key")
    return None, None


def _planned_release_date(
    stories: list[dict[str, Any]],
    fix_version: dict[str, Any] | None,
    project_versions: list[dict[str, Any]],
) -> tuple[str | None, str | None]:
    if fix_version and fix_version.get("release_date"):
        return fix_version["release_date"], stories[0].get("key")
    value, source = _find_named_value(stories, r"(?:fix|planned|target|release).*date", None)
    if value:
        return value, source
    if fix_version:
        match = next(
            (version for version in project_versions if version.get("id") == fix_version.get("id")),
            None,
        )
        if match and match.get("releaseDate"):
            return match["releaseDate"], stories[0].get("key")
    return None, None


def _all_release_fields(stories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"source_issue": story.get("key"), **field}
        for story in stories
        for field in (story.get("release_fields") or [])
        if _value_text(field.get("value"))
    ]


def _value_text(value: Any) -> str:
    if value in (None, "", [], {}):
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and "value" in value:
        return str(value["value"])
    if isinstance(value, dict) and "name" in value:
        return str(value["name"])
    if isinstance(value, list):
        return ", ".join(filter(None, (_value_text(item) for item in value)))
    return json.dumps(value, default=str)
