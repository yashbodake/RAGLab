import os
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Add sqlite3 override at the very entrypoint to make sure any Chroma load is safe
import sys
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

from backend.core.config import settings, setup_logging
from backend.services.embedding import EmbeddingService
from backend.services.chroma_store import ChromaStore
from backend.core.bm25 import build_bm25_index
from backend.services.llm import LLMClient
from backend.services.log_buffer import LogBuffer
from backend.core.retrieval import RetrievalManager
from backend.api.routes import router, limiter

# Configure logging
setup_logging(settings.log_level)
logger = logging.getLogger("backend.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for initialization and cleanup."""
    try:
        app.state.startup_time = time.time()
        
        # Step 1: Validate configuration
        if not settings.cerebras_api_key:
            raise RuntimeError(
                "CEREBRAS_API_KEY environment variable is required. "
                "Set it in .env for local dev or as a Space Secret for HF Spaces."
            )

        # Step 2: Load embedding model
        logger.info("Loading embedding model...")
        embedding_service = EmbeddingService()
        embedding_service.load()
        app.state.embedding_service = embedding_service
        logger.info("Embedding model loaded successfully")

        # Step 3: Initialize Chroma Store
        logger.info("Initializing ChromaDB...")
        # Resolve persistence path safely
        chroma_store = ChromaStore(persist_path=settings.chroma_persist_path)
        chroma_store.initialize(embedding_service)
        app.state.chroma_store = chroma_store
        logger.info(f"ChromaDB ready: {chroma_store.get_stats()}")

        # Initialize Document Metadata Store
        from backend.services.doc_store import DocumentMetadataStore
        doc_store_path = os.path.join(
            os.path.dirname(os.path.abspath(settings.chroma_persist_path)),
            "uploaded_docs.json"
        )
        app.state.doc_store = DocumentMetadataStore(filepath=doc_store_path)

        # Step 4: Build BM25 Index
        logger.info("Building BM25 index...")
        bm25_index = build_bm25_index(chroma_store)
        app.state.bm25_index = bm25_index
        logger.info(f"BM25 index ready: {len(bm25_index.doc_ids)} documents")

        # Step 5: Initialize Log Buffer and Retrieval Manager
        app.state.log_buffer = LogBuffer(max_size=settings.log_buffer_size)
        app.state.retrieval_manager = RetrievalManager(
            embedding_service=embedding_service,
            chroma_store=chroma_store,
            bm25_index=bm25_index,
            doc_store=app.state.doc_store
        )
        
        # Step 6: Initialize LLM client
        app.state.llm_client = LLMClient()
        logger.info("LLM client initialized")

        yield

    except Exception as e:
        logger.critical(f"Startup failed: {e}", exc_info=True)
        raise  # Crash container and restart

# Create FastAPI app
app = FastAPI(
    title="Industrial RAG Demonstrator",
    description="FastAPI Backend for RAG Retrieval Improvement Features",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
origins = [
    "http://localhost:5173",  # Local Vite dev server
    "http://127.0.0.1:5173",
    "https://*.hf.space",     # Hugging Face Spaces subdomain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Accept"],
    allow_credentials=False,
)

# Register slowapi rate limiting components
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include API routes
app.include_router(router)

# Mount frontend static directory after API routes
static_dir = "static"
os.makedirs(static_dir, exist_ok=True)
# Create a simple placeholder index.html if it doesn't exist
index_path = os.path.join(static_dir, "index.html")
if not os.path.exists(index_path):
    with open(index_path, "w") as f:
        f.write("<!DOCTYPE html><html><body><h1>Industrial RAG Backend</h1></body></html>")

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
