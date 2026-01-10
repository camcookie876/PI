# 🍪 Camcookie Plugin Engine — Plugin Developer Guide  
### **Version 1.4 BETA**

The **Camcookie Plugin Engine** is the shared hardware service for Camcookie OS.  
It provides:

- A **Wayland‑safe virtual mouse**
- Arduino‑powered input support
- LED control (GPIO‑ready)
- Temperature sensor support (future‑ready)
- A local **HTTP API** for apps
- A permissions system (“Connected Apps”)
- A PyWebView HTML UI for configuration

This document explains how **apps** and **plugins** integrate with the engine.

---

# 📦 What is a Camcookie Plugin?

A **Camcookie Plugin** is a hardware feature module that runs inside the Camcookie Plugin Engine.  
Plugins are written in Python and registered inside `app.py`.

Examples included in V1.4 BETA:

| Plugin ID        | Description |
|------------------|-------------|
| `arduino_mouse`  | Reads Arduino serial input and controls the virtual mouse |
| `led`            | Controls LEDs (GPIO-ready) |
| `temp`           | Reads temperature sensors (future-ready) |

Plugins can be enabled/disabled from the UI or programmatically.

---

# 🧠 How Apps Use Plugins

Apps do **not** load plugins directly.

Instead, apps connect to the **Plugin Engine** using the local HTTP API:

```
http://127.0.0.1:8765
```

Apps must:

1. Be installed through the Camcookie Appstore  
2. Have `"plugin": "YES"` in the Appstore JSON  
3. Be marked as “Connected” in the Plugin Engine UI  
4. Include `?app_id=yourappid` in API requests  

Once connected, apps can use:

- Virtual mouse  
- LED control  
- Temperature reading  
- Arduino data (if needed)

---

# 🔐 Permissions System (Connected Apps)

The Plugin Engine uses:

```
$HOME/.camcookie_connected.json
```

Example:

```json
{
    "camcookieactions": true,
    "mycoolapp": true
}
```

Only apps listed here may access protected API endpoints.

Apps can connect/disconnect using:

```
/connect?app_id=yourappid
/disconnect?app_id=yourappid
```

Apps can request the engine to shut down:

```
/shutdown?app_id=yourappid
```

The engine shuts down **only if no other apps are connected**, with a 5‑second delay.

---

# 🌐 HTTP API Reference

All protected endpoints require:

```
?app_id=yourappid
```

### ✔ Status

```
GET /status
```

Returns:

- Plugin states  
- Arduino data  
- Connected apps  

---

## 🖱 Virtual Mouse API

### Move mouse

```
GET /mouse/move?dx=10&dy=-5&app_id=yourappid
```

### Click

```
GET /mouse/click?app_id=yourappid
```

---

## 💡 LED API

### Set LED state

```
GET /led/set?on=1&app_id=yourappid
```

`on=1` → LED ON  
`on=0` → LED OFF  

---

## 🌡 Temperature API

### Read temperature

```
GET /temp/read?app_id=yourappid
```

Returns:

```json
{
  "ok": true,
  "temp": 22.5
}
```

---

# 🧩 Creating a New Plugin (Python)

Plugins inherit from `BasePlugin`:

```python
class MyPlugin(BasePlugin):
    def __init__(self, manager, ui_api):
        super().__init__(manager, "myplugin", "My Plugin")
        self.ui_api = ui_api

    def start(self):
        self.enabled = True
        self.status = "Running"
        self.ui_api.push_state()

    def stop(self):
        self.enabled = False
        self.status = "Stopped"
        self.ui_api.push_state()
```

Register it in `main()`:

```python
myplugin = MyPlugin(plugin_manager, ui_api)
plugin_manager.register(myplugin)
```

It will automatically appear in the UI.

---

# 🖥 UI Overview

The Plugin Engine UI (PyWebView + HTML/CSS) includes:

### **Home**
- Shows running plugins  
- Shows Arduino input  

### **Plugins**
- Enable/disable plugins  
- Live status updates  

### **Connect**
- Shows installed apps that support plugins  
- Connect/disconnect apps  
- Shows API usage instructions  

---

# 🧪 Headless Mode (Background Service)

Apps can start the Plugin Engine invisibly:

```
python3 $HOME/camcookieplugin/app.py --headless
```

In headless mode:

- No UI window  
- Only the HTTP API runs  
- Plugins run normally  

The engine auto‑shuts down when no apps are connected.

---

# 🛠 Requirements

- Python 3  
- pywebview  
- python3-serial  
- python3-uinput  
- requests  
- Raspberry Pi OS (Wayland or X11)