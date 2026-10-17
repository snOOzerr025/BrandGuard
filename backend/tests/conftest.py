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
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import TSVECTOR
from backend.app.models.domain import Vector


@compiles(TSVECTOR, "sqlite")
def compile_tsvector_sqlite(type_, compiler, **kw):
    return "TEXT"


@compiles(Vector, "sqlite")
def compile_vector_sqlite(type_, compiler, **kw):
    return "TEXT"



@pytest.fixture(name="engine")
def engine_fixture():
    """
    In-memory SQLite engine — fresh per test session.

    Also patches backend.app.db.session.engine so that background tasks
    spawned by FastAPI (e.g. POST /analyze _run_pipeline) use the same
    test DB instead of trying to connect to Postgres.
    """
    import backend.app.db.session as db_session

    import sqlite3
    from sqlalchemy import event

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _sqlite_connect(dbapi_connection, connection_record):
        if isinstance(dbapi_connection, sqlite3.Connection):
            dbapi_connection.create_function("to_tsvector", 2, lambda lang, text: text or "", deterministic=True)

    SQLModel.metadata.create_all(engine)

    # Patch module-level engine so background tasks get the test DB
    original_engine = db_session.engine
    db_session.engine = engine

    yield engine

    db_session.engine = original_engine  # restore after test
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
