# Interview Readiness Guide

This guide explains the project in a way that is easy to present in interviews.

## One-Minute Project Summary

Smart Camera App is a local-first smart camera MVP. It streams a webcam feed,
detects faces, recognizes known people from local reference photos, records local
events, creates suspicious-activity alerts, and exposes debugging dashboards for
recognition, pipeline performance, and activity review.

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
  -> activity review grouping
  -> annotated MJPEG stream
  -> dashboard/debug pages
```

## Frigate-Inspired Decisions

Frigate is a mature open-source NVR system. We are not copying its full
architecture, but we are using its high-level ideas:

- Capture video first, then process only what is needed.
- Track separate FPS metrics instead of one vague health status.
- Convert low-level metrics into a simple system health status.
- Convert low-level events into reviewable activity items.
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
- Diagnostics summary with top recommended action
- System status changes in history

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
- System status: healthy, idle, degraded, or error

5. Open camera diagnostics:

```text
http://localhost:8000/diagnostics
```

Show:

- Health checks for each pipeline stage
- Recommended local actions
- Pipeline metrics in one place

6. Open camera settings:

```text
http://localhost:8000/settings
```

Show:

- Face-recognition thresholds
- Motion-detection thresholds
- Event and alert cooldowns
- Which values came from `.env` versus defaults

7. Open activity review:

```text
http://localhost:8000/review
```

Show:

- Nearby events grouped as one review item
- Severity: `alert`, `detection`, or `info`
- Labels involved in the activity
- Source events that explain why the review item exists

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

## How To Explain System Status

The app turns low-level metrics into a simple status:

```text
healthy  -> stream is active and core checks look good
idle     -> no browser is currently consuming /video
degraded -> the pipeline works, but warnings exist
error    -> an active stream is not reading or streaming frames correctly
```

Example:

If `camera_fps = 10` but `stream_fps = 2`, the system becomes `degraded`
because the camera is producing frames faster than the browser stream is sending
them. That tells us where to debug first.

## How To Explain Diagnostics

The diagnostics page is the human-readable layer above `/stats`.
The live dashboard shows the top recommendation so the operator can see the
next action without opening the full diagnostics page.

Example:

If `/stats` says `consecutive_failed_reads = 3`, diagnostics shows the camera
read check as `degraded` and recommends checking camera access or reconnecting
the camera. This is useful in interviews because it shows that the system can
explain failures instead of only displaying raw numbers.

When the overall status changes, the app stores a local `system` event.

Example:

```text
System status changed from healthy to degraded
```

That makes operational problems visible in the same history as motion, face,
and alert events.

## How To Explain Settings

Settings are read-only in the browser for this MVP. The app exposes the current
non-secret tuning values so the team can debug behavior and discuss tradeoffs.

Example:

Increasing `FACE_ANALYSIS_INTERVAL_FRAMES` reduces CPU work because fewer frames
go through face recognition. The tradeoff is that labels update less often.

## How To Explain Activity Review

The event history is the raw log. Activity review is the human-friendly summary
above it.

Example raw events:

```text
10:00:01 motion detected
10:00:15 Anonymous 1 detected
10:00:16 suspicious activity alert
```

Instead of making the operator inspect three separate rows, `/review` groups them
into one item:

```text
Alert review: Anonymous 1 near activity
duration: 15s
source events: motion, face, alert
```

This is closer to how mature camera systems present activity: the product should
help the user decide what to review, not just dump logs.

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
- A file-length guard keeps tracked files under 1000 lines.
- GitHub Actions runs backend tests, frontend JavaScript checks, and file-length
  guardrails automatically.
- Frigate influenced the pipeline, observability, and review design, but this app
  remains a smaller MVP.

## Next High-Value Improvements

- Add confidence history charts for recognition tuning.
- Add event search by label and time.
- Add a camera health badge on the live dashboard.
- Add a clear architecture diagram to the README.
