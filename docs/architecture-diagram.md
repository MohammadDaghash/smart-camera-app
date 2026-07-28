# Architecture Diagram

This page gives a quick visual explanation of the Smart Camera App architecture.
GitHub renders these Mermaid diagrams directly in Markdown.

## System Overview

```mermaid
flowchart LR
    Browser["Browser UI"]
    Routes["FastAPI routes"]
    Services["Backend services"]
    Vision["Vision modules"]
    LocalData["Local SQLite + snapshots"]
    KnownFaces["Local known_faces images"]
    Experiments["Offline ML experiments"]

    Browser -->|HTML pages + MJPEG + JSON APIs| Routes
    Routes --> Services
    Services --> Vision
    Vision --> KnownFaces
    Services --> LocalData
    Experiments -->|threshold reports| Vision
```

Key idea:
The app is a local-first FastAPI monolith with clear internal boundaries. Routes
handle HTTP, services coordinate workflows, and vision modules handle ML/computer
vision logic.

## Live Camera Pipeline

```mermaid
flowchart TD
    Webcam["Laptop/Desktop webcam"]
    Source["camera_source.py<br/>open/read/reconnect"]
    Pipeline["camera_pipeline.py<br/>frame loop"]
    Motion["motion_detection.py<br/>motion score"]
    Face["face_recognition.py<br/>InsightFace detection + recognition"]
    Smooth["label_smoothing.py<br/>stable labels"]
    Metrics["pipeline_stats.py<br/>FPS + runtime metrics"]
    RecMetrics["recognition_metrics.py<br/>score history"]
    Events["event_log.py<br/>SQLite events"]
    Alerts["alert_rules.py<br/>local suspicious activity"]
    Snapshots["event_snapshots.py<br/>local JPEG snapshots"]
    Streamer["mjpeg_streamer.py<br/>JPEG chunks"]
    Browser["Browser /video"]

    Webcam --> Source
    Source --> Pipeline
    Pipeline --> Motion
    Pipeline --> Face
    Face --> Smooth
    Smooth --> Metrics
    Smooth --> RecMetrics
    Motion --> Metrics
    Motion --> Events
    Smooth --> Events
    Events --> Alerts
    Events --> Snapshots
    Pipeline --> Streamer
    Streamer --> Browser
```

Key idea:
Capture and streaming stay separate from heavier analysis. Face recognition can
run at a controlled cadence while the browser still receives an annotated stream.

## Operator Workflow

```mermaid
flowchart LR
    RawEvents["Raw events<br/>motion, face, alert, system"]
    Review["Activity review<br/>group nearby events"]
    Status["Review status<br/>new, reviewed, false_positive"]
    Dashboard["Live dashboard summary"]
    User["Operator"]

    RawEvents --> Review
    Review --> Status
    Review --> Dashboard
    Status --> Dashboard
    Dashboard --> User
    User -->|triage incidents| Status
```

Key idea:
The raw event log is not the final product experience. The dashboard and review
page turn low-level events into a workflow a person can actually use.

## Debug And ML Feedback Loop

```mermaid
flowchart TD
    KnownFaces["known_faces/<PersonName>/*.jpg"]
    RuntimeScores["Runtime recognition metrics"]
    Debug["Recognition debug page"]
    EvalDataset["experiments/recognition_eval/dataset"]
    EvalReports["CSV + PNG evaluation reports"]
    Threshold["FACE_MATCH_THRESHOLD"]

    KnownFaces --> Debug
    RuntimeScores --> Debug
    RuntimeScores --> Threshold
    EvalDataset --> EvalReports
    EvalReports --> Threshold
    Threshold --> Debug
```

Key idea:
There are two ML quality loops:

- Runtime loop: observe live scores and near-threshold behavior.
- Offline loop: evaluate labeled images before changing thresholds.

## Local Data Boundary

| Data | Location | Git status | Notes |
| --- | --- | --- | --- |
| Known-face photos | `backend/known_faces/` | Ignored | Personal photos stay local. |
| Events | `backend/local_data/events.db` | Ignored | Motion, face, alert, and system events. |
| Review status | `backend/local_data/review_status.db` | Ignored | `new`, `reviewed`, `false_positive`. |
| Recognition metrics | `backend/local_data/recognition_metrics.db` | Ignored | Labels, scores, timestamps; no images or embeddings. |
| Snapshots | `backend/local_data/snapshots/` | Ignored | Local JPEG event snapshots. |
| Experiment results | `experiments/recognition_eval/results/` | Ignored | Local evaluation reports. |

## Interview Summary

One concise way to explain the design:

Smart Camera App is a local-first camera pipeline. It captures frames, runs
motion and face analysis, records local events, converts low-level events into
reviewable incidents, exposes dashboard health metrics, and provides ML tooling
to tune recognition thresholds responsibly.
