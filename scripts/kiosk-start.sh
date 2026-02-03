#!/bin/bash
# Dashboard Kiosk Startup Script
# Starts the FastAPI server and launches Chromium in kiosk mode

set -e

DASHBOARD_DIR="/home/pi/apps/dashboard/repo"
VENV_DIR="${DASHBOARD_DIR}/venv"
PORT=8000

echo "Starting Pi Dashboard..."

# Wait for network
echo "Waiting for network..."
sleep 5

# Activate virtual environment and start server
cd "$DASHBOARD_DIR"

if [ -d "$VENV_DIR" ]; then
    source "${VENV_DIR}/bin/activate"
fi

# Start FastAPI server in background
echo "Starting FastAPI server on port ${PORT}..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT &
SERVER_PID=$!

# Wait for server to be ready
echo "Waiting for server to start..."
sleep 3

# Check if server is running
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "Error: Server failed to start"
    exit 1
fi

echo "Server started (PID: ${SERVER_PID})"

# Launch Chromium in kiosk mode (portrait 1080x1920)
echo "Launching Chromium in kiosk mode..."
/usr/bin/chromium-browser \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-restore-session-state \
    --no-first-run \
    --start-fullscreen \
    --window-size=1080,1920 \
    --window-position=0,0 \
    --check-for-update-interval=31536000 \
    --disable-features=TranslateUI \
    --disable-pinch \
    --overscroll-history-navigation=0 \
    "http://localhost:${PORT}/"

# If Chromium exits, also stop the server
kill $SERVER_PID 2>/dev/null || true
echo "Dashboard stopped"
