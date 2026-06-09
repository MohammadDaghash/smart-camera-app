from fastapi import FastAPI

from app.routes import camera, frontend, health, identities


app = FastAPI(title="Smart Camera App")

app.include_router(frontend.router)
app.include_router(health.router)
app.include_router(camera.router)
app.include_router(identities.router)
