# Decision Log

This document records key architectural and implementation decisions made during development.

## D1: Hybrid Scoring Normalization (2024-03-12)

**Decision**: Implement both min-max and z-score normalization for score fusion

**Context**: BM25 scores (range ~0-50) and vector cosine similarity (range 0-1) need normalization before combining

**Options Considered**:
1. Min-max only
2. Z-score only
3. Both with configurable selection

**Choice**: Option 3 - Both methods, min-max as default

**Rationale**:
- Min-max is intuitive and preserves relative ordering
- Maps both score types to [0, 1] range uniformly
- Z-score better handles outliers but can produce negative values
- Providing both allows experimentation
- Default to min-max for simplicity and interpretability

**Implementation**: `HybridSearch.normalize_scores_minmax()` and `normalize_scores_zscore()`

**Validation**: Testing with edge cases (all scores equal, single score) to ensure no division by zero

---

## D2: CPU-Only Embedding Model Selection (2024-03-12)

**Decision**: Use `all-MiniLM-L6-v2` sentence-transformers model

**Context**: Need semantic search on CPU without GPU dependency

**Options Considered**:
1. all-MiniLM-L6-v2 (384 dim, 23M params)
2. all-mpnet-base-v2 (768 dim, 110M params)
3. all-MiniLM-L12-v2 (384 dim, 34M params)

**Choice**: Option 1 - all-MiniLM-L6-v2

**Rationale**:
- Fastest inference on CPU (~100ms per query)
- Smallest model size (23M parameters)
- 384 dimensions balance expressiveness vs speed
- Excellent performance on semantic similarity tasks
- Widely adopted baseline model
- Fully reproducible on laptop CPUs

**Trade-offs**:
- Lower quality than mpnet-base-v2 but acceptable for this use case
- Sufficient for 300-document corpus

**Performance**: Query encoding ~80-120ms on modern CPU

---

## D3: Index Storage Format (2024-03-12)

**Decision**: Use pickle for BM25, FAISS binary for vectors

**Context**: Need persistent storage for indexes

**Options Considered**:
1. Pure pickle for both
2. JSON for BM25, FAISS for vectors
3. Pickle for BM25, FAISS for vectors

**Choice**: Option 3

**Rationale**:
- BM25 index (rank-bm25 library) serializes naturally with pickle
- FAISS has optimized binary format (`write_index/read_index`)
- Pickle keeps implementation simple for BM25
- FAISS format is industry standard and efficient
- Hybrid approach uses best tool for each index type

**Validation**: Startup validation checks model name + dimension match

---

## D4: Database Choice - SQLite (2024-03-12)

**Decision**: Use SQLite for query logs and metrics

**Context**: Need persistent storage for observability data

**Options Considered**:
1. SQLite
2. PostgreSQL
3. In-memory only

**Choice**: Option 1 - SQLite

**Rationale**:
- Zero-configuration: no separate database server needed
- Sufficient for single-node deployment
- ACID guarantees for data integrity
- Built into Python standard library
- File-based: easy backup and migration
- Performant for <1M query log entries

**Trade-offs**:
- Not suitable for distributed deployment (but that's out of scope)
- Write concurrency limited (acceptable for search logging)

**Schema**: `query_logs` table with indexes on timestamp and query

---

## D5: Frontend Framework - React + Vite (2024-03-12)

**Decision**: React with Vite build system

**Context**: Need interactive dashboard for KPIs and search

**Options Considered**:
1. React + Vite
2. Streamlit
3. Vanilla HTML/JS

**Choice**: Option 1 - React + Vite

**Rationale**:
- React: Component-based, widely known, excellent ecosystem
- Vite: Fast dev server, instant HMR, modern build tool
- Better UX than Streamlit for search interfaces
- Recharts for visualization
- Production-grade architecture
- Assignment prefers React over Streamlit

**Trade-offs**:
- More setup than Streamlit but better developer experience
- Requires Node.js but that's acceptable

---

## D6: API Framework - FastAPI (2024-03-12)

**Decision**: FastAPI for backend API

**Context**: Need REST API for search and metrics

**Options Considered**:
1. FastAPI
2. Flask
3. Django REST Framework

**Choice**: Option 1 - FastAPI

**Rationale**:
- Automatic OpenAPI/Swagger documentation
- Pydantic validation built-in
- Async support (future-proof)
- Type hints throughout
- Excellent performance
- Modern Python best practices
- Assignment specification recommends FastAPI

**Implementation**: Request/response models with Pydantic

---

## D7: Evaluation Metrics Implementation (2024-03-12)

**Decision**: Implement nDCG, Recall, MRR from scratch

**Context**: Need evaluation harness for search quality

**Options Considered**:
1. Implement from scratch
2. Use ranx or ir_measures library
3. Use scikit-learn

**Choice**: Option 1 - Custom implementation

**Rationale**:
- Educational value - demonstrates understanding
- No external library for specific IR metrics needed
- nDCG formula is straightforward
- Full control over implementation
- Assignment validates implementation skill
- Easier to debug and customize

**Formulas Used**:
```
DCG@k = rel[0] + Σ(rel[i] / log2(i+2))
nDCG@k = DCG@k / IDCG@k
Recall@k = |retrieved ∩ relevant| / |relevant|
MRR@k = 1 / rank_first_relevant
```

---

## D8: Zero-Division Protection in Normalization (2024-03-12)

**Decision**: Return uniform scores when normalization would divide by zero

**Context**: Edge cases: all scores equal, or single result

**Implementation**:
```python
if max_score == min_score:
    return [1.0] * len(scores)  # All equally "good"
    
if std == 0:
    return [0.0] * len(scores)  # No variance
```

**Rationale**:
- Prevents runtime errors
- Sensible defaults: equal scores → all 1.0 for min-max
- Tested in unit tests with toy corpus
- Production-ready error handling

---

## D9: Snippet Extraction Strategy (2024-03-12)

**Decision**: Simple context window around first query term match

**Context**: Need text snippets for search results

**Options Considered**:
1. Context window around first match
2. BM25-based passage scoring
3. No snippets, show full text

**Choice**: Option 1 - Context window

**Rationale**:
- Simple and fast
- Sufficient for UI preview
- No additional dependencies
- 100 chars before/after match gives good context
- Graceful fallback if no match (show beginning)

**Implementation**: `HybridSearch.get_highlight_snippet()`

---

## D10: Index Validation on Startup (2024-03-12)

**Decision**: Validate model name and dimension match on index load

**Context**: Prevent dimension mismatch errors at query time

**Implementation**:
```python
if metadata['model_name'] != self.model_name:
    raise ValueError("Model mismatch")
if metadata['dimension'] != self.dimension:
    raise ValueError("Dimension mismatch")
```

**Rationale**:
- Fail fast at startup, not during queries
- Clear error messages for debugging
- Prevents silent correctness issues
- Assignment requires error induction/recovery - this addresses it

**User Experience**: Startup fails with clear message if index incompatible

---

## Summary

These decisions prioritize:
1. **Reproducibility**: CPU-only, no external services
2. **Simplicity**: Sqlite, pickle, straightforward algorithms
3. **Observability**: Structured logs, metrics, evaluation
4. **Production-ready patterns**: Validation, error handling, testing
5. **Assignment compliance**: FastAPI, React, hybrid search, evaluation

All choices documented here are validated through unit tests and end-to-end testing.
