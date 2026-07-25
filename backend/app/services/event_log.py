import json
import sqlite3
import time
from pathlib import Path
from threading import Lock

from app.config import EVENTS_DB_FILE


class EventLog:
    def __init__(self, database_path=":memory:", max_events=100):
        self.database_path = database_path
        self.max_events = max_events
        self._lock = Lock()
        self._last_event_times = {}
        self._connection = self._connect()
        self._create_schema()

    def _connect(self):
        if self.database_path != ":memory:":
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)

        connection = sqlite3.connect(str(self.database_path), check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def _create_schema(self):
        with self._lock:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY,
                    type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    metadata_json TEXT NOT NULL
                )
                """
            )
            self._connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_events_created_at
                ON events (created_at DESC, id DESC)
                """
            )
            self._connection.commit()

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
        metadata = metadata or {}

        with self._lock:
            if cooldown_key and cooldown_seconds > 0:
                last_event_at = self._last_event_times.get(cooldown_key)

                if (
                    last_event_at is not None
                    and created_at - last_event_at < cooldown_seconds
                ):
                    return None

                self._last_event_times[cooldown_key] = created_at

            cursor = self._connection.execute(
                """
                INSERT INTO events (type, message, created_at, metadata_json)
                VALUES (?, ?, ?, ?)
                """,
                (event_type, message, created_at, json.dumps(metadata)),
            )
            self._prune_old_events()
            self._connection.commit()

            return {
                "id": cursor.lastrowid,
                "type": event_type,
                "message": message,
                "created_at": created_at,
                "metadata": dict(metadata),
            }

    def latest(self, limit=10):
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT id, type, message, created_at, metadata_json
                FROM events
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

            return [self._row_to_event(row) for row in rows]

    def reset(self):
        with self._lock:
            self._connection.execute("DELETE FROM events")
            self._connection.commit()
            self._last_event_times.clear()

    def _prune_old_events(self):
        self._connection.execute(
            """
            DELETE FROM events
            WHERE id NOT IN (
                SELECT id
                FROM events
                ORDER BY created_at DESC, id DESC
                LIMIT ?
            )
            """,
            (self.max_events,),
        )

    def _row_to_event(self, row):
        try:
            metadata = json.loads(row["metadata_json"])
        except json.JSONDecodeError:
            metadata = {}

        return {
            "id": row["id"],
            "type": row["type"],
            "message": row["message"],
            "created_at": row["created_at"],
            "metadata": metadata,
        }


event_log = EventLog(database_path=EVENTS_DB_FILE)
