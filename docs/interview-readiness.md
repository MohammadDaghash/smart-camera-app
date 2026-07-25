# Interview Readiness Guide

This guide explains the project in a way that is easy to present in interviews.

## One-Minute Project Summary

Smart Camera App is a local-first smart camera MVP. It streams a webcam feed,
detects faces, recognizes known people from local reference photos, records local
events, creates suspicious-activity alerts, and exposes debugging dashboards for
recognition and pipeline performance.

The important engineering idea is not only "camera works." The important idea is
that the app is built as a small camera pipeline:

```text
Camera frame
  -> motion detection
  -> face detection
  -> face recognition
  -> label smoothing
  -> event logging
  -> alert rules
  -> annotated MJPEG stream
  -> dashboard/debug pages
```

## Frigate-Inspired Decisions

Frigate is a mature open-source NVR system. We are not copying its full
architecture, but we are using its high-level ideas:

- Capture video first, then process only what is needed.
- Track separate FPS metrics instead of one vague health status.
- Keep heavier analysis controllable by cadence.
- Separate capture, processing, events, stats, and frontend views.

Example:

If the camera reads 30 frames per second but face analysis runs at 5 frames per
second, the app can still stream smoothly while keeping CPU usage lower.

## What To Demo

1. Start the backend:

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

2. Open the live dashboard:

```text
http://localhost:8000
```

Show:

- Live MJPEG webcam stream
- Face labels on the video
- Motion status
- Recent events
- Suspicious alert banner

3. Open known-face debug:

```text
http://localhost:8000/known-faces
```

Show:

- Which people are loaded
- How many reference images each person has
- How many embeddings were created

4. Open recognition debug:

```text
http://localhost:8000/recognition-debug
```

Show:

- Raw label
- Smoothed label
- Match score
- Match threshold
- Reason for the label
- Camera FPS
- Stream FPS
- Analysis FPS
- Motion FPS
- Skipped analysis FPS

## How To Explain The FPS Metrics

The app tracks 5-second rolling performance metrics.

Example:

```text
camera_fps = 20
stream_fps = 20
analysis_fps = 5
skipped_analysis_fps = 15
```

Meaning:

- The camera is reading 20 frames per second.
- The browser is receiving 20 frames per second.
- Face recognition runs on 5 frames per second.
- 15 frames per second are streamed without expensive face analysis.

This is useful because the app can stay responsive while controlling CPU usage.

## Key Technical Tradeoffs

### Local-first privacy

Known-face photos, face embeddings, events, and snapshots stay local.

Tradeoff:
Local-first is safer for privacy, but remote/mobile access needs more work later.

### SQLite event history

Events are stored in local SQLite instead of a server database.

Tradeoff:
SQLite is simple and reliable for one machine. A remote database only becomes
necessary when multiple machines or users need shared access.

### Browser notifications

Alerts use local browser notifications while the dashboard is open.

Tradeoff:
This avoids cloud push complexity, but notifications do not work if the browser
is closed.

### Label smoothing

Recognition labels use recent frame votes so one weak frame does not instantly
flip a known face to `Anonymous`.

Tradeoff:
Smoothing improves visual stability, but it can delay label changes by a frame
or two.

## Good Interview Talking Points

- The project started simple and grew incrementally.
- The backend is split into routes, services, and vision modules.
- Heavy work is kept inside the camera pipeline, not inside HTTP route handlers.
- Personal biometric data is gitignored and stored locally.
- Debug endpoints expose metadata, not embeddings or images.
- Tests cover pure logic, route protection, event logging, recognition debug, and
  pipeline metrics.
- Frigate influenced the pipeline and observability design, but this app remains
  a smaller MVP.

## Next High-Value Improvements

- Add a small CI workflow to run backend tests on GitHub.
- Add confidence history charts for recognition tuning.
- Add event search by label and time.
- Add a camera health badge on the live dashboard.
- Add a clear architecture diagram to the README.
