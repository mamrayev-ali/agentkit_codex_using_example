from functools import lru_cache
from typing import Any

from decider_api.infrastructure.ingestion.celery_app import create_celery_app, register_task
from decider_api.infrastructure.ingestion.tasks import (
    INGESTION_TASK_NAME,
    process_ingestion_job_task,
)
from decider_api.settings import get_settings


@lru_cache(maxsize=1)
def get_celery_worker_app() -> Any:
    settings = get_settings()
    celery_app = create_celery_app(settings)
    if celery_app is None:
        raise RuntimeError(
            "Celery is not installed. Install backend dependencies before starting worker."
        )

    register_task(
        celery_app=celery_app,
        task_name=INGESTION_TASK_NAME,
        task_handler=process_ingestion_job_task,
    )
    return celery_app


celery_app = get_celery_worker_app()
