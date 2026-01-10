#!/usr/bin/env python3
import time
import threading
import serial
import serial.tools.list_ports
import uinput
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import requests

# ============================================================
#  Paths / constants
# ============================================================
HOME = os.path.expanduser("~")
INSTALLED_FILE = os.path.join(HOME, ".camcookie_installed.json")
CONNECTED_FILE = os.path.join(HOME, ".camcookie_connected.json")
APPSTORE_URL = "https://camcookie876.github.io/PI/appstore/appstore.json"

HTTP_HOST = "127.0.0.1"
HTTP_PORT = 8765
SHUTDOWN_DELAY_SECONDS = 5


# ============================================================
#  Virtual Mouse (Wayland-safe)
# ============================================================
class MouseController:
    def __init__(self):
        self.device = uinput.Device([
            uinput.REL_X,
            uinput.REL_Y,
            uinput.BTN_LEFT,
        ])

    def move(self, dx, dy):
        self.device.emit(uinput.REL_X, dx)
        self.device.emit(uinput.REL_Y, dy)

    def click(self):
        self.device.emit(uinput.BTN_LEFT, 1)
        self.device.emit(uinput.BTN_LEFT, 0)


MOUSE = MouseController()


# ============================================================
#  Plugin Base
# ============================================================
class BasePlugin:
    def __init__(self, manager, plugin_id, name):
        self.manager = manager
        self.id = plugin_id
        self.name = name
        self.enabled = False
        self.status = "Idle"

    def start(self):
        self.enabled = True
        self.status = "Enabled"

    def stop(self):
        self.enabled = False
        self.status = "Disabled"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "enabled": self.enabled,
            "status": self.status,
        }


# ============================================================
#  Shared State
# ============================================================
class EngineState:
    def __init__(self):
        self.arduino_data = "None"


STATE = EngineState()


# ============================================================
#  Arduino Mouse Plugin
# ============================================================
class ArduinoMousePlugin(BasePlugin):
    def __init__(self, manager):
        super().__init__(manager, "arduino_mouse", "Arduino Mouse")
        self.running = False
        self.thread = None
        self.serial_port = None

    def find_arduino(self):
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if "ttyACM" in p.device or "ttyUSB" in p.device or "Arduino" in p.description:
                return p.device
        return None

    def start(self):
        if self.enabled:
            return
        port = self.find_arduino()
        if not port:
            self.status = "Arduino not found"
            return

        try:
            self.serial_port = serial.Serial(port, 9600, timeout=1)
            self.running = True
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()
            self.enabled = True
            self.status = f"Connected on {port}"
        except Exception as e:
            self.status = f"Error: {e}"

    def _loop(self):
        while self.running:
            try:
                line = self.serial_port.readline().decode(errors="ignore").strip()
                if not line:
                    continue

                STATE.arduino_data = line

                parts = line.split()
                if parts[0] == "MOVE" and len(parts) == 3:
                    dx = max(min(int(parts[1]), 20), -20)
                    dy = max(min(int(parts[2]), 20), -20)
                    MOUSE.move(dx, dy)
                elif parts[0] == "CLICK":
                    MOUSE.click()
            except Exception:
                time.sleep(0.05)

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        if self.serial_port:
            self.serial_port.close()
        self.enabled = False
        self.status = "Disabled"


# ============================================================
#  LED Plugin (stub, ready for future GPIO)
# ============================================================
class LedPlugin(BasePlugin):
    def __init__(self, manager):
        super().__init__(manager, "led", "LED Controller")
        self.led_state = False

    def start(self):
        self.enabled = True
        self.status = "Ready (no LEDs configured yet)"

    def stop(self):
        self.enabled = False
        self.status = "Disabled"

    def set_led(self, on):
        self.led_state = on
        self.status = "LED ON" if on else "LED OFF"


# ============================================================
#  Temperature Plugin (stub, ready for future sensor)
# ============================================================
class TempPlugin(BasePlugin):
    def __init__(self, manager):
        super().__init__(manager, "temp", "Temperature Sensor")
        self.current_temp = None

    def start(self):
        self.enabled = True
        self.status = "Ready (no sensor connected yet)"

    def stop(self):
        self.enabled = False
        self.status = "Disabled"

    def read_temp(self):
        self.current_temp = 22.5
        self.status = f"{self.current_temp} °C"
        return self.current_temp


# ============================================================
#  Plugin Manager
# ============================================================
class PluginManager:
    def __init__(self):
        self.plugins = {}

    def register(self, plugin):
        self.plugins[plugin.id] = plugin

    def get_plugins_state(self):
        return [p.to_dict() for p in self.plugins.values()]

    def enable_plugin(self, plugin_id):
        plugin = self.plugins.get(plugin_id)
        if plugin:
            plugin.start()

    def disable_plugin(self, plugin_id):
        plugin = self.plugins.get(plugin_id)
        if plugin:
            plugin.stop()

    def get_plugin(self, plugin_id):
        return self.plugins.get(plugin_id)


# ============================================================
#  Installed / Appstore / Connected helpers
# ============================================================
def load_json_file(path, default):
    try:
        if not os.path.exists(path):
            return default
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return default


def save_json_file(path, data):
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass


def load_installed_apps():
    return load_json_file(INSTALLED_FILE, {})


def load_connected_apps():
    return load_json_file(CONNECTED_FILE, {})


def save_connected_apps(data):
    save_json_file(CONNECTED_FILE, data)


def load_appstore_json():
    try:
        r = requests.get(APPSTORE_URL, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {"apps": []}


def get_connectable_apps():
    store = load_appstore_json()
    installed = load_installed_apps()
    connected = load_connected_apps()

    apps = []
    for app in store.get("apps", []):
        if app.get("plugin") == "YES":
            app_id = app["id"]
            apps.append({
                "id": app_id,
                "name": app.get("name", app_id),
                "installed": app_id in installed,
                "installed_version": installed.get(app_id),
                "icon": app.get("icon", ""),
                "description": app.get("description", ""),
                "connected": bool(connected.get(app_id, False)),
            })
    return apps


def count_connected_apps():
    connected = load_connected_apps()
    return sum(1 for v in connected.values() if v)


# ============================================================
#  Permission checks
# ============================================================
def app_is_allowed(app_id):
    installed = load_installed_apps()
    if app_id not in installed:
        return False

    store = load_appstore_json()
    for app in store.get("apps", []):
        if app.get("id") == app_id and app.get("plugin") == "YES":
            break
    else:
        return False

    connected = load_connected_apps()
    return bool(connected.get(app_id, False))


# ============================================================
#  HTTP Server
# ============================================================
plugin_manager = None
shutdown_lock = threading.Lock()


def schedule_shutdown_if_last():
    def worker():
        time.sleep(SHUTDOWN_DELAY_SECONDS)
        with shutdown_lock:
            if count_connected_apps() == 0:
                os._exit(0)
    t = threading.Thread(target=worker, daemon=True)
    t.start()


class CamcookieRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, code=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        # Allow UI served from file:// to call this API
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        # CORS preflight
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _require_app(self, qs):
        app_id = qs.get("app_id", [None])[0]
        if not app_id:
            self._send_json({"ok": False, "error": "Missing app_id"}, code=400)
            return None
        return app_id

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        # -------- Public status (UI) --------
        if path == "/status":
            data = {
                "plugins": plugin_manager.get_plugins_state(),
                "arduino_data": STATE.arduino_data,
                "connectable_apps": get_connectable_apps(),
                "connected_apps": load_connected_apps()
            }
            self._send_json(data)
            return

        # -------- Connect / Disconnect / Shutdown (by apps) --------
        if path == "/connect":
            app_id = self._require_app(qs)
            if not app_id:
                return
            connected = load_connected_apps()
            connected[app_id] = True
            save_connected_apps(connected)
            self._send_json({"ok": True, "connected": connected})
            return

        if path == "/disconnect":
            app_id = self._require_app(qs)
            if not app_id:
                return
            connected = load_connected_apps()
            if app_id in connected:
                connected[app_id] = False
            save_connected_apps(connected)
            if count_connected_apps() == 0:
                schedule_shutdown_if_last()
            self._send_json({"ok": True, "connected": connected})
            return

        if path == "/shutdown":
            app_id = self._require_app(qs)
            if not app_id:
                return
            connected = load_connected_apps()
            if app_id in connected:
                connected[app_id] = False
            save_connected_apps(connected)
            if count_connected_apps() == 0:
                schedule_shutdown_if_last()
                self._send_json({"ok": True, "shutting_down": True})
            else:
                self._send_json(
                    {"ok": True, "shutting_down": False, "reason": "Other apps still connected"}
                )
            return

        # -------- Plugin toggle (UI) --------
        if path == "/plugin/toggle":
            pid = qs.get("id", [None])[0]
            enabled_str = qs.get("enabled", ["0"])[0]
            if not pid:
                self._send_json({"ok": False, "error": "Missing id"}, code=400)
                return
            enabled = enabled_str == "1"
            if enabled:
                plugin_manager.enable_plugin(pid)
            else:
                plugin_manager.disable_plugin(pid)
            data = {
                "plugins": plugin_manager.get_plugins_state(),
                "arduino_data": STATE.arduino_data,
                "connectable_apps": get_connectable_apps(),
                "connected_apps": load_connected_apps()
            }
            self._send_json({"ok": True, "state": data})
            return

        # -------- Protected endpoints (need app_id + permission) --------
        app_id = qs.get("app_id", [None])[0]
        if app_id is None or not app_is_allowed(app_id):
            self._send_json({"ok": False, "error": "Access denied or app not connected"}, code=403)
            return

        if path == "/mouse/move":
            try:
                dx = int(qs.get("dx", [0])[0])
                dy = int(qs.get("dy", [0])[0])
                dx = max(min(dx, 50), -50)
                dy = max(min(dy, 50), -50)
                MOUSE.move(dx, dy)
                self._send_json({"ok": True})
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, code=400)
            return

        if path == "/mouse/click":
            try:
                MOUSE.click()
                self._send_json({"ok": True})
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, code=400)
            return

        if path == "/led/set":
            led = plugin_manager.get_plugin("led")
            if not led:
                self._send_json({"ok": False, "error": "LED plugin not found"}, code=404)
                return
            on_str = qs.get("on", ["0"])[0]
            led.set_led(on_str == "1")
            self._send_json({"ok": True})
            return

        if path == "/temp/read":
            temp = plugin_manager.get_plugin("temp")
            if not temp:
                self._send_json({"ok": False, "error": "Temp plugin not found"}, code=404)
                return
            value = temp.read_temp()
            self._send_json({"ok": True, "temp": value})
            return

        self._send_json({"ok": False, "error": "Unknown endpoint"}, code=404)


def start_http_server():
    server = HTTPServer((HTTP_HOST, HTTP_PORT), CamcookieRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


# ============================================================
#  Main
# ============================================================
def main():
    global plugin_manager

    plugin_manager = PluginManager()

    arduino_mouse = ArduinoMousePlugin(plugin_manager)
    led_plugin = LedPlugin(plugin_manager)
    temp_plugin = TempPlugin(plugin_manager)

    plugin_manager.register(arduino_mouse)
    plugin_manager.register(led_plugin)
    plugin_manager.register(temp_plugin)

    http_server = start_http_server()

    # Backend just runs; UI is Chromium pointing to web/index.html
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    http_server.shutdown()
    for p in plugin_manager.plugins.values():
        p.stop()


if __name__ == "__main__":
    main()