# Camcookie Plugin - Camcookie app
By: Camcookie INC
## Description:
Shared hardware engine with virtual mouse, Arduino support, LED and temperature plugins, Chromium-based HTML UI, and app connection permissions.

## Jump to:
- [Camcookie Plugin Engine — User Guide](#camcookie-plugin-engine)
- [Camcookie Plugin Engine — Developer Guide](#camcookie-plugin-engine--developer-guide)

# Camcookie Plugin Engine  
### **Version 1.5 — User Guide**

Welcome to the **Camcookie Plugin Engine**!  
This tool powers the hardware features used by Camcookie OS apps, such as:

- Arduino‑powered mouse control  
- LED control  
- Temperature sensors  
- Other hardware plugins  

You don’t need to write code or build apps to use it — this guide explains everything you need to know as a regular user.

---

# 🎯 What the Plugin Engine Does

The Plugin Engine runs in the background and lets apps share hardware safely.  
It provides:

- A **virtual mouse** (safe for Wayland)  
- Arduino input support  
- LED and temperature plugins  
- A permissions system so apps must ask before using hardware  
- A simple interface to turn plugins on or off  

Think of it like the “hardware brain” for Camcookie OS.

---

# 🚀 How to Open the Plugin Engine

After installing it from the Camcookie Appstore, you’ll see:

**Camcookie Plugin**  
in your Raspberry Pi menu.

Click it to open.

This will:

1. Start the background engine  
2. Open the Plugin UI in a Chromium window  

You don’t need to keep the window open — the engine keeps running until no apps are connected.

---

# 🏠 Home Section

The top of the page shows:

### ✔ How many plugins are running  
Example:  
“You currently have 2 plugins running”

### ✔ Arduino input  
If you have an Arduino connected, you’ll see the latest command it sent.

If nothing is connected, it will say:  
“None”

---

# 🔌 Plugins Section

This section lists all hardware plugins included with the engine.

Each plugin shows:

- **Name**  
- **Status**  
- **On/Off toggle**

### Example plugins:

- **Arduino Mouse**  
  Reads Arduino commands and moves the mouse

- **LED Controller**  
  Controls LEDs (GPIO-ready)

- **Temperature Sensor**  
  Reads temperature (future-ready)

### Turning plugins on/off

Just flip the switch next to each plugin.

The status updates automatically.

---

# 🔗 Connect Apps Section

This section shows apps on your system that can use the Plugin Engine.

Each app shows:

- Installed or not  
- Connected or not  
- Buttons to Connect / Disconnect  
- A button to request engine shutdown  

### Connecting an app

Press **Connect** next to the app.

This gives the app permission to use hardware features.

### Disconnecting an app

Press **Disconnect**.

The app will immediately lose access to the hardware API.

### Requesting shutdown

If no apps are connected, the engine will shut down automatically.

If another app is still connected, shutdown will be delayed.

---

# 🌐 API Information (For Reference Only)

At the bottom of the page, you’ll see:

```
http://127.0.0.1:8765
```

This is the local address apps use to talk to the engine.

You don’t need to use this unless you’re building an app.

---

# 🧠 When Does the Engine Stop Running?

The engine automatically shuts down when:

- No apps are connected  
- No apps are using hardware  
- A short delay has passed  

You don’t need to close it manually.

---

# 🛠 Troubleshooting

### The UI shows nothing  
Make sure the Plugin Engine is running.  
Open it from the Pi menu again.

### Plugins won’t turn on  
Some plugins require hardware (like an Arduino).  
Check your connections.

### An app can’t use hardware  
Make sure it is **Connected** in the Connect Apps section.


---


# **Camcookie Plugin Engine — Developer Guide**  
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