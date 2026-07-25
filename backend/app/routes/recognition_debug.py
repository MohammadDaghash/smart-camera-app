from fastapi import APIRouter, Depends

from app.services.recognition_debug import recognition_debug_snapshot
from app.utils.auth import require_login


router = APIRouter()


@router.get("/api/recognition-debug")
async def recognition_debug(user: str = Depends(require_login)):
    return recognition_debug_snapshot()
