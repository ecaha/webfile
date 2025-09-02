from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import requests

BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:5000")

app = Flask(__name__)


@app.get("/")
def index():
    path = request.args.get("path", "")
    r = requests.get(f"{BACKEND_URL}/api/list", params={"path": path}, timeout=10)
    data = r.json()
    return render_template("index.html", data=data)


@app.post("/mkdir")
def mkdir():
    path = request.form.get("path", "")
    name = request.form.get("name", "")
    target = f"{path}/{name}" if path else name
    r = requests.post(f"{BACKEND_URL}/api/mkdir", json={"path": target}, timeout=20)
    if r.ok:
        return redirect(url_for("index", path=path))
    return jsonify(r.json()), r.status_code


@app.post("/upload")
def upload():
    path = request.form.get("path", "")
    files = request.files.getlist("file")

    files_param = [("file", (f.filename, f.stream, f.mimetype)) for f in files]
    r = requests.post(f"{BACKEND_URL}/api/upload", params={"path": path}, files=files_param, timeout=120)
    if r.ok:
        return redirect(url_for("index", path=path))
    return jsonify(r.json()), r.status_code


@app.get("/download/<path:filename>")
def proxy_download(filename):
    # redirect to backend direct download URI to keep stable paths
    return redirect(f"{BACKEND_URL}/download/{filename}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
