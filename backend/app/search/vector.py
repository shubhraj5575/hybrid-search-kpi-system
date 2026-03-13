"""
Vector/semantic search implementation using sentence-transformers and FAISS
"""

import json
import pickle
from pathlib import Path
from typing import List, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss


class VectorIndex:
    """Vector index for semantic search using sentence embeddings"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize with a sentence-transformers model
        
        Args:
            model_name: HuggingFace model name (CPU-friendly default)
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = None
        self.doc_ids = []
        self.documents = []
        
    def build(self, documents: List[dict], text_fields: List[str] = None) -> None:
        """
        Build vector index from documents
        
        Args:
            documents: List of dicts with doc_id and text fields
            text_fields: Fields to embed (default: ['title', 'text'])
        """
        if text_fields is None:
            text_fields = ['title', 'text']
        
        self.documents = documents
        self.doc_ids = [doc['doc_id'] for doc in documents]
        
        # Combine fields for embedding
        texts_to_embed = []
        for doc in documents:
            combined_text = ' '.join(
                str(doc.get(field, '')) for field in text_fields
            )
            texts_to_embed.append(combined_text)
        
        print(f"Encoding {len(texts_to_embed)} documents...")
        
        # Generate embeddings (batch processing for efficiency)
        embeddings = self.model.encode(
            texts_to_embed,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # Create FAISS index (CPU)
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add to index
        self.index.add(embeddings.astype('float32'))
        
        print(f"Vector index built: {len(documents)} documents, dim={self.dimension}")
    
    def query(self, query_text: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Query the vector index
        
        Args:
            query_text: Search query
            top_k: Number of results to return
            
        Returns:
            List of (doc_id, score) tuples, sorted by score descending
        """
        if self.index is None:
            raise ValueError("Index not built. Call build() first.")
        
        # Encode query
        query_embedding = self.model.encode([query_text], convert_to_numpy=True)
        
        # Normalize for cosine similarity
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        # Convert to results
        results = [
            (self.doc_ids[idx], float(score))
            for idx, score in zip(indices[0], scores[0])
        ]
        
        return results
    
    def save(self, output_dir: str) -> None:
        """Save index to disk"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(output_path / "vector_index.faiss"))
        
        # Save metadata
        metadata = {
            'model_name': self.model_name,
            'dimension': self.dimension,
            'doc_ids': self.doc_ids
        }
        with open(output_path / "vector_metadata.pkl", 'wb') as f:
            pickle.dump(metadata, f)
        
        # Save documents
        with open(output_path / "documents.jsonl", 'w') as f:
            for doc in self.documents:
                f.write(json.dumps(doc) + '\n')
        
        print(f"Vector index saved to {output_dir}")
    
    def load(self, input_dir: str) -> None:
        """Load index from disk"""
        input_path = Path(input_dir)
        
        # Load metadata
        with open(input_path / "vector_metadata.pkl", 'rb') as f:
            metadata = pickle.load(f)
        
        # Validate model compatibility
        if metadata['model_name'] != self.model_name:
            raise ValueError(
                f"Model mismatch: index was built with {metadata['model_name']}, "
                f"but current model is {self.model_name}"
            )
        
        if metadata['dimension'] != self.dimension:
            raise ValueError(
                f"Dimension mismatch: index has dim={metadata['dimension']}, "
                f"but model has dim={self.dimension}"
            )
        
        self.doc_ids = metadata['doc_ids']
        
        # Load FAISS index
        self.index = faiss.read_index(str(input_path / "vector_index.faiss"))
        
        # Load documents
        self.documents = []
        with open(input_path / "documents.jsonl", 'r') as f:
            for line in f:
                self.documents.append(json.loads(line))
        
        print(f"Vector index loaded: {len(self.doc_ids)} documents, dim={self.dimension}")
    
    def get_document(self, doc_id: str) -> dict:
        """Retrieve document by ID"""
        for doc in self.documents:
            if doc['doc_id'] == doc_id:
                return doc
        return None
