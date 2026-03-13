import React, { useState } from 'react';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(10);
  const [alpha, setAlpha] = useState(0.5);
  const [normalization, setNormalization] = useState('minmax');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: topK, alpha, normalization })
      });

      if (!response.ok) {
        throw new Error(`Search failed: ${response.status}`);
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="search-page">
      <div className="search-form-container">
        <form onSubmit={handleSearch} className="search-form">
          <div className="search-input-group">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your search query..."
              className="search-input"
              required
            />
            <button type="submit" className="search-button" disabled={loading}>
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>

          <div className="search-controls">
            <div className="control-group">
              <label>
                Top K: {topK}
                <input
                  type="range"
                  min="1"
                  max="50"
                  value={topK}
                  onChange={(e) => setTopK(Number(e.target.value))}
                />
              </label>
            </div>

            <div className="control-group">
              <label>
                Alpha (BM25 weight): {alpha.toFixed(2)}
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={alpha}
                  onChange={(e) => setAlpha(Number(e.target.value))}
                />
              </label>
            </div>

            <div className="control-group">
              <label>
                Normalization:
                <select value={normalization} onChange={(e) => setNormalization(e.target.value)}>
                  <option value="minmax">Min-Max</option>
                  <option value="zscore">Z-Score</option>
                </select>
              </label>
            </div>
          </div>
        </form>
      </div>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {results && (
        <div className="search-results">
          <div className="results-header">
            <h2>{results.total_results} results</h2>
            <span className="latency">Latency: {results.latency_ms.toFixed(2)}ms</span>
          </div>

          <div className="results-list">
            {results.results.map((result, idx) => (
              <div key={result.doc_id} className="result-card">
                <div className="result-rank">#{idx + 1}</div>
                <div className="result-content">
                  <h3>{result.title}</h3>
                  <p className="result-snippet">{result.snippet}</p>
                  <div className="result-metadata">
                    <span className="doc-id">{result.doc_id}</span>
                    <span className="source">{result.source}</span>
                  </div>
                  <div className="result-scores">
                    <div className="score-item">
                      <span className="score-label">Hybrid:</span>
                      <span className="score-value">{result.hybrid_score.toFixed(4)}</span>
                    </div>
                    <div className="score-item">
                      <span className="score-label">BM25:</span>
                      <span className="score-value">{result.bm25_score_norm.toFixed(4)}</span>
                      <span className="score-raw">({result.bm25_score.toFixed(2)})</span>
                    </div>
                    <div className="score-item">
                      <span className="score-label">Vector:</span>
                      <span className="score-value">{result.vector_score_norm.toFixed(4)}</span>
                      <span className="score-raw">({result.vector_score.toFixed(4)})</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
