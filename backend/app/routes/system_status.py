from fastapi import APIRouter, Depends

from app.services.pipeline_stats import pipeline_stats
from app.services.system_status import build_system_status
from app.utils.auth import require_login


router = APIRouter()


@router.get("/api/system-status")
async def system_status(user: str = Depends(require_login)):
    snapshot = pipeline_stats.snapshot()
    return build_system_status(snapshot)
