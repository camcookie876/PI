import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkhtmlview import HTMLLabel

SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved")
os.makedirs(SAVE_DIR, exist_ok=True)

class HTMLMakerApp:
    def __init__(self, root):
        self.root = root
        root.title("HTML Maker")
        root.geometry("1000x700")

        # Main layout
        self.editor = tk.Text(root, wrap="none", font=("Courier", 12))
        self.editor.pack(side="left", fill="both", expand=True)

        self.preview = HTMLLabel(root, html="<h1>Preview</h1>")
        self.preview.pack(side="right", fill="both", expand=True)

        # Bottom bar
        bar = tk.Frame(root)
        bar.pack(side="bottom", fill="x")

        self.filename_entry = tk.Entry(bar, width=30)
        self.filename_entry.pack(side="left", padx=5)

        tk.Button(bar, text="Save", command=self.save_file).pack(side="left", padx=5)
        tk.Button(bar, text="Load", command=self.load_file).pack(side="left", padx=5)
        tk.Button(bar, text="Run ▶", command=self.update_preview).pack(side="left", padx=5)

        # Default HTML
        default_html = """
<!DOCTYPE html>
<html>
<head>
<title>My Page</title>
</head>
<body>
<h1>Hello from HTML Maker!</h1>
<p>Edit this HTML and see the preview update.</p>
</body>
</html>
"""
        self.editor.insert("1.0", default_html)
        self.update_preview()

    def update_preview(self):
        html = self.editor.get("1.0", "end")
        self.preview.set_html(html)

    def save_file(self):
        filename = self.filename_entry.get().strip()
        if not filename:
            messagebox.showerror("Error", "Enter a filename first")
            return

        if not filename.endswith(".html"):
            filename += ".html"

        path = os.path.join(SAVE_DIR, filename)
        html = self.editor.get("1.0", "end")

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

        messagebox.showinfo("Saved", f"Saved as {filename}")

    def load_file(self):
        path = filedialog.askopenfilename(initialdir=SAVE_DIR, filetypes=[("HTML Files", "*.html")])
        if not path:
            return

        with open(path, "r", encoding="utf-8") as f:
            html = f.read()

        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", html)
        self.update_preview()

        self.filename_entry.delete(0, "end")
        self.filename_entry.insert(0, os.path.basename(path))

if __name__ == "__main__":
    root = tk.Tk()
    app = HTMLMakerApp(root)
    root.mainloop()