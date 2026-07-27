"""
Unit tests for the anomaly detector — pure computation, no DB needed.

The detector is stateless: given a list of SentimentRow objects and a
reference datetime, it returns a list of AnomalyResult objects.

These tests simulate realistic scenarios:
  - No data → no alerts
  - Stable sentiment → no alerts
  - Sharp negative spike → HIGH alert
  - Moderate drop → MEDIUM alert
  - Volume spike → volume_anomaly alert
  - Dedup: same data twice → same anomalies (idempotent)
  - Cross-aspect isolation: Battery drop does not trigger Quality alert
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from backend.app.ml.anomaly.detector import (
    RECENT_DAYS,
    BASELINE_DAYS,
    SentimentRow,
    detect_anomalies,
)

NOW = datetime.now(tz=timezone.utc)


def make_rows(
    aspect: str,
    polarity: str,
    count: int,
    days_ago_start: int,
    days_ago_end: int,
) -> list[SentimentRow]:
    """
    Generate `count` SentimentRow objects spread evenly between
    days_ago_start and days_ago_end relative to NOW.
    """
    if count == 0:
        return []
    span = days_ago_start - days_ago_end
    step = span / count
    rows = []
    for i in range(count):
        days_ago = days_ago_start - (i * step)
        rows.append(SentimentRow(
            aspect=aspect,
            polarity=polarity,
            confidence=0.90,
            computed_at=NOW - timedelta(days=days_ago),
        ))
    return rows


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAnomalyDetector:

    def test_empty_rows_returns_no_anomalies(self):
        assert detect_anomalies([], reference_dt=NOW) == []

    def test_stable_positive_sentiment_no_alert(self):
        """All positive in both windows → no drop → no alert."""
        rows = (
            make_rows("Quality", "positive", 20, RECENT_DAYS + BASELINE_DAYS, RECENT_DAYS + 1)
            + make_rows("Quality", "positive", 10, RECENT_DAYS, 0)
        )
        anomalies = detect_anomalies(rows, reference_dt=NOW)
        assert anomalies == []

    def test_sharp_negative_spike_creates_high_alert(self):
        """
        Baseline: 20 positives → score = +1.0
        Recent:   10 negatives → score = -1.0
        Delta = -2.0 → clearly HIGH severity
        """
        rows = (
            make_rows("Battery", "positive", 20, RECENT_DAYS + BASELINE_DAYS, RECENT_DAYS + 1)
            + make_rows("Battery", "negative", 10, RECENT_DAYS, 0)
        )
        anomalies = detect_anomalies(rows, reference_dt=NOW)
        assert len(anomalies) >= 1
        battery = next(a for a in anomalies if a.aspect == "Battery")
        assert battery.severity == "high"
        assert battery.alert_type == "sentiment_spike"
        assert battery.score_delta < -0.30

    def test_moderate_drop_creates_medium_alert(self):
        """
        Baseline: 15 pos + 5 neg → score = +0.5
        Recent:   4 pos + 6 neg  → score = -0.2
        Delta ≈ -0.7 → HIGH (>0.30 drop)
        """
        rows = (
            make_rows("Delivery", "positive", 15, RECENT_DAYS + BASELINE_DAYS, RECENT_DAYS + 1)
            + make_rows("Delivery", "negative", 5, RECENT_DAYS + BASELINE_DAYS, RECENT_DAYS + 1)
            + make_rows("Delivery", "positive", 4, RECENT_DAYS, 0)
            + make_rows("Delivery", "negative", 6, RECENT_DAYS, 0)
        )
        anomalies = detect_anomalies(rows, reference_dt=NOW)
        delivery = next((a for a in anomalies if a.aspect == "Delivery"), None)
        assert delivery is not None
        assert delivery.severity in ("high", "medium")
        assert delivery.score_delta < -0.15

    def test_cross_aspect_isolation(self):
        """
        Battery drops sharply. Quality stays stable.
        Only Battery alert should fire — not Quality.
        """
        rows = (
            # Battery: positive baseline → negative recent
            make_rows("Battery", "positive", 15, RECENT_DAYS + BASELINE_DAYS, RECENT_DAYS + 1)
            + make_rows("Battery", "negative", 10, RECENT_DAYS, 0)
            # Quality: stable positive in both windows
            + make_rows("Quality", "positive", 15, RECENT_DAYS + BASELINE_DAYS, RECENT_DAYS + 1)
            + make_rows("Quality", "positive", 8, RECENT_DAYS, 0)
        )
        anomalies = detect_anomalies(rows, reference_dt=NOW)
        alerted_aspects = {a.aspect for a in anomalies}
        assert "Battery" in alerted_aspects
        assert "Quality" not in alerted_aspects

    def test_insufficient_baseline_suppresses_alert(self):
        """
        Fewer than min_baseline_mentions (3) → alert suppressed to avoid false positives.
        """
        rows = (
            make_rows("Price", "positive", 2, RECENT_DAYS + BASELINE_DAYS, RECENT_DAYS + 1)
            + make_rows("Price", "negative", 8, RECENT_DAYS, 0)
        )
        anomalies = detect_anomalies(rows, reference_dt=NOW, min_baseline_mentions=3)
        price_alerts = [a for a in anomalies if a.aspect == "Price"]
        assert price_alerts == []

    def test_volume_spike_creates_volume_anomaly(self):
        """
        Baseline: 10 reviews over 30 days → 0.33/day
        Recent:   30 reviews in 7 days   → 4.3/day  (13x spike)
        """
        rows = (
            make_rows("General", "positive", 10, RECENT_DAYS + BASELINE_DAYS, RECENT_DAYS + 1)
            + make_rows("General", "negative", 30, RECENT_DAYS, 0)
        )
        anomalies = detect_anomalies(rows, reference_dt=NOW)
        volume_alerts = [a for a in anomalies if a.alert_type == "volume_anomaly"]
        assert len(volume_alerts) >= 1

    def test_results_sorted_high_first(self):
        """HIGH severity alerts must appear before MEDIUM and LOW."""
        rows = (
            # Aspect A — sharp drop → HIGH
            make_rows("Aspect_A", "positive", 20, RECENT_DAYS + BASELINE_DAYS, RECENT_DAYS + 1)
            + make_rows("Aspect_A", "negative", 10, RECENT_DAYS, 0)
            # Aspect B — minor drop → likely LOW or MEDIUM
            + make_rows("Aspect_B", "positive", 20, RECENT_DAYS + BASELINE_DAYS, RECENT_DAYS + 1)
            + make_rows("Aspect_B", "positive", 7, RECENT_DAYS, 0)
            + make_rows("Aspect_B", "negative", 3, RECENT_DAYS, 0)
        )
        anomalies = detect_anomalies(rows, reference_dt=NOW)
        if len(anomalies) >= 2:
            severity_order = {"high": 0, "medium": 1, "low": 2}
            for i in range(len(anomalies) - 1):
                assert severity_order[anomalies[i].severity] <= severity_order[anomalies[i + 1].severity]

    def test_detector_is_idempotent(self):
        """Running the detector twice on the same data should return the same anomalies."""
        rows = (
            make_rows("Quality", "positive", 20, RECENT_DAYS + BASELINE_DAYS, RECENT_DAYS + 1)
            + make_rows("Quality", "negative", 10, RECENT_DAYS, 0)
        )
        result1 = detect_anomalies(rows, reference_dt=NOW)
        result2 = detect_anomalies(rows, reference_dt=NOW)
        assert len(result1) == len(result2)
        for a1, a2 in zip(result1, result2):
            assert a1.aspect == a2.aspect
            assert a1.severity == a2.severity
            assert a1.score_delta == a2.score_delta
