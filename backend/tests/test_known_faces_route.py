from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from app.config import AUTH_PASSWORD, AUTH_USERNAME
from app.routes import auth, known_faces
from app.services import login_throttle, session_store


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret-key")
    app.include_router(auth.router)
    app.include_router(known_faces.router)
    return app


def login(client: TestClient):
    return client.post(
        "/login",
        data={"username": AUTH_USERNAME, "password": AUTH_PASSWORD},
    )


def test_known_faces_redirects_when_anonymous():
    client = TestClient(build_test_app(), follow_redirects=False)

    response = client.get("/known-faces")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_known_faces_returns_summary_when_authenticated(monkeypatch):
    monkeypatch.setattr(
        known_faces,
        "get_known_faces_summary",
        lambda: {
            "known_faces_dir": "backend/known_faces",
            "known_faces_dir_exists": True,
            "loaded_embeddings": 5,
            "supported_extensions": [".jpeg", ".jpg", ".png"],
            "people": [
                {
                    "name": "Mohammad",
                    "source_images": 3,
                    "loaded_embeddings": 3,
                },
                {
                    "name": "Omar",
                    "source_images": 2,
                    "loaded_embeddings": 2,
                },
            ],
        },
    )
    session_store.revoke_all()
    login_throttle.clear()

    client = TestClient(build_test_app(), follow_redirects=False)
    login(client)

    response = client.get("/known-faces")

    assert response.status_code == 200
    assert response.json() == {
        "known_faces_dir": "backend/known_faces",
        "known_faces_dir_exists": True,
        "loaded_embeddings": 5,
        "supported_extensions": [".jpeg", ".jpg", ".png"],
        "people": [
            {
                "name": "Mohammad",
                "source_images": 3,
                "loaded_embeddings": 3,
            },
            {
                "name": "Omar",
                "source_images": 2,
                "loaded_embeddings": 2,
            },
        ],
    }
