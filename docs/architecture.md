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
Latest in-memory events are shown in the browser
```

## Camera Pipeline Helpers

- `backend/app/services/camera_source.py`: opens, tests, releases, and reopens camera devices.
- `backend/app/services/camera_pipeline.py`: coordinates frame reads, face-analysis cadence, overlay drawing, reconnect handling, and streaming logs.
- `backend/app/services/event_log.py`: stores the latest in-memory motion and face events.
- `backend/app/services/mjpeg_streamer.py`: converts annotated frames into MJPEG response chunks.
- `backend/app/services/pipeline_stats.py`: keeps in-memory counters for `/stats`.
- `backend/app/services/camera_service.py`: compatibility wrapper for older imports.
- `backend/app/vision/motion_detection.py`: compares consecutive frames and reports basic motion signals.

## Pipeline Stats

`GET /stats` returns a protected JSON snapshot with:

- camera frame reads and streamed frames
- failed frame reads and reconnect count
- encoding failures
- face-analysis interval and analysis-frame count
- latest face count and labels
- motion activity, score, changed area, and event count
- latest in-memory motion and face events

Stats and events are local memory only and reset on backend restart.

## Performance Tuning

- `FACE_ANALYSIS_INTERVAL_FRAMES=1` keeps current behavior by analyzing every frame.
- Higher values reuse the latest annotations between analysis frames to reduce CPU usage.
- Increase the interval only after checking that label boxes still feel responsive enough.

## Privacy Defaults

- Known-face images stay local.
- `.gitignore` excludes `backend/known_faces/*`.
- No database, cloud storage, or smart-home integration exists yet.

## Near-Term Architecture Goals

- Add smoothing and confidence history without adding a database.
- Add motion-event cooldowns and persistent local event history.
- Add a `/known-faces` debug endpoint.
- Add minimal tests for pure logic and route availability.
