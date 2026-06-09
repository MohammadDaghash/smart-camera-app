from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.vision.face_recognition import identity_store


router = APIRouter()


class PromoteIdentityRequest(BaseModel):
    name: str


@router.get("/identities")
async def list_identities():
    return {
        "identities": identity_store.list_identities(),
    }


@router.post("/identities/{identity_id}/promote")
async def promote_identity(identity_id: str, request: PromoteIdentityRequest):
    try:
        identity = identity_store.promote_identity(identity_id, request.name)
    except KeyError:
        raise HTTPException(status_code=404, detail="Identity was not found") from None
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from None

    return {
        "identity": identity,
    }
