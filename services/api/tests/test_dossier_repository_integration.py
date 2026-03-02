from decider_api.application.dossiers import create_dossier, get_dossier, list_dossiers
from decider_api.infrastructure.storage import (
    SqliteDossierRepository,
    apply_initial_schema,
    create_sqlite_connection,
)


def _build_repository() -> SqliteDossierRepository:
    connection = create_sqlite_connection("sqlite:///:memory:")
    apply_initial_schema(connection)
    return SqliteDossierRepository(connection)


def test_dossier_repository_create_and_get_same_tenant() -> None:
    repository = _build_repository()

    created = create_dossier(
        repository=repository,
        tenant_id="tenant-a",
        dossier_id="dos-001",
        subject_name="Acme LLP",
        subject_type="organization",
    )
    loaded = get_dossier(
        repository=repository,
        tenant_id="tenant-a",
        dossier_id="dos-001",
    )

    assert loaded is not None
    assert loaded.tenant_id == created.tenant_id
    assert loaded.dossier_id == created.dossier_id
    assert loaded.subject_name == "Acme LLP"


def test_dossier_repository_enforces_tenant_scope_on_reads() -> None:
    repository = _build_repository()

    create_dossier(
        repository=repository,
        tenant_id="tenant-a",
        dossier_id="dos-001",
        subject_name="John Doe",
        subject_type="person",
    )

    cross_tenant_read = get_dossier(
        repository=repository,
        tenant_id="tenant-b",
        dossier_id="dos-001",
    )

    assert cross_tenant_read is None


def test_dossier_repository_allows_same_business_id_in_different_tenants() -> None:
    repository = _build_repository()

    create_dossier(
        repository=repository,
        tenant_id="tenant-a",
        dossier_id="dos-001",
        subject_name="Tenant A org",
        subject_type="organization",
    )
    create_dossier(
        repository=repository,
        tenant_id="tenant-b",
        dossier_id="dos-001",
        subject_name="Tenant B org",
        subject_type="organization",
    )

    tenant_a = get_dossier(
        repository=repository,
        tenant_id="tenant-a",
        dossier_id="dos-001",
    )
    tenant_b = get_dossier(
        repository=repository,
        tenant_id="tenant-b",
        dossier_id="dos-001",
    )

    assert tenant_a is not None
    assert tenant_b is not None
    assert tenant_a.subject_name != tenant_b.subject_name


def test_dossier_repository_lists_only_requested_tenant_in_reverse_created_order() -> None:
    repository = _build_repository()

    first = create_dossier(
        repository=repository,
        tenant_id="tenant-a",
        dossier_id="dos-001",
        subject_name="First org",
        subject_type="organization",
    )
    create_dossier(
        repository=repository,
        tenant_id="tenant-b",
        dossier_id="dos-001",
        subject_name="Other tenant org",
        subject_type="organization",
    )
    second = create_dossier(
        repository=repository,
        tenant_id="tenant-a",
        dossier_id="dos-002",
        subject_name="Second org",
        subject_type="organization",
    )

    listed = list_dossiers(repository=repository, tenant_id="tenant-a")

    assert [item.dossier_id for item in listed] == [second.dossier_id, first.dossier_id]
