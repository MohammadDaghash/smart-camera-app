from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent

FRONTEND_FILE = PROJECT_DIR / "frontend" / "index.html"
KNOWN_FACES_DIR = BACKEND_DIR / "known_faces"

CAMERA_INDEXES = [0, 1, 2]
READ_ATTEMPTS = 10
RECONNECT_AFTER_FAILURES = 10

INSIGHTFACE_MODEL_NAME = "buffalo_l"
INSIGHTFACE_DETECTION_SIZE = (640, 640)
FACE_MATCH_THRESHOLD = 0.45
KNOWN_FACE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
