"""
Integration tests for Phase 4 — Ask BrandGuard RAG endpoint.

Strategy:
  - No real Gemini API calls in tests (no API key in CI)
  - The gemini_client gracefully returns structured fallback responses when
    GEMINI_API_KEY is not set — tests assert on the endpoint structure, not
    the LLM output content.
  - Real DB (SQLite in-memory) with real reviews and real SentimentResult rows.
  - FallbackRetriever auto-detected (SQLite dialect) — no pgvector needed.

What is tested:
  1. Chat endpoint requires auth
  2. Chat endpoint returns 404 for non-owned product
  3. Chat endpoint returns valid ChatResponse structure
  4. Chat endpoint returns 422 for too-short questions
  5. Chat endpoint with reviews returns non-empty answer field
  6. QueryLog row is eventually written (async)
  7. Cross-user isolation: user B cannot ask about user A's product
"""
from __future__ import annotations

import pytest
from sqlmodel import Session, select

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


def create_product_with_reviews(client, token: str, n_reviews: int = 5) -> dict:
    """Create product and ingest n_reviews into it."""
    prod_resp = client.post(
        BASE_PROD,
        json={"name": "RAG Test Product", "source": "csv_upload"},
        headers=auth_headers(token),
    )
    product = prod_resp.json()
    pid = product["id"]

    reviews = [
        {
            "text": f"The battery life is {'excellent' if i % 2 == 0 else 'terrible'}. "
                    f"Quality {'feels premium' if i % 3 == 0 else 'needs improvement'}.",
            "rating": (i % 5) + 1,
            "product_id": pid,
        }
        for i in range(n_reviews)
    ]
    client.post(
        f"{BASE_PROD}/{pid}/reviews/bulk",
        json={"reviews": reviews},
        headers=auth_headers(token),
    )
    return product


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestChatEndpoint:

    def test_chat_requires_auth(self, client):
        """Chat endpoint must reject unauthenticated requests."""
        resp = client.post(
            f"{BASE_PROD}/00000000-0000-0000-0000-000000000000/chat",
            json={"question": "What do customers say?"},
        )
        assert resp.status_code == 401

    def test_chat_returns_404_for_nonexistent_product(self, client):
        """404 for product that doesn't exist — not 403 (don't leak existence)."""
        import uuid
        token = signup_and_login(client, "chat_404@example.com")
        fake_id = str(uuid.uuid4())
        resp = client.post(
            f"{BASE_PROD}/{fake_id}/chat",
            json={"question": "What do customers complain about?"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 404

    def test_chat_cross_user_isolation(self, client):
        """User B cannot ask about User A's product — must get 404."""
        token_a = signup_and_login(client, "chat_a@example.com")
        token_b = signup_and_login(client, "chat_b@example.com")
        product = create_product_with_reviews(client, token_a, n_reviews=3)

        resp = client.post(
            f"{BASE_PROD}/{product['id']}/chat",
            json={"question": "What do customers say about quality?"},
            headers=auth_headers(token_b),  # wrong user
        )
        assert resp.status_code == 404

    def test_chat_question_too_short_returns_422(self, client):
        """Questions under 5 chars should be rejected at validation layer."""
        token = signup_and_login(client, "chat_short@example.com")
        product = create_product_with_reviews(client, token, n_reviews=2)

        resp = client.post(
            f"{BASE_PROD}/{product['id']}/chat",
            json={"question": "Hi"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 422

    def test_chat_returns_valid_response_structure(self, client):
        """
        Chat endpoint must return a valid ChatResponse with all required fields.
        Content is not asserted (no API key in tests) — structure is.
        """
        token = signup_and_login(client, "chat_struct@example.com")
        product = create_product_with_reviews(client, token, n_reviews=5)

        resp = client.post(
            f"{BASE_PROD}/{product['id']}/chat",
            json={"question": "What are the main complaints about this product?"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()

        # All required fields must be present
        assert "answer" in data, "Missing 'answer' field"
        assert "citations" in data, "Missing 'citations' field"
        assert "confidence" in data, "Missing 'confidence' field"
        assert "query_type_used" in data, "Missing 'query_type_used' field"

        # Type checks
        assert isinstance(data["answer"], str)
        assert isinstance(data["citations"], list)
        assert data["confidence"] in ("high", "medium", "low")
        assert data["query_type_used"] in ("PURE_VECTOR", "SQL_AGGREGATE", "HYBRID")

    def test_chat_answer_is_non_empty(self, client):
        """The answer field should never be an empty string."""
        token = signup_and_login(client, "chat_nonempty@example.com")
        product = create_product_with_reviews(client, token, n_reviews=3)

        resp = client.post(
            f"{BASE_PROD}/{product['id']}/chat",
            json={"question": "How is the overall sentiment for this product?"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        assert len(resp.json()["answer"]) > 0

    def test_chat_empty_product_still_returns_200(self, client):
        """
        A product with no reviews should still return a 200 with a structured
        response — not a 500. The answer should communicate no data available.
        """
        token = signup_and_login(client, "chat_empty@example.com")
        prod_resp = client.post(
            BASE_PROD,
            json={"name": "Empty Product"},
            headers=auth_headers(token),
        )
        pid = prod_resp.json()["id"]

        resp = client.post(
            f"{BASE_PROD}/{pid}/chat",
            json={"question": "What do customers think about delivery?"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        assert "answer" in resp.json()

    def test_query_log_is_written_after_chat(self, client, session):
        """
        After a chat response is returned, a QueryLog row must eventually
        exist in the DB (background task). We call the endpoint then check
        the DB directly.
        """
        from backend.app.models.query_log import QueryLog

        token = signup_and_login(client, "chat_log@example.com")
        product = create_product_with_reviews(client, token, n_reviews=3)

        resp = client.post(
            f"{BASE_PROD}/{product['id']}/chat",
            json={"question": "What is the most common complaint?"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 200

        # Background tasks run synchronously in TestClient — log should exist
        logs = session.exec(select(QueryLog)).all()
        assert len(logs) >= 1
        assert logs[-1].question == "What is the most common complaint?"
        assert len(logs[-1].answer) > 0
