from app.config import RECONNECT_AFTER_FAILURES


STATUS_PRIORITY = {
    "healthy": 0,
    "idle": 1,
    "degraded": 2,
    "error": 3,
}


def build_system_status(snapshot):
    camera = snapshot.get("camera", {})
    analysis = snapshot.get("analysis", {})
    performance = snapshot.get("performance", {})
    active_streams = camera.get("active_streams", 0)

    if active_streams <= 0:
        return {
            "status": "idle",
            "message": "No active camera stream. Open the live view to start the pipeline.",
            "checks": [
                {
                    "name": "stream",
                    "status": "idle",
                    "message": "No browser is currently consuming /video.",
                }
            ],
        }

    checks = [
        {
            "name": "stream",
            "status": "healthy",
            "message": f"{active_streams} active stream(s).",
        },
        camera_read_check(camera, performance),
        stream_output_check(camera, performance),
        encoding_check(camera),
        analysis_check(camera, analysis, performance),
    ]
    overall_status = max((check["status"] for check in checks), key=STATUS_PRIORITY.get)

    return {
        "status": overall_status,
        "message": status_message(overall_status),
        "checks": checks,
    }


def camera_read_check(camera, performance):
    camera_fps = performance.get("camera_fps", 0.0)
    consecutive_failed_reads = camera.get("consecutive_failed_reads", 0)

    if camera_fps <= 0:
        return {
            "name": "camera_read",
            "status": "error",
            "message": "Stream is active, but no camera frames are being read.",
        }

    if consecutive_failed_reads > 0:
        return {
            "name": "camera_read",
            "status": "degraded",
            "message": (
                f"{consecutive_failed_reads}/{RECONNECT_AFTER_FAILURES} consecutive "
                "camera reads failed."
            ),
        }

    return {
        "name": "camera_read",
        "status": "healthy",
        "message": f"Camera is reading at {camera_fps:.2f} FPS.",
    }


def stream_output_check(camera, performance):
    camera_fps = performance.get("camera_fps", 0.0)
    stream_fps = performance.get("stream_fps", 0.0)

    if camera.get("frames_read", 0) > 0 and stream_fps <= 0:
        return {
            "name": "stream_output",
            "status": "error",
            "message": "Frames are being read, but none are being streamed.",
        }

    if camera_fps >= 1.0 and stream_fps < camera_fps * 0.5:
        return {
            "name": "stream_output",
            "status": "degraded",
            "message": (
                f"Stream FPS ({stream_fps:.2f}) is far below camera FPS "
                f"({camera_fps:.2f})."
            ),
        }

    return {
        "name": "stream_output",
        "status": "healthy",
        "message": f"Browser stream is sending {stream_fps:.2f} FPS.",
    }


def encoding_check(camera):
    encoding_failures = camera.get("encoding_failures", 0)

    if encoding_failures > 0:
        return {
            "name": "encoding",
            "status": "degraded",
            "message": f"{encoding_failures} frame encoding failure(s) recorded.",
        }

    return {
        "name": "encoding",
        "status": "healthy",
        "message": "No frame encoding failures recorded.",
    }


def analysis_check(camera, analysis, performance):
    frames_read = camera.get("frames_read", 0)
    interval = analysis.get("face_analysis_interval_frames", 1)
    analysis_fps = performance.get("analysis_fps", 0.0)

    if frames_read >= interval and analysis_fps <= 0:
        return {
            "name": "face_analysis",
            "status": "degraded",
            "message": "Camera is reading frames, but no recent face analysis is recorded.",
        }

    return {
        "name": "face_analysis",
        "status": "healthy",
        "message": f"Face analysis is running at {analysis_fps:.2f} FPS.",
    }


def status_message(status):
    if status == "healthy":
        return "Camera pipeline is healthy."

    if status == "degraded":
        return "Camera pipeline is running with warnings."

    if status == "error":
        return "Camera pipeline needs attention."

    return "Camera pipeline is idle."
