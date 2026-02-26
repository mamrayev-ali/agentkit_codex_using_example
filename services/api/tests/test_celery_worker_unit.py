from decider_api.infrastructure.ingestion.celery_app import create_celery_app
from decider_api.infrastructure.ingestion.tasks import INGESTION_TASK_NAME
from decider_api.infrastructure.ingestion.worker import get_celery_worker_app
from decider_api.settings import AppSettings


def setup_function() -> None:
    get_celery_worker_app.cache_clear()


def teardown_function() -> None:
    get_celery_worker_app.cache_clear()


def test_create_celery_app_applies_config() -> None:
    settings = AppSettings(
        ingestion_task_always_eager=False,
        ingestion_task_broker_url="memory://",
        ingestion_task_backend_url="cache+memory://",
    )

    celery_app = create_celery_app(settings)

    assert celery_app is not None
    assert celery_app.conf.task_always_eager is False
    assert celery_app.conf.broker_url == "memory://"


def test_worker_entrypoint_registers_ingestion_task() -> None:
    celery_app = get_celery_worker_app()

    assert INGESTION_TASK_NAME in celery_app.tasks
