import json, os, urllib.request, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = "0.0.0.0"
PORT = 8080
PLUGIN = "http://127.0.0.1:8765"
APP_ID = "camcookieactions"

def pget(path, params=None):
    if params is None:
        params = {}
    params["app_id"] = APP_ID
    url = f"{PLUGIN}{path}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=2) as r:
        t = r.read().decode("utf-8")
        try:
            return json.loads(t)
        except:
            return {"raw": t}

def load_actions():
    with open("actions.json") as f:
        return json.load(f)

ACTIONS = load_actions()
STATE = {
    "last_action": None,
    "lamp": "off",
    "last_temp": None,
    "last_controller": None
}

def run_action(action_id):
    a = ACTIONS.get(action_id)
    if not a:
        return False
    k = a.get("kind")
    if k == "plugin_led":
        on = int(a.get("on", 1))
        pget("/led/set", {"on": on})
        STATE["lamp"] = "on" if on else "off"
        STATE["last_action"] = action_id
        return True
    if k == "plugin_mouse_move":
        dx = a.get("dx", 0)
        dy = a.get("dy", 0)
        pget("/mouse/move", {"dx": dx, "dy": dy})
        STATE["last_action"] = action_id
        return True
    if k == "plugin_mouse_click":
        pget("/mouse/click")
        STATE["last_action"] = action_id
        return True
    if k == "plugin_temp":
        d = pget("/temp/read")
        STATE["last_temp"] = d.get("temp")
        STATE["last_action"] = action_id
        return True
    return False

def run_command(text):
    t = text.lower().strip()
    for aid, a in ACTIONS.items():
        if t == a.get("command", "").lower():
            if run_action(aid):
                return aid
    return None

class H(BaseHTTPRequestHandler):
    def _json(self, d, c=200):
        b = json.dumps(d).encode("utf-8")
        self.send_response(c)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _file(self, path, ct):
        if not os.path.exists(path):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"not found")
            return
        with open(path, "rb") as f:
            b = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._file("index.html", "text/html; charset=utf-8")
            return
        if self.path == "/api/actions":
            self._json(ACTIONS)
            return
        if self.path == "/api/state":
            self._json(STATE)
            return
        self._json({"error": "not_found"}, 404)

    def do_POST(self):
        l = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(l).decode("utf-8") if l > 0 else ""
        body = json.loads(raw) if raw else {}

        if self.path.startswith("/api/run/"):
            aid = self.path.split("/api/run/")[1]
            ok = run_action(aid)
            self._json({"ok": ok, "action_id": aid})
            return

        if self.path == "/api/voice":
            t = body.get("text", "")
            m = run_command(t)
            self._json({"matched": m})
            return

        if self.path == "/api/controller/button":
            b = body.get("button")
            STATE["last_controller"] = b
            self._json({"ok": True})
            return

        self._json({"error": "not_found"}, 404)

def start():
    s = HTTPServer((HOST, PORT), H)
    print(f"Camcookie Actions at http://{HOST}:{PORT}")
    s.serve_forever()

if __name__ == "__main__":
    start()