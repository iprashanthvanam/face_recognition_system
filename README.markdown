### Integrated Face Recognition System

### 🔗 Live Application:
https://iprashanthvanam.pythonanywhere.com/  



## Project Overview

The **Integrated Face Recognition System** is a complete web-based face recognition application built using **Flask** and the **face_recognition** library (powered by dlib).

It allows users to:
- Upload images and recognize known faces
- Perform real-time face recognition using webcam
- Add new people to the recognition database
- Delete existing people
- Instantly retrain face encodings without restarting the server

The project demonstrates a full end-to-end face recognition pipeline — from face detection and encoding, to persistent storage, real-time recognition, and a clean user interface.

---

## Key Features

- Image upload + multi-face recognition
- Webcam live recognition (frame-by-frame)
- Add new persons with face images
- Delete persons from database
- Instant retraining of face encodings
- Face distance confidence score
- Responsive modern UI
- Persistent face encodings (pickle file)
- Support for multiple faces per image/frame
- Error handling & user feedback

---

## Tech Stack

| Layer              | Technology              | Purpose                              |
|--------------------|-------------------------|--------------------------------------|
| Backend            | Flask                   | Web framework                        |
| Face Recognition   | face_recognition (dlib) | Face detection & 128D encoding       |
| Computer Vision    | OpenCV (cv2)            | Image & video frame processing       |
| Image Handling     | Pillow (PIL)            | Image loading & conversion           |
| Frontend           | HTML5, CSS3, Jinja2     | User interface & templating          |
| Data Persistence   | Pickle                  | Store & load face encodings          |
| Deployment         | PythonAnywhere          | Free Flask hosting                   |
| Development Server | Flask built-in          | Local development                    |

---



## Installation & Setup (Local)

### Prerequisites
- Python 3.8–3.11 (3.11 recommended)
- pip
- Webcam (for live recognition)



### Clone the Repository
Cloning repository...
```
git clone https://github.com/iprashanthvanam/face-recognition-system.git
cd face-recognition-system || exit
```

### Create & Activate Virtual Environment
Creating virtual environment...
```
python -m venv venv
```

Activating virtual environment...
- Windows:
```
venv\Scripts\activate
```
- Linux / macOS:
```
source venv/bin/activate
```

### Install Dependencies
Installing dependencies...
```
pip install --upgrade pip
pip install -r requirements.txt
```

### If installation fails:
- Install cmake + Visual C++ Build Tools (Windows)
- Or use precompiled dlib wheels

### Initial Training (Optional)
echo "Running initial face training (optional)..."
```
python train_faces.py
```

### Run the Application
Starting Flask application...
```
python app.py
```

Application running at:
```
http://127.0.0.1:5000
```

### How to Use

Add Known Faces
- Go to **Manage Faces**
- Enter person's name
- Upload a clear face image (JPG/PNG)
- Click **Add & Retrain**

### Recognize Faces
- **Upload Image**  
  → Go to **Upload & Recognize** → select image → see results

- **Live Webcam**  
  → Go to **Webcam** → allow camera access → real-time recognition starts

### Delete a Person
- Go to **Manage Faces**
- Click **Delete** next to the person

### Retrain Encodings
- After adding or deleting faces
- Click **Retrain Encodings** button

### Project Pages

- **Home**  
  Introduction and navigation to all features

- **Upload & Recognize**  
  Upload an image → detect & recognize multiple faces

- **Webcam**  
  Real-time face recognition using your camera

- **Manage Faces**  
  Add new people, delete existing ones, retrain encodings


### Deployment Steps:
- Create account on https://www.pythonanywhere.com
- Upload files via Git or Files tab
- Create new Web App → Flask → Python version
- Set source code path:
```
cd /home/yourusername/face-recognition-system
```

### WSGI Configuration:
```
import sys
path = '/home/yourusername/face-recognition-system'
if path not in sys.path:
  sys.path.append(path)
from app import app as application
```

### Install dependencies:
```
pip install --user -r requirements.txt
```

Reload the web app from dashboard
