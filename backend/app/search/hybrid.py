"""
Hybrid search combining BM25 (lexical) and vector (semantic) search
"""

from typing import List, Dict, Tuple
import numpy as np
from .bm25 import BM25Index
from .vector import VectorIndex


class HybridSearch:
    """Combines BM25 and vector search with configurable scoring"""
    
    def __init__(self, bm25_index: BM25Index, vector_index: VectorIndex):
        self.bm25_index = bm25_index
        self.vector_index = vector_index
        
    def normalize_scores_minmax(self, scores: List[float]) -> List[float]:
        """Min-max normalization to [0, 1]"""
        if not scores or len(scores) == 1:
            return [1.0] * len(scores)
        
        scores = np.array(scores)
        min_score = scores.min()
        max_score = scores.max()
        
        if max_score == min_score:
            # All scores equal - avoid division by zero
            return [1.0] * len(scores)
        
        normalized = (scores - min_score) / (max_score - min_score)
        return normalized.tolist()
    
    def normalize_scores_zscore(self, scores: List[float]) -> List[float]:
        """Z-score normalization"""
        if not scores or len(scores) == 1:
            return [0.0] * len(scores)
        
        scores = np.array(scores)
        mean = scores.mean()
        std = scores.std()
        
        if std == 0:
            # No variance - avoid division by zero
            return [0.0] * len(scores)
        
        normalized = (scores - mean) / std
        return normalized.tolist()
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        alpha: float = 0.5,
        normalization: str = "minmax"
    ) -> List[Dict]:
        """
        Hybrid search combining BM25 and vector scores
        
        Args:
            query: Search query string
            top_k: Number of results to return
            alpha: Weight for BM25 (1-alpha for vector). Range [0,1]
            normalization: 'minmax' or 'zscore'
            
        Returns:
            List of result dicts with scores and document data
        """
        # Get more results from each index to ensure good coverage
        retrieval_k = top_k * 3
        
        # Query both indexes
        bm25_results = self.bm25_index.query(query, retrieval_k)
        vector_results = self.vector_index.query(query, retrieval_k)
        
        # Create score dictionaries
        bm25_scores = {doc_id: score for doc_id, score in bm25_results}
        vector_scores = {doc_id: score for doc_id, score in vector_results}
        
        # Get union of doc_ids
        all_doc_ids = set(bm25_scores.keys()) | set(vector_scores.keys())
        
        # Get raw scores for normalization
        bm25_raw = [bm25_scores.get(doc_id, 0.0) for doc_id in all_doc_ids]
        vector_raw = [vector_scores.get(doc_id, 0.0) for doc_id in all_doc_ids]
        
        # Normalize scores
        if normalization == "minmax":
            bm25_norm = self.normalize_scores_minmax(bm25_raw)
            vector_norm = self.normalize_scores_minmax(vector_raw)
        elif normalization == "zscore":
            bm25_norm = self.normalize_scores_zscore(bm25_raw)
            vector_norm = self.normalize_scores_zscore(vector_raw)
        else:
            raise ValueError(f"Unknown normalization: {normalization}")
        
        # Combine scores
        combined_results = []
        for idx, doc_id in enumerate(all_doc_ids):
            bm25_score_norm = bm25_norm[idx]
            vector_score_norm = vector_norm[idx]
            
            # Hybrid score
            hybrid_score = alpha * bm25_score_norm + (1 - alpha) * vector_score_norm
            
            # Get document
            doc = self.bm25_index.get_document(doc_id)
            if doc is None:
                doc = self.vector_index.get_document(doc_id)
            
            if doc:
                combined_results.append({
                    'doc_id': doc_id,
                    'title': doc.get('title', ''),
                    'text': doc.get('text', ''),
                    'source': doc.get('source', ''),
                    'bm25_score': bm25_scores.get(doc_id, 0.0),
                    'vector_score': vector_scores.get(doc_id, 0.0),
                    'bm25_score_norm': bm25_score_norm,
                    'vector_score_norm': vector_score_norm,
                    'hybrid_score': hybrid_score
                })
        
        # Sort by hybrid score
        combined_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
        
        # Return top-k
        return combined_results[:top_k]
    
    def get_highlight_snippet(self, text: str, query: str, context_window: int = 100) -> str:
        """
        Extract a snippet from text containing query terms
        
        Args:
            text: Full document text
            query: Query string
            context_window: Characters before/after match
            
        Returns:
            Highlighted snippet
        """
        query_terms = query.lower().split()
        text_lower = text.lower()
        
        # Find first occurrence of any query term
        best_pos = -1
        for term in query_terms:
            pos = text_lower.find(term)
            if pos != -1:
                if best_pos == -1 or pos < best_pos:
                    best_pos = pos
        
        if best_pos == -1:
            # No match found, return beginning
            return text[:context_window * 2] + "..."
        
        # Extract snippet with context
        start = max(0, best_pos - context_window)
        end = min(len(text), best_pos + context_window)
        
        snippet = text[start:end]
        
        # Add ellipsis
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        
        return snippet
