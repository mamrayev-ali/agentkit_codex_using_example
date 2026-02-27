from pathlib import Path

from decider_api.infrastructure.storage import (
    SqliteAuditEventRepository,
    SqliteManagedEntitlementRepository,
    apply_initial_schema,
    create_sqlite_connection,
)


def _database_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_managed_entitlements_persist_across_connections(tmp_path: Path) -> None:
    database_path = tmp_path / "t15-persistence.db"
    connection = create_sqlite_connection(_database_url(database_path))
    apply_initial_schema(connection)

    repository = SqliteManagedEntitlementRepository(connection)
    repository.upsert_modules(
        tenant_id="acme",
        subject="user-123",
        enabled_modules=["dashboard", "watchlist"],
        actor_subject="admin-1",
        occurred_at="2026-02-27T00:00:00Z",
    )
    connection.close()

    reopened_connection = create_sqlite_connection(_database_url(database_path))
    reopened_repository = SqliteManagedEntitlementRepository(reopened_connection)
    loaded = reopened_repository.get_modules(tenant_id="acme", subject="user-123")

    assert loaded == ["dashboard", "watchlist"]


def test_audit_events_are_queryable_for_tenant_review(tmp_path: Path) -> None:
    database_path = tmp_path / "t15-audit.db"
    connection = create_sqlite_connection(_database_url(database_path))
    apply_initial_schema(connection)

    repository = SqliteAuditEventRepository(connection)
    repository.create_event(
        action="entitlements.updated",
        actor_subject="admin-1",
        target_subject="user-123",
        tenant_id="acme",
        outcome="success",
        occurred_at="2026-02-27T00:00:01Z",
    )
    repository.create_event(
        action="export.requested",
        actor_subject="user-123",
        tenant_id="acme",
        outcome="forbidden",
        reason="missing_scope",
        occurred_at="2026-02-27T00:00:02Z",
    )
    repository.create_event(
        action="export.requested",
        actor_subject="user-999",
        tenant_id="other",
        outcome="forbidden",
        reason="tenant_mismatch",
        occurred_at="2026-02-27T00:00:03Z",
    )

    acme_events = repository.list_events_for_tenant(tenant_id="acme")

    assert len(acme_events) == 2
    assert {item["action"] for item in acme_events} == {
        "entitlements.updated",
        "export.requested",
    }
    assert all(item["tenant_id"] == "acme" for item in acme_events)
