#!/bin/bash

echo "Downloading Camcookie Control Center installer..."

wget -O $HOME/camcookie-install.sh \
https://camcookie876.github.io/PI/camcookie_theme/download/camcookie-install.sh

chmod +x $HOME/camcookie-install.sh

echo "Running installer..."
$HOME/camcookie-install.sh