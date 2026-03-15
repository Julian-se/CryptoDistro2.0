#!/bin/bash
# Start CryptoDistro 2.0 backend (FastAPI)
set -e

cd "$(dirname "$0")/.."

# Activate virtualenv if present
if [ -d "venv" ]; then
  source venv/bin/activate
fi

echo "Starting CryptoDistro backend on http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
echo "WebSocket: ws://localhost:8000/ws"
echo ""

uvicorn backend.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload \
  --log-level info
