from app.services.dashboard_summary import build_dashboard_summary


def snapshot(active_streams=1):
    return {
        "camera": {
            "active_streams": active_streams,
            "current_camera_index": 0 if active_streams else None,
            "frames_read": 10 if active_streams else 0,
            "frames_streamed": 10 if active_streams else 0,
            "failed_reads": 0,
            "reconnects": 0,
            "encoding_failures": 0,
        },
        "analysis": {
            "last_face_count": 1 if active_streams else 0,
            "last_labels": ["Mohammad:0.72"] if active_streams else [],
            "analysis_frames": 10 if active_streams else 0,
        },
        "motion": {
            "enabled": True,
            "motion_active": False,
            "motion_events": 0,
            "last_motion_score": 0.0,
            "last_motion_area": 0,
        },
        "performance": {
            "camera_fps": 10.0 if active_streams else 0.0,
            "stream_fps": 10.0 if active_streams else 0.0,
            "analysis_fps": 5.0 if active_streams else 0.0,
            "motion_fps": 5.0 if active_streams else 0.0,
            "skipped_analysis_fps": 5.0 if active_streams else 0.0,
            "uptime_seconds": 12.0,
        },
    }


def diagnostics(status="healthy"):
    return {
        "system": {
            "status": status,
            "message": f"System is {status}.",
        },
        "checks": [],
        "recommendations": ["No action needed."],
    }


def review_item(
    item_id,
    status="new",
    severity="detection",
    summary="Detection review: Mohammad",
):
    return {
        "id": item_id,
        "summary": summary,
        "severity": severity,
        "labels": ["Mohammad"],
        "start_at": 100.0,
        "event_count": 2,
        "review_status": status,
    }


def test_dashboard_summary_counts_review_statuses():
    summary = build_dashboard_summary(
        snapshot=snapshot(),
        diagnostics=diagnostics(),
        events=[],
        latest_alert=None,
        review_items=[
            review_item("review-1-2", status="new"),
            review_item("review-3-4", status="reviewed"),
            review_item("review-5-6", status="false_positive"),
        ],
    )

    assert summary["review"]["total_items"] == 3
    assert summary["review"]["new_items"] == 1
    assert summary["review"]["reviewed_items"] == 1
    assert summary["review"]["false_positive_items"] == 1
    assert summary["review"]["latest_new_item"]["id"] == "review-1-2"


def test_dashboard_summary_prioritizes_alert_headline():
    summary = build_dashboard_summary(
        snapshot=snapshot(),
        diagnostics=diagnostics(),
        events=[],
        latest_alert={"message": "Suspicious activity"},
        review_items=[
            review_item(
                "review-1-2",
                severity="alert",
                summary="Alert review: Anonymous 1 near activity",
            ),
        ],
    )

    assert summary["headline"]["state"] == "alert"
    assert summary["headline"]["title"] == "Suspicious activity needs review"
    assert summary["review"]["alert_items"] == 1


def test_dashboard_summary_uses_system_headline_when_no_review_work():
    summary = build_dashboard_summary(
        snapshot=snapshot(active_streams=0),
        diagnostics=diagnostics(status="idle"),
        events=[],
        latest_alert=None,
        review_items=[],
    )

    assert summary["headline"]["state"] == "idle"
    assert summary["camera"]["active_streams"] == 0
