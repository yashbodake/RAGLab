import pytest

@pytest.mark.integration
def test_health_returns_200(app_client):
    """Health endpoint returns 200 with status 'healthy'."""
    response = app_client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert "chroma_collections" in data
    assert "docs_body" in data["chroma_collections"]
    assert "docs_title" in data["chroma_collections"]
    assert data["uptime_seconds"] >= 0.0
