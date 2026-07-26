from fastapi import APIRouter, Depends

from app.services.settings_summary import build_settings_summary
from app.utils.auth import require_login


router = APIRouter()


@router.get("/api/settings")
async def settings(user: str = Depends(require_login)):
    return build_settings_summary()
