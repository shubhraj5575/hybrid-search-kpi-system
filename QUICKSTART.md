# QUICKSTART GUIDE

## 🚀 Get Running in 60 Seconds

### Prerequisites
- Python 3.11+
- Node.js 16+
- 4GB RAM
- Git

### Run
```bash
cd hybrid-search-kpi-system
./up.sh
```

That's it! The script handles everything:
- Creates virtual environment
- Installs all dependencies
- Generates 310-document corpus
- Builds BM25 + vector indexes
- Starts backend (port 8000) + frontend (port 3000)

### Access
- **Dashboard**: http://localhost:3000
- **API**: http://localhost:8000/docs (Swagger)
- **Health**: http://localhost:8000/health

### Stop
```bash
./down.sh
```
or press Ctrl+C

---

## 📋 Quick Feature Tour

### 1. Search (Main Tab)
- Type query: "machine learning neural networks"
- Adjust alpha slider (0=pure vector, 1=pure BM25)
- See score breakdown for each result
- View latency in real-time

### 2. KPIs (Second Tab)
- Latency p50/p95/p99
- Top 10 queries by frequency
- Zero-result queries (queries that returned nothing)
- Live latency chart (updates every 5s)

### 3. Evaluation (Third Tab)
- Run experiments with different parameters
- See nDCG/Recall/MRR trends
- Compare normalization strategies

---

## 🧪 Run Experiments

```bash
# Activate environment first
source .venv/bin/activate

# Experiment 1: Balanced (default)
python -m backend.app.eval --alpha 0.5 --normalization minmax

# Experiment 2: BM25-heavy
python -m backend.app.eval --alpha 0.7 --normalization minmax

# Experiment 3: Vector-heavy
python -m backend.app.eval --alpha 0.3 --normalization minmax

# Experiment 4: Z-score normalization
python -m backend.app.eval --alpha 0.5 --normalization zscore

# Experiment 5: Pure BM25
python -m backend.app.eval --alpha 1.0 --normalization minmax
```

Results appear in the Evaluation tab automatically!

---

## 🧪 Run Tests

```bash
source .venv/bin/activate
pytest backend/tests/ -v
```

Should see 15+ tests pass.

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `up.sh` | One-command startup |
| `down.sh` | Stop all services |
| `README.md` | Full documentation |
| `docs/architecture.md` | System design |
| `docs/decision_log.md` | Design rationale |
| `docs/codex_log.md` | Development process |
| `docs/break_fix_log.md` | Error scenarios |

---

## 🔧 Configuration

### Change Alpha Default
Edit `frontend/src/components/SearchPage.jsx`:
```javascript
const [alpha, setAlpha] = useState(0.5);  // Change 0.5 to your default
```

### Change Embedding Model
Edit `backend/app/index.py`:
```python
--model all-MiniLM-L6-v2  # Try: all-mpnet-base-v2
```
Then rebuild indexes:
```bash
rm -rf data/index
./up.sh  # Rebuilds automatically
```

### Add Custom Documents
```bash
# Place .txt or .md files in data/custom/
python -m backend.app.ingest --input data/custom --out data/processed
python -m backend.app.index --input data/processed/docs.jsonl
./down.sh && ./up.sh
```

---

## ❓ Troubleshooting

### "Port already in use"
```bash
# Kill existing processes
./down.sh
pkill -f uvicorn
pkill -f vite
# Then restart
./up.sh
```

### "Module not found"
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Frontend won't load
```bash
cd frontend
npm install
cd ..
./up.sh
```

### Indexes corrupted
```bash
rm -rf data/index data/processed
./up.sh  # Rebuilds everything
```

---

## 📊 Example Queries to Try

**BM25 excels at**:
- "python data structures"
- "SQL injection XSS"
- "quicksort mergesort"

**Vector excels at**:
- "how do I learn AI?"
- "building secure applications"
- "fast sorting methods"

**Hybrid works best**:
- "machine learning algorithms"
- "web security best practices"
- "programming python"

Try different alpha values to see how results change!

---

## 🎯 Assignment Checklist

✅ Hybrid search (BM25 + vector)  
✅ CPU-only (no GPU required)  
✅ FastAPI backend with /search, /health, /metrics  
✅ React dashboard with 3 pages  
✅ Evaluation harness (nDCG, Recall, MRR)  
✅ 310+ document corpus  
✅ 25 labeled queries  
✅ Unit tests (pytest)  
✅ SQLite logging  
✅ One-command startup (./up.sh)  
✅ Documentation (architecture, decisions, break/fix)  
✅ Git commits  

---

## 📝 Next Steps

1. **Run the system**: `./up.sh`
2. **Try searches**: Different alpha values
3. **Run experiments**: 5+ with different parameters
4. **Check KPIs**: Watch metrics populate
5. **Read docs**: Understand design decisions

---

## 🎬 Demo Flow (for video)

1. Start: `./up.sh` → Show startup messages
2. Health check: Open http://localhost:8000/health
3. Search: Query "machine learning", adjust alpha
4. KPIs: Show latency stats, top queries
5. Eval: Show experiment results
6. Tests: `pytest backend/tests/ -v`
7. Code tour: Show hybrid.py score fusion
8. Break/fix: Show validation in vector.py

Total: ~5-7 minutes

---

**Questions?** Check README.md or docs/architecture.md

**Enjoy building with hybrid search! 🔍**
