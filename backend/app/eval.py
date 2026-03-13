"""
Evaluation harness for search quality assessment
Usage: python -m app.eval --queries data/eval/queries.jsonl --qrels data/eval/qrels.json
"""

import argparse
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import numpy as np

from app.search.bm25 import BM25Index
from app.search.vector import VectorIndex
from app.search.hybrid import HybridSearch


def dcg_at_k(relevances: List[float], k: int) -> float:
    """Calculate Discounted Cumulative Gain at K"""
    relevances = relevances[:k]
    if not relevances:
        return 0.0
    
    # DCG formula: sum(rel_i / log2(i + 2)) for i in range(k)
    dcg = relevances[0] + sum(
        rel / np.log2(i + 2) for i, rel in enumerate(relevances[1:], start=1)
    )
    return dcg


def ndcg_at_k(relevances: List[float], k: int) -> float:
    """Calculate Normalized Discounted Cumulative Gain at K"""
    dcg = dcg_at_k(relevances, k)
    
    # Ideal DCG (best possible ordering)
    ideal_relevances = sorted(relevances, reverse=True)
    idcg = dcg_at_k(ideal_relevances, k)
    
    if idcg == 0:
        return 0.0
    
    return dcg / idcg


def recall_at_k(relevant_retrieved: int, total_relevant: int, k: int) -> float:
    """Calculate Recall at K"""
    if total_relevant == 0:
        return 0.0
    return relevant_retrieved / total_relevant


def mrr_at_k(rank_first_relevant: int, k: int) -> float:
    """Calculate Mean Reciprocal Rank at K"""
    if rank_first_relevant == -1 or rank_first_relevant >= k:
        return 0.0
    return 1.0 / (rank_first_relevant + 1)


def evaluate_query(
    query: str,
    qrels: Dict[str, float],
    search_engine: HybridSearch,
    k: int = 10,
    alpha: float = 0.5,
    normalization: str = "minmax"
) -> Dict:
    """
    Evaluate a single query
    
    Args:
        query: Search query
        qrels: Dict mapping doc_id to relevance score
        search_engine: HybridSearch instance
        k: Cutoff for metrics
        alpha: BM25 weight
        normalization: Score normalization method
        
    Returns:
        Dict with metrics
    """
    # Get search results
    results = search_engine.search(query, top_k=k, alpha=alpha, normalization=normalization)
    
    # Extract relevances for retrieved docs
    relevances = []
    retrieved_relevant = 0
    rank_first_relevant = -1
    
    for i, result in enumerate(results):
        doc_id = result['doc_id']
        rel = qrels.get(doc_id, 0.0)
        relevances.append(rel)
        
        if rel > 0:
            retrieved_relevant += 1
            if rank_first_relevant == -1:
                rank_first_relevant = i
    
    # Calculate metrics
    total_relevant = sum(1 for v in qrels.values() if v > 0)
    
    return {
        'ndcg@10': ndcg_at_k(relevances, k),
        'recall@10': recall_at_k(retrieved_relevant, total_relevant, k),
        'mrr@10': mrr_at_k(rank_first_relevant, k),
        'num_results': len(results),
        'num_relevant': total_relevant,
        'retrieved_relevant': retrieved_relevant
    }


def run_evaluation(
    queries_file: str,
    qrels_file: str,
    alpha: float = 0.5,
    normalization: str = "minmax",
    output_file: str = "data/metrics/experiments.csv"
) -> None:
    """Run full evaluation and save results"""
    
    # Load indexes
    print("Loading indexes...")
    metadata_path = Path("data/index/metadata.json")
    with open(metadata_path) as f:
        metadata = json.load(f)
    
    bm25_index = BM25Index()
    bm25_index.load(metadata['bm25_dir'])
    
    vector_index = VectorIndex(model_name=metadata['embedding_model'])
    vector_index.load(metadata['vector_dir'])
    
    search_engine = HybridSearch(bm25_index, vector_index)
    
    # Load queries
    queries = []
    with open(queries_file, 'r') as f:
        for line in f:
            queries.append(json.loads(line))
    
    # Load qrels
    with open(qrels_file, 'r') as f:
        qrels_data = json.load(f)
    
    print(f"Evaluating {len(queries)} queries...")
    
    # Evaluate each query
    all_metrics = []
    for query_data in queries:
        query_id = query_data['query_id']
        query_text = query_data['query']
        qrels = qrels_data.get(query_id, {})
        
        metrics = evaluate_query(
            query_text,
            qrels,
            search_engine,
            k=10,
            alpha=alpha,
            normalization=normalization
        )
        all_metrics.append(metrics)
        
        print(f"  {query_id}: nDCG@10={metrics['ndcg@10']:.3f}, Recall@10={metrics['recall@10']:.3f}")
    
    # Aggregate metrics
    avg_metrics = {
        'ndcg@10': np.mean([m['ndcg@10'] for m in all_metrics]),
        'recall@10': np.mean([m['recall@10'] for m in all_metrics]),
        'mrr@10': np.mean([m['mrr@10'] for m in all_metrics])
    }
    
    print(f"\nAverage metrics:")
    print(f"  nDCG@10: {avg_metrics['ndcg@10']:.4f}")
    print(f"  Recall@10: {avg_metrics['recall@10']:.4f}")
    print(f"  MRR@10: {avg_metrics['mrr@10']:.4f}")
    
    # Save to experiments CSV
    import subprocess
    try:
        git_commit = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True, text=True, timeout=1
        ).stdout.strip()
    except:
        git_commit = "unknown"
    
    experiment_row = {
        'timestamp': datetime.now().isoformat(),
        'git_commit': git_commit,
        'alpha': alpha,
        'normalization': normalization,
        'embedding_model': metadata['embedding_model'],
        'ndcg@10': avg_metrics['ndcg@10'],
        'recall@10': avg_metrics['recall@10'],
        'mrr@10': avg_metrics['mrr@10'],
        'num_queries': len(queries)
    }
    
    # Append to CSV
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_exists = output_path.exists()
    with open(output_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=experiment_row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(experiment_row)
    
    print(f"\nResults saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate search quality")
    parser.add_argument("--queries", default="data/eval/queries.jsonl")
    parser.add_argument("--qrels", default="data/eval/qrels.json")
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--normalization", default="minmax")
    parser.add_argument("--output", default="data/metrics/experiments.csv")
    
    args = parser.parse_args()
    
    run_evaluation(
        args.queries,
        args.qrels,
        args.alpha,
        args.normalization,
        args.output
    )


if __name__ == "__main__":
    main()
