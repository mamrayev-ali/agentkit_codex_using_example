from fastapi import FastAPI

from decider_api.api.routes.health import router as health_router
from decider_api.api.routes.v1 import router as v1_router
from decider_api.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.public_api_version,
    )
    app.include_router(health_router)
    app.include_router(v1_router, prefix=settings.public_api_prefix)
    return app


app = create_app()
