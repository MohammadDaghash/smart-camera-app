from app.services.alert_rules import AlertRuleEngine, is_anonymous_label
from app.services.event_log import EventLog


def test_is_anonymous_label_matches_current_and_future_anonymous_labels():
    assert is_anonymous_label("Anonymous") is True
    assert is_anonymous_label("Anonymous 1") is True
    assert is_anonymous_label("Mohammad") is False


def test_alert_rule_creates_alert_when_anonymous_face_follows_motion():
    event_log = EventLog()
    alert_rules = AlertRuleEngine(
        event_log=event_log,
        motion_window_seconds=30,
        cooldown_seconds=60,
    )

    motion_event = event_log.add_event("motion", "Motion detected", now=100.0)
    face_event = event_log.add_event(
        "face",
        "Anonymous detected",
        metadata={"label": "Anonymous"},
        now=110.0,
    )
    alert_event = alert_rules.evaluate_event(face_event)

    assert alert_event["type"] == "alert"
    assert alert_event["message"] == "Suspicious activity: anonymous face near motion"
    assert alert_event["metadata"]["face_event_id"] == face_event["id"]
    assert alert_event["metadata"]["motion_event_id"] == motion_event["id"]
    assert alert_event["metadata"]["severity"] == "medium"


def test_alert_rule_creates_alert_when_motion_follows_anonymous_face():
    event_log = EventLog()
    alert_rules = AlertRuleEngine(event_log=event_log, motion_window_seconds=30)

    face_event = event_log.add_event(
        "face",
        "Anonymous detected",
        metadata={"label": "Anonymous 1"},
        now=100.0,
    )
    motion_event = event_log.add_event("motion", "Motion detected", now=120.0)
    alert_event = alert_rules.evaluate_event(motion_event)

    assert alert_event["type"] == "alert"
    assert alert_event["metadata"]["label"] == "Anonymous 1"
    assert alert_event["metadata"]["face_event_id"] == face_event["id"]
    assert alert_event["metadata"]["motion_event_id"] == motion_event["id"]


def test_alert_rule_ignores_known_faces():
    event_log = EventLog()
    alert_rules = AlertRuleEngine(event_log=event_log, motion_window_seconds=30)

    event_log.add_event("motion", "Motion detected", now=100.0)
    face_event = event_log.add_event(
        "face",
        "Mohammad detected",
        metadata={"label": "Mohammad"},
        now=110.0,
    )

    assert alert_rules.evaluate_event(face_event) is None


def test_alert_rule_ignores_events_outside_motion_window():
    event_log = EventLog()
    alert_rules = AlertRuleEngine(event_log=event_log, motion_window_seconds=10)

    event_log.add_event("motion", "Motion detected", now=100.0)
    face_event = event_log.add_event(
        "face",
        "Anonymous detected",
        metadata={"label": "Anonymous"},
        now=111.0,
    )

    assert alert_rules.evaluate_event(face_event) is None


def test_alert_rule_uses_cooldown_to_avoid_duplicate_alerts():
    event_log = EventLog()
    alert_rules = AlertRuleEngine(
        event_log=event_log,
        motion_window_seconds=30,
        cooldown_seconds=60,
    )

    event_log.add_event("motion", "Motion detected", now=100.0)
    first_face_event = event_log.add_event(
        "face",
        "Anonymous detected",
        metadata={"label": "Anonymous"},
        now=110.0,
    )
    second_face_event = event_log.add_event(
        "face",
        "Anonymous detected",
        metadata={"label": "Anonymous"},
        now=120.0,
    )

    first_alert = alert_rules.evaluate_event(first_face_event)
    second_alert = alert_rules.evaluate_event(second_face_event)

    assert first_alert is not None
    assert second_alert is None


def test_alert_rule_can_be_disabled():
    event_log = EventLog()
    alert_rules = AlertRuleEngine(event_log=event_log, enabled=False)

    event_log.add_event("motion", "Motion detected", now=100.0)
    face_event = event_log.add_event(
        "face",
        "Anonymous detected",
        metadata={"label": "Anonymous"},
        now=110.0,
    )

    assert alert_rules.evaluate_event(face_event) is None
