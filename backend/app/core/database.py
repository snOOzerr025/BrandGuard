"""
core/database.py — Unified Database Engine and Multi-Tenant Session Management
-----------------------------------------------------------------------------
Provides:
- Sync engine & sessionmaker (SyncSessionLocal) for Celery workers & sync endpoints
- Async engine & sessionmaker (AsyncSessionLocal) for async RAG copilot retrieval
- Row-Level Security (RLS) tenant isolation helper: set_tenant_context()
- Automatic SQLite mock for to_tsvector() in tests
"""
import sqlite3
import uuid
from typing import Any, AsyncGenerator, Generator
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel

from backend.app.core.config import settings

# 1. Sync Engine
engine = create_engine(
    settings.database_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# SQLite test compatibility: register dummy to_tsvector function
@event.listens_for(engine, "connect")
def _sqlite_connect_hook(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        dbapi_connection.create_function("to_tsvector", 2, lambda lang, text: text or "", deterministic=True)

SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)


# 2. Async Engine (for RAG Hybrid Retrieval)
async_database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")

try:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    async_engine = create_async_engine(
        async_database_url,
        echo=settings.DEBUG,
        pool_pre_ping=True,
    )
    AsyncSessionLocal = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
except ImportError:
    async_engine = None  # type: ignore
    AsyncSessionLocal = None  # type: ignore


def set_tenant_context(session: Session, user_id: uuid.UUID) -> None:
    """
    Enforces defense-in-depth PostgreSQL Row-Level Security (RLS).
    Executes SET LOCAL app.current_user_id inside the transaction so that
    RLS policies isolate queries to the authenticated tenant even without
    explicit WHERE clauses.
    """
    if session.bind and session.bind.dialect.name == "postgresql":
        session.execute(text(f"SET LOCAL app.current_user_id = '{str(user_id)}'"))


async def set_async_tenant_context(session: Any, user_id: uuid.UUID) -> None:
    """Async variant for Row-Level Security setting inside transaction."""
    if session.bind and session.bind.dialect.name == "postgresql":
        await session.execute(text(f"SET LOCAL app.current_user_id = '{str(user_id)}'"))


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency — yields a scoped DB session per request."""
    with SyncSessionLocal() as session:
        yield session


async def get_async_session() -> AsyncGenerator[Any, None]:
    """FastAPI dependency — yields an async DB session for RAG endpoints."""
    if AsyncSessionLocal is None:
        raise RuntimeError("Async database driver (asyncpg) is not installed.")
    async with AsyncSessionLocal() as session:
        yield session


def create_db_and_tables() -> None:
    """Create all tables defined in SQLModel metadata (used for dev/testing)."""
    import backend.app.models  # noqa: F401
    SQLModel.metadata.create_all(engine)
