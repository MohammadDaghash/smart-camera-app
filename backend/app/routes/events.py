from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.services.alert_rules import alert_rule_engine
from app.services.event_log import event_log
from app.services.event_snapshots import event_snapshot_store
from app.utils.auth import require_login


router = APIRouter()

ALLOWED_EVENT_TYPES = {"motion", "face", "alert"}


@router.get("/api/events")
async def events(
    user: str = Depends(require_login),
    limit: int = Query(default=50, ge=1, le=200),
    event_type: str | None = Query(default=None, alias="type"),
):
    if event_type == "all":
        event_type = None

    if event_type is not None and event_type not in ALLOWED_EVENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Event type must be one of: all, motion, face, alert",
        )

    return {
        "events": event_log.latest(limit=limit, event_type=event_type),
        "filters": {
            "limit": limit,
            "type": event_type or "all",
        },
        "retention": event_log.retention_settings(),
        "alerts": alert_rule_engine.settings(),
    }


@router.get("/api/snapshots/{filename}")
async def snapshot(filename: str, user: str = Depends(require_login)):
    snapshot_path = event_snapshot_store.get_snapshot_path(filename)

    if snapshot_path is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    return FileResponse(snapshot_path, media_type="image/jpeg")
