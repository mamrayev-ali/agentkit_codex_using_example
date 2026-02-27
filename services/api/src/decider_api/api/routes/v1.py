from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from decider_api.api.dependencies.auth import get_authenticated_auth_context
from decider_api.api.schemas.v1 import (
    AuditEventResponse,
    AuthContextResponse,
    EntitlementsResponse,
    EntitlementsUpdateRequest,
    ExportResponse,
    HealthResponse,
    TenantAuditEventsResponse,
    TenantResourcesResponse,
)
from decider_api.application.audit import list_audit_events_for_tenant
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
from decider_api.application.tenant_resources import list_tenant_base_resources
from decider_api.domain.permissions import has_module_access, has_scope, is_admin_actor
from decider_api.domain.tenant_guard import is_tenant_access_allowed

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

    enabled_modules = resolve_modules_from_auth_context(auth_context)
    if not has_module_access(module_key="dossiers", enabled_modules=enabled_modules):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )

    return list_tenant_base_resources(tenant_id)


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
    actor_subject = auth_context.get("subject")
    if not isinstance(actor_subject, str) or not actor_subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

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
