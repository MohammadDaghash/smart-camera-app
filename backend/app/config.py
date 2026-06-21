import os
import secrets
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env")

FRONTEND_FILE = PROJECT_DIR / "frontend" / "index.html"
LOGIN_FILE = PROJECT_DIR / "frontend" / "login.html"
KNOWN_FACES_DIR = BACKEND_DIR / "known_faces"

CAMERA_INDEXES = [0, 1, 2]
READ_ATTEMPTS = 10
RECONNECT_AFTER_FAILURES = 10

INSIGHTFACE_MODEL_NAME = "buffalo_l"
INSIGHTFACE_DETECTION_SIZE = (640, 640)
FACE_MATCH_THRESHOLD = 0.45
KNOWN_FACE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

# Authentication / session configuration.
# Real credentials and secrets belong in backend/.env (gitignored), never here.
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "admin")
AUTH_USING_DEFAULT_CREDENTIALS = (
    os.getenv("AUTH_USERNAME") is None or os.getenv("AUTH_PASSWORD") is None
)

SESSION_SECRET = os.getenv("SESSION_SECRET") or secrets.token_urlsafe(32)
SESSION_SECRET_IS_EPHEMERAL = not os.getenv("SESSION_SECRET")
SESSION_COOKIE_NAME = "smart_camera_session"
SESSION_MAX_AGE_SECONDS = int(os.getenv("SESSION_MAX_AGE_SECONDS", str(24 * 60 * 60)))
