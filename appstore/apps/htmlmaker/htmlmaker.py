import os
import webview
from flask import Flask, send_from_directory, request, jsonify
import threading

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "saved")
os.makedirs(SAVE_DIR, exist_ok=True)

@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "editor.html")

@app.route("/save", methods=["POST"])
def save():
    data = request.get_json()
    filename = data.get("filename", "untitled.html")
    code = data.get("code", "")
    filename = os.path.basename(filename)
    path = os.path.join(SAVE_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    return jsonify({"status": "ok", "filename": filename})

@app.route("/load", methods=["GET"])
def load():
    filename = request.args.get("filename", "")
    filename = os.path.basename(filename)
    path = os.path.join(SAVE_DIR, filename)
    if not os.path.exists(path):
        return jsonify({"status": "error", "message": "File not found"}), 404
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()
    return jsonify({"status": "ok", "code": code})

@app.route("/list", methods=["GET"])
def list_files():
    files = [f for f in os.listdir(SAVE_DIR) if f.endswith(".html")]
    return jsonify({"status": "ok", "files": files})

def start_flask():
    app.run(host="127.0.0.1", port=8000)

if __name__ == "__main__":
    threading.Thread(target=start_flask).start()
    webview.create_window("HTML Maker", "http://127.0.0.1:8000", width=1000, height=700)