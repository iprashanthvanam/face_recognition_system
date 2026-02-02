# Integrated Face Recognition System

**Full Project Documentation & README**  
**Last updated:** July 2025  
**Author:** Prashanth  
**Project Type:** Computer Vision / Face Recognition Web Application  
**Location:** India  

---

## Project Overview

The **Integrated Face Recognition System** is a Flask-based web application that performs real-time and image-based face recognition using computer vision and deep learning techniques.

The application allows users to:
- Upload images to identify known faces
- Perform live face recognition using a webcam
- Add new people to the system dynamically
- Retrain face encodings without restarting the server
- Manage and delete existing known faces

This project demonstrates a **complete end-to-end face recognition pipeline**, combining backend processing, model persistence, and a clean web-based user interface.

---

## Key Features

- **Image Upload Recognition:** Detect and recognize faces from uploaded images
- **Webcam Recognition:** Real-time face recognition via webcam snapshots
- **Face Management:** Add, delete, and retrain known faces dynamically
- **Encodings Persistence:** Face encodings stored using pickle for fast reuse
- **Multi-Face Detection:** Supports multiple faces in a single image/frame
- **Distance Scoring:** Displays face distance confidence
- **Clean UI:** Responsive HTML + CSS interface
- **Production Ready:** Gunicorn + Render deployment support

---

## Tech Stack

| Layer | Technology | Purpose |
|-----|-----------|--------|
| **Backend** | Flask | Web framework |
| **Face Recognition** | face_recognition (dlib) | Face detection & encoding |
| **Computer Vision** | OpenCV | Image & webcam processing |
| **Image Handling** | Pillow (PIL) | Image decoding |
| **Frontend** | HTML, CSS, Jinja2 | User interface |
| **Model Storage** | Pickle (.pkl) | Face encodings persistence |
| **Server** | Gunicorn | Production WSGI server |
| **Deployment** | Render | Cloud deployment |

---

## Application Pages

### Home
- Navigation to upload, webcam, and management pages

### Upload & Recognize
- Upload an image
- Detect and recognize all faces
- Display names and distance scores

### Webcam Recognition
- Capture webcam snapshots every second
- Send frames to backend for recognition
- Display live recognition results

### Manage Faces
- Add new people with images
- Delete existing people
- Retrain encodings instantly

---

## Face Recognition Workflow

1. User uploads image / webcam frame
2. Face locations detected using `face_recognition`
3. Face encodings extracted
4. Encodings compared against stored encodings
5. Best match selected using distance threshold
6. Results returned to UI

---

## Installation & Setup (Local)

### 1️⃣ Prerequisites

- Python ≥ 3.11
- pip
- Webcam (for live recognition)

---

```bash
### 2️⃣ Clone Repository

git clone <your-repo-url>
cd face-recognition-system


### 3️⃣ Create Virtual Environment:
python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows

### 4️⃣ Install Dependencies:
pip install -r requirements.txt


### ⚠️ dlib-bin is used to avoid compilation issues.

### 5️⃣ Train Initial Face Encodings (Optional):
python train_faces.py

### 6️⃣ Run Development Server:
python app.py


### App runs at:
http://127.0.0.1:5000

### Adding New Faces:

Go to Manage Faces
Enter person name
Upload an image with one clear face
System automatically retrains encodings

✔ No restart required
✔ Encodings updated instantly

### Deleting Faces:

Delete individual people from Manage Faces
Encodings retrained automatically
Supported Inputs
JPG / JPEG
PNG

### Webcam snapshots:
Multiple faces per image

### Deployment (Render):
The app is configured for Render using Gunicorn.
services:
  - type: web
    name: face-recognition
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app


![Home Page](templates/Screenshot 2026-02-02 225013.png)

