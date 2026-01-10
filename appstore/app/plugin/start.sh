#!/bin/bash
# Camcookie Plugin V1.5 - Chromium App Mode launcher

APP_DIR="$HOME/camcookieplugin"
APP_PY="$APP_DIR/app.py"

# Start backend if not already running
if ! pgrep -f "$APP_PY" > /dev/null; then
  python3 "$APP_PY" &
  sleep 1
fi

# Launch Chromium in app mode
chromium-browser --app="file://$APP_DIR/web/index.html"