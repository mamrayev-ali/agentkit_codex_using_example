from decider_api.infrastructure.storage.db import create_sqlite_connection
from decider_api.infrastructure.storage.migrations import (
    apply_initial_schema,
    rollback_initial_schema,
)


def _table_exists(connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def test_initial_schema_migration_creates_core_tables() -> None:
    connection = create_sqlite_connection("sqlite:///:memory:")

    apply_initial_schema(connection)

    assert _table_exists(connection, "dossiers")
    assert _table_exists(connection, "search_requests")
    assert _table_exists(connection, "managed_entitlements")
    assert _table_exists(connection, "audit_events")


def test_initial_schema_rollback_drops_core_tables() -> None:
    connection = create_sqlite_connection("sqlite:///:memory:")
    apply_initial_schema(connection)

    rollback_initial_schema(connection)

    assert not _table_exists(connection, "audit_events")
    assert not _table_exists(connection, "managed_entitlements")
    assert not _table_exists(connection, "search_requests")
    assert not _table_exists(connection, "dossiers")
