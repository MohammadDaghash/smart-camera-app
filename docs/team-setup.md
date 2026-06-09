# Smart Camera App - Team Setup

The Smart Camera App repository is ready:

https://github.com/MohammadDaghash/smart-camera-app

## Current Workflow

- `main` = stable production-ready version
- `dev` = active development branch
- `feature/*` = individual feature branches created from `dev`

Please do **not** work directly on `main`.

## First Setup

Clone the project:

```bash
git clone https://github.com/MohammadDaghash/smart-camera-app.git
cd smart-camera-app
```

Switch to the development branch:

```bash
git checkout dev
git pull origin dev
```

## Run Locally

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

On macOS, make sure Terminal, VS Code, or Python has Camera permission enabled:

```text
System Settings -> Privacy & Security -> Camera
```

## Team Responsibilities

### Omar - Backend / Architecture Lead

Feature branch:

```bash
git checkout dev
git pull origin dev
git checkout -b feature/backend-refactor
```

Focus:

- Review backend architecture
- Improve `camera_service.py`
- Improve camera open, release, and reconnect logic
- Review scalability of `/video` streaming
- Improve backend structure and maintainability
- Review pull requests and architecture decisions

First issue:

```text
Refine backend camera pipeline boundaries
```

### Mohammad - ML / Computer Vision Lead

Feature branch:

```bash
git checkout dev
git pull origin dev
git checkout -b feature/multi-photo-recognition
```

Focus:

- Improve face recognition accuracy
- Support multiple photos per person
- Average embeddings per person
- Tune `FACE_MATCH_THRESHOLD`
- Add smoothing across frames
- Improve recognition stability under different lighting and angles

First issue:

```text
Support multiple known-face photos per person
```

### Majd - Frontend / Dashboard Lead

Feature branch:

```bash
git checkout dev
git pull origin dev
git checkout -b feature/frontend-dashboard
```

Focus:

- Improve frontend UI
- Create a dashboard layout
- Add camera status indicators
- Improve recognition label styling
- Improve anonymous and known-person overlays
- Keep live stream as the main focus

First issue:

```text
Build a simple frontend dashboard shell
```

## Team Git Workflow

Before starting work, always update `dev` first:

```bash
git checkout dev
git pull origin dev
```

Then create or update your feature branch.

Before pushing code, check your local changes:

```bash
git status
```

Push a new feature branch:

```bash
git push -u origin feature/your-branch-name
```

After the first push, later pushes can use:

```bash
git push
```

## Pull Request Workflow

When your feature is ready:

1. Push your branch.
2. Open a Pull Request from your feature branch into `dev`.
3. Request review from the team.
4. Merge only after review.

## Important Rules

- Never push directly to `main`.
- Avoid pushing directly to `dev`.
- Use feature branches for everything.
- Keep commits clean and focused.
- Test locally before opening PRs.
- Do not commit local known-face photos.

Known face images should stay local and are ignored by Git:

```text
backend/known_faces/
```

## Current Project Goal

Current focus:

```text
Build a stable local computer-vision MVP.
```

Not yet:

- Cloud deployment
- Databases
- Authentication
- Mobile apps
- Smart-home integrations

Current priority:

```text
Accuracy + stability + clean architecture
```
