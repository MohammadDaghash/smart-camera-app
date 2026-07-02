import secrets
import threading
import time

from app.config import SESSION_MAX_AGE_SECONDS


_lock = threading.Lock()
_sessions: dict[str, float] = {}


def create_session(now: float | None = None) -> str:
    current = time.time() if now is None else now
    session_id = secrets.token_urlsafe(32)

    with _lock:
        _sessions[session_id] = current + SESSION_MAX_AGE_SECONDS

    return session_id


def is_valid(session_id: str, now: float | None = None) -> bool:
    current = time.time() if now is None else now

    with _lock:
        expires_at = _sessions.get(session_id)

        if expires_at is None:
            return False

        if expires_at <= current:
            _sessions.pop(session_id, None)
            return False

    return True


def revoke(session_id: str) -> None:
    with _lock:
        _sessions.pop(session_id, None)


def revoke_all() -> None:
    with _lock:
        _sessions.clear()


def active_count() -> int:
    with _lock:
        return len(_sessions)
