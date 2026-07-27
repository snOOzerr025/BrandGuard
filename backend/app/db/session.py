"""Database engine and session management."""
from sqlmodel import Session, SQLModel, create_engine

from backend.app.core.config import settings

engine = create_engine(
    settings.database_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)


def create_db_and_tables() -> None:
    """Create all tables defined in SQLModel metadata.

    Used for local dev / testing. Production uses Alembic migrations.
    """
    # Import all models so their metadata is registered before create_all
    import backend.app.models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency — yields a DB session per request."""
    with Session(engine) as session:
        yield session
