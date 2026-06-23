---
title: Industrial RAG Demonstrator
emoji: 🔧
colorFrom: cyan
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Industrial RAG Demonstrator

A production-grade sandboxed web application demonstrating 7 advanced retrieval improvement techniques for Retrieval-Augmented Generation (RAG) using a Vue 3 frontend and a FastAPI backend, designed for CPU-only execution and deployed on Hugging Face Spaces.

## Key Features

1. **Hybrid Retrieval** — Combines local dense SentenceTransformer embeddings (`all-MiniLM-L6-v2`) with sparse keyword retrieval (`BM25`) using Reciprocal Rank Fusion (`RRF`).
2. **Remote Embedding Service** — Supports routing query embedding tasks dynamically to remote REST endpoints via local loopback calls.
3. **Adaptive Query Routing** — Automatically classifies queries into `FACT`, `TOPIC`, or `COMPARE` categories to fine-tune retrieval strategies (adaptive top-k and sub-query splitting).
4. **Metadata-Aware Filtering** — Performs entity extraction on input queries using regex patterns to isolate and focus database queries on matching error codes or products.
5. **Multi-Index Strategy** — Dynamically queries isolated indices (such as article titles for `FACT` type questions) to retrieve highly targeted sources.
6. **HNSW Vector Index Tuning** — Demonstrates graph-search scaling parameters (`efSearch`) on Chroma collections to optimize trade-offs between speed and search accuracy.
7. **Eager Sources Streaming** — Emits retrieved sources and rank scores via Server-Sent Events (SSE) before generation begins to minimize perceived user latency.

---

## Local Development & Setup

### Prerequisites
- Node.js (v20+ recommended)
- Python 3.10+
- An API Key from Cerebras (`CEREBRAS_API_KEY`)

### Running the Application

1. **Configure Environment Variables**:
   Create a `.env` file in the root folder matching the `.env.example` template:
   ```env
   CEREBRAS_API_KEY="your-api-key"
   CHROMA_PERSIST_PATH="./data/chroma_db"
   HF_HOME="./data/huggingface"
   LOG_LEVEL="INFO"
   ```

2. **Launch backend**:
   ```bash
   pip install -r requirements.txt
   uvicorn backend.main:app --port 7860 --reload
   ```

3. **Launch frontend (in development mode)**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Open `http://localhost:5173` to test with hot reloading.

### Running with Docker

Build and run the single container setup:
```bash
docker build -t industrial-rag .
docker run -p 7860:7860 -e CEREBRAS_API_KEY="your-api-key" industrial-rag
```
Visit `http://localhost:7860` in your browser.
