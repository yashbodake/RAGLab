import pytest
import json
import os
import sys

# Ensure backend can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure CEREBRAS_API_KEY is mocked/set during test collection/execution
os.environ["CEREBRAS_API_KEY"] = "mock-key-for-testing"
os.environ["CHROMA_PERSIST_PATH"] = "./data/chroma_db_test"
os.environ["HF_HOME"] = "./data/huggingface_test"

@pytest.fixture(scope="session")
def sample_articles():
    """10 sample articles for fast testing."""
    fixture_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "fixtures",
        "sample_articles.json"
    )
    with open(fixture_path) as f:
        return json.load(f)

@pytest.fixture(scope="session")
def sample_chunks(sample_articles):
    """Pre-chunked documents from sample articles."""
    from backend.data.seed import chunk_article
    chunks = []
    for article in sample_articles:
        chunks.extend(chunk_article(article))
    return chunks

@pytest.fixture(scope="session")
def embedding_service():
    """Loaded embedding service."""
    # Ensure CEREBRAS_API_KEY is mocked/set so config loading doesn't crash on import
    os.environ["CEREBRAS_API_KEY"] = "mock-key-for-testing"
    from backend.services.embedding import EmbeddingService
    svc = EmbeddingService()
    svc.load()
    return svc

@pytest.fixture
def mock_chroma(tmp_path, sample_chunks, embedding_service):
    """In-memory Chroma instance seeded with sample data."""
    from backend.services.chroma_store import ChromaStore
    store = ChromaStore(persist_path=str(tmp_path / "chroma_test"))
    store.initialize(embedding_service)
    return store

@pytest.fixture
def bm25_index(sample_chunks):
    """BM25 index built from sample chunks."""
    from backend.core.bm25 import BM25Index
    index = BM25Index()
    index.build(sample_chunks)
    return index

@pytest.fixture
def feature_flags_all_off():
    """Feature flags with everything disabled."""
    from backend.models.schemas import FeatureFlags
    return FeatureFlags()

@pytest.fixture(scope="session")
def app_client():
    """FastAPI test client."""
    from fastapi.testclient import TestClient
    from backend.main import app
    with TestClient(app) as client:
        yield client
