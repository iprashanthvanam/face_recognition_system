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
import face_recognition  # Added missing import

from face_recognition_utils import (
    encode_all_faces,
    recognize_image_file,
    recognize_frame,
    recognize_video_file,
    add_face_from_file,
    delete_face,
    load_encodings,
    ENC_PATH,
    FACES_DIR,
    UPLOADS_DIR
)

# Configuration
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
FACES_DIR = STATIC_DIR / "faces"
UPLOADS_DIR = STATIC_DIR / "uploads"
ENC_PATH = STATIC_DIR / "faces_encodings.pkl"

FACES_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
if not ENC_PATH.exists():
    encode_all_faces(FACES_DIR, ENC_PATH)

app = Flask(__name__)
app.secret_key = "replace-this-with-a-secret"  # Set a better secret for production
app.config["UPLOAD_FOLDER"] = str(UPLOADS_DIR)
app.config["FACES_FOLDER"] = str(FACES_DIR)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["GET", "POST"])
def upload_page():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        filename = secure_filename(file.filename)
        save_path = UPLOADS_DIR / filename
        file.save(save_path)
        
        video_exts = ('.mp4', '.avi', '.mov', '.mkv')
        if filename.lower().endswith(video_exts):
            source = "video"
            result = {"status": "pending", "message": "Processing faces in real-time..."}
        else:
            result = recognize_image_file(str(save_path), str(ENC_PATH))
            source = "upload"
            if result.get("processed_file"):
                filename = result["processed_file"]
        
        return render_template("result.html", result=result, filename=filename, source=source)
    return render_template("upload.html")

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/webcam")
def webcam_page():
    return render_template("webcam.html")

@app.route("/recognize_webcam", methods=["POST"])
def recognize_webcam():
    data = request.json
    if not data or "image" not in data:
        return jsonify({"error": "no image provided"}), 400
    header, b64 = data["image"].split(",", 1)
    img_bytes = base64.b64decode(b64)
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    encodings = load_encodings(ENC_PATH)
    face_locations = face_recognition.face_locations(frame)
    if not face_locations:
        return jsonify({"status": "no_faces", "message": "No faces detected."})
    
    face_encodings = face_recognition.face_encodings(frame, face_locations)
    flat_known = []
    flat_names = []
    for name, enc_list in encodings.items():
        for enc in enc_list:
            flat_known.append(enc)
            flat_names.append(name)
    
    results = []
    for i, (loc, enc) in enumerate(zip(face_locations, face_encodings)):
        matches = face_recognition.compare_faces(flat_known, enc, tolerance=0.5)
        face_distances = face_recognition.face_distance(flat_known, enc)
        if any(matches):
            best_idx = int(np.argmin(face_distances))
            name = flat_names[best_idx]
            distance = float(face_distances[best_idx])
        else:
            name = "Unknown"
            distance = None
        results.append({"face_index": i, "name": name, "distance": distance, "location": loc})
    
    return jsonify({"status": "ok", "results": results})

@app.route("/manage", methods=["GET"])
def manage_page():
    persons = []
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}
    for entry in sorted(FACES_DIR.iterdir()):
        if entry.is_dir():
            name = entry.name
            # Find the first image file in the person's folder
            face_image = None
            for f in sorted(entry.iterdir()):
                if f.suffix.lower() in image_extensions:
                    # Build a URL-friendly relative path: name/filename
                    face_image = f"{name}/{f.name}"
                    break
            persons.append({"name": name, "image": face_image})
        else:
            # Flat file (legacy): the file itself is the face image
            name = entry.stem
            face_image = entry.name  # direct file in faces/
            persons.append({"name": name, "image": face_image})
    return render_template("manage.html", persons=persons)

@app.route("/face_image/<path:filepath>")
def face_image(filepath):
    """Serve individual face images from the faces directory."""
    return send_from_directory(str(FACES_DIR), filepath)

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
