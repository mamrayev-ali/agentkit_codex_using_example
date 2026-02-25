from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"]


class AuthContextResponse(BaseModel):
    authenticated: bool
    subject: str
    tenant_id: str | None
    scopes: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    module_entitlements: list[str] = Field(default_factory=list)


class TenantBaseResource(BaseModel):
    resource_id: str
    name: str


class TenantResourcesResponse(BaseModel):
    tenant_id: str
    resources: list[TenantBaseResource] = Field(default_factory=list)


class EntitlementAuditMetadata(BaseModel):
    event_id: str
    action: Literal["entitlements.updated"]
    actor_subject: str
    target_subject: str
    tenant_id: str
    occurred_at: str


class EntitlementsUpdateRequest(BaseModel):
    enabled_modules: list[str] = Field(default_factory=list)


class EntitlementsResponse(BaseModel):
    tenant_id: str
    subject: str
    enabled_modules: list[str] = Field(default_factory=list)
    audit_metadata: EntitlementAuditMetadata | None = None
