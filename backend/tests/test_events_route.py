from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from app.config import AUTH_PASSWORD, AUTH_USERNAME
from app.routes import auth, events
from app.services import login_throttle, session_store
from app.services.event_log import EventLog
from app.services.event_snapshots import EventSnapshotStore


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret-key")
    app.include_router(auth.router)
    app.include_router(events.router)
    return app


def login(client: TestClient):
    return client.post(
        "/login",
        data={"username": AUTH_USERNAME, "password": AUTH_PASSWORD},
    )


def test_events_redirects_when_anonymous():
    client = TestClient(build_test_app(), follow_redirects=False)

    response = client.get("/api/events")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_events_returns_filtered_events_when_authenticated(monkeypatch, tmp_path):
    test_event_log = EventLog(database_path=tmp_path / "events.db")
    monkeypatch.setattr(events, "event_log", test_event_log)
    session_store.revoke_all()
    login_throttle.clear()

    client = TestClient(build_test_app(), follow_redirects=False)
    login(client)
    test_event_log.add_event("motion", "Motion detected", now=100.0)
    test_event_log.add_event("face", "Mohammad detected", now=101.0)

    response = client.get("/api/events?type=face&limit=25")

    assert response.status_code == 200
    assert response.json()["filters"] == {
        "limit": 25,
        "type": "face",
        "label": None,
        "start_at": None,
        "end_at": None,
    }
    assert response.json()["retention"] == {
        "max_events": 100,
        "retention_days": None,
    }
    assert response.json()["alerts"] == {
        "enabled": True,
        "anonymous_motion_window_seconds": 30,
        "cooldown_seconds": 60,
    }
    assert response.json()["events"] == [
        {
            "id": 2,
            "type": "face",
            "message": "Mohammad detected",
            "created_at": 101.0,
            "metadata": {},
        }
    ]


def test_events_rejects_unknown_event_type(monkeypatch, tmp_path):
    test_event_log = EventLog(database_path=tmp_path / "events.db")
    monkeypatch.setattr(events, "event_log", test_event_log)
    session_store.revoke_all()
    login_throttle.clear()

    client = TestClient(build_test_app(), follow_redirects=False)
    login(client)

    response = client.get("/api/events?type=unknown")

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Event type must be one of: all, motion, face, alert, system"
    )


def test_events_can_filter_alert_events(monkeypatch, tmp_path):
    test_event_log = EventLog(database_path=tmp_path / "events.db")
    monkeypatch.setattr(events, "event_log", test_event_log)
    session_store.revoke_all()
    login_throttle.clear()

    client = TestClient(build_test_app(), follow_redirects=False)
    login(client)
    test_event_log.add_event("motion", "Motion detected", now=100.0)
    test_event_log.add_event("alert", "Suspicious activity", now=101.0)

    response = client.get("/api/events?type=alert")

    assert response.status_code == 200
    assert response.json()["filters"]["type"] == "alert"
    assert response.json()["events"][0]["type"] == "alert"


def test_events_can_filter_system_events(monkeypatch, tmp_path):
    test_event_log = EventLog(database_path=tmp_path / "events.db")
    monkeypatch.setattr(events, "event_log", test_event_log)
    session_store.revoke_all()
    login_throttle.clear()

    client = TestClient(build_test_app(), follow_redirects=False)
    login(client)
    test_event_log.add_event("motion", "Motion detected", now=100.0)
    test_event_log.add_event("system", "System status changed", now=101.0)

    response = client.get("/api/events?type=system")

    assert response.status_code == 200
    assert response.json()["filters"]["type"] == "system"
    assert response.json()["events"][0]["type"] == "system"


def test_events_can_filter_by_label_and_time(monkeypatch, tmp_path):
    test_event_log = EventLog(database_path=tmp_path / "events.db")
    monkeypatch.setattr(events, "event_log", test_event_log)
    session_store.revoke_all()
    login_throttle.clear()

    client = TestClient(build_test_app(), follow_redirects=False)
    login(client)
    test_event_log.add_event(
        "face",
        "Mohammad detected too early",
        metadata={"label": "Mohammad"},
        now=100.0,
    )
    test_event_log.add_event(
        "face",
        "Mohammad detected",
        metadata={"label": "Mohammad"},
        now=150.0,
    )
    test_event_log.add_event(
        "face",
        "Omar detected",
        metadata={"label": "Omar"},
        now=151.0,
    )

    response = client.get("/api/events?label=moh&start_at=125&end_at=175")

    assert response.status_code == 200
    assert response.json()["filters"]["label"] == "moh"
    assert response.json()["filters"]["start_at"] == 125.0
    assert response.json()["filters"]["end_at"] == 175.0
    assert [event["message"] for event in response.json()["events"]] == [
        "Mohammad detected"
    ]


def test_events_rejects_invalid_time_range(monkeypatch, tmp_path):
    test_event_log = EventLog(database_path=tmp_path / "events.db")
    monkeypatch.setattr(events, "event_log", test_event_log)
    session_store.revoke_all()
    login_throttle.clear()

    client = TestClient(build_test_app(), follow_redirects=False)
    login(client)

    response = client.get("/api/events?start_at=200&end_at=100")

    assert response.status_code == 400
    assert response.json()["detail"] == "start_at must be less than or equal to end_at"


def test_snapshot_redirects_when_anonymous():
    client = TestClient(build_test_app(), follow_redirects=False)

    response = client.get("/api/snapshots/100-1-motion.jpg")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_snapshot_returns_file_when_authenticated(monkeypatch, tmp_path):
    test_snapshot_store = EventSnapshotStore(snapshots_dir=tmp_path)
    monkeypatch.setattr(events, "event_snapshot_store", test_snapshot_store)
    snapshot_path = tmp_path / "100-1-motion.jpg"
    snapshot_path.write_bytes(b"snapshot-bytes")
    session_store.revoke_all()
    login_throttle.clear()

    client = TestClient(build_test_app(), follow_redirects=False)
    login(client)

    response = client.get("/api/snapshots/100-1-motion.jpg")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.content == b"snapshot-bytes"


def test_snapshot_rejects_invalid_filename(monkeypatch, tmp_path):
    test_snapshot_store = EventSnapshotStore(snapshots_dir=tmp_path)
    monkeypatch.setattr(events, "event_snapshot_store", test_snapshot_store)
    session_store.revoke_all()
    login_throttle.clear()

    client = TestClient(build_test_app(), follow_redirects=False)
    login(client)

    response = client.get("/api/snapshots/not-a-generated-name.jpg")

    assert response.status_code == 404
