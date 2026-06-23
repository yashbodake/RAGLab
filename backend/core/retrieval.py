import re
import time
import httpx
import numpy as np
from typing import List, Dict, Optional, Any
from backend.core.config import settings
from backend.models.schemas import Classification, FeatureFlags, ChunkResult, ChunkScores
from backend.core.rrf import rrf_fuse
from backend.core.bm25 import BM25Result

PRODUCT_NAMES = {"server", "router", "switch", "gateway", "controller", "sensor", "actuator", "plc"}
SOURCE_TYPES = {"maintenance_manual", "troubleshooting_guide", "release_notes", "safety_bulletin", "installation_guide"}

def extract_metadata_filter(query: str) -> Optional[dict]:
    """
    Extract a Chroma-compatible 'where' filter from the query text.

    Returns:
        A Chroma 'where' dict, or None if no entities found.
    """
    filters = []
    query_lower = query.lower()

    # Extract error codes (e.g. E452, e305)
    error_codes = re.findall(r"[Ee]\d{3}", query)
    if error_codes:
        # Normalize to uppercase
        code = error_codes[0].upper()
        filters.append({"error_code": code})

    # Extract product names
    for product in PRODUCT_NAMES:
        if product in query_lower:
            filters.append({"product": product})
            break  # Take first match

    # Extract source types
    for source in SOURCE_TYPES:
        readable = source.replace("_", " ")
        if readable in query_lower:
            filters.append({"source": source})
            break

    if not filters:
        return None
    elif len(filters) == 1:
        return filters[0]
    else:
        return {"$and": filters}

def matches_filter(metadata: dict, where_filter: dict) -> bool:
    """Check if a metadata dict matches a Chroma 'where' filter dict."""
    if not where_filter:
        return True

    if "$and" in where_filter:
        return all(matches_filter(metadata, f) for f in where_filter["$and"])

    # Single field filter, e.g. {"product": "server"}
    for key, value in where_filter.items():
        if metadata.get(key) != value:
            return False

    return True

async def call_embed_endpoint(texts: List[str]) -> np.ndarray:
    """Call the local HTTP /embed endpoint to simulate a remote service call."""
    base_url = f"http://127.0.0.1:{settings.port}"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/embed",
            json={"texts": texts},
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()
        return np.array(data["embeddings"])

def parse_dense_results(dense_results: dict) -> List[ChunkResult]:
    """Convert Chroma dense query results dictionary into ChunkResult Pydantic models."""
    chunks = []
    if not dense_results or "ids" not in dense_results or not dense_results["ids"] or len(dense_results["ids"][0]) == 0:
        return chunks
    for rank, (doc_id, text, metadata, distance) in enumerate(
        zip(
            dense_results["ids"][0],
            dense_results["documents"][0],
            dense_results["metadatas"][0],
            dense_results["distances"][0],
        ),
        start=1
    ):
        chunks.append(
            ChunkResult(
                id=doc_id,
                text=text,
                metadata=metadata,
                scores=ChunkScores(
                    dense=float(1.0 - distance),
                    bm25=None,
                    fused=None
                ),
                rank=rank
            )
        )
    return chunks

def deduplicate_by_id(chunks: List[ChunkResult]) -> List[ChunkResult]:
    """Remove duplicate ChunkResult objects by keeping the first occurrence of each unique ID."""
    seen = set()
    deduped = []
    for c in chunks:
        if c.id not in seen:
            seen.add(c.id)
            deduped.append(c)
    return deduped

class RetrievalManager:
    """Orchestrates dense and sparse searches, filtering, and rank fusion."""

    def __init__(self, embedding_service, chroma_store, bm25_index, doc_store=None):
        self.embedding_service = embedding_service
        self.chroma_store = chroma_store
        self.bm25_index = bm25_index
        self.doc_store = doc_store

    async def retrieve(
        self,
        query: str,
        classification: Classification,
        features: FeatureFlags,
        log_buffer
    ) -> List[ChunkResult]:
        """
        Orchestrate complete retrieval pipeline.
        """
        top_k = classification.top_k
        queries = classification.sub_queries or [query]
        all_results: List[ChunkResult] = []

        # Get disabled document sources from store
        disabled_sources = set()
        if self.doc_store:
            disabled_sources = self.doc_store.get_disabled_sources()

        for q in queries:
            # Step 1: Encode query
            if features.remote_embed:
                log_buffer.append("embedding", f"Requesting remote embedding for: '{q}'", "info")
                start = time.monotonic()
                try:
                    # In case call_embed_endpoint fails, log error and fallback to local
                    embeddings = await call_embed_endpoint([q])
                    latency = (time.monotonic() - start) * 1000
                    log_buffer.append("embedding", f"Remote embed success: 1 text(s) in {latency:.1f}ms", "info")
                    embedding = embeddings[0]
                except Exception as e:
                    log_buffer.append("embedding", f"Remote embed failed ({e}), falling back to local model", "warn")
                    embedding = self.embedding_service.encode([q])[0]
            else:
                start = time.monotonic()
                embedding = self.embedding_service.encode([q])[0]
                latency = (time.monotonic() - start) * 1000
                log_buffer.append("embedding", f"Local embedding complete in {latency:.1f}ms", "debug")

            # Step 2: Select collection
            if features.multi_index and classification.type == "FACT":
                collection = self.chroma_store.get_collection("docs_title")
                log_buffer.append("retrieval", "Using docs_title index (FACT query)", "info")
            else:
                collection = self.chroma_store.get_collection("docs_body")
                log_buffer.append("retrieval", "Using docs_body index", "info")

            # Step 3: Build metadata filter
            where_filter = None
            if features.metadata_aware:
                where_filter = extract_metadata_filter(q)
                if where_filter:
                    log_buffer.append("metadata", f"Applied filter: {where_filter}", "info")

            # Step 4: Dense retrieval
            hnsw_params = None
            if features.hnsw:
                hnsw_params = {"search_ef": 100}
                log_buffer.append("hnsw", "HNSW search_ef=100 enabled", "info")

            # Execute Chroma Query
            start = time.monotonic()
            dense_results = collection.query(
                query_embeddings=[embedding.tolist()],
                n_results=30,  # Increased from 10 to ensure we have enough candidates post-filtering
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            dense_time = (time.monotonic() - start) * 1000
            
            # Metadata filter fallback: if 0 results, query again without filter
            if features.metadata_aware and where_filter and (not dense_results["ids"] or len(dense_results["ids"][0]) == 0):
                log_buffer.append("metadata", "Metadata filter returned 0 results. Falling back to unfiltered query.", "warn")
                dense_results = collection.query(
                    query_embeddings=[embedding.tolist()],
                    n_results=30,  # Increased from 10
                    where=None,
                    include=["documents", "metadatas", "distances"]
                )
            
            # Filter disabled docs from dense results
            filtered_dense = {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
            if dense_results and "ids" in dense_results and dense_results["ids"]:
                for doc_id, text, metadata, distance in zip(
                    dense_results["ids"][0],
                    dense_results["documents"][0],
                    dense_results["metadatas"][0],
                    dense_results["distances"][0]
                ):
                    if metadata.get("source") not in disabled_sources:
                        filtered_dense["ids"][0].append(doc_id)
                        filtered_dense["documents"][0].append(text)
                        filtered_dense["metadatas"][0].append(metadata)
                        filtered_dense["distances"][0].append(distance)
            dense_results = filtered_dense

            log_buffer.append("retrieval", f"Dense search: {len(dense_results['ids'][0]) if dense_results['ids'] else 0} candidates in {dense_time:.1f}ms", "info")

            # Step 5: Hybrid fusion (optional)
            if features.hybrid:
                start = time.monotonic()
                # Get BM25 top_n limit
                top_n = settings.bm25_top_n
                # Request extra candidates from BM25 to compensate for potential filtered documents
                sparse_results = self.bm25_index.search(q, top_n=max(30, top_n))
                sparse_time = (time.monotonic() - start) * 1000
                log_buffer.append("bm25", f"Sparse search: {len(sparse_results)} candidates in {sparse_time:.1f}ms", "info")

                # Filter out disabled docs from sparse results
                sparse_results = [r for r in sparse_results if r.metadata.get("source") not in disabled_sources]

                # Post-filter sparse results if metadata_aware is active
                if features.metadata_aware and where_filter:
                    filtered_sparse = [r for r in sparse_results if matches_filter(r.metadata, where_filter)]
                    # Fallback to unfiltered BM25 if filtered sparse matches 0 docs
                    if len(filtered_sparse) == 0 and len(sparse_results) > 0:
                        log_buffer.append("metadata", "Metadata post-filter returned 0 sparse results. Falling back to unfiltered sparse.", "warn")
                    else:
                        sparse_results = filtered_sparse
                    log_buffer.append("metadata", f"Post-filtered BM25 to {len(sparse_results)} results", "info")

                # Slice sparse results to top_n before RRF fusion
                sparse_results = sparse_results[:top_n]

                # Fuse using RRF
                fused = rrf_fuse(dense_results, sparse_results, k=settings.rrf_k)
                if fused:
                    log_buffer.append("rrf", f"RRF fusion: merged {len(fused)} unique → top {top_k}, best_score={fused[0].scores.fused:.3f}", "info")
                all_results.extend(fused[:top_k])
            else:
                chunks = parse_dense_results(dense_results)
                all_results.extend(chunks[:top_k])

        # Deduplicate if COMPARE produced overlapping results
        all_results = deduplicate_by_id(all_results)

        # Re-rank based on scores (fused score if present, else dense score)
        all_results.sort(key=lambda c: c.scores.fused if c.scores.fused is not None else c.scores.dense or 0.0, reverse=True)
        
        # Assign final positions
        for i, chunk in enumerate(all_results):
            chunk.rank = i + 1

        return all_results
