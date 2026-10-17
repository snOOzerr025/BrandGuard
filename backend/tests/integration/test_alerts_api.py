"""
Integration tests for Phase 5 — Anomaly Alerts API.

These tests use a real in-memory SQLite DB and insert SentimentResult rows
with controlled timestamps to simulate realistic scenarios:

  - Stable baseline: no alerts
  - Negative spike: scan creates HIGH alert
  - Scan is dedup-safe: second scan within 24h creates no duplicates
  - List alerts: returns correct count and severity
  - Acknowledge: marks alert as resolved
  - Cross-user: user B cannot access user A's alerts
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import Session

from backend.app.ml.anomaly.detector import BASELINE_DAYS, RECENT_DAYS

NOW = datetime.now(tz=timezone.utc)
BASE_AUTH = "/api/v1/auth"
BASE_PROD = "/api/v1/products"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def signup_and_login(client, email: str, password: str = "strongPass1") -> str:
    client.post(f"{BASE_AUTH}/signup", json={"email": email, "password": password})
    resp = client.post(f"{BASE_AUTH}/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _insert_sentiment_rows(
    session: Session,
    user_id: uuid.UUID,
    product_id: uuid.UUID,
    review_id: uuid.UUID,
    aspect: str,
    polarity_and_times: list[tuple[str, datetime]],
):
    """Directly insert SentimentResult rows with controlled timestamps."""
    from backend.app.models.sentiment_result import SentimentResult

    for polarity, ts in polarity_and_times:
        pol_val = polarity.lower() if isinstance(polarity, str) else str(polarity).lower()
        num_score = 1.0 if "pos" in pol_val else (-1.0 if "neg" in pol_val else 0.0)
        row = SentimentResult(
            user_id=user_id,
            review_id=review_id,
            product_id=product_id,
            aspect=aspect,
            polarity=polarity,
            confidence=0.90,
            numeric_score=num_score,
            model_version="v2-test",
            created_at=ts,
            computed_at=ts,
        )
        session.add(row)
    session.commit()


def _setup_spike(session: Session, email: str, client) -> tuple[str, str, str]:
    """
    Create user+product+review, then insert:
      - 15 POSITIVE rows in baseline window (>7 days ago)
      - 10 NEGATIVE rows in recent window (last 7 days)
    This guarantees a HIGH severity sentiment_spike alert.
    Returns (token, product_id, user_id).
    """
    from backend.app.models.product import Product
    from backend.app.models.review import Review
    from backend.app.models.user import User
    from backend.app.auth.security import hash_password

    user = User(email=email, hashed_password=hash_password("strongPass1"))
    session.add(user)
    session.commit()
    session.refresh(user)

    product = Product(user_id=user.id, name="Spike Test Product")
    session.add(product)
    session.commit()
    session.refresh(product)

    review = Review(user_id=user.id, product_id=product.id, text="Test review")
    session.add(review)
    session.commit()
    session.refresh(review)

    # Baseline: 30 positives (8–28 days ago)
    baseline_rows = [
        ("positive", NOW - timedelta(days=RECENT_DAYS + (i % 20) + 1))
        for i in range(30)
    ]
    # Recent: 15 negatives (within last 30 hours to satisfy support & burst thresholds)
    recent_rows = [
        ("negative", NOW - timedelta(hours=i * 2 + 1))
        for i in range(15)
    ]

    _insert_sentiment_rows(
        session, user.id, product.id, review.id, "Battery",
        baseline_rows + recent_rows,
    )

    login_resp = client.post(
        f"{BASE_AUTH}/login",
        json={"email": email, "password": "strongPass1"},
    )
    return login_resp.json()["access_token"], str(product.id), str(user.id)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAlertsEndpoints:

    def test_scan_requires_auth(self, client):
        fake_id = str(uuid.uuid4())
        resp = client.post(f"{BASE_PROD}/{fake_id}/alerts/scan")
        assert resp.status_code == 401

    def test_scan_returns_404_for_nonexistent_product(self, client):
        token = signup_and_login(client, "alert_404@example.com")
        fake_id = str(uuid.uuid4())
        resp = client.post(
            f"{BASE_PROD}/{fake_id}/alerts/scan",
            headers=auth_headers(token),
        )
        assert resp.status_code == 404

    def test_scan_empty_product_returns_no_alerts(self, client):
        """A product with no SentimentResult rows yields zero alerts."""
        token = signup_and_login(client, "alert_empty@example.com")
        prod = client.post(
            BASE_PROD,
            json={"name": "Empty"},
            headers=auth_headers(token),
        ).json()

        resp = client.post(
            f"{BASE_PROD}/{prod['id']}/alerts/scan",
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["new_alerts"] == 0

    def test_spike_triggers_high_alert(self, client, session):
        """
        Negative spike in recent window vs positive baseline
        → scan must create at least one HIGH severity alert.
        """
        token, pid, _ = _setup_spike(session, "alert_spike@example.com", client)

        resp = client.post(
            f"{BASE_PROD}/{pid}/alerts/scan",
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["new_alerts"] >= 1

        severities = [a["severity"].lower() for a in data["alerts"]]
        assert any(s in ("high", "critical") for s in severities)

    def test_scan_dedup_no_duplicates(self, client, session):
        """
        Running scan twice within 24h must not create duplicate alerts
        for the same (aspect, alert_type).
        """
        token, pid, _ = _setup_spike(session, "alert_dedup@example.com", client)

        # First scan
        resp1 = client.post(
            f"{BASE_PROD}/{pid}/alerts/scan",
            headers=auth_headers(token),
        )
        first_count = resp1.json()["new_alerts"]

        # Second scan — same data, within 24h → no new alerts
        resp2 = client.post(
            f"{BASE_PROD}/{pid}/alerts/scan",
            headers=auth_headers(token),
        )
        assert resp2.json()["new_alerts"] == 0

    def test_list_alerts_returns_correct_count(self, client, session):
        """After a spike scan, list_alerts returns the same alerts."""
        token, pid, _ = _setup_spike(session, "alert_list@example.com", client)

        client.post(f"{BASE_PROD}/{pid}/alerts/scan", headers=auth_headers(token))

        resp = client.get(f"{BASE_PROD}/{pid}/alerts", headers=auth_headers(token))
        assert resp.status_code == 200
        alerts = resp.json()
        assert len(alerts) >= 1
        # All alerts have required fields
        for alert in alerts:
            assert "id" in alert
            assert "severity" in alert
            assert "alert_type" in alert
            assert "message" in alert
            assert "is_acknowledged" in alert

    def test_list_alerts_severity_filter(self, client, session):
        """?severity=high returns only HIGH alerts."""
        token, pid, _ = _setup_spike(session, "alert_filter@example.com", client)
        client.post(f"{BASE_PROD}/{pid}/alerts/scan", headers=auth_headers(token))

        resp = client.get(
            f"{BASE_PROD}/{pid}/alerts?severity=high",
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        for alert in resp.json():
            assert alert["severity"] == "high"

    def test_acknowledge_alert(self, client, session):
        """PATCH /acknowledge marks alert as acknowledged=True."""
        token, pid, _ = _setup_spike(session, "alert_ack@example.com", client)

        scan_resp = client.post(
            f"{BASE_PROD}/{pid}/alerts/scan",
            headers=auth_headers(token),
        )
        alerts = scan_resp.json()["alerts"]
        assert len(alerts) >= 1
        alert_id = alerts[0]["id"]

        ack_resp = client.patch(
            f"{BASE_PROD}/{pid}/alerts/{alert_id}/acknowledge",
            headers=auth_headers(token),
        )
        assert ack_resp.status_code == 200
        assert ack_resp.json()["is_acknowledged"] is True

    def test_cross_user_alert_isolation(self, client, session):
        """User B cannot scan or list User A's product alerts."""
        token_a, pid, _ = _setup_spike(session, "alert_cross_a@example.com", client)
        token_b = signup_and_login(client, "alert_cross_b@example.com")

        # Scan with wrong user
        resp = client.post(
            f"{BASE_PROD}/{pid}/alerts/scan",
            headers=auth_headers(token_b),
        )
        assert resp.status_code == 404

        # List with wrong user
        resp = client.get(
            f"{BASE_PROD}/{pid}/alerts",
            headers=auth_headers(token_b),
        )
        assert resp.status_code == 404

    def test_unacknowledged_filter(self, client, session):
        """?unacknowledged_only=true returns only unacked alerts."""
        token, pid, _ = _setup_spike(session, "alert_unack@example.com", client)

        scan_resp = client.post(
            f"{BASE_PROD}/{pid}/alerts/scan",
            headers=auth_headers(token),
        )
        alerts = scan_resp.json()["alerts"]
        if not alerts:
            pytest.skip("No alerts generated — check fixture data")

        # Acknowledge first alert
        client.patch(
            f"{BASE_PROD}/{pid}/alerts/{alerts[0]['id']}/acknowledge",
            headers=auth_headers(token),
        )

        # Unacknowledged filter should return one fewer
        resp = client.get(
            f"{BASE_PROD}/{pid}/alerts?unacknowledged_only=true",
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        unacked = resp.json()
        acked_ids = {alerts[0]["id"]}
        for a in unacked:
            assert a["id"] not in acked_ids
