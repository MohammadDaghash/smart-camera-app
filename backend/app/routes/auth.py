from fastapi import APIRouter, Form, Request
from fastapi.responses import FileResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER

from app.config import LOGIN_FILE
from app.services import login_throttle
from app.services.auth_service import verify_credentials
from app.utils.auth import is_authenticated, login_user, logout_user
from app.utils.logging import logger


router = APIRouter()


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


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
    client_key = _client_key(request)
    locked_for = login_throttle.lockout_remaining(client_key)

    if locked_for > 0:
        logger.warning(
            "Login blocked for %s; locked for %.0fs", client_key, locked_for
        )
        return RedirectResponse("/login?error=locked", status_code=HTTP_303_SEE_OTHER)

    if verify_credentials(username, password):
        login_throttle.record_success(client_key)
        login_user(request, username)
        logger.info("User '%s' logged in from %s", username, client_key)
        return RedirectResponse("/", status_code=HTTP_303_SEE_OTHER)

    login_throttle.record_failure(client_key)
    logger.warning("Failed login attempt for user '%s' from %s", username, client_key)
    return RedirectResponse("/login?error=1", status_code=HTTP_303_SEE_OTHER)


@router.get("/logout")
def logout(request: Request):
    logout_user(request)
    return RedirectResponse("/login", status_code=HTTP_303_SEE_OTHER)
