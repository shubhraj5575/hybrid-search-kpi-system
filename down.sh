#!/bin/bash

echo "Stopping services..."

# Kill processes by PID if files exist
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    kill $BACKEND_PID 2>/dev/null && echo "✓ Backend stopped (PID: $BACKEND_PID)"
    rm .backend.pid
fi

if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    kill $FRONTEND_PID 2>/dev/null && echo "✓ Frontend stopped (PID: $FRONTEND_PID)"
    rm .frontend.pid
fi

# Fallback: kill by process name
pkill -f "uvicorn backend.app.main:app" 2>/dev/null
pkill -f "vite" 2>/dev/null

echo "✓ All services stopped"
