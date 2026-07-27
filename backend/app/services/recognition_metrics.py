import sqlite3
import time
from pathlib import Path
from threading import Lock

from app.config import (
    FACE_MATCH_THRESHOLD,
    RECOGNITION_METRICS_DB_FILE,
    RECOGNITION_METRICS_MAX_OBSERVATIONS,
    RECOGNITION_METRICS_SAMPLE_INTERVAL_SECONDS,
)


class RecognitionMetricsStore:
    def __init__(
        self,
        database_path=RECOGNITION_METRICS_DB_FILE,
        max_observations=RECOGNITION_METRICS_MAX_OBSERVATIONS,
        sample_interval_seconds=RECOGNITION_METRICS_SAMPLE_INTERVAL_SECONDS,
    ):
        self.database_path = database_path
        self.max_observations = max_observations
        self.sample_interval_seconds = sample_interval_seconds
        self._lock = Lock()
        self._last_saved_at = None
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
                CREATE TABLE IF NOT EXISTS recognition_observations (
                    id INTEGER PRIMARY KEY,
                    created_at REAL NOT NULL,
                    track_id TEXT,
                    label TEXT NOT NULL,
                    score REAL NOT NULL,
                    raw_label TEXT NOT NULL,
                    raw_score REAL NOT NULL
                )
                """
            )
            self._connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_recognition_observations_created_at
                ON recognition_observations (created_at DESC, id DESC)
                """
            )
            self._connection.commit()

    def add_observations(self, annotations, now=None):
        saved_at = now if now is not None else time.time()
        rows = [observation_from_annotation(annotation) for annotation in annotations]

        if not rows:
            return []

        with self._lock:
            if not self._should_sample(saved_at):
                return []

            self._connection.executemany(
                """
                INSERT INTO recognition_observations (
                    created_at,
                    track_id,
                    label,
                    score,
                    raw_label,
                    raw_score
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        saved_at,
                        row["track_id"],
                        row["label"],
                        row["score"],
                        row["raw_label"],
                        row["raw_score"],
                    )
                    for row in rows
                ],
            )
            self._last_saved_at = saved_at
            self._prune_old_observations()
            self._connection.commit()

        return [
            {
                **row,
                "created_at": saved_at,
            }
            for row in rows
        ]

    def latest(self, limit=100, label=None):
        limit = max(1, min(int(limit), self.max_observations))
        conditions = []
        params = []

        if label:
            conditions.append("LOWER(label) LIKE ?")
            params.append(f"%{label.strip().lower()}%")

        query = """
            SELECT id, created_at, track_id, label, score, raw_label, raw_score
            FROM recognition_observations
        """

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_at DESC, id DESC LIMIT ?"
        params.append(limit)

        with self._lock:
            rows = self._connection.execute(query, params).fetchall()

        return [row_to_observation(row) for row in rows]

    def summary(self, limit=200, label=None):
        observations = list(reversed(self.latest(limit=limit, label=label)))
        return summarize_observations(observations, threshold=FACE_MATCH_THRESHOLD)

    def reset(self):
        with self._lock:
            self._connection.execute("DELETE FROM recognition_observations")
            self._connection.commit()
            self._last_saved_at = None

    def _should_sample(self, saved_at):
        if self.sample_interval_seconds <= 0:
            return True

        return (
            self._last_saved_at is None
            or saved_at - self._last_saved_at >= self.sample_interval_seconds
        )

    def _prune_old_observations(self):
        self._connection.execute(
            """
            DELETE FROM recognition_observations
            WHERE id NOT IN (
                SELECT id
                FROM recognition_observations
                ORDER BY created_at DESC, id DESC
                LIMIT ?
            )
            """,
            (self.max_observations,),
        )


def observation_from_annotation(annotation):
    label = str(annotation.get("label", "Anonymous"))
    raw_label = str(annotation.get("raw_label", label))

    return {
        "track_id": as_text(annotation.get("track_id")),
        "label": label,
        "score": round(float(annotation.get("score", 0.0)), 4),
        "raw_label": raw_label,
        "raw_score": round(
            float(annotation.get("raw_score", annotation.get("score", 0.0))),
            4,
        ),
    }


def row_to_observation(row):
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "track_id": row["track_id"],
        "label": row["label"],
        "score": row["score"],
        "raw_label": row["raw_label"],
        "raw_score": row["raw_score"],
    }


def summarize_observations(observations, threshold=FACE_MATCH_THRESHOLD):
    per_label = {}
    near_threshold_count = 0

    for observation in observations:
        label = observation["label"]
        label_summary = per_label.setdefault(
            label,
            {
                "label": label,
                "count": 0,
                "average_score": 0.0,
                "min_score": None,
                "max_score": None,
                "latest_score": None,
                "latest_seen_at": None,
            },
        )

        score = float(observation["raw_score"])
        label_summary["count"] += 1
        label_summary["average_score"] += score
        label_summary["min_score"] = min_score(label_summary["min_score"], score)
        label_summary["max_score"] = max_score(label_summary["max_score"], score)
        label_summary["latest_score"] = score
        label_summary["latest_seen_at"] = observation["created_at"]

        if abs(score - threshold) <= 0.05:
            near_threshold_count += 1

    for label_summary in per_label.values():
        label_summary["average_score"] = round(
            label_summary["average_score"] / label_summary["count"],
            4,
        )
        label_summary["min_score"] = round(label_summary["min_score"], 4)
        label_summary["max_score"] = round(label_summary["max_score"], 4)
        label_summary["latest_score"] = round(label_summary["latest_score"], 4)

    total_observations = len(observations)
    known_observations = sum(
        1
        for observation in observations
        if not is_anonymous_label(observation["label"])
    )

    return {
        "total_observations": total_observations,
        "known_observations": known_observations,
        "anonymous_observations": total_observations - known_observations,
        "near_threshold_observations": near_threshold_count,
        "threshold": threshold,
        "per_label": sorted(
            per_label.values(),
            key=lambda item: (-item["count"], item["label"]),
        ),
    }


def as_text(value):
    if value is None:
        return None

    return str(value)


def is_anonymous_label(label):
    return label.strip().lower().startswith("anonymous")


def min_score(current_value, new_value):
    if current_value is None:
        return new_value

    return min(current_value, new_value)


def max_score(current_value, new_value):
    if current_value is None:
        return new_value

    return max(current_value, new_value)


recognition_metrics_store = RecognitionMetricsStore()
