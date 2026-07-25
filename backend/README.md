# Backend

The backend is a FastAPI application that serves the frontend, opens the local webcam with OpenCV, streams MJPEG video, and annotates frames with InsightFace face-recognition labels.

## Run

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Routes

- `GET /`: serves `frontend/index.html`
- `GET /health`: simple API health check
- `GET /camera-test`: checks whether OpenCV can open the webcam
- `GET /video`: MJPEG live video stream with face overlays
- `GET /stats`: current in-memory camera pipeline statistics

## Folder Guide

```text
app/main.py
```

Creates the FastAPI app and registers routers.

```text
app/routes/
```

HTTP route definitions. Keep these thin.

```text
app/services/
```

Application services such as camera open/read/reconnect and stream generation.

```text
app/vision/
```

Computer-vision and ML logic, including InsightFace loading, known-face embeddings, detection, recognition, and drawing overlays.

```text
app/models/
```

Reserved for future Pydantic schemas or internal data models.

```text
app/utils/
```

Shared utilities such as logging.

```text
known_faces/
```

Local-only known-face images. Personal images are ignored by Git.

```text
tests/
```

Backend test folder. Add tests as modules become more stable.

## Dependency Notes

- Keep dependencies in `requirements.txt`.
- Use the project virtual environment in `backend/venv`.
- Do not commit the virtual environment.
- Do not commit personal face images.
- The first InsightFace run may download model files into `~/.insightface`.

## Camera Pipeline Notes

The camera pipeline is split into small helpers:

- `app/services/camera_source.py`: camera open, test, release, and reconnect logic.
- `app/services/camera_pipeline.py`: frame read loop, face-analysis cadence, overlay drawing, and stream logs.
- `app/services/mjpeg_streamer.py`: JPEG encoding and MJPEG chunk formatting.
- `app/services/pipeline_stats.py`: in-memory counters for camera reads, stream output, reconnects, and face analysis.

The pipeline follows the same high-level idea used in mature camera systems:
capture frames continuously, but keep expensive analysis controllable.

Optional tuning:

```bash
FACE_ANALYSIS_INTERVAL_FRAMES=1
```

`1` analyzes every frame. Higher values reuse the latest face annotations between
analysis frames, which can reduce CPU usage but may make boxes feel slightly less
responsive.

Stats are available at:

```text
GET /stats
```

The stats reset when the backend restarts. This is intentional for the local MVP;
we will add persistent event history later when the event model is clear.

## Recommended Local Command

Use this command for the live camera app:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

`--reload` can be noisy while `venv` is inside `backend`, because file watchers may react to dependency files. Use reload only when needed:

```bash
uvicorn app.main:app --reload --reload-exclude 'venv/**'
```
