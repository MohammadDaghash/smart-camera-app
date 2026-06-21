# Smart Camera App

Smart Camera App is a local smart-home camera MVP. The project currently streams a live webcam feed in the browser, detects faces, and labels known people using local InsightFace embeddings.

The long-term goal is to grow this into a smart camera system that can recognize known people, detect suspicious activity, analyze movement, and eventually integrate with smart-home devices. The current focus is keeping the foundation simple, private, and reliable.

## Current Features

- FastAPI backend
- Browser live video stream at `/video`
- Local webcam access through OpenCV
- Face detection and bounding boxes
- Basic known-face recognition with InsightFace
- `Anonymous` label for unknown faces
- Local known-face image folder
- Health endpoint at `/health`
- Camera access test endpoint at `/camera-test`

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

Protected routes (`/`, `/video`, `/camera-test`) redirect to `/login` when the user
is not signed in. `/health` stays public.


## Known Faces

Personal face photos are intentionally ignored by Git.

For local development, place known faces in:

```text
backend/known_faces/
```

Current simple format:

```text
backend/known_faces/mohammad.jpg
backend/known_faces/omar.jpeg
```

Future planned format:

```text
backend/known_faces/
  Mohammad/
    1.jpg
    2.jpg
  Omar/
    1.jpg
    2.jpg
```

## Git Workflow

Branch roles:

- `main`: stable production-ready versions
- `dev`: active development integration branch
- `feature/*`: focused feature branches created from `dev`

Example feature branches:

```text
feature/multi-photo-recognition
feature/frontend-dashboard
feature/backend-refactor
```

Basic workflow:

```bash
git checkout dev
git pull origin dev
git checkout -b feature/my-feature

# make changes
git add .
git commit -m "Describe the change"
git push -u origin feature/my-feature
```

Open a pull request from the feature branch into `dev`. After testing and review, merge `dev` into `main` for stable releases.

See [docs/git-workflow.md](docs/git-workflow.md) for the full workflow.

## Roadmap

- Multi-photo recognition per person
- Recognition smoothing across frames
- Confidence threshold tuning tools
- Frontend dashboard and camera status indicators
- Better overlays for labels, confidence, and unknown faces
- Camera pipeline performance improvements
- Movement detection
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
