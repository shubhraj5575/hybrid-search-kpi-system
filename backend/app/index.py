"""
Indexing pipeline - builds BM25 and vector indexes
Usage: python -m app.index --input data/processed/docs.jsonl
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
import hashlib
from app.search.bm25 import BM25Index
from app.search.vector import VectorIndex


def build_indexes(input_file: str, bm25_dir: str, vector_dir: str, model_name: str) -> None:
    """Build both BM25 and vector indexes from JSONL corpus"""
    
    # Load documents
    documents = []
    with open(input_file, 'r') as f:
        for line in f:
            documents.append(json.loads(line))
    
    print(f"Loaded {len(documents)} documents")
    
    # Generate corpus hash
    corpus_hash = hashlib.sha256(
        ''.join(sorted(d['doc_id'] for d in documents)).encode()
    ).hexdigest()[:16]
    
    # Build BM25 index
    print("\nBuilding BM25 index...")
    bm25_index = BM25Index()
    bm25_index.build(documents, text_fields=['title', 'text'])
    bm25_index.save(bm25_dir)
    
    # Build vector index
    print("\nBuilding vector index...")
    vector_index = VectorIndex(model_name=model_name)
    vector_index.build(documents, text_fields=['title', 'text'])
    vector_index.save(vector_dir)
    
    # Save index metadata for validation
    metadata = {
        'corpus_hash': corpus_hash,
        'num_documents': len(documents),
        'embedding_model': model_name,
        'embedding_dimension': vector_index.dimension,
        'build_timestamp': datetime.now().isoformat(),
        'bm25_dir': bm25_dir,
        'vector_dir': vector_dir
    }
    
    metadata_file = Path("data/index/metadata.json")
    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nIndexing complete!")
    print(f"  Corpus hash: {corpus_hash}")
    print(f"  Embedding model: {model_name}")
    print(f"  Dimension: {vector_index.dimension}")
    print(f"  Metadata: {metadata_file}")


def main():
    parser = argparse.ArgumentParser(description="Build search indexes")
    parser.add_argument(
        "--input",
        default="data/processed/docs.jsonl",
        help="Input JSONL file"
    )
    parser.add_argument(
        "--bm25-dir",
        default="data/index/bm25",
        help="Output directory for BM25 index"
    )
    parser.add_argument(
        "--vector-dir",
        default="data/index/vector",
        help="Output directory for vector index"
    )
    parser.add_argument(
        "--model",
        default="all-MiniLM-L6-v2",
        help="Sentence transformer model name"
    )
    
    args = parser.parse_args()
    
    build_indexes(args.input, args.bm25_dir, args.vector_dir, args.model)


if __name__ == "__main__":
    main()
