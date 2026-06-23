# Retrieval Pipeline Specification

## Core Modules

### QueryRouter
Classifies query into **FACT**, **TOPIC**, or **COMPARE**.
- COMPARE: regex `difference between|vs\.?|compare|comparison` → split entities, create two sub‑queries.
- FACT: word count ≤8 and ends with `?` → top‑k=3.
- TOPIC: everything else → top‑k=7.
When `query_understanding` is off, defaults to FACT with top‑k=5.

**Classification Logic (pseudocode):**
```python
def classify(query: str, query_understanding: bool) -> Classification:
    if not query_understanding:
        return Classification(type="FACT", top_k=5, sub_queries=None)

    query_lower = query.lower().strip()

    # Check COMPARE first (most specific)
    compare_pattern = r"difference between|vs\.?|compare|comparison"
    if re.search(compare_pattern, query_lower):
        # Extract entities around the compare keyword
        entities = extract_compare_entities(query_lower)
        sub_queries = [f"{entity.strip()}" for entity in entities]
        return Classification(type="COMPARE", top_k=5, sub_queries=sub_queries)

    # Check FACT: short question
    word_count = len(query_lower.split())
    if word_count <= 8 and query_lower.endswith("?"):
        return Classification(type="FACT", top_k=3, sub_queries=None)

    # Default: TOPIC
    return Classification(type="TOPIC", top_k=7, sub_queries=None)

def extract_compare_entities(query: str) -> list[str]:
    """Split query around comparison keywords to find the two entities."""
    split_patterns = [" vs.? ", " versus ", " compared to ", " difference between "]
    for pattern in split_patterns:
        parts = re.split(pattern, query, maxsplit=1)
        if len(parts) == 2:
            return [parts[0].strip(), parts[1].strip()]
    # Fallback: treat as single query
    return [query]
```

**Output Schema:**
```python
class Classification(BaseModel):
    type: Literal["FACT", "TOPIC", "COMPARE"]
    top_k: int
    sub_queries: list[str] | None = None
```

---

### RetrievalManager
Orchestrates retrieval:
1. **Select collection**: `multi_index` and FACT → `docs_title`, else `docs_body`.
2. **Dense retrieval baseline**: Chroma `.query()` with `n_results=10`.
3. **Hybrid** (if `hybrid` flag on):
   - BM25 on chunk corpus (pre‑built index) → top‑10.
   - RRF fusion (k=60) of dense + BM25 results, take top‑k.
   - If off, use dense results directly.
4. **Metadata filtering** (if `metadata_aware`):
   - Extract entities (error codes like `E\d{3}`, product names) via regex.
   - Apply Chroma `where` filter; BM25 results post‑filtered to matching metadata.
5. **Remote embedding** (if `remote_embed`): calls internal `/embed` endpoint instead of local encode; logs latency.
All steps are logged.

**Full Orchestration (pseudocode):**
```python
async def retrieve(
    query: str,
    classification: Classification,
    features: FeatureFlags,
    log_buffer: LogBuffer
) -> list[ChunkResult]:

    top_k = classification.top_k
    queries = classification.sub_queries or [query]
    all_results = []

    for q in queries:
        # Step 1: Encode query
        if features.remote_embed:
            log_buffer.append("embedding", "Using remote embedding endpoint", "info")
            start = time.monotonic()
            embedding = await call_embed_endpoint([q])
            latency = (time.monotonic() - start) * 1000
            log_buffer.append("embedding", f"Remote embed latency: {latency:.1f}ms", "info")
        else:
            embedding = embedding_service.encode([q])
            log_buffer.append("embedding", "Local embedding complete", "debug")

        # Step 2: Select collection
        if features.multi_index and classification.type == "FACT":
            collection = chroma_store.get_collection("docs_title")
            log_buffer.append("retrieval", "Using docs_title index (FACT query)", "info")
        else:
            collection = chroma_store.get_collection("docs_body")
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

        start = time.monotonic()
        dense_results = collection.query(
            query_embeddings=embedding.tolist(),
            n_results=10,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        dense_time = (time.monotonic() - start) * 1000
        log_buffer.append("retrieval", f"Dense search: {len(dense_results['ids'][0])} candidates in {dense_time:.1f}ms", "info")

        # Step 5: Hybrid fusion (optional)
        if features.hybrid:
            start = time.monotonic()
            sparse_results = bm25_index.search(q, top_n=10)
            sparse_time = (time.monotonic() - start) * 1000
            log_buffer.append("bm25", f"Sparse search: {len(sparse_results)} candidates in {sparse_time:.1f}ms", "info")

            # Post-filter sparse results if metadata_aware
            if features.metadata_aware and where_filter:
                sparse_results = [r for r in sparse_results if matches_filter(r.metadata, where_filter)]
                log_buffer.append("metadata", f"Post-filtered BM25 to {len(sparse_results)} results", "info")

            fused = rrf_fuse(dense_results, sparse_results, k=60)
            log_buffer.append("rrf", f"RRF fusion: merged {len(fused)} unique → top {top_k}, best_score={fused[0].fused_score:.3f}", "info")
            all_results.extend(fused[:top_k])
        else:
            # Convert dense results to ChunkResult objects
            chunks = parse_dense_results(dense_results)
            all_results.extend(chunks[:top_k])

    # Deduplicate if COMPARE produced overlapping results
    all_results = deduplicate_by_id(all_results)

    # Re-rank and assign final positions
    all_results.sort(key=lambda c: c.fused_score or c.dense_score, reverse=True)
    for i, chunk in enumerate(all_results):
        chunk.rank = i + 1

    return all_results
```

---

### RRF (Reciprocal Rank Fusion)

Combines ranked lists from multiple retrieval methods into a single fused ranking.

**Formula:**
```
RRF_score(d) = Σ  1 / (k + rank_i(d))
               i
```
Where:
- `d` is a document (chunk)
- `k` is a constant (default: 60) that mitigates the impact of high rankings
- `rank_i(d)` is the rank of document `d` in ranked list `i` (1-indexed)
- The sum is over all ranked lists that contain `d`

**Implementation:**
```python
def rrf_fuse(
    dense_results: ChromaQueryResult,
    sparse_results: list[BM25Result],
    k: int = 60
) -> list[ChunkResult]:
    """
    Fuse dense (Chroma) and sparse (BM25) results using
    Reciprocal Rank Fusion.

    Args:
        dense_results: Chroma query output (ids, documents, metadatas, distances).
        sparse_results: BM25 ranked results with scores.
        k: RRF constant (default 60).

    Returns:
        List of ChunkResult sorted by fused score descending.
    """
    scores: dict[str, float] = {}
    chunk_data: dict[str, dict] = {}

    # Score dense results
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
            "dense_score": 1.0 - distance,  # Convert cosine distance to similarity
            "dense_rank": rank,
        }

    # Score sparse results
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
        chunk_data[doc_id]["bm25_score"] = bm25_result.score
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
                dense_score=data.get("dense_score"),
                bm25_score=data.get("bm25_score"),
                fused_score=fused_score,
            )
        )

    return fused
```

---

### BM25 Sparse Retrieval

In-memory BM25 index built at startup from all chunk texts.

**Implementation:**
```python
from rank_bm25 import BM25Okapi
import re

class BM25Index:
    def __init__(self):
        self.index: BM25Okapi | None = None
        self.doc_ids: list[str] = []
        self.doc_texts: list[str] = []
        self.doc_metadata: list[dict] = []

    def build(self, chunks: list[dict]):
        """
        Build BM25 index from chunk documents.

        Args:
            chunks: List of {id, text, metadata} dicts.
        """
        self.doc_ids = [c["id"] for c in chunks]
        self.doc_texts = [c["text"] for c in chunks]
        self.doc_metadata = [c["metadata"] for c in chunks]

        tokenized = [self._tokenize(text) for text in self.doc_texts]
        self.index = BM25Okapi(tokenized)

    def search(self, query: str, top_n: int = 10) -> list[BM25Result]:
        """Search the BM25 index and return ranked results."""
        tokens = self._tokenize(query)
        scores = self.index.get_scores(tokens)

        # Get top-N indices
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_n]

        return [
            BM25Result(
                doc_id=self.doc_ids[i],
                text=self.doc_texts[i],
                metadata=self.doc_metadata[i],
                score=float(scores[i]),
            )
            for i in top_indices
            if scores[i] > 0  # Exclude zero-score matches
        ]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Simple whitespace + lowering tokenizer."""
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        return text.split()
```

**BM25Result Schema:**
```python
class BM25Result(BaseModel):
    doc_id: str
    text: str
    metadata: dict
    score: float
```

---

### Metadata Filter Extraction

Extracts metadata constraints from the query text for Chroma `where` filtering.

**Supported Patterns:**
| Pattern | Regex | Metadata Field | Example Match |
|---------|-------|---------------|---------------|
| Error codes | `E\d{3}` | `error_code` | "E452", "E501" |
| Product names | hardcoded list | `product` | "server", "router", "switch", "gateway", "controller" |
| Source types | hardcoded list | `source` | "maintenance_manual", "troubleshooting_guide", "release_notes" |

**Implementation:**
```python
PRODUCT_NAMES = {"server", "router", "switch", "gateway", "controller", "sensor", "actuator", "plc"}
SOURCE_TYPES = {"maintenance_manual", "troubleshooting_guide", "release_notes", "safety_bulletin", "installation_guide"}

def extract_metadata_filter(query: str) -> dict | None:
    """
    Extract a Chroma-compatible 'where' filter from the query text.

    Returns:
        A Chroma 'where' dict, or None if no entities found.
    """
    filters = []
    query_lower = query.lower()

    # Extract error codes
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
```

---

### ChunkResult Schema

```python
class ChunkResult(BaseModel):
    id: str
    text: str
    metadata: dict  # {source, error_code, product, chunk_index, article_id}
    scores: ChunkScores
    rank: int

class ChunkScores(BaseModel):
    dense: float | None = None
    bm25: float | None = None
    fused: float | None = None
```

---

## Pipeline Logging

Every step in the retrieval pipeline appends a structured log entry to the `LogBuffer`.

**Log Entry Schema:**
```python
class LogEntry(BaseModel):
    timestamp: str          # ISO 8601
    stage: str              # "query_router" | "embedding" | "retrieval" | "bm25" | "rrf" | "metadata" | "hnsw" | "llm"
    message: str            # Human-readable description
    level: str              # "info" | "warn" | "debug"
```

**Log Buffer:**
```python
class LogBuffer:
    """Thread-safe ring buffer for pipeline logs."""

    def __init__(self, max_size: int = 500):
        self._buffer: deque[LogEntry] = deque(maxlen=max_size)
        self._query_logs: list[LogEntry] = []  # Current query's logs

    def start_query(self):
        """Reset per-query log collection."""
        self._query_logs = []

    def append(self, stage: str, message: str, level: str = "info"):
        entry = LogEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            stage=stage,
            message=message,
            level=level,
        )
        self._buffer.append(entry)
        self._query_logs.append(entry)

    def flush_query_logs(self) -> list[LogEntry]:
        """Return and clear current query's logs."""
        logs = self._query_logs.copy()
        self._query_logs = []
        return logs
```