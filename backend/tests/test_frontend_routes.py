from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from app.config import AUTH_PASSWORD, AUTH_USERNAME
from app.routes import auth, frontend
from app.services import login_throttle, session_store


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret-key")
    app.include_router(auth.router)
    app.include_router(frontend.router)
    return app


def login(client: TestClient):
    return client.post(
        "/login",
        data={"username": AUTH_USERNAME, "password": AUTH_PASSWORD},
    )


def test_recognition_debug_page_redirects_when_anonymous():
    client = TestClient(build_test_app(), follow_redirects=False)

    response = client.get("/recognition-debug")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_diagnostics_page_redirects_when_anonymous():
    client = TestClient(build_test_app(), follow_redirects=False)

    response = client.get("/diagnostics")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_settings_page_redirects_when_anonymous():
    client = TestClient(build_test_app(), follow_redirects=False)

    response = client.get("/settings")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_home_page_loads_diagnostics_summary_when_authenticated():
    session_store.revoke_all()
    login_throttle.clear()

    client = TestClient(build_test_app(), follow_redirects=False)
    login(client)

    response = client.get("/")

    assert response.status_code == 200
    assert "Smart Camera Live View" in response.text
    assert "Top action:" in response.text


def test_recognition_debug_page_loads_when_authenticated():
    session_store.revoke_all()
    login_throttle.clear()

    client = TestClient(build_test_app(), follow_redirects=False)
    login(client)

    response = client.get("/recognition-debug")

    assert response.status_code == 200
    assert "Recognition Debug" in response.text


def test_diagnostics_page_loads_when_authenticated():
    session_store.revoke_all()
    login_throttle.clear()

    client = TestClient(build_test_app(), follow_redirects=False)
    login(client)

    response = client.get("/diagnostics")

    assert response.status_code == 200
    assert "Camera Diagnostics" in response.text


def test_settings_page_loads_when_authenticated():
    session_store.revoke_all()
    login_throttle.clear()

    client = TestClient(build_test_app(), follow_redirects=False)
    login(client)

    response = client.get("/settings")

    assert response.status_code == 200
    assert "Camera Settings" in response.text
