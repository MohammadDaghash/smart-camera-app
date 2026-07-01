import os
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent

# Load backend/.env (if present) so notification settings can live in a local,
# gitignored file. Falls back to plain environment variables when python-dotenv
# is not installed.
try:
    from dotenv import load_dotenv

    load_dotenv(BACKEND_DIR / ".env")
except ImportError:
    pass

FRONTEND_FILE = PROJECT_DIR / "frontend" / "index.html"
KNOWN_FACES_DIR = BACKEND_DIR / "known_faces"

CAMERA_INDEXES = [0, 1, 2]
READ_ATTEMPTS = 10
RECONNECT_AFTER_FAILURES = 10

INSIGHTFACE_MODEL_NAME = "buffalo_l"
INSIGHTFACE_DETECTION_SIZE = (640, 640)
FACE_MATCH_THRESHOLD = 0.45
KNOWN_FACE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def _env_flag(name, default):
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return int(default)


# Email notifications: send a message when a target person is seen on the feed.
# Configure via environment variables (see backend/.env.example). When SMTP is
# not configured the notification feature is a safe no-op.
NOTIFY_PERSON_NAME = os.environ.get("NOTIFY_PERSON_NAME", "Omar")
NOTIFY_COOLDOWN_SECONDS = _env_int("NOTIFY_COOLDOWN_SECONDS", "300")

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = _env_int("SMTP_PORT", "587")
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_USE_TLS = _env_flag("SMTP_USE_TLS", "true")

NOTIFY_EMAIL_FROM = os.environ.get("NOTIFY_EMAIL_FROM", "")
NOTIFY_EMAIL_TO = os.environ.get("NOTIFY_EMAIL_TO", "")
