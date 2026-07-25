from fastapi import APIRouter, Depends

from app.utils.auth import require_login


router = APIRouter()


def get_known_faces_summary():
    from app.vision.face_recognition import known_faces_summary

    return known_faces_summary()


@router.get("/known-faces")
async def known_faces(user: str = Depends(require_login)):
    return get_known_faces_summary()
