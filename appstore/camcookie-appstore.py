#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import subprocess
import json
import urllib.request
import os
import sys
import webbrowser
import re

# =========================
# Basic config and paths
# =========================

APPSTORE_URL = "https://camcookie876.github.io/app/appstore/appstore.json"

HOME = os.path.expanduser("~")
LOCAL_DB = os.path.join(HOME, ".camcookie_installed.json")
ICON_CACHE_DIR = os.path.join(HOME, ".camcookie", "icons")
SETTINGS_FILE = os.path.join(HOME, ".camcookie", "appstore-settings.json")

os.makedirs(ICON_CACHE_DIR, exist_ok=True)
os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)

icon_cache_images = {}

# =========================
# Settings
# =========================

DEFAULT_SETTINGS = {
    "theme": "soft_blue",       # soft_blue, light, dark
    "tile_bg_color": "#1f3b5b", # soft tile
    "background_color": "#0b1220",
    "background_mode": "color", # reserved
    "startup_tab": "Home"       # Home, All, Installed, Updates, Settings
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

# =========================
# Installed versions DB
# =========================

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

# =========================
# Helpers
# =========================

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

# =========================
# Icon handling
# =========================

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

def clear_icon_cache_for_app(app_id):
    # Remove cached image from memory and disk
    if app_id in icon_cache_images:
        del icon_cache_images[app_id]
    for fname in os.listdir(ICON_CACHE_DIR):
        if fname.startswith(app_id):
            try:
                os.remove(os.path.join(ICON_CACHE_DIR, fname))
            except Exception:
                pass

# =========================
# Files from JSON
# =========================

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

# =========================
# Install / Uninstall logic
# =========================

def run_commands(cmd_list, title):
    cmds = expand_list(cmd_list)
    for cmd in cmds:
        subprocess.run(cmd, shell=True, check=True)

def install_app(app):
    create_files(app)
    try:
        run_commands(app.get("install", []), "Install")
        local_versions[app["id"]] = app["version"]
        save_local_versions(local_versions)
        messagebox.showinfo(
            "Installed",
            f"{app['name']} v{app['version']} installed successfully."
        )
    except Exception as e:
        messagebox.showerror("Error", f"Install failed:\n{e}")

def uninstall_app(app):
    app_id = app["id"]
    if app_id not in local_versions:
        messagebox.showinfo("Not installed", f"{app['name']} is not marked as installed.")
        return

    confirm = messagebox.askyesno(
        "Uninstall App",
        f"Completely uninstall {app['name']}?\n\n"
        "This will run its uninstall commands and remove it from installed apps."
    )
    if not confirm:
        return

    try:
        uninstall_cmds = app.get("uninstall", [])
        if uninstall_cmds:
            run_commands(uninstall_cmds, "Uninstall")
        # Drop from DB
        del local_versions[app_id]
        save_local_versions(local_versions)
        clear_icon_cache_for_app(app_id)
        messagebox.showinfo("Uninstalled", f"{app['name']} was uninstalled.")
        refresh_all_views()
    except Exception as e:
        messagebox.showerror("Error", f"Uninstall failed:\n{e}")

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

def handle_install_button(app):
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

# =========================
# Self-update for appstore
# =========================

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
            run_commands(appstore_entry.get("install", []), "Appstore Update")
            local_versions["camcookieappstore"] = remote_version
            save_local_versions(local_versions)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update Appstore:\n{e}")
            sys.exit(1)
        os.execv(sys.executable, ["python3"] + sys.argv)

# =========================
# URL link handling
# =========================

URL_REGEX = re.compile(r"(https?://[^\s]+)")

def make_linked_label(parent, text, fg="white", bg=None):
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

# =========================
# Theme
# =========================

TILE_BG = settings.get("tile_bg_color", "#1f3b5b")

def apply_theme(root):
    global TILE_BG
    theme = settings.get("theme", "soft_blue")
    TILE_BG = settings.get("tile_bg_color", "#1f3b5b")
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
        style.configure("Main.TFrame", background="#f0f0f0")
        style.configure("Nav.TFrame", background="#e4e4e4")
        style.configure("Nav.TButton",
                        background="#d0d0d0",
                        foreground="#000000",
                        padding=(12, 6))
        style.map("Nav.TButton",
                  background=[("active", "#c0c0c0")])
    elif theme == "dark":
        style.configure("Main.TFrame", background="#050816")
        style.configure("Nav.TFrame", background="#111827")
        style.configure("Nav.TButton",
                        background="#1f2937",
                        foreground="#ffffff",
                        padding=(12, 6))
        style.map("Nav.TButton",
                  background=[("active", "#374151")])
    else:  # soft_blue
        style.configure("Main.TFrame", background=bg_color)
        style.configure("Nav.TFrame", background="#020617")
        style.configure("Nav.TButton",
                        background="#020617",
                        foreground="#e5e7eb",
                        padding=(12, 6))
        style.map("Nav.TButton",
                  background=[("active", "#0f172a")])

    style.configure("TLabel", background=style.lookup("Main.TFrame", "background"),
                    foreground="#e5e7eb" if theme != "light" else "#000000")

# =========================
# UI helpers
# =========================

def clear_frame(frame):
    for w in frame.winfo_children():
        w.destroy()

# =========================
# App card + details
# =========================

def open_app_details(app):
    details = tk.Toplevel(root)
    details.title(app.get("name", "App details"))
    details.geometry("600x500")
    details.configure(bg="#020617")

    theme = settings.get("theme", "soft_blue")
    if theme == "light":
        fg = "#000000"
        bg = "#f9fafb"
        subfg = "#4b5563"
    else:
        fg = "#e5e7eb"
        bg = "#020617"
        subfg = "#9ca3af"

    details.configure(bg=bg)

    header = tk.Frame(details, bg=bg)
    header.pack(fill="x", padx=20, pady=(20, 10))

    icon_img = load_icon_image(app)
    if icon_img:
        icon_label = tk.Label(header, image=icon_img, bg=bg)
        icon_label.image = icon_img
        icon_label.pack(side="left", padx=(0, 12))
    else:
        icon_label = tk.Label(header, text="🟦", font=("Arial", 24), bg=bg, fg=fg)
        icon_label.pack(side="left", padx=(0, 12))

    name_frame = tk.Frame(header, bg=bg)
    name_frame.pack(side="left", fill="x", expand=True)

    tk.Label(name_frame, text=app.get("name", app["id"]),
             font=("Arial", 18, "bold"), bg=bg, fg=fg).pack(anchor="w")
    tk.Label(name_frame, text=f"by {app.get('creator', 'Unknown')}",
             font=("Arial", 11, "italic"), bg=bg, fg=subfg).pack(anchor="w")

    center = tk.Frame(details, bg=bg)
    center.pack(fill="both", expand=True, padx=20, pady=10)

    desc_label = tk.Label(center, text="Description:",
                          font=("Arial", 11, "bold"), bg=bg, fg=fg)
    desc_label.pack(anchor="w")
    make_linked_label(center, app.get("description", ""), fg=fg, bg=bg)

    version_text = f"Version: {app.get('version', 'N/A')}"
    local_version = local_versions.get(app["id"])
    if local_version:
        version_text += f"   Installed: {local_version}"
    tk.Label(center, text=version_text, font=("Arial", 10),
             bg=bg, fg=subfg).pack(anchor="w", pady=(6, 2))

    homepage = app.get("homepage")
    if homepage:
        def open_home():
            webbrowser.open(homepage)
        ttk.Button(center, text="Open homepage", command=open_home).pack(anchor="w", pady=(4, 8))

    btn_row = tk.Frame(details, bg=bg)
    btn_row.pack(fill="x", padx=20, pady=(10, 20))

    ttk.Button(btn_row, text="Install / Update",
               command=lambda a=app: [handle_install_button(a), details.destroy()]
               ).pack(side="left", padx=4)

    ttk.Button(btn_row, text="Open",
               command=lambda a=app: launch_app(a)
               ).pack(side="left", padx=4)

    ttk.Button(btn_row, text="Uninstall",
               command=lambda a=app: [uninstall_app(a), details.destroy()]
               ).pack(side="left", padx=4)

    ttk.Button(btn_row, text="Close", command=details.destroy).pack(side="right", padx=4)

def build_app_card(parent, app, compact=False):
    app_id = app["id"]
    name = app.get("name", app_id)
    creator = app.get("creator", "Unknown creator")
    description = app.get("description", "")
    remote_version = app.get("version", "0.0")
    local_version = local_versions.get(app_id)

    card = tk.Frame(parent, bd=0, bg=TILE_BG, highlightthickness=0)
    card.pack(fill="x", pady=8, padx=10)

    inner = tk.Frame(card, bg=TILE_BG)
    inner.pack(fill="both", expand=True, padx=8, pady=8)

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

    name_label = tk.Label(text_frame, text=name,
                          font=("Arial", 14, "bold"), bg=TILE_BG, fg="white")
    name_label.pack(anchor="w")

    creator_label = tk.Label(text_frame, text=f"by {creator}",
                             font=("Arial", 10, "italic"),
                             bg=TILE_BG, fg="#d1d5db")
    creator_label.pack(anchor="w")

    if not compact:
        make_linked_label(inner, description, fg="#e5e7eb", bg=TILE_BG)

    version_text = ""
    if local_version:
        if local_version == remote_version:
            version_text = f"Installed: {local_version} (up to date)"
        else:
            version_text = f"Installed: {local_version} | Available: {remote_version}"
    else:
        version_text = f"Available: {remote_version}"

    version_label = tk.Label(inner, text=version_text,
                             font=("Arial", 9), bg=TILE_BG, fg="#d1d5db")
    version_label.pack(anchor="w")

    btn_frame = tk.Frame(inner, bg=TILE_BG)
    btn_frame.pack(anchor="e", pady=(6, 0))

    ttk.Button(
        btn_frame,
        text="More info",
        command=lambda a=app: open_app_details(a)
    ).pack(side="left", padx=4)

    if local_version is None:
        primary_text = "Install"
    elif local_version != remote_version:
        primary_text = "Update"
    else:
        primary_text = "Reinstall"

    ttk.Button(
        btn_frame,
        text=primary_text,
        command=lambda a=app: handle_install_button(a)
    ).pack(side="left", padx=4)

    ttk.Button(
        btn_frame,
        text="Open",
        command=lambda a=app: launch_app(a)
    ).pack(side="left", padx=4)

    ttk.Button(
        btn_frame,
        text="Uninstall",
        command=lambda a=app: uninstall_app(a)
    ).pack(side="left", padx=4)

# =========================
# Views (tabs via top nav)
# =========================

def populate_home():
    clear_frame(home_frame)
    title = tk.Label(
        home_frame, text="Welcome to Camcookie Appstore",
        font=("Arial", 18, "bold"),
        bg=home_frame.cget("bg"),
        fg="#e5e7eb" if settings.get("theme") != "light" else "#111827"
    )
    title.pack(anchor="w", padx=20, pady=(20, 5))

    subtitle = tk.Label(
        home_frame,
        text="Featured apps, recent updates, and tools built for Camcookie OS.",
        font=("Arial", 11),
        bg=home_frame.cget("bg"),
        fg="#9ca3af" if settings.get("theme") != "light" else "#4b5563"
    )
    subtitle.pack(anchor="w", padx=20, pady=(0, 15))

    # Featured: first few apps
    if all_apps:
        tk.Label(
            home_frame, text="Featured Apps", font=("Arial", 13, "bold"),
            bg=home_frame.cget("bg"),
            fg="#e5e7eb" if settings.get("theme") != "light" else "#111827"
        ).pack(anchor="w", padx=20, pady=(5, 5))

        featured_frame = tk.Frame(home_frame, bg=home_frame.cget("bg"))
        featured_frame.pack(fill="x", padx=10)
        count = 0
        for app in all_apps:
            build_app_card(featured_frame, app, compact=True)
            count += 1
            if count >= 3:
                break

def populate_all_apps():
    clear_frame(all_apps_inner)
    search_term = all_search_var.get().strip().lower()
    for app in all_apps:
        if search_term:
            text_blob = " ".join([
                str(app.get("name", "")),
                str(app.get("creator", "")),
                str(app.get("description", "")),
                str(app.get("id", "")),
                " ".join(app.get("tags", []))
            ]).lower()
            if search_term not in text_blob:
                continue
        build_app_card(all_apps_inner, app)

def populate_installed():
    clear_frame(installed_inner)
    any_installed = False
    for app in all_apps:
        app_id = app["id"]
        if app_id in local_versions:
            build_app_card(installed_inner, app)
            any_installed = True
    if not any_installed:
        tk.Label(
            installed_inner,
            text="No apps installed yet. Go to All Apps to install something!",
            font=("Arial", 11),
            bg=installed_inner.cget("bg"),
            fg="#9ca3af" if settings.get("theme") != "light" else "#4b5563"
        ).pack(pady=20)

def populate_updates():
    clear_frame(updates_inner)
    any_updates = False
    for app in all_apps:
        app_id = app["id"]
        remote_version = app.get("version")
        local_version = local_versions.get(app_id)
        if local_version and remote_version and local_version != remote_version:
            build_app_card(updates_inner, app)
            any_updates = True
    if not any_updates:
        tk.Label(
            updates_inner,
            text="All apps are up to date.",
            font=("Arial", 11),
            bg=updates_inner.cget("bg"),
            fg="#9ca3af" if settings.get("theme") != "light" else "#4b5563"
        ).pack(pady=20)

def refresh_all_views(*args):
    populate_home()
    populate_all_apps()
    populate_installed()
    populate_updates()
    build_settings_page()

# =========================
# Settings UI
# =========================

def on_theme_change(new_theme):
    settings["theme"] = new_theme
    save_settings(settings)
    apply_theme(root)
    refresh_all_views()
    update_nav_style()

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

def reset_settings():
    confirm = messagebox.askyesno(
        "Reset Settings",
        "Reset Appstore appearance settings to defaults?"
    )
    if not confirm:
        return
    for k in list(settings.keys()):
        settings[k] = DEFAULT_SETTINGS.get(k, settings[k])
    save_settings(settings)
    apply_theme(root)
    refresh_all_views()
    update_nav_style()

def build_settings_page():
    clear_frame(settings_frame)

    title = ttk.Label(settings_frame, text="Settings", font=("Arial", 16, "bold"))
    title.pack(anchor="w", pady=(15, 10), padx=20)

    # Theme
    theme_label = ttk.Label(settings_frame, text="Theme:")
    theme_label.pack(anchor="w", padx=20)

    theme_frame = ttk.Frame(settings_frame)
    theme_frame.pack(anchor="w", padx=20, pady=(4, 10))

    current_theme = settings.get("theme", "soft_blue")
    theme_var = tk.StringVar(value=current_theme)

    def change_theme():
        on_theme_change(theme_var.get())

    ttk.Radiobutton(theme_frame, text="Soft Blue", value="soft_blue",
                    variable=theme_var, command=change_theme).pack(side="left", padx=4)
    ttk.Radiobutton(theme_frame, text="Light", value="light",
                    variable=theme_var, command=change_theme).pack(side="left", padx=4)
    ttk.Radiobutton(theme_frame, text="Dark", value="dark",
                    variable=theme_var, command=change_theme).pack(side="left", padx=4)

    # Tile color
    tile_label = ttk.Label(settings_frame, text="App tile background color:")
    tile_label.pack(anchor="w", padx=20, pady=(10, 0))

    tile_btn = ttk.Button(settings_frame, text="Choose tile color", command=choose_tile_color)
    tile_btn.pack(anchor="w", padx=20, pady=(4, 10))

    # Background
    bg_label = ttk.Label(settings_frame, text="Background color:")
    bg_label.pack(anchor="w", padx=20, pady=(10, 0))

    bg_btn = ttk.Button(settings_frame, text="Choose background color", command=choose_bg_color)
    bg_btn.pack(anchor="w", padx=20, pady=(4, 10))

    # Startup tab
    startup_label = ttk.Label(settings_frame, text="Startup page:")
    startup_label.pack(anchor="w", padx=20, pady=(10, 0))

    startup_var = tk.StringVar(value=settings.get("startup_tab", "Home"))
    def change_startup(*_):
        settings["startup_tab"] = startup_var.get()
        save_settings(settings)

    startup_combo = ttk.Combobox(
        settings_frame,
        textvariable=startup_var,
        values=["Home", "All Apps", "Installed", "Updates", "Settings"],
        state="readonly",
        width=20
    )
    startup_combo.bind("<<ComboboxSelected>>", change_startup)
    startup_combo.pack(anchor="w", padx=20, pady=(4, 10))

    # Reset
    reset_btn = ttk.Button(settings_frame, text="Reset to defaults", command=reset_settings)
    reset_btn.pack(anchor="w", padx=20, pady=(12, 5))

    info = ttk.Label(
        settings_frame,
        text="Settings are stored in ~/.camcookie/appstore-settings.json",
        font=("Arial", 9)
    )
    info.pack(anchor="w", padx=20, pady=(10, 0))

# =========================
# Navigation bar
# =========================

nav_buttons = {}
current_tab = None

def set_tab(tab_name):
    global current_tab
    current_tab = tab_name
    # Frames visibility
    home_frame.pack_forget()
    all_apps_frame.pack_forget()
    installed_frame.pack_forget()
    updates_frame.pack_forget()
    settings_frame.pack_forget()

    if tab_name == "Home":
        home_frame.pack(fill="both", expand=True)
    elif tab_name == "All Apps":
        all_apps_frame.pack(fill="both", expand=True)
    elif tab_name == "Installed":
        installed_frame.pack(fill="both", expand=True)
    elif tab_name == "Updates":
        updates_frame.pack(fill="both", expand=True)
    elif tab_name == "Settings":
        settings_frame.pack(fill="both", expand=True)

    # Button styles
    update_nav_style()

def update_nav_style():
    theme = settings.get("theme", "soft_blue")
    active_bg = "#2563eb" if theme == "soft_blue" else "#1f2937"
    inactive_bg = "#020617" if theme == "soft_blue" else "#111827"
    active_fg = "#e5e7eb"
    inactive_fg = "#9ca3af" if theme != "light" else "#111827"

    for name, btn in nav_buttons.items():
        if name == current_tab:
            btn.configure(style="NavActive.TButton")
        else:
            btn.configure(style="NavInactive.TButton")

    # Configure styles each time in case theme changed
    style = ttk.Style()
    style.configure(
        "NavActive.TButton",
        background=active_bg,
        foreground=active_fg,
        padding=(14, 6)
    )
    style.map("NavActive.TButton", background=[("active", active_bg)])
    style.configure(
        "NavInactive.TButton",
        background=inactive_bg,
        foreground=inactive_fg,
        padding=(14, 6)
    )
    style.map("NavInactive.TButton", background=[("active", inactive_bg)])

# =========================
# Main
# =========================

def main():
    global root, home_frame, all_apps_frame, installed_frame, updates_frame, settings_frame
    global all_apps, local_versions, all_apps_inner, installed_inner, updates_inner
    global all_search_var, nav_buttons

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

    # Self-update
    check_self_update(apps)

    # Root window
    root = tk.Tk()
    root.title("Camcookie Appstore V12")
    root.geometry("900x650")

    apply_theme(root)

    # Top title
    title_bar = ttk.Frame(root, style="Main.TFrame")
    title_bar.pack(fill="x", padx=16, pady=(10, 0))

    title_label = ttk.Label(
        title_bar, text="Camcookie Appstore",
        font=("Arial", 20, "bold")
    )
    title_label.pack(side="left")

    version_label = ttk.Label(
        title_bar,
        text="V12",
        font=("Arial", 9, "italic")
    )
    version_label.pack(side="left", padx=(8, 0))

    # Navigation bar
    nav_bar = ttk.Frame(root, style="Nav.TFrame")
    nav_bar.pack(fill="x", padx=16, pady=(10, 6))

    def make_nav_button(name):
        btn = ttk.Button(
            nav_bar,
            text=name,
            command=lambda n=name: set_tab(n)
        )
        btn.pack(side="left", padx=(0, 6))
        nav_buttons[name] = btn

    for tab_name in ["Home", "All Apps", "Installed", "Updates", "Settings"]:
        make_nav_button(tab_name)

    # Main content container
    content = ttk.Frame(root, style="Main.TFrame")
    content.pack(fill="both", expand=True, padx=16, pady=(0, 12))

    # Home frame
    home_frame = tk.Frame(content, bg=content.cget("background"))

    # All apps frame
    all_apps_frame = tk.Frame(content, bg=content.cget("background"))
    all_search_bar = ttk.Frame(all_apps_frame)
    all_search_bar.pack(fill="x", pady=(8, 4), padx=10)

    ttk.Label(all_search_bar, text="Search:").pack(side="left")
    all_search_var = tk.StringVar()
    all_search_entry = ttk.Entry(all_search_bar, textvariable=all_search_var, width=40)
    all_search_entry.pack(side="left", padx=6, fill="x", expand=True)
    all_search_var.trace_add("write", lambda *args: populate_all_apps())

    all_canvas = tk.Canvas(all_apps_frame, highlightthickness=0, bd=0,
                           bg=content.cget("background"))
    all_scrollbar = ttk.Scrollbar(all_apps_frame, orient="vertical", command=all_canvas.yview)
    all_apps_inner = tk.Frame(all_canvas, bg=content.cget("background"))

    all_apps_inner.bind(
        "<Configure>",
        lambda e: all_canvas.configure(scrollregion=all_canvas.bbox("all"))
    )

    all_canvas.create_window((0, 0), window=all_apps_inner, anchor="nw")
    all_canvas.configure(yscrollcommand=all_scrollbar.set)

    all_canvas.pack(side="left", fill="both", expand=True)
    all_scrollbar.pack(side="right", fill="y")

    # Installed frame
    installed_frame = tk.Frame(content, bg=content.cget("background"))
    inst_canvas = tk.Canvas(installed_frame, highlightthickness=0, bd=0,
                            bg=content.cget("background"))
    inst_scrollbar = ttk.Scrollbar(installed_frame, orient="vertical", command=inst_canvas.yview)
    installed_inner = tk.Frame(inst_canvas, bg=content.cget("background"))

    installed_inner.bind(
        "<Configure>",
        lambda e: inst_canvas.configure(scrollregion=inst_canvas.bbox("all"))
    )

    inst_canvas.create_window((0, 0), window=installed_inner, anchor="nw")
    inst_canvas.configure(yscrollcommand=inst_scrollbar.set)
    inst_canvas.pack(side="left", fill="both", expand=True)
    inst_scrollbar.pack(side="right", fill="y")

    # Updates frame
    updates_frame = tk.Frame(content, bg=content.cget("background"))
    upd_canvas = tk.Canvas(updates_frame, highlightthickness=0, bd=0,
                           bg=content.cget("background"))
    upd_scrollbar = ttk.Scrollbar(updates_frame, orient="vertical", command=upd_canvas.yview)
    updates_inner = tk.Frame(upd_canvas, bg=content.cget("background"))

    updates_inner.bind(
        "<Configure>",
        lambda e: upd_canvas.configure(scrollregion=upd_canvas.bbox("all"))
    )

    upd_canvas.create_window((0, 0), window=updates_inner, anchor="nw")
    upd_canvas.configure(yscrollcommand=upd_scrollbar.set)
    upd_canvas.pack(side="left", fill="both", expand=True)
    upd_scrollbar.pack(side="right", fill="y")

    # Settings frame
    settings_frame = tk.Frame(content, bg=content.cget("background"))

    # Initial content
    refresh_all_views()

    # Start on configured tab
    start_tab = settings.get("startup_tab", "Home")
    if start_tab not in ["Home", "All Apps", "Installed", "Updates", "Settings"]:
        start_tab = "Home"
    set_tab(start_tab)

    root.mainloop()

if __name__ == "__main__":
    main()