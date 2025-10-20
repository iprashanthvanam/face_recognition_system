import os
import io
import base64
import shutil
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np
import cv2

from face_recognition_utils import (
    encode_all_faces,
    recognize_image_file,
    recognize_frame,
    add_face_from_file,
    delete_face,
    ENC_PATH,
    FACES_DIR,
    UPLOADS_DIR
)

# Configuration
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
FACES_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
if not ENC_PATH.exists():
    # ensure there's an encoding file (empty)
    encode_all_faces(FACES_DIR, ENC_PATH)

app = Flask(__name__)
app.secret_key = "replace-this-with-a-secret"  # set a better secret for production
app.config["UPLOAD_FOLDER"] = str(UPLOADS_DIR)
app.config["FACES_FOLDER"] = str(FACES_DIR)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload


@app.route("/")
def index():
    return render_template("index.html")


# Upload + Recognize (image file)
@app.route("/upload", methods=["GET", "POST"])
def upload_page():
    if request.method == "POST":
        if "image" not in request.files:
            flash("No image part")
            return redirect(request.url)
        file = request.files["image"]
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        filename = secure_filename(file.filename)
        save_path = UPLOADS_DIR / filename
        file.save(save_path)
        result = recognize_image_file(str(save_path), str(ENC_PATH))
        return render_template("result.html", result=result, filename=filename, source="upload")
    return render_template("upload.html")


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# Webcam page (client captures frames & sends as base64)
@app.route("/webcam")
def webcam_page():
    return render_template("webcam.html")


@app.route("/recognize_webcam", methods=["POST"])
def recognize_webcam():
    data = request.json
    if not data or "image" not in data:
        return jsonify({"error": "no image provided"}), 400
    # data["image"] is like "data:image/png;base64,...."
    header, b64 = data["image"].split(",", 1)
    img_bytes = base64.b64decode(b64)
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    result = recognize_frame(frame, str(ENC_PATH))
    return jsonify(result)


# Manage known faces
@app.route("/manage", methods=["GET"])
def manage_page():
    # list files in faces dir (grouped by person subfolders or files)
    persons = []
    for entry in sorted(FACES_DIR.iterdir()):
        if entry.is_dir():
            persons.append(entry.name)
        else:
            # if faces stored as files directly, show filename base
            persons.append(entry.stem)
    return render_template("manage.html", persons=persons)


@app.route("/add_face", methods=["POST"])
def add_face():
    if "image" not in request.files or "name" not in request.form:
        flash("Missing data")
        return redirect(url_for("manage_page"))
    file = request.files["image"]
    name = request.form["name"].strip()
    if name == "":
        flash("Provide a name")
        return redirect(url_for("manage_page"))
    filename = secure_filename(file.filename)
    save_path = UPLOADS_DIR / filename
    file.save(save_path)
    ok, msg = add_face_from_file(str(save_path), name, FACES_DIR, ENC_PATH)
    flash(msg)
    return redirect(url_for("manage_page"))


@app.route("/delete_face", methods=["POST"])
def delete_face_route():
    name = request.form.get("name")
    if not name:
        flash("No name provided")
        return redirect(url_for("manage_page"))
    ok, msg = delete_face(name, FACES_DIR, ENC_PATH)
    flash(msg)
    return redirect(url_for("manage_page"))


@app.route("/retrain", methods=["POST"])
def retrain():
    encode_all_faces(FACES_DIR, ENC_PATH)
    flash("Retrained encodings from faces/ directory.")
    return redirect(url_for("manage_page"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
