from app.services.pipeline_stats import PipelineStats


def test_pipeline_stats_tracks_camera_and_analysis_state():
    stats = PipelineStats(face_analysis_interval_frames=3)

    stats.mark_stream_started(camera_index=1)
    stats.record_frame_read(camera_index=1, now=100.0)
    stats.record_frame_streamed()
    stats.record_frame_read_failed(camera_index=1)
    stats.record_reconnect(camera_index=2)
    stats.record_analysis(
        face_count=1,
        labels=["Mohammad:0.81"],
        faces=[
            {
                "track_id": 1,
                "box": (1, 2, 10, 20),
                "label": "Mohammad",
                "score": 0.81234,
                "raw_label": "Anonymous",
                "raw_score": 0.43219,
            }
        ],
        now=101.0,
    )
    stats.record_motion(
        motion_detected=True,
        motion_score=0.12,
        motion_area=4200,
        now=102.0,
    )
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
        "last_faces": [
            {
                "track_id": 1,
                "box": [1, 2, 10, 20],
                "label": "Mohammad",
                "score": 0.8123,
                "raw_label": "Anonymous",
                "raw_score": 0.4322,
            }
        ],
    }
    assert snapshot["motion"] == {
        "enabled": True,
        "motion_frames": 1,
        "motion_events": 1,
        "motion_active": True,
        "last_motion_score": 0.12,
        "last_motion_area": 4200,
    }
    assert snapshot["runtime"]["last_frame_at"] == 100.0
    assert snapshot["runtime"]["last_analysis_at"] == 101.0
    assert snapshot["runtime"]["last_motion_at"] == 102.0


def test_pipeline_stats_marks_stream_stopped_without_negative_count():
    stats = PipelineStats(face_analysis_interval_frames=1)

    stats.mark_stream_stopped()
    stats.mark_stream_started(camera_index=0)
    stats.mark_stream_stopped()

    assert stats.snapshot()["camera"]["active_streams"] == 0


def test_pipeline_stats_counts_motion_events_on_new_motion_only():
    stats = PipelineStats(face_analysis_interval_frames=1)

    stats.record_motion(motion_detected=True, motion_score=0.1, motion_area=1000)
    stats.record_motion(motion_detected=True, motion_score=0.2, motion_area=2000)
    stats.record_motion(motion_detected=False, motion_score=0.0, motion_area=0)
    stats.record_motion(motion_detected=True, motion_score=0.3, motion_area=3000)

    snapshot = stats.snapshot()

    assert snapshot["motion"]["motion_frames"] == 4
    assert snapshot["motion"]["motion_events"] == 2
    assert snapshot["motion"]["motion_active"] is True
    assert snapshot["motion"]["last_motion_score"] == 0.3
    assert snapshot["motion"]["last_motion_area"] == 3000
