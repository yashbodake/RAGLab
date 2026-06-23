import pytest
from backend.core.rrf import rrf_fuse
from backend.core.bm25 import BM25Result
from backend.models.schemas import ChunkResult

@pytest.mark.unit
def test_rrf_basic_fusion():
    """Two lists with overlapping docs produce correct fused scores."""
    dense = {
        "ids": [["doc1", "doc2"]],
        "documents": [["text1", "text2"]],
        "metadatas": [[{"product": "server"}, {"product": "router"}]],
        "distances": [[0.1, 0.4]] # similarity = 0.9, 0.6
    }
    sparse = [
        BM25Result(doc_id="doc2", text="text2", metadata={"product": "router"}, score=12.5),
        BM25Result(doc_id="doc3", text="text3", metadata={"product": "switch"}, score=8.2)
    ]
    
    fused = rrf_fuse(dense, sparse, k=60)
    
    # doc2 appears at rank 2 in dense, rank 1 in sparse
    # score(doc2) = 1/(60+2) + 1/(60+1) = 1/62 + 1/61 = 0.016129 + 0.016393 = 0.032522
    # doc1 appears at rank 1 in dense, absent in sparse
    # score(doc1) = 1/(60+1) = 1/61 = 0.016393
    # doc3 appears at rank 2 in sparse, absent in dense
    # score(doc3) = 1/(60+2) = 1/62 = 0.016129
    
    assert len(fused) == 3
    assert fused[0].id == "doc2"
    assert fused[0].scores.fused == pytest.approx(1/62 + 1/61, abs=1e-5)
    assert fused[1].id == "doc1"
    assert fused[1].scores.fused == pytest.approx(1/61, abs=1e-5)
    assert fused[2].id == "doc3"
    assert fused[2].scores.fused == pytest.approx(1/62, abs=1e-5)

@pytest.mark.unit
def test_rrf_disjoint_lists():
    """Non-overlapping results all appear in output."""
    dense = {
        "ids": [["doc1"]],
        "documents": [["text1"]],
        "metadatas": [[{"product": "server"}]],
        "distances": [[0.2]]
    }
    sparse = [
        BM25Result(doc_id="doc2", text="text2", metadata={"product": "router"}, score=5.0)
    ]
    fused = rrf_fuse(dense, sparse, k=60)
    assert len(fused) == 2
    assert {f.id for f in fused} == {"doc1", "doc2"}

@pytest.mark.unit
def test_rrf_single_list():
    """Single result set returns same ranking."""
    dense = {
        "ids": [["doc1", "doc2"]],
        "documents": [["text1", "text2"]],
        "metadatas": [[{"product": "server"}, {"product": "router"}]],
        "distances": [[0.1, 0.3]]
    }
    fused = rrf_fuse(dense, [], k=60)
    assert len(fused) == 2
    assert fused[0].id == "doc1"
    assert fused[1].id == "doc2"
