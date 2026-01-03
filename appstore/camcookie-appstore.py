#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, filedialog
import subprocess
import json
import urllib.request
import os
import sys
import webbrowser
import re

# ---------- Config ----------

APPSTORE_URL = "https://camcookie876.github.io/app/appstore/appstore.json"

HOME = os.path.expanduser("~")
LOCAL_DB = os.path.join(HOME, ".camcookie_installed.json")
ICON_CACHE_DIR = os.path.join(HOME, ".camcookie", "icons")
SETTINGS_FILE = os.path.join(HOME, ".camcookie", "appstore-settings.json")

os.makedirs(ICON_CACHE_DIR, exist_ok=True)
os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)

icon_cache_images = {}

# ---------- Settings ----------

DEFAULT_SETTINGS = {
    "theme": "soft_blue",       # soft_blue, light, dark
    "tile_bg_color": "#1f3b5b", # default soft blue tile
    "background_mode": "color", # color or image
    "background_color": "#0b1220",
    "background_image": ""      # path to image (not used heavily in Tk)
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
        merged = DEFAULT_SETTINGS.copy()
        merged.update(data)
        return merged
    except Exception:
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


settings = load_settings()

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

# ---------- Helpers ----------

def expand_home(text):
    if isinstance(text, str):
        return text.replace("$HOME", HOME)
    return text

def expand_list(cmds):
    return [expand_home(c) for c in cmds]

def load_catalog():
    with urllib.request.urlopen(APPSTORE_URL) as response:
        data = response.read().decode()
        return json.loads(data)["apps"]

# ---------- Icon handling ----------

def get_icon_path_for_app(app):
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

def load_icon_image(app):
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

# ---------- Delete logic ----------

def delete_app(app):
    app_id = app["id"]
    if app_id not in local_versions:
        messagebox.showinfo("Not installed", f"{app['name']} is not installed.")
        return
    confirm = messagebox.askyesno(
        "Delete App",
        f"Remove {app['name']} from installed apps?\n\n"
        "This will forget its installed version.\n"
        "Files created by the app may remain on disk."
    )
    if not confirm:
        return
    try:
        del local_versions[app_id]
        save_local_versions(local_versions)
        messagebox.showinfo("Deleted", f"{app['name']} was removed from installed apps.")
        refresh_all_views()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete app:\n{e}")

# ---------- Launch logic ----------

def launch_app(app):
    app_id = app["id"]
    remote_version = app["version"]
    local_version = local_versions.get(app_id)

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

# ---------- Install button handler ----------

def handle_install(app):
    app_id = app["id"]
    remote_version = app["version"]
    local_version = local_versions.get(app_id)

    if local_version is None:
        install_app(app)
        refresh_all_views()
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
        refresh_all_views()
    else:
        messagebox.showinfo("Keeping Version", "Keeping installed version.")

# ---------- Self-update for appstore ----------

def check_self_update(apps):
    appstore_entry = None
    for app in apps:
        if app.get("id") == "camcookieappstore":
            appstore_entry = app
            break
    if appstore_entry is None:
        return

    remote_version = appstore_entry["version"]
    local_version = local_versions.get("camcookieappstore")

    if local_version != remote_version:
        messagebox.showinfo(
            "Appstore Update",
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
            local_versions["camcookieappstore"] = remote_version
            save_local_versions(local_versions)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update Appstore:\n{e}")
            sys.exit(1)
        os.execv(sys.executable, ["python3"] + sys.argv)

# ---------- URL link handling in descriptions ----------

URL_REGEX = re.compile(r"(https?://[^\s]+)")

def make_linked_label(parent, text, fg="white", bg=None, wrap=540):
    # Very simple: detect URLs and create a Text-like clickable label
    frame = tk.Frame(parent, bg=bg)
    frame.pack(fill="x", pady=(4, 4))
    text_widget = tk.Text(
        frame, height=3, wrap="word", bd=0,
        bg=bg or parent.cget("bg"), fg=fg
    )
    text_widget.pack(fill="both", expand=True)

    text_widget.insert("1.0", text)

    for match in URL_REGEX.finditer(text):
        start, end = match.span()
        url = match.group(0)
        start_index = f"1.0+{start}c"
        end_index = f"1.0+{end}c"
        text_widget.tag_add(url, start_index, end_index)
        text_widget.tag_config(url, foreground="#61afef", underline=1)
        def callback(event, link=url):
            webbrowser.open(link)
        text_widget.tag_bind(url, "<Button-1>", callback)

    text_widget.configure(state="disabled")
    return frame

# ---------- UI: Themes ----------

def apply_theme(root):
    theme = settings.get("theme", "soft_blue")
    tile_bg = settings.get("tile_bg_color", "#1f3b5b")
    bg_color = settings.get("background_color", "#0b1220")

    if theme == "light":
        root.configure(bg="#f0f0f0")
    elif theme == "dark":
        root.configure(bg="#050816")
    else:  # soft_blue
        root.configure(bg=bg_color)

    style = ttk.Style()
    style.theme_use("clam")

    if theme == "light":
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", background="#f0f0f0", foreground="#000000")
        style.configure("TNotebook", background="#e0e0e0")
        style.configure("TNotebook.Tab", background="#d0d0d0", foreground="#000000")
        style.map("TNotebook.Tab", background=[("selected", "#ffffff")])
        style.configure("TButton", background="#d0d0d0", foreground="#000000")
    elif theme == "dark":
        style.configure("TFrame", background="#050816")
        style.configure("TLabel", background="#050816", foreground="#ffffff")
        style.configure("TNotebook", background="#0b1220")
        style.configure("TNotebook.Tab", background="#111827", foreground="#ffffff")
        style.map("TNotebook.Tab", background=[("selected", "#1f2937")])
        style.configure("TButton", background="#1f2937", foreground="#ffffff")
    else:  # soft_blue
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, foreground="#e5e7eb")
        style.configure("TNotebook", background="#111827")
        style.configure("TNotebook.Tab", background="#1f2937", foreground="#e5e7eb")
        style.map("TNotebook.Tab", background=[("selected", "#2563eb")])
        style.configure("TButton", background="#2563eb", foreground="#e5e7eb")

    # Update tile background everywhere via global
    global TILE_BG
    TILE_BG = tile_bg

# ---------- UI: App cards ----------

def build_app_card(parent, app):
    app_id = app["id"]
    name = app.get("name", app_id)
    creator = app.get("creator", "Unknown creator")
    description = app.get("description", "")
    remote_version = app.get("version", "0.0")
    local_version = local_versions.get(app_id)

    card = tk.Frame(parent, bd=0, bg=TILE_BG, highlightthickness=0)
    card.pack(fill="x", pady=8, padx=10)

    # Fake rounded corners via padding + bg color
    inner = tk.Frame(card, bg=TILE_BG)
    inner.pack(fill="both", expand=True, padx=6, pady=6)

    top_frame = tk.Frame(inner, bg=TILE_BG)
    top_frame.pack(fill="x")

    icon_img = load_icon_image(app)
    if icon_img is not None:
        icon_label = tk.Label(top_frame, image=icon_img, bg=TILE_BG)
        icon_label.image = icon_img
        icon_label.pack(side="left", padx=(0, 10))
    else:
        placeholder = tk.Label(
            top_frame,
            text="🟦",
            font=("Arial", 20),
            width=2,
            bg=TILE_BG,
            fg="white"
        )
        placeholder.pack(side="left", padx=(0, 10))

    text_frame = tk.Frame(top_frame, bg=TILE_BG)
    text_frame.pack(side="left", fill="x", expand=True)

    name_label = tk.Label(text_frame, text=name, font=("Arial", 14, "bold"), bg=TILE_BG, fg="white")
    name_label.pack(anchor="w")

    creator_label = tk.Label(text_frame, text=f"by {creator}", font=("Arial", 10, "italic"), bg=TILE_BG, fg="#d1d5db")
    creator_label.pack(anchor="w")

    make_linked_label(inner, description, fg="#e5e7eb", bg=TILE_BG)

    version_text = ""
    if local_version:
        if local_version == remote_version:
            version_text = f"Installed: {local_version} (up to date)"
        else:
            version_text = f"Installed: {local_version} | Available: {remote_version}"
    else:
        version_text = f"Available: {remote_version}"

    version_label = tk.Label(inner, text=version_text, font=("Arial", 9), bg=TILE_BG, fg="#d1d5db")
    version_label.pack(anchor="w")

    btn_frame = tk.Frame(inner, bg=TILE_BG)
    btn_frame.pack(anchor="e", pady=(6, 0))

    download_or_update_text = None
    show_open = False
    show_delete = False

    if local_version is None:
        download_or_update_text = "Download"
    elif local_version != remote_version:
        download_or_update_text = "Update"
        show_open = False
        show_delete = True
    else:
        show_open = True
        show_delete = True

    if download_or_update_text is not None:
        install_btn = ttk.Button(
            btn_frame,
            text=download_or_update_text,
            command=lambda a=app: handle_install(a)
        )
        install_btn.pack(side="left", padx=4)

    if show_open:
        open_btn = ttk.Button(
            btn_frame,
            text="Open",
            command=lambda a=app: launch_app(a)
        )
        open_btn.pack(side="left", padx=4)

    if show_delete:
        delete_btn = ttk.Button(
            btn_frame,
            text="Delete",
            command=lambda a=app: delete_app(a)
        )
        delete_btn.pack(side="left", padx=4)

# ---------- Views (tabs) ----------

def clear_frame(frame):
    for w in frame.winfo_children():
        w.destroy()

def populate_all_apps():
    clear_frame(all_apps_frame_inner)
    search_term = all_search_var.get().strip().lower()
    for app in all_apps:
        if search_term:
            text_blob = " ".join([
                str(app.get("name", "")),
                str(app.get("creator", "")),
                str(app.get("description", "")),
                str(app.get("id", ""))
            ]).lower()
            if search_term not in text_blob:
                continue
        build_app_card(all_apps_frame_inner, app)

def populate_installed():
    clear_frame(installed_frame_inner)
    for app in all_apps:
        app_id = app["id"]
        if app_id in local_versions:
            build_app_card(installed_frame_inner, app)

def populate_updates():
    clear_frame(updates_frame_inner)
    for app in all_apps:
        app_id = app["id"]
        remote_version = app.get("version")
        local_version = local_versions.get(app_id)
        if local_version and remote_version and local_version != remote_version:
            build_app_card(updates_frame_inner, app)

def refresh_all_views(*args):
    populate_all_apps()
    populate_installed()
    populate_updates()

# ---------- Settings UI ----------

def on_theme_change(new_theme):
    settings["theme"] = new_theme
    save_settings(settings)
    apply_theme(root)
    refresh_all_views()

def choose_tile_color():
    color = colorchooser.askcolor(initialcolor=settings.get("tile_bg_color"))[1]
    if color:
        settings["tile_bg_color"] = color
        save_settings(settings)
        apply_theme(root)
        refresh_all_views()

def choose_bg_color():
    color = colorchooser.askcolor(initialcolor=settings.get("background_color"))[1]
    if color:
        settings["background_color"] = color
        settings["background_mode"] = "color"
        save_settings(settings)
        apply_theme(root)
        refresh_all_views()

def build_settings_page():
    clear_frame(settings_frame)

    title = ttk.Label(settings_frame, text="Settings", font=("Arial", 16, "bold"))
    title.pack(anchor="w", pady=(10, 10), padx=10)

    theme_label = ttk.Label(settings_frame, text="Theme:")
    theme_label.pack(anchor="w", padx=10)

    theme_frame = ttk.Frame(settings_frame)
    theme_frame.pack(anchor="w", padx=10, pady=(4, 10))

    current_theme = settings.get("theme", "soft_blue")
    theme_var = tk.StringVar(value=current_theme)

    def change_theme():
        on_theme_change(theme_var.get())

    ttk.Radiobutton(theme_frame, text="Soft Blue", value="soft_blue", variable=theme_var, command=change_theme).pack(side="left", padx=4)
    ttk.Radiobutton(theme_frame, text="Light", value="light", variable=theme_var, command=change_theme).pack(side="left", padx=4)
    ttk.Radiobutton(theme_frame, text="Dark", value="dark", variable=theme_var, command=change_theme).pack(side="left", padx=4)

    tile_label = ttk.Label(settings_frame, text="App tile background color:")
    tile_label.pack(anchor="w", padx=10, pady=(10, 0))

    tile_btn = ttk.Button(settings_frame, text="Choose tile color", command=choose_tile_color)
    tile_btn.pack(anchor="w", padx=10, pady=(4, 10))

    bg_label = ttk.Label(settings_frame, text="Background color:")
    bg_label.pack(anchor="w", padx=10, pady=(10, 0))

    bg_btn = ttk.Button(settings_frame, text="Choose background color", command=choose_bg_color)
    bg_btn.pack(anchor="w", padx=10, pady=(4, 10))

    info = ttk.Label(
        settings_frame,
        text="Settings are saved automatically in ~/.camcookie/appstore-settings.json",
        font=("Arial", 9)
    )
    info.pack(anchor="w", padx=10, pady=(20, 0))

# ---------- Main ----------

def main():
    global local_versions, all_apps
    global root, all_search_var, all_apps_frame_inner
    global installed_frame_inner, updates_frame_inner, settings_frame
    global TILE_BG

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

    # Self update
    check_self_update(apps)

    root = tk.Tk()
    root.title("Camcookie Appstore V11")
    root.geometry("820x640")

    apply_theme(root)

    # Title bar
    title_frame = ttk.Frame(root)
    title_frame.pack(fill="x", pady=(10, 5), padx=10)

    title_label = ttk.Label(title_frame, text="Camcookie Appstore", font=("Arial", 20, "bold"))
    title_label.pack(side="left")

    # Notebook (tabs)
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # All Apps tab
    all_apps_tab = ttk.Frame(notebook)
    notebook.add(all_apps_tab, text="All Apps")

    all_search_frame = ttk.Frame(all_apps_tab)
    all_search_frame.pack(fill="x", pady=(6, 4), padx=6)

    ttk.Label(all_search_frame, text="Search:").pack(side="left")
    all_search_var = tk.StringVar()
    all_search_entry = ttk.Entry(all_search_frame, textvariable=all_search_var, width=40)
    all_search_entry.pack(side="left", padx=6, fill="x", expand=True)
    all_search_var.trace_add("write", lambda *args: populate_all_apps())

    all_canvas = tk.Canvas(all_apps_tab, highlightthickness=0, bd=0)
    all_scrollbar = ttk.Scrollbar(all_apps_tab, orient="vertical", command=all_canvas.yview)
    all_apps_frame_inner = tk.Frame(all_canvas)

    all_apps_frame_inner.bind(
        "<Configure>",
        lambda e: all_canvas.configure(scrollregion=all_canvas.bbox("all"))
    )

    all_canvas.create_window((0, 0), window=all_apps_frame_inner, anchor="nw")
    all_canvas.configure(yscrollcommand=all_scrollbar.set)

    all_canvas.pack(side="left", fill="both", expand=True)
    all_scrollbar.pack(side="right", fill="y")

    # Installed tab
    installed_tab = ttk.Frame(notebook)
    notebook.add(installed_tab, text="Installed")

    inst_canvas = tk.Canvas(installed_tab, highlightthickness=0, bd=0)
    inst_scrollbar = ttk.Scrollbar(installed_tab, orient="vertical", command=inst_canvas.yview)
    installed_frame_inner = tk.Frame(inst_canvas)

    installed_frame_inner.bind(
        "<Configure>",
        lambda e: inst_canvas.configure(scrollregion=inst_canvas.bbox("all"))
    )

    inst_canvas.create_window((0, 0), window=installed_frame_inner, anchor="nw")
    inst_canvas.configure(yscrollcommand=inst_scrollbar.set)

    inst_canvas.pack(side="left", fill="both", expand=True)
    inst_scrollbar.pack(side="right", fill="y")

    # Updates tab
    updates_tab = ttk.Frame(notebook)
    notebook.add(updates_tab, text="Updates")

    upd_canvas = tk.Canvas(updates_tab, highlightthickness=0, bd=0)
    upd_scrollbar = ttk.Scrollbar(updates_tab, orient="vertical", command=upd_canvas.yview)
    updates_frame_inner = tk.Frame(upd_canvas)

    updates_frame_inner.bind(
        "<Configure>",
        lambda e: upd_canvas.configure(scrollregion=upd_canvas.bbox("all"))
    )

    upd_canvas.create_window((0, 0), window=updates_frame_inner, anchor="nw")
    upd_canvas.configure(yscrollcommand=upd_scrollbar.set)

    upd_canvas.pack(side="left", fill="both", expand=True)
    upd_scrollbar.pack(side="right", fill="y")

    # Settings tab
    settings_tab = ttk.Frame(notebook)
    notebook.add(settings_tab, text="Settings")
    settings_frame = settings_tab

    TILE_BG = settings.get("tile_bg_color", "#1f3b5b")

    populate_all_apps()
    populate_installed()
    populate_updates()
    build_settings_page()

    root.mainloop()

if __name__ == "__main__":
    main()