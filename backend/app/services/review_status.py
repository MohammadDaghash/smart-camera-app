import sqlite3
import time
from pathlib import Path
from threading import Lock

from app.config import REVIEW_STATUS_DB_FILE


REVIEW_STATUSES = ("new", "reviewed", "false_positive")


class ReviewStatusStore:
    def __init__(self, database_path=REVIEW_STATUS_DB_FILE):
        self.database_path = database_path
        self._lock = Lock()
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
                CREATE TABLE IF NOT EXISTS review_statuses (
                    review_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )
            self._connection.commit()

    def get_statuses(self, review_ids):
        review_ids = list(dict.fromkeys(review_ids))

        if not review_ids:
            return {}

        placeholders = ", ".join("?" for _ in review_ids)

        with self._lock:
            rows = self._connection.execute(
                f"""
                SELECT review_id, status, updated_at
                FROM review_statuses
                WHERE review_id IN ({placeholders})
                """,
                review_ids,
            ).fetchall()

        return {
            row["review_id"]: {
                "status": row["status"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        }

    def set_status(self, review_id, status, now=None):
        normalized_status = (
            status.strip().lower().replace("-", "_").replace(" ", "_")
        )

        if normalized_status not in REVIEW_STATUSES:
            raise ValueError(
                f"status must be one of: {', '.join(REVIEW_STATUSES)}"
            )

        updated_at = now if now is not None else time.time()

        with self._lock:
            self._connection.execute(
                """
                INSERT INTO review_statuses (review_id, status, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(review_id) DO UPDATE SET
                    status = excluded.status,
                    updated_at = excluded.updated_at
                """,
                (review_id, normalized_status, updated_at),
            )
            self._connection.commit()

        return {
            "review_id": review_id,
            "status": normalized_status,
            "updated_at": updated_at,
        }

    def apply_statuses(self, items):
        saved_statuses = self.get_statuses(item["id"] for item in items)
        decorated_items = []

        for item in items:
            decorated_item = dict(item)
            saved_status = saved_statuses.get(item["id"])
            decorated_item["review_status"] = (
                saved_status["status"] if saved_status else "new"
            )
            decorated_item["review_status_updated_at"] = (
                saved_status["updated_at"] if saved_status else None
            )
            decorated_items.append(decorated_item)

        return decorated_items

    def reset(self):
        with self._lock:
            self._connection.execute("DELETE FROM review_statuses")
            self._connection.commit()


review_status_store = ReviewStatusStore()
