import pytest
import json

@pytest.mark.integration
def test_document_lifecycle(app_client):
    """
    Test the full lifecycle of document ingestion, listing, active toggling,
    retrieval exclusion, and deletion.
    """
    # 1. Initially documents list should be empty (or list only custom uploaded files)
    response = app_client.get("/documents")
    assert response.status_code == 200
    docs = response.json()
    initial_count = len(docs)

    # 2. Upload a custom document
    file_content = b"Maintenance procedure: Use override key K999 to bypass valve safety lockouts."
    file_tuple = ("override_safety_lock.txt", file_content, "text/plain")
    
    upload_resp = app_client.post("/upload", files={"file": file_tuple})
    assert upload_resp.status_code == 200
    upload_data = upload_resp.json()
    assert upload_data["success"] is True
    
    # 3. Verify it is listed in the manager
    list_resp = app_client.get("/documents")
    assert list_resp.status_code == 200
    docs = list_resp.json()
    assert len(docs) == initial_count + 1
    
    # Find our uploaded doc
    doc = next((d for d in docs if d["filename"] == "override_safety_lock.txt"), None)
    assert doc is not None
    assert doc["status"] == "success"
    assert doc["active"] is True
    assert doc["chunk_count"] > 0
    doc_id = doc["id"]

    # 4. Search for the content (should be found)
    query_resp = app_client.post("/query", json={
        "query": "override key K999 safety",
        "features": {"hybrid": True}
    })
    assert query_resp.status_code == 200
    assert "override_safety_lock" in query_resp.text

    # 5. Toggle the document active status off (disable it)
    toggle_resp = app_client.post(f"/documents/{doc_id}/toggle")
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["active"] is False

    # 6. Verify listing reflects change
    list_resp = app_client.get("/documents")
    doc = next((d for d in list_resp.json() if d["id"] == doc_id), None)
    assert doc["active"] is False

    # 7. Search again (should be excluded!)
    query_resp2 = app_client.post("/query", json={
        "query": "override key K999 safety",
        "features": {"hybrid": True}
    })
    assert query_resp2.status_code == 200
    assert "override_safety_lock" not in query_resp2.text

    # 8. Toggle document active status back on (enable it)
    toggle_resp = app_client.post(f"/documents/{doc_id}/toggle")
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["active"] is True

    # 9. Search again (should be found again!)
    query_resp3 = app_client.post("/query", json={
        "query": "override key K999 safety",
        "features": {"hybrid": True}
    })
    assert query_resp3.status_code == 200
    assert "override_safety_lock" in query_resp3.text

    # 10. Delete the document
    delete_resp = app_client.delete(f"/documents/{doc_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["success"] is True

    # 11. Verify it is removed from list
    list_resp_final = app_client.get("/documents")
    docs_final = list_resp_final.json()
    assert len(docs_final) == initial_count
    assert not any(d["id"] == doc_id for d in docs_final)

    # 12. Search again (should not be found anymore)
    query_resp_final = app_client.post("/query", json={
        "query": "override key K999 safety",
        "features": {"hybrid": True}
    })
    assert query_resp_final.status_code == 200
    assert "override_safety_lock" not in query_resp_final.text
