from fastapi import APIRouter, Depends

from app.config import REVIEW_SOURCE_EVENT_LIMIT
from app.services.activity_review import build_activity_review
from app.services.dashboard_summary import build_dashboard_summary
from app.services.diagnostics import build_diagnostics
from app.services.event_log import event_log
from app.services.pipeline_stats import pipeline_stats
from app.services.review_status import review_status_store
from app.services.status_events import status_event_recorder
from app.utils.auth import require_login


router = APIRouter()


@router.get("/api/dashboard-summary")
async def dashboard_summary(user: str = Depends(require_login)):
    snapshot = pipeline_stats.snapshot()
    diagnostics = build_diagnostics(snapshot)
    status_event_recorder.record_if_changed(
        {
            **diagnostics["system"],
            "checks": diagnostics["checks"],
        }
    )

    events = event_log.latest(limit=10)
    latest_alerts = event_log.latest(limit=1, event_type="alert")
    review_events = event_log.latest(limit=REVIEW_SOURCE_EVENT_LIMIT)
    review = build_activity_review(
        review_events,
        source_event_limit=REVIEW_SOURCE_EVENT_LIMIT,
    )
    review_items = review_status_store.apply_statuses(review["items"])

    return build_dashboard_summary(
        snapshot=snapshot,
        diagnostics=diagnostics,
        events=events,
        latest_alert=latest_alerts[0] if latest_alerts else None,
        review_items=review_items,
    )
