#!/usr/bin/env python3
import time
import threading
import RPi.GPIO as GPIO
import pyautogui

# ============================================================
#  CAMCOOKIE PLUGIN APP — UNIFIED HARDWARE EXTENSION SYSTEM
# ============================================================

# ------------------------------------------------------------
# Base Plugin Class
# ------------------------------------------------------------
class BasePlugin:
    def __init__(self, manager):
        self.manager = manager

    def start(self):
        pass

    def stop(self):
        pass

    def update(self):
        pass


# ------------------------------------------------------------
# CookieJoystick Plugin
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

    # GPIO callbacks
    def _up(self, ch):
        self.up = (GPIO.input(self.PIN_UP) == GPIO.LOW)

    def _down(self, ch):
        self.down = (GPIO.input(self.PIN_DOWN) == GPIO.LOW)

    def _left(self, ch):
        self.left = (GPIO.input(self.PIN_LEFT) == GPIO.LOW)

    def _right(self, ch):
        self.right = (GPIO.input(self.PIN_RIGHT) == GPIO.LOW)

    def _click(self, ch):
        pyautogui.click()

    # Movement loop
    def _loop(self):
        while self.running:
            dx = 0
            dy = 0

            if self.up and not self.down:
                dy -= self.CURSOR_STEP
            elif self.down and not self.up:
                dy += self.CURSOR_STEP

            if self.left and not self.right:
                dx -= self.CURSOR_STEP
            elif self.right and not self.left:
                dx += self.CURSOR_STEP

            if dx != 0 or dy != 0:
                try:
                    pyautogui.moveRel(dx, dy, duration=0)
                except Exception as e:
                    print("[Joystick] Cursor error:", e)

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


# ------------------------------------------------------------
# Main Camcookie Plugin App
# ------------------------------------------------------------
def main():
    print("=== Camcookie Plugin App ===")

    manager = PluginManager()

    # Register all plugins here
    manager.register(CookieJoystick)

    # Start everything
    manager.start_all()

    print("Camcookie Plugins running. Press Ctrl+C to exit.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down Camcookie Plugins...")
    finally:
        manager.stop_all()
        GPIO.cleanup()
        print("Goodbye!")


if __name__ == "__main__":
    main()