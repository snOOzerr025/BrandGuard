"""
services/alert_service.py — Statistical Anomaly Detection & Attribution Service
-------------------------------------------------------------------------------
Orchestrates:
1. STL + EWMA control chart anomaly detection across aspect time-series.
2. Root-cause attribution linking the top negative HDBSCAN micro-theme.
3. Attaching medoid review UUIDs as immutable verifiable proof.
4. Enforcing deterministic SHA-256 24-hour deduplication fingerprint.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlmodel import Session, select

from backend.app.ml.anomaly.stl_ewma_engine import (
    AnomalyAlertCandidate,
    STLEWMAAnomalyEngine,
    compute_alert_dedup_fingerprint,
)
from backend.app.models.domain import Alert, MicroCluster, Review, SentimentResult, SeverityTier, User


class AlertService:

    @staticmethod
    def scan(
        product_id: uuid.UUID,
        user: User,
        session: Session,
        reference_dt: Optional[datetime] = None,
    ) -> List[Alert]:
        """
        Runs STL + EWMA statistical anomaly detection on stored SentimentResult rows.
        Links root-cause MicroCluster, attaches medoid review UUIDs, and deduplicates
        via SHA-256 fingerprint within a 24-hour window.
        """
        ref_now = reference_dt or datetime.now(timezone.utc)
        if ref_now.tzinfo is None:
            ref_now = ref_now.replace(tzinfo=timezone.utc)

        # 1. Fetch ALL SentimentResult rows for this product
        all_sentiment_rows = session.exec(
            select(SentimentResult).where(
                SentimentResult.product_id == product_id,
                SentimentResult.user_id == user.id,
            ).order_by(SentimentResult.created_at)
        ).all()

        if not all_sentiment_rows:
            return []

        # 2. Fetch all reviews for product to compute Thematic Star Impact
        all_reviews = session.exec(
            select(Review).where(
                Review.product_id == product_id,
                Review.user_id == user.id,
            )
        ).all()

        total_review_count = len(all_reviews)
        sum_total_ratings = sum(r.rating for r in all_reviews)
        mean_all_stars = sum_total_ratings / total_review_count if total_review_count > 0 else 0.0

        # Review lookup by id
        review_map = {r.id: r for r in all_reviews}

        # 3. Pull MicroClusters for root-cause attribution
        micro_clusters = session.exec(
            select(MicroCluster).where(
                MicroCluster.product_id == product_id,
                MicroCluster.user_id == user.id,
            )
        ).all()

        clusters_by_aspect: Dict[str, List[MicroCluster]] = {}
        for mc in micro_clusters:
            clusters_by_aspect.setdefault(mc.macro_aspect, []).append(mc)

        # 4. Compute Star Impact and medoids per aspect
        star_impact_by_aspect: Dict[str, float] = {}
        medoids_by_aspect: Dict[str, List[str]] = {}
        top_cluster_by_aspect: Dict[str, Optional[uuid.UUID]] = {}

        # Group review IDs mentioning each aspect
        aspect_to_rev_ids: Dict[str, set[uuid.UUID]] = {}
        for s in all_sentiment_rows:
            aspect_to_rev_ids.setdefault(s.aspect_category, set()).add(s.review_id)

        for aspect, rev_ids in aspect_to_rev_ids.items():
            # Leave-One-Out: mean of all reviews minus mean of reviews excluding this aspect
            excl_ratings = [r.rating for r in all_reviews if r.id not in rev_ids]
            if excl_ratings:
                mean_excl = sum(excl_ratings) / len(excl_ratings)
                impact = mean_all_stars - mean_excl
            else:
                aspect_mcs = clusters_by_aspect.get(aspect, [])
                if aspect_mcs:
                    impact = min(c.star_impact_delta for c in aspect_mcs)
                else:
                    impact = 0.0
            star_impact_by_aspect[aspect] = impact

            # Find worst micro-cluster in this aspect
            aspect_mcs = clusters_by_aspect.get(aspect, [])
            if aspect_mcs:
                worst_mc = min(aspect_mcs, key=lambda c: c.star_impact_delta)
                top_cluster_by_aspect[aspect] = worst_mc.id
                medoids_by_aspect[aspect] = worst_mc.evidence_review_ids or []
            else:
                top_cluster_by_aspect[aspect] = None
                # Pick negative reviews as medoid evidence
                neg_rev_ids = [
                    str(s.review_id) for s in all_sentiment_rows
                    if s.aspect_category == aspect and s.numeric_score < 0
                ]
                medoids_by_aspect[aspect] = neg_rev_ids[:5]

        # 5. Convert rows for the STL + EWMA engine
        formatted_records = [
            {
                "aspect": s.aspect_category,
                "numeric_score": s.numeric_score,
                "created_at": s.created_at,
                "review_id": str(s.review_id),
                "rating": review_map[s.review_id].rating if s.review_id in review_map else 3,
            }
            for s in all_sentiment_rows
        ]

        engine = STLEWMAAnomalyEngine()
        candidates: List[AnomalyAlertCandidate] = engine.detect_aspect_anomalies(
            aspect_records=formatted_records,
            reference_dt=ref_now,
            star_impact_by_aspect=star_impact_by_aspect,
            medoids_by_aspect=medoids_by_aspect,
        )

        if not candidates:
            return []

        # 6. Deduplication and persistence
        new_alerts: List[Alert] = []
        date_str = ref_now.strftime("%Y-%m-%d")

        for cand in candidates:
            fingerprint = compute_alert_dedup_fingerprint(
                user_id=user.id,
                product_id=product_id,
                aspect=cand.aspect,
                target_date=date_str,
            )

            # Check if alert already exists for this fingerprint
            existing = session.exec(
                select(Alert).where(
                    Alert.product_id == product_id,
                    Alert.user_id == user.id,
                    Alert.dedup_fingerprint == fingerprint,
                )
            ).first()

            # Deduplicate unless escalated to CRITICAL
            if existing and existing.severity == SeverityTier.CRITICAL:
                continue
            elif existing and cand.severity != SeverityTier.CRITICAL:
                continue

            alert = Alert(
                user_id=user.id,
                product_id=product_id,
                aspect_category=cand.aspect,
                micro_cluster_id=top_cluster_by_aspect.get(cand.aspect),
                severity=cand.severity,
                alert_type=cand.alert_type,
                z_score=cand.z_score,
                baseline_mean=cand.baseline_mean,
                current_value=cand.current_value,
                star_impact=cand.star_impact,
                support_count=cand.support_count,
                message=cand.message,
                evidence_review_ids=cand.evidence_review_ids,
                dedup_fingerprint=fingerprint,
                created_at=ref_now,
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
    ) -> List[Alert]:
        """List alerts for a product, optionally filtered by severity or ack status."""
        query = select(Alert).where(
            Alert.product_id == product_id,
            Alert.user_id == user.id,
        )

        if severity:
            sev_upper = severity.upper()
            query = query.where(Alert.severity == sev_upper)

        if unacknowledged_only:
            query = query.where(Alert.is_acknowledged == False)  # noqa: E712

        return session.exec(query.order_by(Alert.created_at.desc()).limit(limit)).all()

    @staticmethod
    def acknowledge_alert(
        alert_id: uuid.UUID,
        user: User,
        session: Session,
    ) -> Alert:
        """Mark an alert as acknowledged by user."""
        alert = session.exec(
            select(Alert).where(Alert.id == alert_id, Alert.user_id == user.id)
        ).first()
        if not alert:
            raise ValueError(f"Alert {alert_id} not found.")

        alert.is_acknowledged = True
        session.add(alert)
        session.commit()
        session.refresh(alert)
        return alert

    @staticmethod
    def acknowledge(
        alert_id: uuid.UUID,
        product_id: uuid.UUID,
        user: User,
        session: Session,
    ) -> Alert:
        """Alias for router matching."""
        return AlertService.acknowledge_alert(alert_id, user, session)
