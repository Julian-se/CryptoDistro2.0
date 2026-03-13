#!/bin/bash
# CryptoDistro 2.0 — Start script
# Usage: ./scripts/start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Check for virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "No virtual environment found. Create one with:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Check config
if [ ! -f "config/settings.yaml" ]; then
    echo "ERROR: config/settings.yaml not found"
    exit 1
fi

echo "Starting CryptoDistro 2.0..."
python -m main
