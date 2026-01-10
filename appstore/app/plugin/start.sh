#!/bin/bash

APP_DIR="$HOME/camcookieplugin"
APP_PY="$APP_DIR/app.py"

# Start backend if not running
if ! pgrep -f "$APP_PY" > /dev/null; then
  python3 "$APP_PY" &
  sleep 1
fi

# Launch Chromium App Mode
chromium --app="file://$APP_DIR/web/index.html"