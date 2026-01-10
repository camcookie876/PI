#!/usr/bin/env python3
import time
import threading
import serial
import serial.tools.list_ports
import uinput
import webview
import json
import os

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
#  Arduino Plugin (UNO Serial)
# ============================================================
class ArduinoPlugin:
    def __init__(self, ui_api):
        self.ui_api = ui_api
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
        port = self.find_arduino()
        if not port:
            self.ui_api.update_status("Arduino", "Not Found")
            return

        try:
            self.serial_port = serial.Serial(port, 9600, timeout=1)
            self.running = True
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()
            self.ui_api.update_status("Arduino", f"Connected on {port}")
        except Exception as e:
            self.ui_api.update_status("Arduino", f"Error: {e}")

    def _loop(self):
        while self.running:
            try:
                line = self.serial_port.readline().decode(errors="ignore").strip()
                if not line:
                    continue

                self.ui_api.update_arduino_data(line)

                parts = line.split()

                if parts[0] == "MOVE" and len(parts) == 3:
                    dx = max(min(int(parts[1]), 20), -20)
                    dy = max(min(int(parts[2]), 20), -20)
                    MOUSE.move(dx, dy)

                elif parts[0] == "CLICK":
                    MOUSE.click()

            except Exception:
                pass

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        if self.serial_port:
            self.serial_port.close()


# ============================================================
#  UI API (Python ↔ JavaScript Bridge)
# ============================================================
class UI_API:
    def __init__(self):
        self.status = {
            "Arduino": "Idle"
        }
        self.arduino_data = "None"

    def update_status(self, plugin, text):
        self.status[plugin] = text
        self._push()

    def update_arduino_data(self, text):
        self.arduino_data = text
        self._push()

    def _push(self):
        if window:
            window.evaluate_js(f"updateUI({json.dumps(self.status)}, '{self.arduino_data}')")


# ============================================================
#  Main
# ============================================================
ui_api = UI_API()
window = None

def main():
    global window

    # Start Arduino plugin
    arduino = ArduinoPlugin(ui_api)
    arduino.start()

    # Start UI
    html_path = os.path.join(os.path.dirname(__file__), "web/index.html")
    window = webview.create_window("Camcookie Plugin", html_path, width=700, height=500)
    webview.start()

    arduino.stop()


if __name__ == "__main__":
    main()