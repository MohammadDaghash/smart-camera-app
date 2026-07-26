from app.services.system_status import build_system_status


CHECK_RECOMMENDATIONS = {
    "stream": {
        "idle": "Open the live view or recognition debug page to start consuming /video.",
        "healthy": "No stream action needed.",
    },
    "camera_read": {
        "error": "Run /camera-test, check webcam permissions, and close other apps using the camera.",
        "degraded": "Watch the stream for a few seconds. If failures continue, reconnect the camera.",
        "healthy": "Camera reads are working.",
    },
    "stream_output": {
        "error": "Refresh the browser and confirm the /video image is not broken.",
        "degraded": "The stream is slower than capture. Reduce load or lower analysis frequency later.",
        "healthy": "Browser stream output is working.",
    },
    "encoding": {
        "degraded": "Frame JPEG encoding failed at least once. Check CPU load and camera format.",
        "healthy": "Frame encoding is working.",
    },
    "face_analysis": {
        "degraded": "Confirm recognition models loaded and the analysis loop is still running.",
        "healthy": "Face analysis is running.",
    },
}


def build_diagnostics(snapshot):
    system = build_system_status(snapshot)
    checks = [diagnostic_check(check) for check in system["checks"]]
    recommendations = recommended_actions(system["status"], checks)

    return {
        "system": {
            "status": system["status"],
            "message": system["message"],
        },
        "checks": checks,
        "metrics": diagnostic_metrics(snapshot),
        "recommendations": recommendations,
    }


def diagnostic_check(check):
    status = check["status"]
    name = check["name"]
    recommendation = CHECK_RECOMMENDATIONS.get(name, {}).get(
        status,
        "Inspect the related pipeline metric and backend terminal logs.",
    )

    return {
        "name": name,
        "label": check_label(name),
        "status": status,
        "message": check["message"],
        "recommendation": recommendation,
    }


def diagnostic_metrics(snapshot):
    camera = snapshot.get("camera", {})
    analysis = snapshot.get("analysis", {})
    motion = snapshot.get("motion", {})
    performance = snapshot.get("performance", {})

    return {
        "active_streams": camera.get("active_streams", 0),
        "camera_index": camera.get("current_camera_index"),
        "frames_read": camera.get("frames_read", 0),
        "frames_streamed": camera.get("frames_streamed", 0),
        "failed_reads": camera.get("failed_reads", 0),
        "consecutive_failed_reads": camera.get("consecutive_failed_reads", 0),
        "reconnects": camera.get("reconnects", 0),
        "encoding_failures": camera.get("encoding_failures", 0),
        "analysis_frames": analysis.get("analysis_frames", 0),
        "last_face_count": analysis.get("last_face_count", 0),
        "motion_active": motion.get("motion_active", False),
        "motion_events": motion.get("motion_events", 0),
        "camera_fps": performance.get("camera_fps", 0.0),
        "stream_fps": performance.get("stream_fps", 0.0),
        "analysis_fps": performance.get("analysis_fps", 0.0),
        "motion_fps": performance.get("motion_fps", 0.0),
        "uptime_seconds": performance.get("uptime_seconds", 0.0),
    }


def recommended_actions(status, checks):
    if status == "healthy":
        return ["No action needed. The local camera pipeline is healthy."]

    if status == "idle":
        return ["Open the live view to start the camera pipeline."]

    return [
        check["recommendation"]
        for check in checks
        if check["status"] in {"degraded", "error"}
    ]


def check_label(name):
    labels = {
        "stream": "Browser stream",
        "camera_read": "Camera reads",
        "stream_output": "MJPEG output",
        "encoding": "Frame encoding",
        "face_analysis": "Face analysis",
    }

    return labels.get(name, name.replace("_", " ").title())
