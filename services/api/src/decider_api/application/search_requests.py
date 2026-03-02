from dataclasses import dataclass

from decider_api.domain.dossiers import DossierRepository
from decider_api.domain.search_requests import (
    SearchRequest,
    SearchRequestDraft,
    SearchRequestRepository,
    normalize_request_status,
)
from decider_api.infrastructure.ingestion.celery_app import QueueProtocol
from decider_api.infrastructure.ingestion.tasks import enqueue_ingestion_job


@dataclass(frozen=True)
class SearchRequestEnqueueMetadata:
    task_id: str
    queue_status: str
    result_status: str | None = None


def create_search_request(
    *,
    repository: SearchRequestRepository,
    tenant_id: str,
    request_id: str,
    dossier_id: str,
    query_text: str,
    status: str = "queued",
) -> SearchRequest:
    draft = SearchRequestDraft(
        tenant_id=tenant_id,
        request_id=request_id,
        dossier_id=dossier_id,
        query_text=query_text,
        status=status,
    )
    return repository.create(draft)


def get_search_request(
    *,
    repository: SearchRequestRepository,
    tenant_id: str,
    request_id: str,
) -> SearchRequest | None:
    return repository.get_by_id(tenant_id=tenant_id, request_id=request_id)


def list_search_requests(
    *,
    repository: SearchRequestRepository,
    tenant_id: str,
) -> list[SearchRequest]:
    return repository.list_for_tenant(tenant_id=tenant_id)


def update_search_request_status(
    *,
    repository: SearchRequestRepository,
    tenant_id: str,
    request_id: str,
    status: str,
) -> SearchRequest | None:
    normalized_status = normalize_request_status(status)
    return repository.update_status(
        tenant_id=tenant_id,
        request_id=request_id,
        status=normalized_status,
    )


def create_search_request_with_ingestion(
    *,
    dossier_repository: DossierRepository,
    search_request_repository: SearchRequestRepository,
    tenant_id: str,
    request_id: str,
    dossier_id: str,
    query_text: str,
    source_key: str,
    remote_url: str,
    requested_by: str,
    queue: QueueProtocol | None = None,
) -> tuple[SearchRequest, SearchRequestEnqueueMetadata]:
    dossier = dossier_repository.get_by_id(tenant_id=tenant_id, dossier_id=dossier_id)
    if dossier is None:
        raise LookupError("Dossier not found.")

    enqueue_response = enqueue_ingestion_job(
        tenant_id=tenant_id,
        source_key=source_key,
        remote_url=remote_url,
        requested_by=requested_by,
        queue=queue,
    )
    search_request = create_search_request(
        repository=search_request_repository,
        tenant_id=tenant_id,
        request_id=request_id,
        dossier_id=dossier.dossier_id,
        query_text=query_text,
        status=_resolve_search_request_status(enqueue_response),
    )
    return search_request, _build_enqueue_metadata(enqueue_response)


def _resolve_search_request_status(enqueue_response: dict[str, object]) -> str:
    result = enqueue_response.get("result")
    if isinstance(result, dict):
        raw_result_status = result.get("status")
        if isinstance(raw_result_status, str) and raw_result_status:
            return normalize_request_status(raw_result_status)

    queue_status = enqueue_response.get("queue_status")
    if queue_status == "queued":
        return "queued"
    if queue_status == "success":
        return "completed"
    return "failed"


def _build_enqueue_metadata(
    enqueue_response: dict[str, object],
) -> SearchRequestEnqueueMetadata:
    task_id = enqueue_response.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        raise ValueError("Ingestion queue response is missing task_id.")

    queue_status = enqueue_response.get("queue_status")
    if not isinstance(queue_status, str) or not queue_status:
        raise ValueError("Ingestion queue response is missing queue_status.")

    result_status: str | None = None
    result = enqueue_response.get("result")
    if isinstance(result, dict):
        raw_result_status = result.get("status")
        if isinstance(raw_result_status, str) and raw_result_status:
            result_status = normalize_request_status(raw_result_status)

    return SearchRequestEnqueueMetadata(
        task_id=task_id,
        queue_status=queue_status,
        result_status=result_status,
    )
