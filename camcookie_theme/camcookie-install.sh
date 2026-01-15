#!/bin/bash

echo "Installing Camcookie Control Center + Theme Engine..."

# ---------- FOLDERS ----------
mkdir -p $HOME/camcookie/themes
mkdir -p $HOME/camcookie/theme-engine
mkdir -p $HOME/camcookie/theme-videos
mkdir -p $HOME/camcookie/theme-sounds
mkdir -p $HOME/camcookie/theme-icons
mkdir -p $HOME/camcookie/theme-wallpapers
mkdir -p $HOME/camcookie/theme-cache
mkdir -p $HOME/camcookie/themestore
mkdir -p $HOME/camcookie/themestore/versions
mkdir -p $HOME/camcookie/control-center/ui
mkdir -p $HOME/camcookie/control-center/backend

# ---------- DEPENDENCIES ----------
sudo apt update
sudo apt install -y python3 python3-pip omxplayer chromium-browser

# ---------- DOWNLOAD ICON ----------
wget -O $HOME/camcookie/control-center/ui/icon.png \
https://camcookie876.github.io/PI/appstore/app/icons/camcookie-control.png

# ---------- THEME IMPORTER ----------
cat > $HOME/camcookie/theme-engine/import_theme.py << 'EOF'
# (same importer code you already have)
EOF

# ---------- THEMESTORE DOWNLOADER ----------
cat > $HOME/camcookie/theme-engine/download_theme.py << 'EOF'
# (same downloader code you already have)
EOF

# ---------- NOTIFICATION VIDEO PLAYER ----------
cat > $HOME/camcookie/theme-engine/play_notification_video.sh << 'EOF'
#!/bin/bash
VIDEO="$HOME/camcookie/theme-videos/notification.mp4"
if [ -f "$VIDEO" ]; then
  omxplayer --no-osd --layer 9999 "$VIDEO"
fi
EOF
chmod +x $HOME/camcookie/theme-engine/play_notification_video.sh

# ---------- BACKEND SERVER ----------
cat > $HOME/camcookie/control-center/backend/server.py << 'EOF'
# (same backend code you already have)
EOF

# ---------- UI FILES ----------
cat > $HOME/camcookie/control-center/ui/index.html << 'EOF'
# (same index.html you already have)
EOF

cat > $HOME/camcookie/control-center/ui/style.css << 'EOF'
# (same style.css you already have)
EOF

cat > $HOME/camcookie/control-center/ui/app.js << 'EOF'
# (same app.js you already have)
EOF

# ---------- LAUNCHER ----------
cat > $HOME/camcookie/control-center/launch.sh << 'EOF'
#!/bin/bash
python3 "$HOME/camcookie/control-center/backend/server.py" &
sleep 2
chromium-browser --app=http://localhost:8787 --start-fullscreen
EOF
chmod +x $HOME/camcookie/control-center/launch.sh

# ---------- RASPBERRY PI MENU ENTRY ----------
mkdir -p $HOME/.local/share/applications

cat > $HOME/.local/share/applications/camcookie-control.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Camcookie Control Center
Comment=Customize your Raspberry Pi with themes, notifications, accessories, and system tools.
Exec=/home/pi/camcookie/control-center/launch.sh
Icon=/home/pi/camcookie/control-center/ui/icon.png
Terminal=false
Categories=Settings;Utility;
EOF

# ---------- ALIASES ----------
echo 'alias camcookie-import="python3 $HOME/camcookie/theme-engine/import_theme.py"' >> ~/.bashrc
echo 'alias camcookie-control="$HOME/camcookie/control-center/launch.sh"' >> ~/.bashrc

echo "🎉 Installation complete!"
echo "Restart your terminal and open Camcookie Control Center from the Raspberry Pi menu."