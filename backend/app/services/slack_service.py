"""
services/slack_service.py — Slack Block Kit Alert Dispatcher
------------------------------------------------------------
Constructs and dispatches rich interactive Block Kit payloads for
statistical anomalies and critical sentiment drift alerts.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class SlackNotificationService:

    @staticmethod
    def build_anomaly_block_kit_payload(
        product_name: str,
        aspect: str,
        severity: str,
        z_score: float,
        star_impact: float,
        message: str,
        evidence_snippets: List[str],
        dashboard_url: str,
        alert_id: str,
    ) -> Dict[str, Any]:
        """
        Builds Slack Block Kit JSON structure for anomaly notification with interactive actions.
        """
        severity_emoji = {
            "CRITICAL": ":rotating_light:",
            "HIGH": ":warning:",
            "MEDIUM": ":large_yellow_circle:",
            "LOW": ":information_source:",
        }.get(severity.upper(), ":warning:")

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{severity_emoji} BrandGuard Anomaly Alert: {aspect}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Product:*\n{product_name}"},
                    {"type": "mrkdwn", "text": f"*Severity:*\n`{severity.upper()}`"},
                    {"type": "mrkdwn", "text": f"*Statistical Drift:*\n`Z = {z_score:.2f}σ`"},
                    {"type": "mrkdwn", "text": f"*Star Drag:*\n`{star_impact:+.2f}★`"},
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Diagnosis:*\n{message}",
                },
            },
        ]

        if evidence_snippets:
            quote_text = "\n".join([f"> \"_{s[:160]}..._\"" for s in evidence_snippets[:2]])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Medoid Customer Evidence:*\n{quote_text}",
                },
            })

        # Interactive actions
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View in Dashboard", "emoji": True},
                    "style": "primary",
                    "url": f"{dashboard_url}?aspect={aspect}&highlightAlert={alert_id}",
                    "action_id": "open_dashboard",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Acknowledge", "emoji": True},
                    "action_id": f"ack_alert_{alert_id}",
                },
            ],
        })

        return {"blocks": blocks}

    @classmethod
    async def dispatch_alert(
        cls,
        webhook_url: Optional[str],
        payload: Dict[str, Any],
    ) -> bool:
        """Dispatches Block Kit payload via Slack incoming webhook."""
        url = webhook_url or getattr(settings, "SLACK_WEBHOOK_URL", None)
        if not url:
            logger.info("Slack webhook URL not configured; skipping dispatch.")
            return False

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(url, json=payload)
                return res.status_code == 200
        except Exception as exc:
            logger.error("Failed to send Slack alert: %s", exc)
            return False
