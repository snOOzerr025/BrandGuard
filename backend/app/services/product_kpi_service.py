"""
services/product_kpi_service.py
--------------------------------
Calculates production KPIs, theme rollups, and anomaly control-chart timelines
following Section 6.3 & Section 7.2 of the BrandGuard Master Specification:
- Brand Health Score (0-100)
- Chattermill Net Sentiment ([-100, +100])
- Thematic Leave-One-Out Star Impact: (a/b) - (c/d)
- 8-dimension Diverging Aspect Matrix
- HDBSCAN Micro-Cluster Themes
- Deseasonalized EWMA Control Chart Timeline (2-sigma, 3-sigma bands)
"""
from __future__ import annotations

import math
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np
from sqlmodel import Session, select

from backend.app.ml.anomaly.stl_ewma_engine import DEFAULT_LAMBDA, SHRINKAGE_PSEUDOCOUNT
from backend.app.models.domain import Alert, MicroCluster, Product, Review, SentimentResult, SeverityTier, User


class ProductKpiService:

    @staticmethod
    def get_product_kpis(
        product_id: uuid.UUID,
        user: User,
        session: Session,
        window_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Calculates executive KPIs and aspect matrix for a product over window_days.
        """
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=window_days)

        # 1. Fetch reviews
        reviews = session.exec(
            select(Review).where(
                Review.product_id == product_id,
                Review.user_id == user.id,
                Review.reviewed_at >= start_date,
            )
        ).all()

        total_reviews = len(reviews)
        if total_reviews == 0:
            # Fallback to all-time reviews if window has none
            reviews = session.exec(
                select(Review).where(
                    Review.product_id == product_id,
                    Review.user_id == user.id,
                )
            ).all()
            total_reviews = len(reviews)

        # Global star rating
        all_ratings = [r.rating for r in reviews if r.rating is not None]
        global_star_rating = float(np.mean(all_ratings)) if all_ratings else 0.0

        # 2. Fetch sentiment results
        sentiment_rows = session.exec(
            select(SentimentResult).where(
                SentimentResult.product_id == product_id,
                SentimentResult.user_id == user.id,
            )
        ).all()

        # Aspect aggregation
        aspect_reviews: Dict[str, set[uuid.UUID]] = defaultdict(set)
        aspect_counts: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"positive": 0, "neutral": 0, "negative": 0}
        )

        for s in sentiment_rows:
            aspect = s.aspect_category
            aspect_reviews[aspect].add(s.review_id)
            pol = str(s.polarity).lower()
            if "positive" in pol:
                aspect_counts[aspect]["positive"] += 1
            elif "negative" in pol:
                aspect_counts[aspect]["negative"] += 1
            else:
                aspect_counts[aspect]["neutral"] += 1

        # Global Net Sentiment
        total_pos = sum(c["positive"] for c in aspect_counts.values())
        total_neg = sum(c["negative"] for c in aspect_counts.values())
        total_mentions = sum(
            c["positive"] + c["neutral"] + c["negative"] for c in aspect_counts.values()
        )
        if total_mentions > 0:
            net_sentiment = round(((total_pos - total_neg) / total_mentions) * 100.0, 1)
        else:
            net_sentiment = 0.0

        # Brand Health Score (0 - 100)
        # 60% Net Sentiment normalized to [0, 100] + 40% Star Rating normalized to [0, 100]
        sentiment_norm = (net_sentiment + 100.0) / 2.0
        rating_norm = (global_star_rating / 5.0) * 100.0 if global_star_rating > 0 else 50.0
        brand_health_score = round(0.6 * sentiment_norm + 0.4 * rating_norm, 1)

        # Build aspect matrix with Leave-One-Out Star Impact
        aspect_matrix = []
        top_drag_aspect: Optional[str] = None
        min_star_impact = 0.0

        canonical_order = [
            "Battery", "Audio Quality", "Connectivity", "Build Quality",
            "Comfort & Fit", "Customer Support", "Software & App", "Packaging",
            "Miscellaneous"
        ]
        # Include canonical aspects even if 0 mentions, plus any emergent ones
        all_aspect_keys = sorted(
            set(canonical_order).union(aspect_counts.keys()),
            key=lambda x: canonical_order.index(x) if x in canonical_order else 99
        )

        for aspect in all_aspect_keys:
            c = aspect_counts.get(aspect, {"positive": 0, "neutral": 0, "negative": 0})
            pos = c["positive"]
            neu = c["neutral"]
            neg = c["negative"]
            mentions = pos + neu + neg

            pos_pct = round((pos / mentions * 100.0), 1) if mentions > 0 else 0.0
            neu_pct = round((neu / mentions * 100.0), 1) if mentions > 0 else 0.0
            neg_pct = round((neg / mentions * 100.0), 1) if mentions > 0 else 0.0
            asp_net = round(((pos - neg) / mentions * 100.0), 1) if mentions > 0 else 0.0

            # Leave-One-Out Star Impact: mean(all) - mean(excl)
            rev_ids = aspect_reviews.get(aspect, set())
            if mentions > 0 and len(reviews) > len(rev_ids) and rev_ids:
                excl_ratings = [r.rating for r in reviews if r.id not in rev_ids and r.rating is not None]
                if excl_ratings:
                    mean_excl = float(np.mean(excl_ratings))
                    star_impact_delta = round(global_star_rating - mean_excl, 3)
                else:
                    star_impact_delta = 0.0
            else:
                star_impact_delta = 0.0

            if star_impact_delta < min_star_impact:
                min_star_impact = star_impact_delta
                top_drag_aspect = aspect

            aspect_matrix.append({
                "aspect": aspect,
                "mention_count": mentions,
                "positive_count": pos,
                "neutral_count": neu,
                "negative_count": neg,
                "positive_pct": pos_pct,
                "neutral_pct": neu_pct,
                "negative_pct": neg_pct,
                "net_sentiment": asp_net,
                "star_impact_delta": star_impact_delta,
            })

        # Count active anomalies (unacknowledged alerts)
        active_anomalies_count = len(
            session.exec(
                select(Alert).where(
                    Alert.product_id == product_id,
                    Alert.user_id == user.id,
                    Alert.is_acknowledged == False,  # noqa: E712
                )
            ).all()
        )

        return {
            "product_id": str(product_id),
            "brand_health_score": brand_health_score,
            "net_sentiment": net_sentiment,
            "star_rating": round(global_star_rating, 2),
            "total_reviews": total_reviews,
            "active_anomalies": active_anomalies_count,
            "top_rating_drag": {
                "aspect": top_drag_aspect or (aspect_matrix[0]["aspect"] if aspect_matrix else "None"),
                "star_impact_delta": min_star_impact,
            },
            "aspect_matrix": aspect_matrix,
        }

    @staticmethod
    def get_product_themes(
        product_id: uuid.UUID,
        user: User,
        session: Session,
        macro_aspect: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieves HDBSCAN micro-clusters for product, optionally filtered by macro_aspect.
        Sorted by most negative star impact delta (rating drag).
        """
        query = select(MicroCluster).where(
            MicroCluster.product_id == product_id,
            MicroCluster.user_id == user.id,
        )
        if macro_aspect:
            query = query.where(MicroCluster.macro_aspect == macro_aspect)

        clusters = session.exec(query).all()

        cluster_items = [
            {
                "id": str(c.id),
                "macro_aspect": c.macro_aspect,
                "hdbscan_label": c.hdbscan_label,
                "theme_label": c.theme_label,
                "top_ctfidf_terms": c.top_ctfidf_terms or [],
                "volume": c.review_volume,
                "net_sentiment": round(c.net_sentiment, 1),
                "star_impact_delta": round(c.star_impact_delta, 3),
                "evidence_review_ids": [str(rid) for rid in (c.evidence_review_ids or [])],
            }
            for c in clusters
        ]

        # Sort by star_impact_delta ASC (most drag first)
        cluster_items.sort(key=lambda x: x["star_impact_delta"])

        return {
            "product_id": str(product_id),
            "macro_aspect": macro_aspect,
            "total_clusters": len(cluster_items),
            "clusters": cluster_items,
        }

    @staticmethod
    def get_product_anomalies(
        product_id: uuid.UUID,
        user: User,
        session: Session,
        window_days: int = 90,
        severity: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Returns daily deseasonalized EWMA timeline series with 2-sigma and 3-sigma
        control bands, plus active/historical anomaly alerts.
        """
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=window_days)

        # 1. Fetch alerts
        alert_query = select(Alert).where(
            Alert.product_id == product_id,
            Alert.user_id == user.id,
            Alert.created_at >= start_date,
        )
        if severity:
            sev_enum = SeverityTier(severity.upper())
            alert_query = alert_query.where(Alert.severity == sev_enum)

        alerts = session.exec(alert_query.order_by(Alert.created_at.desc())).all()

        alert_items = [
            {
                "id": str(a.id),
                "aspect_category": a.aspect_category,
                "severity": a.severity.value if hasattr(a.severity, "value") else str(a.severity),
                "alert_type": a.alert_type,
                "z_score": round(a.z_score, 2),
                "baseline_mean": round(a.baseline_mean, 2),
                "current_value": round(a.current_value, 2),
                "star_impact": round(a.star_impact, 3),
                "support_count": a.support_count,
                "message": a.message,
                "evidence_review_ids": [str(rid) for rid in (a.evidence_review_ids or [])],
                "is_acknowledged": a.is_acknowledged,
                "created_at": a.created_at.isoformat(),
            }
            for a in alerts
        ]

        # 2. Build Daily EWMA Control Chart Timeline
        sentiments = session.exec(
            select(SentimentResult).where(
                SentimentResult.product_id == product_id,
                SentimentResult.user_id == user.id,
                SentimentResult.created_at >= start_date,
            ).order_by(SentimentResult.created_at.asc())
        ).all()

        timeline_series: List[Dict[str, Any]] = []

        if sentiments:
            daily_scores: Dict[str, List[float]] = defaultdict(list)
            for s in sentiments:
                d_str = s.created_at.strftime("%Y-%m-%d")
                daily_scores[d_str].append(s.numeric_score)

            all_scores = [s.numeric_score for s in sentiments]
            mu_0 = float(np.mean(all_scores))
            sigma_0 = max(float(np.std(all_scores)), 0.20)

            # Sort days
            sorted_days = sorted(daily_scores.keys())
            lam = DEFAULT_LAMBDA
            z_ewma = mu_0

            # Alert date set for anomaly pinning
            alert_dates = {a.created_at.strftime("%Y-%m-%d") for a in alerts}

            for t_idx, d_str in enumerate(sorted_days, start=1):
                day_vals = daily_scores[d_str]
                daily_mean = float(np.mean(day_vals))
                n_t = len(day_vals)

                # Empirical Bayes shrinkage towards baseline
                y_shrunk = (n_t * daily_mean + SHRINKAGE_PSEUDOCOUNT * mu_0) / (n_t + SHRINKAGE_PSEUDOCOUNT)
                z_ewma = lam * y_shrunk + (1.0 - lam) * z_ewma

                # Finite-horizon standard error
                factor = (lam / (2.0 - lam)) * (1.0 - ((1.0 - lam) ** (2 * t_idx)))
                sigma_zt = (sigma_0 / math.sqrt(max(n_t, 1))) * math.sqrt(max(factor, 1e-4))

                upper_2 = round(mu_0 + 2.0 * sigma_zt, 3)
                lower_2 = round(mu_0 - 2.0 * sigma_zt, 3)
                upper_3 = round(mu_0 + 3.0 * sigma_zt, 3)
                lower_3 = round(mu_0 - 3.0 * sigma_zt, 3)
                z_score = round((z_ewma - mu_0) / max(sigma_zt, 1e-4), 2)
                is_anomaly = (d_str in alert_dates) or (z_score <= -2.5)

                timeline_series.append({
                    "date": d_str,
                    "daily_mean_sentiment": round(daily_mean, 3),
                    "ewma_sentiment": round(z_ewma, 3),
                    "upper_limit_2sigma": upper_2,
                    "lower_limit_2sigma": lower_2,
                    "upper_limit_3sigma": upper_3,
                    "lower_limit_3sigma": lower_3,
                    "z_score": z_score,
                    "review_count": n_t,
                    "is_anomaly": is_anomaly,
                })

        return {
            "product_id": str(product_id),
            "window_days": window_days,
            "timeline_series": timeline_series,
            "alerts": alert_items,
        }
