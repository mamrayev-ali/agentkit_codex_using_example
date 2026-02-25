from typing import Annotated

from fastapi import APIRouter, Depends

from decider_api.api.dependencies.auth import get_authenticated_auth_context
from decider_api.api.schemas.v1 import (
    AuthContextResponse,
    HealthResponse,
    TenantResourcesResponse,
)
from decider_api.application.health import get_health_response
from decider_api.application.tenant_resources import list_tenant_base_resources

router = APIRouter(tags=["v1"])


@router.get("/health", response_model=HealthResponse)
def get_health_v1() -> dict[str, str]:
    return get_health_response()


@router.get(
    "/auth/context",
    response_model=AuthContextResponse,
    responses={401: {"description": "Unauthorized"}},
)
def get_auth_context_v1(
    auth_context: Annotated[dict[str, object], Depends(get_authenticated_auth_context)],
) -> dict[str, object]:
    return auth_context


@router.get(
    "/tenants/{tenant_id}/resources",
    response_model=TenantResourcesResponse,
)
def get_tenant_resources_v1(tenant_id: str) -> dict[str, object]:
    return list_tenant_base_resources(tenant_id)
