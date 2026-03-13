"""Generate evaluation queries and relevance judgments"""

import json
from pathlib import Path

# Evaluation queries with expected relevant documents
EVAL_QUERIES = [
    {
        "query_id": "q001",
        "query": "machine learning basics",
        "relevant_docs": ["doc_0001", "doc_0002", "doc_0003"]  # ML, Neural Networks, NLP
    },
    {
        "query_id": "q002",
        "query": "neural networks deep learning",
        "relevant_docs": ["doc_0002", "doc_0001", "doc_0003"]
    },
    {
        "query_id": "q003",
        "query": "natural language processing",
        "relevant_docs": ["doc_0003", "doc_0001", "doc_0005"]
    },
    {
        "query_id": "q004",
        "query": "information retrieval search",
        "relevant_docs": ["doc_0004", "doc_0005", "doc_0006"]
    },
    {
        "query_id": "q005",
        "query": "vector embeddings semantic search",
        "relevant_docs": ["doc_0005", "doc_0006", "doc_0004"]
    },
    {
        "query_id": "q006",
        "query": "hybrid search BM25",
        "relevant_docs": ["doc_0006", "doc_0004", "doc_0005"]
    },
    {
        "query_id": "q007",
        "query": "evaluation metrics nDCG",
        "relevant_docs": ["doc_0007", "doc_0004", "doc_0006"]
    },
    {
        "query_id": "q008",
        "query": "database indexing",
        "relevant_docs": ["doc_0008", "doc_0004"]
    },
    {
        "query_id": "q009",
        "query": "API design REST",
        "relevant_docs": ["doc_0009", "doc_0010"]
    },
    {
        "query_id": "q010",
        "query": "web application architecture",
        "relevant_docs": ["doc_0010", "doc_0009"]
    },
    {
        "query_id": "q011",
        "query": "python programming",
        "relevant_docs": ["doc_0011", "doc_0012", "doc_0013"]
    },
    {
        "query_id": "q012",
        "query": "python data structures lists",
        "relevant_docs": ["doc_0012", "doc_0011"]
    },
    {
        "query_id": "q013",
        "query": "python functions decorators",
        "relevant_docs": ["doc_0013", "doc_0011"]
    },
    {
        "query_id": "q014",
        "query": "sorting algorithms quicksort",
        "relevant_docs": ["doc_0014", "doc_0015", "doc_0016"]
    },
    {
        "query_id": "q015",
        "query": "graph algorithms BFS DFS",
        "relevant_docs": ["doc_0015", "doc_0014"]
    },
    {
        "query_id": "q016",
        "query": "dynamic programming",
        "relevant_docs": ["doc_0016", "doc_0014", "doc_0015"]
    },
    {
        "query_id": "q017",
        "query": "data preprocessing machine learning",
        "relevant_docs": ["doc_0017", "doc_0001", "doc_0018"]
    },
    {
        "query_id": "q018",
        "query": "supervised learning classification",
        "relevant_docs": ["doc_0018", "doc_0017", "doc_0001"]
    },
    {
        "query_id": "q019",
        "query": "unsupervised learning clustering",
        "relevant_docs": ["doc_0019", "doc_0018", "doc_0001"]
    },
    {
        "query_id": "q020",
        "query": "HTML semantic web",
        "relevant_docs": ["doc_0020", "doc_0021", "doc_0022"]
    },
    {
        "query_id": "q021",
        "query": "CSS flexbox grid",
        "relevant_docs": ["doc_0021", "doc_0020"]
    },
    {
        "query_id": "q022",
        "query": "JavaScript DOM events",
        "relevant_docs": ["doc_0022", "doc_0020", "doc_0021"]
    },
    {
        "query_id": "q023",
        "query": "web security SQL injection XSS",
        "relevant_docs": ["doc_0023", "doc_0024", "doc_0025"]
    },
    {
        "query_id": "q024",
        "query": "authentication password hashing",
        "relevant_docs": ["doc_0024", "doc_0023"]
    },
    {
        "query_id": "q025",
        "query": "encryption TLS SSL",
        "relevant_docs": ["doc_0025", "doc_0024", "doc_0023"]
    }
]

def generate_eval_data():
    """Generate queries.jsonl and qrels.json"""
    
    # Create output directory
    output_dir = Path("data/eval")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write queries
    queries_file = output_dir / "queries.jsonl"
    with open(queries_file, 'w') as f:
        for q in EVAL_QUERIES:
            f.write(json.dumps({
                "query_id": q["query_id"],
                "query": q["query"]
            }) + '\n')
    
    # Generate qrels (relevance judgments)
    # Format: {query_id: {doc_id: relevance_score}}
    # Using graded relevance: 3 = highly relevant, 2 = relevant, 1 = marginally relevant
    qrels = {}
    for q in EVAL_QUERIES:
        query_id = q["query_id"]
        qrels[query_id] = {}
        
        for i, doc_id in enumerate(q["relevant_docs"]):
            # First doc gets highest relevance
            if i == 0:
                qrels[query_id][doc_id] = 3.0
            elif i == 1:
                qrels[query_id][doc_id] = 2.0
            else:
                qrels[query_id][doc_id] = 1.0
    
    # Write qrels
    qrels_file = output_dir / "qrels.json"
    with open(qrels_file, 'w') as f:
        json.dump(qrels, f, indent=2)
    
    print(f"Generated {len(EVAL_QUERIES)} evaluation queries")
    print(f"  Queries: {queries_file}")
    print(f"  Qrels: {qrels_file}")

if __name__ == "__main__":
    generate_eval_data()
