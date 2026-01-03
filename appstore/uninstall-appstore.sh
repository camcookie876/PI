#!/bin/bash

echo "Uninstalling Camcookie Appstore V10..."

HOME_DIR="$HOME"

# Remove Appstore script
if [ -f "$HOME_DIR/camcookie-appstore.py" ]; then
    rm "$HOME_DIR/camcookie-appstore.py"
    echo "Removed Appstore script."
fi

# Remove menu entry
if [ -f "$HOME_DIR/.local/share/applications/camcookie-appstore.desktop" ]; then
    rm "$HOME_DIR/.local/share/applications/camcookie-appstore.desktop"
    echo "Removed menu launcher."
fi

# Remove installed versions database
if [ -f "$HOME_DIR/.camcookie_installed.json" ]; then
    rm "$HOME_DIR/.camcookie_installed.json"
    echo "Removed installed versions database."
fi

# Remove icon cache folder
if [ -d "$HOME_DIR/.camcookie/icons" ]; then
    rm -r "$HOME_DIR/.camcookie/icons"
    echo "Removed icon cache."
fi

# Refresh menu
update-desktop-database "$HOME_DIR/.local/share/applications" >/dev/null 2>&1

echo "Camcookie Appstore V10 has been fully uninstalled."