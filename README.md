# Hybrid Search + KPI Dashboard System

End-to-end search system combining BM25 lexical search with semantic vector search, featuring a real-time KPI dashboard and comprehensive evaluation harness.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  Search UI • KPI Dashboard • Evaluation Viewer              │
└────────────┬────────────────────────────────────────────────┘
             │ HTTP/JSON
┌────────────▼────────────────────────────────────────────────┐
│                   FastAPI Backend                            │
│  /search • /health • /metrics • /api/*                      │
└────────────┬────────────────────────────────────────────────┘
             │
      ┌──────┴──────┐
      │             │
┌─────▼─────┐ ┌────▼────────┐
│ BM25      │ │ Vector      │
│ (Lexical) │ │ (Semantic)  │
└───────────┘ └─────────────┘
      │             │
      └──────┬──────┘
       ┌─────▼─────────┐
       │ Hybrid Scorer │
       │  (α weighted) │
       └───────────────┘
```

### Components

- **BM25 Index**: Lexical search using rank-bm25
- **Vector Index**: Semantic search using sentence-transformers + FAISS (CPU)
- **Hybrid Search**: Configurable score fusion with normalization
- **API**: FastAPI with structured logging and metrics
- **Dashboard**: React UI with real-time KPIs and evaluation trends
- **Database**: SQLite for query logs and metrics
- **Evaluation**: nDCG@10, Recall@10, MRR@10 on labeled queries

## 🚀 1-Minute Quickstart

### Prerequisites

- Python 3.11+
- Node.js 16+ (for frontend)
- 4GB RAM minimum
- Git

### Run

```bash
git clone <repo-url>
cd hybrid-search-kpi-system
./up.sh
```

This single command:
1. Creates Python virtual environment
2. Installs all dependencies
3. Generates sample corpus (310 documents)
4. Builds BM25 + vector indexes
5. Starts backend API (port 8000)
6. Starts frontend dashboard (port 3000)

**Access**: http://localhost:3000

**Stop**: `./down.sh` or Ctrl+C

## System Requirements

- **CPU-only**: No GPU required
- **RAM**: 2-4GB for indexes
- **Disk**: ~500MB for indexes + corpus
- **OS**: Linux or macOS (Windows via WSL)

## Usage

### Search

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning neural networks",
    "top_k": 10,
    "alpha": 0.5,
    "normalization": "minmax"
  }'
```

### Run Tests

```bash
source .venv/bin/activate
pytest backend/tests/ -v
```

### Run Evaluation

```bash
source .venv/bin/activate
python -m backend.app.eval \
  --queries data/eval/queries.jsonl \
  --qrels data/eval/qrels.json \
  --alpha 0.5 \
  --normalization minmax
```

Run multiple experiments with different parameters:

```bash
# Experiment 1: Balanced hybrid (α=0.5)
python -m backend.app.eval --alpha 0.5 --normalization minmax

# Experiment 2: BM25-heavy (α=0.7)
python -m backend.app.eval --alpha 0.7 --normalization minmax

# Experiment 3: Vector-heavy (α=0.3)
python -m backend.app.eval --alpha 0.3 --normalization minmax

# Experiment 4: Z-score normalization
python -m backend.app.eval --alpha 0.5 --normalization zscore

# Experiment 5: Pure BM25 (α=1.0)
python -m backend.app.eval --alpha 1.0 --normalization minmax
```

Results are appended to `data/metrics/experiments.csv` and visualized in the dashboard.

### Ingest Custom Data

```bash
# Place .txt or .md files in data/custom/
python -m backend.app.ingest --input data/custom --out data/processed

# Rebuild indexes
python -m backend.app.index --input data/processed/docs.jsonl

# Restart services
./down.sh && ./up.sh
```

## API Endpoints

### `GET /health`
Health check with version and commit hash

### `POST /search`
Hybrid search with score breakdown

Request:
```json
{
  "query": "string",
  "top_k": 10,
  "alpha": 0.5,
  "normalization": "minmax"
}
```

Response:
```json
{
  "results": [
    {
      "doc_id": "doc_0001",
      "title": "...",
      "text": "...",
      "bm25_score": 4.23,
      "vector_score": 0.87,
      "bm25_score_norm": 0.92,
      "vector_score_norm": 0.76,
      "hybrid_score": 0.84,
      "snippet": "..."
    }
  ],
  "latency_ms": 45.2,
  "total_results": 10
}
```

### `GET /metrics`
Prometheus-style metrics (latency percentiles, request counts)

### `GET /api/stats`
JSON stats for dashboard (latency, top queries, zero-result queries)

### `GET /api/experiments`
Evaluation experiment results

## Directory Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── search/
│   │   │   ├── bm25.py          # BM25 indexing & search
│   │   │   ├── vector.py        # Vector indexing & search
│   │   │   └── hybrid.py        # Hybrid scoring
│   │   ├── db/
│   │   │   └── models.py        # SQLite models
│   │   ├── ingest.py            # Data ingestion
│   │   ├── index.py             # Index building
│   │   ├── eval.py              # Evaluation harness
│   │   └── main.py              # FastAPI app
│   └── tests/
│       └── test_search.py       # Unit tests
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── SearchPage.jsx   # Search interface
│       │   ├── KPIPage.jsx      # KPI dashboard
│       │   └── EvaluationPage.jsx # Eval viewer
│       └── main.jsx             # React entry
├── data/
│   ├── raw/                     # Raw documents
│   ├── processed/               # JSONL corpus
│   ├── index/                   # BM25 + vector indexes
│   ├── eval/                    # Queries + qrels
│   └── metrics/                 # SQLite DB + experiments.csv
├── docs/
│   ├── architecture.md
│   ├── codex_log.md
│   ├── decision_log.md
│   └── break_fix_log.md
├── up.sh                        # Start everything
├── down.sh                      # Stop services
├── requirements.txt
└── README.md
```

## Key Design Decisions

### 1. Normalization Strategy

**Choice**: Min-max as default, with z-score option

**Rationale**: 
- BM25 and vector scores have different ranges
- Min-max maps both to [0,1], preserving relative ordering
- Z-score handles outliers better but can produce negative scores
- Both are implemented; α parameter controls fusion weight

### 2. CPU-Only Architecture

**Choice**: sentence-transformers (all-MiniLM-L6-v2) + FAISS CPU

**Rationale**:
- Embedding model: 384 dimensions, 23M parameters
- Fast on CPU: ~100ms for query encoding
- FAISS IndexFlatIP for exact cosine similarity
- No GPU dependency ensures reproducibility

### 3. Hybrid Scoring Formula

```
hybrid_score = α × norm(bm25_score) + (1-α) × norm(vector_score)
```

**Rationale**:
- α=1.0: Pure BM25 (lexical)
- α=0.0: Pure vector (semantic)
- α=0.5: Balanced hybrid (default)
- Evaluation experiments tune α for optimal nDCG@10

## Evaluation Methodology

### Dataset
- 25 queries with graded relevance (3=highly, 2=relevant, 1=marginal)
- Covers diverse topics: ML, algorithms, web dev, security
- Qrels manually curated for ground truth

### Metrics
- **nDCG@10**: Accounts for graded relevance and position
- **Recall@10**: Fraction of relevant docs retrieved
- **MRR@10**: Mean reciprocal rank of first relevant result

### Experiments
Run >= 5 experiments varying:
- α (BM25 vs vector weight)
- Normalization method
- Embedding model (if changed)

Results visualized in dashboard as trend lines.

## Production Considerations

### Implemented
- ✅ Structured JSON logging per request
- ✅ Latency tracking (p50, p95, p99)
- ✅ Request/error counting
- ✅ Index validation on startup
- ✅ Unit tests for core modules
- ✅ Input validation and rate limiting hooks

### Not Implemented (Production TODOs)
- ⚠️ Authentication/authorization
- ⚠️ Persistent rate limiting (in-memory only)
- ⚠️ Distributed deployment (single-node design)
- ⚠️ Index versioning/rollback
- ⚠️ Monitoring/alerting integration

## Troubleshooting

### "Indexes not found"
Run: `python -m backend.app.index --input data/processed/docs.jsonl`

### "Database locked"
Stop all services: `./down.sh`, then restart: `./up.sh`

### Port already in use
Change ports in `up.sh` (backend: 8000, frontend: 3000)

### Frontend not loading
Check `logs/frontend.log`, ensure Node.js 16+ installed

### Tests failing
Ensure indexes built: `./up.sh` creates them automatically

## License

Public domain / Open source (sample project)

## Author

Created for KOS Intern Assignment
