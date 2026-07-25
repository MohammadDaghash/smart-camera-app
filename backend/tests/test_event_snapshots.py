import os

import cv2
import numpy as np

from app.services.event_snapshots import EventSnapshotStore


def test_event_snapshot_store_saves_resized_jpeg_snapshot(tmp_path):
    store = EventSnapshotStore(
        snapshots_dir=tmp_path,
        max_width=50,
        jpeg_quality=80,
        retention_days=0,
    )
    frame = np.zeros((100, 200, 3), dtype=np.uint8)

    metadata = store.save_snapshot(frame, event_id=7, event_type="motion", now=1234.0)

    assert metadata == {
        "snapshot_filename": "1234-7-motion.jpg",
        "snapshot_url": "/api/snapshots/1234-7-motion.jpg",
    }
    snapshot_path = store.get_snapshot_path("1234-7-motion.jpg")
    assert snapshot_path is not None
    saved_image = cv2.imread(str(snapshot_path))
    assert saved_image.shape[1] == 50


def test_event_snapshot_store_rejects_invalid_snapshot_filenames(tmp_path):
    store = EventSnapshotStore(snapshots_dir=tmp_path)

    assert store.get_snapshot_path("../events.db") is None
    assert store.get_snapshot_path("not-a-generated-name.jpg") is None


def test_event_snapshot_store_can_be_disabled(tmp_path):
    store = EventSnapshotStore(snapshots_dir=tmp_path, enabled=False)
    frame = np.zeros((20, 20, 3), dtype=np.uint8)

    metadata = store.save_snapshot(frame, event_id=1, event_type="motion")

    assert metadata is None
    assert list(tmp_path.iterdir()) == []


def test_event_snapshot_store_deletes_expired_and_over_limit_files(tmp_path):
    store = EventSnapshotStore(
        snapshots_dir=tmp_path,
        max_snapshots=1,
        retention_days=1,
    )
    old_file = tmp_path / "100-1-motion.jpg"
    older_file = tmp_path / "200-2-motion.jpg"
    newest_file = tmp_path / "300-3-motion.jpg"

    old_file.write_bytes(b"old")
    older_file.write_bytes(b"older")
    newest_file.write_bytes(b"newest")
    os.utime(old_file, (100.0, 100.0))
    os.utime(older_file, (200.0, 200.0))
    os.utime(newest_file, (300.0, 300.0))

    result = store.cleanup(now=300.0 + (2 * 24 * 60 * 60))

    assert result["deleted_expired"] == 3
    assert result["deleted_over_limit"] == 0
    assert list(tmp_path.glob("*.jpg")) == []


def test_event_snapshot_store_deletes_over_limit_files(tmp_path):
    store = EventSnapshotStore(
        snapshots_dir=tmp_path,
        max_snapshots=1,
        retention_days=0,
    )
    older_file = tmp_path / "200-2-motion.jpg"
    newest_file = tmp_path / "300-3-motion.jpg"

    older_file.write_bytes(b"older")
    newest_file.write_bytes(b"newest")
    os.utime(older_file, (200.0, 200.0))
    os.utime(newest_file, (300.0, 300.0))

    result = store.cleanup()

    assert result["deleted_expired"] == 0
    assert result["deleted_over_limit"] == 1
    assert [path.name for path in tmp_path.glob("*.jpg")] == ["300-3-motion.jpg"]
