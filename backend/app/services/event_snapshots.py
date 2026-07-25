import re
import time
from pathlib import Path

import cv2

from app.config import (
    EVENT_MAX_EVENTS,
    EVENT_RETENTION_DAYS,
    EVENT_SNAPSHOT_JPEG_QUALITY,
    EVENT_SNAPSHOT_MAX_WIDTH,
    EVENT_SNAPSHOTS_DIR,
    EVENT_SNAPSHOTS_ENABLED,
)
from app.services.event_log import SECONDS_PER_DAY
from app.utils.logging import logger


SNAPSHOT_FILENAME_PATTERN = re.compile(r"^[0-9]+-[0-9]+-[a-zA-Z0-9_-]+\.jpg$")


class EventSnapshotStore:
    def __init__(
        self,
        snapshots_dir=EVENT_SNAPSHOTS_DIR,
        enabled=EVENT_SNAPSHOTS_ENABLED,
        max_width=EVENT_SNAPSHOT_MAX_WIDTH,
        jpeg_quality=EVENT_SNAPSHOT_JPEG_QUALITY,
        max_snapshots=EVENT_MAX_EVENTS,
        retention_days=EVENT_RETENTION_DAYS,
    ):
        self.snapshots_dir = Path(snapshots_dir)
        self.enabled = enabled
        self.max_width = max_width
        self.jpeg_quality = min(100, max(1, jpeg_quality))
        self.max_snapshots = max_snapshots
        self.retention_seconds = None

        if retention_days > 0:
            self.retention_seconds = retention_days * SECONDS_PER_DAY

        if self.enabled:
            self.snapshots_dir.mkdir(parents=True, exist_ok=True)
            self.cleanup()

    def save_snapshot(self, frame, event_id, event_type, now=None):
        if not self.enabled:
            return None

        created_at = now if now is not None else time.time()
        safe_event_type = self._safe_event_type(event_type)
        filename = f"{int(created_at)}-{event_id}-{safe_event_type}.jpg"
        snapshot_path = self.snapshots_dir / filename
        snapshot_frame = self._resize_frame(frame)

        success, encoded_frame = cv2.imencode(
            ".jpg",
            snapshot_frame,
            [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality],
        )

        if not success:
            logger.warning("Could not encode event snapshot for event %s", event_id)
            return None

        try:
            snapshot_path.write_bytes(encoded_frame.tobytes())
        except OSError as error:
            logger.warning("Could not save event snapshot %s: %s", snapshot_path, error)
            return None

        self.cleanup(now=created_at)

        return {
            "snapshot_filename": filename,
            "snapshot_url": f"/api/snapshots/{filename}",
        }

    def get_snapshot_path(self, filename):
        if not self.is_valid_snapshot_filename(filename):
            return None

        snapshot_path = self.snapshots_dir / filename

        if not snapshot_path.exists():
            return None

        return snapshot_path

    def cleanup(self, now=None):
        if not self.enabled or not self.snapshots_dir.exists():
            return {
                "deleted_expired": 0,
                "deleted_over_limit": 0,
            }

        cleanup_at = now if now is not None else time.time()
        snapshots = self._snapshot_files()
        deleted_expired = self._delete_expired_snapshots(snapshots, cleanup_at)
        snapshots = self._snapshot_files()
        deleted_over_limit = self._delete_over_limit_snapshots(snapshots)

        return {
            "deleted_expired": deleted_expired,
            "deleted_over_limit": deleted_over_limit,
        }

    def is_valid_snapshot_filename(self, filename):
        return bool(SNAPSHOT_FILENAME_PATTERN.fullmatch(filename))

    def _resize_frame(self, frame):
        height, width = frame.shape[:2]

        if width <= self.max_width:
            return frame

        scale = self.max_width / width
        resized_height = max(1, int(height * scale))

        return cv2.resize(frame, (self.max_width, resized_height))

    def _safe_event_type(self, event_type):
        safe_event_type = re.sub(r"[^a-zA-Z0-9_-]", "-", event_type)
        return safe_event_type.strip("-") or "event"

    def _snapshot_files(self):
        return sorted(
            self.snapshots_dir.glob("*.jpg"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

    def _delete_expired_snapshots(self, snapshots, now):
        if not self.retention_seconds:
            return 0

        cutoff = now - self.retention_seconds
        deleted = 0

        for snapshot_path in snapshots:
            if snapshot_path.stat().st_mtime >= cutoff:
                continue

            if self._delete_file(snapshot_path):
                deleted += 1

        return deleted

    def _delete_over_limit_snapshots(self, snapshots):
        deleted = 0

        for snapshot_path in snapshots[self.max_snapshots :]:
            if self._delete_file(snapshot_path):
                deleted += 1

        return deleted

    def _delete_file(self, path):
        try:
            path.unlink()
            return True
        except FileNotFoundError:
            return False
        except OSError as error:
            logger.warning("Could not delete old snapshot %s: %s", path, error)
            return False


event_snapshot_store = EventSnapshotStore()
