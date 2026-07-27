"""
auth/dependencies.py
--------------------
FastAPI dependency: get_current_user

Injected into every route that touches user-owned data.
Returns the authenticated User or raises HTTP 401.
"""
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from backend.app.auth.security import decode_token
from backend.app.db.session import get_session
from backend.app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> User:
    """Extract and validate the JWT from Authorization: Bearer <token>.

    Raises HTTP 401 if:
    - No token is provided
    - Token is invalid or expired
    - Token type is not 'access'
    - User is not found or is inactive
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    user_id_str = decode_token(credentials.credentials, expected_type="access")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    user = session.exec(select(User).where(User.id == user_id)).first()
    if user is None or not user.is_active:
        raise credentials_exception

    return user
