#!/bin/bash
# ASTER-26 startup script
# Starts the Dash app then opens Chromium once the server is ready

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_URL="http://127.0.0.1:8050"
MAX_WAIT=30   # seconds to wait for server before opening browser

# Start the app in the background
cd "$SCRIPT_DIR"
python3 "$SCRIPT_DIR/main.py" &
APP_PID=$!

# Wait until the server responds (or timeout)
echo "Waiting for server at $APP_URL ..."
elapsed=0
until curl -s --head "$APP_URL" > /dev/null 2>&1; do
    sleep 1
    elapsed=$((elapsed + 1))
    if [ "$elapsed" -ge "$MAX_WAIT" ]; then
        echo "Server did not respond after ${MAX_WAIT}s — opening browser anyway."
        break
    fi
done

echo "Opening browser..."
chromium-browser --start-fullscreen "$APP_URL" &

# Keep script alive so the app process stays supervised
wait $APP_PID
