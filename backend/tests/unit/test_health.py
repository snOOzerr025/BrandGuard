def test_health_check_endpoint(client):
    """Verify that the /health endpoint is accessible and returns expected status"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert "environment" in data
    assert "debug" in data
