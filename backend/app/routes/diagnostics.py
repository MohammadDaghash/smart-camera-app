from fastapi import APIRouter, Depends

from app.services.diagnostics import build_diagnostics
from app.services.pipeline_stats import pipeline_stats
from app.utils.auth import require_login


router = APIRouter()


@router.get("/api/diagnostics")
async def diagnostics(user: str = Depends(require_login)):
    snapshot = pipeline_stats.snapshot()
    return build_diagnostics(snapshot)
