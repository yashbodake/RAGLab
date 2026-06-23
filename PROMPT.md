# Spec-Driven Development Prompt — Industrial RAG Demonstrator

> Copy and paste this prompt into a new chat session to begin building the project. It instructs the AI to follow the specs exactly.

---

## THE PROMPT

```
You are building an "Industrial RAG Demonstrator" — a production-grade chat application that showcases 7 advanced retrieval techniques with a Vue 3 frontend and FastAPI backend, deployed on Hugging Face Spaces via Docker.

## Rules — Spec-Driven Development

1. **The specs are the source of truth.** All 15 specification files are in the `specs/` folder. Read them BEFORE writing any code. NEVER deviate from a spec without explicitly stating why and updating the spec first.
2. **Read specs in dependency order.** Start with `00_spec_index.md` to understand the full map, then follow the implementation order defined there.
3. **Every code file must trace to a spec.** When creating a file, reference which spec(s) it implements (e.g., "Implements spec 05, QueryRouter section").
4. **Follow the directory structure exactly** as defined in `specs/02_architecture.md`.
5. **Use the schemas exactly** as defined in `specs/04_backend_api.md` and `specs/05_retrieval_pipeline.md`.
6. **Use the CSS variables and component tree exactly** as defined in `specs/03_frontend_ui.md`.
7. **Handle errors** according to `specs/14_error_handling.md`. Every error case in the taxonomy must be handled.
8. **Write tests** alongside each component per `specs/13_testing_strategy.md`.

## Implementation Order

Follow this exact order (from `00_spec_index.md`):

### Phase 1: Foundation
1. Read ALL specs thoroughly (00–14).
2. Initialize project skeleton matching the directory structure in `specs/02_architecture.md`.
3. Create `requirements.txt` from `specs/10_deployment.md`.
4. Create `.env.example` from `specs/11_environment_config.md`.
5. Set up `Settings` config class from `specs/11_environment_config.md`.

### Phase 2: Data Layer
6. Generate `articles.json` (200 articles) per `specs/12_data_generation.md`.
7. Implement chunking logic per `specs/08_data_model_and_chroma.md`.
8. Implement `EmbeddingService` per `specs/07_embedding_service.md`.
9. Implement `ChromaStore` with seeding per `specs/08_data_model_and_chroma.md`.
10. Implement `BM25Index` per `specs/05_retrieval_pipeline.md` (BM25 section).

### Phase 3: Retrieval Pipeline
11. Implement `QueryRouter` per `specs/05_retrieval_pipeline.md` (QueryRouter section).
12. Implement `rrf_fuse()` per `specs/05_retrieval_pipeline.md` (RRF section).
13. Implement metadata filter extraction per `specs/05_retrieval_pipeline.md` (Metadata section).
14. Implement `RetrievalManager` per `specs/05_retrieval_pipeline.md` (full orchestration).
15. Implement `LogBuffer` per `specs/05_retrieval_pipeline.md` (logging section).

### Phase 4: LLM & API
16. Implement `LLMClient` per `specs/06_llm_integration.md`.
17. Implement prompt construction per `specs/06_llm_integration.md` (prompt template section).
18. Implement API routes (`/query` SSE, `/embed`, `/health`) per `specs/04_backend_api.md`.
19. Implement FastAPI app with lifespan startup per `specs/02_architecture.md` + `specs/14_error_handling.md`.

### Phase 5: Frontend
20. Initialize Vue 3 + Vite project per `specs/02_architecture.md`.
21. Create CSS design system (variables, glassmorphism, typography) per `specs/03_frontend_ui.md`.
22. Build all composables (`useChat`, `useFeatures`, `useMetrics`, `useLogs`, `useChunks`) per `specs/03_frontend_ui.md`.
23. Build component tree per `specs/03_frontend_ui.md` (Component Tree section).
24. Wire SSE streaming per `specs/03_frontend_ui.md` (SSE lifecycle section) + `specs/04_backend_api.md`.

### Phase 6: Polish & Deploy
25. Implement comparison mode per `specs/09_feature_proofs.md` (baseline protocol).
26. Add responsive layout and animations per `specs/03_frontend_ui.md`.
27. Write tests per `specs/13_testing_strategy.md`.
28. Create Dockerfile per `specs/10_deployment.md`.
29. Verify all 7 feature proofs per `specs/09_feature_proofs.md` (demo queries table).

## Key Constraints
- CPU only, no GPU, 16GB RAM max.
- All components in a single Docker container.
- Cerebras API for LLM (free tier via `CEREBRAS_API_KEY`).
- `all-MiniLM-L6-v2` for embeddings (local CPU).
- Chroma for vector storage, BM25 for sparse retrieval.
- Must run on free Hugging Face Spaces.

## Start Now
Begin by reading `specs/00_spec_index.md`, then proceed to Phase 1, Step 1. After reading all specs, set up the project skeleton. Track progress using a task checklist. Do NOT skip steps.
```

---

## Usage

1. Open a **new chat session**.
2. Paste the prompt above.
3. The agent will read all specs, then build the project step by step.
4. Each step references specific spec files, ensuring traceability.

> **Tip**: If you want to tackle it in stages, you can paste only the phases you want (e.g., "Do Phase 1 and Phase 2 only") and continue in follow-up sessions.
