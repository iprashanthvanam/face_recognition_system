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

# def recognize_image_file(image_path: str, enc_path: str, tolerance=0.5) -> dict:
#     encodings = load_encodings(Path(enc_path))
#     if not encodings:
#         return {"status": "no_encodings", "message": "No known faces. Add faces and retrain."}
#     image = face_recognition.load_image_file(image_path)
#     boxes = face_recognition.face_locations(image)
#     if not boxes:
#         return {"status": "no_faces", "message": "No faces detected in the image."}
#     face_encs = face_recognition.face_encodings(image, boxes)
#     results = []
#     names = list(encodings.keys())
#     known_encs = []
#     for n in names:
#         known_encs.append(encodings[n])
#     # for easier comparison, flatten
#     flat_known = []
#     flat_names = []
#     for i, name in enumerate(names):
#         for enc in known_encs[i]:
#             flat_known.append(enc)
#             flat_names.append(name)
#     for i, fe in enumerate(face_encs):
#         matches = face_recognition.compare_faces(flat_known, fe, tolerance=tolerance)
#         face_distances = face_recognition.face_distance(flat_known, fe)
#         best_match_idx = None
#         if any(matches):
#             best_match_idx = int(np.argmin(face_distances))
#             name = flat_names[best_match_idx]
#             results.append({"face_index": i, "name": name, "distance": float(face_distances[best_match_idx])})
#         else:
#             results.append({"face_index": i, "name": "Unknown", "distance": None})
#     return {"status": "ok", "results": results}

def recognize_image_file(image_path: str, enc_path: str, tolerance: float = 0.5) -> dict:
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)
    if not face_locations:
        return {"status": "no_faces", "message": "No faces detected in the image."}
    
    face_encodings = face_recognition.face_encodings(image, face_locations)
    encodings = load_encodings(Path(enc_path))
    flat_known = []
    flat_names = []
    for name, enc_list in encodings.items():
        for enc in enc_list:
            flat_known.append(enc)
            flat_names.append(name)
    
    results = []
    for i, (loc, enc) in enumerate(zip(face_locations, face_encodings)):
        matches = face_recognition.compare_faces(flat_known, enc, tolerance=tolerance)
        face_distances = face_recognition.face_distance(flat_known, enc)
        if any(matches):
            best_idx = int(np.argmin(face_distances))
            name = flat_names[best_idx]
            distance = float(face_distances[best_idx])
        else:
            name = "Unknown"
            distance = None
        results.append({"face_index": i, "name": name, "distance": distance, "location": loc})
    
    # Process image with boxes
    img = cv2.imread(image_path)
    for r in results:
        top, right, bottom, left = r["location"]
        color = (0, 255, 0) if r["name"] != "Unknown" else (0, 0, 255)  # Green for known, Red for unknown
        cv2.rectangle(img, (left, top), (right, bottom), color, 2)
        label = f"{r['name']} (Face #{r['face_index']})" if r["name"] != "Unknown" else f"Unknown (Face #{r['face_index']})"
        cv2.putText(img, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    output_path = Path(image_path).with_suffix('.processed.jpg')
    cv2.imwrite(str(output_path), img)
    
    return {"status": "ok", "results": results, "processed_file": str(output_path.name)}




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





# def recognize_video_file(video_path: str, enc_path: str, frame_skip: int = 30, tolerance: float = 0.5) -> dict:
#     """
#     Process a video file, recognize faces in skipped frames, and aggregate unique known faces with min distances.
#     """
#     encodings = load_encodings(Path(enc_path))
#     if not encodings:
#         return {"status": "no_encodings", "message": "No known faces. Add faces and retrain."}
    
#     cap = cv2.VideoCapture(video_path)
#     if not cap.isOpened():
#         return {"status": "error", "message": "Could not open video file."}
    
#     detected = {}  # name: min_distance
#     frame_num = 0
    
#     flat_known = []
#     flat_names = []
#     for name, enc_list in encodings.items():
#         for enc in enc_list:
#             flat_known.append(enc)
#             flat_names.append(name)
    
#     while cap.isOpened():
#         ret, frame = cap.read()
#         if not ret:
#             break
        
#         if frame_num % frame_skip == 0:
#             # Recognize on this frame
#             face_encs = face_recognition.face_encodings(frame, face_recognition.face_locations(frame))
#             if face_encs:
#                 for fe in face_encs:
#                     matches = face_recognition.compare_faces(flat_known, fe, tolerance=tolerance)
#                     face_distances = face_recognition.face_distance(flat_known, fe)
#                     if any(matches):
#                         best_idx = int(np.argmin(face_distances))
#                         name = flat_names[best_idx]
#                         dist = float(face_distances[best_idx])
#                         if name != "Unknown":  # Ignore unknowns
#                             if name not in detected or dist < detected[name]:
#                                 detected[name] = dist
        
#         frame_num += 1
    
#     cap.release()
    
#     if detected:
#         results = [{"name": name, "distance": dist} for name, dist in sorted(detected.items())]
#         return {"status": "ok", "results": results}
#     else:
#         return {"status": "no_faces", "message": "No known faces detected in the video."}





def recognize_video_file(video_path: str, enc_path: str, frame_skip: int = 30, tolerance: float = 0.5) -> dict:
    encodings = load_encodings(Path(enc_path))
    if not encodings:
        return {"status": "no_encodings", "message": "No known faces. Add faces and retrain."}
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"status": "error", "message": "Could not open video file."}
    
    detected = {}  # name: (min_distance, locations)
    frame_num = 0
    frame_with_faces = None
    
    flat_known = []
    flat_names = []
    for name, enc_list in encodings.items():
        for enc in enc_list:
            flat_known.append(enc)
            flat_names.append(name)
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_num % frame_skip == 0:
            face_locations = face_recognition.face_locations(frame)
            if face_locations:
                frame_with_faces = frame.copy()
                face_encodings = face_recognition.face_encodings(frame, face_locations)
                for loc, enc in zip(face_locations, face_encodings):
                    matches = face_recognition.compare_faces(flat_known, enc, tolerance=tolerance)
                    face_distances = face_recognition.face_distance(flat_known, enc)
                    if any(matches):
                        best_idx = int(np.argmin(face_distances))
                        name = flat_names[best_idx]
                        dist = float(face_distances[best_idx])
                    else:
                        name = "Unknown"
                        dist = None
                    if name not in detected or (dist is not None and dist < detected[name][0]):
                        detected[name] = (dist, loc)
        
        frame_num += 1
    
    cap.release()
    
    if frame_with_faces is not None and detected:
        for name, (dist, loc) in detected.items():
            top, right, bottom, left = loc
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            cv2.rectangle(frame_with_faces, (left, top), (right, bottom), color, 2)
            label = f"{name} (Face #{list(detected.keys()).index(name)})" if name != "Unknown" else f"Unknown (Face #{list(detected.keys()).index(name)})"
            cv2.putText(frame_with_faces, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        output_path = Path(video_path).with_suffix('.processed.jpg')
        cv2.imwrite(str(output_path), frame_with_faces)
        results = [{"name": name, "distance": dist, "location": loc} for name, (dist, loc) in detected.items()]
        return {"status": "ok", "results": results, "processed_file": str(output_path.name)}
    else:
        return {"status": "no_faces", "message": "No known faces detected in the video."}