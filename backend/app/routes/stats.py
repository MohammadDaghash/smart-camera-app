from fastapi import APIRouter, Depends

from app.services.pipeline_stats import pipeline_stats
from app.utils.auth import require_login


router = APIRouter()


@router.get("/stats")
async def stats(user: str = Depends(require_login)):
    return pipeline_stats.snapshot()
