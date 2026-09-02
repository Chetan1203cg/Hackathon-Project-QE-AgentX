"""
integrations/jira_client.py
============================
Jira REST API v3 client.
Refactored from the existing jira_to_testcases.py with clean class interface.
"""

from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser

import httpx

from config.settings import Settings
from integrations.release_traceability import build_release_traceability

logger = logging.getLogger(__name__)


class _HTMLTextExtractor(HTMLParser):
    """Strip HTML tags to plain text (ported from generate_testcases.py)."""

    def __init__(self):
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(self._parts).strip()


def _strip_html(html: str) -> str:
    p = _HTMLTextExtractor()
    p.feed(html or "")
    return re.sub(r"\s+", " ", p.get_text()).strip()


class JiraClient:
    """Thread-safe Jira REST API v3 client using httpx."""

    MAX_RELATED_ISSUES = 100

    def __init__(self, settings: Settings):
        self._base_url = settings.jira_base_url.rstrip("/")
        self._auth = settings.jira_auth
        self._client = httpx.Client(
            auth=self._auth,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=30.0,
        )

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def get_story(self, issue_key: str) -> dict:
        """
        Fetch a Jira issue and return a normalised story dict compatible
        with the QE AgentX pipeline.
        """
        primary_story = self._fetch_story(issue_key)
        stories = [primary_story]
        visited = {issue_key}
        traversal_truncated = False

        with ThreadPoolExecutor(max_workers=10) as executor:
            direct_keys = list(dict.fromkeys(primary_story.get("relationship_keys", [])))
            if len(direct_keys) >= self.MAX_RELATED_ISSUES:
                traversal_truncated = True
            direct_keys = direct_keys[: self.MAX_RELATED_ISSUES - 1]
            visited.update(direct_keys)
            direct_stories = [
                story
                for story in executor.map(self._fetch_related_story, direct_keys)
                if story
            ]
            stories.extend(direct_stories)

            hierarchy_keys = list(dict.fromkeys(
                key
                for story in direct_stories
                for key in (story.get("parent_key"), story.get("epic_key"))
                if key and key not in visited
            ))
            remaining = self.MAX_RELATED_ISSUES - len(visited)
            if len(hierarchy_keys) > remaining:
                traversal_truncated = True
            hierarchy_keys = hierarchy_keys[:remaining]
            visited.update(hierarchy_keys)
            stories.extend(
                story
                for story in executor.map(self._fetch_related_story, hierarchy_keys)
                if story
            )

        project_versions = self._get_project_versions(stories[0].get("project_key", ""))
        stories[0]["release_traceability"] = build_release_traceability(
            stories,
            project_versions,
            traversal_truncated=traversal_truncated,
        )
        stories[0]["related_work_items"] = stories[1:]
        return stories[0]

    def _fetch_related_story(self, issue_key: str) -> dict | None:
        try:
            return self._fetch_story(issue_key)
        except httpx.HTTPError:
            logger.warning("[JiraClient] Could not enrich linked issue %s", issue_key)
            return None

    def _fetch_story(self, issue_key: str) -> dict:
        url = f"{self._base_url}/rest/api/3/issue/{issue_key}"
        response = self._client.get(url, params={"expand": "names"})
        response.raise_for_status()
        return self._normalise(response.json())

    def _get_project_versions(self, project_key: str) -> list[dict]:
        if not project_key:
            return []
        response = self._client.get(
            f"{self._base_url}/rest/api/3/project/{project_key}/versions"
        )
        if response.is_error:
            logger.warning("[JiraClient] Could not retrieve project release metadata")
            return []
        return response.json()

    def post_comment(self, issue_key: str, comment_text: str) -> None:
        """Add a plain-text comment to a Jira issue."""
        url = f"{self._base_url}/rest/api/3/issue/{issue_key}/comment"
        payload = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": comment_text}],
                    }
                ],
            }
        }
        resp = self._client.post(url, json=payload)
        resp.raise_for_status()
        logger.info("[JiraClient] Comment posted to %s", issue_key)

    def create_bug(
        self,
        project_key: str,
        summary: str,
        description: str,
        linked_issue_key: str,
    ) -> dict:
        """Create a Jira bug and link it to the source requirement."""
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": self._adf_document(description),
                "issuetype": {"name": "Bug"},
            }
        }
        response = self._client.post(f"{self._base_url}/rest/api/3/issue", json=payload)
        response.raise_for_status()
        bug = response.json()
        self.link_issues(linked_issue_key, bug["key"])
        return {"key": bug["key"], "summary": summary, "source": "created"}

    def link_issues(self, requirement_key: str, defect_key: str) -> None:
        """Create a Jira relationship between a requirement and existing defect."""
        payload = {
            "type": {"name": "Relates"},
            "inwardIssue": {"key": requirement_key},
            "outwardIssue": {"key": defect_key},
        }
        response = self._client.post(
            f"{self._base_url}/rest/api/3/issueLink", json=payload
        )
        response.raise_for_status()

    @staticmethod
    def _adf_document(text: str) -> dict:
        return {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": text or "No description provided"}],
                }
            ],
        }

    def get_sprints_for_issue(self, issue_key: str) -> str:
        """Return the sprint name for an issue, or empty string."""
        story = self.get_story(issue_key)
        return story.get("sprint", "")

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    def _normalise(self, raw: dict) -> dict:
        """Map Jira API v3 response to the flat dict used by agents."""
        fields = raw.get("fields", {})
        names = raw.get("names", {})

        # Description — can be ADF (Atlassian Document Format) or plain text
        description_raw = fields.get("description") or {}
        if isinstance(description_raw, dict):
            description = self._extract_adf_text(description_raw)
        else:
            description = _strip_html(str(description_raw))

        sprint_field_id = next(
            (field_id for field_id, name in names.items() if name.lower() == "sprint"),
            "customfield_10020",
        )
        sprints = [
            {
                "id": sprint.get("id"),
                "name": sprint.get("name", ""),
                "state": sprint.get("state", ""),
                "start_date": sprint.get("startDate", ""),
                "end_date": sprint.get("endDate", ""),
                "complete_date": sprint.get("completeDate", ""),
            }
            for sprint in (fields.get(sprint_field_id) or [])
            if isinstance(sprint, dict)
        ]

        # Sprint name
        sprint_name = ""
        for sprint in sprints:
            if sprint.get("state") == "active":
                sprint_name = sprint.get("name", "")
                break
        if not sprint_name:
            sprint_name = sprints[-1].get("name", "") if sprints else ""

        comments = []
        for comment in (fields.get("comment") or {}).get("comments", []):
            body = comment.get("body") or {}
            comments.append({
                "author": (comment.get("author") or {}).get("displayName", ""),
                "created": comment.get("created", ""),
                "body": self._extract_adf_text(body) if isinstance(body, dict) else str(body),
            })

        attachments = [
            {
                "filename": attachment.get("filename", ""),
                "mime_type": attachment.get("mimeType", ""),
                "size": attachment.get("size", 0),
                "content_url": attachment.get("content", ""),
            }
            for attachment in (fields.get("attachment") or [])
        ]

        related_issues = []
        for issue_link in (fields.get("issuelinks") or []):
            linked_issue = issue_link.get("outwardIssue") or issue_link.get("inwardIssue") or {}
            if linked_issue:
                related_issues.append({
                    "relationship": (issue_link.get("type") or {}).get(
                        "outward" if issue_link.get("outwardIssue") else "inward", ""
                    ),
                    "key": linked_issue.get("key", ""),
                    "summary": (linked_issue.get("fields") or {}).get("summary", ""),
                })

        parent_key = (fields.get("parent") or {}).get("key", "")
        subtask_keys = [item.get("key", "") for item in (fields.get("subtasks") or [])]
        epic_key = ""
        release_fields = []
        release_name_pattern = re.compile(
            r"sprint|release|calendar\s*week|\bcw\b|fix|version|deploy|environment|epic",
            re.IGNORECASE,
        )
        for field_id, name in names.items():
            value = fields.get(field_id)
            if name.lower() == "epic link" and isinstance(value, str):
                epic_key = value
            if release_name_pattern.search(name) and value not in (None, "", [], {}):
                if isinstance(value, dict) and value.get("type") == "doc":
                    value = self._extract_adf_text(value)
                release_fields.append({"field_id": field_id, "name": name, "value": value})

        relationship_keys = [
            parent_key,
            epic_key,
            *subtask_keys,
            *(item.get("key", "") for item in related_issues),
        ]
        fix_versions = [
            {
                "id": version.get("id"),
                "name": version.get("name", ""),
                "released": version.get("released", False),
                "release_date": version.get("releaseDate", ""),
            }
            for version in (fields.get("fixVersions") or [])
        ]

        return {
            "key": raw.get("key", ""),
            "summary": fields.get("summary", ""),
            "link": f"{self._base_url}/browse/{raw.get('key', '')}",
            "sprint": sprint_name,
            "sprints": sprints,
            "type": (fields.get("issuetype") or {}).get("name", ""),
            "priority": (fields.get("priority") or {}).get("name", ""),
            "status": (fields.get("status") or {}).get("name", ""),
            "component": ", ".join(
                c.get("name", "") for c in (fields.get("components") or [])
            ),
            "assignee": (fields.get("assignee") or {}).get("displayName", ""),
            "description": description,
            "comments": comments,
            "attachments": attachments,
            "related_issues": related_issues,
            "labels": fields.get("labels") or [],
            "project_key": (fields.get("project") or {}).get("key", ""),
            "parent_key": parent_key,
            "subtask_keys": subtask_keys,
            "epic_key": epic_key,
            "relationship_keys": list(dict.fromkeys(filter(None, relationship_keys))),
            "fix_versions": fix_versions,
            "release_fields": release_fields,
        }

    def _extract_adf_text(self, adf: dict) -> str:
        """Recursively extract plain text from Atlassian Document Format."""
        texts: list[str] = []
        for content in adf.get("content", []):
            node_type = content.get("type", "")
            if node_type == "text":
                texts.append(content.get("text", ""))
            elif "content" in content:
                texts.append(self._extract_adf_text(content))
        return " ".join(texts).strip()

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
