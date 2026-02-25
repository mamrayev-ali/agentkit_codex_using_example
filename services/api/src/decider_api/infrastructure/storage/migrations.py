import sqlite3
from pathlib import Path

_MIGRATIONS_DIR = Path(__file__).resolve().parents[4] / "migrations" / "versions"


def migration_script_path(filename: str) -> Path:
    script_path = _MIGRATIONS_DIR / filename
    if not script_path.exists():
        raise FileNotFoundError(f"Migration script not found: {script_path}")
    return script_path


def apply_sql_script(connection: sqlite3.Connection, *, script_path: Path) -> None:
    script = script_path.read_text(encoding="utf-8")
    connection.executescript(script)


def apply_initial_schema(connection: sqlite3.Connection) -> None:
    apply_sql_script(
        connection,
        script_path=migration_script_path("0001_initial_dossier_core.up.sql"),
    )


def rollback_initial_schema(connection: sqlite3.Connection) -> None:
    apply_sql_script(
        connection,
        script_path=migration_script_path("0001_initial_dossier_core.down.sql"),
    )
