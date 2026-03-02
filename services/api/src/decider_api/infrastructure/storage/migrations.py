import sqlite3
from pathlib import Path

_MIGRATIONS_DIR = Path(__file__).resolve().parents[4] / "migrations" / "versions"
_MIGRATION_STEPS: tuple[tuple[str, str], ...] = (
    ("0001_initial_dossier_core.up.sql", "0001_initial_dossier_core.down.sql"),
    (
        "0002_entitlements_audit_persistence.up.sql",
        "0002_entitlements_audit_persistence.down.sql",
    ),
)
_MIGRATION_TABLE_NAME = "schema_migrations"
_EXPECTED_ARTIFACTS_BY_VERSION: dict[str, tuple[tuple[str, str], ...]] = {
    "0001_initial_dossier_core": (
        ("table", "dossiers"),
        ("index", "idx_dossiers_tenant_created"),
        ("table", "search_requests"),
        ("index", "idx_search_requests_tenant_dossier"),
    ),
    "0002_entitlements_audit_persistence": (
        ("table", "managed_entitlements"),
        ("index", "idx_managed_entitlements_tenant"),
        ("table", "audit_events"),
        ("index", "idx_audit_events_tenant_occurred"),
    ),
}


def migration_script_path(filename: str) -> Path:
    script_path = _MIGRATIONS_DIR / filename
    if not script_path.exists():
        raise FileNotFoundError(f"Migration script not found: {script_path}")
    return script_path


def apply_sql_script(connection: sqlite3.Connection, *, script_path: Path) -> None:
    script = script_path.read_text(encoding="utf-8")
    connection.executescript(script)


def _ensure_migration_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {_MIGRATION_TABLE_NAME} (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP)
        )
        """
    )
    connection.commit()


def _is_migration_applied(connection: sqlite3.Connection, *, version: str) -> bool:
    row = connection.execute(
        f"SELECT version FROM {_MIGRATION_TABLE_NAME} WHERE version = ?",
        (version,),
    ).fetchone()
    return row is not None


def _mark_migration_applied(connection: sqlite3.Connection, *, version: str) -> None:
    connection.execute(
        f"""
        INSERT INTO {_MIGRATION_TABLE_NAME} (version)
        VALUES (?)
        """,
        (version,),
    )
    connection.commit()


def _mark_migration_rolled_back(connection: sqlite3.Connection, *, version: str) -> None:
    connection.execute(
        f"""
        DELETE FROM {_MIGRATION_TABLE_NAME}
        WHERE version = ?
        """,
        (version,),
    )
    connection.commit()


def _schema_artifact_exists(
    connection: sqlite3.Connection,
    *,
    artifact_type: str,
    name: str,
) -> bool:
    row = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = ? AND name = ?
        """,
        (artifact_type, name),
    ).fetchone()
    return row is not None


def _expected_artifacts_exist(connection: sqlite3.Connection, *, version: str) -> bool:
    expected_artifacts = _EXPECTED_ARTIFACTS_BY_VERSION.get(version, ())
    return all(
        _schema_artifact_exists(
            connection,
            artifact_type=artifact_type,
            name=artifact_name,
        )
        for artifact_type, artifact_name in expected_artifacts
    )


def apply_all_migrations(connection: sqlite3.Connection) -> None:
    _ensure_migration_table(connection)
    for up_script, _down_script in _MIGRATION_STEPS:
        migration_version = up_script.removesuffix(".up.sql")
        if _is_migration_applied(connection, version=migration_version):
            continue
        if _expected_artifacts_exist(connection, version=migration_version):
            _mark_migration_applied(connection, version=migration_version)
            continue
        apply_sql_script(connection, script_path=migration_script_path(up_script))
        if not _expected_artifacts_exist(connection, version=migration_version):
            raise sqlite3.OperationalError(
                f"Migration '{migration_version}' did not create the expected schema artifacts."
            )
        _mark_migration_applied(connection, version=migration_version)


def rollback_all_migrations(connection: sqlite3.Connection) -> None:
    _ensure_migration_table(connection)
    for _up_script, down_script in reversed(_MIGRATION_STEPS):
        migration_version = down_script.removesuffix(".down.sql")
        if not _is_migration_applied(connection, version=migration_version):
            continue
        apply_sql_script(connection, script_path=migration_script_path(down_script))
        _mark_migration_rolled_back(connection, version=migration_version)


def apply_initial_schema(connection: sqlite3.Connection) -> None:
    apply_all_migrations(connection)


def rollback_initial_schema(connection: sqlite3.Connection) -> None:
    rollback_all_migrations(connection)
