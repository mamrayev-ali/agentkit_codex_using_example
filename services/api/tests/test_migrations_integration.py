import sqlite3

import pytest

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


def _index_exists(connection, index_name: str) -> bool:
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'index' AND name = ?",
        (index_name,),
    ).fetchone()
    return row is not None


def _applied_versions(connection) -> list[str]:
    rows = connection.execute(
        "SELECT version FROM schema_migrations ORDER BY version ASC"
    ).fetchall()
    return [row["version"] for row in rows]


def test_initial_schema_migration_creates_core_tables() -> None:
    connection = create_sqlite_connection("sqlite:///:memory:")

    apply_initial_schema(connection)

    assert _table_exists(connection, "dossiers")
    assert _table_exists(connection, "search_requests")
    assert _table_exists(connection, "managed_entitlements")
    assert _table_exists(connection, "audit_events")
    assert _applied_versions(connection) == [
        "0001_initial_dossier_core",
        "0002_entitlements_audit_persistence",
    ]


def test_initial_schema_rollback_drops_core_tables() -> None:
    connection = create_sqlite_connection("sqlite:///:memory:")
    apply_initial_schema(connection)

    rollback_initial_schema(connection)

    assert not _table_exists(connection, "audit_events")
    assert not _table_exists(connection, "managed_entitlements")
    assert not _table_exists(connection, "search_requests")
    assert not _table_exists(connection, "dossiers")


def test_initial_schema_bootstrap_marks_existing_legacy_migration_and_applies_remaining() -> None:
    connection = create_sqlite_connection("sqlite:///:memory:")
    connection.executescript(
        """
        CREATE TABLE dossiers (
            tenant_id TEXT NOT NULL,
            dossier_id TEXT NOT NULL,
            subject_name TEXT NOT NULL,
            subject_type TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (tenant_id, dossier_id)
        );
        CREATE INDEX idx_dossiers_tenant_created
            ON dossiers (tenant_id, created_at);
        CREATE TABLE search_requests (
            tenant_id TEXT NOT NULL,
            request_id TEXT NOT NULL,
            dossier_id TEXT NOT NULL,
            query_text TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (tenant_id, request_id),
            FOREIGN KEY (tenant_id, dossier_id)
                REFERENCES dossiers (tenant_id, dossier_id)
                ON DELETE CASCADE
        );
        CREATE INDEX idx_search_requests_tenant_dossier
            ON search_requests (tenant_id, dossier_id);
        """
    )

    apply_initial_schema(connection)

    assert _table_exists(connection, "managed_entitlements")
    assert _table_exists(connection, "audit_events")
    assert _applied_versions(connection) == [
        "0001_initial_dossier_core",
        "0002_entitlements_audit_persistence",
    ]


def test_initial_schema_fails_without_marking_partial_existing_migration_as_applied() -> None:
    connection = create_sqlite_connection("sqlite:///:memory:")
    connection.execute(
        """
        CREATE TABLE dossiers (
            tenant_id TEXT NOT NULL,
            dossier_id TEXT NOT NULL,
            subject_name TEXT NOT NULL,
            subject_type TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (tenant_id, dossier_id)
        )
        """
    )
    connection.commit()

    with pytest.raises(sqlite3.OperationalError):
        apply_initial_schema(connection)

    assert _table_exists(connection, "schema_migrations")
    assert not _index_exists(connection, "idx_dossiers_tenant_created")
    assert _applied_versions(connection) == []
