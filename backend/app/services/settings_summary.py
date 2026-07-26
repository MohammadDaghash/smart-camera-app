import os

from app import config


def build_settings_summary():
    return {
        "mode": "read_only",
        "restart_required": True,
        "groups": [
            {
                "id": "face_recognition",
                "title": "Face Recognition",
                "settings": [
                    setting(
                        "FACE_MATCH_THRESHOLD",
                        config.FACE_MATCH_THRESHOLD,
                        "float",
                        "Minimum similarity score required for a known label.",
                        "Higher is stricter; lower is more permissive.",
                    ),
                    setting(
                        "FACE_ANALYSIS_INTERVAL_FRAMES",
                        config.FACE_ANALYSIS_INTERVAL_FRAMES,
                        "integer",
                        "How often face recognition runs on incoming frames.",
                        "Higher reduces CPU load but updates labels less often.",
                    ),
                    setting(
                        "FACE_LABEL_SMOOTHING_ENABLED",
                        config.FACE_LABEL_SMOOTHING_ENABLED,
                        "boolean",
                        "Whether labels are stabilized across recent frames.",
                        "Enabled reduces label flicker.",
                    ),
                    setting(
                        "FACE_LABEL_SMOOTHING_HISTORY_SIZE",
                        config.FACE_LABEL_SMOOTHING_HISTORY_SIZE,
                        "integer",
                        "Number of recent observations used for label smoothing.",
                        "Higher is steadier but slower to react.",
                    ),
                    setting(
                        "FACE_LABEL_SMOOTHING_MIN_VOTES",
                        config.FACE_LABEL_SMOOTHING_MIN_VOTES,
                        "integer",
                        "Votes needed before a smoothed label is displayed.",
                        "Higher reduces false switches.",
                    ),
                    setting(
                        "FACE_TRACK_IOU_THRESHOLD",
                        config.FACE_TRACK_IOU_THRESHOLD,
                        "float",
                        "Face-box overlap required to treat detections as the same track.",
                        "Higher requires faces to overlap more closely.",
                    ),
                    setting(
                        "FACE_TRACK_TTL_FRAMES",
                        config.FACE_TRACK_TTL_FRAMES,
                        "integer",
                        "Frames a tracked face can be missing before it expires.",
                        "Higher keeps labels around longer after brief detection gaps.",
                    ),
                ],
            },
            {
                "id": "motion",
                "title": "Motion Detection",
                "settings": [
                    setting(
                        "MOTION_DETECTION_ENABLED",
                        config.MOTION_DETECTION_ENABLED,
                        "boolean",
                        "Whether frame-to-frame motion detection runs.",
                        "Disable only when testing face recognition alone.",
                    ),
                    setting(
                        "MOTION_MIN_AREA",
                        config.MOTION_MIN_AREA,
                        "integer",
                        "Minimum changed pixel area needed before motion counts.",
                        "Higher ignores small noise and tiny movements.",
                    ),
                    setting(
                        "MOTION_SCORE_THRESHOLD",
                        config.MOTION_SCORE_THRESHOLD,
                        "float",
                        "Minimum changed-frame ratio needed before motion counts.",
                        "Higher makes motion detection less sensitive.",
                    ),
                ],
            },
            {
                "id": "events_alerts",
                "title": "Events And Alerts",
                "settings": [
                    setting(
                        "EVENT_MOTION_COOLDOWN_SECONDS",
                        config.EVENT_MOTION_COOLDOWN_SECONDS,
                        "integer",
                        "Minimum seconds between repeated motion events.",
                        "Higher reduces event history noise.",
                    ),
                    setting(
                        "EVENT_FACE_COOLDOWN_SECONDS",
                        config.EVENT_FACE_COOLDOWN_SECONDS,
                        "integer",
                        "Minimum seconds between repeated face-label events.",
                        "Higher reduces duplicate face events.",
                    ),
                    setting(
                        "EVENT_MAX_EVENTS",
                        config.EVENT_MAX_EVENTS,
                        "integer",
                        "Maximum local events retained in SQLite.",
                        "Higher keeps more history on disk.",
                    ),
                    setting(
                        "EVENT_RETENTION_DAYS",
                        config.EVENT_RETENTION_DAYS,
                        "integer",
                        "Maximum age of local events before cleanup.",
                        "Zero disables age-based cleanup.",
                    ),
                    setting(
                        "ALERTS_ENABLED",
                        config.ALERTS_ENABLED,
                        "boolean",
                        "Whether local suspicious-activity alert rules run.",
                        "Disable when tuning motion or recognition noise.",
                    ),
                    setting(
                        "ALERT_ANONYMOUS_MOTION_WINDOW_SECONDS",
                        config.ALERT_ANONYMOUS_MOTION_WINDOW_SECONDS,
                        "integer",
                        "Time window that links anonymous-face and motion events.",
                        "Higher makes alerts easier to trigger.",
                    ),
                    setting(
                        "ALERT_COOLDOWN_SECONDS",
                        config.ALERT_COOLDOWN_SECONDS,
                        "integer",
                        "Minimum seconds between repeated suspicious alerts.",
                        "Higher reduces repeated alert notifications.",
                    ),
                    setting(
                        "REVIEW_EVENT_GAP_SECONDS",
                        config.REVIEW_EVENT_GAP_SECONDS,
                        "integer",
                        "Maximum gap between events before a new review item starts.",
                        "Higher groups more nearby activity into one review item.",
                    ),
                    setting(
                        "REVIEW_SOURCE_EVENT_LIMIT",
                        config.REVIEW_SOURCE_EVENT_LIMIT,
                        "integer",
                        "Recent event count used to build the review page.",
                        "Higher lets review include more history.",
                    ),
                ],
            },
        ],
    }


def setting(env_var, value, value_type, description, effect):
    return {
        "env_var": env_var,
        "value": value,
        "type": value_type,
        "source": "env" if os.getenv(env_var) is not None else "default",
        "description": description,
        "effect": effect,
        "restart_required": True,
    }
