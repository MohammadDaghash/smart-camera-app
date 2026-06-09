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

## Recommended Local Command

Use this command for the live camera app:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

`--reload` can be noisy while `venv` is inside `backend`, because file watchers may react to dependency files. Use reload only when needed:

```bash
uvicorn app.main:app --reload --reload-exclude 'venv/**'
```
