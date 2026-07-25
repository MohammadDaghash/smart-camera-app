# Architecture Notes

Smart Camera App is currently a local monolith with a clear internal backend layout.

The camera path is inspired by Frigate's high-level pipeline approach: acquire
frames first, then apply heavier analysis at a controlled cadence before sending
output to the viewer. We are not copying Frigate's full NVR architecture.

## Backend Boundaries

- Routes handle HTTP requests and responses.
- Services handle application workflows like camera opening and frame streaming.
- Vision modules handle ML and computer-vision logic.
- Utils hold small shared helpers.

## Current Data Flow

```text
Browser <img src="/video">
        |
        v
FastAPI /video route
        |
        v
Camera source opens webcam and reads frames
        |
        v
Camera pipeline runs motion detection and face analysis
        |
        v
Local alert rules evaluate accepted events
        |
        v
Frame is annotated
        |
        v
MJPEG streamer encodes the frame as JPEG
        |
        v
MJPEG stream is sent back to browser
        |
        v
Pipeline stats can be inspected at /stats
        |
        v
Latest local SQLite events are shown in the browser
        |
        v
Event history can be viewed at /history
        |
        v
Event snapshots can be served through /api/snapshots/{filename}
```

## Camera Pipeline Helpers

- `backend/app/services/camera_source.py`: opens, tests, releases, and reopens camera devices.
- `backend/app/services/camera_pipeline.py`: coordinates frame reads, face-analysis cadence, overlay drawing, reconnect handling, and streaming logs.
- `backend/app/services/alert_rules.py`: creates local alert events when simple suspicious-activity rules match.
- `backend/app/services/event_log.py`: stores local SQLite motion and face events, with cooldowns to avoid repeated event spam.
- `backend/app/services/event_snapshots.py`: stores local JPEG snapshots for accepted events.
- `backend/app/services/mjpeg_streamer.py`: converts annotated frames into MJPEG response chunks.
- `backend/app/services/pipeline_stats.py`: keeps in-memory counters for `/stats`.
- `backend/app/services/camera_service.py`: compatibility wrapper for older imports.
- `backend/app/routes/known_faces.py`: exposes a protected known-face loading summary without embeddings or images.
- `backend/app/vision/motion_detection.py`: compares consecutive frames and reports basic motion signals.

## Pipeline Stats

`GET /stats` returns a protected JSON snapshot with:

- camera frame reads and streamed frames
- failed frame reads and reconnect count
- encoding failures
- face-analysis interval and analysis-frame count
- latest face count and labels
- motion activity, score, changed area, and event count
- latest local motion and face events
- filterable local event history through `/api/events`
- protected local event snapshots through `/api/snapshots/{filename}`
- local alert events when motion and an anonymous face happen close together
- latest alert for the live dashboard indicator

Pipeline stats are local memory only and reset on backend restart. Events persist
in `backend/local_data/events.db`, which is gitignored. Event cleanup is controlled
by `EVENT_MAX_EVENTS` and `EVENT_RETENTION_DAYS`.

Event snapshots are stored in `backend/local_data/snapshots/`, which is also
gitignored.

## Performance Tuning

- `FACE_ANALYSIS_INTERVAL_FRAMES=1` keeps current behavior by analyzing every frame.
- Higher values reuse the latest annotations between analysis frames to reduce CPU usage.
- Increase the interval only after checking that label boxes still feel responsive enough.

## Privacy Defaults

- Known-face images stay local.
- `.gitignore` excludes `backend/known_faces/*`.
- Local events and snapshots stay under `backend/local_data/`.
- Browser notifications are local to the open dashboard session.
- No external notification service, cloud storage, or smart-home integration exists yet.

## Near-Term Architecture Goals

- Add smoothing and confidence history without adding cloud services.
- Add notification preferences after local browser notifications are stable.
- Add minimal tests for pure logic and route availability.
