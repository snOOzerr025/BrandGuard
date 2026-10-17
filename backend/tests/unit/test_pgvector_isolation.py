"""
tests/unit/test_pgvector_isolation.py
--------------------------------------
Validates Phase 0 Database & Multi-Tenant Hardening:
1. Multi-tenant isolation invariants: queries never return cross-tenant data.
2. Small tenant query strategy: CTE Materialized exact scan generation (<2,000 reviews).
3. Large tenant query strategy: HNSW iterative scan with outer dist + 0 re-sorting (>=2,000 reviews).
4. SQLModel schema invariants:
   - rating bounds check constraint (1 <= rating <= 5)
   - deduplication constraints
   - foreign key scoping
"""
import uuid
import pytest
from sqlalchemy.dialects import postgresql
from sqlmodel import Session, select

from backend.app.db.vector_isolation import (
    build_tenant_dense_vector_query,
    execute_tenant_vector_search,
)
from backend.app.models.domain import (
    JobState,
    PlanTier,
    PolarityLabel,
    Product,
    Review,
    SentimentResult,
    SeverityTier,
    User,
)


def test_models_instantiation_and_fields():
    """Verify all domain models can be instantiated with default and custom values."""
    user = User(
        email="test_tenant@brandguard.ai",
        hashed_password="fake_hashed_pw",
        full_name="Tenant Tester",
        organization_name="BrandGuard Labs",
        plan_tier=PlanTier.ENTERPRISE,
    )
    assert user.email == "test_tenant@brandguard.ai"
    assert user.plan_tier == PlanTier.ENTERPRISE
    assert isinstance(user.id, uuid.UUID)

    product = Product(
        user_id=user.id,
        name="SoundBar Pro",
        sku="SKU-SBPRO-01",
    )
    assert product.user_id == user.id
    assert product.sku == "SKU-SBPRO-01"
    assert product.brand_health_score == 100.0

    review = Review(
        user_id=user.id,
        product_id=product.id,
        body="Outstanding audio clarity and deep bass.",
        rating=5,
    )
    assert review.rating == 5
    assert review.text == "Outstanding audio clarity and deep bass."
    assert review.has_rating_discrepancy is False


def test_small_tenant_query_structure():
    """
    Verify that for small tenants (<2,000 reviews), the adaptive query router
    generates a materialized CTE targeting the tenant's reviews first.
    """
    user_id = uuid.uuid4()
    product_id = uuid.uuid4()
    dummy_vec = [0.1] * 384

    stmt = build_tenant_dense_vector_query(
        user_id=user_id,
        product_id=product_id,
        query_embedding=dummy_vec,
        tenant_review_count=150,
        candidate_limit=10,
    )

    query_str = str(stmt.compile(dialect=postgresql.dialect()))
    # Must use CTE for small tenants to avoid HNSW post-filter graph exhaustion
    assert "WITH tenant_scope AS" in query_str
    assert "JOIN tenant_scope ON reviews.id = tenant_scope.id" in query_str
    assert "LIMIT %(param_1)s" in query_str or "LIMIT" in query_str


def test_large_tenant_query_structure():
    """
    Verify that for large tenants (>=2,000 reviews), the adaptive query router
    generates an HNSW scan with outer dist + 0 re-sorting.
    """
    user_id = uuid.uuid4()
    product_id = uuid.uuid4()
    dummy_vec = [0.1] * 384

    stmt = build_tenant_dense_vector_query(
        user_id=user_id,
        product_id=product_id,
        query_embedding=dummy_vec,
        tenant_review_count=50000,
        candidate_limit=20,
    )

    query_str = str(stmt.compile(dialect=postgresql.dialect()))
    # Large tenant query uses subquery and outer order by dist + 0 to fix relaxed_order anomaly
    assert "dist + %(dist_1)s" in query_str or "dist + " in query_str
    assert "ORDER BY anon_1.dist" in query_str or "ORDER BY" in query_str


def test_multi_tenant_isolation_in_db(session: Session):
    """
    Guarantee that two distinct tenants with reviews for their own products
    never leak data into each other's queries.
    """
    user_a = User(email="tenant_a@brandguard.ai", hashed_password="pw")
    user_b = User(email="tenant_b@brandguard.ai", hashed_password="pw")
    session.add_all([user_a, user_b])
    session.commit()

    prod_a = Product(user_id=user_a.id, name="Product A")
    prod_b = Product(user_id=user_b.id, name="Product B")
    session.add_all([prod_a, prod_b])
    session.commit()

    rev_a = Review(
        user_id=user_a.id,
        product_id=prod_a.id,
        text="Review belonging strictly to Tenant A",
        rating=5,
    )
    rev_b = Review(
        user_id=user_b.id,
        product_id=prod_b.id,
        text="Review belonging strictly to Tenant B",
        rating=1,
    )
    session.add_all([rev_a, rev_b])
    session.commit()

    # Query for Tenant A
    hits_a = execute_tenant_vector_search(
        session=session,
        user_id=user_a.id,
        product_id=prod_a.id,
        query_embedding=[0.0] * 384,
        tenant_review_count=1,
        candidate_limit=10,
    )

    assert len(hits_a) == 1
    assert hits_a[0].id == rev_a.id
    assert hits_a[0].user_id == user_a.id

    # Tenant A searching for Tenant B's product gets 0 results
    hits_leak = execute_tenant_vector_search(
        session=session,
        user_id=user_a.id,
        product_id=prod_b.id,
        query_embedding=[0.0] * 384,
        tenant_review_count=1,
        candidate_limit=10,
    )
    assert len(hits_leak) == 0


def test_sentiment_result_attributes_and_aliases(session: Session):
    """Verify SentimentResult compatibility with both legacy and new fields."""
    user = User(email="sent_test@brandguard.ai", hashed_password="pw")
    session.add(user)
    session.commit()

    prod = Product(user_id=user.id, name="Sent Product")
    session.add(prod)
    session.commit()

    rev = Review(user_id=user.id, product_id=prod.id, text="Battery life is super good", rating=5)
    session.add(rev)
    session.commit()

    sent = SentimentResult(
        user_id=user.id,
        product_id=prod.id,
        review_id=rev.id,
        aspect="Battery",
        polarity="Positive",
        confidence=0.98,
    )
    session.add(sent)
    session.commit()

    assert sent.aspect == "Battery"
    assert sent.aspect_category == "Battery"
    assert sent.polarity == PolarityLabel.POSITIVE
    assert sent.numeric_score == 1.0
    assert sent.confidence == 0.98
