#!/bin/bash
echo "Downloading Camcookie installer..."
wget -O $HOME/camcookie-install.sh https://camcookie876.github.io/PI/camcookie_theme/download/camcookie-install.sh
chmod +x $HOME/camcookie-install.sh
$HOME/camcookie-install.sh