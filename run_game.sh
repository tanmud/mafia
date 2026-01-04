#!/usr/bin/env bash

set -e

BACKEND_PORT=8000
RAG_PORT=9000
FRONTEND_PORT=3000   # Vite dev port

# Get IPv4 for en0 (Wi‑Fi) on macOS
IPV4=$(ipconfig getifaddr en0 2>/dev/null || true)

if [ -z "$IPV4" ]; then
  echo "Could not detect IPv4 on en0. Falling back to localhost."
  IPV4="localhost"
fi

PIDS=()

cleanup() {
  echo
  echo "Caught interrupt, stopping all services..."
  if [ ${#PIDS[@]} -gt 0 ]; then
    kill "${PIDS[@]}" 2>/dev/null || true
  fi
  exit 0
}

trap cleanup INT

echo "Using host IP: ${IPV4}"

echo "=== Starting Ollama RAG server on port ${RAG_PORT} ==="
cd ollama_service
# Make sure deps installed once: pip install fastapi uvicorn httpx
uvicorn rag_server:app --host 0.0.0.0 --port "${RAG_PORT}" > ../rag_server.log 2>&1 &
PIDS+=($!)
cd ..

echo "=== Starting FastAPI + Socket.IO backend on port ${BACKEND_PORT} ==="
cd backend
# Make sure deps installed once: pip install fastapi uvicorn python-socketio httpx
MAFIA_LAN_IP="${IPV4}" \
MAFIA_BACKEND_PORT="${BACKEND_PORT}" \
MAFIA_FRONTEND_PORT="${FRONTEND_PORT}" \
uvicorn main:app --host 0.0.0.0 --port "${BACKEND_PORT}" --reload > ../backend.log 2>&1 &
PIDS+=($!)
cd ..

echo "=== Starting React frontend dev server on port ${FRONTEND_PORT} ==="
cd frontend
# Make sure deps installed once: npm install
VITE_MAFIA_BASE_URL="http://${IPV4}:${BACKEND_PORT}" \
npm run dev -- --host 0.0.0.0 --port ${FRONTEND_PORT} > ../frontend.log 2>&1 &
PIDS+=($!)
cd ..

echo "=== All services started ==="
echo "RAG server log:      rag_server.log"
echo "Backend server log:  backend.log"
echo "Frontend server log: frontend.log"
echo
echo "=== URLs ==="
echo "Server control panel (use on this laptop):"
echo "  http://localhost:${FRONTEND_PORT}/?role=control"
echo
echo "Client join link (share with friends on your Wi‑Fi):"
echo "  http://${IPV4}:${FRONTEND_PORT}/?role=player"
echo
echo "Backend health (debug):"
echo "  http://${IPV4}:${BACKEND_PORT}/health"
echo
echo "Press Ctrl+C to stop everything."

wait
