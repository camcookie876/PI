#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox
import subprocess
import json
import urllib.request
import os
import sys

# ---------- Config ----------

# JSON catalog URL
APPSTORE_URL = "https://camcookie876.github.io/app/appstore/appstore.json"

HOME = os.path.expanduser("~")
LOCAL_DB = os.path.join(HOME, ".camcookie_installed.json")
ICON_CACHE_DIR = os.path.join(HOME, ".camcookie", "icons")

# Ensure icon cache dir exists
os.makedirs(ICON_CACHE_DIR, exist_ok=True)

# Keep references to PhotoImage objects to avoid garbage collection
icon_cache_images = {}

# ---------- Installed versions database ----------

def load_local_versions():
    if not os.path.exists(LOCAL_DB):
        return {}
    try:
        with open(LOCAL_DB, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_local_versions(db):
    with open(LOCAL_DB, "w") as f:
        json.dump(db, f)

# ---------- Expand $HOME in commands and paths ----------

def expand_home(text):
    if isinstance(text, str):
        return text.replace("$HOME", HOME)
    return text

def expand_list(cmds):
    return [expand_home(c) for c in cmds]

# ---------- Remote catalog ----------

def load_catalog():
    with urllib.request.urlopen(APPSTORE_URL) as response:
        data = response.read().decode()
        return json.loads(data)["apps"]

# ---------- Icon handling ----------

def get_icon_path_for_app(app):
    """
    Use app['icon'] URL and cache it under ~/.camcookie/icons/<id>.png
    """
    icon_url = app.get("icon")
    app_id = app.get("id", "unknown")
    if not icon_url:
        return None

    ext = os.path.splitext(icon_url)[1]
    if ext.lower() not in [".png", ".gif", ".ppm", ".pgm"]:
        ext = ".png"
    local_icon_path = os.path.join(ICON_CACHE_DIR, f"{app_id}{ext}")
    return icon_url, local_icon_path

def download_icon_if_needed(app):
    result = get_icon_path_for_app(app)
    if not result:
        return None
    icon_url, local_icon_path = result

    if not os.path.exists(local_icon_path):
        try:
            urllib.request.urlretrieve(icon_url, local_icon_path)
        except Exception:
            return None
    return local_icon_path

def load_icon_image(app, size=(64, 64)):
    """
    Load a PhotoImage from the cached icon file.
    Tkinter PhotoImage only supports GIF/PNG/PPM/PGM.
    No resizing here (Tkinter can't resize easily without PIL),
    so make your icons ~64x64 on the server.
    """
    app_id = app.get("id", "unknown")

    if app_id in icon_cache_images:
        return icon_cache_images[app_id]

    local_icon_path = download_icon_if_needed(app)
    if not local_icon_path or not os.path.exists(local_icon_path):
        return None

    try:
        img = tk.PhotoImage(file=local_icon_path)
        icon_cache_images[app_id] = img
        return img
    except Exception:
        return None

# ---------- File creation from JSON ----------

def create_files(app):
    files = app.get("files", [])
    for file in files:
        path = expand_home(file["path"])
        content = file["content"]
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            os.chmod(path, 0o755)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to write file {path}:\n{e}")

# ---------- Install logic ----------

def install_app(app):
    create_files(app)

    try:
        cmds = expand_list(app.get("install", []))
        for cmd in cmds:
            subprocess.run(cmd, shell=True, check=True)

        local_versions[app["id"]] = app["version"]
        save_local_versions(local_versions)

        messagebox.showinfo(
            "Installed",
            f"{app['name']} v{app['version']} installed successfully."
        )
    except Exception as e:
        messagebox.showerror("Error", f"Install failed:\n{e}")

# ---------- Launch logic ----------

def launch_app(app):
    app_id = app["id"]
    remote_version = app["version"]
    local_version = local_versions.get(app_id)

    # Safety: do not allow launch if not installed or outdated
    if local_version != remote_version:
        messagebox.showwarning(
            "Not Installed or Outdated",
            f"{app['name']} is not installed or not up-to-date.\n"
            "Please install or update it first."
        )
        return

    try:
        launch_cmd = expand_home(app["launch"])
        subprocess.Popen(launch_cmd, shell=True)
    except Exception as e:
        messagebox.showerror("Error", f"Launch failed:\n{e}")

# ---------- Install button handler (version logic) ----------

def handle_install(app):
    app_id = app["id"]
    remote_version = app["version"]
    local_version = local_versions.get(app_id)

    if local_version is None:
        install_app(app)
        refresh_app_list()
        return

    if local_version == remote_version:
        messagebox.showinfo(
            "Installed",
            f"{app['name']} v{remote_version} is already installed."
        )
        return

    choice = messagebox.askyesno(
        "Update Available",
        f"{app['name']} has an update available.\n\n"
        f"Installed: {local_version}\n"
        f"Available: {remote_version}\n\n"
        "Install the new version?"
    )

    if choice:
        install_app(app)
        refresh_app_list()
    else:
        messagebox.showinfo("Keeping Version", "Keeping installed version.")

# ---------- Self-update for appstore ----------

def check_self_update(apps):
    appstore_entry = None
    for app in apps:
        if app.get("id") == "appstore":
            appstore_entry = app
            break

    if appstore_entry is None:
        return

    remote_version = appstore_entry["version"]
    local_version = local_versions.get("appstore")

    if local_version != remote_version:
        messagebox.showinfo(
            "Appstore Update Required",
            f"A new version of Camcookie Appstore is available.\n\n"
            f"Installed: {local_version}\n"
            f"Available: {remote_version}\n\n"
            "Updating now..."
        )

        create_files(appstore_entry)

        try:
            cmds = expand_list(appstore_entry.get("install", []))
            for cmd in cmds:
                subprocess.run(cmd, shell=True, check=True)

            local_versions["appstore"] = remote_version
            save_local_versions(local_versions)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update Appstore:\n{e}")
            sys.exit(1)

        os.execv(sys.executable, ["python3"] + sys.argv)

# ---------- UI building ----------

def build_app_card(parent, app):
    app_id = app["id"]
    name = app.get("name", app_id)
    creator = app.get("creator", "Unknown creator")
    description = app.get("description", "")
    remote_version = app.get("version", "0.0")
    local_version = local_versions.get(app_id)

    box = tk.Frame(parent, bd=2, relief="groove", padx=10, pady=10)
    box.pack(fill="x", pady=5, padx=5)

    top_frame = tk.Frame(box)
    top_frame.pack(fill="x")

    icon_img = load_icon_image(app)
    if icon_img is not None:
        icon_label = tk.Label(top_frame, image=icon_img)
        icon_label.image = icon_img
        icon_label.pack(side="left", padx=(0, 10))
    else:
        placeholder = tk.Label(
            top_frame,
            text="🟦",
            font=("Arial", 24),
            width=2
        )
        placeholder.pack(side="left", padx=(0, 10))

    text_frame = tk.Frame(top_frame)
    text_frame.pack(side="left", fill="x", expand=True)

    name_label = tk.Label(text_frame, text=name, font=("Arial", 14, "bold"))
    name_label.pack(anchor="w")

    creator_label = tk.Label(text_frame, text=f"by {creator}", font=("Arial", 10, "italic"))
    creator_label.pack(anchor="w")

    desc_label = tk.Label(
        box,
        text=description,
        font=("Arial", 10),
        wraplength=540,
        justify="left"
    )
    desc_label.pack(anchor="w", pady=(5, 5))

    version_text = ""
    if local_version:
        if local_version == remote_version:
            version_text = f"Installed: {local_version} (up to date)"
        else:
            version_text = f"Installed: {local_version} | Available: {remote_version}"
    else:
        version_text = f"Available: {remote_version}"

    version_label = tk.Label(box, text=version_text, font=("Arial", 9))
    version_label.pack(anchor="w")

    btn_frame = tk.Frame(box)
    btn_frame.pack(anchor="e", pady=(5, 0))

    download_or_update_text = None
    show_open = False

    if local_version is None:
        download_or_update_text = "Download"
    elif local_version != remote_version:
        download_or_update_text = "Update"
        show_open = False
    else:
        show_open = True

    if download_or_update_text is not None:
        install_btn = tk.Button(
            btn_frame,
            text=download_or_update_text,
            command=lambda a=app: handle_install(a)
        )
        install_btn.pack(side="left", padx=5)

    if show_open:
        open_btn = tk.Button(
            btn_frame,
            text="Open",
            command=lambda a=app: launch_app(a)
        )
        open_btn.pack(side="left", padx=5)

# ---------- Search + refresh logic ----------

def refresh_app_list(*args):
    search_term = search_var.get().strip().lower()
    for widget in scroll_frame.winfo_children():
        widget.destroy()

    for app in all_apps:
        text_blob = " ".join([
            str(app.get("name", "")),
            str(app.get("creator", "")),
            str(app.get("description", "")),
            str(app.get("id", ""))
        ]).lower()

        if search_term in text_blob:
            build_app_card(scroll_frame, app)

# ---------- Main ----------

def main():
    global local_versions, all_apps, root, search_var, scroll_frame

    if not os.path.exists(LOCAL_DB):
        with open(LOCAL_DB, "w") as f:
            f.write("{}")

    local_versions = load_local_versions()

    try:
        apps = load_catalog()
    except Exception as e:
        tk.Tk().withdraw()
        messagebox.showerror("Error", f"Failed to load app catalog:\n{e}")
        return

    all_apps = apps

    check_self_update(apps)

    root = tk.Tk()
    root.title("Camcookie Appstore")
    root.geometry("700x600")

    title = tk.Label(root, text="Camcookie Appstore", font=("Arial", 20))
    title.pack(pady=(10, 5))

    search_frame = tk.Frame(root)
    search_frame.pack(fill="x", padx=10, pady=(0, 10))

    search_label = tk.Label(search_frame, text="Search:", font=("Arial", 10))
    search_label.pack(side="left")

    search_var = tk.StringVar()
    search_entry = tk.Entry(search_frame, textvariable=search_var, width=40)
    search_entry.pack(side="left", padx=5, fill="x", expand=True)

    search_var.trace_add("write", refresh_app_list)

    canvas = tk.Canvas(root)
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas)

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(0, 10))
    scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=(0, 10))

    refresh_app_list()

    root.mainloop()

if __name__ == "__main__":
    main()