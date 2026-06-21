from fastapi import APIRouter, Form, Request
from fastapi.responses import FileResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER

from app.config import LOGIN_FILE
from app.services.auth_service import verify_credentials
from app.utils.auth import is_authenticated, login_user, logout_user
from app.utils.logging import logger


router = APIRouter()


@router.get("/login")
def login_page(request: Request):
    if is_authenticated(request):
        return RedirectResponse("/", status_code=HTTP_303_SEE_OTHER)

    return FileResponse(LOGIN_FILE)


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if verify_credentials(username, password):
        login_user(request, username)
        logger.info("User '%s' logged in", username)
        return RedirectResponse("/", status_code=HTTP_303_SEE_OTHER)

    logger.warning("Failed login attempt for user '%s'", username)
    return RedirectResponse("/login?error=1", status_code=HTTP_303_SEE_OTHER)


@router.get("/logout")
def logout(request: Request):
    logout_user(request)
    return RedirectResponse("/login", status_code=HTTP_303_SEE_OTHER)
