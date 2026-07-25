from app.services import recognition_debug


class FakePipelineStats:
    def snapshot(self):
        return {
            "camera": {
                "frames_read": 10,
                "frames_streamed": 9,
                "active_streams": 1,
            },
            "analysis": {
                "analysis_frames": 3,
                "last_face_count": 1,
                "last_labels": ["Mohammad:0.81"],
                "last_faces": [
                    {
                        "label": "Mohammad",
                        "raw_label": "Mohammad",
                        "raw_score": 0.81,
                    }
                ],
            },
            "performance": {
                "camera_fps": 5.0,
                "stream_fps": 4.8,
                "analysis_fps": 1.0,
                "motion_fps": 5.0,
                "skipped_analysis_fps": 4.0,
                "uptime_seconds": 12.0,
            },
            "runtime": {
                "last_analysis_at": 123.0,
            },
        }


def test_recognition_debug_snapshot_includes_performance(monkeypatch):
    monkeypatch.setattr(recognition_debug, "pipeline_stats", FakePipelineStats())
    monkeypatch.setattr(
        recognition_debug,
        "get_known_faces_summary",
        lambda: {"loaded_embeddings": 2},
    )

    snapshot = recognition_debug.recognition_debug_snapshot()

    assert snapshot["runtime"]["performance"] == {
        "camera_fps": 5.0,
        "stream_fps": 4.8,
        "analysis_fps": 1.0,
        "motion_fps": 5.0,
        "skipped_analysis_fps": 4.0,
        "uptime_seconds": 12.0,
    }
    assert snapshot["recognition"]["faces"][0]["reason"] == (
        "Known-face score 0.81 reached threshold 0.45."
    )


def test_recognition_reason_explains_known_match():
    reason = recognition_debug.recognition_reason(
        {
            "label": "Mohammad",
            "raw_label": "Mohammad",
            "raw_score": 0.72,
        }
    )

    assert "reached threshold" in reason
    assert "0.72" in reason


def test_recognition_reason_explains_anonymous_match():
    reason = recognition_debug.recognition_reason(
        {
            "label": "Anonymous",
            "raw_label": "Anonymous",
            "raw_score": 0.32,
        }
    )

    assert "No known-face match reached threshold" in reason
    assert "0.32" in reason


def test_recognition_reason_explains_smoothed_label():
    reason = recognition_debug.recognition_reason(
        {
            "label": "Mohammad",
            "raw_label": "Anonymous",
            "raw_score": 0.36,
        }
    )

    assert "held by smoothing" in reason
    assert "Raw frame label was Anonymous" in reason
