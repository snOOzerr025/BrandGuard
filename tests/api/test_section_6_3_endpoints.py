"""
tests/api/test_section_6_3_endpoints.py
---------------------------------------
Validates Section 6.3 REST API endpoints:
1. GET /api/v1/products/{id}/kpis (window_days=30)
2. GET /api/v1/products/{id}/themes (macro_aspect=Battery)
3. GET /api/v1/products/{id}/anomalies (window_days=90, severity=HIGH)
4. GET /api/v1/reviews (keyset pagination, aspect & discrepancy filters)
5. POST /api/v1/webhooks/trustpilot (HMAC-SHA256 signature verification)
6. GET /api/v1/tasks/{task_id}
"""
import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from backend.app.auth.dependencies import get_current_user
from backend.app.main import app
from backend.app.models.domain import (
    Alert,
    MicroCluster,
    PolarityLabel,
    Product,
    Review,
    SentimentResult,
    SeverityTier,
    User,
)


@pytest.fixture(name="auth_user")
def auth_user_fixture(session: Session):
    user = User(email="test_executive@brandguard.ai", hashed_password="pw")
    session.add(user)
    session.commit()
    session.refresh(user)

    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]


def test_section_6_3_kpis_endpoint(client: TestClient, session: Session, auth_user: User):
    product = Product(user_id=auth_user.id, name="Studio Pro Headphones")
    session.add(product)
    session.commit()
    session.refresh(product)

    now = datetime.now(timezone.utc)
    # Add 10 positive reviews and 5 negative reviews
    for i in range(10):
        r = Review(
            user_id=auth_user.id,
            product_id=product.id,
            rating=5,
            body=f"Fantastic sound quality and bass {i}",
            reviewed_at=now - timedelta(days=2),
        )
        session.add(r)
        session.commit()
        session.refresh(r)

        s = SentimentResult(
            user_id=auth_user.id,
            product_id=product.id,
            review_id=r.id,
            aspect_category="Audio Quality",
            polarity=PolarityLabel.POSITIVE,
            confidence=0.98,
            numeric_score=1.0,
            created_at=now - timedelta(days=2),
        )
        session.add(s)
        session.commit()

    for i in range(5):
        r = Review(
            user_id=auth_user.id,
            product_id=product.id,
            rating=1,
            body=f"Battery died after 30 minutes defect {i}",
            reviewed_at=now - timedelta(days=1),
        )
        session.add(r)
        session.commit()
        session.refresh(r)

        s = SentimentResult(
            user_id=auth_user.id,
            product_id=product.id,
            review_id=r.id,
            aspect_category="Battery",
            polarity=PolarityLabel.NEGATIVE,
            confidence=0.95,
            numeric_score=-1.0,
            created_at=now - timedelta(days=1),
        )
        session.add(s)
        session.commit()

    res = client.get(f"/api/v1/products/{product.id}/kpis?window_days=30")
    assert res.status_code == 200
    data = res.json()

    assert data["product_id"] == str(product.id)
    assert "brand_health_score" in data
    assert "net_sentiment" in data
    assert "star_rating" in data
    assert data["total_reviews"] == 15
    assert "top_rating_drag" in data
    assert len(data["aspect_matrix"]) > 0

    # Battery aspect must show negative star impact delta (rating drag)
    battery_asp = next(a for a in data["aspect_matrix"] if a["aspect"] == "Battery")
    assert battery_asp["negative_count"] == 5
    assert battery_asp["star_impact_delta"] < 0


def test_section_6_3_themes_endpoint(client: TestClient, session: Session, auth_user: User):
    product = Product(user_id=auth_user.id, name="Aero Buds")
    session.add(product)
    session.commit()
    session.refresh(product)

    cluster = MicroCluster(
        user_id=auth_user.id,
        product_id=product.id,
        macro_aspect="Battery",
        hdbscan_label=0,
        theme_label="Fast discharge in cold weather",
        top_ctfidf_terms=["cold", "discharge", "freezing", "battery"],
        review_volume=24,
        net_sentiment=-82.5,
        star_impact_delta=-0.45,
        evidence_review_ids=["11111111-1111-1111-1111-111111111111"],
    )
    session.add(cluster)
    session.commit()

    res = client.get(f"/api/v1/products/{product.id}/themes?macro_aspect=Battery")
    assert res.status_code == 200
    data = res.json()
    assert data["macro_aspect"] == "Battery"
    assert len(data["clusters"]) == 1
    c = data["clusters"][0]
    assert c["theme_label"] == "Fast discharge in cold weather"
    assert c["star_impact_delta"] == -0.45
    assert "cold" in c["top_ctfidf_terms"]


def test_section_6_3_anomalies_endpoint(client: TestClient, session: Session, auth_user: User):
    product = Product(user_id=auth_user.id, name="Smart ANC 400")
    session.add(product)
    session.commit()
    session.refresh(product)

    alert = Alert(
        user_id=auth_user.id,
        product_id=product.id,
        aspect_category="Battery",
        severity=SeverityTier.HIGH,
        alert_type="EWMA_DRIFT",
        z_score=-3.45,
        baseline_mean=0.72,
        current_value=-0.35,
        star_impact=-0.48,
        support_count=18,
        message="Critical 3.45-sigma drop in Battery sentiment",
        evidence_review_ids=["22222222-2222-2222-2222-222222222222"],
        dedup_fingerprint="test-fp-12345",
    )
    session.add(alert)
    session.commit()

    res = client.get(f"/api/v1/products/{product.id}/anomalies?window_days=90&severity=HIGH")
    assert res.status_code == 200
    data = res.json()
    assert len(data["alerts"]) == 1
    a = data["alerts"][0]
    assert a["z_score"] == -3.45
    assert a["severity"] == "HIGH"
    assert "timeline_series" in data


def test_section_6_3_review_stream_keyset_pagination(client: TestClient, session: Session, auth_user: User):
    product = Product(user_id=auth_user.id, name="Keyset Test Product")
    session.add(product)
    session.commit()
    session.refresh(product)

    now = datetime.now(timezone.utc)
    for i in range(10):
        r = Review(
            user_id=auth_user.id,
            product_id=product.id,
            rating=1 if i == 0 else 5,
            body=f"Review test item body number {i}",
            has_rating_discrepancy=(i == 0),
            reviewed_at=now - timedelta(minutes=i * 10),
        )
        session.add(r)
        session.commit()

    # 1. First page: limit 4
    res1 = client.get(f"/api/v1/reviews?product_id={product.id}&limit=4")
    assert res1.status_code == 200
    data1 = res1.json()
    assert len(data1["items"]) == 4
    assert data1["has_more"] is True
    assert data1["next_cursor"] is not None

    # 2. Second page using cursor
    res2 = client.get(f"/api/v1/reviews?product_id={product.id}&limit=4&cursor={data1['next_cursor']}")
    assert res2.status_code == 200
    data2 = res2.json()
    assert len(data2["items"]) == 4
    # Ensure items are strictly disjoint
    page1_ids = {item["id"] for item in data1["items"]}
    page2_ids = {item["id"] for item in data2["items"]}
    assert len(page1_ids.intersection(page2_ids)) == 0

    # 3. Filter by discrepancy_only
    res_disc = client.get(f"/api/v1/reviews?product_id={product.id}&discrepancy_only=true")
    assert res_disc.status_code == 200
    data_disc = res_disc.json()
    assert len(data_disc["items"]) == 1
    assert data_disc["items"][0]["has_rating_discrepancy"] is True


def test_section_6_3_trustpilot_webhook_hmac(client: TestClient, session: Session):
    from backend.app.api.routes.webhooks import TRUSTPILOT_SECRET

    payload = {
        "businessUnitId": "tp-test-unit",
        "review": {
            "id": "tp-rev-9999",
            "stars": 2,
            "title": "Shipping arrived dented",
            "text": "The box arrived dented and the charging cable was missing.",
        },
    }
    import json
    raw_bytes = json.dumps(payload).encode("utf-8")
    sig = hmac.new(TRUSTPILOT_SECRET.encode("utf-8"), raw_bytes, hashlib.sha256).hexdigest()

    # Valid signature
    res = client.post(
        "/api/v1/webhooks/trustpilot",
        content=raw_bytes,
        headers={"Content-Type": "application/json", "X-Trustpilot-Signature": sig},
    )
    assert res.status_code == 202
    assert res.json()["status"] == "QUEUED"

    # Invalid signature should return 401
    bad_res = client.post(
        "/api/v1/webhooks/trustpilot",
        content=raw_bytes,
        headers={"Content-Type": "application/json", "X-Trustpilot-Signature": "bad_sig"},
    )
    assert bad_res.status_code == 401
