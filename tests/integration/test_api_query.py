import json
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.integration
def test_query_validation_error(app_client):
    """Empty query returns 422 validation error."""
    response = app_client.post(
        "/query",
        json={"query": "", "features": {}}
    )
    assert response.status_code == 422

@pytest.mark.integration
@patch("backend.services.llm.LLMClient.stream_completion")
def test_query_returns_sse_stream(mock_stream, app_client):
    """POST /query returns text/event-stream with correct sequential events."""
    async def mock_generator(*args, **kwargs):
        yield "According "
        yield "to "
        yield "docs."
    mock_stream.side_effect = mock_generator

    response = app_client.post(
        "/query",
        json={
            "query": "E430 errors on switch",
            "features": {"hybrid": True, "metadata_aware": True},
            "compare_with_baseline": True
        }
    )
    
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"].lower()
    
    # Parse SSE events from response text
    lines = response.text.split("\n")
    events = []
    current_event = None
    for line in lines:
        if line.startswith("event:"):
            current_event = line.split(":", 1)[1].strip()
        elif line.startswith("data:") and current_event:
            data_json = json.loads(line.split(":", 1)[1].strip())
            events.append((current_event, data_json))
            current_event = None

    event_types = [e[0] for e in events]
    
    # Check correct order and presence of events
    assert "classification" in event_types
    assert "sources" in event_types
    assert "baseline_sources" in event_types
    assert "token" in event_types
    assert "metrics" in event_types
    assert "baseline_metrics" in event_types
    assert "logs" in event_types
    assert "done" in event_types
    
    # Check classification details
    clf_event = [e[1] for e in events if e[0] == "classification"][0]
    assert clf_event["type"] == "FACT" # <= 8 words, ends in ? -> FACT
    
    # Check sources presence
    sources_event = [e[1] for e in events if e[0] == "sources"][0]
    assert len(sources_event["chunks"]) > 0
    assert sources_event["chunks"][0]["metadata"]["product"] == "switch"
    assert sources_event["chunks"][0]["metadata"]["error_code"] == "E430"
