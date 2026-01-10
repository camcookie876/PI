# 🍪 **Camcookie Plugin Engine — Developer Guide**  
### Version 1.5 — Chromium App Mode Edition

Welcome to the official **Camcookie Plugin Engine Developer Guide**.  
This document explains how to build apps that connect to the Camcookie Plugin Engine and use shared hardware features such as:

- Virtual mouse control  
- Arduino input  
- LED control  
- Temperature sensors  
- Future plugins  

This guide is for developers building apps for **Camcookie OS**.

---

# 🎯 **What the Plugin Engine Is**

The Plugin Engine is a **background service** that runs on the Raspberry Pi and exposes a local HTTP API at:

```
http://127.0.0.1:8765
```

Apps can connect to this engine to use hardware features without needing to write low‑level code.

The engine provides:

- A **virtual mouse** (Wayland‑safe)
- Arduino serial input
- LED control
- Temperature sensor support
- Plugin enable/disable system
- App permission system (“Connected Apps”)
- Auto‑shutdown when unused

---

# 🧩 **How Apps Connect**

Apps must:

1. Be installed through the Camcookie Appstore  
2. Have `"plugin": "YES"` in their Appstore JSON  
3. Be marked as **Connected** in the Plugin UI  
4. Include `?app_id=yourappid` in every protected API request  

Example:

```
http://127.0.0.1:8765/mouse/move?dx=10&dy=-5&app_id=camcookieactions
```

---

# 🔐 **Permissions System**

Connected apps are stored in:

```
$HOME/.camcookie_connected.json
```

Example:

```json
{
  "camcookieactions": true
}
```

Apps can connect/disconnect themselves:

```
/connect?app_id=yourappid
/disconnect?app_id=yourappid
```

Apps can request shutdown:

```
/shutdown?app_id=yourappid
```

The engine shuts down only when **no apps are connected**.

---

# 🌐 **HTTP API Reference**

All protected endpoints require:

```
?app_id=yourappid
```

---

## 📌 **Status**

```
GET /status
```

Returns:

- Plugin list  
- Plugin status  
- Arduino data  
- Installed connectable apps  
- Connected apps  

---

## 🖱 **Virtual Mouse**

Move the mouse:

```
GET /mouse/move?dx=10&dy=-5&app_id=yourappid
```

Click:

```
GET /mouse/click?app_id=yourappid
```

Limits:

- dx/dy are clamped to ±50  
- Safe for Wayland  

---

## 💡 **LED Control**

```
GET /led/set?on=1&app_id=yourappid
```

`on=1` → LED ON  
`on=0` → LED OFF  

---

## 🌡 **Temperature Sensor**

```
GET /temp/read?app_id=yourappid
```

Returns:

```json
{ "ok": true, "temp": 22.5 }
```

---

# 🧱 **Plugin Architecture**

Plugins inherit from:

```python
class BasePlugin:
    def __init__(self, manager, plugin_id, name):
        self.manager = manager
        self.id = plugin_id
        self.name = name
        self.enabled = False
        self.status = "Idle"
```

To create a new plugin:

```python
class MyPlugin(BasePlugin):
    def __init__(self, manager):
        super().__init__(manager, "myplugin", "My Plugin")

    def start(self):
        self.enabled = True
        self.status = "Running"

    def stop(self):
        self.enabled = False
        self.status = "Stopped"
```

Register it in `app.py`:

```python
plugin_manager.register(MyPlugin(plugin_manager))
```

It will automatically appear in the UI.

---

# 🖥 **UI Overview (Single‑Page Layout)**

The UI shows:

### **Home**
- Running plugin count  
- Arduino input  

### **Plugins**
- All plugins  
- Enable/disable toggles  
- Live status  

### **Connect**
- Installed apps that support plugins  
- Connect/disconnect buttons  
- Shutdown request  
- API instructions  

The UI auto‑refreshes every 2 seconds.

---

# 🚀 **Building a Plugin‑Enabled App**

Your Appstore JSON must include:

```json
"plugin": "YES"
```

Example:

```json
{
  "id": "camcookieactions",
  "name": "Camcookie Actions",
  "plugin": "YES",
  "version": "1.0"
}
```

Then your app can call:

```
http://127.0.0.1:8765/mouse/move?dx=10&dy=0&app_id=camcookieactions
```

---

# 🧪 **Testing Your App**

1. Install your app through the Appstore  
2. Open the Camcookie Plugin UI  
3. Go to **Connect Apps**  
4. Press **Connect**  
5. Test your API calls  

If your app disconnects, the engine will auto‑shutdown after 5 seconds.

---

# 🛠 **Troubleshooting**

### ❌ My app gets “Access denied”
- You forgot `?app_id=yourappid`
- Your app is not marked as Connected
- Your app is not installed through the Appstore
- Your app JSON is missing `"plugin": "YES"`

### ❌ Mouse doesn’t move
- Virtual mouse plugin is disabled
- Wayland blocked uinput (rare)
- Arduino plugin is interfering

### ❌ UI shows nothing
- Backend not running  
- Wrong file path  
- Chromium App Mode blocked external JS (fixed in V1.5 by inline JS)