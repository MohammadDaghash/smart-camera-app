from fastapi import HTTPException, Request
from starlette.status import HTTP_303_SEE_OTHER


SESSION_USER_KEY = "user"
LOGIN_PATH = "/login"


def is_authenticated(request: Request) -> bool:
    return bool(request.session.get(SESSION_USER_KEY))


def login_user(request: Request, username: str) -> None:
    request.session[SESSION_USER_KEY] = username


def logout_user(request: Request) -> None:
    request.session.pop(SESSION_USER_KEY, None)


def require_login(request: Request) -> str:
    user = request.session.get(SESSION_USER_KEY)

    if not user:
        raise HTTPException(
            status_code=HTTP_303_SEE_OTHER,
            headers={"Location": LOGIN_PATH},
        )

    return user
