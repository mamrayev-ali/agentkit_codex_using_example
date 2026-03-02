import pytest

from decider_api.application.dossiers import create_dossier
from decider_api.application.search_requests import (
    create_search_request,
    get_search_request,
    list_search_requests,
    update_search_request_status,
)
from decider_api.infrastructure.storage import (
    SqliteDossierRepository,
    SqliteSearchRequestRepository,
    apply_initial_schema,
    create_sqlite_connection,
)


def _build_repositories() -> tuple[SqliteDossierRepository, SqliteSearchRequestRepository]:
    connection = create_sqlite_connection("sqlite:///:memory:")
    apply_initial_schema(connection)
    return SqliteDossierRepository(connection), SqliteSearchRequestRepository(connection)


def test_search_request_repository_create_and_get_same_tenant() -> None:
    dossier_repository, search_repository = _build_repositories()
    create_dossier(
        repository=dossier_repository,
        tenant_id="tenant-a",
        dossier_id="dos-001",
        subject_name="Acme LLP",
        subject_type="organization",
    )

    created = create_search_request(
        repository=search_repository,
        tenant_id="tenant-a",
        request_id="req-001",
        dossier_id="dos-001",
        query_text="open sanctions check",
    )
    loaded = get_search_request(
        repository=search_repository,
        tenant_id="tenant-a",
        request_id="req-001",
    )

    assert loaded is not None
    assert loaded.request_id == created.request_id
    assert loaded.dossier_id == "dos-001"
    assert loaded.status == "queued"


def test_search_request_repository_enforces_tenant_scope_on_reads() -> None:
    dossier_repository, search_repository = _build_repositories()
    create_dossier(
        repository=dossier_repository,
        tenant_id="tenant-a",
        dossier_id="dos-001",
        subject_name="Acme LLP",
        subject_type="organization",
    )
    create_search_request(
        repository=search_repository,
        tenant_id="tenant-a",
        request_id="req-001",
        dossier_id="dos-001",
        query_text="query",
    )

    cross_tenant_read = get_search_request(
        repository=search_repository,
        tenant_id="tenant-b",
        request_id="req-001",
    )

    assert cross_tenant_read is None


def test_search_request_requires_existing_tenant_scoped_dossier() -> None:
    _dossier_repository, search_repository = _build_repositories()

    with pytest.raises(ValueError, match="unknown tenant dossier"):
        create_search_request(
            repository=search_repository,
            tenant_id="tenant-a",
            request_id="req-001",
            dossier_id="missing-dossier",
            query_text="query",
        )


def test_search_request_repository_lists_only_requested_tenant_and_updates_status() -> None:
    dossier_repository, search_repository = _build_repositories()
    create_dossier(
        repository=dossier_repository,
        tenant_id="tenant-a",
        dossier_id="dos-001",
        subject_name="Acme LLP",
        subject_type="organization",
    )
    create_dossier(
        repository=dossier_repository,
        tenant_id="tenant-b",
        dossier_id="dos-001",
        subject_name="Other LLP",
        subject_type="organization",
    )
    create_search_request(
        repository=search_repository,
        tenant_id="tenant-a",
        request_id="req-001",
        dossier_id="dos-001",
        query_text="first query",
    )
    second = create_search_request(
        repository=search_repository,
        tenant_id="tenant-a",
        request_id="req-002",
        dossier_id="dos-001",
        query_text="second query",
    )
    create_search_request(
        repository=search_repository,
        tenant_id="tenant-b",
        request_id="req-100",
        dossier_id="dos-001",
        query_text="other tenant query",
    )

    listed = list_search_requests(repository=search_repository, tenant_id="tenant-a")
    updated = update_search_request_status(
        repository=search_repository,
        tenant_id="tenant-a",
        request_id="req-002",
        status="completed",
    )

    assert [item.request_id for item in listed] == [second.request_id, "req-001"]
    assert updated is not None
    assert updated.status == "completed"
