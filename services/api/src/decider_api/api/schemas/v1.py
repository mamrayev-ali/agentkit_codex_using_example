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


class DossierCreateRequest(BaseModel):
    subject_name: str = Field(min_length=1)
    subject_type: Literal["organization", "person"]


class DossierResponse(BaseModel):
    tenant_id: str
    dossier_id: str
    subject_name: str
    subject_type: Literal["organization", "person"]
    created_at: str


class TenantDossiersResponse(BaseModel):
    tenant_id: str
    dossiers: list[DossierResponse] = Field(default_factory=list)


class SearchRequestCreateRequest(BaseModel):
    dossier_id: str = Field(min_length=1)
    query_text: str = Field(min_length=1)
    source_key: str = Field(min_length=1)
    remote_url: str = Field(min_length=1)


class SearchRequestResponse(BaseModel):
    tenant_id: str
    request_id: str
    dossier_id: str
    query_text: str
    status: Literal["queued", "running", "completed", "failed"]
    created_at: str


class SearchRequestEnqueueMetadataResponse(BaseModel):
    task_id: str
    queue_status: str
    result_status: Literal["queued", "running", "completed", "failed"] | None = None


class SearchRequestCreateResponse(BaseModel):
    search_request: SearchRequestResponse
    enqueue_metadata: SearchRequestEnqueueMetadataResponse


class TenantSearchRequestsResponse(BaseModel):
    tenant_id: str
    search_requests: list[SearchRequestResponse] = Field(default_factory=list)


class SearchRequestStatusResponse(BaseModel):
    tenant_id: str
    request_id: str
    status: Literal["queued", "running", "completed", "failed"]


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


class ExportAuditMetadata(BaseModel):
    event_id: str
    action: Literal["export.requested"]
    actor_subject: str
    tenant_id: str
    outcome: Literal["success", "forbidden"]
    occurred_at: str
    reason: str | None = None


class ExportResponse(BaseModel):
    tenant_id: str
    export_id: str
    status: Literal["accepted"]
    audit_metadata: ExportAuditMetadata


class AuditEventResponse(BaseModel):
    event_id: str
    action: Literal["entitlements.updated", "export.requested"]
    actor_subject: str
    target_subject: str | None = None
    tenant_id: str
    outcome: Literal["success", "forbidden"]
    occurred_at: str
    reason: str | None = None


class TenantAuditEventsResponse(BaseModel):
    tenant_id: str
    events: list[AuditEventResponse] = Field(default_factory=list)
