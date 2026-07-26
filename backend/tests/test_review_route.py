from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from app.config import AUTH_PASSWORD, AUTH_USERNAME
from app.routes import auth, review
from app.services import login_throttle, session_store
from app.services.event_log import EventLog


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret-key")
    app.include_router(auth.router)
    app.include_router(review.router)
    return app


def login(client: TestClient):
    return client.post(
        "/login",
        data={"username": AUTH_USERNAME, "password": AUTH_PASSWORD},
    )


def test_review_redirects_when_anonymous():
    client = TestClient(build_test_app(), follow_redirects=False)

    response = client.get("/api/review")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_review_returns_grouped_items_when_authenticated(monkeypatch, tmp_path):
    test_event_log = EventLog(database_path=tmp_path / "events.db")
    monkeypatch.setattr(review, "event_log", test_event_log)
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

    response = client.get("/api/review?limit=25")

    assert response.status_code == 200
    assert response.json()["settings"]["source_event_limit"] == 25
    assert response.json()["items"][0]["severity"] == "alert"
    assert response.json()["items"][0]["labels"] == ["Anonymous 1"]
