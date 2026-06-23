# Project Overview: Industrial RAG Demonstrator

## Purpose
A production‑grade chat application that incrementally demonstrates seven advanced retrieval techniques. The UI exposes each technique with toggles, live before/after comparisons, metrics, and logs. The backend is fully decoupled and deployable for free on Hugging Face Spaces via Docker.

## Scope
- Implement 7 retrieval improvement features, each independently toggleable.
- Provide a Vue 3 single‑page application (SPA) with a dark industrial design.
- FastAPI backend handling retrieval orchestration, streaming, and logging.
- Use Chroma for vector storage and BM25 for sparse retrieval, all embedded.
- LLM inference via Cerebras API (free tier usage).
- Embedding model runs locally on CPU (all‑MiniLM‑L6‑v2).
- All components run in a single Docker container on free Hugging Face Spaces.

## Target Audience
- Evaluators of RAG improvements.
- Developers learning advanced retrieval patterns.
- Stakeholders reviewing the tech feasibility.

## Success Criteria
- All 7 features are demonstrable via UI toggles.
- Each feature toggle produces a measurable improvement in retrieval metrics (recall@5, MRR) compared to a baseline.
- Real‑time logs show classification, fusion, metadata filtering, and latency.
- The system runs entirely on free‑tier infrastructure with no cost.
- The UI looks polished, industrial, and professional.

## Constraints
- No GPU available; CPU only, 16 GB RAM max.
- Must use free hosting (Hugging Face Spaces).
- Must remain a self‑contained Docker image.
- Models must be small enough to load on CPU without performance degradation.