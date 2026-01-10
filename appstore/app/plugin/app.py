#!/usr/bin/env python3
import time
import threading
import serial
import serial.tools.list_ports
import tkinter as tk
import RPi.GPIO as GPIO
import uinput

# ============================================================
#  Camcookie Plugin v3
#  - Wayland-safe virtual mouse (uinput)
#  - GPIO joystick plugin
#  - Arduino serial plugin (UNO)
#  - Styled UI with live status
# ============================================================

# ------------------------------------------------------------
# Virtual mouse (uinput)
# ------------------------------------------------------------
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
        self.device.emit_click(uinput.BTN_LEFT)


MOUSE = MouseController()


# ------------------------------------------------------------
# Base Plugin
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
# CookieJoystick Plugin (GPIO digital joystick)
# ------------------------------------------------------------
class CookieJoystick(BasePlugin):
    # BCM pin numbers
    PIN_UP = 17
    PIN_DOWN = 27
    PIN_LEFT = 22
    PIN_RIGHT = 23
    PIN_CLICK = 24

    CURSOR_STEP = 3
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

        GPIO.add_event_detect(self.PIN_UP, GPIO.BOTH, callback=self._up, bouncetime=20)
        GPIO.add_event_detect(self.PIN_DOWN, GPIO.BOTH, callback=self._down, bouncetime=20)
        GPIO.add_event_detect(self.PIN_LEFT, GPIO.BOTH, callback=self._left, bouncetime=20)
        GPIO.add_event_detect(self.PIN_RIGHT, GPIO.BOTH, callback=self._right, bouncetime=20)
        GPIO.add_event_detect(self.PIN_CLICK, GPIO.FALLING, callback=self._click, bouncetime=150)

    def _up(self, ch):
        self.up = (GPIO.input(self.PIN_UP) == GPIO.LOW)

    def _down(self, ch):
        self.down = (GPIO.input(self.PIN_DOWN) == GPIO.LOW)

    def _left(self, ch):
        self.left = (GPIO.input(self.PIN_LEFT) == GPIO.LOW)

    def _right(self, ch):
        self.right = (GPIO.input(self.PIN_RIGHT) == GPIO.LOW)

    def _click(self, ch):
        MOUSE.click()
        self.status = "Click"

    def _loop(self):
        while self.running:
            dx = dy = 0

            if self.up and not self.down:
                dy -= self.CURSOR_STEP
            elif self.down and not self.up:
                dy += self.CURSOR_STEP

            if self.left and not self.right:
                dx -= self.CURSOR_STEP
            elif self.right and not self.left:
                dx += self.CURSOR_STEP

            if dx or dy:
                MOUSE.move(dx, dy)
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
# Arduino Serial Plugin (UNO, serial protocol)
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
            # UNO usually appears as ttyACM or ttyUSB
            if "ttyACM" in p.device or "ttyUSB" in p.device or "Arduino" in p.description:
                return p.device
        return None

    def start(self):
        port = self.find_arduino()
        if not port:
            self.status = "No Arduino found"
            print("[ArduinoPlugin] No Arduino found")
            return

        try:
            self.serial_port = serial.Serial(port, 9600, timeout=1)
            self.running = True
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()
            self.status = "Connected"
            print(f"[ArduinoPlugin] Connected on {port}")
        except Exception as e:
            self.status = f"Error: {e}"
            print("[ArduinoPlugin] Serial error:", e)

    def _loop(self):
        while self.running:
            try:
                line = self.serial_port.readline().decode(errors="ignore").strip()
                if not line:
                    continue

                # Example: "MOVE 1 -2" or "CLICK"
                parts = line.split()
                self.status = f"Data: {line}"

                if parts[0] == "MOVE" and len(parts) == 3:
                    try:
                        dx = int(parts[1])
                        dy = int(parts[2])
                        # Safety clamp, so crazy values don't explode
                        dx = max(min(dx, 20), -20)
                        dy = max(min(dy, 20), -20)
                        MOUSE.move(dx, dy)
                    except ValueError:
                        pass

                elif parts[0] == "CLICK":
                    MOUSE.click()

            except Exception as e:
                self.status = "Serial error"
                print("[ArduinoPlugin] Loop error:", e)
                time.sleep(0.1)

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
        self.root.geometry("540x420")
        self.root.configure(bg="#dfe3ff")

        # Header
        header = tk.Frame(self.root, bg="#4a57ff", height=60)
        header.pack(fill="x")

        tk.Label(
            header,
            text="Camcookie Plugin",
            font=("Arial Rounded MT Bold", 22),
            fg="white",
            bg="#4a57ff"
        ).pack(pady=10)

        # Instructions box
        box = tk.Frame(self.root, bg="white", bd=3, relief="ridge")
        box.pack(pady=15, padx=20, fill="x")

        tk.Label(
            box,
            text=(
                "• GPIO joystick moves the system mouse\n"
                "• Press joystick down to click\n"
                "• Arduino UNO sends commands over USB serial:\n"
                "    MOVE dx dy\n"
                "    CLICK\n"
                "• Works on Wayland using a virtual mouse (uinput)"
            ),
            font=("Arial", 12),
            bg="white",
            justify="left"
        ).pack(padx=15, pady=15)

        # Status title
        tk.Label(
            self.root,
            text="Plugin status",
            font=("Arial Rounded MT Bold", 16),
            bg="#dfe3ff"
        ).pack()

        # Status area
        self.status_frame = tk.Frame(self.root, bg="#dfe3ff")
        self.status_frame.pack(pady=10)

        self.status_labels = []

        # Footer
        footer = tk.Frame(self.root, bg="#4a57ff", height=40)
        footer.pack(side="bottom", fill="x")

        tk.Label(
            footer,
            text="Camcookie OS Hardware Engine v3 • Virtual Mouse",
            font=("Arial", 11),
            fg="white",
            bg="#4a57ff"
        ).pack(pady=5)

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
                font=("Arial", 12),
                bg="#dfe3ff"
            )
            lbl.pack()
            self.status_labels.append(lbl)

        self.root.after(300, self.update_loop)

    def run(self):
        self.root.mainloop()


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    print("=== Camcookie Plugin v3 (Wayland-safe) ===")

    manager = PluginManager()

    # Register plugins
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