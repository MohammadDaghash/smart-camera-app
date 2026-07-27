from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from app.config import AUTH_PASSWORD, AUTH_USERNAME
from app.routes import auth, recognition_metrics
from app.services import login_throttle, session_store
from app.services.recognition_metrics import RecognitionMetricsStore


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret-key")
    app.include_router(auth.router)
    app.include_router(recognition_metrics.router)
    return app


def login(client: TestClient):
    return client.post(
        "/login",
        data={"username": AUTH_USERNAME, "password": AUTH_PASSWORD},
    )


def test_recognition_metrics_redirects_when_anonymous():
    client = TestClient(build_test_app(), follow_redirects=False)

    response = client.get("/api/recognition-metrics")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_recognition_metrics_returns_observations_when_authenticated(
    monkeypatch,
    tmp_path,
):
    store = RecognitionMetricsStore(
        database_path=tmp_path / "recognition_metrics.db",
        sample_interval_seconds=0,
    )
    monkeypatch.setattr(recognition_metrics, "recognition_metrics_store", store)
    session_store.revoke_all()
    login_throttle.clear()

    client = TestClient(build_test_app(), follow_redirects=False)
    login(client)
    store.add_observations(
        [
            {
                "track_id": 1,
                "label": "Mohammad",
                "score": 0.82,
                "raw_label": "Mohammad",
                "raw_score": 0.82,
            }
        ],
        now=100.0,
    )

    response = client.get("/api/recognition-metrics?limit=50")

    assert response.status_code == 200
    assert response.json()["filters"] == {
        "limit": 50,
        "label": None,
    }
    assert response.json()["summary"]["known_observations"] == 1
    assert response.json()["observations"][0]["label"] == "Mohammad"
