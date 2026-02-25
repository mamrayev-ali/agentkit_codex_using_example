from decider_api.domain.search_requests import (
    SearchRequest,
    SearchRequestDraft,
    SearchRequestRepository,
)


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
