from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from app.config import AUTH_PASSWORD, AUTH_USERNAME
from app.routes import auth, dashboard
from app.services import login_throttle, session_store
from app.services.event_log import EventLog
from app.services.review_status import ReviewStatusStore


class FakePipelineStats:
    def snapshot(self):
        return {
            "camera": {
                "active_streams": 1,
                "current_camera_index": 0,
                "frames_read": 20,
                "frames_streamed": 20,
                "failed_reads": 0,
                "consecutive_failed_reads": 0,
                "reconnects": 0,
                "encoding_failures": 0,
            },
            "analysis": {
                "face_analysis_interval_frames": 1,
                "analysis_frames": 20,
                "last_face_count": 1,
                "last_labels": ["Anonymous 1:0.62"],
            },
            "motion": {
                "enabled": True,
                "motion_frames": 20,
                "motion_events": 1,
                "motion_active": True,
                "last_motion_score": 0.12,
                "last_motion_area": 1200,
            },
            "performance": {
                "camera_fps": 10.0,
                "stream_fps": 10.0,
                "analysis_fps": 5.0,
                "motion_fps": 5.0,
                "skipped_analysis_fps": 5.0,
                "uptime_seconds": 30.0,
            },
            "runtime": {},
        }


class FakeStatusEventRecorder:
    def __init__(self):
        self.statuses = []

    def record_if_changed(self, status):
        self.statuses.append(status["status"])
        return None


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret-key")
    app.include_router(auth.router)
    app.include_router(dashboard.router)
    return app


def login(client: TestClient):
    return client.post(
        "/login",
        data={"username": AUTH_USERNAME, "password": AUTH_PASSWORD},
    )


def test_dashboard_summary_redirects_when_anonymous():
    client = TestClient(build_test_app(), follow_redirects=False)

    response = client.get("/api/dashboard-summary")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_dashboard_summary_returns_operational_snapshot(monkeypatch, tmp_path):
    test_event_log = EventLog(database_path=tmp_path / "events.db")
    test_review_status_store = ReviewStatusStore(
        database_path=tmp_path / "review_status.db"
    )
    fake_recorder = FakeStatusEventRecorder()
    monkeypatch.setattr(dashboard, "event_log", test_event_log)
    monkeypatch.setattr(dashboard, "pipeline_stats", FakePipelineStats())
    monkeypatch.setattr(dashboard, "review_status_store", test_review_status_store)
    monkeypatch.setattr(dashboard, "status_event_recorder", fake_recorder)
    session_store.revoke_all()
    login_throttle.clear()

    client = TestClient(build_test_app(), follow_redirects=False)
    login(client)
    test_event_log.add_event("motion", "Motion detected", now=100.0)
    test_event_log.add_event(
        "face",
        "Anonymous 1 detected",
        metadata={"label": "Anonymous 1"},
        now=101.0,
    )
    test_event_log.add_event(
        "alert",
        "Suspicious activity",
        metadata={"label": "Anonymous 1"},
        now=102.0,
    )

    response = client.get("/api/dashboard-summary")

    assert response.status_code == 200
    assert response.json()["headline"]["state"] == "alert"
    assert response.json()["camera"]["active_streams"] == 1
    assert response.json()["analysis"]["face_count"] == 1
    assert response.json()["motion"]["active"] is True
    assert response.json()["alerts"]["latest_alert"]["message"] == "Suspicious activity"
    assert response.json()["review"]["new_items"] == 1
    assert response.json()["review"]["latest_new_item"]["severity"] == "alert"
    assert response.json()["events"][0]["message"] == "Suspicious activity"
    assert fake_recorder.statuses == ["healthy"]
