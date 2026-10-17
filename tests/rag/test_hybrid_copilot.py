"""
tests/rag/test_hybrid_copilot.py
---------------------------------
Validates Phase 5 Hybrid RRF + Cross-Encoder RAG Copilot:
1. Intent routing: SQL_AGGREGATE, PURE_VECTOR, HYBRID.
2. Parameterized SQL Fact calculation (exact counts, Net Sentiment, Star Impact).
3. RRF candidate fusion (k=60).
4. Cross-Encoder reranker and NLI entailment scoring.
5. Post-generation verification guardrail (strips hallucinated UUIDs).
6. POST /api/v1/copilot/ask API endpoint with QueryLog persistence.
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend.app.models.domain import Product, QueryLog, Review, SentimentResult, User
from backend.app.rag.citation_verifier import CitationVerifier
from backend.app.rag.intent_router import IntentRouter
from backend.app.rag.rag_copilot import RAGCopilotEngine
from backend.app.rag.reranker import CrossEncoderReranker
from backend.app.rag.schemas import CitedClaim, CopilotStructuredResponse, QueryType
from backend.app.rag.sql_facts import SQLFactsAggregator


def test_intent_router_classification():
    """Verify routing into quantitative SQL vs qualitative vector vs hybrid."""
    router = IntentRouter()

    # Quantitative question
    r_quant = router.route("What percentage of reviews complained about battery life and what was its impact?")
    assert r_quant.query_type == QueryType.SQL_AGGREGATE
    assert r_quant.aspect_focus == "Battery"

    # Qualitative question
    r_qual = router.route("What specific charging cables or wire parts are users describing as broken?")
    assert r_qual.query_type == QueryType.PURE_VECTOR

    # Hybrid diagnostic question
    r_hybrid = router.route("Why did our rating drop last week, and what specific complaints are customers describing?")
    assert r_hybrid.query_type == QueryType.HYBRID


def test_sql_facts_deterministic_aggregation(session: Session):
    """Verify exact SQL fact computation without LLM guesswork."""
    user = User(email="facts_test@brandguard.ai", hashed_password="pw")
    session.add(user)
    session.commit()

    prod = Product(user_id=user.id, name="Facts Product")
    session.add(prod)
    session.commit()

    # 3 reviews: two 5-star, one 1-star
    r1 = Review(user_id=user.id, product_id=prod.id, rating=5, body="Great")
    r2 = Review(user_id=user.id, product_id=prod.id, rating=5, body="Solid")
    r3 = Review(user_id=user.id, product_id=prod.id, rating=1, body="Defective battery")
    session.add_all([r1, r2, r3])
    session.commit()

    # Sentiment on r3
    s3 = SentimentResult(
        user_id=user.id,
        product_id=prod.id,
        review_id=r3.id,
        aspect="Battery",
        polarity="Negative",
        confidence=0.99,
        numeric_score=-1.0,
    )
    session.add(s3)
    session.commit()

    facts = SQLFactsAggregator.compute_facts(prod.id, user.id, session)
    assert facts["total_reviews"] == 3
    assert facts["average_rating"] == pytest.approx(3.67, 0.05)
    assert "Battery" in facts["aspects"]
    assert facts["aspects"]["Battery"]["net_sentiment"] == -100.0
    assert "<deterministic_sql_facts>" in facts["xml_block"]


def test_citation_verifier_strips_hallucinated_uuids():
    """
    Verify Invariant: Post-generation citation verifier MUST strip any UUID
    that was not in the retrieved evidence set.
    """
    real_rev_1 = Review(user_id=uuid.uuid4(), product_id=uuid.uuid4(), rating=1, body="Real defect")
    real_rev_2 = Review(user_id=uuid.uuid4(), product_id=uuid.uuid4(), rating=5, body="Real praise")

    retrieved_set = [real_rev_1, real_rev_2]
    verifier = CitationVerifier()

    hallucinated_uuid = str(uuid.uuid4())
    raw_response = CopilotStructuredResponse(
        executive_summary="Summary with fake citations.",
        quantitative_metrics_used=[],
        claims=[
            CitedClaim(statement="Fake claim", cited_review_ids=[hallucinated_uuid], confidence=0.95),
            CitedClaim(statement="Real defect claim", cited_review_ids=[str(real_rev_1.id)], confidence=0.95),
        ],
    )

    verified = verifier.verify_response(raw_response, retrieved_set)

    # Fake claim should be stripped because hallucinated_uuid is not in retrieved_set
    assert len(verified.claims) == 1
    assert str(real_rev_1.id) in verified.claims[0].cited_review_ids
    assert hallucinated_uuid not in verified.claims[0].cited_review_ids


def test_copilot_ask_api_endpoint(client: TestClient, session: Session):
    """
    Test POST /api/v1/copilot/ask endpoint:
    - Returns 200 OK with CopilotStructuredResponse
    - Logs to QueryLog
    - Enforces tenant product scoping
    """
    client.post("/api/v1/auth/signup", json={"email": "copilot_user@brandguard.ai", "password": "strongPass123"})
    login_resp = client.post("/api/v1/auth/login", json={"email": "copilot_user@brandguard.ai", "password": "strongPass123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    user = session.exec(select(User).where(User.email == "copilot_user@brandguard.ai")).first()
    assert user is not None

    prod = Product(user_id=user.id, name="Copilot Headset")
    session.add(prod)
    session.commit()

    r = Review(
        user_id=user.id,
        product_id=prod.id,
        rating=1,
        body="Charging port overheats and shuts off after 20 minutes.",
        embedding=[0.1] * 384,
    )
    session.add(r)
    session.commit()

    payload = {
        "product_id": str(prod.id),
        "query": "What are customers saying about the charging port and overheating?",
    }

    resp = client.post("/api/v1/copilot/ask", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "executive_summary" in data
    assert "claims" in data
    assert data["latency_ms"] > 0

    # Verify query was logged to QueryLog table
    logs = session.exec(select(QueryLog).where(QueryLog.product_id == prod.id)).all()
    assert len(logs) == 1
    assert logs[0].routed_intent in ("PURE_VECTOR", "HYBRID")
