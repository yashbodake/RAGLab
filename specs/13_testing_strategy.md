# Testing Strategy

## Philosophy

Every spec has a corresponding test. Tests are the executable version of the specification. If a spec says "QueryRouter classifies queries with ≤8 words ending in `?` as FACT," there must be a test that asserts exactly that.

## Test Structure

```
tests/
├── unit/
│   ├── test_query_router.py
│   ├── test_retrieval_manager.py
│   ├── test_rrf.py
│   ├── test_bm25.py
│   ├── test_metadata_filter.py
│   ├── test_embedding_service.py
│   ├── test_llm_client.py
│   ├── test_chroma_store.py
│   ├── test_log_buffer.py
│   ├── test_schemas.py
│   └── test_config.py
├── integration/
│   ├── test_api_query.py
│   ├── test_api_embed.py
│   ├── test_api_health.py
│   ├── test_retrieval_pipeline.py
│   └── test_sse_streaming.py
├── e2e/
│   └── test_full_query_flow.py
├── fixtures/
│   ├── sample_articles.json       # 10 articles for fast tests
│   ├── sample_chunks.json         # Pre-chunked from sample articles
│   └── sample_embeddings.npy      # Pre-computed embeddings for sample chunks
├── conftest.py                    # Shared fixtures
└── pytest.ini
```

## Coverage Targets

| Layer | Target | Rationale |
|-------|--------|-----------|
| Unit tests | 90% line coverage | Core logic must be thoroughly tested |
| Integration tests | 80% endpoint coverage | All API endpoints and SSE events tested |
| E2E tests | Key user flows | Happy path + error paths |

## Test Configuration

### `pytest.ini`
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
markers =
    unit: Unit tests (fast, no external deps)
    integration: Integration tests (need running services)
    e2e: End-to-end tests (full stack)
    slow: Tests that take >5s
asyncio_mode = auto
```

### `conftest.py` (Key Fixtures)
```python
import pytest
import json
import numpy as np

@pytest.fixture
def sample_articles():
    """10 sample articles for fast testing."""
    with open("tests/fixtures/sample_articles.json") as f:
        return json.load(f)

@pytest.fixture
def sample_chunks(sample_articles):
    """Pre-chunked documents from sample articles."""
    from backend.data.seed import chunk_article
    chunks = []
    for article in sample_articles:
        chunks.extend(chunk_article(article))
    return chunks

@pytest.fixture
def embedding_service():
    """Loaded embedding service (cached across test session)."""
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

@pytest.fixture
def feature_flags_all_on():
    """Feature flags with everything enabled."""
    from backend.models.schemas import FeatureFlags
    return FeatureFlags(
        hybrid=True, remote_embed=True, query_understanding=True,
        metadata_aware=True, multi_index=True, hnsw=True, stream_sources=True,
    )

@pytest.fixture
def app_client():
    """FastAPI test client."""
    from fastapi.testclient import TestClient
    from backend.main import app
    return TestClient(app)
```

---

## Unit Tests

### `test_query_router.py`
Spec reference: `05_retrieval_pipeline.md` → QueryRouter

```python
# Tests to implement:

def test_classify_fact_short_question():
    """≤8 words ending with '?' → FACT, top_k=3."""

def test_classify_topic_long_question():
    """Long queries without compare keywords → TOPIC, top_k=7."""

def test_classify_compare_vs():
    """Query containing 'vs' → COMPARE with sub_queries."""

def test_classify_compare_difference_between():
    """Query with 'difference between' → COMPARE."""

def test_classify_query_understanding_off():
    """When query_understanding=False → always FACT, top_k=5."""

def test_extract_compare_entities():
    """'X vs Y' → ['X', 'Y']."""

def test_extract_compare_entities_no_split():
    """Query with compare keyword but no clear split → single query."""
```

### `test_rrf.py`
Spec reference: `05_retrieval_pipeline.md` → RRF

```python
def test_rrf_basic_fusion():
    """Two lists with overlapping docs produce correct fused scores."""

def test_rrf_score_formula():
    """Verify RRF score = sum(1/(k+rank)) for k=60."""

def test_rrf_disjoint_lists():
    """Non-overlapping results all appear in output."""

def test_rrf_single_list():
    """Single result set returns same ranking."""

def test_rrf_ordering():
    """Output is sorted by fused_score descending."""
```

### `test_bm25.py`
Spec reference: `05_retrieval_pipeline.md` → BM25

```python
def test_bm25_build_index():
    """Index builds without error and has correct size."""

def test_bm25_search_returns_results():
    """Searching for known term returns matching docs."""

def test_bm25_search_exact_keyword():
    """Error code 'E452' matches documents containing it."""

def test_bm25_search_no_match():
    """Gibberish query returns empty results."""

def test_bm25_search_top_n():
    """Results limited to top_n."""

def test_bm25_tokenizer():
    """Tokenizer lowercases and removes punctuation."""
```

### `test_metadata_filter.py`
Spec reference: `05_retrieval_pipeline.md` → Metadata Filter Extraction

```python
def test_extract_error_code():
    """'Fix E452' → {'error_code': 'E452'}."""

def test_extract_product():
    """'server troubleshooting' → {'product': 'server'}."""

def test_extract_combined():
    """'E452 on server' → {'$and': [{'error_code':'E452'}, {'product':'server'}]}."""

def test_extract_no_entities():
    """Generic query → None."""

def test_extract_lowercase_error_code():
    """'e452' normalized to 'E452'."""
```

### `test_embedding_service.py`
Spec reference: `07_embedding_service.md`

```python
def test_encode_single_text():
    """Single text returns shape (1, 384)."""

def test_encode_batch():
    """Batch of N texts returns shape (N, 384)."""

def test_encode_normalized():
    """Output vectors have unit L2 norm."""

def test_encode_deterministic():
    """Same text produces same embedding."""

def test_encode_without_load_raises():
    """Calling encode before load raises RuntimeError."""
```

### `test_log_buffer.py`
Spec reference: `05_retrieval_pipeline.md` → Pipeline Logging

```python
def test_append_and_flush():
    """Appended entries are returned by flush_query_logs."""

def test_flush_clears_query_logs():
    """After flush, query logs are empty."""

def test_ring_buffer_max_size():
    """Buffer does not exceed max_size."""

def test_start_query_resets():
    """start_query clears per-query logs."""
```

### `test_schemas.py`
Spec reference: `04_backend_api.md`

```python
def test_query_request_valid():
    """Valid request body passes validation."""

def test_query_request_empty_query():
    """Empty query string fails validation."""

def test_query_request_query_too_long():
    """Query > 2000 chars fails validation."""

def test_feature_flags_defaults():
    """All flags default to False."""

def test_embed_request_valid():
    """Valid embed request passes."""

def test_embed_request_empty_texts():
    """Empty texts list fails validation."""

def test_embed_request_too_many_texts():
    """More than 32 texts fails validation."""
```

---

## Integration Tests

### `test_api_query.py`
Spec reference: `04_backend_api.md` → POST /query

```python
def test_query_returns_sse_stream():
    """POST /query returns text/event-stream content type."""

def test_query_sse_event_order():
    """Events arrive in order: classification → sources → token(s) → metrics → logs → done."""

def test_query_with_baseline_comparison():
    """compare_with_baseline=True produces baseline_sources and baseline_metrics events."""

def test_query_validation_error():
    """Empty query returns 400."""

def test_query_rate_limit():
    """11th request in 1 minute returns 429."""

def test_query_stream_sources_early():
    """stream_sources=True sends sources before first token."""
```

### `test_api_embed.py`
Spec reference: `04_backend_api.md` → POST /embed

```python
def test_embed_returns_embeddings():
    """Valid request returns correct shape embeddings."""

def test_embed_dimensions():
    """Response dimensions field is 384."""

def test_embed_matches_local():
    """Remote embed result matches local EmbeddingService.encode()."""
```

### `test_api_health.py`
Spec reference: `04_backend_api.md` → GET /health

```python
def test_health_returns_200():
    """Health endpoint returns 200 with status 'healthy'."""

def test_health_includes_collection_counts():
    """Response includes chroma_collections with counts."""
```

### `test_retrieval_pipeline.py`
Spec reference: `05_retrieval_pipeline.md`

```python
def test_pipeline_dense_only():
    """All features off → dense retrieval only."""

def test_pipeline_hybrid():
    """Hybrid on → results include bm25_score and fused_score."""

def test_pipeline_metadata_filtering():
    """metadata_aware on → all results match extracted metadata."""

def test_pipeline_multi_index_fact():
    """multi_index + FACT → uses docs_title collection."""

def test_pipeline_multi_index_topic():
    """multi_index + TOPIC → uses docs_body collection."""
```

---

## E2E Tests

### `test_full_query_flow.py`

```python
def test_full_query_happy_path():
    """
    1. Send a query with features enabled.
    2. Receive SSE stream.
    3. Verify classification, sources, tokens, metrics, logs, done events.
    4. Verify metrics contain retrieval_time_ms and generation_time_ms.
    """

def test_full_query_all_features_off():
    """Baseline query with no features produces valid results."""

def test_full_query_comparison_mode():
    """Comparison mode returns both enhanced and baseline results."""
```

---

## Running Tests

```bash
# All tests
pytest

# Unit tests only (fast, ~5s)
pytest -m unit

# Integration tests (need model loaded, ~30s)
pytest -m integration

# With coverage report
pytest --cov=backend --cov-report=html

# Single test file
pytest tests/unit/test_query_router.py -v
```

## CI Pipeline

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest -m "unit" --cov=backend --cov-fail-under=90
```

### `requirements-dev.txt`
```
pytest==8.2.0
pytest-asyncio==0.23.0
pytest-cov==5.0.0
httpx==0.27.0
```
