"""
tests/db/test_pgvector_isolation.py
-----------------------------------
Root-level test runner for Phase 0 pgvector isolation.
Re-exports and runs tests from backend.tests.unit.test_pgvector_isolation.
"""
from backend.tests.unit.test_pgvector_isolation import (
    test_large_tenant_query_structure,
    test_models_instantiation_and_fields,
    test_multi_tenant_isolation_in_db,
    test_sentiment_result_attributes_and_aliases,
    test_small_tenant_query_structure,
)

__all__ = [
    "test_models_instantiation_and_fields",
    "test_small_tenant_query_structure",
    "test_large_tenant_query_structure",
    "test_multi_tenant_isolation_in_db",
    "test_sentiment_result_attributes_and_aliases",
]
