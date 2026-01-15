#!/bin/bash

echo "Installing Camcookie Control Center + Theme Engine (no Chromium)..."

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
sudo apt install -y python3 python3-pip omxplayer xdg-utils

# ---------- DOWNLOAD ICON ----------
wget -O $HOME/camcookie/control-center/ui/icon.png \
https://camcookie876.github.io/PI/appstore/app/icons/camcookie-control.png

# ---------- THEME IMPORTER ----------
cat > $HOME/camcookie/theme-engine/import_theme.py << 'EOF'
import json, base64, os

HOME = os.path.expanduser("~")
BASE = f"{HOME}/camcookie"

def save_file(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(base64.b64decode(data))

def apply_theme(json_path):
    with open(json_path, "r") as f:
        theme = json.load(f)

    if "wallpapers" in theme:
        for name, data in theme["wallpapers"].items():
            save_file(f"{BASE}/theme-wallpapers/{name}.png", data)

    if "notifications" in theme and "video" in theme["notifications"]:
        save_file(f"{BASE}/theme-videos/notification.mp4",
                  theme["notifications"]["video"])

    if "sounds" in theme:
        for name, data in theme["sounds"].items():
            save_file(f"{BASE}/theme-sounds/{name}.mp3", data)

    if "appearance" in theme and "iconPack" in theme["appearance"]:
        save_file(f"{BASE}/theme-icons/icons.zip",
                  theme["appearance"]["iconPack"])

    print("Theme applied successfully!")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: import_theme.py <theme.json>")
    else:
        apply_theme(sys.argv[1])
EOF

# ---------- THEMESTORE DOWNLOADER ----------
cat > $HOME/camcookie/theme-engine/download_theme.py << 'EOF'
import json, os, urllib.request

HOME = os.path.expanduser("~")
STORE = f"{HOME}/camcookie/themestore"

def download_theme(name, version):
    kjson_path = f"{STORE}/{name}.kjson"
    if not os.path.exists(kjson_path):
        print("Theme not found in ThemeStore.")
        return

    with open(kjson_path, "r") as f:
        data = json.load(f)

    if "versions" not in data or version not in data["versions"]:
        print("Version not found.")
        return

    url = data["versions"][version]["url"]
    out = f"{STORE}/versions/{name}-{version}.json"

    urllib.request.urlretrieve(url, out)
    print(f"Downloaded {name} version {version} to {out}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: download_theme.py <name> <version>")
    else:
        download_theme(sys.argv[1], sys.argv[2])
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
from http.server import SimpleHTTPRequestHandler, HTTPServer
import json, os, subprocess

HOME = os.path.expanduser("~")
BASE = f"{HOME}/camcookie"

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/system":
            data = {
                "wallpapers": os.listdir(f"{BASE}/theme-wallpapers"),
                "sounds": os.listdir(f"{BASE}/theme-sounds"),
                "videos": os.listdir(f"{BASE}/theme-videos"),
                "themes": os.listdir(f"{BASE}/themestore/versions")
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        else:
            if self.path == "/":
                self.path = "/index.html"
            return super().do_GET()

    def do_POST(self):
        if self.path == "/api/import":
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            data = json.loads(body.decode())
            theme_path = data.get("path")
            if not theme_path:
                self.send_response(400)
                self.end_headers()
                return
            subprocess.run(["python3", f"{BASE}/theme-engine/import_theme.py", theme_path])
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    os.chdir(f"{BASE}/control-center/ui")
    server = HTTPServer(("0.0.0.0", 8787), Handler)
    print("Camcookie Control Center running on http://localhost:8787")
    server.serve_forever()
EOF

# ---------- UI: INDEX ----------
cat > $HOME/camcookie/control-center/ui/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Camcookie Control Center</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div id="app">
    <aside class="sidebar">
      <h1>Camcookie</h1>
      <button onclick="showPage('home')">Home</button>
      <button onclick="showPage('appearance')">Appearance</button>
      <button onclick="showPage('notifications')">Notifications</button>
      <button onclick="showPage('themes')">Themes</button>
      <button onclick="showPage('themestore')">ThemeStore</button>
      <button onclick="showPage('accessories')">Accessories</button>
      <button onclick="showPage('system')">System</button>
    </aside>
    <main class="main">
      <section id="home" class="page active">
        <h2>Welcome</h2>
        <p>Camcookie Control Center for Raspberry Pi.</p>
      </section>

      <section id="appearance" class="page">
        <h2>Appearance</h2>
        <p>Future: colors, fonts, icons, wallpapers.</p>
      </section>

      <section id="notifications" class="page">
        <h2>Notifications</h2>
        <p>Future: notification style, video, sounds.</p>
      </section>

      <section id="themes" class="page">
        <h2>Installed Themes</h2>
        <button onclick="refreshSystem()">Refresh</button>
        <ul id="themes-list"></ul>
        <h3>Import Theme JSON</h3>
        <input type="text" id="theme-path" placeholder="/home/pi/Downloads/mytheme.json">
        <button onclick="importTheme()">Import</button>
      </section>

      <section id="themestore" class="page">
        <h2>ThemeStore</h2>
        <p>Future: list themes from themestore.json, pick version, download.</p>
      </section>

      <section id="accessories" class="page">
        <h2>Accessories</h2>
        <ul id="accessories-list"></ul>
      </section>

      <section id="system" class="page">
        <h2>System Info</h2>
        <pre id="system-info"></pre>
      </section>
    </main>
  </div>
  <script src="app.js"></script>
</body>
</html>
EOF

# ---------- UI: STYLE ----------
cat > $HOME/camcookie/control-center/ui/style.css << 'EOF'
body {
  margin: 0;
  font-family: system-ui, sans-serif;
  background: #101010;
  color: #f5f5f5;
}
#app {
  display: flex;
  height: 100vh;
}
.sidebar {
  width: 220px;
  background: #181818;
  padding: 16px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.sidebar h1 {
  margin-top: 0;
  margin-bottom: 16px;
  font-size: 20px;
}
.sidebar button {
  background: #252525;
  border: none;
  color: #f5f5f5;
  padding: 8px 10px;
  text-align: left;
  border-radius: 6px;
  cursor: pointer;
}
.sidebar button:hover {
  background: #333333;
}
.main {
  flex: 1;
  padding: 16px;
  box-sizing: border-box;
  overflow: auto;
}
.page {
  display: none;
}
.page.active {
  display: block;
}
button {
  font-family: inherit;
}
input[type="text"] {
  width: 100%;
  max-width: 400px;
  padding: 6px 8px;
  border-radius: 4px;
  border: 1px solid #444;
  background: #181818;
  color: #f5f5f5;
}
EOF

# ---------- UI: APP.JS ----------
cat > $HOME/camcookie/control-center/ui/app.js << 'EOF'
function showPage(id) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(id).classList.add('active');

  if (id === "accessories") loadAccessories();
}

async function refreshSystem() {
  const res = await fetch('/api/system');
  const data = await res.json();
  document.getElementById('system-info').textContent = JSON.stringify(data, null, 2);

  const list = document.getElementById('themes-list');
  list.innerHTML = '';
  data.themes.forEach(t => {
    const li = document.createElement('li');
    li.textContent = t;
    list.appendChild(li);
  });
}

async function importTheme() {
  const path = document.getElementById('theme-path').value.trim();
  if (!path) return alert('Enter a theme JSON path.');
  await fetch('/api/import', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ path })
  });
  alert('Import command sent.');
}

async function loadAccessories() {
  const res = await fetch('/api/accessories');
  const data = await res.json();
  const list = document.getElementById('accessories-list');
  list.innerHTML = '';
  data.apps.forEach(app => {
    const li = document.createElement('li');
    li.textContent = app;
    list.appendChild(li);
  });
}
EOF

# ---------- EXTEND BACKEND FOR ACCESSORIES ----------
python3 - << 'EOF'
import os, fileinput, sys
HOME = os.path.expanduser("~")
path = f"{HOME}/camcookie/control-center/backend/server.py"
text = open(path).read()
if "api/accessories" not in text:
    insert = """
        elif self.path == "/api/accessories":
            apps = sorted(os.listdir("/usr/share/applications"))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"apps": apps}).encode())
"""
    text = text.replace("        if self.path == \"/api/system\":", "        if self.path == \"/api/system\":")\
               .replace("        else:\n            if self.path == \"/\":", insert + "\n        else:\n            if self.path == \"/\":")
    open(path, "w").write(text)
EOF

# ---------- LAUNCHER ----------
cat > $HOME/camcookie/control-center/launch.sh << 'EOF'
#!/bin/bash
python3 "$HOME/camcookie/control-center/backend/server.py" &
sleep 2
xdg-open http://localhost:8787
EOF
chmod +x $HOME/camcookie/control-center/launch.sh

# ---------- RASPBERRY PI MENU ENTRY ----------
mkdir -p $HOME/.local/share/applications

cat > $HOME/.local/share/applications/camcookiethemes.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Camcookie Themes
Comment=Customize your Raspberry Pi with CUT themes, wallpapers, sounds, and system styling.
Exec=/home/pi/camcookie/control-center/launch.sh
Icon=/home/pi/camcookie/control-center/ui/icon.png
Terminal=false
Categories=Settings;Utility;
EOF

# ---------- ALIASES ----------
echo 'alias camcookie-import="python3 $HOME/camcookie/theme-engine/import_theme.py"' >> ~/.bashrc
echo 'alias camcookie-control="$HOME/camcookie/control-center/launch.sh"' >> ~/.bashrc

echo "🎉 Installation complete!"
echo "Open Camcookie Themes from the Raspberry Pi menu."