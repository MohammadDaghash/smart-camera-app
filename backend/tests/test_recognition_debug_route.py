from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from app.config import AUTH_PASSWORD, AUTH_USERNAME
from app.routes import auth, recognition_debug
from app.services import login_throttle, session_store


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret-key")
    app.include_router(auth.router)
    app.include_router(recognition_debug.router)
    return app


def login(client: TestClient):
    return client.post(
        "/login",
        data={"username": AUTH_USERNAME, "password": AUTH_PASSWORD},
    )


def test_recognition_debug_redirects_when_anonymous():
    client = TestClient(build_test_app(), follow_redirects=False)

    response = client.get("/api/recognition-debug")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_recognition_debug_returns_snapshot_when_authenticated(monkeypatch):
    monkeypatch.setattr(
        recognition_debug,
        "recognition_debug_snapshot",
        lambda: {
            "settings": {"face_match_threshold": 0.45},
            "runtime": {"active_streams": 1},
            "recognition": {
                "last_face_count": 1,
                "faces": [
                    {
                        "label": "Mohammad",
                        "raw_label": "Anonymous",
                        "reason": "Displayed label is held by smoothing.",
                    }
                ],
            },
            "known_faces": {"loaded_embeddings": 3},
        },
    )
    session_store.revoke_all()
    login_throttle.clear()

    client = TestClient(build_test_app(), follow_redirects=False)
    login(client)

    response = client.get("/api/recognition-debug")

    assert response.status_code == 200
    assert response.json()["recognition"]["last_face_count"] == 1
    assert response.json()["recognition"]["faces"][0]["label"] == "Mohammad"
