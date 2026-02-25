from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

_ALLOWED_SUBJECT_TYPES = ("organization", "person")


@dataclass(frozen=True)
class DossierDraft:
    tenant_id: str
    dossier_id: str
    subject_name: str
    subject_type: str


@dataclass(frozen=True)
class Dossier:
    tenant_id: str
    dossier_id: str
    subject_name: str
    subject_type: str
    created_at: datetime


class DossierRepository(Protocol):
    def create(self, draft: DossierDraft) -> Dossier:
        ...

    def get_by_id(self, *, tenant_id: str, dossier_id: str) -> Dossier | None:
        ...


def _require_non_empty(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty.")
    return normalized


def normalize_subject_type(value: str) -> str:
    normalized = _require_non_empty(value, field_name="subject_type").lower()
    if normalized not in _ALLOWED_SUBJECT_TYPES:
        raise ValueError("Unsupported subject_type.")
    return normalized


def validate_dossier_draft(draft: DossierDraft) -> DossierDraft:
    return DossierDraft(
        tenant_id=_require_non_empty(draft.tenant_id, field_name="tenant_id"),
        dossier_id=_require_non_empty(draft.dossier_id, field_name="dossier_id"),
        subject_name=_require_non_empty(draft.subject_name, field_name="subject_name"),
        subject_type=normalize_subject_type(draft.subject_type),
    )
