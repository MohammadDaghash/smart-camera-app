from app.services.pipeline_stats import PipelineStats


def test_pipeline_stats_tracks_camera_and_analysis_state():
    stats = PipelineStats(face_analysis_interval_frames=3)

    stats.mark_stream_started(camera_index=1)
    stats.record_frame_read(camera_index=1, now=100.0)
    stats.record_frame_streamed()
    stats.record_frame_read_failed(camera_index=1)
    stats.record_reconnect(camera_index=2)
    stats.record_analysis(face_count=1, labels=["Mohammad:0.81"], now=101.0)
    stats.record_encoding_failure()

    snapshot = stats.snapshot()

    assert snapshot["camera"] == {
        "active_streams": 1,
        "current_camera_index": 2,
        "frames_read": 1,
        "frames_streamed": 1,
        "failed_reads": 1,
        "consecutive_failed_reads": 0,
        "reconnects": 1,
        "encoding_failures": 1,
    }
    assert snapshot["analysis"] == {
        "face_analysis_interval_frames": 3,
        "analysis_frames": 1,
        "last_face_count": 1,
        "last_labels": ["Mohammad:0.81"],
    }
    assert snapshot["runtime"]["last_frame_at"] == 100.0
    assert snapshot["runtime"]["last_analysis_at"] == 101.0


def test_pipeline_stats_marks_stream_stopped_without_negative_count():
    stats = PipelineStats(face_analysis_interval_frames=1)

    stats.mark_stream_stopped()
    stats.mark_stream_started(camera_index=0)
    stats.mark_stream_stopped()

    assert stats.snapshot()["camera"]["active_streams"] == 0
