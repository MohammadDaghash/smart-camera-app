from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.event_log import event_log
from app.utils.auth import require_login


router = APIRouter()

ALLOWED_EVENT_TYPES = {"motion", "face"}


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
            detail="Event type must be one of: all, motion, face",
        )

    return {
        "events": event_log.latest(limit=limit, event_type=event_type),
        "filters": {
            "limit": limit,
            "type": event_type or "all",
        },
    }
