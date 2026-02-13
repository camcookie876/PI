#!/bin/bash

echo "=== Installing Camcookie Chat (Pi Edition) ==="

# Update system
sudo apt update
sudo apt install -y python3 python3-pip

echo "=== Installing Playwright ==="
pip3 install playwright

echo "=== Downloading Chromium (Playwright browser) ==="
python3 - << 'EOF'
from playwright.sync_api import sync_playwright
print("Downloading Chromium...")
with sync_playwright() as p:
    p.chromium.install()
EOF

echo "=== Creating Camcookie Chat App Folder ==="
mkdir -p $HOME/camcookie-chat
cd $HOME/camcookie-chat

echo "=== Writing Python Chat App ==="
cat << 'EOF' > chat.py
import json
import os
from playwright.sync_api import sync_playwright

SESSION_FILE = "/home/pi/.camcookie_session.json"

def read_connect_session(page):
    return page.evaluate("""
        () => {
            return {
                token: localStorage.getItem("connect26_token"),
                user: localStorage.getItem("connect26_user"),
                refresh: localStorage.getItem("connect26_refresh")
            };
        }
    """)

def inject_session(page, session):
    page.evaluate(f"""
        localStorage.setItem("connect26_token", "{session['token']}");
        localStorage.setItem("connect26_user", "{session['user']}");
        localStorage.setItem("connect26_refresh", "{session['refresh']}");
    """)

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Load Connect 26 login page
        page.goto("https://camcookie876.github.io/connect/26/")
        page.wait_for_timeout(3000)

        # Read session from Connect 26
        session = read_connect_session(page)
        print("Session:", session)

        # Save session locally
        with open(SESSION_FILE, "w") as f:
            json.dump(session, f)

        # Load Chat App
        page.goto("https://camcookie876.github.io/chat/home/")
        page.wait_for_timeout(1000)

        # Inject session into Chat
        inject_session(page, session)

        print("Chat loaded with Connect 26 session.")
        page.wait_for_timeout(99999999)

if __name__ == "__main__":
    main()
EOF

echo "=== Creating Launcher Script ==="
cat << 'EOF' > run-chat.sh
#!/bin/bash
python3 $HOME/camcookie-chat/chat.py
EOF

chmod +x run-chat.sh

echo "=== Creating Desktop Icon ==="
mkdir -p $HOME/.local/share/applications
cat << 'EOF' > $HOME/.local/share/applications/camcookie-chat.desktop
[Desktop Entry]
Name=Camcookie Chat
Comment=Chat with Camcookie
Exec=bash /home/pi/camcookie-chat/run-chat.sh
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Network;
EOF

echo "=== Camcookie Chat Installed Successfully ==="