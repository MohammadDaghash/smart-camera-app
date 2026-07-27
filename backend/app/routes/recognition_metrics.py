from fastapi import APIRouter, Depends, Query

from app.config import (
    FACE_MATCH_THRESHOLD,
    RECOGNITION_METRICS_MAX_OBSERVATIONS,
    RECOGNITION_METRICS_SAMPLE_INTERVAL_SECONDS,
)
from app.services.recognition_metrics import recognition_metrics_store
from app.utils.auth import require_login


router = APIRouter()


@router.get("/api/recognition-metrics")
async def recognition_metrics(
    user: str = Depends(require_login),
    limit: int = Query(default=200, ge=1, le=1000),
    label: str | None = Query(default=None, min_length=1, max_length=100),
):
    observations = recognition_metrics_store.latest(limit=limit, label=label)
    timeline = list(reversed(observations))

    return {
        "settings": {
            "face_match_threshold": FACE_MATCH_THRESHOLD,
            "max_observations": RECOGNITION_METRICS_MAX_OBSERVATIONS,
            "sample_interval_seconds": RECOGNITION_METRICS_SAMPLE_INTERVAL_SECONDS,
        },
        "filters": {
            "limit": limit,
            "label": label,
        },
        "summary": recognition_metrics_store.summary(limit=limit, label=label),
        "observations": timeline,
    }
