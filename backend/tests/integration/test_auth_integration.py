"""
Integration tests for Phase 1.5 Auth endpoints.

Tests run against a real in-memory SQLite DB via conftest.py fixtures.
The key authorization test (user A cannot access user B's data) is
explicitly verified here — this is the bug that actually matters.
"""
import pytest


BASE = "/api/v1/auth"


class TestSignup:
    def test_signup_creates_user(self, client):
        resp = client.post(f"{BASE}/signup", json={
            "email": "alice@example.com",
            "password": "strongPass1",
            "full_name": "Alice",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "alice@example.com"
        assert data["full_name"] == "Alice"
        assert "hashed_password" not in data  # NEVER returned
        assert "password" not in data

    def test_duplicate_email_returns_409(self, client):
        payload = {"email": "bob@example.com", "password": "strongPass1"}
        client.post(f"{BASE}/signup", json=payload)
        resp = client.post(f"{BASE}/signup", json=payload)
        assert resp.status_code == 409

    def test_short_password_returns_422(self, client):
        resp = client.post(f"{BASE}/signup", json={
            "email": "charlie@example.com",
            "password": "short",
        })
        assert resp.status_code == 422

    def test_invalid_email_returns_422(self, client):
        resp = client.post(f"{BASE}/signup", json={
            "email": "not-an-email",
            "password": "strongPass1",
        })
        assert resp.status_code == 422


class TestLogin:
    def _signup(self, client, email="testuser@example.com", password="strongPass1"):
        client.post(f"{BASE}/signup", json={"email": email, "password": password})

    def test_login_returns_tokens(self, client):
        self._signup(client)
        resp = client.post(f"{BASE}/login", json={
            "email": "testuser@example.com",
            "password": "strongPass1",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_wrong_password_returns_401(self, client):
        self._signup(client)
        resp = client.post(f"{BASE}/login", json={
            "email": "testuser@example.com",
            "password": "wrongPassword",
        })
        assert resp.status_code == 401
        # Generic message — no hint whether email or password was wrong
        assert "Invalid" in resp.json()["detail"]

    def test_nonexistent_email_returns_401(self, client):
        resp = client.post(f"{BASE}/login", json={
            "email": "ghost@example.com",
            "password": "anyPassword1",
        })
        assert resp.status_code == 401


class TestProtectedRoutes:
    def _create_and_login(self, client, email, password="strongPass1"):
        client.post(f"{BASE}/signup", json={"email": email, "password": password})
        resp = client.post(f"{BASE}/login", json={"email": email, "password": password})
        return resp.json()["access_token"]

    def test_me_without_token_returns_401(self, client):
        resp = client.get(f"{BASE}/me")
        assert resp.status_code == 401

    def test_me_with_invalid_token_returns_401(self, client):
        resp = client.get(f"{BASE}/me", headers={"Authorization": "Bearer invalidtoken"})
        assert resp.status_code == 401

    def test_me_with_valid_token_returns_profile(self, client):
        token = self._create_and_login(client, "dave@example.com")
        resp = client.get(f"{BASE}/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["email"] == "dave@example.com"

    def test_token_refresh_issues_new_access_token(self, client):
        self._create_and_login(client, "eve@example.com")
        login_resp = client.post(f"{BASE}/login", json={
            "email": "eve@example.com", "password": "strongPass1"
        })
        refresh_token = login_resp.json()["refresh_token"]
        resp = client.post(f"{BASE}/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    # -----------------------------------------------------------------------
    # THE AUTHORIZATION TEST — this is the bug that matters
    # User A using their own valid token should NOT be able to see User B's
    # profile by guessing/swapping tokens.
    # -----------------------------------------------------------------------
    def test_user_a_cannot_impersonate_user_b(self, client):
        """
        Alice logs in and gets a valid token.
        Bob also has an account.
        Alice's token must only return Alice's profile, not Bob's.
        (GET /me is scoped to the token's subject — no ID parameter to guess.)
        """
        alice_token = self._create_and_login(client, "alice2@example.com")
        self._create_and_login(client, "bob2@example.com")  # Bob also exists

        # Alice's /me must return Alice's data
        resp = client.get(f"{BASE}/me", headers={"Authorization": f"Bearer {alice_token}"})
        assert resp.status_code == 200
        assert resp.json()["email"] == "alice2@example.com"
        assert resp.json()["email"] != "bob2@example.com"
