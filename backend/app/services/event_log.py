import json
import sqlite3
import time
from pathlib import Path
from threading import Lock

from app.config import EVENT_MAX_EVENTS, EVENT_RETENTION_DAYS, EVENTS_DB_FILE


SECONDS_PER_DAY = 24 * 60 * 60


class EventLog:
    def __init__(self, database_path=":memory:", max_events=100, retention_seconds=None):
        self.database_path = database_path
        self.max_events = max_events
        self.retention_seconds = retention_seconds
        self._lock = Lock()
        self._last_event_times = {}
        self._connection = self._connect()
        self._create_schema()
        self.cleanup()

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
            self._delete_expired_events(created_at)
            self._prune_old_events()
            self._connection.commit()

            return {
                "id": cursor.lastrowid,
                "type": event_type,
                "message": message,
                "created_at": created_at,
                "metadata": dict(metadata),
            }

    def latest(
        self,
        limit=10,
        event_type=None,
        label=None,
        start_at=None,
        end_at=None,
    ):
        with self._lock:
            conditions = []
            params = []

            if event_type is not None:
                conditions.append("type = ?")
                params.append(event_type)

            if start_at is not None:
                conditions.append("created_at >= ?")
                params.append(start_at)

            if end_at is not None:
                conditions.append("created_at <= ?")
                params.append(end_at)

            query = """
                SELECT id, type, message, created_at, metadata_json
                FROM events
            """

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY created_at DESC, id DESC LIMIT ?"
            params.append(self.max_events if label else limit)

            rows = self._connection.execute(query, params).fetchall()
            events = [self._row_to_event(row) for row in rows]

            if label:
                events = [
                    event
                    for event in events
                    if event_matches_label(event, label)
                ][:limit]

            return events

    def update_event_metadata(self, event_id, metadata):
        with self._lock:
            row = self._connection.execute(
                """
                SELECT id, type, message, created_at, metadata_json
                FROM events
                WHERE id = ?
                """,
                (event_id,),
            ).fetchone()

            if row is None:
                return None

            event = self._row_to_event(row)
            event["metadata"].update(metadata)

            self._connection.execute(
                """
                UPDATE events
                SET metadata_json = ?
                WHERE id = ?
                """,
                (json.dumps(event["metadata"]), event_id),
            )
            self._connection.commit()

            return event

    def reset(self):
        with self._lock:
            self._connection.execute("DELETE FROM events")
            self._connection.commit()
            self._last_event_times.clear()

    def cleanup(self, now=None):
        cleanup_at = now if now is not None else time.time()

        with self._lock:
            deleted_expired = self._delete_expired_events(cleanup_at)
            deleted_over_limit = self._prune_old_events()
            self._connection.commit()

            return {
                "deleted_expired": deleted_expired,
                "deleted_over_limit": deleted_over_limit,
            }

    def retention_settings(self):
        retention_days = None

        if self.retention_seconds is not None:
            retention_days = self.retention_seconds / SECONDS_PER_DAY

        return {
            "max_events": self.max_events,
            "retention_days": retention_days,
        }

    def _delete_expired_events(self, now):
        if not self.retention_seconds:
            return 0

        cutoff = now - self.retention_seconds
        cursor = self._connection.execute(
            "DELETE FROM events WHERE created_at < ?",
            (cutoff,),
        )

        return cursor.rowcount

    def _prune_old_events(self):
        cursor = self._connection.execute(
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

        return cursor.rowcount

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


def event_matches_label(event, label):
    query = label.strip().lower()

    if not query:
        return True

    metadata = event.get("metadata") or {}
    candidate_labels = []

    label_value = metadata.get("label")

    if isinstance(label_value, str):
        candidate_labels.append(label_value)

    labels_value = metadata.get("labels")

    if isinstance(labels_value, list):
        candidate_labels.extend(
            value
            for value in labels_value
            if isinstance(value, str)
        )

    return any(query in candidate.lower() for candidate in candidate_labels)


event_retention_seconds = None

if EVENT_RETENTION_DAYS > 0:
    event_retention_seconds = EVENT_RETENTION_DAYS * SECONDS_PER_DAY

event_log = EventLog(
    database_path=EVENTS_DB_FILE,
    max_events=EVENT_MAX_EVENTS,
    retention_seconds=event_retention_seconds,
)
