"""
ml/anomaly/detector.py
-----------------------
Anomaly detection over pre-computed SentimentResult rows.

Algorithm (v1 — rolling window comparison):
  1. For each aspect, compute sentiment_score over a RECENT window (last N days)
  2. Compare to sentiment_score over a BASELINE window (prior M days)
  3. If the drop exceeds a threshold → flag an Alert

Severity:
  - HIGH   : score drop > 0.30 (strong negative swing)
  - MEDIUM : score drop > 0.15 (moderate negative swing)
  - LOW    : score drop > 0.05 (minor — logged but not alerted by default)

Alert types:
  - sentiment_spike  : aspect sentiment dropped significantly
  - volume_anomaly   : review volume spiked 3x+ above baseline (could be viral complaint)

DESIGN RULE:
  This module is PURE COMPUTATION — it reads SentimentResult rows and returns
  a list of anomalies. It does NOT write to the DB. Writing is the
  AlertService's job. Separation makes this unit-testable without a DB.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

RECENT_DAYS    = 7     # rolling window for "current" period
BASELINE_DAYS  = 30    # look-back window for "normal" baseline
VOLUME_SPIKE_X = 3.0   # volume considered anomalous if recent/baseline > this ratio

SEVERITY_THRESHOLDS = {
    "high":   0.30,
    "medium": 0.15,
    "low":    0.05,
}


@dataclass
class SentimentRow:
    """Lightweight data class mirroring SentimentResult fields needed for detection."""
    aspect: str
    polarity: str       # "positive" | "negative" | "neutral"
    confidence: float
    computed_at: datetime


@dataclass
class AnomalyResult:
    """Detected anomaly — returned by the detector, persisted by AlertService."""
    alert_type: str           # "sentiment_spike" | "volume_anomaly"
    aspect: str
    severity: str             # "high" | "medium" | "low"
    message: str
    recent_score: float       # sentiment score in the recent window
    baseline_score: float     # sentiment score in the baseline window
    score_delta: float        # recent_score - baseline_score (negative = dropped)
    recent_count: int         # review mentions in recent window
    baseline_count: int       # review mentions in baseline window


def _sentiment_score(rows: list[SentimentRow]) -> float:
    """
    Compute sentiment score from a list of rows.
    score = (positive - negative) / total ∈ [-1.0, 1.0]
    Returns 0.0 for empty lists.
    """
    if not rows:
        return 0.0
    pos = sum(1 for r in rows if r.polarity == "positive")
    neg = sum(1 for r in rows if r.polarity == "negative")
    return (pos - neg) / len(rows)


def detect_anomalies(
    rows: list[SentimentRow],
    reference_dt: Optional[datetime] = None,
    min_baseline_mentions: int = 3,
) -> list[AnomalyResult]:
    """
    Run anomaly detection over a list of SentimentRow objects.

    Args:
        rows:                    All relevant SentimentResult rows for a product+user.
        reference_dt:            The "now" reference time (default: actual UTC now).
                                 Injected in tests to use fixture timestamps.
        min_baseline_mentions:   Minimum rows needed in baseline to fire an alert.
                                 Prevents false positives on products with few reviews.

    Returns:
        List of AnomalyResult objects (may be empty).
    """
    if not rows:
        return []

    now = reference_dt or datetime.now(tz=timezone.utc)

    # Ensure all rows have timezone info for comparison
    def _ensure_tz(dt: datetime) -> datetime:
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    recent_cutoff   = now - timedelta(days=RECENT_DAYS)
    baseline_cutoff = now - timedelta(days=RECENT_DAYS + BASELINE_DAYS)

    # Split rows into recent vs baseline windows
    recent_rows   = [r for r in rows if _ensure_tz(r.computed_at) >= recent_cutoff]
    baseline_rows = [
        r for r in rows
        if baseline_cutoff <= _ensure_tz(r.computed_at) < recent_cutoff
    ]

    anomalies: list[AnomalyResult] = []

    # -----------------------------------------------------------------------
    # 1. Per-aspect sentiment spike detection
    # -----------------------------------------------------------------------
    aspects = {r.aspect for r in rows}

    for aspect in aspects:
        r_rows = [r for r in recent_rows   if r.aspect == aspect]
        b_rows = [r for r in baseline_rows if r.aspect == aspect]

        if len(b_rows) < min_baseline_mentions:
            continue  # not enough baseline data to compare

        recent_score   = _sentiment_score(r_rows)
        baseline_score = _sentiment_score(b_rows)
        delta = recent_score - baseline_score  # negative = drop

        # Only flag drops (negative delta)
        if delta >= -SEVERITY_THRESHOLDS["low"]:
            continue

        # Determine severity
        severity = "low"
        if delta <= -SEVERITY_THRESHOLDS["high"]:
            severity = "high"
        elif delta <= -SEVERITY_THRESHOLDS["medium"]:
            severity = "medium"

        message = (
            f"{aspect} sentiment dropped by {abs(delta):.2f} points "
            f"(baseline: {baseline_score:+.2f} → recent: {recent_score:+.2f}). "
            f"Based on {len(r_rows)} recent vs {len(b_rows)} baseline mentions."
        )

        anomalies.append(AnomalyResult(
            alert_type="sentiment_spike",
            aspect=aspect,
            severity=severity,
            message=message,
            recent_score=round(recent_score, 3),
            baseline_score=round(baseline_score, 3),
            score_delta=round(delta, 3),
            recent_count=len(r_rows),
            baseline_count=len(b_rows),
        ))

    # -----------------------------------------------------------------------
    # 2. Overall volume anomaly detection
    # -----------------------------------------------------------------------
    daily_recent   = len(recent_rows)   / RECENT_DAYS
    daily_baseline = len(baseline_rows) / BASELINE_DAYS

    if daily_baseline > 0 and daily_recent > 0:
        volume_ratio = daily_recent / daily_baseline
        if volume_ratio >= VOLUME_SPIKE_X:
            severity = "high" if volume_ratio >= VOLUME_SPIKE_X * 2 else "medium"
            anomalies.append(AnomalyResult(
                alert_type="volume_anomaly",
                aspect="General",
                severity=severity,
                message=(
                    f"Review volume spiked {volume_ratio:.1f}x above baseline "
                    f"({daily_recent:.1f}/day recent vs {daily_baseline:.1f}/day baseline). "
                    f"Potential viral complaint or promotion surge."
                ),
                recent_score=_sentiment_score(recent_rows),
                baseline_score=_sentiment_score(baseline_rows),
                score_delta=round(_sentiment_score(recent_rows) - _sentiment_score(baseline_rows), 3),
                recent_count=len(recent_rows),
                baseline_count=len(baseline_rows),
            ))

    # Sort by severity — high first
    severity_order = {"high": 0, "medium": 1, "low": 2}
    return sorted(anomalies, key=lambda a: severity_order.get(a.severity, 3))
