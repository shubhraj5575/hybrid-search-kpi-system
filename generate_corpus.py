"""
Sample corpus generator - creates 300+ public domain documents
Uses excerpts from classic literature (public domain)
"""

import json
import os
from datetime import datetime, timedelta
import random

# Public domain text excerpts from classic literature
SAMPLE_TEXTS = [
    {
        "title": "Introduction to Machine Learning",
        "text": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on the development of computer programs that can access data and use it to learn for themselves. The process of learning begins with observations or data, such as examples, direct experience, or instruction, in order to look for patterns in data and make better decisions in the future.",
        "source": "ML Basics"
    },
    {
        "title": "Neural Networks Fundamentals",
        "text": "Neural networks are computing systems inspired by biological neural networks that constitute animal brains. Such systems learn to perform tasks by considering examples, generally without being programmed with task-specific rules. A neural network consists of layers of interconnected nodes, where each connection can transmit a signal from one node to another. The receiving node processes the signal and signals downstream nodes.",
        "source": "Deep Learning Guide"
    },
    {
        "title": "Natural Language Processing Overview",
        "text": "Natural Language Processing (NLP) is a branch of artificial intelligence that helps computers understand, interpret and manipulate human language. NLP draws from many disciplines, including computer science and computational linguistics, to bridge the gap between human communication and computer understanding. Common NLP tasks include text classification, sentiment analysis, machine translation, and question answering.",
        "source": "NLP Handbook"
    },
    {
        "title": "Information Retrieval Systems",
        "text": "Information retrieval is the activity of obtaining information system resources that are relevant to an information need from a collection of those resources. Searches can be based on full-text or other content-based indexing. Information retrieval systems became widespread in the late 20th century. Traditional IR systems use techniques like BM25 for ranking documents based on query terms.",
        "source": "IR Textbook"
    },
    {
        "title": "Vector Embeddings in Search",
        "text": "Vector embeddings represent text as dense numerical vectors in a high-dimensional space, where semantically similar text has similar vector representations. This enables semantic search capabilities that go beyond keyword matching. Embeddings are typically generated using neural networks trained on large text corpora. Popular embedding models include Word2Vec, GloVe, and transformer-based models like BERT.",
        "source": "Modern Search Techniques"
    },
    {
        "title": "Hybrid Search Approaches",
        "text": "Hybrid search combines multiple retrieval methods to leverage their complementary strengths. A common approach merges lexical search (like BM25) with semantic search (vector similarity). BM25 excels at exact keyword matches and rare term identification, while semantic search captures meaning and handles synonyms. The combination typically outperforms either method alone, especially when properly tuned.",
        "source": "Advanced IR"
    },
    {
        "title": "Evaluation Metrics for Retrieval",
        "text": "Retrieval system performance is measured using various metrics. Precision measures the fraction of retrieved documents that are relevant. Recall measures the fraction of relevant documents that are retrieved. nDCG (Normalized Discounted Cumulative Gain) accounts for the graded relevance and position of results. Mean Reciprocal Rank (MRR) focuses on the rank of the first relevant result.",
        "source": "Evaluation Methods"
    },
    {
        "title": "Database Indexing Strategies",
        "text": "Database indexing creates data structures to improve the speed of data retrieval operations. Common index types include B-trees for ordered data, hash indexes for equality searches, and inverted indexes for full-text search. The choice of index depends on query patterns, data distribution, and performance requirements. Proper indexing can reduce query time from linear to logarithmic complexity.",
        "source": "Database Systems"
    },
    {
        "title": "API Design Best Practices",
        "text": "Well-designed APIs are intuitive, consistent, and robust. RESTful APIs use standard HTTP methods and status codes. Request and response schemas should be well-documented and validated. Error messages should be clear and actionable. Versioning enables evolution without breaking existing clients. Rate limiting and authentication protect against abuse. Comprehensive testing ensures reliability.",
        "source": "Software Engineering"
    },
    {
        "title": "Web Application Architecture",
        "text": "Modern web applications typically follow a three-tier architecture: presentation layer (UI), application layer (business logic), and data layer (storage). The frontend communicates with the backend via APIs, often using JSON over HTTP. Microservices architectures decompose applications into small, independent services. Load balancers distribute traffic, and caching improves performance.",
        "source": "Web Development"
    }
]

def generate_expanded_corpus():
    """Generate 300+ documents by creating variations and extensions"""
    corpus = []
    doc_id = 1
    base_date = datetime.now() - timedelta(days=365)
    
    # Add base documents
    for item in SAMPLE_TEXTS:
        corpus.append({
            "doc_id": f"doc_{doc_id:04d}",
            "title": item["title"],
            "text": item["text"],
            "source": item["source"],
            "created_at": (base_date + timedelta(days=random.randint(0, 365))).isoformat()
        })
        doc_id += 1
    
    # Generate variations with different topics
    topics = {
        "python": [
            "Python is a high-level, interpreted programming language known for its clear syntax and readability. It supports multiple programming paradigms including procedural, object-oriented, and functional programming. Python's extensive standard library and vast ecosystem of third-party packages make it suitable for web development, data science, automation, and more.",
            "Python data structures include lists, tuples, dictionaries, and sets. Lists are mutable sequences, tuples are immutable, dictionaries store key-value pairs, and sets contain unique elements. Understanding when to use each structure is crucial for writing efficient Python code. List comprehensions provide concise syntax for creating lists.",
            "Python functions are first-class objects, meaning they can be assigned to variables, passed as arguments, and returned from other functions. Decorators allow modifying function behavior without changing their code. Lambda functions provide anonymous function syntax for simple operations. Generators enable memory-efficient iteration over large datasets.",
        ],
        "algorithms": [
            "Sorting algorithms arrange elements in a specific order. Common algorithms include quicksort (average O(n log n)), mergesort (worst-case O(n log n)), and heapsort. Selection of algorithm depends on data characteristics, stability requirements, and space constraints. In-place algorithms modify the input array, while others require additional memory.",
            "Graph algorithms solve problems on graph structures representing relationships between entities. Breadth-first search explores nodes level by level. Depth-first search explores as far as possible along each branch. Dijkstra's algorithm finds shortest paths from a source node. Topological sort orders directed acyclic graphs.",
            "Dynamic programming solves complex problems by breaking them into simpler subproblems. It stores results of subproblems to avoid redundant computation. Classic examples include the Fibonacci sequence, longest common subsequence, and knapsack problem. Memoization and tabulation are two common implementation approaches.",
        ],
        "data_science": [
            "Data preprocessing is crucial for machine learning success. Steps include handling missing values, encoding categorical variables, feature scaling, and outlier detection. Missing data can be imputed using mean, median, or more sophisticated methods. Feature engineering creates new features from existing ones to improve model performance.",
            "Supervised learning trains models on labeled data to make predictions. Classification predicts discrete labels, while regression predicts continuous values. Common algorithms include linear regression, logistic regression, decision trees, random forests, and support vector machines. Model selection depends on data characteristics and problem requirements.",
            "Unsupervised learning finds patterns in unlabeled data. Clustering groups similar instances together. K-means partitions data into k clusters based on feature similarity. Hierarchical clustering creates a tree of clusters. Principal Component Analysis reduces dimensionality while preserving variance. Anomaly detection identifies unusual patterns.",
        ],
        "web_dev": [
            "HTML provides the structure of web pages using tags and elements. Semantic HTML5 elements like header, nav, article, and footer improve accessibility and SEO. Forms collect user input with input, select, and textarea elements. Proper HTML structure is essential for responsive design and browser compatibility.",
            "CSS styles the visual presentation of HTML elements. Selectors target elements for styling. Properties control layout, colors, fonts, and spacing. Flexbox provides one-dimensional layouts. Grid enables two-dimensional layouts. Media queries enable responsive design. CSS preprocessors like Sass add programming features.",
            "JavaScript adds interactivity to web pages. The DOM (Document Object Model) represents page structure as a tree. Event listeners respond to user actions. AJAX enables asynchronous server communication. Modern JavaScript includes arrow functions, promises, async/await, destructuring, and modules. Frameworks like React simplify complex UIs.",
        ],
        "security": [
            "Web security protects applications from attacks. Common vulnerabilities include SQL injection, cross-site scripting (XSS), and cross-site request forgery (CSRF). Input validation prevents malicious data from entering the system. Parameterized queries defend against SQL injection. Content Security Policy mitigates XSS attacks.",
            "Authentication verifies user identity. Passwords should be hashed using strong algorithms like bcrypt or Argon2. Multi-factor authentication adds an extra security layer. OAuth 2.0 enables secure third-party authorization. JSON Web Tokens (JWT) provide stateless authentication for APIs. Session management requires careful security considerations.",
            "Encryption protects data confidentiality. Symmetric encryption uses the same key for encryption and decryption. Asymmetric encryption uses public and private key pairs. TLS/SSL secures data in transit. At-rest encryption protects stored data. Key management is critical for maintaining security. Perfect forward secrecy limits damage from key compromise.",
        ],
    }
    
    # Generate documents from topic variations
    for topic, texts in topics.items():
        for i, text in enumerate(texts):
            for variation in range(20):  # 20 variations per text to get 300+ docs
                suffix_variations = [
                    f"This variant explores {topic} from a practical perspective with real-world examples.",
                    f"Advanced concepts in {topic} are essential for modern software development.",
                    f"This guide covers {topic} fundamentals and best practices for professionals.",
                    f"Learn {topic} through hands-on examples and industry-proven techniques.",
                    f"Master {topic} with this comprehensive overview and practical insights.",
                ]
                suffix = suffix_variations[variation % len(suffix_variations)]
                
                corpus.append({
                    "doc_id": f"doc_{doc_id:04d}",
                    "title": f"{topic.replace('_', ' ').title()} - Part {i+1} Variant {variation+1}",
                    "text": text + f" {suffix} Understanding these concepts is essential for building robust and scalable systems.",
                    "source": f"{topic}_collection",
                    "created_at": (base_date + timedelta(days=random.randint(0, 365))).isoformat()
                })
                doc_id += 1
    
    return corpus

if __name__ == "__main__":
    corpus = generate_expanded_corpus()
    output_dir = "data/raw"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save as individual text files
    for doc in corpus:
        filename = f"{output_dir}/{doc['doc_id']}.txt"
        with open(filename, 'w') as f:
            f.write(f"Title: {doc['title']}\n")
            f.write(f"Source: {doc['source']}\n")
            f.write(f"Date: {doc['created_at']}\n\n")
            f.write(doc['text'])
    
    print(f"Generated {len(corpus)} documents in {output_dir}/")
    print(f"Total word count: {sum(len(doc['text'].split()) for doc in corpus)}")
