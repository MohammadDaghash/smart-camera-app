# Interview Demo Script

Use this script to demo the project clearly in 8-12 minutes.

## Pre-Demo Checklist

Run from the project root:

```bash
git checkout dev
git pull origin dev
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

If macOS blocks the camera, allow camera access for Terminal, VS Code, or Python:

```text
System Settings -> Privacy & Security -> Camera
```

## One-Minute Pitch

Smart Camera App is a local-first smart camera MVP. It streams the webcam,
detects faces, recognizes known people from local reference photos, records
local events, groups activity into reviewable incidents, and exposes health and
ML debugging dashboards.

The engineering focus is the pipeline:

```text
camera frame -> motion -> face recognition -> smoothing -> events -> alerts
             -> review workflow -> metrics/debug pages -> MJPEG stream
```

## Demo Flow

### 1. Live Dashboard

Open:

```text
http://127.0.0.1:8000
```

Show:

- Live webcam feed
- System status
- Face labels
- Motion status
- Latest alert
- New review count
- Camera, stream, and analysis FPS
- Top recommended action

What to say:

The dashboard is the operator view. It does not force the user to inspect raw
logs. It summarizes health, alerts, review state, and performance in one place.

### 2. Recognition Debug

Open:

```text
http://127.0.0.1:8000/recognition-debug
```

Show:

- Current label
- Raw label
- Score
- Raw score
- Match threshold
- Reason for the displayed label
- Known-face loading summary

What to say:

Recognition is not treated as magic. The app exposes the score, threshold, raw
label, and smoothed label so we can debug why a decision happened.

### 3. Recognition Metrics

Open:

```text
http://127.0.0.1:8000/recognition-metrics
```

Show:

- Score history chart
- Red threshold line
- Per-label average/min/max scores
- Near-threshold count
- Latest observations

What to say:

This is the runtime ML monitoring view. If scores often sit near the threshold,
we know the model is uncertain and should tune reference photos or thresholds.
The app stores labels and scores only, not face photos or embeddings.

### 4. Event History

Open:

```text
http://127.0.0.1:8000/history
```

Show:

- Motion events
- Face events
- Alert events
- System events
- Label/time filters
- Local snapshots when available

What to say:

The event log is the raw timeline. It is stored locally in SQLite and bounded by
retention settings.

### 5. Activity Review

Open:

```text
http://127.0.0.1:8000/review
```

Show:

- Grouped incidents
- Severity: `alert`, `detection`, `info`
- Source events inside each review item
- Status buttons: `reviewed`, `false_positive`, reset
- Status filter

What to say:

Review is the product workflow above raw events. Instead of three disconnected
rows like motion, face, alert, the app groups nearby events into one item the
operator can review.

### 6. Diagnostics

Open:

```text
http://127.0.0.1:8000/diagnostics
```

Show:

- Pipeline checks
- Camera read health
- Stream output health
- Encoding health
- Face-analysis health
- Recommended next action

What to say:

The app can explain failures. If frames are read but not streamed, that points
to a different problem than camera permission failure.

### 7. Settings

Open:

```text
http://127.0.0.1:8000/settings
```

Show:

- `FACE_MATCH_THRESHOLD`
- `FACE_ANALYSIS_INTERVAL_FRAMES`
- Smoothing settings
- Motion settings
- Review/event settings
- Recognition metrics settings

What to say:

Settings are read-only in the UI for this MVP. Real changes happen in
`backend/.env`, followed by a backend restart.

## Technical Questions To Expect

### Why local-first?

Because this project handles camera and face data. For the MVP, known faces,
events, metrics, snapshots, and review status stay on the laptop.

### Why SQLite?

SQLite is enough for one local camera process. A remote database becomes useful
only when multiple users, multiple cameras, or remote access are required.

### Why not train a model yet?

The current system uses pretrained InsightFace embeddings. The ML work right now
is thresholding, evaluation, smoothing, and confidence monitoring. Training or
fine-tuning comes later when we have a real labeled dataset and a reason to beat
the pretrained baseline.

### What came from Frigate?

The high-level ideas:

- Capture first, analyze at controlled cadence.
- Track separate FPS and health metrics.
- Turn low-level events into reviewable activity.
- Keep camera, analysis, events, stats, and UI concerns separate.

The code is our own smaller MVP, not a copy of Frigate.

### What makes this interview-ready?

- Working local camera pipeline
- Real-time stream
- Face recognition and smoothing
- Local event history
- Review workflow
- Saved triage status
- Diagnostics and health checks
- Recognition confidence metrics
- Offline evaluation toolkit
- Tests and GitHub Actions
- Clear privacy boundary

## Fallback If Camera Fails

Open:

```text
http://127.0.0.1:8000/camera-test
http://127.0.0.1:8000/diagnostics
```

Explain:

Camera access can fail because of OS permissions or another app using the
webcam. The app exposes `/camera-test` and diagnostics so this is debuggable.

## Validation Commands

Run backend tests:

```bash
cd backend
source venv/bin/activate
PYTHONPATH=. python -m pytest -q
```

Check recent GitHub Actions:

```bash
gh run list --repo MohammadDaghash/smart-camera-app --branch dev --limit 5
```
