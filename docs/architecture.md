# System Architecture

## Overview

The Hybrid Search + KPI Dashboard system is a three-tier application:

1. **Frontend**: React SPA with real-time KPI visualization
2. **Backend**: FastAPI REST API with search and metrics endpoints
3. **Data Layer**: File-based indexes (BM25 + Vector) + SQLite logs

```
┌──────────────────────────────────────────────────────────────┐
│                     Browser (User)                            │
└──────────────────┬───────────────────────────────────────────┘
                   │ HTTP/JSON
┌──────────────────▼───────────────────────────────────────────┐
│                 React Frontend (Port 3000)                    │
│  • SearchPage: Query UI with controls                        │
│  • KPIPage: Latency metrics, top queries                     │
│  • EvaluationPage: nDCG trends, experiments table            │
└──────────────────┬───────────────────────────────────────────┘
                   │ Vite Proxy → Backend
┌──────────────────▼───────────────────────────────────────────┐
│                FastAPI Backend (Port 8000)                    │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Endpoints                                             │  │
│  │  • POST /search → HybridSearch.search()               │  │
│  │  • GET /health → Index metadata + version             │  │
│  │  • GET /metrics → Prometheus format                   │  │
│  │  • GET /api/stats → Dashboard JSON                    │  │
│  │  • GET /api/experiments → CSV results                 │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Search Engine (Hybrid)                                │  │
│  │  ┌──────────────┐         ┌──────────────┐            │  │
│  │  │ BM25Index    │         │ VectorIndex  │            │  │
│  │  │ (Lexical)    │         │ (Semantic)   │            │  │
│  │  │              │         │              │            │  │
│  │  │ rank-bm25    │         │ sentence-    │            │  │
│  │  │ Tokenizer    │         │ transformers │            │  │
│  │  │ Inverted idx │         │ + FAISS CPU  │            │  │
│  │  └──────┬───────┘         └──────┬───────┘            │  │
│  │         │                        │                     │  │
│  │         └────────┬───────────────┘                     │  │
│  │                  │                                     │  │
│  │         ┌────────▼─────────┐                          │  │
│  │         │  HybridSearch    │                          │  │
│  │         │  • Normalize     │                          │  │
│  │         │  • Fuse (alpha)  │                          │  │
│  │         │  • Rank          │                          │  │
│  │         └──────────────────┘                          │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Database (SQLite)                                     │  │
│  │  • query_logs: request tracking                       │  │
│  │  • Latency p50/p95/p99                                │  │
│  │  • Top queries, zero-result queries                   │  │
│  └────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
                   │
                   │ File I/O
                   ▼
┌──────────────────────────────────────────────────────────────┐
│                      Data Layer                               │
│  • data/index/bm25/       - BM25 index (pickle)              │
│  • data/index/vector/     - FAISS index + metadata           │
│  • data/processed/        - JSONL corpus                     │
│  • data/metrics/app.db    - SQLite database                  │
│  • data/metrics/experiments.csv - Eval results               │
└──────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Data Ingestion (`backend/app/ingest.py`)

**Purpose**: Convert raw text files to normalized JSONL format

**Input**: Directory of .txt/.md files

**Output**: `data/processed/docs.jsonl` with schema:
```json
{
  "doc_id": "doc_0001",
  "title": "Document Title",
  "text": "Full text content...",
  "source": "source_name",
  "created_at": "2024-03-12T10:30:00"
}
```

**Processing**:
- Parse metadata from file headers (Title, Source, Date)
- Clean whitespace
- Handle long documents (truncate to 10K chars)
- Generate corpus hash for validation

---

### 2. Indexing (`backend/app/index.py`)

**Purpose**: Build BM25 and vector indexes from JSONL corpus

**BM25 Index**:
- Library: `rank-bm25` (pure Python, CPU)
- Tokenization: Whitespace + lowercase
- Indexed fields: title + text (concatenated)
- Storage: Pickle format in `data/index/bm25/`

**Vector Index**:
- Library: `sentence-transformers` + FAISS
- Model: `all-MiniLM-L6-v2` (384 dim, 23M params)
- Batch encoding: 32 docs at a time
- Normalization: L2 for cosine similarity
- Storage: FAISS binary + pickle metadata in `data/index/vector/`

**Metadata File** (`data/index/metadata.json`):
```json
{
  "corpus_hash": "abc123...",
  "num_documents": 310,
  "embedding_model": "all-MiniLM-L6-v2",
  "embedding_dimension": 384,
  "build_timestamp": "2024-03-12T15:00:00",
  "bm25_dir": "data/index/bm25",
  "vector_dir": "data/index/vector"
}
```

---

### 3. Search Components

#### BM25Index (`backend/app/search/bm25.py`)

**Methods**:
- `build(documents, text_fields)`: Create inverted index
- `query(query_text, top_k)`: Return (doc_id, score) tuples
- `save/load(dir)`: Persist with pickle
- `get_document(doc_id)`: Retrieve full document

**Scoring**: BM25 Okapi formula (standard parameterization)

#### VectorIndex (`backend/app/search/vector.py`)

**Methods**:
- `build(documents, text_fields)`: Encode + index embeddings
- `query(query_text, top_k)`: Cosine similarity search
- `save/load(dir)`: FAISS write_index + metadata
- `get_document(doc_id)`: Retrieve full document

**Validation on Load**:
- Check model name matches
- Check embedding dimension matches
- Fail fast if mismatch

#### HybridSearch (`backend/app/search/hybrid.py`)

**Scoring Formula**:
```
norm_bm25 = normalize(bm25_scores, method)
norm_vector = normalize(vector_scores, method)
hybrid = alpha * norm_bm25 + (1 - alpha) * norm_vector
```

**Normalization Methods**:

1. **Min-Max** (default):
   ```
   norm(x) = (x - min) / (max - min)
   Range: [0, 1]
   Edge case: if max == min, return [1.0] * len
   ```

2. **Z-Score**:
   ```
   norm(x) = (x - mean) / std
   Range: [-∞, +∞] (typically [-3, +3])
   Edge case: if std == 0, return [0.0] * len
   ```

**Why Min-Max Default**:
- Bounded output [0,1]
- Preserves relative ordering
- Intuitive interpretation
- Works well with alpha blending

**Retrieval Strategy**:
- Fetch top_k * 3 from each index
- Ensures good coverage after fusion
- Re-rank by hybrid score
- Return top_k final results

---

### 4. API Layer (`backend/app/main.py`)

**Framework**: FastAPI with Uvicorn ASGI server

**Request Flow**:
```
1. Client sends POST /search
2. Pydantic validates request (SearchRequest model)
3. Generate request_id (UUID)
4. Start timer
5. Call HybridSearch.search()
6. Add snippets to results
7. Stop timer, calculate latency
8. Log to database (async)
9. Return SearchResponse with results + latency
```

**Error Handling**:
- Invalid parameters → 400 Bad Request
- Search engine not ready → 503 Service Unavailable
- Internal errors → 500 with error logged

**Startup Validation**:
```python
@app.on_event("startup")
async def startup_event():
    # Load metadata
    # Load BM25 index
    # Load vector index
    # Validate doc_ids match between indexes
    # Initialize database connection
```

---

### 5. Database Schema (`backend/app/db/models.py`)

**QueryLog Table**:
```sql
CREATE TABLE query_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT UNIQUE NOT NULL,  -- UUID for tracing
    query TEXT NOT NULL,               -- Search query
    top_k INTEGER,                     -- Requested result count
    alpha REAL,                        -- BM25 weight
    normalization TEXT,                -- minmax or zscore
    result_count INTEGER,              -- Actual results returned
    latency_ms REAL,                   -- Response time
    error TEXT,                        -- Error message if failed
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_query_logs_timestamp ON query_logs(timestamp);
CREATE INDEX idx_query_logs_query ON query_logs(query);
CREATE INDEX idx_query_logs_latency ON query_logs(latency_ms);
CREATE INDEX idx_query_logs_request_id ON query_logs(request_id);
```

**Queries**:
- `get_latency_stats()`: Percentiles (p50, p95, p99) + mean/min/max
- `get_top_queries(limit)`: GROUP BY query, ORDER BY count DESC
- `get_zero_result_queries(limit)`: WHERE result_count = 0
- `get_query_stats(limit)`: Recent queries for time-series viz

---

### 6. Evaluation (`backend/app/eval.py`)

**Metrics**:

1. **nDCG@10** (Normalized Discounted Cumulative Gain):
   ```
   DCG@k = rel[0] + Σ(rel[i] / log2(i+2)) for i in 1..k-1
   nDCG@k = DCG@k / IDCG@k
   ```
   - Accounts for graded relevance (3=highly, 2=relevant, 1=marginal)
   - Position-aware (higher-ranked results weighted more)

2. **Recall@10**:
   ```
   Recall@k = |retrieved ∩ relevant| / |relevant|
   ```
   - Fraction of relevant docs found in top-k

3. **MRR@10** (Mean Reciprocal Rank):
   ```
   MRR@k = 1 / rank_of_first_relevant
   ```
   - Rewards finding relevant result quickly

**Evaluation Dataset**:
- 25 queries (`data/eval/queries.jsonl`)
- Graded qrels (`data/eval/qrels.json`)
- Covers: ML, algorithms, web dev, security topics

**Experiment Workflow**:
```bash
python -m backend.app.eval --alpha 0.5 --normalization minmax
# Appends row to data/metrics/experiments.csv
```

**CSV Schema**:
```
timestamp,git_commit,alpha,normalization,embedding_model,ndcg@10,recall@10,mrr@10,num_queries
```

---

### 7. Frontend Dashboard

**Tech Stack**:
- React 18 (hooks-based components)
- Vite (dev server + build)
- Recharts (charts)
- Axios (HTTP client)

**Pages**:

1. **SearchPage** (`frontend/src/components/SearchPage.jsx`):
   - Query input with live controls (top_k, alpha, normalization)
   - Result cards with score breakdown
   - Latency display

2. **KPIPage** (`frontend/src/components/KPIPage.jsx`):
   - Latency stats (p50/p95/p99)
   - Top queries by frequency
   - Zero-result queries
   - Recent latency time-series chart

3. **EvaluationPage** (`frontend/src/components/EvaluationPage.jsx`):
   - nDCG/Recall/MRR trend line chart
   - Experiment table with parameters + metrics
   - Sortable by timestamp

**Data Refresh**:
- KPIs auto-refresh every 5 seconds
- Experiments loaded on page mount (static)

---

## Data Flow Examples

### Search Request Flow

```
1. User types query "machine learning" in UI
2. Frontend: POST /search {query, top_k:10, alpha:0.5, normalization:"minmax"}
3. Backend: Validate request with Pydantic
4. Backend: Generate UUID request_id
5. Backend: Call BM25Index.query("machine learning", 30)
   → Returns [(doc_0001, 8.5), (doc_0003, 7.2), ...]
6. Backend: Call VectorIndex.query("machine learning", 30)
   → Returns [(doc_0001, 0.92), (doc_0002, 0.87), ...]
7. Backend: HybridSearch normalizes scores
   → BM25: [1.0, 0.85, ...] (min-max)
   → Vector: [1.0, 0.95, ...] (min-max)
8. Backend: Compute hybrid scores
   → hybrid[i] = 0.5 * bm25_norm[i] + 0.5 * vector_norm[i]
9. Backend: Sort by hybrid score, take top 10
10. Backend: Add snippets with get_highlight_snippet()
11. Backend: Record latency, log to SQLite
12. Backend: Return JSON with results
13. Frontend: Render result cards
```

### Evaluation Flow

```
1. Run: python -m backend.app.eval --alpha 0.6
2. Load queries from data/eval/queries.jsonl
3. Load qrels from data/eval/qrels.json
4. For each query:
   a. Call HybridSearch.search(query, k=10, alpha=0.6)
   b. Extract relevances for retrieved docs from qrels
   c. Calculate nDCG@10, Recall@10, MRR@10
5. Average metrics across all queries
6. Get git commit hash
7. Append row to data/metrics/experiments.csv
8. Print results to console
```

---

## Deployment Considerations

### Single-Node Design
- All components run on one machine
- SQLite for simplicity (not distributed)
- File-based indexes (no remote storage)

### Scaling Approaches (Future)
- **Horizontal**: Shard corpus across multiple index nodes
- **Vertical**: Larger embedding models (GPU required)
- **Caching**: Redis for query result cache
- **Database**: PostgreSQL for multi-write concurrency

### Resource Requirements
- **RAM**: 2-4GB (indexes in memory)
- **CPU**: 4 cores recommended (parallel encoding)
- **Disk**: ~500MB for indexes + corpus
- **Network**: Local only (no external dependencies)

---

## Security & Production Hardening

### Implemented
- ✅ Input validation (Pydantic schemas)
- ✅ Structured error logging
- ✅ CORS middleware (configurable)

### TODO for Production
- ⚠️ Authentication (OAuth2 / API keys)
- ⚠️ Rate limiting (token bucket)
- ⚠️ HTTPS/TLS termination
- ⚠️ Index encryption at rest
- ⚠️ Audit logging
- ⚠️ Health check probes (liveness/readiness)

---

## Monitoring & Observability

**Current State**:
- Structured JSON logs (request_id, latency, query, error)
- Prometheus-compatible /metrics endpoint
- SQLite query logs with p50/p95/p99 tracking

**Production Additions**:
- Export metrics to Prometheus/Grafana
- Distributed tracing (OpenTelemetry)
- Centralized logging (ELK/Loki)
- Alerting on error rate / latency SLOs

---

## Technology Choices Recap

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Backend | FastAPI | Modern, async, automatic docs |
| BM25 | rank-bm25 | Pure Python, CPU-only |
| Vectors | sentence-transformers | State-of-art embeddings |
| Vector Search | FAISS CPU | Industry standard, exact search |
| Database | SQLite | Zero-config, ACID, sufficient |
| Frontend | React + Vite | Component-based, fast HMR |
| Charts | Recharts | Simple, responsive |
| Packaging | requirements.txt | Standard, reproducible |

All choices prioritize **CPU-only** execution and **single-command reproducibility**.
