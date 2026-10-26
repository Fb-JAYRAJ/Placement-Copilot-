#!/usr/bin/env bash
# Placement Copilot — Unified Development Server Launcher
# Starts FastAPI backend (port 8000) and Vite React frontend (port 5173) together.

set -e

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${WORKSPACE_DIR}/backend"
FRONTEND_DIR="${WORKSPACE_DIR}/frontend"
BACKEND_LOG="${WORKSPACE_DIR}/backend.log"

echo "=========================================================="
echo " Starting Placement Copilot (Development Environment)   "
echo "=========================================================="

# Check Python venv
if [ ! -d "${BACKEND_DIR}/.venv" ]; then
    echo "Creating Python virtual environment in backend/.venv..."
    python3 -m venv "${BACKEND_DIR}/.venv"
    "${BACKEND_DIR}/.venv/bin/pip" install --upgrade pip
    "${BACKEND_DIR}/.venv/bin/pip" install -e "${BACKEND_DIR}"
fi

# Trap signals for graceful shutdown
cleanup() {
    local exit_code=$?
    echo ""
    echo "Shutting down Placement Copilot services..."
    if [ -n "${BACKEND_PID}" ]; then
        kill "${BACKEND_PID}" 2>/dev/null || true
    fi
    if [ -n "${FRONTEND_PID}" ]; then
        kill "${FRONTEND_PID}" 2>/dev/null || true
    fi
    if [ -n "${TAIL_PID}" ]; then
        kill "${TAIL_PID}" 2>/dev/null || true
    fi
    wait 2>/dev/null || true
    echo "Services stopped cleanly. Goodbye!"
    exit "${exit_code}"
}

trap cleanup SIGINT SIGTERM EXIT

# Start Backend
echo "Starting FastAPI backend on http://localhost:8000..."
cd "${BACKEND_DIR}"
"${BACKEND_DIR}/.venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 > "${BACKEND_LOG}" 2>&1 &
BACKEND_PID=$!

# Wait for backend database health check
echo "Waiting for backend database health check (/api/v1/health/db)..."
BACKEND_READY=0
for i in {1..40}; do
    if ! kill -0 "${BACKEND_PID}" 2>/dev/null; then
        echo "✗ Backend process exited unexpectedly."
        break
    fi
    if curl -s -f http://127.0.0.1:8000/api/v1/health/db > /dev/null 2>&1; then
        echo "✓ Backend & Database healthy and ready at http://localhost:8000"
        BACKEND_READY=1
        break
    fi
    sleep 0.5
done

if [ "${BACKEND_READY}" -ne 1 ]; then
    echo "=========================================================="
    echo " ERROR: Backend failed to pass /api/v1/health/db"
    echo " Last 30 lines of backend log:"
    echo "=========================================================="
    tail -n 30 "${BACKEND_LOG}" 2>/dev/null || true
    echo "=========================================================="
    kill "${BACKEND_PID}" 2>/dev/null || true
    trap - SIGINT SIGTERM EXIT
    exit 1
fi

# Stream backend log lines in background while running
tail -n 0 -f "${BACKEND_LOG}" &
TAIL_PID=$!

# Start Frontend
echo "Starting Vite frontend on http://localhost:5173..."
cd "${FRONTEND_DIR}"
npm run dev -- --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!

echo "=========================================================="
echo " Placement Copilot is running:                           "
echo " • Frontend: http://localhost:5173                       "
echo " • Backend API: http://localhost:8000                    "
echo " • API Docs: http://localhost:8000/docs                  "
echo " Demo Login: demo@placementcopilot.com / DemoCandidate2026!"
echo " Press Ctrl+C to terminate both servers.                 "
echo "=========================================================="

wait
