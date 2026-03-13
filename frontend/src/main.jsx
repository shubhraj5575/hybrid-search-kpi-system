import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import SearchPage from './components/SearchPage';
import KPIPage from './components/KPIPage';
import EvaluationPage from './components/EvaluationPage';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('search');
  const [health, setHealth] = useState(null);

  useEffect(() => {
    fetch('/health')
      .then(res => res.json())
      .then(data => setHealth(data))
      .catch(err => console.error('Health check failed:', err));
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <h1>🔍 Hybrid Search Dashboard</h1>
        <div className="health-status">
          {health && (
            <span className={health.status === 'OK' ? 'status-ok' : 'status-error'}>
              {health.status} • v{health.version} • {health.commit_hash}
            </span>
          )}
        </div>
      </header>

      <nav className="app-nav">
        <button
          className={activeTab === 'search' ? 'active' : ''}
          onClick={() => setActiveTab('search')}
        >
          Search
        </button>
        <button
          className={activeTab === 'kpi' ? 'active' : ''}
          onClick={() => setActiveTab('kpi')}
        >
          KPIs
        </button>
        <button
          className={activeTab === 'eval' ? 'active' : ''}
          onClick={() => setActiveTab('eval')}
        >
          Evaluation
        </button>
      </nav>

      <main className="app-main">
        {activeTab === 'search' && <SearchPage />}
        {activeTab === 'kpi' && <KPIPage />}
        {activeTab === 'eval' && <EvaluationPage />}
      </main>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
