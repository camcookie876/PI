#!/usr/bin/env python3
import time
import threading
import subprocess
import serial
import serial.tools.list_ports
import tkinter as tk
import RPi.GPIO as GPIO

# ============================================================
#  CAMCOOKIE PLUGIN — VERSION 2
#  Styled UI + Instructions + Arduino Serial Support
# ============================================================

# ------------------------------------------------------------
# Helper functions for mouse control (xdotool)
# ------------------------------------------------------------
def move_mouse(dx, dy):
    subprocess.run(["xdotool", "mousemove_relative", "--", str(dx), str(dy)])

def click_mouse():
    subprocess.run(["xdotool", "click", "1"])


# ------------------------------------------------------------
# Base Plugin Class
# ------------------------------------------------------------
class BasePlugin:
    def __init__(self, manager):
        self.manager = manager
        self.status = "Idle"

    def start(self):
        pass

    def stop(self):
        pass

    def get_status(self):
        return self.status


# ------------------------------------------------------------
# CookieJoystick Plugin (GPIO)
# ------------------------------------------------------------
class CookieJoystick(BasePlugin):
    PIN_UP = 17
    PIN_DOWN = 27
    PIN_LEFT = 22
    PIN_RIGHT = 23
    PIN_CLICK = 24

    CURSOR_STEP = 5
    LOOP_DELAY = 0.02

    def __init__(self, manager):
        super().__init__(manager)

        self.up = False
        self.down = False
        self.left = False
        self.right = False

        self.running = False
        self.thread = None

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        for pin in (self.PIN_UP, self.PIN_DOWN, self.PIN_LEFT, self.PIN_RIGHT, self.PIN_CLICK):
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        GPIO.add_event_detect(self.PIN_UP, GPIO.BOTH, callback=self._up, bouncetime=30)
        GPIO.add_event_detect(self.PIN_DOWN, GPIO.BOTH, callback=self._down, bouncetime=30)
        GPIO.add_event_detect(self.PIN_LEFT, GPIO.BOTH, callback=self._left, bouncetime=30)
        GPIO.add_event_detect(self.PIN_RIGHT, GPIO.BOTH, callback=self._right, bouncetime=30)
        GPIO.add_event_detect(self.PIN_CLICK, GPIO.FALLING, callback=self._click, bouncetime=150)

    def _up(self, ch): self.up = (GPIO.input(self.PIN_UP) == GPIO.LOW)
    def _down(self, ch): self.down = (GPIO.input(self.PIN_DOWN) == GPIO.LOW)
    def _left(self, ch): self.left = (GPIO.input(self.PIN_LEFT) == GPIO.LOW)
    def _right(self, ch): self.right = (GPIO.input(self.PIN_RIGHT) == GPIO.LOW)

    def _click(self, ch):
        click_mouse()
        self.status = "Click"

    def _loop(self):
        while self.running:
            dx = dy = 0

            if self.up and not self.down: dy -= self.CURSOR_STEP
            elif self.down and not self.up: dy += self.CURSOR_STEP

            if self.left and not self.right: dx -= self.CURSOR_STEP
            elif self.right and not self.left: dx += self.CURSOR_STEP

            if dx or dy:
                move_mouse(dx, dy)
                self.status = f"Moving ({dx},{dy})"
            else:
                self.status = "Idle"

            time.sleep(self.LOOP_DELAY)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print("[CookieJoystick] Started")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        print("[CookieJoystick] Stopped")


# ------------------------------------------------------------
# Arduino Serial Plugin
# ------------------------------------------------------------
class ArduinoPlugin(BasePlugin):
    def __init__(self, manager):
        super().__init__(manager)
        self.running = False
        self.thread = None
        self.serial_port = None

    def find_arduino(self):
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if "Arduino" in p.description or "ttyACM" in p.device:
                return p.device
        return None

    def start(self):
        port = self.find_arduino()
        if not port:
            self.status = "No Arduino found"
            return

        try:
            self.serial_port = serial.Serial(port, 9600, timeout=1)
            self.running = True
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()
            self.status = "Connected"
        except Exception as e:
            self.status = f"Error: {e}"

    def _loop(self):
        while self.running:
            try:
                line = self.serial_port.readline().decode().strip()
                if line:
                    self.status = f"Data: {line}"

                    # Example protocol:
                    # MOVE x y
                    # CLICK
                    parts = line.split()

                    if parts[0] == "MOVE" and len(parts) == 3:
                        dx = int(parts[1])
                        dy = int(parts[2])
                        move_mouse(dx, dy)

                    elif parts[0] == "CLICK":
                        click_mouse()

            except:
                self.status = "Serial error"

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        if self.serial_port:
            self.serial_port.close()
        print("[ArduinoPlugin] Stopped")


# ------------------------------------------------------------
# Plugin Manager
# ------------------------------------------------------------
class PluginManager:
    def __init__(self):
        self.plugins = []

    def register(self, plugin_class):
        plugin = plugin_class(self)
        self.plugins.append(plugin)
        return plugin

    def start_all(self):
        for p in self.plugins:
            p.start()

    def stop_all(self):
        for p in self.plugins:
            p.stop()

    def get_statuses(self):
        return [(type(p).__name__, p.get_status()) for p in self.plugins]


# ------------------------------------------------------------
# Styled UI
# ------------------------------------------------------------
class CamcookieUI:
    def __init__(self, manager):
        self.manager = manager
        self.root = tk.Tk()
        self.root.title("Camcookie Plugin")
        self.root.geometry("450x360")
        self.root.configure(bg="#e8e8ff")

        # Title
        tk.Label(
            self.root,
            text="Camcookie Plugin",
            font=("Arial Rounded MT Bold", 20),
            bg="#e8e8ff"
        ).pack(pady=10)

        # Instructions box
        frame = tk.Frame(self.root, bg="#ffffff", bd=2, relief="ridge")
        frame.pack(pady=10, padx=20, fill="x")

        tk.Label(
            frame,
            text="• Joystick controls your mouse\n"
                 "• Press down to click\n"
                 "• Arduino can send MOVE and CLICK commands\n"
                 "• More plugins coming soon!",
            font=("Arial", 12),
            bg="#ffffff",
            justify="left"
        ).pack(padx=10, pady=10)

        # Status panel
        self.status_frame = tk.Frame(self.root, bg="#e8e8ff")
        self.status_frame.pack(pady=10)

        self.status_labels = []

        self.update_loop()

    def update_loop(self):
        for label in self.status_labels:
            label.destroy()
        self.status_labels.clear()

        statuses = self.manager.get_statuses()
        for name, status in statuses:
            lbl = tk.Label(
                self.status_frame,
                text=f"{name}: {status}",
                font=("Arial", 11),
                bg="#e8e8ff"
            )
            lbl.pack()
            self.status_labels.append(lbl)

        self.root.after(500, self.update_loop)

    def run(self):
        self.root.mainloop()


# ------------------------------------------------------------
# Main App
# ------------------------------------------------------------
def main():
    print("=== Camcookie Plugin v2 ===")

    manager = PluginManager()

    manager.register(CookieJoystick)
    manager.register(ArduinoPlugin)

    manager.start_all()

    ui = CamcookieUI(manager)
    try:
        ui.run()
    finally:
        manager.stop_all()
        GPIO.cleanup()
        print("Goodbye!")


if __name__ == "__main__":
    main()