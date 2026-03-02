from decider_api.domain.dossiers import (
    Dossier,
    DossierDraft,
    DossierRepository,
)


def create_dossier(
    *,
    repository: DossierRepository,
    tenant_id: str,
    dossier_id: str,
    subject_name: str,
    subject_type: str,
) -> Dossier:
    draft = DossierDraft(
        tenant_id=tenant_id,
        dossier_id=dossier_id,
        subject_name=subject_name,
        subject_type=subject_type,
    )
    return repository.create(draft)


def get_dossier(
    *,
    repository: DossierRepository,
    tenant_id: str,
    dossier_id: str,
) -> Dossier | None:
    return repository.get_by_id(tenant_id=tenant_id, dossier_id=dossier_id)


def list_dossiers(
    *,
    repository: DossierRepository,
    tenant_id: str,
) -> list[Dossier]:
    return repository.list_for_tenant(tenant_id=tenant_id)
