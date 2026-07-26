from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.config import (
    DIAGNOSTICS_FILE,
    EVENTS_FILE,
    FRONTEND_FILE,
    RECOGNITION_DEBUG_FILE,
    REVIEW_FILE,
    SETTINGS_FILE,
)
from app.utils.auth import require_login


router = APIRouter()


@router.get("/")
def home(user: str = Depends(require_login)):
    return FileResponse(FRONTEND_FILE)


@router.get("/history")
def history(user: str = Depends(require_login)):
    return FileResponse(EVENTS_FILE)


@router.get("/review")
def activity_review(user: str = Depends(require_login)):
    return FileResponse(REVIEW_FILE)


@router.get("/recognition-debug")
def recognition_debug(user: str = Depends(require_login)):
    return FileResponse(RECOGNITION_DEBUG_FILE)


@router.get("/diagnostics")
def diagnostics(user: str = Depends(require_login)):
    return FileResponse(DIAGNOSTICS_FILE)


@router.get("/settings")
def settings(user: str = Depends(require_login)):
    return FileResponse(SETTINGS_FILE)
