from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from app.config import AUTH_PASSWORD, AUTH_USERNAME
from app.routes import auth, system_status
from app.services import login_throttle, session_store


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
    app.include_router(system_status.router)
    return app


def login(client: TestClient):
    return client.post(
        "/login",
        data={"username": AUTH_USERNAME, "password": AUTH_PASSWORD},
    )


def test_system_status_redirects_when_anonymous():
    client = TestClient(build_test_app(), follow_redirects=False)

    response = client.get("/api/system-status")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_system_status_returns_status_when_authenticated(monkeypatch):
    fake_recorder = FakeStatusEventRecorder()

    class FakePipelineStats:
        def snapshot(self):
            return {
                "camera": {
                    "active_streams": 0,
                },
                "analysis": {},
                "performance": {},
            }

    monkeypatch.setattr(system_status, "pipeline_stats", FakePipelineStats())
    monkeypatch.setattr(system_status, "status_event_recorder", fake_recorder)
    session_store.revoke_all()
    login_throttle.clear()

    client = TestClient(build_test_app(), follow_redirects=False)
    login(client)

    response = client.get("/api/system-status")

    assert response.status_code == 200
    assert response.json()["status"] == "idle"
    assert fake_recorder.statuses == ["idle"]
