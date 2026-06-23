from backend.models.schemas import ChunkResult, ChunkScores
from backend.core.bm25 import BM25Result

def rrf_fuse(
    dense_results: dict,
    sparse_results: list[BM25Result],
    k: int = 60
) -> list[ChunkResult]:
    """
    Fuse dense (Chroma) and sparse (BM25) results using
    Reciprocal Rank Fusion.

    Args:
        dense_results: Chroma query output dict (ids, documents, metadatas, distances).
        sparse_results: BM25 ranked results.
        k: RRF constant (default 60).

    Returns:
        List of ChunkResult sorted by fused score descending.
    """
    scores: dict[str, float] = {}
    chunk_data: dict[str, dict] = {}

    # Score dense results
    has_dense = (
        dense_results and
        "ids" in dense_results and
        dense_results["ids"] and
        len(dense_results["ids"][0]) > 0
    )

    if has_dense:
        for rank, (doc_id, text, metadata, distance) in enumerate(
            zip(
                dense_results["ids"][0],
                dense_results["documents"][0],
                dense_results["metadatas"][0],
                dense_results["distances"][0],
            ),
            start=1,
        ):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
            chunk_data[doc_id] = {
                "text": text,
                "metadata": metadata,
                "dense_score": float(1.0 - distance),
                "dense_rank": rank,
            }

    # Score sparse results
    if sparse_results:
        for rank, bm25_result in enumerate(sparse_results, start=1):
            doc_id = bm25_result.doc_id
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
            if doc_id not in chunk_data:
                chunk_data[doc_id] = {
                    "text": bm25_result.text,
                    "metadata": bm25_result.metadata,
                    "dense_score": None,
                    "dense_rank": None,
                }
            chunk_data[doc_id]["bm25_score"] = float(bm25_result.score)
            chunk_data[doc_id]["bm25_rank"] = rank

    # Build fused results
    fused = []
    for doc_id, fused_score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        data = chunk_data[doc_id]
        fused.append(
            ChunkResult(
                id=doc_id,
                text=data["text"],
                metadata=data["metadata"],
                scores=ChunkScores(
                    dense=data.get("dense_score"),
                    bm25=data.get("bm25_score"),
                    fused=float(fused_score),
                ),
                rank=0, # Set by RetrievalManager or caller
            )
        )

    return fused
