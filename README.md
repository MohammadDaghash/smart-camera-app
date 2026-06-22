# Smart Camera App

Local-first computer-vision security app for real-time monitoring and privacy-conscious face recognition.

This team project streams a local webcam feed through a FastAPI backend, detects faces with InsightFace, labels known people, and keeps unknown people as local anonymous identities. The long-term product direction is an AI-powered smart home/security platform with local recognition, event alerts, and privacy-first identity handling.

## What It Does

- Streams live webcam video in the browser through an MJPEG endpoint.
- Detects faces on each frame and draws bounding boxes/labels.
- Matches known faces with local InsightFace embeddings.
- Creates stable anonymous identities for unknown faces and stores embeddings locally.
- Lets users promote anonymous identities into known identities from the browser UI.
- Keeps personal face images and identity embeddings out of Git.

## Key Features

- FastAPI backend with thin route modules
- OpenCV webcam capture and reconnect handling
- InsightFace face detection and recognition
- ONNX Runtime CPU inference
- Known/unknown identity matching with configurable thresholds
- Local identity store for anonymous identity memory
- `/identities` API and browser UI for identity promotion
- `/health`, `/camera-test`, and `/video` endpoints
- Simple HTML/CSS live-view frontend

## Team / My Contribution

This is a collaborative team project.

- Omar: backend architecture, camera pipeline optimization, scalability, code review, GitHub workflow supervision
- Mohammad: face recognition, computer vision logic, embedding matching, thresholds, ML behavior, future movement-analysis direction
- Majd: frontend/dashboard experience, overlays, status indicators, user experience

## Tech Stack

- Python
- FastAPI
- Uvicorn
- OpenCV
- InsightFace
- ONNX Runtime
- NumPy
- Pillow
- HTML/CSS/JavaScript

## Architecture / How It Works

```text
Browser <img src="/video">
        |
        v
FastAPI route
        |
        v
Camera service opens local webcam and reads frames
        |
        v
Vision module detects faces and creates embeddings
        |
        v
Known-face matcher or local anonymous identity store
        |
        v
Annotated JPEG frames streamed back to the browser
```

Important modules:

- `backend/app/main.py` registers route modules.
- `backend/app/routes/camera.py` exposes `/camera-test` and `/video`.
- `backend/app/routes/identities.py` exposes local identity listing and promotion.
- `backend/app/services/camera_service.py` handles webcam opening, frame streaming, and reconnect behavior.
- `backend/app/vision/face_recognition.py` loads InsightFace, extracts embeddings, matches known faces, and annotates frames.
- `backend/app/services/identity_store.py` stores anonymous/known identity embeddings locally.

## Screenshots

Screenshots are not committed yet. Recommended captures:

- Live webcam view with face overlay
- Anonymous identity list
- Identity promotion form
- Camera health/test response

## Setup

From the project root:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://localhost:8000
```

Useful routes:

```text
GET /health
GET /camera-test
GET /video
GET /identities
POST /identities/{identity_id}/promote
```

The first InsightFace run may download model files into `~/.insightface`.

## Privacy Defaults

- Known-face images stay local in `backend/known_faces/`.
- Local identity embeddings stay in `backend/local_data/`.
- `.gitignore` excludes personal face photos and local embedding data.
- No cloud storage, database, authentication, or smart-home integration is required for the current local-first workflow.

## Roadmap

- Multi-reference known-person profiles
- Recognition smoothing across frames
- Confidence threshold tuning tools
- Activity/movement analysis
- Local event history
- Suspicious activity alert rules
- Optional smart-home integrations after privacy rules are defined

## What This Demonstrates

- Computer-vision pipeline design with OpenCV and InsightFace
- Local ML inference with privacy-conscious storage
- Face-embedding matching and unknown identity memory
- FastAPI route/service/module separation
- Practical team collaboration around an AI product direction
