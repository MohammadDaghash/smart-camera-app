from fastapi import APIRouter, Depends

from app.services.diagnostics import build_diagnostics
from app.services.pipeline_stats import pipeline_stats
from app.services.status_events import status_event_recorder
from app.utils.auth import require_login


router = APIRouter()


@router.get("/api/diagnostics")
async def diagnostics(user: str = Depends(require_login)):
    snapshot = pipeline_stats.snapshot()
    diagnostics = build_diagnostics(snapshot)
    status_event_recorder.record_if_changed(
        {
            **diagnostics["system"],
            "checks": diagnostics["checks"],
        }
    )
    return diagnostics
