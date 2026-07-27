"""
services/insight_service.py
----------------------------
Business logic for sentiment insights, history retrieval, and cluster summaries.

Design rule: every insight is QUERIED from stored SentimentResult rows.
We never recompute on the fly for history endpoints — the data is already
in the DB from the pipeline run. This is what makes trend charts honest.
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from backend.app.models.product import Product
from backend.app.models.sentiment_result import SentimentResult
from backend.app.models.review import Review
from backend.app.models.user import User


class InsightService:

    @staticmethod
    def get_aspect_summary(
        product_id: uuid.UUID,
        user: User,
        session: Session,
        from_dt: Optional[datetime] = None,
        to_dt: Optional[datetime] = None,
    ) -> list[dict]:
        """
        Aggregate SentimentResult rows for a product into per-aspect summaries.
        Optionally filtered by time window.
        """
        query = select(SentimentResult).where(
            SentimentResult.product_id == product_id,
            SentimentResult.user_id == user.id,
        )
        if from_dt:
            query = query.where(SentimentResult.computed_at >= from_dt)
        if to_dt:
            query = query.where(SentimentResult.computed_at <= to_dt)

        rows = session.exec(query).all()
        if not rows:
            return []

        # Aggregate per aspect
        aspect_data: dict[str, dict] = defaultdict(
            lambda: {"mention_count": 0, "positive": 0, "negative": 0, "neutral": 0, "total_confidence": 0.0}
        )
        for row in rows:
            d = aspect_data[row.aspect]
            d["mention_count"] += 1
            d[row.polarity] += 1
            d["total_confidence"] += row.confidence

        result = []
        for aspect, d in sorted(aspect_data.items(), key=lambda x: -x[1]["mention_count"]):
            total = d["mention_count"]
            result.append({
                "aspect": aspect,
                "mention_count": total,
                "positive_count": d["positive"],
                "negative_count": d["negative"],
                "neutral_count": d["neutral"],
                "positive_ratio": round(d["positive"] / total * 100, 1) if total else 0.0,
                "avg_confidence": round(d["total_confidence"] / total, 3) if total else 0.0,
                "sentiment_score": round(
                    (d["positive"] - d["negative"]) / total, 3
                ) if total else 0.0,
            })
        return result

    @staticmethod
    def get_history(
        product_id: uuid.UUID,
        user: User,
        session: Session,
        from_dt: Optional[datetime] = None,
        to_dt: Optional[datetime] = None,
        limit: int = 200,
    ) -> list[dict]:
        """
        Return raw historical SentimentResult rows for a product,
        ordered by computed_at ascending (for trend charts).

        This returns REAL historical rows — not a recomputed snapshot.
        """
        query = (
            select(SentimentResult)
            .where(
                SentimentResult.product_id == product_id,
                SentimentResult.user_id == user.id,
            )
            .order_by(SentimentResult.computed_at)
            .limit(limit)
        )
        if from_dt:
            query = query.where(SentimentResult.computed_at >= from_dt)
        if to_dt:
            query = query.where(SentimentResult.computed_at <= to_dt)

        rows = session.exec(query).all()
        return [
            {
                "id": str(row.id),
                "review_id": str(row.review_id),
                "aspect": row.aspect,
                "polarity": row.polarity,
                "confidence": row.confidence,
                "cluster_id": row.cluster_id,
                "cluster_label": row.cluster_label,
                "model_version": row.model_version,
                "computed_at": row.computed_at.isoformat(),
            }
            for row in rows
        ]

    @staticmethod
    def get_overall_sentiment(
        product_id: uuid.UUID,
        user: User,
        session: Session,
        from_dt: Optional[datetime] = None,
        to_dt: Optional[datetime] = None,
    ) -> dict:
        """
        Returns overall product sentiment as a single summary dict.
        """
        rows_query = select(SentimentResult).where(
            SentimentResult.product_id == product_id,
            SentimentResult.user_id == user.id,
        )
        if from_dt:
            rows_query = rows_query.where(SentimentResult.computed_at >= from_dt)
        if to_dt:
            rows_query = rows_query.where(SentimentResult.computed_at <= to_dt)

        rows = session.exec(rows_query).all()
        if not rows:
            return {"total": 0, "positive": 0, "negative": 0, "neutral": 0, "sentiment_score": 0.0}

        total = len(rows)
        pos = sum(1 for r in rows if r.polarity == "positive")
        neg = sum(1 for r in rows if r.polarity == "negative")
        neu = sum(1 for r in rows if r.polarity == "neutral")

        return {
            "total": total,
            "positive": pos,
            "negative": neg,
            "neutral": neu,
            "positive_ratio": round(pos / total * 100, 1),
            "negative_ratio": round(neg / total * 100, 1),
            "sentiment_score": round((pos - neg) / total, 3),
        }

    @staticmethod
    def get_clusters(
        product_id: uuid.UUID,
        user: User,
        session: Session,
    ) -> list[dict]:
        """Return distinct cluster labels for a product's reviews."""
        rows = session.exec(
            select(SentimentResult).where(
                SentimentResult.product_id == product_id,
                SentimentResult.user_id == user.id,
                SentimentResult.cluster_id != None,  # noqa: E711
            )
        ).all()

        clusters: dict[int, dict] = {}
        for row in rows:
            cid = row.cluster_id
            if cid not in clusters:
                clusters[cid] = {
                    "cluster_id": cid,
                    "cluster_label": row.cluster_label or f"Cluster {cid}",
                    "review_count": 0,
                    "positive": 0,
                    "negative": 0,
                    "neutral": 0,
                }
            clusters[cid]["review_count"] += 1
            clusters[cid][row.polarity] += 1

        return sorted(clusters.values(), key=lambda x: -x["review_count"])
