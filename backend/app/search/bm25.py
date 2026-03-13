"""
BM25 lexical search implementation
Provides BM25Index class for building and querying BM25 indexes
"""

import json
import pickle
from pathlib import Path
from typing import List, Tuple
from rank_bm25 import BM25Okapi
import numpy as np


class BM25Index:
    """BM25 index for lexical search"""
    
    def __init__(self):
        self.index = None
        self.doc_ids = []
        self.documents = []
        self.tokenized_corpus = []
        
    def tokenize(self, text: str) -> List[str]:
        """Simple whitespace tokenization with lowercasing"""
        return text.lower().split()
    
    def build(self, documents: List[dict], text_fields: List[str] = None) -> None:
        """
        Build BM25 index from documents
        
        Args:
            documents: List of dicts with doc_id and text fields
            text_fields: Fields to index (default: ['title', 'text'])
        """
        if text_fields is None:
            text_fields = ['title', 'text']
        
        self.documents = documents
        self.doc_ids = [doc['doc_id'] for doc in documents]
        
        # Combine specified fields for indexing
        self.tokenized_corpus = []
        for doc in documents:
            combined_text = ' '.join(
                str(doc.get(field, '')) for field in text_fields
            )
            tokens = self.tokenize(combined_text)
            self.tokenized_corpus.append(tokens)
        
        # Build BM25 index
        self.index = BM25Okapi(self.tokenized_corpus)
        
        print(f"BM25 index built: {len(documents)} documents")
    
    def query(self, query_text: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Query the BM25 index
        
        Args:
            query_text: Search query
            top_k: Number of results to return
            
        Returns:
            List of (doc_id, score) tuples, sorted by score descending
        """
        if self.index is None:
            raise ValueError("Index not built. Call build() first.")
        
        # Tokenize query
        query_tokens = self.tokenize(query_text)
        
        # Get BM25 scores
        scores = self.index.get_scores(query_tokens)
        
        # Get top-k results
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = [
            (self.doc_ids[idx], float(scores[idx]))
            for idx in top_indices
        ]
        
        return results
    
    def save(self, output_dir: str) -> None:
        """Save index to disk"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save index components
        with open(output_path / "bm25_index.pkl", 'wb') as f:
            pickle.dump({
                'index': self.index,
                'doc_ids': self.doc_ids,
                'tokenized_corpus': self.tokenized_corpus
            }, f)
        
        # Save documents for retrieval
        with open(output_path / "documents.jsonl", 'w') as f:
            for doc in self.documents:
                f.write(json.dumps(doc) + '\n')
        
        print(f"BM25 index saved to {output_dir}")
    
    def load(self, input_dir: str) -> None:
        """Load index from disk"""
        input_path = Path(input_dir)
        
        # Load index components
        with open(input_path / "bm25_index.pkl", 'rb') as f:
            data = pickle.load(f)
            self.index = data['index']
            self.doc_ids = data['doc_ids']
            self.tokenized_corpus = data['tokenized_corpus']
        
        # Load documents
        self.documents = []
        with open(input_path / "documents.jsonl", 'r') as f:
            for line in f:
                self.documents.append(json.loads(line))
        
        print(f"BM25 index loaded: {len(self.doc_ids)} documents")
    
    def get_document(self, doc_id: str) -> dict:
        """Retrieve document by ID"""
        for doc in self.documents:
            if doc['doc_id'] == doc_id:
                return doc
        return None
