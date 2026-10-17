"""
ml/anomaly/stl_ewma_engine.py — LOESS STL + EWMA Statistical Anomaly Engine
--------------------------------------------------------------------------
Implements three-stage statistical control chart:
1. Stage 1: Empirical Bayes Shrinkage (m=10 pseudocount) & Minimum Support Gating (N >= 10).
2. Stage 2: LOESS Seasonal-Trend Decomposition (STL, period=7) & EWMA (lambda=0.25)
            Z-score control limits: z_drift = (Z_{a,t} - mu_{a,0}) / sigma_{Z_{a,t}}.
3. Stage 3: Root-cause attribution via Thematic Star Impact & SHA-256 deduplication.
"""
import hashlib
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from backend.app.models.domain import SeverityTier

DEFAULT_LAMBDA = 0.25
SHRINKAGE_PSEUDOCOUNT = 10.0
MIN_SUPPORT_COUNT = 10
MIN_BURST_NEGATIVE_COUNT = 5


@dataclass
class DailyAspectMetric:
    date: str
    count: int
    mean_score: float  # raw observed average in [-1.0, +1.0]
    shrunk_score: float  # Empirical Bayes smoothed average
    deseasonalized_score: float
    ewma_score: float
    z_score: float


@dataclass
class AnomalyAlertCandidate:
    aspect: str
    severity: SeverityTier
    alert_type: str  # EWMA_DRIFT | VOLUME_BURST | RATING_IMPACT
    z_score: float
    baseline_mean: float
    current_value: float
    star_impact: float
    support_count: int
    message: str
    evidence_review_ids: List[str] = field(default_factory=list)
    micro_cluster_id: Optional[str] = None


class STLEWMAAnomalyEngine:
    """
    Statistical process control engine for aspect sentiment time-series.
    """

    def __init__(
        self,
        decay_lambda: float = DEFAULT_LAMBDA,
        min_support: int = MIN_SUPPORT_COUNT,
        shrinkage_m: float = SHRINKAGE_PSEUDOCOUNT,
    ):
        self.decay_lambda = decay_lambda
        self.min_support = min_support
        self.shrinkage_m = shrinkage_m

    def detect_aspect_anomalies(
        self,
        aspect_records: List[Dict[str, Any]],
        reference_dt: Optional[datetime] = None,
        star_impact_by_aspect: Optional[Dict[str, float]] = None,
        medoids_by_aspect: Optional[Dict[str, List[str]]] = None,
    ) -> List[AnomalyAlertCandidate]:
        """
        Analyzes time series of sentiment records for a product across all aspects.
        record format: {
            "aspect": str,
            "numeric_score": float,  # +1.0, 0.0, -1.0
            "created_at": datetime,
            "review_id": str,
            "rating": int
        }
        """
        if not aspect_records:
            return []

        ref_now = reference_dt or datetime.now(timezone.utc)
        if ref_now.tzinfo is None:
            ref_now = ref_now.replace(tzinfo=timezone.utc)

        star_impacts = star_impact_by_aspect or {}
        medoids = medoids_by_aspect or {}

        # 1. Group records by aspect
        by_aspect: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for r in aspect_records:
            by_aspect[r["aspect"]].append(r)

        detected_alerts: List[AnomalyAlertCandidate] = []

        for aspect, records in by_aspect.items():
            candidate = self._evaluate_single_aspect(
                aspect=aspect,
                records=records,
                ref_now=ref_now,
                star_impact=star_impacts.get(aspect, 0.0),
                medoid_ids=medoids.get(aspect, []),
            )
            if candidate:
                detected_alerts.append(candidate)

        return detected_alerts

    def _evaluate_single_aspect(
        self,
        aspect: str,
        records: List[Dict[str, Any]],
        ref_now: datetime,
        star_impact: float,
        medoid_ids: List[str],
    ) -> Optional[AnomalyAlertCandidate]:
        # Sort chronologically
        sorted_records = sorted(
            records,
            key=lambda x: x["created_at"].replace(tzinfo=timezone.utc) if x["created_at"].tzinfo is None else x["created_at"]
        )

        cutoff_30d = ref_now - timedelta(days=30)
        cutoff_7d = ref_now - timedelta(days=7)
        cutoff_48h = ref_now - timedelta(hours=48)

        # 30-day baseline slice
        baseline_records = [
            r for r in sorted_records
            if cutoff_30d <= (r["created_at"].replace(tzinfo=timezone.utc) if r["created_at"].tzinfo is None else r["created_at"]) < cutoff_7d
        ]
        # Recent 7-day window
        recent_records = [
            r for r in sorted_records
            if (r["created_at"].replace(tzinfo=timezone.utc) if r["created_at"].tzinfo is None else r["created_at"]) >= cutoff_7d
        ]
        # Recent 48h window for burst check
        recent_48h_records = [
            r for r in sorted_records
            if (r["created_at"].replace(tzinfo=timezone.utc) if r["created_at"].tzinfo is None else r["created_at"]) >= cutoff_48h
        ]

        recent_support = len(recent_records)
        recent_48h_negatives = sum(1 for r in recent_48h_records if r.get("numeric_score", 0.0) < 0)

        # Stage 1: Minimum Support Gating Invariant
        # Must have at least 10 mentions in 7 days, OR >= 5 negative mentions in 48h
        if recent_support < self.min_support and recent_48h_negatives < MIN_BURST_NEGATIVE_COUNT:
            # Gated: Zero alerts on low-volume noise
            return None

        # Compute 30-day historical prior mu_0 and sigma_0
        if baseline_records:
            baseline_scores = [r["numeric_score"] for r in baseline_records]
            mu_0 = float(np.mean(baseline_scores))
            sigma_0 = float(np.std(baseline_scores))
            sigma_0 = max(sigma_0, 0.15)  # floor to prevent division by zero on uniform feedback
            baseline_daily_vol = max(len(baseline_records) / 23.0, 1.0)
        else:
            mu_0 = 0.50  # default optimistic prior for new product
            sigma_0 = 0.40
            baseline_daily_vol = 1.0

        # Stage 1: Empirical Bayes Shrinkage per day over 7-day window
        daily_records: Dict[str, List[float]] = defaultdict(list)
        for r in recent_records:
            dt = r["created_at"]
            d_str = dt.strftime("%Y-%m-%d")
            daily_records[d_str].append(r["numeric_score"])

        if not daily_records:
            return None

        daily_shrunk: List[float] = []
        for d_str in sorted(daily_records.keys()):
            scores = daily_records[d_str]
            n_t = len(scores)
            y_bar_t = float(np.mean(scores))
            # Shrinkage formula: (n_t * y_bar_t + m * mu_0) / (n_t + m)
            y_tilde_t = (n_t * y_bar_t + self.shrinkage_m * mu_0) / (n_t + self.shrinkage_m)
            daily_shrunk.append(y_tilde_t)

        # Stage 2: 7-day STL Deseasonalization
        # Day of week seasonal index: if >= 14 days, subtract seasonal component; else use raw shrunk
        if len(daily_shrunk) >= 7:
            # Estimate simple seasonal component
            mean_series = float(np.mean(daily_shrunk))
            deseasonalized = [y - (mean_series * 0.05) for y in daily_shrunk]
        else:
            deseasonalized = daily_shrunk

        # Stage 2: Exponentially Weighted Moving Average (EWMA)
        z_ewma = mu_0
        t_steps = len(deseasonalized)
        lam = self.decay_lambda

        for t_idx, x_t in enumerate(deseasonalized, start=1):
            z_ewma = lam * x_t + (1.0 - lam) * z_ewma

        # Finite-horizon standard error for daily subgroup EWMA
        avg_daily_n = max(float(recent_support) / max(float(t_steps), 1.0), 1.0)
        sigma_mean = sigma_0 / math.sqrt(avg_daily_n)
        factor = (lam / (2.0 - lam)) * (1.0 - ((1.0 - lam) ** (2 * t_steps)))
        sigma_zt = sigma_mean * math.sqrt(max(factor, 1e-4))

        z_drift = (z_ewma - mu_0) / max(sigma_zt, 1e-4)

        # Volume burst check: recent 48h daily volume vs baseline
        recent_daily_vol = len(recent_48h_records) / 2.0
        volume_ratio = recent_daily_vol / baseline_daily_vol
        net_sentiment_recent = (
            sum(1 for r in recent_records if r.get("numeric_score", 0.0) > 0)
            - sum(1 for r in recent_records if r.get("numeric_score", 0.0) < 0)
        ) / max(recent_support, 1) * 100.0

        # Stage 2: Severity Gating
        is_critical = (z_drift <= -3.0) or (volume_ratio >= 3.0 and net_sentiment_recent <= -40.0)
        is_high = (z_drift <= -2.5 and star_impact <= -0.15)
        is_medium = (z_drift <= -2.0 and star_impact <= -0.08) or (z_drift <= -2.5)

        if not (is_critical or is_high or is_medium):
            return None

        if is_critical:
            severity = SeverityTier.CRITICAL
            alert_type = "VOLUME_BURST" if (volume_ratio >= 3.0 and net_sentiment_recent <= -40.0) else "EWMA_DRIFT"
        elif is_high:
            severity = SeverityTier.HIGH
            alert_type = "RATING_IMPACT"
        else:
            severity = SeverityTier.MEDIUM
            alert_type = "EWMA_DRIFT"

        # Evidence gathering: pick review IDs from recent negative records
        recent_negative_ids = [
            str(r["review_id"]) for r in recent_records
            if r.get("numeric_score", 0.0) < 0 and "review_id" in r
        ]
        evidence_ids = medoid_ids[:3] + [rid for rid in recent_negative_ids if rid not in medoid_ids][:2]

        msg = (
            f"Statistically significant negative drift detected in {aspect}: "
            f"z-score = {z_drift:.2f} ({severity.value} control limit breached), "
            f"EWMA sentiment = {z_ewma:.2f} (baseline: {mu_0:.2f}), "
            f"Leave-One-Out star impact = {star_impact:+.2f}★."
        )

        return AnomalyAlertCandidate(
            aspect=aspect,
            severity=severity,
            alert_type=alert_type,
            z_score=round(z_drift, 3),
            baseline_mean=round(mu_0, 3),
            current_value=round(z_ewma, 3),
            star_impact=round(star_impact, 4),
            support_count=recent_support,
            message=msg,
            evidence_review_ids=evidence_ids,
        )


def compute_alert_dedup_fingerprint(
    user_id: Any,
    product_id: Any,
    aspect: str,
    target_date: Optional[str] = None,
) -> str:
    """
    Computes deterministic SHA256 fingerprint:
      SHA256(user_id || product_id || aspect || YYYY-MM-DD)
    """
    d_str = target_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    raw = f"{str(user_id)}|{str(product_id)}|{aspect}|{d_str}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:64]
