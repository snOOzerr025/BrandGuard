"""
auth/router.py
--------------
FastAPI router for auth endpoints:
  POST /auth/signup   — create a new account
  POST /auth/login    — exchange email+password for JWT pair
  POST /auth/refresh  — exchange a refresh token for a new access token
  GET  /auth/me       — return the current user's profile

Security invariants:
- Passwords are hashed with bcrypt before being stored (security.py handles this)
- Passwords are NEVER returned in any response
- Login errors use a generic message to prevent email enumeration
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
    UserRead,
)
from backend.app.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from backend.app.db.session import get_session
from backend.app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, session: Session = Depends(get_session)) -> User:
    """Create a new user account.

    Returns the created user profile (no password fields).
    Raises 409 if email is already registered.
    """
    existing = session.exec(select(User).where(User.email == payload.email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: Session = Depends(get_session)) -> TokenResponse:
    """Authenticate with email + password and receive an access + refresh token pair.

    Uses a generic error message for both "user not found" and "wrong password"
    to prevent email enumeration attacks.
    """
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
    )

    user = session.exec(select(User).where(User.email == payload.email)).first()
    if not user or not user.is_active:
        raise invalid_credentials

    if not verify_password(payload.password, user.hashed_password):
        raise invalid_credentials

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, session: Session = Depends(get_session)) -> TokenResponse:
    """Exchange a valid refresh token for a new access + refresh token pair."""
    user_id_str = decode_token(payload.refresh_token, expected_type="refresh")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    import uuid
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed token.")

    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    """Return the authenticated user's profile."""
    return current_user
