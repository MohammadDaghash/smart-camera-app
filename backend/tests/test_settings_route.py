from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from app.config import AUTH_PASSWORD, AUTH_USERNAME
from app.routes import auth, settings
from app.services import login_throttle, session_store


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret-key")
    app.include_router(auth.router)
    app.include_router(settings.router)
    return app


def login(client: TestClient):
    return client.post(
        "/login",
        data={"username": AUTH_USERNAME, "password": AUTH_PASSWORD},
    )


def test_settings_redirects_when_anonymous():
    client = TestClient(build_test_app(), follow_redirects=False)

    response = client.get("/api/settings")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_settings_returns_read_only_tuning_values_when_authenticated():
    session_store.revoke_all()
    login_throttle.clear()

    client = TestClient(build_test_app(), follow_redirects=False)
    login(client)

    response = client.get("/api/settings")

    assert response.status_code == 200
    assert response.json()["mode"] == "read_only"
    assert response.json()["groups"][0]["id"] == "face_recognition"
