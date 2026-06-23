import sys
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import pytest
import chromadb
from backend.services.chroma_store import ChromaStore

@pytest.mark.unit
def test_chroma_store_initialization(tmp_path, embedding_service):
    """Verify that collections are created successfully."""
    store = ChromaStore(persist_path=str(tmp_path / "chroma_test"))
    store.initialize(embedding_service)
    
    body_col = store.get_collection("docs_body")
    title_col = store.get_collection("docs_title")
    
    assert isinstance(body_col, chromadb.Collection)
    assert isinstance(title_col, chromadb.Collection)
    assert body_col.name == "docs_body"
    assert title_col.name == "docs_title"

@pytest.mark.unit
def test_chroma_store_seeding(mock_chroma):
    """Verify database seeding has loaded articles and chunks."""
    stats = mock_chroma.get_stats()
    assert "docs_body" in stats
    assert "docs_title" in stats
    
    # We should have exactly 200 articles seeded (meaning docs_title count == 200)
    assert stats["docs_title"] == 200
    
    # For docs_body we should have chunks (which will be > 200, roughly 200 * 9 = 1800)
    assert stats["docs_body"] > 200

@pytest.mark.unit
def test_chroma_query(mock_chroma, embedding_service):
    """Verify querying works on seeded collections."""
    collection = mock_chroma.get_collection("docs_body")
    query_emb = embedding_service.encode(["power supply unit calibration"]).tolist()
    
    results = collection.query(
        query_embeddings=query_emb,
        n_results=3,
        include=["documents", "distances", "metadatas"]
    )
    
    assert "documents" in results
    assert len(results["documents"][0]) == 3
    assert len(results["distances"][0]) == 3
    assert len(results["metadatas"][0]) == 3
    
    # Check that metadata fields are correct
    metadata = results["metadatas"][0][0]
    assert "source" in metadata
    assert "product" in metadata
    assert "chunk_index" in metadata
    assert "article_id" in metadata
