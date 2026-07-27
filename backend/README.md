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
- `GET /review`: serves `frontend/review.html`
- `GET /diagnostics`: serves `frontend/diagnostics.html`
- `GET /settings`: serves `frontend/settings.html`
- `GET /recognition-debug`: serves `frontend/recognition-debug.html`
- `GET /recognition-metrics`: serves `frontend/recognition-metrics.html`
- `GET /health`: simple API health check
- `GET /camera-test`: checks whether OpenCV can open the webcam
- `GET /video`: MJPEG live video stream with face overlays
- `GET /stats`: current in-memory camera pipeline statistics and latest local events
- `GET /api/dashboard-summary`: protected operational summary for the live dashboard
- `GET /api/system-status`: protected health summary based on pipeline metrics
- `GET /api/diagnostics`: protected readable health checks and recommended actions
- `GET /api/settings`: protected read-only tuning settings summary
- `GET /known-faces`: protected debug summary of loaded known-face labels and counts
- `GET /api/recognition-debug`: protected recognition scores, thresholds, and label reasons
- `GET /api/recognition-metrics`: protected local recognition score history
- `GET /api/events`: local event history with `type`, `label`, `start_at`,
  `end_at`, and `limit` filters
- `GET /api/review`: grouped activity review items built from recent events,
  with `label`, `start_at`, `end_at`, and `limit` filters
- `PATCH /api/review/{review_id}/status`: saves a local review status:
  `new`, `reviewed`, or `false_positive`
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
- Keep experiment/test dependencies in `requirements-dev.txt`.
- Use the project virtual environment in `backend/venv`.
- Do not commit the virtual environment.
- Do not commit personal face images.
- The first InsightFace run may download model files into `~/.insightface`.

Install development and experiment dependencies with:

```bash
pip install -r requirements-dev.txt
```

## Camera Pipeline Notes

The camera pipeline is split into small helpers:

- `app/services/camera_source.py`: camera open, test, release, and reconnect logic.
- `app/services/camera_pipeline.py`: frame read loop, face-analysis cadence, overlay drawing, and stream logs.
- `app/services/alert_rules.py`: local suspicious-activity rule evaluation.
- `app/services/event_log.py`: SQLite-backed local motion and face events with cooldown support.
- `app/services/event_snapshots.py`: local JPEG snapshots for saved events.
- `app/services/activity_review.py`: groups nearby raw events into reviewable activity items.
- `app/services/dashboard_summary.py`: combines health, review, alert, and FPS data for the homepage.
- `app/services/review_status.py`: stores local review status decisions in SQLite.
- `app/services/mjpeg_streamer.py`: JPEG encoding and MJPEG chunk formatting.
- `app/services/pipeline_stats.py`: in-memory counters for camera reads, stream output, reconnects, and face analysis.
- `app/services/diagnostics.py`: readable health checks and recommended actions from pipeline metrics.
- `app/services/settings_summary.py`: read-only non-secret tuning settings for `/api/settings`.
- `app/services/status_events.py`: records local events when the overall system status changes.
- `app/services/recognition_debug.py`: builds the recognition debug API response from safe runtime metadata.
- `app/services/recognition_metrics.py`: stores bounded local recognition label and score observations.
- `app/services/system_status.py`: converts low-level pipeline metrics into `healthy`, `idle`, `degraded`, or `error`.
- `app/vision/label_smoothing.py`: stabilizes recognition labels across nearby face boxes and recent frames.
- `app/vision/motion_detection.py`: simple frame-to-frame motion detection.

The pipeline follows the same high-level idea used in mature camera systems:
capture frames continuously, but keep expensive analysis controllable.

Optional tuning:

```bash
FACE_ANALYSIS_INTERVAL_FRAMES=1
FACE_MATCH_THRESHOLD=0.45
FACE_LABEL_SMOOTHING_ENABLED=true
FACE_LABEL_SMOOTHING_HISTORY_SIZE=5
FACE_LABEL_SMOOTHING_MIN_VOTES=2
FACE_TRACK_IOU_THRESHOLD=0.2
FACE_TRACK_TTL_FRAMES=5
RECOGNITION_METRICS_MAX_OBSERVATIONS=1000
RECOGNITION_METRICS_SAMPLE_INTERVAL_SECONDS=1.0
```

`1` analyzes every frame. Higher values reuse the latest face annotations between
analysis frames, which can reduce CPU usage but may make boxes feel slightly less
responsive.

`FACE_MATCH_THRESHOLD` controls how strict known-face recognition is. Lower it
slightly if known people are often shown as `Anonymous`; raise it if the app
labels the wrong person as known. Valid values are clamped between `0.0` and
`1.0`. Restart the backend after changing `.env`.

Label smoothing compares nearby face boxes across analysis frames and uses recent
label votes before switching labels. This reduces one-frame flicker between a
known person and `Anonymous`.

Stats are available at:

```text
GET /stats
```

The stats include camera counters, face-analysis counters, basic motion
detection values such as `motion_active`, `last_motion_score`, and
`last_motion_area`, 5-second rolling FPS metrics, the latest 10 local events,
and the latest local alert.

Performance metrics follow the same observability idea used by mature camera
systems such as Frigate:

- `camera_fps`: frames read from the camera
- `stream_fps`: frames encoded and sent to the browser
- `analysis_fps`: frames processed by face recognition
- `motion_fps`: frames processed by motion detection
- `skipped_analysis_fps`: camera frames not processed by face recognition
- `uptime_seconds`: backend pipeline uptime since stats reset

`/api/system-status` summarizes those low-level values into a simple status:

- `healthy`: camera, stream, encoding, and analysis checks look good
- `idle`: no browser is currently consuming `/video`
- `degraded`: the pipeline is running, but warnings exist
- `error`: an active stream is not reading or streaming frames correctly

`/diagnostics` and `/api/diagnostics` add a readable layer on top of that status:
each health check includes what happened and the next local action to try.
When the status changes, the backend records a local `system` event so the
transition is visible in history.

`/settings` and `/api/settings` show current non-secret `.env` tuning values.
Editing settings still happens locally in `backend/.env`, followed by a backend
restart.

Pipeline stats reset when the backend restarts. Events are stored locally in
SQLite and survive backend restarts.

Local event database:

```text
backend/local_data/events.db
backend/local_data/review_status.db
backend/local_data/recognition_metrics.db
backend/local_data/snapshots/
```

`backend/local_data/` is gitignored. Do not commit local event history or
recognition score history, review status data, or snapshots.

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
REVIEW_EVENT_GAP_SECONDS=90
REVIEW_SOURCE_EVENT_LIMIT=200
```

Cooldowns prevent the same motion or face label from filling the event list too
quickly when detection flickers. Retention settings keep the local SQLite
database bounded. `EVENT_RETENTION_DAYS=0` disables age-based cleanup.
Snapshot settings control whether event images are saved and how large they are.
Alert settings control the local rule that creates an `alert` event when motion
and an anonymous face happen close together. The frontend can show local browser
notifications for new alerts while the dashboard is open. No external
notification service is used.

Review settings control how raw events become review items. If motion, face, and
alert events happen within `REVIEW_EVENT_GAP_SECONDS`, `/review` shows them as
one incident instead of disconnected rows. History and review pages can filter by
label and local time range for faster debugging. Review decisions are stored
locally as `new`, `reviewed`, or `false_positive`, so refreshes and backend
restarts keep the operator's triage state.

## Recommended Local Command

Use this command for the live camera app:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

`--reload` can be noisy while `venv` is inside `backend`, because file watchers may react to dependency files. Use reload only when needed:

```bash
uvicorn app.main:app --reload --reload-exclude 'venv/**'
```
