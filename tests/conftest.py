"""
Root conftest.py — re-exports shared fixtures so pytest can run from project root.
"""
from backend.tests.conftest import client_fixture, engine_fixture, session_fixture

__all__ = ["engine_fixture", "session_fixture", "client_fixture"]
