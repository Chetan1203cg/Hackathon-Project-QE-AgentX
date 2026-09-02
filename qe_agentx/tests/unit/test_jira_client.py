"""Tests for Jira issue normalization."""

from __future__ import annotations

from integrations.jira_client import JiraClient


def test_normalise_includes_ticket_review_context():
    client = JiraClient.__new__(JiraClient)
    client._base_url = "https://jira.example"
    raw = {
        "key": "NGWD6-1",
        "fields": {
            "summary": "Feature update",
            "description": {
                "type": "doc",
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": "AC details"}]}],
            },
            "comment": {
                "comments": [{
                    "author": {"displayName": "QA User"},
                    "created": "2026-09-01",
                    "body": {
                        "type": "doc",
                        "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Extra requirement"}]}],
                    },
                }],
            },
            "attachment": [{
                "filename": "design.png",
                "mimeType": "image/png",
                "size": 123,
                "content": "https://jira.example/attachment/1",
            }],
            "issuelinks": [{
                "type": {"outward": "relates to"},
                "outwardIssue": {"key": "NGWD6-2", "fields": {"summary": "Related work"}},
            }],
            "labels": ["nbd-2026"],
            "environment": {
                "type": "doc",
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Test"}]}],
            },
        },
        "names": {"environment": "Environment"},
    }

    story = client._normalise(raw)

    assert story["comments"][0]["body"] == "Extra requirement"
    assert story["attachments"][0]["filename"] == "design.png"
    assert story["related_issues"][0]["key"] == "NGWD6-2"
    assert story["labels"] == ["nbd-2026"]
    assert story["release_fields"][0]["value"] == "Test"