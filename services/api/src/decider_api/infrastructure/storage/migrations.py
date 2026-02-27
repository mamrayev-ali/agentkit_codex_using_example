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


def apply_all_migrations(connection: sqlite3.Connection) -> None:
    _ensure_migration_table(connection)
    for up_script, _down_script in _MIGRATION_STEPS:
        migration_version = up_script.removesuffix(".up.sql")
        if _is_migration_applied(connection, version=migration_version):
            continue
        try:
            apply_sql_script(connection, script_path=migration_script_path(up_script))
        except sqlite3.OperationalError as exc:
            if "already exists" not in str(exc).lower():
                raise
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
