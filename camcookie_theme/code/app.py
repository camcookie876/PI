import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

HOME = os.path.expanduser("~")
BASE = f"{HOME}/camcookie"
THEME_DIR = f"{BASE}/theme-engine"
STORE_FILE = f"{BASE}/themestore/themestore.json"
THEME_VERSIONS = f"{BASE}/themestore/versions"

# ------------------------------
# Theme Import Logic
# ------------------------------

def import_theme(path):
    try:
        with open(path, "r") as f:
            theme = json.load(f)

        # Wallpapers
        if "wallpapers" in theme:
            for name, data in theme["wallpapers"].items():
                out = f"{BASE}/theme-wallpapers/{name}.png"
                with open(out, "wb") as w:
                    w.write(bytes.fromhex(data))

        # Sounds
        if "sounds" in theme:
            for name, data in theme["sounds"].items():
                out = f"{BASE}/theme-sounds/{name}.mp3"
                with open(out, "wb") as w:
                    w.write(bytes.fromhex(data))

        # Icons
        if "appearance" in theme and "iconPack" in theme["appearance"]:
            out = f"{BASE}/theme-icons/icons.zip"
            with open(out, "wb") as w:
                w.write(bytes.fromhex(theme["appearance"]["iconPack"]))

        messagebox.showinfo("Theme Imported", "Theme imported successfully!")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to import theme:\n{e}")

# ------------------------------
# GUI Application
# ------------------------------

class CamcookieApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Camcookie Control Center")
        self.geometry("900x600")
        self.configure(bg="#101010")

        self.sidebar = tk.Frame(self, bg="#181818", width=200)
        self.sidebar.pack(side="left", fill="y")

        self.main = tk.Frame(self, bg="#101010")
        self.main.pack(side="right", fill="both", expand=True)

        self.pages = {}

        self.create_sidebar()
        self.create_pages()
        self.show_page("home")

    # --------------------------
    # Sidebar
    # --------------------------

    def create_sidebar(self):
        buttons = [
            ("Home", "home"),
            ("Appearance", "appearance"),
            ("Notifications", "notifications"),
            ("Themes", "themes"),
            ("ThemeStore", "themestore"),
            ("Accessories", "accessories"),
            ("System", "system")
        ]

        for text, page in buttons:
            b = tk.Button(
                self.sidebar,
                text=text,
                bg="#252525",
                fg="white",
                relief="flat",
                command=lambda p=page: self.show_page(p)
            )
            b.pack(fill="x", pady=5, padx=10)

    # --------------------------
    # Pages
    # --------------------------

    def create_pages(self):
        self.pages["home"] = self.page_home()
        self.pages["appearance"] = self.page_appearance()
        self.pages["notifications"] = self.page_notifications()
        self.pages["themes"] = self.page_themes()
        self.pages["themestore"] = self.page_themestore()
        self.pages["accessories"] = self.page_accessories()
        self.pages["system"] = self.page_system()

    def show_page(self, name):
        for p in self.pages.values():
            p.pack_forget()
        self.pages[name].pack(fill="both", expand=True)

    # --------------------------
    # Individual Page Layouts
    # --------------------------

    def page_home(self):
        f = tk.Frame(self.main, bg="#101010")
        tk.Label(f, text="Welcome to Camcookie Control Center", fg="white", bg="#101010", font=("Arial", 20)).pack(pady=20)
        return f

    def page_appearance(self):
        f = tk.Frame(self.main, bg="#101010")
        tk.Label(f, text="Appearance Settings", fg="white", bg="#101010", font=("Arial", 18)).pack(pady=20)
        return f

    def page_notifications(self):
        f = tk.Frame(self.main, bg="#101010")
        tk.Label(f, text="Notification Animation", fg="white", bg="#101010", font=("Arial", 18)).pack(pady=20)

        tk.Label(f, text="Choose animation:", fg="white", bg="#101010").pack()

        animations = ["fade", "slide", "bounce", "pop", "glow"]
        self.anim_var = tk.StringVar(value="fade")

        for a in animations:
            tk.Radiobutton(f, text=a, variable=self.anim_var, value=a, bg="#101010", fg="white", selectcolor="#181818").pack(anchor="w")

        return f

    def page_themes(self):
        f = tk.Frame(self.main, bg="#101010")

        tk.Label(f, text="Installed Themes", fg="white", bg="#101010", font=("Arial", 18)).pack(pady=10)

        self.theme_list = tk.Listbox(f, bg="#181818", fg="white")
        self.theme_list.pack(fill="both", expand=True, padx=20, pady=10)

        tk.Button(f, text="Import Theme", command=self.import_theme_dialog).pack(pady=10)

        self.refresh_themes()

        return f

    def import_theme_dialog(self):
        path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if path:
            import_theme(path)
            self.refresh_themes()

    def refresh_themes(self):
        self.theme_list.delete(0, tk.END)
        if os.path.exists(THEME_VERSIONS):
            for f in os.listdir(THEME_VERSIONS):
                self.theme_list.insert(tk.END, f)

    def page_themestore(self):
        f = tk.Frame(self.main, bg="#101010")

        tk.Label(f, text="ThemeStore", fg="white", bg="#101010", font=("Arial", 18)).pack(pady=10)

        self.store_list = tk.Listbox(f, bg="#181818", fg="white")
        self.store_list.pack(fill="both", expand=True, padx=20, pady=10)

        tk.Button(f, text="Refresh", command=self.load_themestore).pack(pady=10)

        return f

    def load_themestore(self):
        self.store_list.delete(0, tk.END)
        try:
            with open(STORE_FILE, "r") as f:
                data = json.load(f)
            for theme in data["themes"]:
                self.store_list.insert(tk.END, theme["name"])
        except:
            self.store_list.insert(tk.END, "Failed to load ThemeStore")

    def page_accessories(self):
        f = tk.Frame(self.main, bg="#101010")

        tk.Label(f, text="Accessories", fg="white", bg="#101010", font=("Arial", 18)).pack(pady=10)

        self.acc_list = tk.Listbox(f, bg="#181818", fg="white")
        self.acc_list.pack(fill="both", expand=True, padx=20, pady=10)

        tk.Button(f, text="Refresh", command=self.load_accessories).pack(pady=10)

        return f

    def load_accessories(self):
        self.acc_list.delete(0, tk.END)
        apps = "/usr/share/applications"
        if os.path.exists(apps):
            for f in os.listdir(apps):
                self.acc_list.insert(tk.END, f)

    def page_system(self):
        f = tk.Frame(self.main, bg="#101010")

        tk.Label(f, text="System Info", fg="white", bg="#101010", font=("Arial", 18)).pack(pady=10)

        info = tk.Text(f, bg="#181818", fg="white")
        info.pack(fill="both", expand=True, padx=20, pady=10)

        info.insert("end", f"Home: {HOME}\n")
        info.insert("end", f"Camcookie Base: {BASE}\n")

        return f


# ------------------------------
# Run App
# ------------------------------

if __name__ == "__main__":
    app = CamcookieApp()
    app.mainloop()