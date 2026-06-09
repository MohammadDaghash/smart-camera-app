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
Camera service opens webcam and reads frames
        |
        v
Vision module detects and recognizes faces
        |
        v
Frame is annotated and encoded as JPEG
        |
        v
MJPEG stream is sent back to browser
```

## Privacy Defaults

- Known-face images stay local.
- `.gitignore` excludes `backend/known_faces/*`.
- No database, cloud storage, authentication, or smart-home integration exists yet.

## Near-Term Architecture Goals

- Add multi-photo known-face folders.
- Add smoothing and confidence history without adding a database.
- Add a `/known-faces` debug endpoint.
- Add minimal tests for pure logic and route availability.
