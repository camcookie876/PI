#!/bin/bash

echo "🍪 Installing Camcookie (Python-only)..."

sudo apt update
sudo apt install -y python3 python3-pip python3-tk xdg-utils

mkdir -p $HOME/camcookie/theme-engine
mkdir -p $HOME/camcookie/theme-wallpapers
mkdir -p $HOME/camcookie/theme-sounds
mkdir -p $HOME/camcookie/theme-icons
mkdir -p $HOME/camcookie/theme-videos
mkdir -p $HOME/camcookie/themestore/versions
mkdir -p $HOME/camcookie/control-center

# Download Python app
wget -O $HOME/camcookie/control-center/app.py \
https://camcookie876.github.io/PI/camcookie_theme/code/app.py

# Download theme engine
wget -O $HOME/camcookie/theme-engine/import_theme.py \
https://camcookie876.github.io/PI/camcookie_theme/code/import_theme.py

wget -O $HOME/camcookie/theme-engine/download_theme.py \
https://camcookie876.github.io/PI/camcookie_theme/code/download_theme.py

# Download ThemeStore
wget -O $HOME/camcookie/themestore/themestore.json \
https://camcookie876.github.io/PI/camcookie_theme/themestore.json

# Launcher
echo '#!/bin/bash' > $HOME/camcookie/control-center/launch.sh
echo 'python3 $HOME/camcookie/control-center/app.py' >> $HOME/camcookie/control-center/launch.sh
chmod +x $HOME/camcookie/control-center/launch.sh

# Menu entry
mkdir -p $HOME/.local/share/applications

cat > $HOME/.local/share/applications/camcookiethemes.desktop << EOF
[Desktop Entry]
Type=Application
Name=Camcookie Themes
Exec=/home/pi/camcookie/control-center/launch.sh
Icon=/home/pi/camcookie/control-center/icon.png
Terminal=false
Categories=Settings;
EOF

echo "🎉 Camcookie installed!"