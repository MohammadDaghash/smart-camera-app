from fastapi import HTTPException, Request
from starlette.status import HTTP_303_SEE_OTHER

from app.services import session_store


SESSION_USER_KEY = "user"
SESSION_ID_KEY = "sid"
LOGIN_PATH = "/login"


def _valid_user(request: Request) -> str | None:
    user = request.session.get(SESSION_USER_KEY)
    session_id = request.session.get(SESSION_ID_KEY)

    if user and session_id and session_store.is_valid(session_id):
        return user

    return None


def is_authenticated(request: Request) -> bool:
    return _valid_user(request) is not None


def login_user(request: Request, username: str) -> None:
    session_id = session_store.create_session()
    request.session[SESSION_USER_KEY] = username
    request.session[SESSION_ID_KEY] = session_id


def logout_user(request: Request) -> None:
    session_id = request.session.get(SESSION_ID_KEY)

    if session_id:
        session_store.revoke(session_id)

    request.session.clear()


def require_login(request: Request) -> str:
    user = _valid_user(request)

    if not user:
        raise HTTPException(
            status_code=HTTP_303_SEE_OTHER,
            headers={"Location": LOGIN_PATH},
        )

    return user
