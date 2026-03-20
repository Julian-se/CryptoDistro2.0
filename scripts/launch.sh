#!/bin/bash
# CryptoDistro 2.0 — Desktop launcher
# Opens a terminal running all services, then opens the browser when ready.

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Open terminal with start_all.sh
if command -v gnome-terminal &>/dev/null; then
  gnome-terminal --title="CryptoDistro 2.0" -- bash -c "cd '$ROOT' && bash scripts/start_all.sh; exec bash"
elif command -v konsole &>/dev/null; then
  konsole --title "CryptoDistro 2.0" -e bash -c "cd '$ROOT' && bash scripts/start_all.sh; exec bash"
elif command -v xfce4-terminal &>/dev/null; then
  xfce4-terminal --title="CryptoDistro 2.0" -e "bash -c \"cd '$ROOT' && bash scripts/start_all.sh; exec bash\""
elif command -v xterm &>/dev/null; then
  xterm -title "CryptoDistro 2.0" -e "bash -c \"cd '$ROOT' && bash scripts/start_all.sh; exec bash\""
else
  echo "No terminal emulator found. Run manually: bash $ROOT/scripts/start_all.sh"
  exit 1
fi

# Wait for backend to be ready (up to 60s), then open browser
echo "Waiting for services to start..."
for i in $(seq 1 60); do
  if curl -sf http://localhost:8000/api/health >/dev/null 2>&1; then
    xdg-open http://localhost:3000
    exit 0
  fi
  sleep 1
done

# Fallback: open browser anyway after timeout
xdg-open http://localhost:3000
