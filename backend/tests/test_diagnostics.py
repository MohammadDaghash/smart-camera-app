from app.services.diagnostics import build_diagnostics


def snapshot(active_streams=1, camera_fps=10.0, stream_fps=10.0):
    return {
        "camera": {
            "active_streams": active_streams,
            "current_camera_index": 0 if active_streams else None,
            "frames_read": 10 if active_streams else 0,
            "frames_streamed": 10 if active_streams else 0,
            "failed_reads": 0,
            "consecutive_failed_reads": 0,
            "reconnects": 0,
            "encoding_failures": 0,
        },
        "analysis": {
            "face_analysis_interval_frames": 1,
            "analysis_frames": 10 if active_streams else 0,
            "last_face_count": 1 if active_streams else 0,
        },
        "motion": {
            "motion_active": False,
            "motion_events": 0,
        },
        "performance": {
            "camera_fps": camera_fps,
            "stream_fps": stream_fps,
            "analysis_fps": 5.0 if active_streams else 0.0,
            "motion_fps": 5.0 if active_streams else 0.0,
            "uptime_seconds": 12.0,
        },
    }


def test_diagnostics_returns_idle_recommendation_without_stream():
    diagnostics = build_diagnostics(snapshot(active_streams=0))

    assert diagnostics["system"]["status"] == "idle"
    assert diagnostics["recommendations"] == [
        "Open the live view to start the camera pipeline."
    ]


def test_diagnostics_returns_metric_summary():
    diagnostics = build_diagnostics(snapshot())

    assert diagnostics["metrics"]["active_streams"] == 1
    assert diagnostics["metrics"]["camera_fps"] == 10.0
    assert diagnostics["metrics"]["last_face_count"] == 1


def test_diagnostics_recommends_action_for_slow_stream():
    diagnostics = build_diagnostics(snapshot(camera_fps=10.0, stream_fps=2.0))

    assert diagnostics["system"]["status"] == "degraded"
    assert any(
        "stream is slower" in recommendation.lower()
        for recommendation in diagnostics["recommendations"]
    )
