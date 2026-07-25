# Smart Camera App

Smart Camera App is a local smart-home camera MVP. The project currently streams a live webcam feed in the browser, detects faces, and labels known people using local InsightFace embeddings.

The long-term goal is to grow this into a smart camera system that can recognize known people, detect suspicious activity, analyze movement, and eventually integrate with smart-home devices. The current focus is keeping the foundation simple, private, and reliable.

## Current Features

- FastAPI backend
- Browser live video stream at `/video`
- Local webcam access through OpenCV
- Face detection and bounding boxes
- Basic known-face recognition with InsightFace
- Configurable face match threshold
- Recognition label smoothing across recent frames
- `Anonymous` label for unknown faces
- Basic motion detection stats
- Local known-face image folder
- Health endpoint at `/health`
- Camera access test endpoint at `/camera-test`
- Pipeline stats endpoint at `/stats`
- Pipeline performance FPS metrics
- Known-face debug endpoint at `/known-faces`
- Recognition debug page at `/recognition-debug`
- Basic frontend status panel for camera, faces, labels, and motion
- Persistent local camera events with simple cooldowns
- Event history page with type and limit filters
- Configurable local event cleanup and retention
- Local event snapshots shown in history
- Local suspicious-activity alert events
- Live dashboard alert indicator
- Local browser notifications for new suspicious alerts

## Team

| Team member | Background | Main responsibilities |
| --- | --- | --- |
| Omar | 5-year software engineer at Microsoft | Backend architecture, camera pipeline optimization, scalability, code review, GitHub workflow supervision |
| Mohammad | BSc Mathematics and Computer Science, MSc student in Data Analysis and Statistics | Face recognition, computer vision, smoothing, confidence thresholds, ML logic, future movement analysis |
| Majd | BSc Software Engineering, MSc student in Data Analysis and Statistics, full-stack focused | Frontend, dashboard UI, user experience, overlays, status indicators |

## Technologies

- Python
- FastAPI
- Uvicorn
- OpenCV
- InsightFace
- ONNX Runtime
- Pillow
- SQLite
- HTML/CSS frontend

## Project Structure

```text
smart-camera-app/
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── vision/
│   │   ├── models/
│   │   ├── utils/
│   │   └── main.py
│   ├── known_faces/
│   ├── tests/
│   ├── requirements.txt
│   └── README.md
├── frontend/
├── docs/
├── .gitignore
└── README.md
```

## Running Locally

From the project root:

```bash
cd backend
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

Useful backend routes:

```text
http://localhost:8000/login
http://localhost:8000/health
http://localhost:8000/camera-test
http://localhost:8000/video
http://localhost:8000/stats
http://localhost:8000/known-faces
http://localhost:8000/recognition-debug
http://localhost:8000/api/recognition-debug
http://localhost:8000/history
http://localhost:8000/api/events
http://localhost:8000/api/snapshots/<snapshot-filename>
```

Note: the first run may download InsightFace model files into `~/.insightface`. The local `backend/main.py` still exists as a compatibility entrypoint, but `uvicorn app.main:app` is the recommended command.

## Authentication

The app requires a login before serving the camera UI or streams. Authentication
uses a signed, HTTP-only session cookie (Starlette `SessionMiddleware`).

Configure credentials in `backend/.env` (gitignored). Copy the template:

```bash
cp backend/.env.example backend/.env
```

Windows:

```bash
copy backend\.env.example backend\.env
```

| Variable | Purpose | Default |
| --- | --- | --- |
| `AUTH_USERNAME` | Admin username | `admin` |
| `AUTH_PASSWORD` | Admin password | `admin` |
| `SESSION_SECRET` | Key used to sign session cookies | random per start |
| `SESSION_MAX_AGE_SECONDS` | Session lifetime in seconds | `86400` |
| `SESSION_HTTPS_ONLY` | Send the session cookie only over HTTPS (enable behind TLS) | `false` |
| `LOGIN_MAX_ATTEMPTS` | Failed logins (per client IP) before lockout | `5` |
| `LOGIN_ATTEMPT_WINDOW_SECONDS` | Window in which failures are counted | `300` |
| `LOGIN_LOCKOUT_SECONDS` | How long a client is locked out | `300` |

If `AUTH_USERNAME` / `AUTH_PASSWORD` are unset, the app falls back to `admin` /
`admin` and logs a warning at startup. Set real values before exposing the server on
a network. If `SESSION_SECRET` is unset, a random key is generated at startup and all
sessions reset on restart; set it for stable logins.

Auth routes:

```text
GET  /login     login page
POST /login     submit credentials
GET  /logout    clear the session
```

Protected routes (`/`, `/history`, `/video`, `/camera-test`, `/stats`,
`/known-faces`, `/recognition-debug`, `/api/recognition-debug`, `/api/events`,
`/api/snapshots/*`) redirect to `/login` when the user is not signed in.
`/health` stays public.

### Session hardening

- **Server-side sessions:** each login gets a server-tracked session id. Logout
  revokes it immediately, so a captured cookie stops working even before it expires.
  Sessions are held in memory, so a server restart logs everyone out (swap in a shared
  store such as Redis when running multiple processes).
- **Login lockout:** after `LOGIN_MAX_ATTEMPTS` failed logins from one client IP within
  `LOGIN_ATTEMPT_WINDOW_SECONDS`, that client is locked out for `LOGIN_LOCKOUT_SECONDS`.
- **Secure cookie:** set `SESSION_HTTPS_ONLY=true` once the server is behind TLS so the
  session cookie is never sent over plain HTTP.

Note: lockout is keyed on the direct client IP. Behind a reverse proxy you must forward
and trust the real client IP for it to be effective.


## Known Faces

Personal face photos are intentionally ignored by Git.

For local development, place known faces in:

```text
backend/known_faces/
```

Single-photo format is still supported:

```text
backend/known_faces/mohammad.jpg
backend/known_faces/omar.jpeg
```

Recommended multi-photo format:

```text
backend/known_faces/
  Mohammad/
    1.jpg
    2.jpg
    3.jpg
  Omar/
    1.jpg
    2.jpg
```

Folder names are used as the person labels. Every supported image file inside a
person folder is loaded as a separate reference embedding, and recognition uses
the best match score across all loaded embeddings.

After logging in, open this debug route to verify loaded labels and photo counts:

```text
http://localhost:8000/known-faces
```

## Git Workflow

Branch roles:

- `main`: primary protected branch
- `feature/*`: focused feature branches created from `main`

Example feature branches:

```text
feature/multi-photo-recognition
feature/frontend-dashboard
feature/backend-refactor
```

Basic workflow:

```bash
git checkout main
git pull origin main
git checkout -b feature/my-feature

# make changes
git add .
git commit -m "Describe the change"
git push -u origin feature/my-feature
```

Open a pull request from the feature branch into `main`. Each pull request should be reviewed before merge.

See [docs/git-workflow.md](docs/git-workflow.md) for the full workflow.

## Roadmap

See [docs/spec.md](docs/spec.md) for the living product spec and feature priorities.
See [docs/interview-readiness.md](docs/interview-readiness.md) for a concise
demo script and system-design explanation.

- Multi-photo recognition per person
- Fuller frontend dashboard and camera controls
- Better overlays for labels, confidence, and unknown faces
- Camera pipeline performance improvements
- Local browser alert notifications
- Suspicious activity alerts
- Local event history
- Optional smart-home device integrations

## Future AI And Security Goals

- Keep face recognition local by default
- Avoid committing personal biometric images
- Add clear thresholds before sending alerts
- Add audit logs for recognition and suspicious activity events
- Add privacy controls before any cloud or smart-home integration
- Basic session login is in place; expand to multi-user accounts and tokens when remote access becomes necessary

## Development Practices

- Work from feature branches, not directly on `main`
- Keep pull requests small and reviewable
- Do not commit `venv`, caches, `.env`, or personal face images
- Prefer local modules under `backend/app/` over growing a single large file
- Keep routes thin and move business logic into services or vision modules
- Add tests as logic becomes stable enough to protect
