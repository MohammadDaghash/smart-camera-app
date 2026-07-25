from app.services.event_log import EventLog, SECONDS_PER_DAY


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


def test_event_log_filters_by_type():
    event_log = EventLog()

    event_log.add_event("motion", "Motion detected", now=100.0)
    event_log.add_event("face", "Mohammad detected", now=101.0)
    event_log.add_event("motion", "Motion detected again", now=102.0)

    events = event_log.latest(event_type="motion")

    assert [event["message"] for event in events] == [
        "Motion detected again",
        "Motion detected",
    ]


def test_event_log_drops_old_events_after_max_size():
    event_log = EventLog(max_events=2)

    event_log.add_event("motion", "Motion 1")
    event_log.add_event("motion", "Motion 2")
    event_log.add_event("motion", "Motion 3")

    events = event_log.latest()

    assert [event["message"] for event in events] == ["Motion 3", "Motion 2"]


def test_event_log_removes_expired_events_after_new_insert():
    event_log = EventLog(retention_seconds=10)

    event_log.add_event("motion", "Old motion", now=100.0)
    event_log.add_event("motion", "New motion", now=111.0)

    events = event_log.latest()

    assert [event["message"] for event in events] == ["New motion"]


def test_event_log_manual_cleanup_reports_deleted_counts():
    event_log = EventLog(retention_seconds=10)

    event_log.add_event("motion", "Old motion", now=100.0)
    event_log.add_event("face", "Old face", now=101.0)

    result = event_log.cleanup(now=112.0)

    assert result["deleted_expired"] == 2
    assert result["deleted_over_limit"] == 0
    assert event_log.latest() == []


def test_event_log_returns_retention_settings():
    event_log = EventLog(max_events=7, retention_seconds=2 * SECONDS_PER_DAY)

    assert event_log.retention_settings() == {
        "max_events": 7,
        "retention_days": 2.0,
    }


def test_event_log_persists_events_between_instances(tmp_path):
    database_path = tmp_path / "events.db"
    first_event_log = EventLog(database_path=database_path)

    first_event_log.add_event(
        "face",
        "Mohammad detected",
        metadata={"label": "Mohammad"},
        now=100.0,
    )
    second_event_log = EventLog(database_path=database_path)

    events = second_event_log.latest()

    assert events[0] == {
        "id": 1,
        "type": "face",
        "message": "Mohammad detected",
        "created_at": 100.0,
        "metadata": {"label": "Mohammad"},
    }


def test_event_log_reset_clears_events_and_resets_ids():
    event_log = EventLog()

    event_log.add_event("motion", "Motion detected")
    event_log.reset()
    event = event_log.add_event("face", "Anonymous detected")

    assert event["id"] == 1
    assert event_log.latest()[0]["message"] == "Anonymous detected"


def test_event_log_skips_same_cooldown_key_inside_window():
    event_log = EventLog()

    first_event = event_log.add_event(
        "motion",
        "Motion detected",
        now=100.0,
        cooldown_key="motion",
        cooldown_seconds=10,
    )
    skipped_event = event_log.add_event(
        "motion",
        "Motion detected",
        now=105.0,
        cooldown_key="motion",
        cooldown_seconds=10,
    )
    next_event = event_log.add_event(
        "motion",
        "Motion detected",
        now=111.0,
        cooldown_key="motion",
        cooldown_seconds=10,
    )

    assert first_event is not None
    assert skipped_event is None
    assert next_event is not None
    assert len(event_log.latest()) == 2


def test_event_log_allows_different_cooldown_keys():
    event_log = EventLog()

    event_log.add_event(
        "face",
        "Mohammad detected",
        now=100.0,
        cooldown_key="face:Mohammad",
        cooldown_seconds=20,
    )
    event_log.add_event(
        "face",
        "Omar detected",
        now=101.0,
        cooldown_key="face:Omar",
        cooldown_seconds=20,
    )

    events = event_log.latest()

    assert [event["message"] for event in events] == [
        "Omar detected",
        "Mohammad detected",
    ]


def test_event_log_reset_clears_cooldowns():
    event_log = EventLog()

    event_log.add_event(
        "motion",
        "Motion detected",
        now=100.0,
        cooldown_key="motion",
        cooldown_seconds=10,
    )
    event_log.reset()
    event = event_log.add_event(
        "motion",
        "Motion detected",
        now=105.0,
        cooldown_key="motion",
        cooldown_seconds=10,
    )

    assert event is not None
    assert event["id"] == 1
