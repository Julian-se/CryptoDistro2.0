#!/bin/bash
# Start CryptoDistro 2.0 frontend (Next.js)
set -e

FRONTEND_DIR="$(dirname "$0")/../frontend"
cd "$FRONTEND_DIR"

# Install if node_modules missing
if [ ! -d "node_modules" ]; then
  echo "Installing frontend dependencies..."
  npm install
fi

echo "Starting CryptoDistro frontend on http://localhost:3000"
echo ""

npm run dev
