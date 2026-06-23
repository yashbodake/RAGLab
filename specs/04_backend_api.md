# Backend API Specification

## Base URL
`http://localhost:7860` (inside container) / `https://{space}.hf.space`

## Common Headers

**Request Headers:**
| Header | Value | Required |
|--------|-------|----------|
| `Content-Type` | `application/json` | Yes |
| `Accept` | `text/event-stream` | Yes (for `/query`) |

**Response Headers:**
| Header | Value |
|--------|-------|
| `Content-Type` | `text/event-stream; charset=utf-8` (for SSE) or `application/json` |
| `Cache-Control` | `no-cache, no-store` |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Content-Security-Policy` | `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; connect-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'` |

---

## Endpoints

### `POST /query`

Main query endpoint. Accepts the user's question and active feature flags. Returns a Server-Sent Events stream.

**Request Body:**
```json
{
  "query": "How to fix error E452 on server?",
  "features": {
    "hybrid": true,
    "remote_embed": false,
    "query_understanding": true,
    "metadata_aware": false,
    "multi_index": false,
    "hnsw": true,
    "stream_sources": false
  },
  "compare_with_baseline": false
}
```

**Request Schema (Pydantic):**
```python
class FeatureFlags(BaseModel):
    hybrid: bool = False
    remote_embed: bool = False
    query_understanding: bool = False
    metadata_aware: bool = False
    multi_index: bool = False
    hnsw: bool = False
    stream_sources: bool = False

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    features: FeatureFlags = FeatureFlags()
    compare_with_baseline: bool = False
```

**Response: Server-Sent Events Stream**

The response is an SSE stream with the following event types, sent in this order:

#### Event: `classification`
Sent immediately after query classification. Always sent.
```
event: classification
data: {"type": "FACT", "top_k": 3, "sub_queries": null}
```
```
event: classification
data: {"type": "COMPARE", "top_k": 5, "sub_queries": ["error E452", "error E501"]}
```

#### Event: `sources`
Sent after retrieval completes. Contains the ranked chunks. If `stream_sources` is enabled, this is sent before token generation begins. Otherwise, it's sent alongside the first token.
```
event: sources
data: {
  "chunks": [
    {
      "id": "article_12_chunk_3",
      "text": "To resolve error E452, first check the power supply unit...",
      "metadata": {
        "source": "maintenance_manual",
        "error_code": "E452",
        "product": "server",
        "chunk_index": 3,
        "article_id": "article_12"
      },
      "scores": {
        "dense": 0.847,
        "bm25": 0.623,
        "fused": 0.891
      },
      "rank": 1
    }
  ]
}
```

#### Event: `baseline_sources`
Sent only when `compare_with_baseline` is `true`. Contains chunks retrieved with all features disabled.
```
event: baseline_sources
data: {
  "chunks": [
    {
      "id": "article_12_chunk_3",
      "text": "...",
      "metadata": { ... },
      "scores": { "dense": 0.847 },
      "rank": 1
    }
  ]
}
```

#### Event: `token`
Streamed one at a time as the LLM generates. Each event contains a single token or small text fragment.
```
event: token
data: {"text": "To"}
```
```
event: token
data: {"text": " resolve"}
```

#### Event: `metrics`
Sent after generation completes. Contains timing and quality metrics.
```
event: metrics
data: {
  "retrieval_time_ms": 45.2,
  "generation_time_ms": 1230.5,
  "recall_at_5": 0.80,
  "mrr": 0.667,
  "total_chunks_retrieved": 5,
  "collection_used": "docs_body",
  "classification": "FACT"
}
```

#### Event: `baseline_metrics`
Sent only when `compare_with_baseline` is `true`.
```
event: baseline_metrics
data: {
  "retrieval_time_ms": 52.1,
  "generation_time_ms": 1180.3,
  "recall_at_5": 0.60,
  "mrr": 0.500,
  "total_chunks_retrieved": 5,
  "collection_used": "docs_body",
  "classification": "FACT"
}
```

#### Event: `logs`
Sent after generation completes. Contains all pipeline log entries for this query.
```
event: logs
data: {
  "entries": [
    {
      "timestamp": "2025-01-15T10:30:45.123Z",
      "stage": "query_router",
      "message": "Classified as FACT, top_k=3",
      "level": "info"
    },
    {
      "timestamp": "2025-01-15T10:30:45.135Z",
      "stage": "retrieval",
      "message": "Dense search: 10 candidates in 12.3ms",
      "level": "info"
    },
    {
      "timestamp": "2025-01-15T10:30:45.148Z",
      "stage": "bm25",
      "message": "Sparse search: 10 candidates in 3.1ms",
      "level": "info"
    },
    {
      "timestamp": "2025-01-15T10:30:45.150Z",
      "stage": "rrf",
      "message": "RRF fusion: merged 18 unique → top 3, best_score=0.891",
      "level": "info"
    }
  ]
}
```

#### Event: `error`
Sent if any stage fails. Connection closes after this event.
```
event: error
data: {"message": "LLM API rate limit exceeded. Try again in 60s.", "stage": "llm"}
```

#### Event: `done`
Sent as the final event, signaling the stream is complete.
```
event: done
data: {}
```

**Error Responses (non-SSE):**

| Status | Body | Condition |
|--------|------|-----------|
| 400 | `{"detail": "Query must be between 1 and 2000 characters"}` | Validation failure |
| 429 | `{"detail": "Rate limit exceeded. Max 10 queries per minute."}` | Rate limiting |
| 500 | `{"detail": "Internal server error"}` | Unhandled exception |

---

### `POST /embed`

Internal embedding endpoint. Used by `RetrievalManager` when `remote_embed` feature is active. Simulates a remote embedding service call.

**Request Body:**
```json
{
  "texts": ["How to fix error E452?", "Server power supply troubleshooting"]
}
```

**Request Schema:**
```python
class EmbedRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1, max_length=32)
```

**Response (200):**
```json
{
  "embeddings": [[0.023, -0.156, 0.089, ...]],
  "model": "all-MiniLM-L6-v2",
  "dimensions": 384,
  "latency_ms": 11.7
}
```

**Response Schema:**
```python
class EmbedResponse(BaseModel):
    embeddings: list[list[float]]
    model: str
    dimensions: int
    latency_ms: float
```

---

### `GET /health`

Health check endpoint for Docker and Hugging Face Spaces monitoring.

**Response (200):**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "chroma_collections": {
    "docs_body": 1847,
    "docs_title": 200
  },
  "bm25_index_size": 1847,
  "uptime_seconds": 3421.5
}
```

---

## Rate Limiting

- **`POST /query`**: 10 requests per minute per client IP.
- **`POST /embed`**: 30 requests per minute (internal use only, but rate-limited as safety).
- **`GET /health`**: No rate limit.

Implementation: Use `slowapi` middleware with in-memory storage.

## CORS Policy

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://{space}.hf.space"],  # Restrict to HF Spaces origin
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Accept"],
    allow_credentials=False,
)
```

For local development, `allow_origins` includes `http://localhost:5173` (Vite dev server).

## Error Handling Strategy

1. All exceptions caught at the route level.
2. Generic error messages returned to client; detailed errors logged server-side.
3. SSE streams send an `error` event before closing on failures.
4. Pydantic validation errors return 400 with field-level detail.