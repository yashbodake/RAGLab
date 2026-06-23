# Environment & Configuration

## Environment Variables

All configuration is via environment variables. No hardcoded secrets. No `.env` files committed to source control.

### Required Variables

| Variable | Example | Description | Where Set |
|----------|---------|-------------|-----------|
| `CEREBRAS_API_KEY` | `csk-...` | Cerebras API key for LLM inference | HF Space Secret / local `.env` |

### Optional Variables (with defaults)

| Variable | Default | Description |
|----------|---------|-------------|
| `HF_HOME` | `/data/huggingface` | Directory for cached HuggingFace model files |
| `CHROMA_PERSIST_PATH` | `/data/chroma_db` | Directory for Chroma persistent storage |
| `PORT` | `7860` | Server port |
| `LOG_LEVEL` | `info` | Logging level: `debug`, `info`, `warn`, `error` |
| `RATE_LIMIT_QUERY` | `10/minute` | Rate limit for `/query` endpoint |
| `RATE_LIMIT_EMBED` | `30/minute` | Rate limit for `/embed` endpoint |
| `EMBEDDING_BATCH_SIZE` | `32` | Max batch size for embedding encode |
| `LLM_MAX_TOKENS` | `1024` | Max tokens for LLM generation |
| `LLM_TEMPERATURE` | `0.3` | LLM temperature parameter |
| `BM25_TOP_N` | `10` | Number of BM25 candidates to retrieve |
| `DENSE_TOP_N` | `10` | Number of dense candidates to retrieve |
| `RRF_K` | `60` | RRF fusion constant |
| `LOG_BUFFER_SIZE` | `500` | Max entries in log ring buffer |

## Configuration Loading

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Required
    cerebras_api_key: str

    # Paths
    hf_home: str = "/data/huggingface"
    chroma_persist_path: str = "/data/chroma_db"
    port: int = 7860

    # Logging
    log_level: str = "info"

    # Rate limiting
    rate_limit_query: str = "10/minute"
    rate_limit_embed: str = "30/minute"

    # Embedding
    embedding_batch_size: int = 32

    # LLM
    llm_max_tokens: int = 1024
    llm_temperature: float = 0.3

    # Retrieval
    bm25_top_n: int = 10
    dense_top_n: int = 10
    rrf_k: int = 60

    # Logging buffer
    log_buffer_size: int = 500

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()
```

## `.env.example` (committed to repo)

```bash
# === REQUIRED ===
CEREBRAS_API_KEY=your-cerebras-api-key-here

# === OPTIONAL (defaults shown) ===
# HF_HOME=/data/huggingface
# CHROMA_PERSIST_PATH=/data/chroma_db
# PORT=7860
# LOG_LEVEL=info
# RATE_LIMIT_QUERY=10/minute
# RATE_LIMIT_EMBED=30/minute
# LLM_MAX_TOKENS=1024
# LLM_TEMPERATURE=0.3
```

## `.env` (local development, git-ignored)

```bash
CEREBRAS_API_KEY=csk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
HF_HOME=./data/huggingface
CHROMA_PERSIST_PATH=./data/chroma_db
LOG_LEVEL=debug
```

## Secrets Management

| Environment | Secret Storage | Access Method |
|-------------|---------------|---------------|
| Local dev | `.env` file (git-ignored) | `pydantic-settings` reads from file |
| HF Spaces | Space Secrets UI | Injected as env vars by HF runtime |
| CI/CD | GitHub Secrets | Injected into test runner env |

### Security Rules

1. **NEVER** commit `.env` to version control. Only `.env.example` is committed.
2. **NEVER** hardcode API keys or use literal fallback values.
3. If `CEREBRAS_API_KEY` is missing, the application **MUST** fail at startup with a clear error message:
   ```
   RuntimeError: CEREBRAS_API_KEY environment variable is required. 
   Set it in .env for local dev or as a Space Secret for HF Spaces.
   ```
4. All other variables have safe defaults and are optional.

## Configuration Hierarchy

```
1. Environment variables (highest priority)
2. .env file (local dev only)
3. Defaults in Settings class (lowest priority)
```

## Logging Configuration

```python
import logging

def setup_logging(level: str = "info"):
    """Configure structured logging."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Suppress noisy third-party loggers
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
```

**Log format example:**
```
2025-01-15 10:30:45 | INFO  | backend.core.retrieval | Dense search: 10 candidates in 12.3ms
2025-01-15 10:30:45 | INFO  | backend.core.rrf | RRF fusion: merged 18 unique → top 3
2025-01-15 10:30:45 | DEBUG | backend.services.embedding | Encoded 1 text(s) in 11.2ms
```
