import os
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import tempfile

SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved")
os.makedirs(SAVE_DIR, exist_ok=True)

class PythonMakerApp:
    def __init__(self, root):
        self.root = root
        root.title("Python Maker")
        root.geometry("1000x700")

        # Editor frame
        editor_frame = tk.Frame(root)
        editor_frame.pack(side="left", fill="both", expand=True)

        tk.Label(editor_frame, text="Python Code", font=("Arial", 14, "bold")).pack(anchor="w")

        self.editor = tk.Text(editor_frame, wrap="none", font=("Courier", 12))
        self.editor.pack(fill="both", expand=True)

        # Output frame
        output_frame = tk.Frame(root, bg="#f0f0f0")
        output_frame.pack(side="right", fill="both", expand=True)

        tk.Label(output_frame, text="Output", font=("Arial", 14, "bold"), bg="#f0f0f0").pack(anchor="w")

        self.output = tk.Text(output_frame, wrap="word", font=("Courier", 12), bg="#ffffff")
        self.output.pack(fill="both", expand=True)

        # Bottom bar
        bar = tk.Frame(root)
        bar.pack(side="bottom", fill="x")

        self.filename_entry = tk.Entry(bar, width=30)
        self.filename_entry.pack(side="left", padx=5)

        tk.Button(bar, text="Save", command=self.save_file).pack(side="left", padx=5)
        tk.Button(bar, text="Load", command=self.load_file).pack(side="left", padx=5)
        tk.Button(bar, text="Run ▶", command=self.run_code).pack(side="left", padx=5)

        # Default starter code
        starter = """print("Hello from PythonMaker!")"""
        self.editor.insert("1.0", starter)

    def run_code(self):
        code = self.editor.get("1.0", "end")

        # Save to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp:
            tmp.write(code.encode("utf-8"))
            tmp_path = tmp.name

        # Run Python and capture output
        try:
            result = subprocess.run(
                ["python3", tmp_path],
                capture_output=True,
                text=True
            )
            output_text = result.stdout + result.stderr
        except Exception as e:
            output_text = str(e)

        self.output.delete("1.0", "end")
        self.output.insert("1.0", output_text)

    def save_file(self):
        filename = self.filename_entry.get().strip()
        if not filename:
            messagebox.showerror("Error", "Enter a filename first")
            return

        if not filename.endswith(".py"):
            filename += ".py"

        path = os.path.join(SAVE_DIR, filename)
        code = self.editor.get("1.0", "end")

        with open(path, "w", encoding="utf-8") as f:
            f.write(code)

        messagebox.showinfo("Saved", f"Saved as {filename}")

    def load_file(self):
        path = filedialog.askopenfilename(initialdir=SAVE_DIR, filetypes=[("Python Files", "*.py")])
        if not path:
            return

        with open(path, "r", encoding="utf-8") as f:
            code = f.read()

        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", code)

        self.filename_entry.delete(0, "end")
        self.filename_entry.insert(0, os.path.basename(path))

if __name__ == "__main__":
    root = tk.Tk()
    app = PythonMakerApp(root)
    root.mainloop()