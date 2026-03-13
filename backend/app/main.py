"""
FastAPI application - main entry point
"""

import time
import uuid
import json
import subprocess
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.search.bm25 import BM25Index
from app.search.vector import VectorIndex
from app.search.hybrid import HybridSearch
from app.db.models import Database


# Pydantic models
class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query text")
    top_k: int = Field(10, ge=1, le=100, description="Number of results")
    alpha: float = Field(0.5, ge=0.0, le=1.0, description="BM25 weight (1-alpha for vector)")
    normalization: str = Field("minmax", description="Score normalization method")
    filters: Optional[dict] = Field(None, description="Optional filters (not implemented)")


class SearchResult(BaseModel):
    doc_id: str
    title: str
    text: str
    source: str
    bm25_score: float
    vector_score: float
    bm25_score_norm: float
    vector_score_norm: float
    hybrid_score: float
    snippet: str


class SearchResponse(BaseModel):
    results: list[SearchResult]
    query: str
    latency_ms: float
    total_results: int


class HealthResponse(BaseModel):
    status: str
    version: str
    commit_hash: str
    index_metadata: dict


# Initialize app
app = FastAPI(
    title="Hybrid Search API",
    description="BM25 + Semantic Vector Search",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
search_engine: Optional[HybridSearch] = None
db: Optional[Database] = None


def get_git_commit_hash() -> str:
    """Get current git commit hash"""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=1
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except:
        return "unknown"


@app.on_event("startup")
async def startup_event():
    """Initialize indexes and database on startup"""
    global search_engine, db
    
    print("Loading indexes...")
    
    # Initialize database
    db = Database("data/metrics/app.db")
    
    # Load index metadata
    metadata_path = Path("data/index/metadata.json")
    if not metadata_path.exists():
        print("WARNING: No index metadata found. Run indexing first.")
        return
    
    with open(metadata_path) as f:
        metadata = json.load(f)
    
    # Load BM25 index
    bm25_index = BM25Index()
    bm25_index.load(metadata['bm25_dir'])
    
    # Load vector index
    vector_index = VectorIndex(model_name=metadata['embedding_model'])
    vector_index.load(metadata['vector_dir'])
    
    # Validate consistency
    if bm25_index.doc_ids != vector_index.doc_ids:
        raise ValueError("BM25 and Vector indexes have different document sets!")
    
    # Create hybrid search
    search_engine = HybridSearch(bm25_index, vector_index)
    
    print(f"✓ Indexes loaded: {len(bm25_index.doc_ids)} documents")
    print(f"✓ Model: {metadata['embedding_model']}")
    print(f"✓ Dimension: {metadata['embedding_dimension']}")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    metadata_path = Path("data/index/metadata.json")
    metadata = {}
    
    if metadata_path.exists():
        with open(metadata_path) as f:
            metadata = json.load(f)
    
    return HealthResponse(
        status="OK" if search_engine else "NOT_READY",
        version="1.0.0",
        commit_hash=get_git_commit_hash(),
        index_metadata=metadata
    )


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Hybrid search endpoint"""
    if not search_engine:
        raise HTTPException(status_code=503, message="Search engine not initialized")
    
    request_id = str(uuid.uuid4())
    start_time = time.time()
    error = None
    
    try:
        # Validate normalization
        if request.normalization not in ['minmax', 'zscore']:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid normalization: {request.normalization}"
            )
        
        # Perform search
        results = search_engine.search(
            query=request.query,
            top_k=request.top_k,
            alpha=request.alpha,
            normalization=request.normalization
        )
        
        # Add snippets
        for result in results:
            result['snippet'] = search_engine.get_highlight_snippet(
                result['text'],
                request.query
            )
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Log to database
        db.log_query(
            request_id=request_id,
            query=request.query,
            top_k=request.top_k,
            alpha=request.alpha,
            normalization=request.normalization,
            result_count=len(results),
            latency_ms=latency_ms
        )
        
        return SearchResponse(
            results=[SearchResult(**r) for r in results],
            query=request.query,
            latency_ms=latency_ms,
            total_results=len(results)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        error = str(e)
        latency_ms = (time.time() - start_time) * 1000
        
        # Log error
        db.log_query(
            request_id=request_id,
            query=request.query,
            top_k=request.top_k,
            alpha=request.alpha,
            normalization=request.normalization,
            result_count=0,
            latency_ms=latency_ms,
            error=error
        )
        
        raise HTTPException(status_code=500, detail=error)


@app.get("/metrics")
async def get_metrics():
    """Prometheus-style metrics endpoint"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    stats = db.get_latency_stats()
    
    # Format as Prometheus text
    lines = [
        "# HELP search_requests_total Total number of search requests",
        "# TYPE search_requests_total counter",
        f"search_requests_total {stats.get('count', 0)}",
        "",
        "# HELP search_latency_seconds Search latency in seconds",
        "# TYPE search_latency_seconds summary",
        f"search_latency_seconds{{quantile=\"0.5\"}} {stats.get('p50', 0) / 1000}",
        f"search_latency_seconds{{quantile=\"0.95\"}} {stats.get('p95', 0) / 1000}",
        f"search_latency_seconds{{quantile=\"0.99\"}} {stats.get('p99', 0) / 1000}",
        f"search_latency_seconds_sum {stats.get('mean', 0) * stats.get('count', 0) / 1000}",
        f"search_latency_seconds_count {stats.get('count', 0)}",
    ]
    
    return "\n".join(lines)


@app.get("/api/stats")
async def get_stats():
    """Get query statistics for dashboard"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    return {
        'latency': db.get_latency_stats(),
        'top_queries': db.get_top_queries(10),
        'zero_result_queries': db.get_zero_result_queries(10),
        'recent_queries': db.get_query_stats(50)
    }


@app.get("/api/experiments")
async def get_experiments():
    """Get experiment results for dashboard"""
    exp_file = Path("data/metrics/experiments.csv")
    
    if not exp_file.exists():
        return {"experiments": []}
    
    import csv
    experiments = []
    with open(exp_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            experiments.append(row)
    
    return {"experiments": experiments}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
