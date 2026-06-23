import logging
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Required
    cerebras_api_key: str | None = None

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

    def __init__(self, **values):
        super().__init__(**values)
        if not self.cerebras_api_key:
            raise RuntimeError(
                "CEREBRAS_API_KEY environment variable is required. "
                "Set it in .env for local dev or as a Space Secret for HF Spaces."
            )

# Instantiate settings
try:
    settings = Settings()
except Exception as e:
    # If instantiation fails due to missing CEREBRAS_API_KEY, we want to ensure
    # that any import of this module fails fast with the appropriate message.
    # Note: In test environments we might want to mock settings, but failing fast is critical.
    raise e

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
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
