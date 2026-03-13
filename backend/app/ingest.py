"""
Data ingestion pipeline - converts raw text files to normalized JSONL format
Usage: python -m app.ingest --input data/raw --out data/processed
"""

import argparse
import json
import os
import re
from pathlib import Path
from datetime import datetime
import hashlib


def clean_text(text: str) -> str:
    """Basic text preprocessing: whitespace cleanup"""
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def split_into_sentences(text: str) -> list[str]:
    """Simple sentence splitting for long documents"""
    # Basic sentence splitting on period, question mark, exclamation
    sentences = re.split(r'[.!?]+\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def process_document(filepath: Path, max_length: int = 10000) -> dict:
    """Process a single text file into normalized format"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse metadata from file
    lines = content.split('\n')
    title = ""
    source = ""
    created_at = datetime.now().isoformat()
    text = content
    
    # Extract metadata if present
    if lines[0].startswith("Title:"):
        title = lines[0].replace("Title:", "").strip()
        if len(lines) > 1 and lines[1].startswith("Source:"):
            source = lines[1].replace("Source:", "").strip()
        if len(lines) > 2 and lines[2].startswith("Date:"):
            created_at = lines[2].replace("Date:", "").strip()
        # Text is everything after metadata
        text = '\n'.join(lines[3:]) if len(lines) > 3 else ""
    
    # Clean and validate
    text = clean_text(text)
    
    # Handle extremely long documents
    if len(text) > max_length:
        # Truncate with warning
        sentences = split_into_sentences(text)
        text = '. '.join(sentences[:50]) + '.'  # Keep first 50 sentences
        print(f"Warning: {filepath.name} truncated from {len(content)} to {len(text)} chars")
    
    # Generate doc_id from filename
    doc_id = filepath.stem
    
    return {
        "doc_id": doc_id,
        "title": title or filepath.stem,
        "text": text,
        "source": source or "unknown",
        "created_at": created_at
    }


def ingest_corpus(input_dir: str, output_dir: str) -> None:
    """Ingest all text files from input directory and write JSONL"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all text files
    text_files = list(input_path.glob("*.txt")) + list(input_path.glob("*.md"))
    
    if not text_files:
        raise ValueError(f"No .txt or .md files found in {input_dir}")
    
    print(f"Found {len(text_files)} files to process")
    
    # Process all documents
    documents = []
    for filepath in text_files:
        try:
            doc = process_document(filepath)
            documents.append(doc)
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
            continue
    
    # Write to JSONL
    output_file = output_path / "docs.jsonl"
    with open(output_file, 'w', encoding='utf-8') as f:
        for doc in documents:
            f.write(json.dumps(doc) + '\n')
    
    # Generate corpus hash for validation
    corpus_hash = hashlib.sha256(
        ''.join(sorted(d['doc_id'] for d in documents)).encode()
    ).hexdigest()[:16]
    
    # Write metadata
    metadata = {
        "num_documents": len(documents),
        "corpus_hash": corpus_hash,
        "ingestion_time": datetime.now().isoformat(),
        "total_words": sum(len(doc['text'].split()) for doc in documents),
        "avg_doc_length": sum(len(doc['text']) for doc in documents) / len(documents) if documents else 0
    }
    
    metadata_file = output_path / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nIngestion complete:")
    print(f"  Documents: {metadata['num_documents']}")
    print(f"  Total words: {metadata['total_words']}")
    print(f"  Avg length: {metadata['avg_doc_length']:.0f} chars")
    print(f"  Corpus hash: {metadata['corpus_hash']}")
    print(f"  Output: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Ingest and normalize document corpus")
    parser.add_argument("--input", default="data/raw", help="Input directory with text files")
    parser.add_argument("--out", default="data/processed", help="Output directory for JSONL")
    args = parser.parse_args()
    
    ingest_corpus(args.input, args.out)


if __name__ == "__main__":
    main()
