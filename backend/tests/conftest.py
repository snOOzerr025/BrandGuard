import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture(scope="module")
def client():
    """Module-scoped FastAPI TestClient fixture"""
    with TestClient(app) as test_client:
        yield test_client
