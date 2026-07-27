KNOWN_REVIEW_STATUSES = ("new", "reviewed", "false_positive")
KNOWN_SEVERITIES = ("alert", "detection", "info")


def build_dashboard_summary(snapshot, diagnostics, events, latest_alert, review_items):
    review_summary = summarize_review_items(review_items)

    return {
        "headline": build_headline(
            diagnostics.get("system", {}),
            latest_alert,
            review_summary,
        ),
        "system": diagnostics.get("system", {}),
        "top_action": first_recommendation(diagnostics),
        "camera": camera_summary(snapshot),
        "analysis": analysis_summary(snapshot),
        "motion": motion_summary(snapshot),
        "performance": performance_summary(snapshot),
        "alerts": {
            "latest_alert": latest_alert,
        },
        "review": review_summary,
        "events": events,
    }


def summarize_review_items(review_items):
    status_counts = {status: 0 for status in KNOWN_REVIEW_STATUSES}
    severity_counts = {severity: 0 for severity in KNOWN_SEVERITIES}
    latest_new_item = None

    for item in review_items:
        status = item.get("review_status", "new")
        severity = item.get("severity", "info")

        if status not in status_counts:
            status = "new"

        if severity not in severity_counts:
            severity = "info"

        status_counts[status] += 1
        severity_counts[severity] += 1

        if status == "new" and latest_new_item is None:
            latest_new_item = compact_review_item(item)

    return {
        "total_items": len(review_items),
        "status_counts": status_counts,
        "severity_counts": severity_counts,
        "new_items": status_counts["new"],
        "reviewed_items": status_counts["reviewed"],
        "false_positive_items": status_counts["false_positive"],
        "alert_items": severity_counts["alert"],
        "latest_new_item": latest_new_item,
    }


def compact_review_item(item):
    return {
        "id": item.get("id"),
        "summary": item.get("summary"),
        "severity": item.get("severity"),
        "labels": item.get("labels", []),
        "start_at": item.get("start_at"),
        "event_count": item.get("event_count", 0),
        "review_status": item.get("review_status", "new"),
    }


def build_headline(system, latest_alert, review_summary):
    status = system.get("status", "idle")

    if latest_alert and review_summary["new_items"] > 0:
        return {
            "state": "alert",
            "title": "Suspicious activity needs review",
            "detail": latest_alert.get("message", "Suspicious activity detected"),
        }

    if review_summary["new_items"] > 0:
        return {
            "state": "review",
            "title": "New activity needs review",
            "detail": f"{review_summary['new_items']} new review item(s).",
        }

    if status == "healthy":
        return {
            "state": "healthy",
            "title": "Camera pipeline is healthy",
            "detail": system.get("message", "No action needed."),
        }

    return {
        "state": status,
        "title": system.get("message", "Camera pipeline status unavailable."),
        "detail": "Open diagnostics for the next local action.",
    }


def first_recommendation(diagnostics):
    recommendations = diagnostics.get("recommendations") or []

    if not recommendations:
        return "No action needed."

    return recommendations[0]


def camera_summary(snapshot):
    camera = snapshot.get("camera", {})

    return {
        "active_streams": camera.get("active_streams", 0),
        "current_camera_index": camera.get("current_camera_index"),
        "frames_read": camera.get("frames_read", 0),
        "frames_streamed": camera.get("frames_streamed", 0),
        "failed_reads": camera.get("failed_reads", 0),
        "reconnects": camera.get("reconnects", 0),
        "encoding_failures": camera.get("encoding_failures", 0),
    }


def analysis_summary(snapshot):
    analysis = snapshot.get("analysis", {})

    return {
        "face_count": analysis.get("last_face_count", 0),
        "labels": analysis.get("last_labels", []),
        "analysis_frames": analysis.get("analysis_frames", 0),
    }


def motion_summary(snapshot):
    motion = snapshot.get("motion", {})

    return {
        "enabled": motion.get("enabled", True),
        "active": motion.get("motion_active", False),
        "events": motion.get("motion_events", 0),
        "score": motion.get("last_motion_score", 0.0),
        "area": motion.get("last_motion_area", 0),
    }


def performance_summary(snapshot):
    performance = snapshot.get("performance", {})

    return {
        "camera_fps": performance.get("camera_fps", 0.0),
        "stream_fps": performance.get("stream_fps", 0.0),
        "analysis_fps": performance.get("analysis_fps", 0.0),
        "motion_fps": performance.get("motion_fps", 0.0),
        "skipped_analysis_fps": performance.get("skipped_analysis_fps", 0.0),
        "uptime_seconds": performance.get("uptime_seconds", 0.0),
    }
