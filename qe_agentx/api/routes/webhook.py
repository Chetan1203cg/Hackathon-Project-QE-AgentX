"""
api/routes/webhook.py
======================
Jira webhook listener for change detection.
Validates HMAC-SHA256 signature before processing.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks

logger = logging.getLogger(__name__)
router = APIRouter()

WEBHOOK_SECRET = os.getenv("JIRA_WEBHOOK_SECRET", "")


@router.post("/jira")
async def jira_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receive Jira issue update events.
    Re-triggers RequirementAgent for the changed story.
    """
    body = await request.body()

    # Validate HMAC signature (skip in dev if secret not configured)
    if WEBHOOK_SECRET:
        signature = request.headers.get("X-Hub-Signature", "")
        if not _verify_signature(body, signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()
    issue_key = (payload.get("issue") or {}).get("key", "")

    if not issue_key:
        return {"status": "ignored", "reason": "no issue key in payload"}

    event_type = payload.get("webhookEvent", "")
    if event_type not in ("jira:issue_updated", "jira:issue_created"):
        return {"status": "ignored", "reason": f"unhandled event: {event_type}"}

    logger.info("[Webhook] Jira change detected: %s (%s)", issue_key, event_type)

    # Queue a re-analysis in background (import here to avoid circular imports)
    from api.routes.pipeline import trigger_pipeline, RunRequest
    background_tasks.add_task(
        _queue_reanalysis, issue_key
    )

    return {"status": "accepted", "issue_key": issue_key}


def _verify_signature(body: bytes, signature: str) -> bool:
    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


async def _queue_reanalysis(issue_key: str):
    """Re-trigger pipeline for a changed story."""
    from api.routes.pipeline import trigger_pipeline, RunRequest
    from fastapi import BackgroundTasks as BT
    logger.info("[Webhook] Queuing re-analysis for: %s", issue_key)
    # In production: publish to Service Bus queue for async processing
