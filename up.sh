#!/bin/bash

set -e  # Exit on error

echo "================================================"
echo "🚀 Hybrid Search + KPI Dashboard System"
echo "================================================"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ------------------------------------------------
# Ensure required directories exist (reproducibility fix)
# ------------------------------------------------
mkdir -p data/db data/index data/metrics data/processed data/raw data/eval logs

# Ensure backend module path works
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend

# ------------------------------------------------
# Step 1: Create/activate virtual environment
# ------------------------------------------------
echo -e "\n${BLUE}[1/7]${NC} Setting up Python virtual environment..."

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${GREEN}✓${NC} Virtual environment exists"
fi

source .venv/bin/activate

# ------------------------------------------------
# Step 2: Install Python dependencies
# ------------------------------------------------
echo -e "\n${BLUE}[2/7]${NC} Installing Python dependencies..."

pip install --upgrade pip setuptools wheel >/dev/null
pip install -r requirements.txt >/dev/null

echo -e "${GREEN}✓${NC} Python dependencies installed"

# ------------------------------------------------
# Step 3: Generate/check corpus
# ------------------------------------------------
echo -e "\n${BLUE}[3/7]${NC} Preparing corpus..."

if [ ! -f "data/processed/docs.jsonl" ]; then
    echo "Generating sample corpus..."
    python3 generate_corpus.py

    echo "Running ingestion pipeline..."
    python3 -m backend.app.ingest --input data/raw --out data/processed

    echo -e "${GREEN}✓${NC} Corpus prepared"
else
    echo -e "${GREEN}✓${NC} Corpus already exists"
fi

# ------------------------------------------------
# Step 4: Build indexes
# ------------------------------------------------
echo -e "\n${BLUE}[4/7]${NC} Building search indexes..."

if [ ! -f "data/index/metadata.json" ]; then
    echo "Building BM25 and vector indexes..."
    python3 -m backend.app.index \
        --input data/processed/docs.jsonl \
        --bm25-dir data/index/bm25 \
        --vector-dir data/index/vector \
        --model all-MiniLM-L6-v2

    echo -e "${GREEN}✓${NC} Indexes built"
else
    echo -e "${GREEN}✓${NC} Indexes already exist"
fi

# ------------------------------------------------
# Step 5: Generate evaluation data
# ------------------------------------------------
echo -e "\n${BLUE}[5/7]${NC} Preparing evaluation data..."

if [ ! -f "data/eval/queries.jsonl" ]; then
    python3 generate_eval_data.py
    echo -e "${GREEN}✓${NC} Evaluation data generated"
else
    echo -e "${GREEN}✓${NC} Evaluation data exists"
fi

# ------------------------------------------------
# Step 6: Setup frontend
# ------------------------------------------------
echo -e "\n${BLUE}[6/7]${NC} Setting up frontend..."

cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install --silent
    echo -e "${GREEN}✓${NC} Frontend dependencies installed"
else
    echo -e "${GREEN}✓${NC} Frontend dependencies exist"
fi

cd "$PROJECT_ROOT"

# ------------------------------------------------
# Step 7: Start services
# ------------------------------------------------
echo -e "\n${BLUE}[7/7]${NC} Starting services..."

pkill -f "uvicorn backend.app.main:app" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true

sleep 1

# Start backend
echo "Starting backend API on port 8000..."

python3 -m uvicorn backend.app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    > logs/backend.log 2>&1 &

BACKEND_PID=$!

echo -e "${GREEN}✓${NC} Backend started (PID: $BACKEND_PID)"

# Wait for backend
echo "Waiting for backend..."

for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✓${NC} Backend ready"
        break
    fi
    sleep 1
done

# Start frontend
echo "Starting frontend on port 3000..."

cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!

cd "$PROJECT_ROOT"

echo -e "${GREEN}✓${NC} Frontend started (PID: $FRONTEND_PID)"

# Save PIDs
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

# ------------------------------------------------
# Print access info
# ------------------------------------------------
echo ""
echo "================================================"
echo -e "${GREEN}✓ System is running!${NC}"
echo "================================================"
echo ""
echo "Dashboard: http://localhost:3000"
echo "API:       http://localhost:8000"
echo "Health:    http://localhost:8000/health"
echo "Metrics:   http://localhost:8000/metrics"
echo ""
echo "Logs:"
echo "  Backend:  logs/backend.log"
echo "  Frontend: logs/frontend.log"
echo ""
echo "Stop system:"
echo "  ./down.sh"
echo ""
echo "================================================"

# Keep running
trap "echo 'Stopping...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait