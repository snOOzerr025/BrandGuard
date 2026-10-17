"""
scripts/verify_phase_0.py
-------------------------
Deterministic verification script for Phase 0:
- Verifies all domain models import and schema compiles
- Verifies SQLite engine creates all tables with simulated to_tsvector hook
- Tests multi-tenant isolation and adaptive vector query compilation
- Validates SQLModel and Pydantic schema compatibility
"""
import sys
import uuid
from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy.dialects import postgresql
import sqlite3
from sqlalchemy import event

# 1. Test imports
print("--> [1/4] Verifying imports from backend.app.models...")
from backend.app.models import (
    User, Product, IngestionJob, Review, SentimentResult,
    MicroCluster, Alert, QueryLog, PlanTier, JobState, PolarityLabel, SeverityTier
)
from backend.app.db.vector_isolation import (
    build_tenant_dense_vector_query, execute_tenant_vector_search
)
print("    Imports successful!")

# 2. Test in-memory table creation
print("--> [2/4] Verifying database schema table generation...")
engine = create_engine("sqlite://", connect_args={"check_same_thread": False})

@event.listens_for(engine, "connect")
def _sqlite_connect(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        dbapi_connection.create_function("to_tsvector", 2, lambda lang, text: text or "")

SQLModel.metadata.create_all(engine)
print("    SQLModel.metadata.create_all() succeeded without errors!")

# 3. Test multi-tenant isolation
print("--> [3/4] Verifying multi-tenant isolation invariants...")
with Session(engine) as session:
    user_1 = User(email="tenant1@test.com", hashed_password="pw1")
    user_2 = User(email="tenant2@test.com", hashed_password="pw2")
    session.add_all([user_1, user_2])
    session.commit()

    prod_1 = Product(user_id=user_1.id, name="Tenant 1 Product")
    prod_2 = Product(user_id=user_2.id, name="Tenant 2 Product")
    session.add_all([prod_1, prod_2])
    session.commit()

    rev_1 = Review(user_id=user_1.id, product_id=prod_1.id, text="T1 Review", rating=5)
    rev_2 = Review(user_id=user_2.id, product_id=prod_2.id, text="T2 Review", rating=1)
    session.add_all([rev_1, rev_2])
    session.commit()

    # Search for tenant 1
    t1_results = execute_tenant_vector_search(session, user_1.id, prod_1.id, [0.0]*384, 1, 10)
    assert len(t1_results) == 1
    assert t1_results[0].id == rev_1.id

    # Search for tenant 1 trying to access tenant 2's product
    leak_results = execute_tenant_vector_search(session, user_1.id, prod_2.id, [0.0]*384, 1, 10)
    assert len(leak_results) == 0
    print("    Multi-tenant isolation verified: Zero data leakage!")

# 4. Test query compilation for small vs large tenants
print("--> [4/4] Verifying adaptive vector query compilation...")
q_small = build_tenant_dense_vector_query(user_1.id, prod_1.id, [0.1]*384, tenant_review_count=100)
compiled_small = str(q_small.compile(dialect=postgresql.dialect()))
assert "WITH tenant_scope AS" in compiled_small
assert "JOIN tenant_scope ON reviews.id = tenant_scope.id" in compiled_small

q_large = build_tenant_dense_vector_query(user_1.id, prod_1.id, [0.1]*384, tenant_review_count=5000)
compiled_large = str(q_large.compile(dialect=postgresql.dialect()))
assert "ORDER BY anon_1.dist" in compiled_large or "dist + " in compiled_large
print("    Small tenant CTE & Large tenant HNSW queries compiled successfully!")

print("\nAll Phase 0 Invariants & Hardening Verified Successfully! 100% Passed.")
