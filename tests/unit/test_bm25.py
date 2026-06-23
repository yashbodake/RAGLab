import pytest
from backend.core.bm25 import BM25Index, BM25Result

@pytest.mark.unit
def test_bm25_build_index(sample_chunks):
    """Index builds without error and has correct size."""
    index = BM25Index()
    index.build(sample_chunks)
    assert len(index.doc_ids) == len(sample_chunks)
    assert len(index.doc_texts) == len(sample_chunks)
    assert len(index.doc_metadata) == len(sample_chunks)

@pytest.mark.unit
def test_bm25_search_returns_results(bm25_index):
    """Searching for known term returns matching docs."""
    # "calibration" or similar terms should exist in sample chunks since they are generated
    # Let's search for "the" or a common product name like "server"
    results = bm25_index.search("server", top_n=5)
    assert isinstance(results, list)
    for r in results:
        assert isinstance(r, BM25Result)
        assert r.score > 0
        assert "server" in r.text.lower() or "server" in r.metadata.get("product", "").lower()

@pytest.mark.unit
def test_bm25_search_exact_keyword(sample_chunks):
    """Error code 'E452' matches documents containing it."""
    # Build custom index with specific content
    custom_chunks = [
        {"id": "doc1", "text": "This is a safety manual about error E452 on servers.", "metadata": {"error_code": "E452"}},
        {"id": "doc2", "text": "No error codes listed here.", "metadata": {"error_code": None}},
        {"id": "doc3", "text": "Some general actuator troubleshooting guidelines.", "metadata": {"error_code": None}}
    ]
    index = BM25Index()
    index.build(custom_chunks)
    results = index.search("E452")
    assert len(results) == 1
    assert results[0].doc_id == "doc1"

@pytest.mark.unit
def test_bm25_search_no_match(bm25_index):
    """Gibberish query returns empty results."""
    results = bm25_index.search("xyzzyqwerasdf12345")
    assert len(results) == 0

@pytest.mark.unit
def test_bm25_search_top_n(bm25_index):
    """Results limited to top_n."""
    results = bm25_index.search("the", top_n=3)
    assert len(results) <= 3

@pytest.mark.unit
def test_bm25_tokenizer():
    """Tokenizer lowercases and removes punctuation."""
    tokens = BM25Index._tokenize("Error, E452: status normal!")
    assert tokens == ["error", "e452", "status", "normal"]
