import time
from collections import deque
from threading import Lock


class EventLog:
    def __init__(self, max_events=100):
        self.max_events = max_events
        self._events = deque(maxlen=max_events)
        self._lock = Lock()
        self._next_id = 1

    def add_event(self, event_type, message, metadata=None, now=None):
        created_at = now if now is not None else time.time()

        with self._lock:
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


event_log = EventLog()
