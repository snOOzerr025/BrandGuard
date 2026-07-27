"""
auth/security.py
----------------
Password hashing and JWT token utilities.

Rules enforced:
- Passwords are ALWAYS hashed with bcrypt before storage. Never stored in plaintext.
- Passwords are NEVER logged, even partially.
- JWTs carry only user_id (UUID) as subject — no role/permission claims yet (v1 is single-user auth).
- Access tokens expire in 30 min; refresh tokens in 7 days.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from backend.app.core.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def hash_password(plain_password: str) -> str:
    """Return bcrypt hash of the plaintext password (max 72 bytes enforced by bcrypt)."""
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if plain_password matches the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def _create_token(subject: str, expires_delta: timedelta, token_type: str) -> str:
    """Internal: create a signed JWT with given expiry."""
    expire = datetime.now(tz=timezone.utc) + expires_delta
    payload = {
        "sub": subject,       # user UUID as string
        "type": token_type,   # "access" | "refresh"
        "exp": expire,
        "iat": datetime.now(tz=timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(user_id: str) -> str:
    """Create a short-lived access token for the given user UUID."""
    return _create_token(
        subject=user_id,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access",
    )


def create_refresh_token(user_id: str) -> str:
    """Create a long-lived refresh token for the given user UUID."""
    return _create_token(
        subject=user_id,
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh",
    )


def decode_token(token: str, expected_type: str = "access") -> Optional[str]:
    """Decode and validate a JWT. Returns the user_id (sub) or None on failure.

    Returns None (not raises) so callers can decide how to handle.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != expected_type:
            return None
        return payload.get("sub")
    except JWTError:
        return None
