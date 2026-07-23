# Architecture Notes

Smart Camera App is currently a local monolith with a clear internal backend layout.

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
Camera pipeline sends frames to the vision module
        |
        v
Frame is annotated
        |
        v
MJPEG streamer encodes the frame as JPEG
        |
        v
MJPEG stream is sent back to browser
```

## Camera Pipeline Helpers

- `backend/app/services/camera_source.py`: opens, tests, releases, and reopens camera devices.
- `backend/app/services/camera_pipeline.py`: coordinates frame reads, face annotation, reconnect handling, and streaming logs.
- `backend/app/services/mjpeg_streamer.py`: converts annotated frames into MJPEG response chunks.
- `backend/app/services/camera_service.py`: compatibility wrapper for older imports.

## Privacy Defaults

- Known-face images stay local.
- `.gitignore` excludes `backend/known_faces/*`.
- No database, cloud storage, or smart-home integration exists yet.

## Near-Term Architecture Goals

- Add smoothing and confidence history without adding a database.
- Add a `/known-faces` debug endpoint.
- Add minimal tests for pure logic and route availability.
