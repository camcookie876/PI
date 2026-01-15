import os
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, HTTPServer
import json
import subprocess

HOME = os.path.expanduser("~")
BASE = f"{HOME}/camcookie"

UI_DIR = f"{BASE}/control-center/ui"
THEME_DIR = f"{BASE}/theme-engine"
STORE_DIR = f"{BASE}/themestore"

# ------------------------------
# Backend API
# ------------------------------

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/system":
            data = {
                "wallpapers": os.listdir(f"{BASE}/theme-wallpapers"),
                "sounds": os.listdir(f"{BASE}/theme-sounds"),
                "themes": os.listdir(f"{BASE}/themestore/versions")
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
            return

        if self.path == "/api/themestore":
            store_path = f"{BASE}/themestore/themestore.json"
            if os.path.exists(store_path):
                with open(store_path, "r") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(data.encode())
            else:
                self.send_response(404)
                self.end_headers()
            return

        if self.path == "/":
            self.path = "/index.html"

        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/import":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body.decode())
            theme_path = data.get("path")

            if theme_path:
                subprocess.run(["python3", f"{THEME_DIR}/import_theme.py", theme_path])

            self.send_response(200)
            self.end_headers()
            return

        self.send_response(404)
        self.end_headers()


# ------------------------------
# Start server + open browser
# ------------------------------

def start_server():
    os.chdir(UI_DIR)
    server = HTTPServer(("0.0.0.0", 8787), Handler)
    print("Camcookie Control Center running at http://localhost:8787")
    server.serve_forever()

def main():
    threading.Thread(target=start_server, daemon=True).start()
    webbrowser.open("http://localhost:8787")

if __name__ == "__main__":
    main()