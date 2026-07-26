from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from app.config import AUTH_PASSWORD, AUTH_USERNAME
from app.routes import auth, diagnostics
from app.services import login_throttle, session_store


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret-key")
    app.include_router(auth.router)
    app.include_router(diagnostics.router)
    return app


def login(client: TestClient):
    return client.post(
        "/login",
        data={"username": AUTH_USERNAME, "password": AUTH_PASSWORD},
    )


def test_diagnostics_redirects_when_anonymous():
    client = TestClient(build_test_app(), follow_redirects=False)

    response = client.get("/api/diagnostics")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_diagnostics_returns_snapshot_when_authenticated(monkeypatch):
    class FakePipelineStats:
        def snapshot(self):
            return {
                "camera": {"active_streams": 0},
                "analysis": {},
                "motion": {},
                "performance": {},
            }

    monkeypatch.setattr(diagnostics, "pipeline_stats", FakePipelineStats())
    session_store.revoke_all()
    login_throttle.clear()

    client = TestClient(build_test_app(), follow_redirects=False)
    login(client)

    response = client.get("/api/diagnostics")

    assert response.status_code == 200
    assert response.json()["system"]["status"] == "idle"
    assert response.json()["recommendations"][0].startswith("Open the live view")
