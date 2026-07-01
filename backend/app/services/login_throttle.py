import threading
import time

from app.config import (
    LOGIN_ATTEMPT_WINDOW_SECONDS,
    LOGIN_LOCKOUT_SECONDS,
    LOGIN_MAX_ATTEMPTS,
)


_lock = threading.Lock()
_failures: dict[str, list[float]] = {}
_locked_until: dict[str, float] = {}


def lockout_remaining(key: str, now: float | None = None) -> float:
    current = time.time() if now is None else now

    with _lock:
        until = _locked_until.get(key)

        if until is None:
            return 0.0

        if until <= current:
            _locked_until.pop(key, None)
            _failures.pop(key, None)
            return 0.0

        return until - current


def record_failure(key: str, now: float | None = None) -> None:
    current = time.time() if now is None else now
    window_start = current - LOGIN_ATTEMPT_WINDOW_SECONDS

    with _lock:
        attempts = [t for t in _failures.get(key, []) if t >= window_start]
        attempts.append(current)
        _failures[key] = attempts

        if len(attempts) >= LOGIN_MAX_ATTEMPTS:
            _locked_until[key] = current + LOGIN_LOCKOUT_SECONDS
            _failures.pop(key, None)


def record_success(key: str) -> None:
    with _lock:
        _failures.pop(key, None)
        _locked_until.pop(key, None)


def clear() -> None:
    with _lock:
        _failures.clear()
        _locked_until.clear()
