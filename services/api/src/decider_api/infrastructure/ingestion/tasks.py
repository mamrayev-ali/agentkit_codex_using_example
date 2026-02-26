from functools import lru_cache

from decider_api.application.ingestion import (
    IngestionJobRequest,
    build_ingestion_job_payload,
    process_ingestion_job,
)
from decider_api.infrastructure.ingestion.celery_app import (
    IngestionTaskQueue,
    QueueProtocol,
    QueueEnqueueResult,
    create_celery_app,
    register_task,
)
from decider_api.infrastructure.ingestion.http_client import RetryPolicy, RetryingHttpClient
from decider_api.infrastructure.ingestion.source_adapters import HttpSourceAdapter
from decider_api.settings import get_settings

INGESTION_TASK_NAME = "decider_api.ingestion.process_job"


@lru_cache(maxsize=1)
def get_retrying_http_client() -> RetryingHttpClient:
    settings = get_settings()
    retry_policy = RetryPolicy(
        timeout_seconds=settings.ingestion_http_timeout_seconds,
        max_retries=settings.ingestion_http_max_retries,
        backoff_seconds=settings.ingestion_http_backoff_seconds,
    )
    return RetryingHttpClient(retry_policy=retry_policy)


@lru_cache(maxsize=1)
def get_source_adapter() -> HttpSourceAdapter:
    return HttpSourceAdapter(http_client=get_retrying_http_client())


def process_ingestion_job_task(job_payload: dict[str, str]) -> dict[str, object]:
    return process_ingestion_job(
        job_payload=job_payload,
        source_adapter=get_source_adapter(),
    )


@lru_cache(maxsize=1)
def get_ingestion_task_queue() -> IngestionTaskQueue:
    settings = get_settings()
    celery_app = create_celery_app(settings)
    celery_task = register_task(
        celery_app=celery_app,
        task_name=INGESTION_TASK_NAME,
        task_handler=process_ingestion_job_task,
    )
    return IngestionTaskQueue(
        settings=settings,
        task_name=INGESTION_TASK_NAME,
        task_handler=process_ingestion_job_task,
        celery_task=celery_task,
    )


def enqueue_ingestion_job(
    *,
    tenant_id: str,
    source_key: str,
    remote_url: str,
    requested_by: str,
    queue: QueueProtocol | None = None,
) -> dict[str, object]:
    request = IngestionJobRequest(
        tenant_id=tenant_id,
        source_key=source_key,
        remote_url=remote_url,
        requested_by=requested_by,
    )
    job_payload = build_ingestion_job_payload(request)

    selected_queue = queue or get_ingestion_task_queue()
    enqueue_result = selected_queue.enqueue(job_payload)
    return _format_enqueue_response(job_payload=job_payload, enqueue_result=enqueue_result)


def _format_enqueue_response(
    *,
    job_payload: dict[str, str],
    enqueue_result: QueueEnqueueResult,
) -> dict[str, object]:
    response: dict[str, object] = {
        "task_id": enqueue_result.task_id,
        "queue_status": enqueue_result.status,
        "job": dict(job_payload),
    }
    if enqueue_result.result is not None:
        response["result"] = dict(enqueue_result.result)
    return response


def reset_ingestion_runtime_state() -> None:
    get_retrying_http_client.cache_clear()
    get_source_adapter.cache_clear()
    get_ingestion_task_queue.cache_clear()
