import time
import logging
import os
import json
import uuid
from typing import AsyncGenerator
from fastapi import APIRouter, Request, HTTPException, status, File, UploadFile
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.core.config import settings
from backend.models.schemas import QueryRequest, EmbedRequest, EmbedResponse, Classification, FeatureFlags
from backend.core.query_router import QueryRouter
from backend.core.retrieval import RetrievalManager
from backend.api.sse import sse_event
from backend.services.log_buffer import LogBuffer

logger = logging.getLogger("backend.api.routes")
router = APIRouter()

# Setup rate limiting
limiter = Limiter(key_func=get_remote_address)

def compute_metrics(retrieved_chunks, query_article_id, k=5) -> dict:
    """
    Compute retrieval metrics.
    Relevance is determined by matching the ground-truth top-ranked article ID.
    """
    if not query_article_id or not retrieved_chunks:
        return {"recall_at_5": 0.0, "mrr": 0.0}

    # Chunks from the same article as relevance proxy
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

@router.get("/health")
def health_endpoint(request: Request):
    """Health check endpoint checking Chroma store and model."""
    try:
        chroma_store = request.app.state.chroma_store
        stats = chroma_store.get_stats()
        uptime = time.time() - request.app.state.startup_time
        
        # Approximate BM25 index size
        bm25_index = request.app.state.bm25_index
        bm25_size = len(bm25_index.doc_ids) if bm25_index else 0
        
        return {
            "status": "healthy",
            "model_loaded": request.app.state.embedding_service.model is not None,
            "chroma_collections": stats,
            "bm25_index_size": bm25_size,
            "uptime_seconds": round(uptime, 1)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed: internal service error"
        )

@router.post("/embed", response_model=EmbedResponse)
@limiter.limit("30/minute")
def embed_endpoint(request: Request, embed_request: EmbedRequest):
    """Simulates a remote embedding endpoint by using local SentenceTransformer."""
    try:
        start_time = time.monotonic()
        emb_service = request.app.state.embedding_service
        embeddings = emb_service.encode(embed_request.texts)
        latency = (time.monotonic() - start_time) * 1000
        
        return EmbedResponse(
            embeddings=embeddings.tolist(),
            model=emb_service.model_name,
            dimensions=emb_service.dimensions,
            latency_ms=round(latency, 2)
        )
    except Exception as e:
        logger.error(f"Embedding failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Embedding generation failed"
        )

@router.post("/query")
@limiter.limit("10/minute")
async def query_endpoint(request: Request, query_request: QueryRequest):
    """SSE streaming query endpoint."""
    async def sse_generator() -> AsyncGenerator[str, None]:
        log_buffer: LogBuffer = request.app.state.log_buffer
        retrieval_manager: RetrievalManager = request.app.state.retrieval_manager
        llm_client = request.app.state.llm_client
        
        log_buffer.start_query()
        query_start = time.monotonic()
        
        log_buffer.append("query_router", f"Received query: '{query_request.query}'", "info")
        
        try:
            # 1. Classification
            clf = QueryRouter.classify(
                query_request.query, 
                query_request.features.query_understanding
            )
            log_buffer.append(
                "query_router", 
                f"Query classified as {clf.type} (top_k={clf.top_k}, sub_queries={clf.sub_queries})", 
                "info"
            )
            yield sse_event("classification", clf.model_dump())
            
            # 2. Enhanced Retrieval
            retrieval_start = time.monotonic()
            chunks = await retrieval_manager.retrieve(
                query_request.query,
                clf,
                query_request.features,
                log_buffer
            )
            retrieval_time_ms = (time.monotonic() - retrieval_start) * 1000
            
            # 3. Optional Baseline Run
            baseline_chunks = []
            baseline_retrieval_time_ms = 0.0
            if query_request.compare_with_baseline:
                log_buffer.append("retrieval", "Running baseline query (all features disabled)", "info")
                base_clf = Classification(type="FACT", top_k=5)
                base_features = FeatureFlags(
                    hybrid=False, remote_embed=False, query_understanding=False,
                    metadata_aware=False, multi_index=False, hnsw=False, stream_sources=False
                )
                
                # Use a separate log buffer to avoid mixing baseline logs
                dummy_buffer = LogBuffer()
                dummy_buffer.start_query()
                
                base_start = time.monotonic()
                baseline_chunks = await retrieval_manager.retrieve(
                    query_request.query,
                    base_clf,
                    base_features,
                    dummy_buffer
                )
                baseline_retrieval_time_ms = (time.monotonic() - base_start) * 1000
                
            # 4. Stream Sources
            yield sse_event("sources", {"chunks": [c.model_dump() for c in chunks]})
            if query_request.compare_with_baseline:
                yield sse_event("baseline_sources", {"chunks": [c.model_dump() for c in baseline_chunks]})
                
            # 5. Token Generation (LLM)
            from backend.services.llm import SYSTEM_PROMPT, build_user_prompt
            user_prompt = build_user_prompt(query_request.query, chunks, clf)
            
            gen_start = time.monotonic()
            tokens_generated = 0
            
            log_buffer.append("llm", "Initiating Cerebras streaming completion...", "info")
            
            try:
                # Wrap generation in timeout safety
                stream = llm_client.stream_completion(
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    max_tokens=settings.llm_max_tokens,
                    temperature=settings.llm_temperature
                )
                
                async for token in stream:
                    yield sse_event("token", {"text": token})
                    tokens_generated += 1
                    
                if tokens_generated == 0:
                    warning_msg = (
                        "⚠️ The API provider returned an empty response. "
                        "This can happen due to transient network congestion or remote API load. "
                        "Please try sending your query again."
                    )
                    yield sse_event("token", {"text": warning_msg})
                    log_buffer.append("llm", "Warning: Generated 0 tokens from Cerebras LLM stream.", "warning")
                else:
                    log_buffer.append("llm", f"Stream complete. Generated {tokens_generated} tokens.", "info")
                    
                generation_time_ms = (time.monotonic() - gen_start) * 1000
                
            except Exception as e:
                # Map LLM errors cleanly
                logger.error(f"LLM streaming failed: {e}", exc_info=True)
                err_msg = "Failed to generate LLM response. Please check CEREBRAS_API_KEY connection."
                if "rate limit" in str(e).lower():
                    err_msg = "LLM rate limit reached. Please try again in 60 seconds."
                log_buffer.append("llm", f"LLM Error: {e}", "error")
                yield sse_event("error", {"message": err_msg, "stage": "llm"})
                yield sse_event("done", {})
                return
                
            # 6. Metrics Computing
            # Top chunk of enhanced run is ground-truth article ID proxy
            query_article_id = chunks[0].metadata.get("article_id") if chunks else None
            enhanced_metrics = compute_metrics(chunks, query_article_id)
            
            metrics_payload = {
                "retrieval_time_ms": round(retrieval_time_ms, 2),
                "generation_time_ms": round(generation_time_ms, 2),
                "recall_at_5": enhanced_metrics["recall_at_5"],
                "mrr": enhanced_metrics["mrr"],
                "total_chunks_retrieved": len(chunks),
                "collection_used": "docs_title" if (query_request.features.multi_index and clf.type == "FACT") else "docs_body",
                "classification": clf.type
            }
            yield sse_event("metrics", metrics_payload)
            
            if query_request.compare_with_baseline:
                baseline_metrics = compute_metrics(baseline_chunks, query_article_id)
                baseline_payload = {
                    "retrieval_time_ms": round(baseline_retrieval_time_ms, 2),
                    "generation_time_ms": round(generation_time_ms, 2), # Use same generation time as comparison
                    "recall_at_5": baseline_metrics["recall_at_5"],
                    "mrr": baseline_metrics["mrr"],
                    "total_chunks_retrieved": len(baseline_chunks),
                    "collection_used": "docs_body",
                    "classification": "FACT"
                }
                yield sse_event("baseline_metrics", baseline_payload)
                
            # 7. Flush Pipeline Logs
            logs = log_buffer.flush_query_logs()
            yield sse_event("logs", {"entries": [l.model_dump() for l in logs]})
            
            # 8. Done
            yield sse_event("done", {})
            
        except Exception as e:
            logger.error(f"Query pipeline crashed: {e}", exc_info=True)
            yield sse_event("error", {"message": "Internal pipeline search crashed.", "stage": "pipeline"})
            yield sse_event("done", {})

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...)
):
    """
    Upload and parse a text, JSON, or PDF document.
    Chunks the document, embeds it, inserts it into Chroma, and rebuilds the BM25 index in-place.
    """
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in [".txt", ".json", ".pdf"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only .txt, .json, and .pdf are allowed."
        )
    
    # Read first 5MB + 1 byte to check size constraint
    content = await file.read(5 * 1024 * 1024 + 1)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the maximum limit of 5MB"
        )

    doc_store = request.app.state.doc_store
    chroma_store = request.app.state.chroma_store
    embedding_service = request.app.state.embedding_service

    # Clean up old upload with the same filename if it exists to avoid duplications
    existing_docs = doc_store.load_docs()
    old_doc = next((d for d in existing_docs if d["filename"] == filename), None)
    if old_doc:
        logger.info(f"Overwriting existing document '{filename}'. Deleting old chunks first.")
        try:
            body_col = chroma_store.get_collection("docs_body")
            title_col = chroma_store.get_collection("docs_title")
            body_col.delete(where={"source": filename})
            title_col.delete(where={"source": filename})
            doc_store.delete_doc(old_doc["id"])
        except Exception as e:
            logger.warning(f"Failed to clear old document chunks for '{filename}': {e}")

    # Register initial "processing" state
    doc_id = f"art_upload_{uuid.uuid4().hex[:8]}"
    doc_title = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ")
    doc_store.add_or_update_doc(
        doc_id=doc_id,
        filename=filename,
        title=doc_title,
        status="processing"
    )
        
    articles = []
    
    try:
        if ext == ".txt":
            text = content.decode("utf-8", errors="ignore")
            if not text.strip():
                raise ValueError("Uploaded text file is empty")
            articles.append({
                "id": doc_id,
                "title": doc_title,
                "body": text,
                "metadata": {
                    "source": filename,
                    "product": "unknown",
                    "error_code": ""
                }
            })
            
        elif ext == ".json":
            try:
                data = json.loads(content.decode("utf-8", errors="ignore"))
                if not isinstance(data, list):
                    raise ValueError("JSON must be a list of article objects")
                for idx, item in enumerate(data):
                    if "title" not in item or "body" not in item:
                        raise ValueError(f"Item at index {idx} must contain 'title' and 'body' keys")
                    articles.append({
                        "id": item.get("id") or f"art_upload_{uuid.uuid4().hex[:8]}_{idx}",
                        "title": item["title"],
                        "body": item["body"],
                        "metadata": item.get("metadata", {
                            "source": filename,
                            "product": "unknown",
                            "error_code": ""
                        })
                    })
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON file format")
                
        elif ext == ".pdf":
            import tempfile
            import pymupdf4llm
            
            # Write bytes safely to temporary file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
                
            try:
                md_text = pymupdf4llm.to_markdown(tmp_path)
            except Exception as e:
                logger.error(f"PDF parsing via pymupdf4llm failed: {e}", exc_info=True)
                raise ValueError(f"Failed to parse PDF: {e}")
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                    
            if not md_text.strip():
                raise ValueError("Extracted text from PDF is empty")
                
            articles.append({
                "id": doc_id,
                "title": doc_title,
                "body": md_text,
                "metadata": {
                    "source": filename,
                    "product": "unknown",
                    "error_code": ""
                }
            })

        chunks_added = chroma_store.add_documents(articles, embedding_service)
        
        # Rebuild BM25 index in-place
        from backend.core.bm25 import build_bm25_index
        new_bm25 = build_bm25_index(chroma_store)
        
        # Re-assign internal state of current app index to avoid breaking retrieval references
        request.app.state.bm25_index.index = new_bm25.index
        request.app.state.bm25_index.doc_ids = new_bm25.doc_ids
        request.app.state.bm25_index.doc_texts = new_bm25.doc_texts
        request.app.state.bm25_index.doc_metadata = new_bm25.doc_metadata
        
        logger.info(f"Ingested document '{filename}' successfully. Added {chunks_added} chunks.")
        
        # Update metadata store to Success
        doc_store.add_or_update_doc(
            doc_id=doc_id,
            filename=filename,
            title=doc_title,
            status="success",
            chunk_count=chunks_added
        )
        
        return {
            "success": True,
            "filename": filename,
            "chunks_added": chunks_added,
            "total_chunks": chroma_store.get_stats()["docs_body"]
        }
        
    except Exception as e:
        logger.error(f"Failed to index document: {e}", exc_info=True)
        # Update metadata store to Failed
        doc_store.add_or_update_doc(
            doc_id=doc_id,
            filename=filename,
            title=doc_title,
            status="failed",
            error_message=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to index document: {str(e)}"
        )

@router.get("/documents")
def list_documents(request: Request):
    """Retrieve list of user-uploaded documents and statuses."""
    doc_store = request.app.state.doc_store
    return doc_store.load_docs()

@router.post("/documents/{doc_id}/toggle")
def toggle_document(request: Request, doc_id: str):
    """Toggle document active status."""
    doc_store = request.app.state.doc_store
    
    docs = doc_store.load_docs()
    doc = next((d for d in docs if d["id"] == doc_id), None)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
        
    new_state = doc_store.toggle_doc(doc_id)
    return {"success": True, "active": new_state}

@router.delete("/documents/{doc_id}")
def delete_document(request: Request, doc_id: str):
    """Permanently delete an uploaded document and rebuild BM25 indices."""
    doc_store = request.app.state.doc_store
    chroma_store = request.app.state.chroma_store
    
    docs = doc_store.load_docs()
    doc_to_delete = next((d for d in docs if d["id"] == doc_id), None)
    if not doc_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
        
    try:
        body_col = chroma_store.get_collection("docs_body")
        title_col = chroma_store.get_collection("docs_title")
        
        # Delete chunks by matching source filename
        body_col.delete(where={"source": doc_to_delete["filename"]})
        title_col.delete(where={"source": doc_to_delete["filename"]})
        
        # Delete entry from document store
        doc_store.delete_doc(doc_id)
        
        # Rebuild BM25 in-place
        from backend.core.bm25 import build_bm25_index
        new_bm25 = build_bm25_index(chroma_store)
        request.app.state.bm25_index.index = new_bm25.index
        request.app.state.bm25_index.doc_ids = new_bm25.doc_ids
        request.app.state.bm25_index.doc_texts = new_bm25.doc_texts
        request.app.state.bm25_index.doc_metadata = new_bm25.doc_metadata
        
        logger.info(f"Deleted document '{doc_to_delete['filename']}' successfully.")
        return {"success": True, "message": "Document deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete document {doc_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {e}"
        )
