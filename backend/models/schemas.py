from typing import Literal, List, Dict, Any, Optional
from pydantic import BaseModel, Field

class FeatureFlags(BaseModel):
    """Features toggle switches payload."""
    hybrid: bool = False
    remote_embed: bool = False
    query_understanding: bool = False
    metadata_aware: bool = False
    multi_index: bool = False
    hnsw: bool = False
    stream_sources: bool = False

class QueryRequest(BaseModel):
    """Query API request schema."""
    query: str = Field(..., min_length=1, max_length=2000)
    features: FeatureFlags = FeatureFlags()
    compare_with_baseline: bool = False

class EmbedRequest(BaseModel):
    """Embedding API request schema."""
    texts: List[str] = Field(..., min_length=1, max_length=32)

class EmbedResponse(BaseModel):
    """Embedding API response schema."""
    embeddings: List[List[float]]
    model: str
    dimensions: int
    latency_ms: float

class Classification(BaseModel):
    """QueryRouter classification result."""
    type: Literal["FACT", "TOPIC", "COMPARE"]
    top_k: int
    sub_queries: Optional[List[str]] = None

class ChunkScores(BaseModel):
    """Scores assigned to a chunk from different retrievers."""
    dense: Optional[float] = None
    bm25: Optional[float] = None
    fused: Optional[float] = None

class ChunkResult(BaseModel):
    """Ranked retrieved document chunk."""
    id: str
    text: str
    metadata: Dict[str, Any]
    scores: ChunkScores
    rank: int

class LogEntry(BaseModel):
    """Pipeline logs ring buffer entry."""
    timestamp: str          # ISO 8601
    stage: str              # "query_router" | "embedding" | "retrieval" | "bm25" | "rrf" | "metadata" | "hnsw" | "llm"
    message: str            # Human-readable description
    level: str              # "info" | "warn" | "debug"
