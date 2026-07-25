from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from app.config import AUTH_PASSWORD, AUTH_USERNAME
from app.routes import auth, stats
from app.services import login_throttle, session_store
from app.services.event_log import EventLog
from app.services.pipeline_stats import pipeline_stats


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret-key")
    app.include_router(auth.router)
    app.include_router(stats.router)
    return app


def login(client: TestClient):
    return client.post(
        "/login",
        data={"username": AUTH_USERNAME, "password": AUTH_PASSWORD},
    )


def test_stats_redirects_when_anonymous():
    client = TestClient(build_test_app(), follow_redirects=False)

    response = client.get("/stats")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_stats_returns_pipeline_snapshot_when_authenticated(monkeypatch, tmp_path):
    test_event_log = EventLog(database_path=tmp_path / "events.db")
    monkeypatch.setattr(stats, "event_log", test_event_log)
    session_store.revoke_all()
    login_throttle.clear()
    pipeline_stats.reset()

    client = TestClient(build_test_app(), follow_redirects=False)
    login(client)
    pipeline_stats.record_frame_read(camera_index=0, now=100.0)
    pipeline_stats.record_frame_streamed()
    test_event_log.add_event("motion", "Motion detected", now=101.0)
    test_event_log.add_event("alert", "Suspicious activity", now=102.0)

    response = client.get("/stats")

    assert response.status_code == 200
    assert response.json()["camera"]["frames_streamed"] == 1
    assert "motion" in response.json()
    assert response.json()["events"][0]["message"] == "Suspicious activity"
    assert response.json()["alerts"]["latest_alert"]["message"] == "Suspicious activity"
    assert response.json()["system"]["status"] == "idle"
