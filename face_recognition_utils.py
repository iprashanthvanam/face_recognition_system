import os
import pickle
from pathlib import Path
from typing import Tuple, Dict, List, Any

import cv2
import numpy as np
from PIL import Image
import face_recognition

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
FACES_DIR = STATIC_DIR / "faces"
UPLOADS_DIR = STATIC_DIR / "uploads"
ENC_PATH = STATIC_DIR / "faces_encodings.pkl"

FACES_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

def load_encodings(enc_path: Path) -> Dict[str, List[np.ndarray]]:
    if not enc_path.exists():
        return {}
    with open(enc_path, "rb") as f:
        data = pickle.load(f)
    return data

def save_encodings(encodings: Dict[str, List[np.ndarray]], enc_path: Path):
    with open(enc_path, "wb") as f:
        pickle.dump(encodings, f)

def encode_all_faces(faces_dir: Path, enc_path: Path) -> Tuple[int, int]:
    """
    Walk faces_dir; expect structure:
    faces/<person_name>/*.jpg
    or faces/person_name_filename.jpg (single-level)
    Returns (num_people, total_encodings)
    """
    encodings = {}
    total = 0
    people = 0
    for child in faces_dir.iterdir():
        if child.is_dir():
            name = child.name
            person_imgs = list(child.glob("*"))
            enc_list = []
            for img_path in person_imgs:
                try:
                    image = face_recognition.load_image_file(str(img_path))
                    boxes = face_recognition.face_locations(image)
                    if not boxes:
                        continue
                    enc = face_recognition.face_encodings(image, boxes)[0]
                    enc_list.append(enc)
                    total += 1
                except Exception:
                    continue
            if enc_list:
                encodings[name] = enc_list
                people += 1
        else:
            # single image files directly under faces/
            if child.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                name = child.stem
                try:
                    image = face_recognition.load_image_file(str(child))
                    boxes = face_recognition.face_locations(image)
                    if not boxes:
                        continue
                    enc = face_recognition.face_encodings(image, boxes)[0]
                    encodings[name] = [enc]
                    total += 1
                    people += 1
                except Exception:
                    continue
    save_encodings(encodings, enc_path)
    return people, total

def recognize_image_file(image_path: str, enc_path: str, tolerance=0.5) -> dict:
    encodings = load_encodings(Path(enc_path))
    if not encodings:
        return {"status": "no_encodings", "message": "No known faces. Add faces and retrain."}
    image = face_recognition.load_image_file(image_path)
    boxes = face_recognition.face_locations(image)
    if not boxes:
        return {"status": "no_faces", "message": "No faces detected in the image."}
    face_encs = face_recognition.face_encodings(image, boxes)
    results = []
    names = list(encodings.keys())
    known_encs = []
    for n in names:
        known_encs.append(encodings[n])
    # for easier comparison, flatten
    flat_known = []
    flat_names = []
    for i, name in enumerate(names):
        for enc in known_encs[i]:
            flat_known.append(enc)
            flat_names.append(name)
    for i, fe in enumerate(face_encs):
        matches = face_recognition.compare_faces(flat_known, fe, tolerance=tolerance)
        face_distances = face_recognition.face_distance(flat_known, fe)
        best_match_idx = None
        if any(matches):
            best_match_idx = int(np.argmin(face_distances))
            name = flat_names[best_match_idx]
            results.append({"face_index": i, "name": name, "distance": float(face_distances[best_match_idx])})
        else:
            results.append({"face_index": i, "name": "Unknown", "distance": None})
    return {"status": "ok", "results": results}

def recognize_frame(frame_bgr, enc_path: str, tolerance=0.5) -> dict:
    """
    frame_bgr: OpenCV BGR image (numpy array)
    """
    encodings = load_encodings(Path(enc_path))
    if not encodings:
        return {"status": "no_encodings", "message": "No known faces. Add faces and retrain."}
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    boxes = face_recognition.face_locations(rgb)
    if not boxes:
        return {"status": "no_faces", "message": "No faces detected."}
    face_encs = face_recognition.face_encodings(rgb, boxes)
    results = []
    names = list(encodings.keys())
    known_encs = []
    for n in names:
        known_encs.append(encodings[n])
    flat_known = []
    flat_names = []
    for i, name in enumerate(names):
        for enc in known_encs[i]:
            flat_known.append(enc)
            flat_names.append(name)
    for i, fe in enumerate(face_encs):
        matches = face_recognition.compare_faces(flat_known, fe, tolerance=tolerance)
        face_distances = face_recognition.face_distance(flat_known, fe)
        if any(matches):
            best_match_idx = int(np.argmin(face_distances))
            name = flat_names[best_match_idx]
            results.append({"face_index": i, "name": name, "distance": float(face_distances[best_match_idx])})
        else:
            results.append({"face_index": i, "name": "Unknown", "distance": None})
    return {"status": "ok", "results": results}


def add_face_from_file(image_path: str, name: str, faces_dir: Path, enc_path: Path) -> Tuple[bool, str]:
    """
    Adds the given image to faces/<name>/ and retrains encodings for that person (and saves enc file).
    """
    name_safe = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip()
    person_dir = faces_dir / name_safe
    person_dir.mkdir(parents=True, exist_ok=True)
    # copy file into person_dir
    try:
        im = face_recognition.load_image_file(image_path)
        boxes = face_recognition.face_locations(im)
        if not boxes:
            return False, "No face detected in provided image. Try another image."
        # save a resized copy to person's dir
        ext = Path(image_path).suffix or ".jpg"
        target = person_dir / (name_safe + "_" + Path(image_path).stem + ext)
        # use OpenCV to read & save to ensure consistent encoding
        import cv2
        frame = cv2.imread(image_path)
        if frame is None:
            # fallback: use PIL
            from PIL import Image
            pil = Image.open(image_path).convert("RGB")
            pil.save(str(target))
        else:
            cv2.imwrite(str(target), frame)
        # retrain all encodings (simple approach)
        encode_all_faces(faces_dir, enc_path)
        return True, f"Added face for '{name_safe}' and retrained encodings."
    except Exception as e:
        return False, f"Error adding face: {e}"

def delete_face(name: str, faces_dir: Path, enc_path: Path) -> Tuple[bool, str]:
    """
    Delete a person's folder (or files named with that person) and retrain encodings.
    """
    name_safe = name
    person_dir = faces_dir / name_safe
    removed = False
    try:
        if person_dir.exists() and person_dir.is_dir():
            # remove directory
            import shutil
            shutil.rmtree(person_dir)
            removed = True
        else:
            # try to delete files with stem matching name
            for f in faces_dir.glob(f"{name_safe}*"):
                if f.is_file():
                    f.unlink()
                    removed = True
        if removed:
            encode_all_faces(faces_dir, enc_path)
            return True, f"Deleted data for '{name_safe}' and retrained encodings."
        else:
            return False, f"No data found for '{name_safe}'."
    except Exception as e:
        return False, f"Error deleting face data: {e}"
