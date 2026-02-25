from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from decider_api.api.dependencies.auth import get_authenticated_auth_context
from decider_api.api.schemas.v1 import (
    AuthContextResponse,
    HealthResponse,
    TenantResourcesResponse,
)
from decider_api.application.health import get_health_response
from decider_api.application.tenant_resources import list_tenant_base_resources
from decider_api.domain.tenant_guard import is_tenant_access_allowed

router = APIRouter(tags=["v1"])


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
    return list_tenant_base_resources(tenant_id)
