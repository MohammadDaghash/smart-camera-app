from fastapi import Depends, FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

import pytest

from app.config import AUTH_PASSWORD, AUTH_USERNAME
from app.routes import auth, frontend, health
from app.utils.auth import require_login


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret-key")
    app.include_router(auth.router)
    app.include_router(frontend.router)
    app.include_router(health.router)

    @app.get("/protected-probe")
    def protected_probe(user: str = Depends(require_login)):
        return PlainTextResponse(user)

    return app


@pytest.fixture
def client() -> TestClient:
    return TestClient(build_test_app(), follow_redirects=False)


def login(client: TestClient, username: str, password: str):
    return client.post(
        "/login",
        data={"username": username, "password": password},
    )


def test_health_is_public(client: TestClient):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_page_is_public(client: TestClient):
    response = client.get("/login")

    assert response.status_code == 200
    assert "Sign in" in response.text


def test_protected_route_redirects_when_anonymous(client: TestClient):
    response = client.get("/protected-probe")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_home_redirects_when_anonymous(client: TestClient):
    response = client.get("/")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_login_with_valid_credentials_grants_access(client: TestClient):
    response = login(client, AUTH_USERNAME, AUTH_PASSWORD)

    assert response.status_code == 303
    assert response.headers["location"] == "/"

    probe = client.get("/protected-probe")
    assert probe.status_code == 200
    assert probe.text == AUTH_USERNAME

    home = client.get("/")
    assert home.status_code == 200


def test_login_with_invalid_credentials_is_rejected(client: TestClient):
    response = login(client, AUTH_USERNAME, "wrong-password")

    assert response.status_code == 303
    assert response.headers["location"] == "/login?error=1"

    probe = client.get("/protected-probe")
    assert probe.status_code == 303


def test_login_with_unknown_user_is_rejected(client: TestClient):
    response = login(client, "not-a-real-user", AUTH_PASSWORD)

    assert response.status_code == 303
    assert response.headers["location"] == "/login?error=1"


def test_logout_clears_session(client: TestClient):
    login(client, AUTH_USERNAME, AUTH_PASSWORD)
    assert client.get("/protected-probe").status_code == 200

    logout = client.get("/logout")
    assert logout.status_code == 303
    assert logout.headers["location"] == "/login"

    assert client.get("/protected-probe").status_code == 303


def test_login_page_redirects_when_authenticated(client: TestClient):
    login(client, AUTH_USERNAME, AUTH_PASSWORD)

    response = client.get("/login")
    assert response.status_code == 303
    assert response.headers["location"] == "/"
