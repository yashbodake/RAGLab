# Feature Proving Methodology

For each feature, the UI toggles and logs provide evidence:

1. **Hybrid Retrieval** – Recall@5 / MRR improve over dense‑only. Logs show RRF fusion and boosted chunks. Comparison view shows ranking shifts.
2. **Remote Embedding** – Logs show HTTP round‑trip latency; retrieved chunks identical to local.
3. **Query Understanding** – Classification badge shown; different top‑k/strategies; MRR gains for FACT/COMPARE.
4. **Metadata‑Aware** – Filtered results all share the extracted metadata; precision@5 improves.
5. **Multi‑Index** – Logs show index chosen; factual queries hit title index; MRR lift.
6. **HNSW** – Latency reduction vs flat search; recall preserved.
7. **Streaming Sources** – UI receives sources event before tokens; user sees sources immediately.

Metrics collected: retrieval_time_ms, generation_time_ms, recall@5, MRR. Baseline (all features off) stored for comparison.

---

## Detailed Feature Proofs

### Feature 1: Hybrid Retrieval (`hybrid`)

| Aspect | Baseline (off) | Enhanced (on) |
|--------|---------------|---------------|
| **Method** | Dense-only (Chroma cosine) | Dense + BM25 → RRF fusion |
| **Expected Recall@5** | ~0.60 | ~0.80 (+33%) |
| **Expected MRR** | ~0.50 | ~0.667 (+33%) |
| **Log Evidence** | `Dense search: 10 candidates` | `Dense search: 10 candidates` + `Sparse search: 10 candidates` + `RRF fusion: merged N unique → top K` |
| **UI Evidence** | Single ranked list | Chunk cards show both `dense_score` and `bm25_score` and `fused_score` |
| **Comparison View** | N/A | Side-by-side shows chunks re-ranked; previously low-ranked exact keyword matches promoted |

**Why it works:** BM25 excels at exact keyword matching (e.g., error codes like "E452"), while dense retrieval captures semantic similarity. RRF fusion combines both strengths.

---

### Feature 2: Remote Embedding (`remote_embed`)

| Aspect | Baseline (off) | Enhanced (on) |
|--------|---------------|---------------|
| **Method** | Direct `model.encode()` call | HTTP POST to self `/embed` endpoint |
| **Expected Latency** | ~10ms | ~12-15ms (HTTP overhead) |
| **Expected Recall@5** | Identical | Identical (same model) |
| **Log Evidence** | `Local embedding complete` | `Remote embedding request: 1 text(s)` + `POST .../embed → 200 in 11.7ms` |
| **UI Evidence** | No extra log entries | Embedding logs show HTTP round-trip details |

**What it demonstrates:** Proves that the system can swap between local and remote embedding services without affecting retrieval quality, validating a microservice-ready architecture.

---

### Feature 3: Query Understanding (`query_understanding`)

| Aspect | Baseline (off) | Enhanced (on) |
|--------|---------------|---------------|
| **Method** | All queries treated as FACT, top_k=5 | Classified as FACT/TOPIC/COMPARE with adaptive top_k |
| **Expected MRR (FACT)** | ~0.50 | ~0.667 (narrower top_k=3 focuses results) |
| **Expected MRR (COMPARE)** | ~0.40 | ~0.60 (sub-query splitting) |
| **Log Evidence** | `Classification: FACT (default), top_k=5` | `Classified as COMPARE, top_k=5, sub_queries: ["X", "Y"]` |
| **UI Evidence** | No badge | Classification badge (FACT/TOPIC/COMPARE) on assistant message |

**Why it works:** FACT queries benefit from fewer, more precise results. COMPARE queries benefit from splitting into sub-queries. TOPIC queries get broader coverage.

---

### Feature 4: Metadata-Aware Retrieval (`metadata_aware`)

| Aspect | Baseline (off) | Enhanced (on) |
|--------|---------------|---------------|
| **Method** | No metadata filtering | Extract entities → Chroma `where` filter + BM25 post-filter |
| **Expected Precision@5** | ~0.60 | ~0.90 (only relevant product/error code) |
| **Log Evidence** | No filter logs | `Applied filter: {"error_code": "E452"}` or `{"$and": [...]}` |
| **UI Evidence** | Mixed metadata in results | All chunk cards share the queried error code / product tag |
| **Comparison View** | Chunks from mixed products | Chunks narrowed to specific product/error |

**Why it works:** Metadata filtering eliminates irrelevant results from other products or error categories, dramatically improving precision.

---

### Feature 5: Multi-Index (`multi_index`)

| Aspect | Baseline (off) | Enhanced (on) |
|--------|---------------|---------------|
| **Method** | Always queries `docs_body` | FACT queries → `docs_title`, else `docs_body` |
| **Expected MRR (FACT)** | ~0.50 | ~0.75 (title index is more focused) |
| **Log Evidence** | `Using docs_body index` | `Using docs_title index (FACT query)` |
| **UI Evidence** | Body chunk results | Title-level results for factual questions, body for topics |

**Why it works:** Factual questions like "What is error E452?" match better against concise, descriptive titles than long body text.

---

### Feature 6: HNSW Tuning (`hnsw`)

| Aspect | Baseline (off) | Enhanced (on) |
|--------|---------------|---------------|
| **Method** | Default Chroma HNSW (search_ef=10) | Tuned HNSW (search_ef=100) |
| **Expected Latency** | ~15ms | ~12ms (better graph traversal) |
| **Expected Recall@5** | ~0.75 | ~0.80 (explores more candidates) |
| **Log Evidence** | No HNSW log | `HNSW search_ef=100 enabled` |
| **UI Evidence** | Metrics panel shows latency | Reduced retrieval_time_ms with maintained/improved recall |

**Why it works:** Higher `search_ef` explores more candidates during HNSW graph traversal, improving recall with negligible latency impact at this scale.

---

### Feature 7: Streaming Sources (`stream_sources`)

| Aspect | Baseline (off) | Enhanced (on) |
|--------|---------------|---------------|
| **Method** | Sources sent alongside first token | Sources sent before token generation starts |
| **Expected UX** | Sources appear after ~500ms (LLM first-token latency) | Sources appear immediately after retrieval (~50ms) |
| **Log Evidence** | Standard event order | `Streaming sources before generation` |
| **UI Evidence** | Chunks appear when text starts | Chunks appear instantly, then text streams in |

**What it demonstrates:** Users can inspect retrieved sources before the answer arrives, improving transparency and trust.

---

## Baseline Comparison Protocol

When `compare_with_baseline` is `true`:

1. **Enhanced run**: Execute query with all active feature flags → save results and metrics.
2. **Baseline run**: Execute same query with all features disabled (defaults to dense-only, FACT classification, top_k=5, docs_body, no filtering) → save results and metrics.
3. **Send both**: SSE emits `sources` + `baseline_sources` and `metrics` + `baseline_metrics`.
4. **UI Comparison View**: Side-by-side columns highlight:
   - Chunks that moved up or down in rank (green ↑ / red ↓ arrows).
   - Chunks present in enhanced but absent from baseline (highlighted green).
   - Metric deltas (e.g., `Recall@5: 0.60 → 0.80 (+33%)`).

## Test Queries for Demonstration

| Query | Expected Classification | Key Feature to Demo |
|-------|------------------------|-------------------|
| "How to fix error E452?" | FACT | Metadata-aware, Query understanding |
| "Explain the maintenance procedure for industrial routers" | TOPIC | Hybrid retrieval, Multi-index |
| "Difference between E452 and E501 errors" | COMPARE | Query understanding (sub-queries) |
| "Server power supply troubleshooting" | TOPIC | Hybrid (keyword "power supply" boosts BM25) |
| "What is E789?" | FACT | Multi-index (title match), Metadata filtering |
| "Compare router and switch installation procedures" | COMPARE | Query understanding, Hybrid |
| "Safety procedures for controller calibration" | TOPIC | Metadata-aware (product: controller) |