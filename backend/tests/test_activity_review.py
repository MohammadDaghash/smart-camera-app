from app.services.activity_review import build_activity_review


def event(event_id, event_type, created_at, message=None, metadata=None):
    return {
        "id": event_id,
        "type": event_type,
        "message": message or f"{event_type} event",
        "created_at": created_at,
        "metadata": metadata or {},
    }


def test_activity_review_groups_nearby_events():
    review = build_activity_review(
        [
            event(2, "face", 110.0, metadata={"label": "Anonymous 1"}),
            event(1, "motion", 100.0),
        ],
        event_gap_seconds=30,
    )

    assert len(review["items"]) == 1
    item = review["items"][0]
    assert item["severity"] == "detection"
    assert item["types"] == ["face", "motion"]
    assert item["labels"] == ["Anonymous 1"]
    assert item["event_count"] == 2
    assert item["summary"] == "Detection review: Anonymous 1 with motion"


def test_activity_review_splits_events_outside_gap():
    review = build_activity_review(
        [
            event(1, "motion", 100.0),
            event(2, "face", 250.0, metadata={"label": "Mohammad"}),
        ],
        event_gap_seconds=30,
    )

    assert len(review["items"]) == 2
    assert review["items"][0]["labels"] == ["Mohammad"]
    assert review["items"][1]["types"] == ["motion"]


def test_activity_review_alert_severity_wins():
    review = build_activity_review(
        [
            event(1, "motion", 100.0),
            event(2, "face", 101.0, metadata={"label": "Anonymous 1"}),
            event(3, "alert", 102.0, metadata={"label": "Anonymous 1"}),
        ],
        event_gap_seconds=30,
    )

    item = review["items"][0]
    assert item["severity"] == "alert"
    assert item["types"] == ["alert", "face", "motion"]
    assert item["summary"] == "Alert review: Anonymous 1 near activity"


def test_activity_review_system_only_item_is_info():
    review = build_activity_review(
        [event(1, "system", 100.0, message="System status changed")],
        event_gap_seconds=30,
    )

    item = review["items"][0]
    assert item["severity"] == "info"
    assert item["summary"] == "System review: status changed"
