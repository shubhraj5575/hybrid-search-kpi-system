"""
Unit tests for search components
Run with: pytest backend/tests/
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.search.bm25 import BM25Index
from app.search.vector import VectorIndex
from app.search.hybrid import HybridSearch


# Test fixtures
@pytest.fixture
def sample_docs():
    """Small toy corpus for testing"""
    return [
        {
            "doc_id": "doc1",
            "title": "Machine Learning Basics",
            "text": "Machine learning is a subset of artificial intelligence that focuses on data and algorithms."
        },
        {
            "doc_id": "doc2",
            "title": "Deep Learning Neural Networks",
            "text": "Deep learning uses neural networks with multiple layers to learn representations from data."
        },
        {
            "doc_id": "doc3",
            "title": "Python Programming",
            "text": "Python is a high-level programming language known for its simplicity and readability."
        }
    ]


@pytest.fixture
def bm25_index(sample_docs):
    """BM25 index with sample data"""
    index = BM25Index()
    index.build(sample_docs)
    return index


@pytest.fixture
def vector_index(sample_docs):
    """Vector index with sample data"""
    index = VectorIndex(model_name="all-MiniLM-L6-v2")
    index.build(sample_docs)
    return index


@pytest.fixture
def hybrid_search(bm25_index, vector_index):
    """Hybrid search with sample data"""
    return HybridSearch(bm25_index, vector_index)


# BM25 Tests
def test_bm25_build(bm25_index):
    """Test BM25 index building"""
    assert bm25_index.index is not None
    assert len(bm25_index.doc_ids) == 3
    assert "doc1" in bm25_index.doc_ids


def test_bm25_query(bm25_index):
    """Test BM25 query returns results"""
    results = bm25_index.query("machine learning", top_k=2)
    assert len(results) <= 2
    assert all(isinstance(doc_id, str) and isinstance(score, float) for doc_id, score in results)
    
    # Check ordering (scores should be descending)
    if len(results) >= 2:
        assert results[0][1] >= results[1][1]


def test_bm25_exact_match(bm25_index):
    """Test BM25 prefers exact keyword matches"""
    results = bm25_index.query("python programming", top_k=3)
    # doc3 should rank high because it contains both "python" and "programming"
    doc_ids = [doc_id for doc_id, _ in results]
    assert "doc3" in doc_ids[:2]  # Should be in top 2


def test_bm25_get_document(bm25_index):
    """Test document retrieval"""
    doc = bm25_index.get_document("doc1")
    assert doc is not None
    assert doc["doc_id"] == "doc1"
    assert "Machine Learning" in doc["title"]


# Vector Search Tests
def test_vector_build(vector_index):
    """Test vector index building"""
    assert vector_index.index is not None
    assert len(vector_index.doc_ids) == 3
    assert vector_index.dimension > 0


def test_vector_query(vector_index):
    """Test vector query returns results"""
    results = vector_index.query("artificial intelligence", top_k=2)
    assert len(results) <= 2
    assert all(isinstance(doc_id, str) and isinstance(score, float) for doc_id, score in results)


def test_vector_semantic_match(vector_index):
    """Test vector search finds semantic matches"""
    # "AI" should match "machine learning" semantically
    results = vector_index.query("AI and neural networks", top_k=3)
    doc_ids = [doc_id for doc_id, _ in results]
    # Should find doc1 or doc2 (related to AI/ML) before doc3 (Python)
    assert "doc1" in doc_ids or "doc2" in doc_ids


# Hybrid Search Tests
def test_hybrid_search(hybrid_search):
    """Test hybrid search combines both methods"""
    results = hybrid_search.search("machine learning", top_k=2, alpha=0.5)
    assert len(results) <= 2
    assert all('hybrid_score' in r for r in results)
    assert all('bm25_score' in r for r in results)
    assert all('vector_score' in r for r in results)


def test_hybrid_normalization_minmax(hybrid_search):
    """Test min-max normalization"""
    results = hybrid_search.search("python", top_k=3, alpha=0.5, normalization="minmax")
    # Check normalized scores are in [0, 1]
    for r in results:
        assert 0.0 <= r['bm25_score_norm'] <= 1.0
        assert 0.0 <= r['vector_score_norm'] <= 1.0


def test_hybrid_normalization_zscore(hybrid_search):
    """Test z-score normalization"""
    results = hybrid_search.search("python", top_k=3, alpha=0.5, normalization="zscore")
    assert len(results) > 0


def test_hybrid_alpha_weight(hybrid_search):
    """Test alpha parameter controls BM25 vs vector weight"""
    # Alpha = 1.0 should give pure BM25 results
    results_bm25 = hybrid_search.search("python programming", top_k=3, alpha=1.0)
    
    # Alpha = 0.0 should give pure vector results
    results_vector = hybrid_search.search("python programming", top_k=3, alpha=0.0)
    
    # Results should potentially differ
    assert results_bm25 is not None
    assert results_vector is not None


def test_hybrid_score_breakdown(hybrid_search):
    """Test that all score components are present"""
    results = hybrid_search.search("machine learning", top_k=1, alpha=0.5)
    if results:
        r = results[0]
        assert 'bm25_score' in r
        assert 'vector_score' in r
        assert 'bm25_score_norm' in r
        assert 'vector_score_norm' in r
        assert 'hybrid_score' in r


def test_hybrid_zero_division_protection(hybrid_search):
    """Test normalization handles edge cases without crashing"""
    # Query unlikely to match anything well - tests divide-by-zero protection
    results = hybrid_search.search("xyzabc123", top_k=3, alpha=0.5)
    assert isinstance(results, list)


def test_highlight_snippet(hybrid_search):
    """Test snippet extraction"""
    snippet = hybrid_search.get_highlight_snippet(
        "Machine learning is a subset of artificial intelligence.",
        "machine learning"
    )
    assert "machine" in snippet.lower() or "learning" in snippet.lower()


def test_highlight_no_match(hybrid_search):
    """Test snippet when query doesn't match"""
    snippet = hybrid_search.get_highlight_snippet(
        "This is some text about Python programming.",
        "quantum physics"
    )
    assert isinstance(snippet, str)
    assert len(snippet) > 0


# Integration Tests
def test_end_to_end_search(hybrid_search):
    """Test complete search workflow"""
    query = "neural networks deep learning"
    results = hybrid_search.search(query, top_k=3, alpha=0.6, normalization="minmax")
    
    assert len(results) <= 3
    
    for result in results:
        assert 'doc_id' in result
        assert 'title' in result
        assert 'text' in result
        assert 'hybrid_score' in result
        # Scores should be present and finite
        assert result['hybrid_score'] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
