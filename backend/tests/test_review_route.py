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
    assert response.json()["filters"] == {
        "limit": 25,
        "label": None,
        "start_at": None,
        "end_at": None,
    }
    assert response.json()["items"][0]["severity"] == "alert"
    assert response.json()["items"][0]["labels"] == ["Anonymous 1"]


def test_review_filters_by_label_without_losing_group_context(monkeypatch, tmp_path):
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
        "face",
        "Omar detected",
        metadata={"label": "Omar"},
        now=250.0,
    )

    response = client.get("/api/review?label=anonymous&limit=1")

    assert response.status_code == 200
    assert response.json()["settings"]["source_event_limit"] == 100
    item = response.json()["items"][0]
    assert item["labels"] == ["Anonymous 1"]
    assert item["types"] == ["face", "motion"]
    assert [event["type"] for event in item["events"]] == ["motion", "face"]


def test_review_filters_by_time(monkeypatch, tmp_path):
    test_event_log = EventLog(database_path=tmp_path / "events.db")
    monkeypatch.setattr(review, "event_log", test_event_log)
    session_store.revoke_all()
    login_throttle.clear()

    client = TestClient(build_test_app(), follow_redirects=False)
    login(client)
    test_event_log.add_event("motion", "Too old", now=100.0)
    test_event_log.add_event("motion", "In range", now=150.0)

    response = client.get("/api/review?start_at=125&end_at=175")

    assert response.status_code == 200
    assert response.json()["items"][0]["events"][0]["message"] == "In range"


def test_review_rejects_invalid_time_range(monkeypatch, tmp_path):
    test_event_log = EventLog(database_path=tmp_path / "events.db")
    monkeypatch.setattr(review, "event_log", test_event_log)
    session_store.revoke_all()
    login_throttle.clear()

    client = TestClient(build_test_app(), follow_redirects=False)
    login(client)

    response = client.get("/api/review?start_at=200&end_at=100")

    assert response.status_code == 400
    assert response.json()["detail"] == "start_at must be less than or equal to end_at"
