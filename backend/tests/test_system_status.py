from app.services.system_status import build_system_status


def snapshot(
    active_streams=1,
    frames_read=10,
    frames_streamed=10,
    consecutive_failed_reads=0,
    encoding_failures=0,
    camera_fps=10.0,
    stream_fps=10.0,
    analysis_fps=5.0,
):
    return {
        "camera": {
            "active_streams": active_streams,
            "frames_read": frames_read,
            "frames_streamed": frames_streamed,
            "consecutive_failed_reads": consecutive_failed_reads,
            "encoding_failures": encoding_failures,
        },
        "analysis": {
            "face_analysis_interval_frames": 1,
        },
        "performance": {
            "camera_fps": camera_fps,
            "stream_fps": stream_fps,
            "analysis_fps": analysis_fps,
        },
    }


def test_system_status_is_idle_without_active_stream():
    status = build_system_status(snapshot(active_streams=0))

    assert status["status"] == "idle"
    assert status["checks"][0]["name"] == "stream"


def test_system_status_is_healthy_when_pipeline_metrics_are_good():
    status = build_system_status(snapshot())

    assert status["status"] == "healthy"
    assert status["message"] == "Camera pipeline is healthy."


def test_system_status_is_error_when_active_stream_has_no_camera_fps():
    status = build_system_status(snapshot(camera_fps=0.0, stream_fps=0.0))

    assert status["status"] == "error"
    assert any(
        check["name"] == "camera_read" and check["status"] == "error"
        for check in status["checks"]
    )


def test_system_status_is_degraded_for_failed_reads():
    status = build_system_status(snapshot(consecutive_failed_reads=2))

    assert status["status"] == "degraded"
    assert any(
        check["name"] == "camera_read" and check["status"] == "degraded"
        for check in status["checks"]
    )


def test_system_status_is_degraded_when_stream_fps_lags_camera_fps():
    status = build_system_status(snapshot(camera_fps=10.0, stream_fps=2.0))

    assert status["status"] == "degraded"
    assert any(
        check["name"] == "stream_output" and check["status"] == "degraded"
        for check in status["checks"]
    )
