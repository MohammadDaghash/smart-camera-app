from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.config import CAMERA_INDEXES
from app.services.camera_service import generate_frames, open_working_camera, release_camera
from app.utils.auth import require_login


router = APIRouter()


@router.get("/camera-test")
async def camera_test(user: str = Depends(require_login)):
    camera, index, error = open_working_camera()

    if camera is None:
        return {
            "camera_available": False,
            "working_index": None,
            "tested_indexes": CAMERA_INDEXES,
            "message": error,
        }

    release_camera(camera, index)

    return {
        "camera_available": True,
        "working_index": index,
        "tested_indexes": CAMERA_INDEXES,
        "message": f"Camera is available on index {index}",
    }


@router.get("/video")
async def video(user: str = Depends(require_login)):
    camera, index, error = open_working_camera()

    if camera is None:
        raise HTTPException(status_code=503, detail=error)

    return StreamingResponse(
        generate_frames(camera, index),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
