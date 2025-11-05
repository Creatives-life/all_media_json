# app.py
import os
import io
import json
import base64
import mimetypes
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change_this_secret")

def file_to_data_uri(filename, raw_bytes):
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = "application/octet-stream"
    encoded = base64.b64encode(raw_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/convert", methods=["POST"])
def convert():
    if "files" not in request.files:
        flash("No files part in the request")
        return redirect(url_for("index"))

    files = request.files.getlist("files")
    if not files or len(files) == 0:
        flash("No files selected")
        return redirect(url_for("index"))

    media_dict = {}
    name_counts = {}

    for f in files:
        if f.filename == "":
            continue
        filename = secure_filename(f.filename)
        # read into memory
        content = f.read()
        # key: filename without extension (avoid duplicates)
        base_key = os.path.splitext(filename)[0]
        # ensure unique keys
        count = name_counts.get(base_key, 0)
        name_counts[base_key] = count + 1
        key = f"{base_key}" if count == 0 else f"{base_key}_{count+1}"
        media_dict[key] = file_to_data_uri(filename, content)

    if not media_dict:
        flash("Failed to process uploaded files")
        return redirect(url_for("index"))

    # create an in-memory JSON file for download
    json_bytes = json.dumps(media_dict, indent=2).encode("utf-8")
    bio = io.BytesIO(json_bytes)
    bio.seek(0)

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_name = f"media_{timestamp}.json"

    return send_file(
        bio,
        as_attachment=True,
        download_name=out_name,
        mimetype="application/json"
    )

if __name__ == "__main__":
    # For local dev. Render will use gunicorn.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
