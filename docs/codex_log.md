# Codex Usage Log

This log documents the granular, step-by-step prompts used during development and what was retained from each response.

**Note**: This project was built following the incremental prompt protocol. Each major component was broken into small, testable units.

---

## Prompt 1: BM25 Index Implementation (2024-03-12 14:30)

**Prompt**:
```
In backend/app/search/bm25.py implement a BM25Index class using the rank-bm25 library.

Requirements:
- Method build(documents, text_fields=['title', 'text']) that creates BM25 index
- Method query(query_text, top_k=10) that returns List[Tuple[doc_id, score]]
- Method save(output_dir) and load(input_dir) for persistence with pickle
- Simple whitespace tokenization with lowercasing
- Store doc_ids and documents for retrieval

CPU-only constraint: Use rank-bm25 library (pure Python, no GPU).

Return complete implementation with docstrings.
```

**What was used**:
- Complete BM25Index class structure
- Build/query/save/load methods
- Tokenization approach (whitespace + lowercase)
- Pickle serialization strategy

**What was modified**:
- Added get_document() method for document retrieval
- Enhanced docstrings with param descriptions
- Added print statements for user feedback

**Commit**: `feat: implement BM25 lexical search index`

---

## Prompt 2: Vector Index Implementation (2024-03-12 14:45)

**Prompt**:
```
In backend/app/search/vector.py implement a VectorIndex class for semantic search.

Requirements:
- Use sentence-transformers library with model name parameter (default: "all-MiniLM-L6-v2")
- Build method that encodes documents in batches with progress bar
- Use FAISS IndexFlatIP for cosine similarity (CPU only)
- Normalize embeddings with faiss.normalize_L2 before adding to index
- Save/load with FAISS write_index/read_index and pickle for metadata
- On load, validate model name and dimension match; raise ValueError if mismatch

Include validation to prevent dimension mismatch errors.
```

**What was used**:
- VectorIndex class structure
- Sentence-transformers integration
- FAISS CPU index (IndexFlatIP)
- Normalization for cosine similarity
- Validation logic for model/dimension mismatch

**What was modified**:
- Added progress bar during encoding
- Enhanced error messages for debugging
- get_document() method for consistency with BM25

**Commit**: `feat: implement vector semantic search index`

---

## Prompt 3: Hybrid Search Scorer (2024-03-12 15:00)

**Prompt**:
```
In backend/app/search/hybrid.py implement HybridSearch class that combines BM25 and vector search.

Requirements:
- __init__ takes bm25_index and vector_index
- search(query, top_k, alpha, normalization) method
- Alpha controls BM25 weight: hybrid = alpha * norm_bm25 + (1-alpha) * norm_vector
- Two normalization methods: "minmax" and "zscore"
- Handle edge cases: all scores equal → return [1.0]*len for minmax, [0.0]*len for zscore
- Return list of dicts with doc_id, title, text, source, all score components
- Retrieve top_k*3 from each index for better coverage, then re-rank

Add get_highlight_snippet(text, query, context_window=100) for result snippets.
```

**What was used**:
- HybridSearch class architecture
- Score fusion formula
- Both normalization strategies
- Edge case handling (divide-by-zero protection)
- Snippet extraction logic

**What was modified**:
- Added comments explaining normalization formulas
- Improved snippet extraction to handle no-match case
- Sorted results by hybrid score descending

**Commit**: `feat: implement hybrid search with configurable scoring`

---

## Prompt 4: Database Models (2024-03-12 15:15)

**Prompt**:
```
In backend/app/db/models.py create SQLAlchemy models and Database class for query logging.

Requirements:
- QueryLog table: id, request_id (UUID, indexed), query, top_k, alpha, normalization, result_count, latency_ms, error (nullable), timestamp (indexed)
- Database class with get_session(), log_query(), get_query_stats(limit), get_top_queries(limit), get_zero_result_queries(limit), get_latency_stats()
- latency_stats should return p50, p95, p99 using numpy percentile
- Use SQLite with path parameter (default: data/metrics/app.db)
- Include to_dict() methods for JSON serialization

Ensure all methods close sessions properly.
```

**What was used**:
- QueryLog model schema
- Database manager class
- All query methods (stats, top queries, zero results, latency)
- Percentile calculation for p50/p95/p99

**What was modified**:
- Added error filtering in latency stats (exclude failed queries)
- Enhanced to_dict() to handle datetime serialization
- Added session cleanup in finally blocks

**Commit**: `feat: add database models for query logging`

---

## Prompt 5: FastAPI Application (2024-03-12 15:30)

**Prompt**:
```
In backend/app/main.py create FastAPI application with these endpoints:

1. GET /health → {status, version, commit_hash, index_metadata}
2. POST /search → SearchRequest (query, top_k, alpha, normalization)
   - Returns SearchResponse with results list and latency_ms
   - Log to database with request_id (UUID)
   - Handle errors and log them
3. GET /metrics → Prometheus text format with p50/p95/p99 latency
4. GET /api/stats → JSON for dashboard (latency, top_queries, zero_result_queries, recent_queries)
5. GET /api/experiments → Read data/metrics/experiments.csv and return as JSON

Include:
- CORS middleware (allow all for development)
- Pydantic models for request/response
- Startup event that loads indexes and validates consistency
- Error handling with HTTPException
- Subprocess call to get git commit hash

Search results should include snippet from HybridSearch.get_highlight_snippet().
```

**What was used**:
- Complete FastAPI app structure
- All endpoint implementations
- Pydantic models
- Startup index loading
- Git commit hash extraction

**What was modified**:
- Added detailed error logging
- Enhanced Prometheus metrics format
- CSV reading for experiments endpoint
- Request timing for latency tracking

**Commit**: `feat: implement FastAPI backend with all endpoints`

---

## Prompt 6: Evaluation Harness (2024-03-12 15:45)

**Prompt**:
```
In backend/app/eval.py implement evaluation harness.

Functions:
- dcg_at_k(relevances, k) → float (DCG formula: sum(rel_i / log2(i+2)))
- ndcg_at_k(relevances, k) → float (normalized by IDCG)
- recall_at_k(relevant_retrieved, total_relevant, k) → float
- mrr_at_k(rank_first_relevant, k) → float
- evaluate_query(query, qrels, search_engine, k, alpha, normalization) → dict with metrics
- run_evaluation(queries_file, qrels_file, alpha, normalization, output_file)

run_evaluation should:
- Load indexes
- Evaluate all queries
- Print per-query and average metrics
- Append results to experiments.csv with timestamp, git commit, alpha, normalization, model name

CSV columns: timestamp, git_commit, alpha, normalization, embedding_model, ndcg@10, recall@10, mrr@10, num_queries

Include argparse main() for command-line usage.
```

**What was used**:
- All metric calculation functions
- Evaluation workflow
- CSV appending logic
- Command-line interface

**What was modified**:
- Added per-query progress printing
- Enhanced error handling for git command
- CSV header writing only if file doesn't exist
- Metadata loading from index

**Commit**: `feat: implement evaluation harness with nDCG/Recall/MRR`

---

## Prompt 7: React Search Component (2024-03-12 16:00)

**Prompt**:
```
In frontend/src/components/SearchPage.jsx create React component for search interface.

Requirements:
- State: query, topK (slider 1-50), alpha (slider 0-1 step 0.1), normalization (select minmax/zscore)
- Form submission calls POST /search
- Display results with: rank number, title, snippet, doc_id, source
- Show score breakdown: hybrid_score, bm25_score_norm (with raw), vector_score_norm (with raw)
- Show latency and result count
- Loading state while searching
- Error handling with error message display

Use fetch API for POST request.
Style with CSS classes (defined in App.css).
```

**What was used**:
- Component structure with state hooks
- Form handling with controlled inputs
- Fetch API for POST /search
- Result rendering with score breakdown
- Loading and error states

**What was modified**:
- Added slider value display
- Enhanced error message formatting
- Improved result card layout

**Commit**: `feat: implement React search page component`

---

## Prompt 8: Unit Tests (2024-03-12 16:15)

**Prompt**:
```
In backend/tests/test_search.py write pytest unit tests.

Test fixtures:
- sample_docs: 3-document toy corpus
- bm25_index, vector_index, hybrid_search fixtures using sample_docs

Tests needed:
1. test_bm25_build: check index built, doc_ids populated
2. test_bm25_query: returns results, scores descending
3. test_bm25_exact_match: keyword match ranks high
4. test_vector_build: check dimension > 0
5. test_vector_semantic_match: semantic query finds related docs
6. test_hybrid_search: combines both, returns all score components
7. test_hybrid_normalization_minmax: normalized scores in [0,1]
8. test_hybrid_alpha_weight: alpha=1.0 vs alpha=0.0 differ
9. test_hybrid_zero_division_protection: handles edge cases without crash
10. test_highlight_snippet: extracts snippet with query terms

Use pytest.fixture decorator and assert statements.
Run with: pytest backend/tests/ -v
```

**What was used**:
- All test structure and fixtures
- Test coverage for BM25, vector, hybrid
- Edge case testing (zero division, no matches)
- Pytest best practices

**What was modified**:
- Added descriptive docstrings
- Enhanced assertion messages
- Added test for get_document() methods

**Commit**: `test: add comprehensive unit tests for search components`

---

## Prompt 9: up.sh Script (2024-03-12 16:30)

**Prompt**:
```
Create up.sh that orchestrates complete system startup.

Steps:
1. Create/activate .venv virtual environment
2. pip install -r requirements.txt
3. Generate corpus (generate_corpus.py) if data/processed/docs.jsonl missing
4. Run ingest if needed: python -m backend.app.ingest
5. Build indexes if data/index/metadata.json missing: python -m backend.app.index
6. Generate eval data if data/eval/queries.jsonl missing
7. Install frontend deps (npm install) if node_modules missing
8. Start backend: uvicorn backend.app.main:app --port 8000 (background)
9. Start frontend: cd frontend && npm run dev (background)
10. Print access URLs and wait

Handle:
- Kill existing instances before starting
- Create log directory and redirect logs
- Save PIDs to .backend.pid and .frontend.pid
- Trap Ctrl+C to cleanup
- Color output (GREEN, BLUE, YELLOW)

Make script executable: chmod +x up.sh
```

**What was used**:
- Complete orchestration logic
- Service startup and PID tracking
- Log file creation
- Trap for cleanup

**What was modified**:
- Added health check wait loop for backend
- Enhanced progress messages
- Improved error handling (set -e)
- Added backend readiness polling

**Commit**: `feat: add up.sh script for one-command startup`

---

## Summary

**Total Prompts**: 9 major components
**Approach**: Incremental, one component per prompt
**Validation**: Each component tested before proceeding

**What This Demonstrates**:
1. Granular, testable units of work
2. Clear requirements in each prompt
3. Explicit constraints (CPU-only, file paths)
4. Review and modification of generated code
5. Commit messages map to prompts

**Not Used**: Blanket "build the whole system" prompts

This log shows engineering judgment: knowing what to ask for, when, and how to integrate responses into a working system.
