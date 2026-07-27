"""
services/alert_service.py
--------------------------
Business logic for anomaly scanning and alert management.

Responsibilities:
  1. scan()       — Run anomaly detector on stored rows, write Alert rows (dedup-safe)
  2. list_alerts()— Return alerts for a product, with optional filters
  3. acknowledge()— Mark an alert as acknowledged

DESIGN:
  scan() reads SentimentResult rows → passes to detector (pure compute) →
  writes Alert rows only if the alert doesn't already exist for this
  (product, aspect, alert_type, severity) combination in the last 24h.
  This prevents alert spam on repeated scans.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlmodel import Session, select

from backend.app.ml.anomaly.detector import AnomalyResult, SentimentRow, detect_anomalies
from backend.app.models.alert import Alert
from backend.app.models.sentiment_result import SentimentResult
from backend.app.models.user import User


class AlertService:

    @staticmethod
    def scan(
        product_id: uuid.UUID,
        user: User,
        session: Session,
        reference_dt: Optional[datetime] = None,
    ) -> list[Alert]:
        """
        Run anomaly detection on stored SentimentResult rows for a product.
        Writes new Alert rows for detected anomalies (dedup: skip if already
        written in the last 24 hours for the same aspect + alert_type).

        Args:
            product_id:   Product to scan.
            user:         Authenticated user (scopes retrieval).
            session:      DB session.
            reference_dt: Override "now" — used in tests to inject fixed timestamps.

        Returns:
            List of newly created Alert rows.
        """
        # Fetch ALL SentimentResult rows for this product (detector handles windowing)
        all_rows = session.exec(
            select(SentimentResult).where(
                SentimentResult.product_id == product_id,
                SentimentResult.user_id == user.id,
            ).order_by(SentimentResult.computed_at)
        ).all()

        # Convert ORM rows to lightweight detector input
        sentiment_rows = [
            SentimentRow(
                aspect=r.aspect,
                polarity=r.polarity,
                confidence=r.confidence,
                computed_at=r.computed_at,
            )
            for r in all_rows
        ]

        anomalies: list[AnomalyResult] = detect_anomalies(
            sentiment_rows,
            reference_dt=reference_dt,
        )

        if not anomalies:
            return []

        # Dedup window: skip if same alert already written in last 24h
        cutoff_24h = (reference_dt or datetime.now(tz=timezone.utc)) - timedelta(hours=24)
        existing = session.exec(
            select(Alert).where(
                Alert.product_id == product_id,
                Alert.user_id == user.id,
                Alert.triggered_at >= cutoff_24h,
            )
        ).all()
        existing_keys = {(a.aspect, a.alert_type) for a in existing}

        new_alerts: list[Alert] = []
        for anomaly in anomalies:
            key = (anomaly.aspect, anomaly.alert_type)
            if key in existing_keys:
                continue  # already alerted recently — skip

            alert = Alert(
                user_id=user.id,
                product_id=product_id,
                alert_type=anomaly.alert_type,
                severity=anomaly.severity,
                aspect=anomaly.aspect,
                message=anomaly.message,
                triggered_at=reference_dt or datetime.now(tz=timezone.utc),
            )
            session.add(alert)
            new_alerts.append(alert)

        session.commit()
        for a in new_alerts:
            session.refresh(a)

        return new_alerts

    @staticmethod
    def list_alerts(
        product_id: uuid.UUID,
        user: User,
        session: Session,
        severity: Optional[str] = None,
        unacknowledged_only: bool = False,
        limit: int = 50,
    ) -> list[Alert]:
        """List alerts for a product, optionally filtered by severity or ack status."""
        query = select(Alert).where(
            Alert.product_id == product_id,
            Alert.user_id == user.id,
        ).order_by(Alert.triggered_at.desc()).limit(limit)

        if severity:
            query = query.where(Alert.severity == severity)
        if unacknowledged_only:
            query = query.where(Alert.is_acknowledged == False)  # noqa: E712

        return session.exec(query).all()

    @staticmethod
    def acknowledge(
        alert_id: uuid.UUID,
        product_id: uuid.UUID,
        user: User,
        session: Session,
    ) -> Alert:
        """
        Mark an alert as acknowledged.
        Raises ValueError if alert not found or not owned by user.
        """
        alert = session.exec(
            select(Alert).where(
                Alert.id == alert_id,
                Alert.product_id == product_id,
                Alert.user_id == user.id,
            )
        ).first()
        if not alert:
            raise ValueError(f"Alert {alert_id} not found.")

        alert.is_acknowledged = True
        session.add(alert)
        session.commit()
        session.refresh(alert)
        return alert
