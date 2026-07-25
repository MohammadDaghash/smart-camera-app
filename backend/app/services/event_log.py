import time
from collections import deque
from threading import Lock


class EventLog:
    def __init__(self, max_events=100):
        self.max_events = max_events
        self._events = deque(maxlen=max_events)
        self._lock = Lock()
        self._next_id = 1
        self._last_event_times = {}

    def add_event(
        self,
        event_type,
        message,
        metadata=None,
        now=None,
        cooldown_key=None,
        cooldown_seconds=0,
    ):
        created_at = now if now is not None else time.time()

        with self._lock:
            if cooldown_key and cooldown_seconds > 0:
                last_event_at = self._last_event_times.get(cooldown_key)

                if (
                    last_event_at is not None
                    and created_at - last_event_at < cooldown_seconds
                ):
                    return None

                self._last_event_times[cooldown_key] = created_at

            event = {
                "id": self._next_id,
                "type": event_type,
                "message": message,
                "created_at": created_at,
                "metadata": metadata or {},
            }
            self._next_id += 1
            self._events.appendleft(event)

            return dict(event)

    def latest(self, limit=10):
        with self._lock:
            return [dict(event) for event in list(self._events)[:limit]]

    def reset(self):
        with self._lock:
            self._events.clear()
            self._next_id = 1
            self._last_event_times.clear()


event_log = EventLog()
