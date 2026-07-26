import os
import secrets
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env")


def _env_int(
    name: str,
    default: int,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    raw = os.getenv(name)

    if raw is None:
        value = default
    else:
        try:
            value = int(raw)
        except ValueError:
            value = default

    if minimum is not None:
        value = max(minimum, value)

    if maximum is not None:
        value = min(maximum, value)

    return value


def _env_float(
    name: str,
    default: float,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    raw = os.getenv(name)

    if raw is None:
        value = default
    else:
        try:
            value = float(raw)
        except ValueError:
            value = default

    if minimum is not None:
        value = max(minimum, value)

    if maximum is not None:
        value = min(maximum, value)

    return value


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)

    if raw is None:
        return default

    return raw.strip().lower() in {"1", "true", "yes", "on"}


FRONTEND_FILE = PROJECT_DIR / "frontend" / "index.html"
LOGIN_FILE = PROJECT_DIR / "frontend" / "login.html"
EVENTS_FILE = PROJECT_DIR / "frontend" / "events.html"
RECOGNITION_DEBUG_FILE = PROJECT_DIR / "frontend" / "recognition-debug.html"
DIAGNOSTICS_FILE = PROJECT_DIR / "frontend" / "diagnostics.html"
SETTINGS_FILE = PROJECT_DIR / "frontend" / "settings.html"
KNOWN_FACES_DIR = BACKEND_DIR / "known_faces"
LOCAL_DATA_DIR = BACKEND_DIR / "local_data"
EVENTS_DB_FILE = LOCAL_DATA_DIR / "events.db"
EVENT_SNAPSHOTS_DIR = LOCAL_DATA_DIR / "snapshots"

CAMERA_INDEXES = [0, 1, 2]
READ_ATTEMPTS = 10
RECONNECT_AFTER_FAILURES = 10
FACE_ANALYSIS_INTERVAL_FRAMES = _env_int("FACE_ANALYSIS_INTERVAL_FRAMES", 1, minimum=1)
FACE_LABEL_SMOOTHING_ENABLED = _env_flag("FACE_LABEL_SMOOTHING_ENABLED", default=True)
FACE_LABEL_SMOOTHING_HISTORY_SIZE = _env_int(
    "FACE_LABEL_SMOOTHING_HISTORY_SIZE",
    5,
    minimum=1,
)
FACE_LABEL_SMOOTHING_MIN_VOTES = _env_int(
    "FACE_LABEL_SMOOTHING_MIN_VOTES",
    2,
    minimum=1,
)
FACE_TRACK_IOU_THRESHOLD = _env_float(
    "FACE_TRACK_IOU_THRESHOLD",
    0.2,
    minimum=0.0,
    maximum=1.0,
)
FACE_TRACK_TTL_FRAMES = _env_int("FACE_TRACK_TTL_FRAMES", 5, minimum=1)

INSIGHTFACE_MODEL_NAME = "buffalo_l"
INSIGHTFACE_DETECTION_SIZE = (640, 640)
FACE_MATCH_THRESHOLD = _env_float(
    "FACE_MATCH_THRESHOLD",
    0.45,
    minimum=0.0,
    maximum=1.0,
)
KNOWN_FACE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

MOTION_DETECTION_ENABLED = _env_flag("MOTION_DETECTION_ENABLED", default=True)
MOTION_MIN_AREA = _env_int("MOTION_MIN_AREA", 500, minimum=1)
MOTION_SCORE_THRESHOLD = _env_float("MOTION_SCORE_THRESHOLD", 0.02, minimum=0.0)

EVENT_MOTION_COOLDOWN_SECONDS = _env_int(
    "EVENT_MOTION_COOLDOWN_SECONDS",
    10,
    minimum=0,
)
EVENT_FACE_COOLDOWN_SECONDS = _env_int(
    "EVENT_FACE_COOLDOWN_SECONDS",
    20,
    minimum=0,
)
EVENT_MAX_EVENTS = _env_int("EVENT_MAX_EVENTS", 1000, minimum=1)
EVENT_RETENTION_DAYS = _env_int("EVENT_RETENTION_DAYS", 30, minimum=0)
EVENT_SNAPSHOTS_ENABLED = _env_flag("EVENT_SNAPSHOTS_ENABLED", default=True)
EVENT_SNAPSHOT_MAX_WIDTH = _env_int("EVENT_SNAPSHOT_MAX_WIDTH", 640, minimum=1)
EVENT_SNAPSHOT_JPEG_QUALITY = _env_int("EVENT_SNAPSHOT_JPEG_QUALITY", 85, minimum=1)

ALERTS_ENABLED = _env_flag("ALERTS_ENABLED", default=True)
ALERT_ANONYMOUS_MOTION_WINDOW_SECONDS = _env_int(
    "ALERT_ANONYMOUS_MOTION_WINDOW_SECONDS",
    30,
    minimum=1,
)
ALERT_COOLDOWN_SECONDS = _env_int("ALERT_COOLDOWN_SECONDS", 60, minimum=0)

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


# Send the session cookie only over HTTPS. Keep False for local HTTP, enable
# behind TLS when serving on a network.
SESSION_HTTPS_ONLY = _env_flag("SESSION_HTTPS_ONLY", default=False)

# Login rate limiting / lockout, tracked per client IP.
LOGIN_MAX_ATTEMPTS = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
LOGIN_ATTEMPT_WINDOW_SECONDS = int(os.getenv("LOGIN_ATTEMPT_WINDOW_SECONDS", "300"))
LOGIN_LOCKOUT_SECONDS = int(os.getenv("LOGIN_LOCKOUT_SECONDS", "300"))
