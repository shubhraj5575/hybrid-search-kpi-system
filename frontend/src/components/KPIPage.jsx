import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function KPIPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        setStats(data);
      } catch (err) {
        console.error('Failed to fetch stats:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="loading">Loading KPIs...</div>;
  }

  if (!stats) {
    return <div className="error">Failed to load statistics</div>;
  }

  const latencyData = stats.recent_queries
    ? stats.recent_queries.slice(0, 50).reverse().map((q, i) => ({
        index: i,
        latency: q.latency_ms
      }))
    : [];

  return (
    <div className="kpi-page">
      <h2>Key Performance Indicators</h2>

      <div className="kpi-grid">
        <div className="kpi-card">
          <h3>Latency Statistics</h3>
          {stats.latency && Object.keys(stats.latency).length > 0 ? (
            <div className="stats-grid">
              <div className="stat-item">
                <div className="stat-label">P50 (Median)</div>
                <div className="stat-value">{stats.latency.p50?.toFixed(2) || 0} ms</div>
              </div>
              <div className="stat-item">
                <div className="stat-label">P95</div>
                <div className="stat-value">{stats.latency.p95?.toFixed(2) || 0} ms</div>
              </div>
              <div className="stat-item">
                <div className="stat-label">P99</div>
                <div className="stat-value">{stats.latency.p99?.toFixed(2) || 0} ms</div>
              </div>
              <div className="stat-item">
                <div className="stat-label">Mean</div>
                <div className="stat-value">{stats.latency.mean?.toFixed(2) || 0} ms</div>
              </div>
              <div className="stat-item">
                <div className="stat-label">Total Requests</div>
                <div className="stat-value">{stats.latency.count || 0}</div>
              </div>
            </div>
          ) : (
            <p>No latency data available yet</p>
          )}
        </div>

        <div className="kpi-card chart-card">
          <h3>Latency Over Time</h3>
          {latencyData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={latencyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="index" />
                <YAxis label={{ value: 'ms', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Line type="monotone" dataKey="latency" stroke="#8884d8" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p>No query history yet</p>
          )}
        </div>

        <div className="kpi-card">
          <h3>Top Queries</h3>
          {stats.top_queries && stats.top_queries.length > 0 ? (
            <div className="query-list">
              {stats.top_queries.map((item, idx) => (
                <div key={idx} className="query-item">
                  <span className="query-rank">#{idx + 1}</span>
                  <span className="query-text">{item.query}</span>
                  <span className="query-count">{item.count}x</span>
                </div>
              ))}
            </div>
          ) : (
            <p>No queries yet</p>
          )}
        </div>

        <div className="kpi-card">
          <h3>Zero Result Queries</h3>
          {stats.zero_result_queries && stats.zero_result_queries.length > 0 ? (
            <div className="query-list">
              {stats.zero_result_queries.map((item, idx) => (
                <div key={idx} className="query-item zero-result">
                  <span className="query-rank">#{idx + 1}</span>
                  <span className="query-text">{item.query}</span>
                  <span className="query-count">{item.count}x</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="success-message">✓ All queries returning results!</p>
          )}
        </div>
      </div>
    </div>
  );
}
