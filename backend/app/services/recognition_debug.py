from app.config import (
    FACE_ANALYSIS_INTERVAL_FRAMES,
    FACE_LABEL_SMOOTHING_ENABLED,
    FACE_LABEL_SMOOTHING_HISTORY_SIZE,
    FACE_LABEL_SMOOTHING_MIN_VOTES,
    FACE_MATCH_THRESHOLD,
    FACE_TRACK_IOU_THRESHOLD,
    FACE_TRACK_TTL_FRAMES,
)
from app.services.pipeline_stats import pipeline_stats


def recognition_debug_snapshot():
    snapshot = pipeline_stats.snapshot()
    analysis = snapshot["analysis"]

    return {
        "settings": {
            "face_match_threshold": FACE_MATCH_THRESHOLD,
            "face_analysis_interval_frames": FACE_ANALYSIS_INTERVAL_FRAMES,
            "label_smoothing": {
                "enabled": FACE_LABEL_SMOOTHING_ENABLED,
                "history_size": FACE_LABEL_SMOOTHING_HISTORY_SIZE,
                "min_votes": FACE_LABEL_SMOOTHING_MIN_VOTES,
                "iou_threshold": FACE_TRACK_IOU_THRESHOLD,
                "ttl_frames": FACE_TRACK_TTL_FRAMES,
            },
        },
        "runtime": {
            "last_analysis_at": snapshot["runtime"]["last_analysis_at"],
            "frames_read": snapshot["camera"]["frames_read"],
            "frames_streamed": snapshot["camera"]["frames_streamed"],
            "active_streams": snapshot["camera"]["active_streams"],
        },
        "recognition": {
            "analysis_frames": analysis["analysis_frames"],
            "last_face_count": analysis["last_face_count"],
            "last_labels": analysis["last_labels"],
            "faces": [
                face_with_reason(face)
                for face in analysis.get("last_faces", [])
            ],
        },
        "known_faces": get_known_faces_summary(),
    }


def face_with_reason(face):
    debug_face = dict(face)
    debug_face["reason"] = recognition_reason(face)
    return debug_face


def recognition_reason(face):
    label = face.get("label", "Anonymous")
    raw_label = face.get("raw_label", label)
    raw_score = float(face.get("raw_score", face.get("score", 0.0)))

    if label != raw_label:
        return (
            "Displayed label is held by smoothing. "
            f"Raw frame label was {raw_label} with score {raw_score:.2f}."
        )

    if label == "Anonymous":
        return (
            f"No known-face match reached threshold {FACE_MATCH_THRESHOLD:.2f}. "
            f"Best raw score was {raw_score:.2f}."
        )

    return (
        f"Known-face score {raw_score:.2f} reached threshold "
        f"{FACE_MATCH_THRESHOLD:.2f}."
    )


def get_known_faces_summary():
    from app.vision.face_recognition import known_faces_summary

    return known_faces_summary()
