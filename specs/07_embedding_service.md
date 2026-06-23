# Embedding Service

## Model
- `all-MiniLM-L6-v2` (Sentence Transformers), 384‑dim.
- Loaded once at startup, cached.
- Files stored under `/data/huggingface` (HF_HOME).

## Modes
### Local (default)
`EmbeddingService.encode(texts: List[str]) -> np.ndarray`  
Direct `model.encode()`.

### Remote (simulated)
When `remote_embed` feature active, backend calls its own `/embed` endpoint via HTTP.
- Shows request/response logs, latency (~12ms).
- Results must match local encoding exactly.

## Performance
- Batch size up to 32.
- Latency ~10‑15ms on CPU.

## Implementation

```python
from sentence_transformers import SentenceTransformer
import numpy as np

class EmbeddingService:
    def __init__(self):
        self.model: SentenceTransformer | None = None
        self.model_name = "all-MiniLM-L6-v2"
        self.dimensions = 384

    def load(self):
        """Load model at startup. Uses HF_HOME cache directory."""
        self.model = SentenceTransformer(self.model_name)

    def encode(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """
        Encode texts to embeddings.

        Args:
            texts: List of strings to embed.
            batch_size: Max batch size for encoding.

        Returns:
            np.ndarray of shape (len(texts), 384).
        """
        if self.model is None:
            raise RuntimeError("Embedding model not loaded. Call load() first.")

        return self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
```

## Remote Embedding Flow

When `remote_embed` is active, the `RetrievalManager` calls the backend's own `/embed` endpoint instead of calling `EmbeddingService.encode()` directly. This simulates a microservice architecture.

```python
import httpx

async def call_embed_endpoint(texts: list[str], base_url: str = "http://127.0.0.1:7860") -> np.ndarray:
    """
    Call the /embed endpoint to simulate remote embedding.

    Args:
        texts: Texts to embed.
        base_url: Backend base URL (self-call).

    Returns:
        np.ndarray of embeddings.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/embed",
            json={"texts": texts},
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()
        return np.array(data["embeddings"])
```

**What the logs show:**
```
[embedding] Remote embedding request: 1 text(s)
[embedding] POST http://127.0.0.1:7860/embed → 200 in 11.7ms
[embedding] Response: 1 embedding(s), 384 dimensions
```

## Model Details

| Property | Value |
|----------|-------|
| Model | `all-MiniLM-L6-v2` |
| Parameters | 22.7M |
| Dimensions | 384 |
| Max sequence length | 256 tokens |
| Disk size | ~90MB |
| Load time (CPU) | ~2-3s |
| Encode time (single text, CPU) | ~10-15ms |
| Encode time (batch of 32, CPU) | ~50-80ms |
| Normalization | L2 normalized (unit vectors) |