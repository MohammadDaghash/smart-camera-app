from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.config import FRONTEND_FILE
from app.utils.auth import require_login


router = APIRouter()


@router.get("/")
def home(user: str = Depends(require_login)):
    return FileResponse(FRONTEND_FILE)
