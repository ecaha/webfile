import os
from flask import Flask, jsonify, request, send_from_directory, abort
from werkzeug.utils import secure_filename
from pathlib import Path

UPLOAD_ROOT = os.environ.get("UPLOAD_ROOT", "/data")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("MAX_CONTENT_LENGTH", 1024 * 1024 * 1024))  # 1GB default


def safe_path(path: str) -> Path:
    base = Path(UPLOAD_ROOT).resolve()
    target = (base / path).resolve()
    if not str(target).startswith(str(base)):
        abort(400, description="Invalid path")
    return target


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/list")
def list_dir():
    rel = request.args.get("path", "")
    # normalize path (strip leading/trailing slashes)
    rel_norm = rel.strip("/")
    # compute parent path
    if rel_norm:
        parent = rel_norm.rsplit("/", 1)[0] if "/" in rel_norm else ""
    else:
        parent = ""

    target = safe_path(rel_norm)
    if not target.exists():
        return jsonify({"path": rel_norm, "parent": parent, "exists": False, "items": []})

    items = []
    if target.is_dir():
        for p in sorted(target.iterdir()):
            stat = p.stat()
            items.append({
                "name": p.name,
                "is_dir": p.is_dir(),
                "size": 0 if p.is_dir() else stat.st_size,
                "mtime": stat.st_mtime,
                "path": str(Path(rel_norm) / p.name) if rel_norm else p.name
            })
    else:
        stat = target.stat()
        items.append({
            "name": target.name,
            "is_dir": False,
            "size": stat.st_size,
            "mtime": stat.st_mtime,
            "path": rel_norm
        })

    return jsonify({"path": rel_norm, "parent": parent, "exists": True, "items": items})


@app.post("/api/mkdir")
def mkdir():
    data = request.get_json(force=True)
    rel = data.get("path", "")
    target = safe_path(rel)
    target.mkdir(parents=True, exist_ok=True)
    return jsonify({"ok": True})


@app.post("/api/upload")
def upload_file():
    rel = request.args.get("path", "")
    base_dir = safe_path(rel)
    base_dir.mkdir(parents=True, exist_ok=True)

    files = request.files.getlist("file")
    relpaths = request.form.getlist("relpath")  # optional, aligned with files order
    saved = []
    for idx, f in enumerate(files):
        # Determine destination relative path
        rp = relpaths[idx] if idx < len(relpaths) else None
        if rp:
            rp_path = Path(rp)
            # sanitize each component and ignore unsafe components
            safe_parts = [secure_filename(p) for p in rp_path.parts if p not in ("", ".", "..")]
            if not safe_parts:
                filename = secure_filename(f.filename)
                dest_rel = Path(rel) / filename
            else:
                # last part is filename
                parts_dir = safe_parts[:-1]
                filename = secure_filename(safe_parts[-1])
                dest_rel = Path(rel)
                for p in parts_dir:
                    dest_rel = dest_rel / p
                dest_rel = dest_rel / filename
        else:
            filename = secure_filename(f.filename)
            if not filename:
                continue
            dest_rel = Path(rel) / filename

        dest_abs = safe_path(str(dest_rel))
        dest_abs.parent.mkdir(parents=True, exist_ok=True)
        f.save(dest_abs)
        saved.append(str(dest_rel))

    return jsonify({"ok": True, "paths": saved})


@app.get("/download/<path:filename>")
def download(filename):
    # direct file download via stable URI
    target = safe_path(filename)
    if not target.exists() or not target.is_file():
        abort(404)
    directory = target.parent
    return send_from_directory(directory, target.name, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
