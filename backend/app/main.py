from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.core.config import settings
from app.core.constants import APP_VERSION
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version=APP_VERSION,
    debug=settings.DEBUG,
)

app.include_router(health_router)


@app.get("/")
async def root():
    return {
        "message": "Personal Health Assistant API",
        "version": APP_VERSION,
    }