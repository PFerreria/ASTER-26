#!/bin/bash
# Waits for the ASTER-26 server then opens Chromium
APP_URL="http://127.0.0.1:8050"
MAX_WAIT=30

elapsed=0
until curl -s --head "$APP_URL" > /dev/null 2>&1; do
    sleep 1
    elapsed=$((elapsed + 1))
    [ "$elapsed" -ge "$MAX_WAIT" ] && break
done

chromium-browser --start-fullscreen "$APP_URL"
