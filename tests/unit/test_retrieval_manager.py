import pytest
from backend.core.retrieval import RetrievalManager
from backend.models.schemas import Classification, FeatureFlags
from backend.services.log_buffer import LogBuffer

@pytest.fixture
def retrieval_manager(embedding_service, mock_chroma, bm25_index):
    """RetrievalManager instance initialized with test fixtures."""
    return RetrievalManager(
        embedding_service=embedding_service,
        chroma_store=mock_chroma,
        bm25_index=bm25_index
    )

@pytest.fixture
def log_buffer():
    """Fresh LogBuffer for tests."""
    buf = LogBuffer()
    buf.start_query()
    return buf

@pytest.mark.unit
@pytest.mark.asyncio
async def test_pipeline_dense_only(retrieval_manager, log_buffer):
    """All features off -> dense retrieval only, top_k=5 (default for no query understanding)."""
    clf = Classification(type="FACT", top_k=5)
    features = FeatureFlags(hybrid=False, metadata_aware=False)
    
    results = await retrieval_manager.retrieve(
        query="power supply calibration",
        classification=clf,
        features=features,
        log_buffer=log_buffer
    )
    
    assert len(results) <= 5
    assert all(r.scores.dense is not None for r in results)
    assert all(r.scores.bm25 is None for r in results)
    assert all(r.scores.fused is None for r in results)
    
    logs = log_buffer.flush_query_logs()
    assert any("Using docs_body index" in l.message for l in logs)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_pipeline_hybrid(retrieval_manager, log_buffer):
    """Hybrid on -> results include bm25 and fused scores."""
    clf = Classification(type="TOPIC", top_k=7)
    features = FeatureFlags(hybrid=True, metadata_aware=False)
    
    # We query with "server" as it is highly frequent
    results = await retrieval_manager.retrieve(
        query="server PSU",
        classification=clf,
        features=features,
        log_buffer=log_buffer
    )
    
    assert len(results) <= 7
    # Since hybrid is enabled, any result scored by both will have bm25/fused
    # We should have at least some fused results
    assert any(r.scores.fused is not None for r in results)
    
    logs = log_buffer.flush_query_logs()
    assert any("Sparse search:" in l.message for l in logs)
    assert any("RRF fusion:" in l.message for l in logs)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_pipeline_metadata_filtering(retrieval_manager, log_buffer):
    """metadata_aware on -> results matched to extracted query product."""
    clf = Classification(type="FACT", top_k=3)
    features = FeatureFlags(hybrid=False, metadata_aware=True)
    
    results = await retrieval_manager.retrieve(
        query="E430 errors on switch",
        classification=clf,
        features=features,
        log_buffer=log_buffer
    )
    
    # Check that all returned chunks match metadata constraints
    assert len(results) > 0
    for r in results:
        assert r.metadata.get("product") == "switch"
        assert r.metadata.get("error_code") == "E430"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_pipeline_multi_index_fact(retrieval_manager, log_buffer):
    """multi_index + FACT -> uses docs_title collection."""
    clf = Classification(type="FACT", top_k=3)
    features = FeatureFlags(multi_index=True)
    
    await retrieval_manager.retrieve(
        query="What is error E452?",
        classification=clf,
        features=features,
        log_buffer=log_buffer
    )
    
    logs = log_buffer.flush_query_logs()
    assert any("Using docs_title index (FACT query)" in l.message for l in logs)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_pipeline_multi_index_topic(retrieval_manager, log_buffer):
    """multi_index + TOPIC -> uses docs_body collection."""
    clf = Classification(type="TOPIC", top_k=5)
    features = FeatureFlags(multi_index=True)
    
    await retrieval_manager.retrieve(
        query="Explain power supply troubleshooting procedures",
        classification=clf,
        features=features,
        log_buffer=log_buffer
    )
    
    logs = log_buffer.flush_query_logs()
    assert any("Using docs_body index" in l.message for l in logs)
