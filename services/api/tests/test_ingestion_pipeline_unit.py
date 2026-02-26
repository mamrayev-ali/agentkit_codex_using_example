import pytest

from decider_api.application.ingestion import (
    IngestionJobRequest,
    build_ingestion_job_payload,
    process_ingestion_job,
)
from decider_api.domain.source_adapter import SourceFetchResult
from decider_api.infrastructure.ingestion.celery_app import (
    IngestionTaskQueue,
    QueueEnqueueResult,
)
from decider_api.infrastructure.ingestion.tasks import enqueue_ingestion_job
from decider_api.settings import AppSettings


class FakeSourceAdapter:
    def fetch(self, *, source_key: str, remote_url: str) -> SourceFetchResult:
        return SourceFetchResult(
            source_key=source_key,
            requested_url=remote_url,
            status_code=200,
            content_type="application/json",
            body=b'{"ok": true}',
        )


class StubQueue:
    def __init__(self) -> None:
        self.last_payload: dict[str, str] | None = None

    def enqueue(self, job_payload: dict[str, str]) -> QueueEnqueueResult:
        self.last_payload = dict(job_payload)
        return QueueEnqueueResult(task_id="task-1", status="queued", result=None)


class FakeAsyncResult:
    def __init__(self, *, task_id: str) -> None:
        self.id = task_id


class FakeCeleryTask:
    def __init__(self) -> None:
        self.last_payload: dict[str, str] | None = None

    def delay(self, job_payload: dict[str, str]) -> FakeAsyncResult:
        self.last_payload = dict(job_payload)
        return FakeAsyncResult(task_id="celery-task-42")


def test_build_ingestion_job_payload_validates_and_normalizes_fields() -> None:
    request = IngestionJobRequest(
        tenant_id=" acme ",
        source_key=" gov-registry ",
        remote_url="https://example.com/api/company",
        requested_by=" analyst-1 ",
    )

    payload = build_ingestion_job_payload(request)

    assert payload["job_id"].startswith("ingestion-")
    assert payload["tenant_id"] == "acme"
    assert payload["source_key"] == "gov-registry"
    assert payload["requested_by"] == "analyst-1"


def test_build_ingestion_job_payload_rejects_unsafe_remote_url() -> None:
    request = IngestionJobRequest(
        tenant_id="acme",
        source_key="gov-registry",
        remote_url="http://127.0.0.1/admin",
        requested_by="analyst-1",
    )

    with pytest.raises(ValueError, match="blocked IP range"):
        build_ingestion_job_payload(request)


def test_process_ingestion_job_returns_metadata_only_response() -> None:
    payload = {
        "job_id": "ingestion-1",
        "tenant_id": "acme",
        "source_key": "gov-registry",
        "remote_url": "https://example.com/api/company",
        "requested_by": "analyst-1",
    }

    result = process_ingestion_job(
        job_payload=payload,
        source_adapter=FakeSourceAdapter(),
    )

    assert result["job_id"] == "ingestion-1"
    assert result["status"] == "completed"
    assert result["http_status"] == 200
    assert result["content_length"] == len(b'{"ok": true}')


def test_ingestion_queue_processes_job_in_eager_mode() -> None:
    settings = AppSettings(ingestion_task_always_eager=True)

    queue = IngestionTaskQueue(
        settings=settings,
        task_name="decider_api.ingestion.process_job",
        task_handler=lambda payload: {
            "job_id": payload["job_id"],
            "status": "completed",
        },
        celery_task=None,
    )

    result = queue.enqueue(
        {
            "job_id": "ingestion-1",
            "tenant_id": "acme",
            "source_key": "gov-registry",
            "remote_url": "https://example.com/api/company",
            "requested_by": "analyst-1",
        }
    )

    assert result.task_id.startswith("eager-")
    assert result.status == "success"
    assert result.result == {"job_id": "ingestion-1", "status": "completed"}


def test_ingestion_queue_requires_celery_when_not_eager() -> None:
    settings = AppSettings(ingestion_task_always_eager=False)

    queue = IngestionTaskQueue(
        settings=settings,
        task_name="decider_api.ingestion.process_job",
        task_handler=lambda payload: {"job_id": payload["job_id"]},
        celery_task=None,
    )

    with pytest.raises(RuntimeError, match="Celery is not installed"):
        queue.enqueue(
            {
                "job_id": "ingestion-1",
                "tenant_id": "acme",
                "source_key": "gov-registry",
                "remote_url": "https://example.com/api/company",
                "requested_by": "analyst-1",
            }
        )


def test_ingestion_queue_uses_celery_task_when_not_eager() -> None:
    settings = AppSettings(ingestion_task_always_eager=False)
    fake_celery_task = FakeCeleryTask()

    queue = IngestionTaskQueue(
        settings=settings,
        task_name="decider_api.ingestion.process_job",
        task_handler=lambda payload: {"job_id": payload["job_id"]},
        celery_task=fake_celery_task,
    )

    result = queue.enqueue(
        {
            "job_id": "ingestion-1",
            "tenant_id": "acme",
            "source_key": "gov-registry",
            "remote_url": "https://example.com/api/company",
            "requested_by": "analyst-1",
        }
    )

    assert result.task_id == "celery-task-42"
    assert result.status == "queued"
    assert result.result is None
    assert fake_celery_task.last_payload is not None
    assert fake_celery_task.last_payload["job_id"] == "ingestion-1"


def test_enqueue_ingestion_job_accepts_injected_queue() -> None:
    queue = StubQueue()

    response = enqueue_ingestion_job(
        tenant_id="acme",
        source_key="gov-registry",
        remote_url="https://example.com/api/company",
        requested_by="analyst-1",
        queue=queue,
    )

    assert response["task_id"] == "task-1"
    assert response["queue_status"] == "queued"
    assert queue.last_payload is not None
    assert queue.last_payload["tenant_id"] == "acme"
    assert queue.last_payload["source_key"] == "gov-registry"
