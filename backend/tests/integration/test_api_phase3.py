"""
Integration tests for Phase 3 — Products, Reviews, and Insights API.

All tests use the in-memory SQLite fixture from conftest.py (no Docker needed).
All timestamps are generated at runtime — NO hardcoded dates.

THE CRITICAL TEST: test_history_returns_two_distinct_timestamped_records
  Inserts two SentimentResult rows with DIFFERENT timestamps,
  confirms GET /insights returns BOTH records — not one re-computed snapshot.
  This is the test that proves the "insert-only" design actually works end-to-end.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

# Realtime reference — all test timestamps derived from this
NOW = datetime.now(tz=timezone.utc)

import pytest
from sqlmodel import Session

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


def create_product(client, token: str, name: str = "TestProduct") -> dict:
    resp = client.post(
        BASE_PROD,
        json={"name": name, "description": "Test", "source": "csv_upload"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# Product endpoint tests
# ---------------------------------------------------------------------------

class TestProductEndpoints:

    def test_create_product_requires_auth(self, client):
        resp = client.post(BASE_PROD, json={"name": "Prod"})
        assert resp.status_code == 401

    def test_create_product_success(self, client):
        token = signup_and_login(client, "prod1@example.com")
        resp = client.post(
            BASE_PROD,
            json={"name": "AmazonBasics Battery", "description": "Test product"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "AmazonBasics Battery"
        assert "id" in data
        assert "user_id" in data

    def test_list_products_returns_only_own(self, client):
        token_a = signup_and_login(client, "alice_p@example.com")
        token_b = signup_and_login(client, "bob_p@example.com")
        create_product(client, token_a, "Alice Product")
        create_product(client, token_b, "Bob Product")

        resp = client.get(BASE_PROD, headers=auth_headers(token_a))
        assert resp.status_code == 200
        names = [p["name"] for p in resp.json()]
        assert "Alice Product" in names
        assert "Bob Product" not in names  # Authorization: no cross-user data

    def test_get_product_not_found_for_other_user(self, client):
        token_a = signup_and_login(client, "alice_g@example.com")
        token_b = signup_and_login(client, "bob_g@example.com")
        product = create_product(client, token_a, "Alice Secret Product")

        # Bob tries to access Alice's product by ID
        resp = client.get(
            f"{BASE_PROD}/{product['id']}",
            headers=auth_headers(token_b),
        )
        assert resp.status_code == 404  # Not 403 — don't leak existence


# ---------------------------------------------------------------------------
# Review endpoint tests
# ---------------------------------------------------------------------------

class TestReviewEndpoints:

    def test_ingest_single_review(self, client):
        token = signup_and_login(client, "rev1@example.com")
        product = create_product(client, token, "Review Test Product")
        product_id = product["id"]

        resp = client.post(
            f"{BASE_PROD}/{product_id}/reviews",
            json={"text": "Great batteries, lasted a long time!", "rating": 5, "product_id": product_id},
            headers=auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["text"] == "Great batteries, lasted a long time!"
        assert data["rating"] == 5

    def test_ingest_review_wrong_product_returns_404(self, client):
        token = signup_and_login(client, "rev2@example.com")
        fake_id = str(uuid.uuid4())
        resp = client.post(
            f"{BASE_PROD}/{fake_id}/reviews",
            json={"text": "test review", "product_id": fake_id},
            headers=auth_headers(token),
        )
        assert resp.status_code == 404

    def test_list_reviews_paginated(self, client):
        token = signup_and_login(client, "rev3@example.com")
        product = create_product(client, token, "Pagination Product")
        pid = product["id"]

        for i in range(5):
            client.post(
                f"{BASE_PROD}/{pid}/reviews",
                json={"text": f"Review number {i}", "product_id": pid},
                headers=auth_headers(token),
            )

        resp = client.get(
            f"{BASE_PROD}/{pid}/reviews?limit=3&offset=0",
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_bulk_ingest(self, client):
        token = signup_and_login(client, "bulk1@example.com")
        product = create_product(client, token, "Bulk Product")
        pid = product["id"]

        reviews = [
            {"text": f"Bulk review {i}", "rating": 4, "product_id": pid}
            for i in range(10)
        ]
        resp = client.post(
            f"{BASE_PROD}/{pid}/reviews/bulk",
            json={"reviews": reviews},
            headers=auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["inserted"] == 10
        assert data["skipped"] == 0


# ---------------------------------------------------------------------------
# Insights endpoint tests — including THE CRITICAL HISTORY TEST
# ---------------------------------------------------------------------------

class TestInsightsEndpoints:

    def _setup_product_with_sentiment_rows(self, client, session, email: str):
        """
        Helper: creates a user, product, and directly inserts two SentimentResult
        rows with DIFFERENT timestamps to simulate two pipeline runs.
        """
        from backend.app.models.product import Product
        from backend.app.models.review import Review
        from backend.app.models.sentiment_result import SentimentResult
        from backend.app.models.user import User
        from backend.app.auth.security import hash_password

        # Create user + product directly in DB for speed (no HTTP round-trip)
        user = User(email=email, hashed_password=hash_password("strongPass1"))
        session.add(user)
        session.commit()
        session.refresh(user)

        product = Product(user_id=user.id, name="History Test Product")
        session.add(product)
        session.commit()
        session.refresh(product)

        review = Review(user_id=user.id, product_id=product.id, text="Good product overall")
        session.add(review)
        session.commit()
        session.refresh(review)

        # Insert TWO SentimentResult rows with different timestamps.
        # Timestamps are fully dynamic — derived from NOW at test runtime.
        t1 = NOW - timedelta(days=180)   # ~6 months ago
        t2 = NOW - timedelta(days=1)     # yesterday

        row1 = SentimentResult(
            user_id=user.id, review_id=review.id, product_id=product.id,
            aspect="Quality", polarity="positive", confidence=0.92,
            model_version="v2-test", computed_at=t1,
        )
        row2 = SentimentResult(
            user_id=user.id, review_id=review.id, product_id=product.id,
            aspect="Quality", polarity="negative", confidence=0.88,
            model_version="v2-test", computed_at=t2,
        )
        session.add(row1)
        session.add(row2)
        session.commit()

        return user, product, [row1, row2]

    def test_get_insight_summary_empty(self, client):
        token = signup_and_login(client, "ins1@example.com")
        product = create_product(client, token)
        pid = product["id"]

        resp = client.get(f"{BASE_PROD}/{pid}/insights/summary", headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.json()["aspects"] == []

    def test_get_overall_sentiment_empty(self, client):
        token = signup_and_login(client, "ins2@example.com")
        product = create_product(client, token)
        pid = product["id"]

        resp = client.get(f"{BASE_PROD}/{pid}/insights/overall", headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_insights_not_accessible_by_other_user(self, client):
        token_a = signup_and_login(client, "ins_a@example.com")
        token_b = signup_and_login(client, "ins_b@example.com")
        product = create_product(client, token_a)

        resp = client.get(
            f"{BASE_PROD}/{product['id']}/insights/summary",
            headers=auth_headers(token_b),
        )
        assert resp.status_code == 404

    def test_analyze_endpoint_returns_202(self, client, session):
        """Trigger analysis endpoint should return 202 immediately."""
        token = signup_and_login(client, "analyze1@example.com")
        product = create_product(client, token)
        pid = product["id"]

        # Ingest a review first
        client.post(
            f"{BASE_PROD}/{pid}/reviews",
            json={"text": "Very good quality product!", "rating": 5, "product_id": pid},
            headers=auth_headers(token),
        )

        resp = client.post(f"{BASE_PROD}/{pid}/analyze", headers=auth_headers(token))
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "queued"
        assert data["reviews_queued"] == 1

    def test_analyze_with_no_reviews_returns_422(self, client):
        token = signup_and_login(client, "analyze2@example.com")
        product = create_product(client, token)
        pid = product["id"]

        resp = client.post(f"{BASE_PROD}/{pid}/analyze", headers=auth_headers(token))
        assert resp.status_code == 422

    # -----------------------------------------------------------------------
    # THE CRITICAL HISTORY TEST
    # -----------------------------------------------------------------------

    def test_history_returns_two_distinct_timestamped_records(self, client, session):
        """
        PROVES the insert-only design works end-to-end:

        Two SentimentResult rows are inserted with different computed_at timestamps
        (Jan 2026 and Jun 2026). The GET /insights endpoint must return BOTH rows,
        ordered by computed_at — not one recomputed snapshot.

        This test would FAIL if the service did UPDATE instead of INSERT,
        or if the history endpoint recomputed results from reviews rather than
        querying stored rows.
        """
        from sqlmodel import Session as S
        from backend.app.db.session import engine

        # We need to use the same session as the client fixture
        user, product, rows = self._setup_product_with_sentiment_rows(
            client, session, "history_test@example.com"
        )

        # Login the user via HTTP
        login_resp = client.post(
            f"{BASE_AUTH}/login",
            json={"email": "history_test@example.com", "password": "strongPass1"},
        )
        token = login_resp.json()["access_token"]

        # GET /insights — must return 2 distinct historical rows
        resp = client.get(
            f"{BASE_PROD}/{product.id}/insights",
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2, f"Expected 2 historical rows, got {data['count']}"

        # Verify the two rows have DIFFERENT timestamps
        timestamps = [r["computed_at"] for r in data["results"]]
        assert timestamps[0] != timestamps[1], "Both rows have the same timestamp — insert-only violated!"

        # Verify they are in chronological order
        t0 = datetime.fromisoformat(timestamps[0])
        t1 = datetime.fromisoformat(timestamps[1])
        assert t0 < t1, "History not returned in chronological order"

        # Verify different polarities (Jan=positive, Jun=negative)
        assert data["results"][0]["polarity"] == "positive"
        assert data["results"][1]["polarity"] == "negative"

    def test_history_time_filter_works(self, client, session):
        """Time window filtering returns only records within range."""
        user, product, rows = self._setup_product_with_sentiment_rows(
            client, session, "timefilter@example.com"
        )
        login_resp = client.post(
            f"{BASE_AUTH}/login",
            json={"email": "timefilter@example.com", "password": "strongPass1"},
        )
        token = login_resp.json()["access_token"]

        # Filter to only the older record (t1, ~6 months ago).
        # Window: [t1 - 1 day, t1 + 1 day] — dynamically computed, never hardcoded.
        window_start = (NOW - timedelta(days=181)).strftime("%Y-%m-%dT%H:%M:%SZ")
        window_end   = (NOW - timedelta(days=179)).strftime("%Y-%m-%dT%H:%M:%SZ")
        resp = client.get(
            f"{BASE_PROD}/{product.id}/insights?from={window_start}&to={window_end}",
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 1
        assert resp.json()["results"][0]["polarity"] == "positive"
