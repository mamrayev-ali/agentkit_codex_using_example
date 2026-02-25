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


class TenantBaseResource(BaseModel):
    resource_id: str
    name: str


class TenantResourcesResponse(BaseModel):
    tenant_id: str
    resources: list[TenantBaseResource] = Field(default_factory=list)
