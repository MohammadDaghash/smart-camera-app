from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.config import (
    AUTH_USING_DEFAULT_CREDENTIALS,
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE_SECONDS,
    SESSION_SECRET,
    SESSION_SECRET_IS_EPHEMERAL,
)
from app.routes import auth, camera, frontend, health
from app.utils.logging import logger


app = FastAPI(title="Smart Camera App")

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie=SESSION_COOKIE_NAME,
    max_age=SESSION_MAX_AGE_SECONDS,
    same_site="lax",
    https_only=False,
)

app.include_router(auth.router)
app.include_router(frontend.router)
app.include_router(health.router)
app.include_router(camera.router)


if AUTH_USING_DEFAULT_CREDENTIALS:
    logger.warning(
        "Using default admin/admin login. Set AUTH_USERNAME and AUTH_PASSWORD in "
        "backend/.env before exposing this server on a network."
    )

if SESSION_SECRET_IS_EPHEMERAL:
    logger.warning(
        "SESSION_SECRET is not set; using a random key. Logins will not survive a "
        "restart. Set SESSION_SECRET in backend/.env for stable sessions."
    )
