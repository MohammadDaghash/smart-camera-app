from fastapi import APIRouter, Depends, Query

from app.config import REVIEW_SOURCE_EVENT_LIMIT
from app.services.activity_review import build_activity_review
from app.services.event_log import event_log
from app.utils.auth import require_login


router = APIRouter()


@router.get("/api/review")
async def activity_review(
    user: str = Depends(require_login),
    limit: int = Query(default=REVIEW_SOURCE_EVENT_LIMIT, ge=1, le=500),
):
    events = event_log.latest(limit=limit)
    return build_activity_review(events, source_event_limit=limit)
