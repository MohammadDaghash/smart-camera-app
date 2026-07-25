from app.config import (
    ALERT_ANONYMOUS_MOTION_WINDOW_SECONDS,
    ALERT_COOLDOWN_SECONDS,
    ALERTS_ENABLED,
)
from app.services.event_log import event_log


ALERT_RULE_ANONYMOUS_FACE_WITH_MOTION = "anonymous_face_with_motion"


class AlertRuleEngine:
    def __init__(
        self,
        event_log,
        enabled=ALERTS_ENABLED,
        motion_window_seconds=ALERT_ANONYMOUS_MOTION_WINDOW_SECONDS,
        cooldown_seconds=ALERT_COOLDOWN_SECONDS,
    ):
        self.event_log = event_log
        self.enabled = enabled
        self.motion_window_seconds = motion_window_seconds
        self.cooldown_seconds = cooldown_seconds

    def evaluate_event(self, event):
        if not self.enabled or event is None:
            return None

        if event["type"] == "face":
            return self._evaluate_face_event(event)

        if event["type"] == "motion":
            return self._evaluate_motion_event(event)

        return None

    def settings(self):
        return {
            "enabled": self.enabled,
            "anonymous_motion_window_seconds": self.motion_window_seconds,
            "cooldown_seconds": self.cooldown_seconds,
        }

    def _evaluate_face_event(self, face_event):
        label = face_event.get("metadata", {}).get("label", "")

        if not is_anonymous_label(label):
            return None

        motion_event = self._find_recent_motion_event(face_event["created_at"])

        if motion_event is None:
            return None

        return self._create_anonymous_motion_alert(
            created_at=face_event["created_at"],
            anonymous_face_event=face_event,
            motion_event=motion_event,
        )

    def _evaluate_motion_event(self, motion_event):
        anonymous_face_event = self._find_recent_anonymous_face_event(
            motion_event["created_at"]
        )

        if anonymous_face_event is None:
            return None

        return self._create_anonymous_motion_alert(
            created_at=motion_event["created_at"],
            anonymous_face_event=anonymous_face_event,
            motion_event=motion_event,
        )

    def _find_recent_motion_event(self, created_at):
        return self._first_recent_event(
            event_type="motion",
            created_at=created_at,
            predicate=lambda event: True,
        )

    def _find_recent_anonymous_face_event(self, created_at):
        return self._first_recent_event(
            event_type="face",
            created_at=created_at,
            predicate=lambda event: is_anonymous_label(
                event.get("metadata", {}).get("label", "")
            ),
        )

    def _first_recent_event(self, event_type, created_at, predicate):
        window_start = created_at - self.motion_window_seconds

        for event in self.event_log.latest(limit=50, event_type=event_type):
            if event["created_at"] < window_start:
                break

            if event["created_at"] > created_at:
                continue

            if predicate(event):
                return event

        return None

    def _create_anonymous_motion_alert(
        self,
        created_at,
        anonymous_face_event,
        motion_event,
    ):
        label = anonymous_face_event.get("metadata", {}).get("label", "Anonymous")

        return self.event_log.add_event(
            event_type="alert",
            message="Suspicious activity: anonymous face near motion",
            metadata={
                "rule": ALERT_RULE_ANONYMOUS_FACE_WITH_MOTION,
                "severity": "medium",
                "label": label,
                "face_event_id": anonymous_face_event["id"],
                "motion_event_id": motion_event["id"],
                "window_seconds": self.motion_window_seconds,
            },
            now=created_at,
            cooldown_key=f"alert:{ALERT_RULE_ANONYMOUS_FACE_WITH_MOTION}",
            cooldown_seconds=self.cooldown_seconds,
        )


def is_anonymous_label(label):
    return label.strip().lower().startswith("anonymous")


alert_rule_engine = AlertRuleEngine(event_log=event_log)
