# Data Model & Chroma

## Source Documents
- 200 articles in `articles.json`.
- Schema: `{id, title, body, metadata: {source, error_code, product}}`
- Chunk size: 150 tokens, 20 token overlap.

### Article Schema

```json
{
  "id": "article_001",
  "title": "Resolving Power Supply Error E452 on Server Units",
  "body": "Error E452 indicates a power delivery fault detected by the onboard monitoring system. This error is triggered when the PSU output voltage drops below the minimum threshold of 11.4V on the 12V rail...",
  "metadata": {
    "source": "maintenance_manual",
    "error_code": "E452",
    "product": "server"
  }
}
```

### Source Types & Distribution

| Source Type | Count | Description |
|------------|-------|-------------|
| `maintenance_manual` | 60 | Step-by-step repair and maintenance procedures |
| `troubleshooting_guide` | 50 | Symptom → diagnosis → fix workflows |
| `release_notes` | 30 | Firmware/software update changelogs |
| `safety_bulletin` | 30 | Safety warnings and compliance procedures |
| `installation_guide` | 30 | Setup and commissioning instructions |

### Product Types

| Product | Count | Description |
|---------|-------|-------------|
| `server` | 40 | Rack-mount server units |
| `router` | 35 | Industrial network routers |
| `switch` | 30 | Network/industrial switches |
| `gateway` | 25 | Protocol conversion gateways |
| `controller` | 25 | PLC and motion controllers |
| `sensor` | 25 | Industrial sensors and transmitters |
| `actuator` | 20 | Valves, motors, and actuators |

### Error Code Format

Error codes follow the pattern `E` + 3 digits (e.g., `E452`, `E100`, `E789`).
- Range `E100–E299`: Hardware faults (power, thermal, mechanical)
- Range `E300–E499`: Network and communication errors
- Range `E500–E699`: Software and firmware errors
- Range `E700–E899`: Configuration and calibration errors
- Range `E900–E999`: Safety and compliance alerts

Not all articles have an `error_code`; approximately 120 of 200 articles include one.

---

## Chunking Strategy

```python
def chunk_article(article: dict, chunk_size: int = 150, overlap: int = 20) -> list[dict]:
    """
    Split an article body into overlapping chunks.

    Args:
        article: Article dict with id, title, body, metadata.
        chunk_size: Target chunk size in whitespace-separated tokens.
        overlap: Number of overlapping tokens between consecutive chunks.

    Returns:
        List of chunk dicts ready for Chroma insertion.
    """
    words = article["body"].split()
    chunks = []
    start = 0
    chunk_index = 0

    while start < len(words):
        end = start + chunk_size
        chunk_text = " ".join(words[start:end])

        chunk = {
            "id": f"{article['id']}_chunk_{chunk_index}",
            "text": chunk_text,
            "metadata": {
                **article["metadata"],
                "chunk_index": chunk_index,
                "article_id": article["id"],
            },
        }
        chunks.append(chunk)

        chunk_index += 1
        start = end - overlap  # Slide forward by (chunk_size - overlap)

        # Prevent infinite loop on very short remaining text
        if start >= len(words):
            break

    return chunks
```

**Expected Output:**
- 200 articles × ~9 chunks average = ~1,800 chunks in `docs_body`.
- 200 title entries in `docs_title`.

---

## Chroma Collections

### `docs_body`
- Embedding function: all-MiniLM-L6-v2 (384 dimensions).
- Metadata fields: `source`, `error_code`, `product`, `chunk_index`, `article_id`.
- Distance metric: cosine.
- HNSW params (when HNSW feature enabled): `construction_ef=200`, `search_ef=100`.
- HNSW params (default/flat): `construction_ef=128`, `search_ef=10`.

### `docs_title`
- Created when `multi_index` active (but always built at startup for readiness).
- Stores title embeddings with same metadata fields.
- Each entry: `{id: article_id, text: title, metadata: {...}}`.

## Collection Initialization

```python
import chromadb

class ChromaStore:
    def __init__(self, persist_path: str = "/data/chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_path)
        self._collections: dict[str, chromadb.Collection] = {}

    def initialize(self, embedding_service):
        """Initialize or load collections. Seed if empty."""
        # Create/get collections
        self._collections["docs_body"] = self.client.get_or_create_collection(
            name="docs_body",
            metadata={
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 200,
                "hnsw:search_ef": 100,
            },
        )
        self._collections["docs_title"] = self.client.get_or_create_collection(
            name="docs_title",
            metadata={"hnsw:space": "cosine"},
        )

        # Check if seeding is needed
        if self._collections["docs_body"].count() == 0:
            self._seed(embedding_service)

    def _seed(self, embedding_service):
        """Load articles, chunk, embed, and upsert into collections."""
        import json

        with open("/app/data/articles.json", "r") as f:
            articles = json.load(f)

        # Seed docs_body
        all_chunks = []
        for article in articles:
            all_chunks.extend(chunk_article(article))

        # Batch embed and upsert (batch size 32)
        for i in range(0, len(all_chunks), 32):
            batch = all_chunks[i : i + 32]
            texts = [c["text"] for c in batch]
            embeddings = embedding_service.encode(texts).tolist()

            self._collections["docs_body"].upsert(
                ids=[c["id"] for c in batch],
                documents=texts,
                embeddings=embeddings,
                metadatas=[c["metadata"] for c in batch],
            )

        # Seed docs_title
        titles = [a["title"] for a in articles]
        title_embeddings = embedding_service.encode(titles).tolist()

        self._collections["docs_title"].upsert(
            ids=[a["id"] for a in articles],
            documents=titles,
            embeddings=title_embeddings,
            metadatas=[a["metadata"] for a in articles],
        )

    def get_collection(self, name: str) -> chromadb.Collection:
        return self._collections[name]

    def get_stats(self) -> dict:
        return {
            name: col.count()
            for name, col in self._collections.items()
        }
```

## Persistence
- Chroma `PersistentClient(path="/data/chroma_db")` survives restarts.
- On Hugging Face Spaces, `/data` is a persistent volume.
- If the Chroma DB already contains data on startup, seeding is skipped.

## Querying
- Dense: `collection.query(query_texts=[query], n_results=k, where=filter_dict)`
- Metadata filter example: `{"error_code": "E452"}` or `{"$and": [{"error_code":"E452"},{"product":"server"}]}`.

## BM25 Index
- Separate in-memory structure built from chunk texts.
- Built at startup after Chroma seeding (or from existing Chroma data).
- Rebuilt on each restart (not persisted).

**BM25 Initialization:**
```python
def build_bm25_index(chroma_store: ChromaStore) -> BM25Index:
    """Build BM25 index from all docs_body chunks."""
    collection = chroma_store.get_collection("docs_body")
    count = collection.count()

    # Fetch all documents from Chroma
    results = collection.get(
        include=["documents", "metadatas"],
        limit=count,
    )

    chunks = [
        {"id": doc_id, "text": text, "metadata": meta}
        for doc_id, text, meta in zip(
            results["ids"], results["documents"], results["metadatas"]
        )
    ]

    index = BM25Index()
    index.build(chunks)
    return index
```

## Metrics Computation

For each query, compute retrieval quality metrics by comparing retrieved chunks against the source article:

```python
def compute_metrics(
    retrieved_chunks: list[ChunkResult],
    query_article_id: str | None,
    k: int = 5
) -> dict:
    """
    Compute retrieval metrics.

    For demonstration purposes, "relevance" is determined by whether
    a retrieved chunk belongs to the same article as the best-matching
    chunk (article_id match).

    Args:
        retrieved_chunks: Ranked list of retrieved chunks.
        query_article_id: Article ID of the top-ranked chunk (treated as ground truth).
        k: Cutoff for recall@k.

    Returns:
        Dict with recall_at_5 and mrr.
    """
    if not query_article_id or not retrieved_chunks:
        return {"recall_at_5": 0.0, "mrr": 0.0}

    # Find all chunks from the same article as a proxy for relevance
    relevant_ids = {
        c.id for c in retrieved_chunks
        if c.metadata.get("article_id") == query_article_id
    }

    # Recall@k: fraction of relevant chunks in top-k
    top_k_ids = {c.id for c in retrieved_chunks[:k]}
    recall_at_k = len(top_k_ids & relevant_ids) / max(len(relevant_ids), 1)

    # MRR: reciprocal rank of first relevant result
    mrr = 0.0
    for i, chunk in enumerate(retrieved_chunks, 1):
        if chunk.metadata.get("article_id") == query_article_id:
            mrr = 1.0 / i
            break

    return {"recall_at_5": round(recall_at_k, 3), "mrr": round(mrr, 3)}
```