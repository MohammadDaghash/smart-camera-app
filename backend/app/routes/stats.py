from fastapi import APIRouter, Depends

from app.services.event_log import event_log
from app.services.pipeline_stats import pipeline_stats
from app.services.status_events import status_event_recorder
from app.services.system_status import build_system_status
from app.utils.auth import require_login


router = APIRouter()


@router.get("/stats")
async def stats(user: str = Depends(require_login)):
    snapshot = pipeline_stats.snapshot()
    snapshot["system"] = build_system_status(snapshot)
    status_event_recorder.record_if_changed(snapshot["system"])
    snapshot["events"] = event_log.latest(limit=10)
    latest_alerts = event_log.latest(limit=1, event_type="alert")
    snapshot["alerts"] = {
        "latest_alert": latest_alerts[0] if latest_alerts else None,
    }

    return snapshot
