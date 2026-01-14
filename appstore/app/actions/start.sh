#!/bin/bash

# Start backend if not already running
if ! pgrep -f "python3 $HOME/camcookie-actions/app.py" > /dev/null; then
    nohup python3 $HOME/camcookie-actions/app.py >/dev/null 2>&1 &
fi

# Launch Chromium App Mode
chromium-browser --app="file://$HOME/camcookie-actions/index.html" --window-size=800,600