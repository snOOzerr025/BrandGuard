"""
db/session.py — Database engine and session management.
------------------------------------------------------
Re-exports from backend.app.core.database for backward compatibility.
"""
from backend.app.core.database import (
    AsyncSessionLocal,
    SyncSessionLocal,
    async_engine,
    create_db_and_tables,
    engine,
    get_async_session,
    get_session,
    set_tenant_context,
)

__all__ = [
    "engine",
    "async_engine",
    "SyncSessionLocal",
    "AsyncSessionLocal",
    "get_session",
    "get_async_session",
    "create_db_and_tables",
    "set_tenant_context",
]
