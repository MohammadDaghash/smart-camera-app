from fastapi import APIRouter, Depends

from app.services.event_log import event_log
from app.services.pipeline_stats import pipeline_stats
from app.utils.auth import require_login


router = APIRouter()


@router.get("/stats")
async def stats(user: str = Depends(require_login)):
    snapshot = pipeline_stats.snapshot()
    snapshot["events"] = event_log.latest(limit=10)
    latest_alerts = event_log.latest(limit=1, event_type="alert")
    snapshot["alerts"] = {
        "latest_alert": latest_alerts[0] if latest_alerts else None,
    }

    return snapshot
