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
- `GET /history`: serves `frontend/events.html`
- `GET /recognition-debug`: serves `frontend/recognition-debug.html`
- `GET /health`: simple API health check
- `GET /camera-test`: checks whether OpenCV can open the webcam
- `GET /video`: MJPEG live video stream with face overlays
- `GET /stats`: current in-memory camera pipeline statistics and latest local events
- `GET /known-faces`: protected debug summary of loaded known-face labels and counts
- `GET /api/recognition-debug`: protected recognition scores, thresholds, and label reasons
- `GET /api/events`: local event history with `type` and `limit` filters
- `GET /api/snapshots/{filename}`: protected local event snapshot image

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

Computer-vision and ML logic, including InsightFace loading, known-face embeddings, detection, recognition, motion detection, and drawing overlays.

`GET /known-faces` exposes a safe summary for debugging known-face loading. It
returns labels, source image counts, and loaded embedding counts. It does not
return embeddings, image files, or snapshots.

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
- `app/services/alert_rules.py`: local suspicious-activity rule evaluation.
- `app/services/event_log.py`: SQLite-backed local motion and face events with cooldown support.
- `app/services/event_snapshots.py`: local JPEG snapshots for saved events.
- `app/services/mjpeg_streamer.py`: JPEG encoding and MJPEG chunk formatting.
- `app/services/pipeline_stats.py`: in-memory counters for camera reads, stream output, reconnects, and face analysis.
- `app/services/recognition_debug.py`: builds the recognition debug API response from safe runtime metadata.
- `app/vision/label_smoothing.py`: stabilizes recognition labels across nearby face boxes and recent frames.
- `app/vision/motion_detection.py`: simple frame-to-frame motion detection.

The pipeline follows the same high-level idea used in mature camera systems:
capture frames continuously, but keep expensive analysis controllable.

Optional tuning:

```bash
FACE_ANALYSIS_INTERVAL_FRAMES=1
FACE_LABEL_SMOOTHING_ENABLED=true
FACE_LABEL_SMOOTHING_HISTORY_SIZE=5
FACE_LABEL_SMOOTHING_MIN_VOTES=2
FACE_TRACK_IOU_THRESHOLD=0.2
FACE_TRACK_TTL_FRAMES=5
```

`1` analyzes every frame. Higher values reuse the latest face annotations between
analysis frames, which can reduce CPU usage but may make boxes feel slightly less
responsive.

Label smoothing compares nearby face boxes across analysis frames and uses recent
label votes before switching labels. This reduces one-frame flicker between a
known person and `Anonymous`.

Stats are available at:

```text
GET /stats
```

The stats include camera counters, face-analysis counters, basic motion
detection values such as `motion_active`, `last_motion_score`, and
`last_motion_area`, the latest 10 local events, and the latest local alert.

Pipeline stats reset when the backend restarts. Events are stored locally in
SQLite and survive backend restarts.

Local event database:

```text
backend/local_data/events.db
backend/local_data/snapshots/
```

`backend/local_data/` is gitignored. Do not commit local event history or
snapshots.

Optional motion tuning:

```bash
MOTION_DETECTION_ENABLED=true
MOTION_MIN_AREA=500
MOTION_SCORE_THRESHOLD=0.02
```

Lower values make motion detection more sensitive. Higher values ignore more
small movement and camera noise.

Optional event tuning:

```bash
EVENT_MOTION_COOLDOWN_SECONDS=10
EVENT_FACE_COOLDOWN_SECONDS=20
EVENT_MAX_EVENTS=1000
EVENT_RETENTION_DAYS=30
EVENT_SNAPSHOTS_ENABLED=true
EVENT_SNAPSHOT_MAX_WIDTH=640
EVENT_SNAPSHOT_JPEG_QUALITY=85
ALERTS_ENABLED=true
ALERT_ANONYMOUS_MOTION_WINDOW_SECONDS=30
ALERT_COOLDOWN_SECONDS=60
```

Cooldowns prevent the same motion or face label from filling the event list too
quickly when detection flickers. Retention settings keep the local SQLite
database bounded. `EVENT_RETENTION_DAYS=0` disables age-based cleanup.
Snapshot settings control whether event images are saved and how large they are.
Alert settings control the local rule that creates an `alert` event when motion
and an anonymous face happen close together. The frontend can show local browser
notifications for new alerts while the dashboard is open. No external
notification service is used.

## Recommended Local Command

Use this command for the live camera app:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

`--reload` can be noisy while `venv` is inside `backend`, because file watchers may react to dependency files. Use reload only when needed:

```bash
uvicorn app.main:app --reload --reload-exclude 'venv/**'
```
