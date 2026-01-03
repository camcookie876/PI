#!/bin/bash

echo "Installing Camcookie Appstore V10..."

HOME_DIR="$HOME"

# Create config directories
mkdir -p "$HOME_DIR/.camcookie/icons"
mkdir -p "$HOME_DIR/.local/share/applications"

# Download latest Appstore V10 script
wget https://camcookie876.github.io/app/appstore/camcookie-appstore.py -O "$HOME_DIR/camcookie-appstore.py"

# Make executable
chmod +x "$HOME_DIR/camcookie-appstore.py"

# Remove old desktop icon if it exists
if [ -f "$HOME_DIR/Desktop/Camcookie-Appstore.desktop" ]; then
    rm "$HOME_DIR/Desktop/Camcookie-Appstore.desktop"
fi

# Create menu launcher
cat > "$HOME_DIR/.local/share/applications/camcookie-appstore.desktop" << EOF
[Desktop Entry]
Name=Camcookie Appstore
Comment=Install and manage Camcookie OS apps
Exec=python3 $HOME_DIR/camcookie-appstore.py
Icon=software-store
Terminal=false
Type=Application
Categories=Utility;Accessories;
EOF

# Make menu entry executable
chmod +x "$HOME_DIR/.local/share/applications/camcookie-appstore.desktop"

# Create installed versions database if missing
if [ ! -f "$HOME_DIR/.camcookie_installed.json" ]; then
    echo "{}" > "$HOME_DIR/.camcookie_installed.json"
fi

# Refresh menu
update-desktop-database "$HOME_DIR/.local/share/applications" >/dev/null 2>&1

echo "Camcookie Appstore V10 installed successfully!"
echo "Launch it from Menu → Accessories → Camcookie Appstore"