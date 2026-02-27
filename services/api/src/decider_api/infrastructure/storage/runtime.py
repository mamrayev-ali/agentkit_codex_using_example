from collections.abc import Callable
from functools import lru_cache
from sqlite3 import Connection
from threading import Lock
from typing import TypeVar

from decider_api.infrastructure.storage.db import create_sqlite_connection
from decider_api.infrastructure.storage.migrations import apply_all_migrations
from decider_api.settings import get_settings

_T = TypeVar("_T")
_SCHEMA_LOCK = Lock()


@lru_cache(maxsize=16)
def _ensure_schema(database_url: str) -> None:
    with _SCHEMA_LOCK:
        connection = create_sqlite_connection(database_url)
        try:
            apply_all_migrations(connection)
        finally:
            connection.close()


def run_with_storage_connection(
    operation: Callable[[Connection], _T],
) -> _T:
    database_url = get_settings().database_url
    _ensure_schema(database_url)

    connection = create_sqlite_connection(database_url)
    try:
        return operation(connection)
    finally:
        connection.close()


def clear_runtime_storage_cache() -> None:
    _ensure_schema.cache_clear()
