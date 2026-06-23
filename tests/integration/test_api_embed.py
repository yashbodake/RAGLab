import pytest

@pytest.mark.integration
def test_embed_returns_embeddings(app_client):
    """Valid request returns correct shape embeddings."""
    response = app_client.post(
        "/embed",
        json={"texts": ["How to fix error E430?", "Switch calibration"]}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["embeddings"]) == 2
    assert len(data["embeddings"][0]) == 384
    assert data["dimensions"] == 384
    assert data["model"] == "all-MiniLM-L6-v2"
    assert "latency_ms" in data

@pytest.mark.integration
def test_embed_validation_error(app_client):
    """Empty texts list fails validation."""
    response = app_client.post("/embed", json={"texts": []})
    assert response.status_code == 422 # FastAPI Pydantic validation error code
