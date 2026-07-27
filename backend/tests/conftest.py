"""
conftest.py — shared pytest fixtures for BrandGuard tests.

Uses an in-memory SQLite database for integration tests so no Docker
or running Postgres is required for the test suite.
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

import backend.app.models  # noqa: F401 — registers all model metadata


@pytest.fixture(name="engine")
def engine_fixture():
    """In-memory SQLite engine — fresh per test session."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="session")
def session_fixture(engine):
    """DB session scoped to each test."""
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(engine):
    """FastAPI TestClient with DB dependency overridden to use test SQLite engine."""
    from backend.app.db.session import get_session
    from backend.app.main import app

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
