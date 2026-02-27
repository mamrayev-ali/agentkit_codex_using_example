import sqlite3
from pathlib import Path


_SQLITE_SCHEME_PREFIX = "sqlite:///"


def _sqlite_path_from_database_url(database_url: str) -> str:
    if database_url == "sqlite:///:memory:":
        return ":memory:"

    if not database_url.startswith(_SQLITE_SCHEME_PREFIX):
        raise ValueError("Only sqlite:/// database URLs are supported.")

    path = database_url.removeprefix(_SQLITE_SCHEME_PREFIX)
    if not path:
        raise ValueError("Database path is required for sqlite URLs.")
    return path


def create_sqlite_connection(database_url: str) -> sqlite3.Connection:
    path = _sqlite_path_from_database_url(database_url)
    if path != ":memory:":
        database_path = Path(path)
        database_path.parent.mkdir(parents=True, exist_ok=True)
        path = str(database_path)

    connection = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection
