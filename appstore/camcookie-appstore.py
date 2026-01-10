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

APPSTORE_URL = "https://camcookie876.github.io/PI/appstore/appstore.json"

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
    "tile_bg_color": "#1f3b5b",
    "background_color": "#0b1220",
    "startup_tab": "Home"       # Home, All Apps, Installed, Updates, Settings
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

def get_safe_color(value, fallback):
    if not isinstance(value, str):
        return fallback
    if not value.startswith("#"):
        return fallback
    if len(value) not in (4, 7):
        return fallback
    return value

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
# Icon handling (V1.5: resize + rounded background)
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

def load_icon_image(app, max_size=56):
    """
    Load and downscale icon to fit inside max_size x max_size,
    preserving aspect ratio, using PhotoImage.subsample.
    """
    app_id = app.get("id", "unknown")
    cache_key = f"{app_id}_{max_size}"
    if cache_key in icon_cache_images:
        return icon_cache_images[cache_key]

    local_icon_path = download_icon_if_needed(app)
    if not local_icon_path or not os.path.exists(local_icon_path):
        return None
    try:
        img = tk.PhotoImage(file=local_icon_path)
    except Exception:
        return None

    w = img.width()
    h = img.height()
    if w <= 0 or h <= 0:
        return None

    # Compute integer subsample factor to ensure the image fits inside max_size
    factor = max(1, max(w // max_size, h // max_size))
    if factor > 1:
        try:
            img = img.subsample(factor, factor)
        except Exception:
            pass  # If subsample fails, keep original (worst case, still works but larger)

    icon_cache_images[cache_key] = img
    return img

def clear_icon_cache_for_app(app_id):
    keys_to_delete = [k for k in icon_cache_images.keys() if k.startswith(app_id + "_")]
    for k in keys_to_delete:
        del icon_cache_images[k]
    for fname in os.listdir(ICON_CACHE_DIR):
        if fname.startswith(app_id):
            try:
                os.remove(os.path.join(ICON_CACHE_DIR, fname))
            except Exception:
                pass

def create_rounded_icon_widget(parent, app, tile_bg, size=64, icon_size=56):
    """
    Creates a canvas with a rounded background and the app icon centered inside.
    - size: total canvas size (e.g., 64x64)
    - icon_size: target maximum icon size inside the rounded area
    """
    canvas = tk.Canvas(parent, width=size, height=size, bg=tile_bg,
                       highlightthickness=0, bd=0)
    # Rounded/circular background
    margin = 4
    canvas.create_oval(margin, margin, size - margin, size - margin,
                       fill="#0f172a", outline="")

    icon_img = load_icon_image(app, max_size=icon_size)
    if icon_img is not None:
        canvas.create_image(size // 2, size // 2, image=icon_img)
        # Keep a reference so it's not garbage collected
        canvas.image = icon_img
    else:
        # Fallback emoji placeholder
        canvas.create_text(size // 2, size // 2, text="🟦", font=("Arial", 18))

    return canvas

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
        if app_id in local_versions:
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
# Theme (pure tk, no ttk bg hacks)
# =========================

def get_theme_colors():
    theme = settings.get("theme", "soft_blue")
    bg = get_safe_color(settings.get("background_color"), "#0b1220")
    tile = get_safe_color(settings.get("tile_bg_color"), "#1f3b5b")

    if theme == "light":
        return {
            "bg": "#f5f5f5",
            "fg_main": "#111827",
            "fg_sub": "#4b5563",
            "tile": "#e5e7eb"
        }
    elif theme == "dark":
        return {
            "bg": "#050816",
            "fg_main": "#e5e7eb",
            "fg_sub": "#9ca3af",
            "tile": tile
        }
    else:  # soft_blue
        return {
            "bg": bg,
            "fg_main": "#e5e7eb",
            "fg_sub": "#9ca3af",
            "tile": tile
        }

# =========================
# UI helpers
# =========================

def clear_frame(frame):
    for w in frame.winfo_children():
        w.destroy()

# =========================
# App details window
# =========================

def open_app_details(app):
    colors = get_theme_colors()
    bg = colors["bg"]
    fg = colors["fg_main"]
    subfg = colors["fg_sub"]

    details = tk.Toplevel(root)
    details.title(app.get("name", "App details"))
    details.geometry("600x500")
    details.configure(bg=bg)

    header = tk.Frame(details, bg=bg)
    header.pack(fill="x", padx=20, pady=(20, 10))

    # Rounded icon in details view
    icon_container = tk.Frame(header, bg=bg)
    icon_container.pack(side="left", padx=(0, 12))
    icon_canvas = create_rounded_icon_widget(icon_container, app, tile_bg=bg, size=64, icon_size=56)
    icon_canvas.pack()

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

# =========================
# App card
# =========================

def build_app_card(parent, app, compact=False):
    colors = get_theme_colors()
    tile_bg = colors["tile"]
    fg_main = "#ffffff"
    fg_sub = "#d1d5db"

    app_id = app["id"]
    name = app.get("name", app_id)
    creator = app.get("creator", "Unknown creator")
    description = app.get("description", "")
    remote_version = app.get("version", "0.0")
    local_version = local_versions.get(app_id)

    card = tk.Frame(parent, bd=0, bg=parent.cget("bg"), highlightthickness=0)
    card.pack(fill="x", pady=8, padx=10)

    inner = tk.Frame(card, bg=tile_bg)
    inner.pack(fill="both", expand=True, padx=8, pady=8)

    top_frame = tk.Frame(inner, bg=tile_bg)
    top_frame.pack(fill="x")

    # Rounded icon container
    icon_container = tk.Frame(top_frame, bg=tile_bg)
    icon_container.pack(side="left", padx=(0, 10))
    icon_canvas = create_rounded_icon_widget(icon_container, app, tile_bg=tile_bg, size=64, icon_size=56)
    icon_canvas.pack()

    text_frame = tk.Frame(top_frame, bg=tile_bg)
    text_frame.pack(side="left", fill="x", expand=True)

    name_label = tk.Label(text_frame, text=name,
                          font=("Arial", 14, "bold"), bg=tile_bg, fg=fg_main)
    name_label.pack(anchor="w")

    creator_label = tk.Label(text_frame, text=f"by {creator}",
                             font=("Arial", 10, "italic"),
                             bg=tile_bg, fg=fg_sub)
    creator_label.pack(anchor="w")

    if not compact:
        make_linked_label(inner, description, fg=fg_main, bg=tile_bg)

    version_text = ""
    if local_version:
        if local_version == remote_version:
            version_text = f"Installed: {local_version} (up to date)"
        else:
            version_text = f"Installed: {local_version} | Available: {remote_version}"
    else:
        version_text = f"Available: {remote_version}"

    version_label = tk.Label(inner, text=version_text,
                             font=("Arial", 9), bg=tile_bg, fg=fg_sub)
    version_label.pack(anchor="w")

    btn_frame = tk.Frame(inner, bg=tile_bg)
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
# Views
# =========================

def populate_home():
    clear_frame(home_frame)
    colors = get_theme_colors()
    bg = colors["bg"]
    fg_main = colors["fg_main"]
    fg_sub = colors["fg_sub"]
    home_frame.configure(bg=bg)

    title = tk.Label(
        home_frame, text="Welcome to Camcookie Appstore",
        font=("Arial", 18, "bold"),
        bg=bg,
        fg=fg_main
    )
    title.pack(anchor="w", padx=20, pady=(20, 5))

    subtitle = tk.Label(
        home_frame,
        text="Featured apps, recent updates, and tools built for Camcookie OS.",
        font=("Arial", 11),
        bg=bg,
        fg=fg_sub
    )
    subtitle.pack(anchor="w", padx=20, pady=(0, 15))

    if all_apps:
        section_label = tk.Label(
            home_frame, text="Featured Apps", font=("Arial", 13, "bold"),
            bg=bg, fg=fg_main
        )
        section_label.pack(anchor="w", padx=20, pady=(5, 5))

        featured_frame = tk.Frame(home_frame, bg=bg)
        featured_frame.pack(fill="x", padx=10)
        count = 0
        for app in all_apps:
            build_app_card(featured_frame, app, compact=True)
            count += 1
            if count >= 3:
                break

def populate_all_apps():
    clear_frame(all_apps_inner)
    colors = get_theme_colors()
    bg = colors["bg"]
    all_apps_inner.configure(bg=bg)
    all_canvas.configure(bg=bg)

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
    colors = get_theme_colors()
    bg = colors["bg"]
    fg_sub = colors["fg_sub"]
    installed_inner.configure(bg=bg)
    inst_canvas.configure(bg=bg)

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
            bg=bg,
            fg=fg_sub
        ).pack(pady=20)

def populate_updates():
    clear_frame(updates_inner)
    colors = get_theme_colors()
    bg = colors["bg"]
    fg_sub = colors["fg_sub"]
    updates_inner.configure(bg=bg)
    upd_canvas.configure(bg=bg)

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
            bg=bg,
            fg=fg_sub
        ).pack(pady=20)

def refresh_all_views(*args):
    populate_home()
    populate_all_apps()
    populate_installed()
    populate_updates()
    build_settings_page()
    apply_colors_to_shell()

# =========================
# Settings UI
# =========================

def on_theme_change(new_theme):
    settings["theme"] = new_theme
    save_settings(settings)
    refresh_all_views()
    update_nav_style()

def choose_tile_color():
    initial = get_safe_color(settings.get("tile_bg_color"), "#1f3b5b")
    color = colorchooser.askcolor(initialcolor=initial)[1]
    if color:
        settings["tile_bg_color"] = color
        save_settings(settings)
        refresh_all_views()

def choose_bg_color():
    initial = get_safe_color(settings.get("background_color"), "#0b1220")
    color = colorchooser.askcolor(initialcolor=initial)[1]
    if color:
        settings["background_color"] = color
        save_settings(settings)
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
    refresh_all_views()
    update_nav_style()

def build_settings_page():
    clear_frame(settings_frame)
    colors = get_theme_colors()
    bg = colors["bg"]
    fg_main = colors["fg_main"]
    fg_sub = colors["fg_sub"]
    settings_frame.configure(bg=bg)

    title = tk.Label(settings_frame, text="Settings",
                     font=("Arial", 16, "bold"), bg=bg, fg=fg_main)
    title.pack(anchor="w", pady=(15, 10), padx=20)

    theme_label = tk.Label(settings_frame, text="Theme:", bg=bg, fg=fg_main)
    theme_label.pack(anchor="w", padx=20)

    theme_frame = tk.Frame(settings_frame, bg=bg)
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

    tile_label = tk.Label(settings_frame, text="App tile background color:",
                          bg=bg, fg=fg_main)
    tile_label.pack(anchor="w", padx=20, pady=(10, 0))

    tile_btn = ttk.Button(settings_frame, text="Choose tile color", command=choose_tile_color)
    tile_btn.pack(anchor="w", padx=20, pady=(4, 10))

    bg_label = tk.Label(settings_frame, text="Background color:",
                        bg=bg, fg=fg_main)
    bg_label.pack(anchor="w", padx=20, pady=(10, 0))

    bg_btn = ttk.Button(settings_frame, text="Choose background color", command=choose_bg_color)
    bg_btn.pack(anchor="w", padx=20, pady=(4, 10))

    startup_label = tk.Label(settings_frame, text="Startup page:",
                             bg=bg, fg=fg_main)
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

    reset_btn = ttk.Button(settings_frame, text="Reset to defaults", command=reset_settings)
    reset_btn.pack(anchor="w", padx=20, pady=(12, 5))

    info = tk.Label(
        settings_frame,
        text="Settings are stored in ~/.camcookie/appstore-settings.json",
        font=("Arial", 9),
        bg=bg,
        fg=fg_sub
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

    update_nav_style()

def update_nav_style():
    colors = get_theme_colors()
    bg = colors["bg"]
    fg_main = colors["fg_main"]
    fg_sub = colors["fg_sub"]

    nav_bg = "#020617" if settings.get("theme") == "soft_blue" else bg
    active_bg = "#2563eb" if settings.get("theme") == "soft_blue" else "#1f2937"
    inactive_bg = nav_bg
    active_fg = "#e5e7eb"
    inactive_fg = fg_sub

    nav_bar.configure(bg=nav_bg)

    for name, btn in nav_buttons.items():
        if name == current_tab:
            btn.configure(
                style="NavActive.TButton"
            )
        else:
            btn.configure(
                style="NavInactive.TButton"
            )

    style = ttk.Style()
    style.configure(
        "NavActive.TButton",
        padding=(14, 6),
        foreground=active_fg
    )
    style.map(
        "NavActive.TButton",
        background=[("!disabled", active_bg), ("active", active_bg)]
    )
    style.configure(
        "NavInactive.TButton",
        padding=(14, 6),
        foreground=inactive_fg
    )
    style.map(
        "NavInactive.TButton",
        background=[("!disabled", inactive_bg), ("active", inactive_bg)]
    )

def apply_colors_to_shell():
    colors = get_theme_colors()
    bg = colors["bg"]
    fg_main = colors["fg_main"]
    fg_sub = colors["fg_sub"]

    root.configure(bg=bg)
    title_bar.configure(bg=bg)
    title_label.configure(bg=bg, fg=fg_main)
    version_label.configure(bg=bg, fg=fg_sub)
    content.configure(bg=bg)

# =========================
# Main
# =========================

def main():
    global root, home_frame, all_apps_frame, installed_frame, updates_frame, settings_frame
    global all_apps, local_versions
    global all_apps_inner, installed_inner, updates_inner
    global all_search_var, all_canvas, inst_canvas, upd_canvas
    global nav_bar, nav_buttons, title_bar, title_label, version_label, content

    if not os.path.exists(LOCAL_DB):
        with open(LOCAL_DB, "w") as f:
            f.write("{}")

    local_versions_dict = load_local_versions()
    globals()["local_versions"] = local_versions_dict

    try:
        apps = load_catalog()
    except Exception as e:
        tk.Tk().withdraw()
        messagebox.showerror("Error", f"Failed to load app catalog:\n{e}")
        return

    globals()["all_apps"] = apps

    check_self_update(apps)

    root = tk.Tk()
    root.title("Camcookie Appstore V1.5")
    root.geometry("900x650")

    colors = get_theme_colors()
    bg = colors["bg"]
    fg_main = colors["fg_main"]
    fg_sub = colors["fg_sub"]

    root.configure(bg=bg)

    title_bar = tk.Frame(root, bg=bg)
    title_bar.pack(fill="x", padx=16, pady=(10, 0))

    title_label = tk.Label(
        title_bar, text="Camcookie Appstore",
        font=("Arial", 20, "bold"),
        bg=bg, fg=fg_main
    )
    title_label.pack(side="left")

    version_label = tk.Label(
        title_bar,
        text="V1.5",
        font=("Arial", 9, "italic"),
        bg=bg, fg=fg_sub
    )
    version_label.pack(side="left", padx=(8, 0))

    nav_bar = tk.Frame(root, bg="#020617" if settings.get("theme") == "soft_blue" else bg)
    nav_bar.pack(fill="x", padx=16, pady=(10, 6))
    globals()["nav_bar"] = nav_bar

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

    content = tk.Frame(root, bg=bg)
    content.pack(fill="both", expand=True, padx=16, pady=(0, 12))

    home_frame = tk.Frame(content, bg=bg)

    all_apps_frame = tk.Frame(content, bg=bg)
    all_search_bar = tk.Frame(all_apps_frame, bg=bg)
    all_search_bar.pack(fill="x", pady=(8, 4), padx=10)

    tk.Label(all_search_bar, text="Search:", bg=bg, fg=fg_main).pack(side="left")
    all_search_var = tk.StringVar()
    all_search_entry = ttk.Entry(all_search_bar, textvariable=all_search_var, width=40)
    all_search_entry.pack(side="left", padx=6, fill="x", expand=True)
    all_search_var.trace_add("write", lambda *args: populate_all_apps())

    all_canvas = tk.Canvas(all_apps_frame, highlightthickness=0, bd=0, bg=bg)
    all_scrollbar = ttk.Scrollbar(all_apps_frame, orient="vertical", command=all_canvas.yview)
    all_apps_inner = tk.Frame(all_canvas, bg=bg)

    all_apps_inner.bind(
        "<Configure>",
        lambda e: all_canvas.configure(scrollregion=all_canvas.bbox("all"))
    )

    all_canvas.create_window((0, 0), window=all_apps_inner, anchor="nw")
    all_canvas.configure(yscrollcommand=all_scrollbar.set)

    all_canvas.pack(side="left", fill="both", expand=True)
    all_scrollbar.pack(side="right", fill="y")

    installed_frame = tk.Frame(content, bg=bg)
    inst_canvas = tk.Canvas(installed_frame, highlightthickness=0, bd=0, bg=bg)
    inst_scrollbar = ttk.Scrollbar(installed_frame, orient="vertical", command=inst_canvas.yview)
    installed_inner = tk.Frame(inst_canvas, bg=bg)

    installed_inner.bind(
        "<Configure>",
        lambda e: inst_canvas.configure(scrollregion=inst_canvas.bbox("all"))
    )

    inst_canvas.create_window((0, 0), window=installed_inner, anchor="nw")
    inst_canvas.configure(yscrollcommand=inst_scrollbar.set)
    inst_canvas.pack(side="left", fill="both", expand=True)
    inst_scrollbar.pack(side="right", fill="y")

    updates_frame = tk.Frame(content, bg=bg)
    upd_canvas = tk.Canvas(updates_frame, highlightthickness=0, bd=0, bg=bg)
    upd_scrollbar = ttk.Scrollbar(updates_frame, orient="vertical", command=upd_canvas.yview)
    updates_inner = tk.Frame(upd_canvas, bg=bg)

    updates_inner.bind(
        "<Configure>",
        lambda e: upd_canvas.configure(scrollregion=upd_canvas.bbox("all"))
    )

    upd_canvas.create_window((0, 0), window=updates_inner, anchor="nw")
    upd_canvas.configure(yscrollcommand=upd_scrollbar.set)
    upd_canvas.pack(side="left", fill="both", expand=True)
    upd_scrollbar.pack(side="right", fill="y")

    settings_frame = tk.Frame(content, bg=bg)

    globals().update({
        "home_frame": home_frame,
        "all_apps_frame": all_apps_frame,
        "installed_frame": installed_frame,
        "updates_frame": updates_frame,
        "settings_frame": settings_frame,
        "content": content,
        "all_canvas": all_canvas,
        "inst_canvas": inst_canvas,
        "upd_canvas": upd_canvas
    })

    refresh_all_views()

    start_tab = settings.get("startup_tab", "Home")
    if start_tab not in ["Home", "All Apps", "Installed", "Updates", "Settings"]:
        start_tab = "Home"
    set_tab(start_tab)

    root.mainloop()

if __name__ == "__main__":
    main()