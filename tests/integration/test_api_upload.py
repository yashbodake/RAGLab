import pytest
from unittest.mock import patch
import json

@pytest.mark.integration
def test_upload_text_file(app_client):
    """Verify uploading a plain text file successfully parses and indexes it."""
    file_content = b"This is a custom user-uploaded maintenance log for switch model S500."
    file_tuple = ("switch_s500.txt", file_content, "text/plain")
    
    response = app_client.post("/upload", files={"file": file_tuple})
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == "switch_s500.txt"
    assert data["chunks_added"] > 0
    
    # Query for the newly ingested text content
    query_response = app_client.post("/query", json={
        "query": "switch model S500",
        "features": {
            "hybrid": True
        }
    })
    assert query_response.status_code == 200
    stream_content = query_response.text
    assert "switch_s500" in stream_content

@pytest.mark.integration
def test_upload_json_file(app_client):
    """Verify uploading a valid JSON file parses and indexes it."""
    articles = [
        {
            "title": "Error E888 Warning",
            "body": "Error E888 indicates a thermal overload in generator G300.",
            "metadata": {
                "source": "manual",
                "product": "generator",
                "error_code": "E888"
            }
        }
    ]
    file_content = json.dumps(articles).encode("utf-8")
    file_tuple = ("generator_warning.json", file_content, "application/json")
    
    response = app_client.post("/upload", files={"file": file_tuple})
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == "generator_warning.json"
    assert data["chunks_added"] == 1
    
    # Query for the new error code
    query_response = app_client.post("/query", json={
        "query": "generator G300 overload E888",
        "features": {
            "metadata_aware": True
        }
    })
    assert query_response.status_code == 200
    assert "E888" in query_response.text

@pytest.mark.integration
@patch("pymupdf4llm.to_markdown")
def test_upload_pdf_file(mock_to_markdown, app_client):
    """Verify uploading a PDF file extracts markdown and indexes it."""
    # Mock pymupdf4llm to avoid C dependencies in standard light unit tests
    mock_to_markdown.return_value = "# Maintenance PDF\nEnsure valve V100 is closed before calibration."
    
    file_content = b"%PDF-1.4 mock pdf data"
    file_tuple = ("calibration_proc.pdf", file_content, "application/pdf")
    
    response = app_client.post("/upload", files={"file": file_tuple})
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == "calibration_proc.pdf"
    assert data["chunks_added"] > 0
    mock_to_markdown.assert_called_once()
    
    # Query for PDF content
    query_response = app_client.post("/query", json={
        "query": "valve V100 calibration",
        "features": {}
    })
    assert query_response.status_code == 200
    assert "calibration_proc" in query_response.text

@pytest.mark.integration
def test_upload_oversized_file(app_client):
    """Verify files over 5MB are rejected."""
    large_content = b"a" * (5 * 1024 * 1024 + 10)
    file_tuple = ("large.txt", large_content, "text/plain")
    
    response = app_client.post("/upload", files={"file": file_tuple})
    assert response.status_code == 400
    assert "exceeds" in response.json()["detail"]

@pytest.mark.integration
def test_upload_invalid_extension(app_client):
    """Verify unsupported extensions are rejected."""
    file_content = b"fake image bytes"
    file_tuple = ("diagram.png", file_content, "image/png")
    
    response = app_client.post("/upload", files={"file": file_tuple})
    assert response.status_code == 400
    assert "Unsupported" in response.json()["detail"]

@pytest.mark.integration
def test_upload_malformed_json(app_client):
    """Verify malformed JSON is rejected with 400."""
    file_content = b"{invalid json}"
    file_tuple = ("bad.json", file_content, "application/json")
    
    response = app_client.post("/upload", files={"file": file_tuple})
    assert response.status_code == 400
    assert "Invalid JSON" in response.json()["detail"]
