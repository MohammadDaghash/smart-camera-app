# Team Setup

This document defines how the team collaborates on the project. Product scope,
feature priorities, and long-term plans live in [spec.md](spec.md).

## Branch Workflow

- `main`: primary protected branch
- `feature/<feature-name>`: all development work

All changes should go through a pull request into `main`. Direct pushes to
`main` should be blocked in GitHub branch protection, and each pull request
should require at least one reviewer.

## Team Responsibilities

### Omar - Backend And Architecture

Owns backend architecture, system design, engineering standards, scalability,
and code review quality.

Main areas:

- Backend architecture and service boundaries
- Runtime reliability and performance
- API design and maintainability
- GitHub workflow and pull request review standards

### Mohammad - Computer Vision And Analytics

Owns machine learning, computer vision, recognition quality, statistical
thinking, and future behavior analysis.

Main areas:

- Face detection and recognition quality
- Confidence thresholds and evaluation metrics
- Recognition stability across frames
- Future motion, activity, and anomaly analysis

### Majd - Frontend And Product Experience

Owns frontend experience, dashboard design, usability, visual feedback, and
status presentation.

Main areas:

- Dashboard structure and user workflows
- Live-view presentation and real-time UI states
- Visual clarity for system status and recognition results
- Frontend quality across desktop and mobile

## Local Development Notes

Run the backend from the backend directory:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Windows activation:

```bash
venv\Scripts\activate
```

Open:

```text
http://localhost:8000
```

On macOS, make sure Terminal, VS Code, or Python has Camera permission enabled:

```text
System Settings -> Privacy & Security -> Camera
```

## Collaboration Rules

- Keep pull requests focused and reviewable.
- Request at least one teammate review before merging.
- Keep architecture and product decisions documented.
- Do not commit local known-face images or private biometric data.
- Update [spec.md](spec.md) when a feature goal, priority, or requirement changes.
