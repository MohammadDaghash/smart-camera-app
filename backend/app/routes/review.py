from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel

from app.config import REVIEW_SOURCE_EVENT_LIMIT
from app.services.activity_review import (
    build_activity_review,
    filter_review_items_by_label,
)
from app.services.event_log import event_log
from app.services.review_status import REVIEW_STATUSES, review_status_store
from app.utils.auth import require_login


router = APIRouter()


class ReviewStatusUpdate(BaseModel):
    status: str


@router.get("/api/review")
async def activity_review(
    user: str = Depends(require_login),
    limit: int = Query(default=REVIEW_SOURCE_EVENT_LIMIT, ge=1, le=500),
    label: str | None = Query(default=None, min_length=1, max_length=100),
    start_at: float | None = Query(default=None, ge=0),
    end_at: float | None = Query(default=None, ge=0),
):
    if start_at is not None and end_at is not None and start_at > end_at:
        raise HTTPException(
            status_code=400,
            detail="start_at must be less than or equal to end_at",
        )

    source_limit = event_log.max_events if label else limit
    events = event_log.latest(
        limit=source_limit,
        start_at=start_at,
        end_at=end_at,
    )
    review = build_activity_review(events, source_event_limit=source_limit)

    if label:
        review["items"] = filter_review_items_by_label(review["items"], label)

    review["items"] = review_status_store.apply_statuses(review["items"])
    review["settings"]["allowed_statuses"] = REVIEW_STATUSES
    review["filters"] = {
        "limit": limit,
        "label": label,
        "start_at": start_at,
        "end_at": end_at,
    }
    return review


@router.patch("/api/review/{review_id}/status")
async def update_review_status(
    update: ReviewStatusUpdate,
    user: str = Depends(require_login),
    review_id: str = Path(min_length=1, max_length=120),
):
    try:
        return review_status_store.set_status(review_id, update.status)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
