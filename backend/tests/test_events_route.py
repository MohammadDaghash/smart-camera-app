from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from app.config import AUTH_PASSWORD, AUTH_USERNAME
from app.routes import auth, events
from app.services import login_throttle, session_store
from app.services.event_log import EventLog


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
    assert response.json()["filters"] == {"limit": 25, "type": "face"}
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
    assert response.json()["detail"] == "Event type must be one of: all, motion, face"
