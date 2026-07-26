from app.services.event_log import EventLog
from app.services.status_events import StatusEventRecorder, attention_checks


def status(status_name, checks=None):
    return {
        "status": status_name,
        "checks": checks or [],
    }


def test_status_event_recorder_sets_baseline_without_event():
    event_log = EventLog()
    recorder = StatusEventRecorder(event_log)

    event = recorder.record_if_changed(status("idle"))

    assert event is None
    assert event_log.latest() == []


def test_status_event_recorder_records_status_transition():
    event_log = EventLog()
    recorder = StatusEventRecorder(event_log)

    recorder.record_if_changed(status("idle"))
    event = recorder.record_if_changed(status("degraded"))

    assert event["type"] == "system"
    assert event["message"] == "System status changed from idle to degraded"
    assert event["metadata"]["previous_status"] == "idle"
    assert event["metadata"]["new_status"] == "degraded"


def test_status_event_recorder_skips_same_status():
    event_log = EventLog()
    recorder = StatusEventRecorder(event_log)

    recorder.record_if_changed(status("healthy"))
    recorder.record_if_changed(status("healthy"))

    assert event_log.latest() == []


def test_attention_checks_only_include_problem_checks():
    checks = attention_checks(
        status(
            "degraded",
            checks=[
                {"name": "stream", "status": "healthy", "message": "ok"},
                {"name": "camera_read", "status": "degraded", "message": "slow"},
                {"name": "encoding", "status": "error", "message": "failed"},
            ],
        )
    )

    assert checks == [
        {"name": "camera_read", "status": "degraded", "message": "slow"},
        {"name": "encoding", "status": "error", "message": "failed"},
    ]
