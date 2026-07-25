from app.services.event_log import EventLog


def test_event_log_returns_latest_events_first():
    event_log = EventLog()

    event_log.add_event("motion", "Motion detected", now=100.0)
    event_log.add_event("face", "Mohammad detected", now=101.0)

    events = event_log.latest()

    assert [event["message"] for event in events] == [
        "Mohammad detected",
        "Motion detected",
    ]
    assert events[0]["id"] == 2
    assert events[0]["created_at"] == 101.0


def test_event_log_respects_limit():
    event_log = EventLog()

    event_log.add_event("motion", "Motion 1")
    event_log.add_event("motion", "Motion 2")
    event_log.add_event("motion", "Motion 3")

    events = event_log.latest(limit=2)

    assert [event["message"] for event in events] == ["Motion 3", "Motion 2"]


def test_event_log_drops_old_events_after_max_size():
    event_log = EventLog(max_events=2)

    event_log.add_event("motion", "Motion 1")
    event_log.add_event("motion", "Motion 2")
    event_log.add_event("motion", "Motion 3")

    events = event_log.latest()

    assert [event["message"] for event in events] == ["Motion 3", "Motion 2"]


def test_event_log_reset_clears_events_and_resets_ids():
    event_log = EventLog()

    event_log.add_event("motion", "Motion detected")
    event_log.reset()
    event = event_log.add_event("face", "Anonymous detected")

    assert event["id"] == 1
    assert event_log.latest()[0]["message"] == "Anonymous detected"
