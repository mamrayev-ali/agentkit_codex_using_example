from fastapi import FastAPI

from decider_api.api.routes.health import router as health_router
from decider_api.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(health_router)
    return app


app = create_app()
