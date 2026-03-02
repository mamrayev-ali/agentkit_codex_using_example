from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

_ALLOWED_REQUEST_STATUSES = ("queued", "running", "completed", "failed")


@dataclass(frozen=True)
class SearchRequestDraft:
    tenant_id: str
    request_id: str
    dossier_id: str
    query_text: str
    status: str = "queued"


@dataclass(frozen=True)
class SearchRequest:
    tenant_id: str
    request_id: str
    dossier_id: str
    query_text: str
    status: str
    created_at: datetime


class SearchRequestRepository(Protocol):
    def create(self, draft: SearchRequestDraft) -> SearchRequest:
        ...

    def get_by_id(self, *, tenant_id: str, request_id: str) -> SearchRequest | None:
        ...

    def list_for_tenant(self, *, tenant_id: str) -> list[SearchRequest]:
        ...

    def update_status(
        self,
        *,
        tenant_id: str,
        request_id: str,
        status: str,
    ) -> SearchRequest | None:
        ...


def _require_non_empty(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty.")
    return normalized


def normalize_request_status(value: str) -> str:
    normalized = _require_non_empty(value, field_name="status").lower()
    if normalized not in _ALLOWED_REQUEST_STATUSES:
        raise ValueError("Unsupported search request status.")
    return normalized


def validate_search_request_draft(draft: SearchRequestDraft) -> SearchRequestDraft:
    return SearchRequestDraft(
        tenant_id=_require_non_empty(draft.tenant_id, field_name="tenant_id"),
        request_id=_require_non_empty(draft.request_id, field_name="request_id"),
        dossier_id=_require_non_empty(draft.dossier_id, field_name="dossier_id"),
        query_text=_require_non_empty(draft.query_text, field_name="query_text"),
        status=normalize_request_status(draft.status),
    )
