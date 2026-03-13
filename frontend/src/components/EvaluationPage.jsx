import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function EvaluationPage() {
  const [experiments, setExperiments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchExperiments = async () => {
      try {
        const response = await fetch('/api/experiments');
        const data = await response.json();
        setExperiments(data.experiments || []);
      } catch (err) {
        console.error('Failed to fetch experiments:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchExperiments();
  }, []);

  if (loading) {
    return <div className="loading">Loading evaluation data...</div>;
  }

  const chartData = experiments.map((exp, idx) => ({
    index: idx + 1,
    'nDCG@10': parseFloat(exp['ndcg@10']),
    'Recall@10': parseFloat(exp['recall@10']),
    'MRR@10': parseFloat(exp['mrr@10']),
    alpha: parseFloat(exp.alpha),
    timestamp: new Date(exp.timestamp).toLocaleDateString()
  }));

  return (
    <div className="eval-page">
      <h2>Evaluation Experiments</h2>

      {experiments.length > 0 ? (
        <>
          <div className="eval-chart">
            <h3>Metrics Over Experiments</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="index" label={{ value: 'Experiment #', position: 'insideBottom', offset: -5 }} />
                <YAxis label={{ value: 'Score', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="nDCG@10" stroke="#8884d8" />
                <Line type="monotone" dataKey="Recall@10" stroke="#82ca9d" />
                <Line type="monotone" dataKey="MRR@10" stroke="#ffc658" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="experiments-table">
            <h3>Experiment Details</h3>
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Timestamp</th>
                  <th>Commit</th>
                  <th>Alpha</th>
                  <th>Normalization</th>
                  <th>Model</th>
                  <th>nDCG@10</th>
                  <th>Recall@10</th>
                  <th>MRR@10</th>
                  <th>Queries</th>
                </tr>
              </thead>
              <tbody>
                {experiments.map((exp, idx) => (
                  <tr key={idx}>
                    <td>{idx + 1}</td>
                    <td>{new Date(exp.timestamp).toLocaleString()}</td>
                    <td><code>{exp.git_commit}</code></td>
                    <td>{parseFloat(exp.alpha).toFixed(2)}</td>
                    <td>{exp.normalization}</td>
                    <td className="model-cell">{exp.embedding_model}</td>
                    <td className="metric-cell">{parseFloat(exp['ndcg@10']).toFixed(4)}</td>
                    <td className="metric-cell">{parseFloat(exp['recall@10']).toFixed(4)}</td>
                    <td className="metric-cell">{parseFloat(exp['mrr@10']).toFixed(4)}</td>
                    <td>{exp.num_queries}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <div className="no-data">
          <p>No experiments run yet.</p>
          <p>Run: <code>python -m app.eval</code></p>
        </div>
      )}
    </div>
  );
}
