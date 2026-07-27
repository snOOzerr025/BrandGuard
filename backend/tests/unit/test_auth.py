"""
Unit tests for Phase 1.5 Auth — security utilities.

Tests the core cryptographic functions in isolation (no DB required).
These are the functions where bugs actually matter: a wrong verify_password
or a decode that accepts expired tokens would be a real security failure.
"""
import time

import pytest

from backend.app.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    """bcrypt password hashing is correct and one-way."""

    def test_hash_is_not_plaintext(self):
        hashed = hash_password("mySecret123")
        assert hashed != "mySecret123"
        assert len(hashed) > 20  # bcrypt hashes are long

    def test_correct_password_verifies(self):
        hashed = hash_password("correctHorse")
        assert verify_password("correctHorse", hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("correctHorse")
        assert verify_password("wrongPassword", hashed) is False

    def test_unicode_password_hashes_safely(self):
        # Should not raise — unicode passwords are utf-8 encoded
        hashed = hash_password("pässwörд123")
        assert verify_password("pässwörд123", hashed) is True

    def test_same_password_produces_different_hashes(self):
        # bcrypt uses random salt per call
        h1 = hash_password("samePassword")
        h2 = hash_password("samePassword")
        assert h1 != h2
        # But both verify correctly
        assert verify_password("samePassword", h1) is True
        assert verify_password("samePassword", h2) is True


class TestJWTTokens:
    """JWT creation and decode round-trips work correctly."""

    def test_access_token_encodes_user_id(self):
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = create_access_token(user_id)
        decoded = decode_token(token, expected_type="access")
        assert decoded == user_id

    def test_refresh_token_encodes_user_id(self):
        user_id = "550e8400-e29b-41d4-a716-446655440001"
        token = create_refresh_token(user_id)
        decoded = decode_token(token, expected_type="refresh")
        assert decoded == user_id

    def test_access_token_rejected_as_refresh(self):
        """An access token must NOT be accepted as a refresh token."""
        token = create_access_token("some-user-id")
        result = decode_token(token, expected_type="refresh")
        assert result is None

    def test_refresh_token_rejected_as_access(self):
        """A refresh token must NOT be accepted as an access token."""
        token = create_refresh_token("some-user-id")
        result = decode_token(token, expected_type="access")
        assert result is None

    def test_tampered_token_rejected(self):
        token = create_access_token("user-123")
        tampered = token[:-5] + "XXXXX"  # corrupt the signature
        result = decode_token(tampered, expected_type="access")
        assert result is None

    def test_garbage_string_rejected(self):
        result = decode_token("not.a.jwt", expected_type="access")
        assert result is None

    def test_empty_string_rejected(self):
        result = decode_token("", expected_type="access")
        assert result is None


class TestAuthSchemas:
    """Pydantic auth schema validation."""

    def test_short_password_rejected(self):
        from pydantic import ValidationError
        from backend.app.auth.schemas import SignupRequest
        with pytest.raises(ValidationError):
            SignupRequest(email="test@example.com", password="short")

    def test_valid_signup_passes(self):
        from backend.app.auth.schemas import SignupRequest
        req = SignupRequest(email="user@example.com", password="strongPass1")
        assert req.email == "user@example.com"

    def test_invalid_email_rejected(self):
        from pydantic import ValidationError
        from backend.app.auth.schemas import SignupRequest
        with pytest.raises(ValidationError):
            SignupRequest(email="not-an-email", password="strongPass1")
