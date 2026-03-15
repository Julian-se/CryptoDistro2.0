#!/bin/bash
# Start both backend and frontend in background, with clean shutdown
set -e

ROOT="$(dirname "$0")/.."
cd "$ROOT"

cleanup() {
  echo ""
  echo "Shutting down..."
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
  exit 0
}
trap cleanup INT TERM

# Backend
echo "▶ Starting backend..."
if [ -d "venv" ]; then source venv/bin/activate; fi
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Frontend
echo "▶ Starting frontend..."
cd frontend
if [ ! -d "node_modules" ]; then npm install; fi
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "═══════════════════════════════════════"
echo "  CryptoDistro 2.0 running"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo "  API docs: http://localhost:8000/docs"
echo "  Ctrl+C to stop"
echo "═══════════════════════════════════════"

wait $BACKEND_PID $FRONTEND_PID
