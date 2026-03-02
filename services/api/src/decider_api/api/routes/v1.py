from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from decider_api.api.dependencies.auth import get_authenticated_auth_context
from decider_api.api.schemas.v1 import (
    AuditEventResponse,
    AuthContextResponse,
    DossierCreateRequest,
    DossierResponse,
    EntitlementsResponse,
    EntitlementsUpdateRequest,
    ExportResponse,
    HealthResponse,
    SearchRequestCreateRequest,
    SearchRequestCreateResponse,
    SearchRequestEnqueueMetadataResponse,
    SearchRequestResponse,
    SearchRequestStatusResponse,
    TenantAuditEventsResponse,
    TenantDossiersResponse,
    TenantResourcesResponse,
    TenantSearchRequestsResponse,
)
from decider_api.application.audit import list_audit_events_for_tenant
from decider_api.application.dossiers import (
    create_dossier,
    get_dossier,
    list_dossiers,
)
from decider_api.application.entitlements import (
    get_managed_modules,
    resolve_modules_from_auth_context,
    update_managed_modules,
)
from decider_api.application.exports import (
    create_export_result,
    record_export_audit_event,
)
from decider_api.application.health import get_health_response
from decider_api.application.search_requests import (
    SearchRequestEnqueueMetadata,
    create_search_request_with_ingestion,
    get_search_request,
    list_search_requests,
)
from decider_api.application.tenant_resources import list_tenant_base_resources
from decider_api.domain.permissions import has_module_access, has_scope, is_admin_actor
from decider_api.domain.tenant_guard import is_tenant_access_allowed
from decider_api.infrastructure.storage import (
    SqliteDossierRepository,
    SqliteSearchRequestRepository,
    run_with_storage_connection,
)

router = APIRouter(tags=["v1"])

_EXPORT_DATA_SCOPE = "export:data"


def _coerce_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []

    parsed: list[str] = []
    for item in value:
        if isinstance(item, str) and item:
            parsed.append(item)
    return parsed


def _assert_tenant_access(*, tenant_id: str, auth_context: dict[str, object]) -> str:
    actor_tenant_id = auth_context.get("tenant_id")
    normalized_actor_tenant_id = (
        actor_tenant_id if isinstance(actor_tenant_id, str) else None
    )
    if not is_tenant_access_allowed(
        requested_tenant_id=tenant_id,
        actor_tenant_id=normalized_actor_tenant_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )
    return normalized_actor_tenant_id


def _assert_admin_access(auth_context: dict[str, object]) -> str:
    roles = _coerce_string_list(auth_context.get("roles"))
    scopes = _coerce_string_list(auth_context.get("scopes"))

    if not is_admin_actor(roles=roles, scopes=scopes):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )

    actor_subject = auth_context.get("subject")
    if not isinstance(actor_subject, str) or not actor_subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

    return actor_subject


def _assert_authenticated_subject(auth_context: dict[str, object]) -> str:
    actor_subject = auth_context.get("subject")
    if not isinstance(actor_subject, str) or not actor_subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )
    return actor_subject


def _assert_dossiers_module_access(auth_context: dict[str, object]) -> None:
    enabled_modules = resolve_modules_from_auth_context(auth_context)
    if not has_module_access(module_key="dossiers", enabled_modules=enabled_modules):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )


def _serialize_created_at(value) -> str:
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def _serialize_dossier(dossier) -> dict[str, object]:
    return {
        "tenant_id": dossier.tenant_id,
        "dossier_id": dossier.dossier_id,
        "subject_name": dossier.subject_name,
        "subject_type": dossier.subject_type,
        "created_at": _serialize_created_at(dossier.created_at),
    }


def _serialize_search_request(search_request) -> dict[str, object]:
    return {
        "tenant_id": search_request.tenant_id,
        "request_id": search_request.request_id,
        "dossier_id": search_request.dossier_id,
        "query_text": search_request.query_text,
        "status": search_request.status,
        "created_at": _serialize_created_at(search_request.created_at),
    }


def _serialize_enqueue_metadata(
    enqueue_metadata: SearchRequestEnqueueMetadata,
) -> dict[str, object]:
    return SearchRequestEnqueueMetadataResponse(
        task_id=enqueue_metadata.task_id,
        queue_status=enqueue_metadata.queue_status,
        result_status=enqueue_metadata.result_status,
    ).model_dump()


@router.get("/health", response_model=HealthResponse)
def get_health_v1() -> dict[str, str]:
    return get_health_response()


@router.get(
    "/auth/context",
    response_model=AuthContextResponse,
    responses={401: {"description": "Invalid or expired token."}},
)
def get_auth_context_v1(
    auth_context: Annotated[dict[str, object], Depends(get_authenticated_auth_context)],
) -> dict[str, object]:
    return auth_context


@router.get(
    "/tenants/{tenant_id}/resources",
    response_model=TenantResourcesResponse,
    responses={
        401: {"description": "Invalid or expired token."},
        403: {"description": "Forbidden"},
    },
)
def get_tenant_resources_v1(
    tenant_id: str,
    auth_context: Annotated[dict[str, object], Depends(get_authenticated_auth_context)],
) -> dict[str, object]:
    _assert_tenant_access(tenant_id=tenant_id, auth_context=auth_context)
    _assert_dossiers_module_access(auth_context)

    return list_tenant_base_resources(tenant_id)


@router.get(
    "/tenants/{tenant_id}/dossiers",
    response_model=TenantDossiersResponse,
    responses={
        401: {"description": "Invalid or expired token."},
        403: {"description": "Forbidden"},
    },
)
def get_tenant_dossiers_v1(
    tenant_id: str,
    auth_context: Annotated[dict[str, object], Depends(get_authenticated_auth_context)],
) -> dict[str, object]:
    _assert_tenant_access(tenant_id=tenant_id, auth_context=auth_context)
    _assert_dossiers_module_access(auth_context)

    dossiers = run_with_storage_connection(
        lambda connection: list_dossiers(
            repository=SqliteDossierRepository(connection),
            tenant_id=tenant_id,
        )
    )
    return {
        "tenant_id": tenant_id,
        "dossiers": [_serialize_dossier(item) for item in dossiers],
    }


@router.post(
    "/tenants/{tenant_id}/dossiers",
    response_model=DossierResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Invalid or expired token."},
        403: {"description": "Forbidden"},
        422: {"description": "Validation error."},
    },
)
def post_tenant_dossier_v1(
    tenant_id: str,
    payload: DossierCreateRequest,
    auth_context: Annotated[dict[str, object], Depends(get_authenticated_auth_context)],
) -> dict[str, object]:
    _assert_tenant_access(tenant_id=tenant_id, auth_context=auth_context)
    _assert_dossiers_module_access(auth_context)

    dossier_id = f"dos-{uuid4().hex[:12]}"
    try:
        dossier = run_with_storage_connection(
            lambda connection: create_dossier(
                repository=SqliteDossierRepository(connection),
                tenant_id=tenant_id,
                dossier_id=dossier_id,
                subject_name=payload.subject_name,
                subject_type=payload.subject_type,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return _serialize_dossier(dossier)


@router.get(
    "/tenants/{tenant_id}/dossiers/{dossier_id}",
    response_model=DossierResponse,
    responses={
        401: {"description": "Invalid or expired token."},
        403: {"description": "Forbidden"},
        404: {"description": "Not found."},
    },
)
def get_tenant_dossier_v1(
    tenant_id: str,
    dossier_id: str,
    auth_context: Annotated[dict[str, object], Depends(get_authenticated_auth_context)],
) -> dict[str, object]:
    _assert_tenant_access(tenant_id=tenant_id, auth_context=auth_context)
    _assert_dossiers_module_access(auth_context)

    dossier = run_with_storage_connection(
        lambda connection: get_dossier(
            repository=SqliteDossierRepository(connection),
            tenant_id=tenant_id,
            dossier_id=dossier_id,
        )
    )
    if dossier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found.",
        )
    return _serialize_dossier(dossier)


@router.get(
    "/tenants/{tenant_id}/search-requests",
    response_model=TenantSearchRequestsResponse,
    responses={
        401: {"description": "Invalid or expired token."},
        403: {"description": "Forbidden"},
    },
)
def get_tenant_search_requests_v1(
    tenant_id: str,
    auth_context: Annotated[dict[str, object], Depends(get_authenticated_auth_context)],
) -> dict[str, object]:
    _assert_tenant_access(tenant_id=tenant_id, auth_context=auth_context)
    _assert_dossiers_module_access(auth_context)

    search_requests = run_with_storage_connection(
        lambda connection: list_search_requests(
            repository=SqliteSearchRequestRepository(connection),
            tenant_id=tenant_id,
        )
    )
    return {
        "tenant_id": tenant_id,
        "search_requests": [_serialize_search_request(item) for item in search_requests],
    }


@router.post(
    "/tenants/{tenant_id}/search-requests",
    response_model=SearchRequestCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Invalid or expired token."},
        403: {"description": "Forbidden"},
        404: {"description": "Not found."},
        422: {"description": "Validation error."},
        503: {"description": "Search ingestion unavailable."},
    },
)
def post_tenant_search_request_v1(
    tenant_id: str,
    payload: SearchRequestCreateRequest,
    auth_context: Annotated[dict[str, object], Depends(get_authenticated_auth_context)],
) -> dict[str, object]:
    _assert_tenant_access(tenant_id=tenant_id, auth_context=auth_context)
    _assert_dossiers_module_access(auth_context)
    actor_subject = _assert_authenticated_subject(auth_context)

    request_id = f"req-{uuid4().hex[:12]}"
    try:
        search_request, enqueue_metadata = run_with_storage_connection(
            lambda connection: create_search_request_with_ingestion(
                dossier_repository=SqliteDossierRepository(connection),
                search_request_repository=SqliteSearchRequestRepository(connection),
                tenant_id=tenant_id,
                request_id=request_id,
                dossier_id=payload.dossier_id,
                query_text=payload.query_text,
                source_key=payload.source_key,
                remote_url=payload.remote_url,
                requested_by=actor_subject,
            )
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search ingestion unavailable.",
        ) from exc

    return {
        "search_request": _serialize_search_request(search_request),
        "enqueue_metadata": _serialize_enqueue_metadata(enqueue_metadata),
    }


@router.get(
    "/tenants/{tenant_id}/search-requests/{request_id}",
    response_model=SearchRequestResponse,
    responses={
        401: {"description": "Invalid or expired token."},
        403: {"description": "Forbidden"},
        404: {"description": "Not found."},
    },
)
def get_tenant_search_request_v1(
    tenant_id: str,
    request_id: str,
    auth_context: Annotated[dict[str, object], Depends(get_authenticated_auth_context)],
) -> dict[str, object]:
    _assert_tenant_access(tenant_id=tenant_id, auth_context=auth_context)
    _assert_dossiers_module_access(auth_context)

    search_request = run_with_storage_connection(
        lambda connection: get_search_request(
            repository=SqliteSearchRequestRepository(connection),
            tenant_id=tenant_id,
            request_id=request_id,
        )
    )
    if search_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found.",
        )
    return _serialize_search_request(search_request)


@router.get(
    "/tenants/{tenant_id}/search-requests/{request_id}/status",
    response_model=SearchRequestStatusResponse,
    responses={
        401: {"description": "Invalid or expired token."},
        403: {"description": "Forbidden"},
        404: {"description": "Not found."},
    },
)
def get_tenant_search_request_status_v1(
    tenant_id: str,
    request_id: str,
    auth_context: Annotated[dict[str, object], Depends(get_authenticated_auth_context)],
) -> dict[str, object]:
    _assert_tenant_access(tenant_id=tenant_id, auth_context=auth_context)
    _assert_dossiers_module_access(auth_context)

    search_request = run_with_storage_connection(
        lambda connection: get_search_request(
            repository=SqliteSearchRequestRepository(connection),
            tenant_id=tenant_id,
            request_id=request_id,
        )
    )
    if search_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found.",
        )
    return {
        "tenant_id": tenant_id,
        "request_id": request_id,
        "status": search_request.status,
    }


@router.post(
    "/tenants/{tenant_id}/exports",
    response_model=ExportResponse,
    responses={
        401: {"description": "Invalid or expired token."},
        403: {"description": "Forbidden"},
    },
)
def post_tenant_export_v1(
    tenant_id: str,
    auth_context: Annotated[dict[str, object], Depends(get_authenticated_auth_context)],
) -> dict[str, object]:
    actor_subject = _assert_authenticated_subject(auth_context)

    actor_tenant_id = auth_context.get("tenant_id")
    normalized_actor_tenant_id = actor_tenant_id if isinstance(actor_tenant_id, str) else None
    if not is_tenant_access_allowed(
        requested_tenant_id=tenant_id,
        actor_tenant_id=normalized_actor_tenant_id,
    ):
        record_export_audit_event(
            tenant_id=tenant_id,
            actor_subject=actor_subject,
            outcome="forbidden",
            reason="tenant_mismatch",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )

    scopes = _coerce_string_list(auth_context.get("scopes"))
    if not has_scope(required_scope=_EXPORT_DATA_SCOPE, scopes=scopes):
        record_export_audit_event(
            tenant_id=tenant_id,
            actor_subject=actor_subject,
            outcome="forbidden",
            reason="missing_scope",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )

    return create_export_result(
        tenant_id=tenant_id,
        actor_subject=actor_subject,
    )


@router.get(
    "/tenants/{tenant_id}/entitlements/{subject}",
    response_model=EntitlementsResponse,
    responses={
        401: {"description": "Invalid or expired token."},
        403: {"description": "Forbidden"},
    },
)
def get_tenant_entitlements_v1(
    tenant_id: str,
    subject: str,
    auth_context: Annotated[dict[str, object], Depends(get_authenticated_auth_context)],
) -> dict[str, object]:
    _assert_tenant_access(tenant_id=tenant_id, auth_context=auth_context)
    _assert_admin_access(auth_context)

    enabled_modules = get_managed_modules(tenant_id=tenant_id, subject=subject)
    return {
        "tenant_id": tenant_id,
        "subject": subject,
        "enabled_modules": enabled_modules,
    }


@router.put(
    "/tenants/{tenant_id}/entitlements/{subject}",
    response_model=EntitlementsResponse,
    responses={
        401: {"description": "Invalid or expired token."},
        403: {"description": "Forbidden"},
        422: {"description": "Validation error."},
    },
)
def put_tenant_entitlements_v1(
    tenant_id: str,
    subject: str,
    payload: EntitlementsUpdateRequest,
    auth_context: Annotated[dict[str, object], Depends(get_authenticated_auth_context)],
) -> dict[str, object]:
    _assert_tenant_access(tenant_id=tenant_id, auth_context=auth_context)
    actor_subject = _assert_admin_access(auth_context)

    try:
        return update_managed_modules(
            tenant_id=tenant_id,
            subject=subject,
            enabled_modules=payload.enabled_modules,
            actor_subject=actor_subject,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.get(
    "/tenants/{tenant_id}/audit/events",
    response_model=TenantAuditEventsResponse,
    responses={
        401: {"description": "Invalid or expired token."},
        403: {"description": "Forbidden"},
    },
)
def get_tenant_audit_events_v1(
    tenant_id: str,
    auth_context: Annotated[dict[str, object], Depends(get_authenticated_auth_context)],
) -> dict[str, object]:
    _assert_tenant_access(tenant_id=tenant_id, auth_context=auth_context)
    _assert_admin_access(auth_context)

    events = list_audit_events_for_tenant(tenant_id=tenant_id)
    validated_events = [AuditEventResponse.model_validate(item) for item in events]
    return {
        "tenant_id": tenant_id,
        "events": [item.model_dump() for item in validated_events],
    }
