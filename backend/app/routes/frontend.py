from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.config import FRONTEND_FILE


router = APIRouter()


@router.get("/")
def home():
    return FileResponse(FRONTEND_FILE)
