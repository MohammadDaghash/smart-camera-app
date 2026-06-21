from fastapi import Depends, FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

import pytest

from app.config import (
    AUTH_PASSWORD,
    AUTH_USERNAME,
    LOGIN_MAX_ATTEMPTS,
    SESSION_MAX_AGE_SECONDS,
)
from app.routes import auth, frontend, health
from app.services import login_throttle, session_store
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


@pytest.fixture(autouse=True)
def _reset_auth_state():
    session_store.revoke_all()
    login_throttle.clear()
    yield
    session_store.revoke_all()
    login_throttle.clear()


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


def test_server_side_revocation_blocks_a_still_valid_cookie(client: TestClient):
    login(client, AUTH_USERNAME, AUTH_PASSWORD)
    assert client.get("/protected-probe").status_code == 200

    # Simulates logout-from-elsewhere or a server restart: the client still holds
    # a structurally valid signed cookie, but the server no longer honors it.
    session_store.revoke_all()

    assert client.get("/protected-probe").status_code == 303


def test_login_lockout_after_repeated_failures(client: TestClient):
    for _ in range(LOGIN_MAX_ATTEMPTS):
        rejected = login(client, AUTH_USERNAME, "wrong-password")
        assert rejected.headers["location"] == "/login?error=1"

    # Even correct credentials are blocked while locked out.
    blocked = login(client, AUTH_USERNAME, AUTH_PASSWORD)
    assert blocked.status_code == 303
    assert blocked.headers["location"] == "/login?error=locked"
    assert client.get("/protected-probe").status_code == 303


def test_session_store_validates_revokes_and_expires():
    session_id = session_store.create_session(now=1000.0)
    assert session_store.is_valid(session_id, now=1000.0) is True
    assert session_store.is_valid(session_id, now=1000.0 + SESSION_MAX_AGE_SECONDS + 1) is False

    fresh = session_store.create_session(now=2000.0)
    session_store.revoke(fresh)
    assert session_store.is_valid(fresh, now=2000.0) is False


def test_login_throttle_locks_then_clears_on_success():
    key = "unit-test-key"

    for _ in range(LOGIN_MAX_ATTEMPTS):
        assert login_throttle.lockout_remaining(key) == 0.0
        login_throttle.record_failure(key)

    assert login_throttle.lockout_remaining(key) > 0.0

    login_throttle.record_success(key)
    assert login_throttle.lockout_remaining(key) == 0.0
