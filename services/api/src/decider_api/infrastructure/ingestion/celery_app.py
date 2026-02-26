from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import uuid4

from decider_api.settings import AppSettings

try:
    from celery import Celery
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    Celery = None  # type: ignore[assignment]


TaskHandler = Callable[[dict[str, str]], dict[str, object]]


@dataclass(frozen=True)
class QueueEnqueueResult:
    task_id: str
    status: str
    result: dict[str, object] | None


class QueueProtocol(Protocol):
    def enqueue(self, job_payload: Mapping[str, str]) -> QueueEnqueueResult:
        ...


class CeleryAsyncResultProtocol(Protocol):
    id: str


class CeleryTaskProtocol(Protocol):
    def delay(self, job_payload: Mapping[str, str]) -> CeleryAsyncResultProtocol:
        ...


class IngestionTaskQueue:
    def __init__(
        self,
        *,
        settings: AppSettings,
        task_name: str,
        task_handler: TaskHandler,
        celery_task: CeleryTaskProtocol | None,
    ) -> None:
        self._settings = settings
        self._task_name = task_name
        self._task_handler = task_handler
        self._celery_task = celery_task

    def enqueue(self, job_payload: Mapping[str, str]) -> QueueEnqueueResult:
        payload = dict(job_payload)

        if self._settings.ingestion_task_always_eager:
            task_id = f"eager-{uuid4().hex[:12]}"
            result = self._task_handler(payload)
            return QueueEnqueueResult(task_id=task_id, status="success", result=result)

        if self._celery_task is None:
            raise RuntimeError(
                "Celery is not installed. Install `celery` or enable eager mode via "
                "DECIDER_INGESTION_TASK_ALWAYS_EAGER=true."
            )

        async_result = self._celery_task.delay(payload)
        return QueueEnqueueResult(
            task_id=str(async_result.id),
            status="queued",
            result=None,
        )


def create_celery_app(settings: AppSettings) -> Any | None:
    if Celery is None:
        return None

    celery_app = Celery(
        "decider_api.ingestion",
        broker=settings.ingestion_task_broker_url,
        backend=settings.ingestion_task_backend_url,
    )
    celery_app.conf.update(
        task_always_eager=settings.ingestion_task_always_eager,
        task_eager_propagates=True,
    )
    return celery_app


def register_task(
    *,
    celery_app: Any | None,
    task_name: str,
    task_handler: TaskHandler,
) -> CeleryTaskProtocol | None:
    if celery_app is None:
        return None

    @celery_app.task(name=task_name)
    def _task(job_payload: dict[str, str]) -> dict[str, object]:
        return task_handler(job_payload)

    return _task
