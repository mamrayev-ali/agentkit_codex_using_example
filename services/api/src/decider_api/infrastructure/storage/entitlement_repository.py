import json
from sqlite3 import Connection


class SqliteManagedEntitlementRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def get_modules(
        self,
        *,
        tenant_id: str,
        subject: str,
    ) -> list[str] | None:
        row = self._connection.execute(
            """
            SELECT enabled_modules
            FROM managed_entitlements
            WHERE tenant_id = ? AND subject = ?
            """,
            (tenant_id, subject),
        ).fetchone()
        if row is None:
            return None

        raw_value = row["enabled_modules"]
        if not isinstance(raw_value, str):
            raise ValueError("Invalid enabled_modules value in managed_entitlements.")

        parsed_value = json.loads(raw_value)
        if not isinstance(parsed_value, list):
            raise ValueError("Invalid managed entitlements payload format.")

        modules: list[str] = []
        for value in parsed_value:
            if isinstance(value, str) and value:
                modules.append(value)
        return modules

    def upsert_modules(
        self,
        *,
        tenant_id: str,
        subject: str,
        enabled_modules: list[str],
        actor_subject: str,
        occurred_at: str,
    ) -> None:
        serialized_modules = json.dumps(enabled_modules)
        self._connection.execute(
            """
            INSERT INTO managed_entitlements (
                tenant_id,
                subject,
                enabled_modules,
                updated_by_subject,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(tenant_id, subject) DO UPDATE SET
                enabled_modules = excluded.enabled_modules,
                updated_by_subject = excluded.updated_by_subject,
                updated_at = excluded.updated_at
            """,
            (
                tenant_id,
                subject,
                serialized_modules,
                actor_subject,
                occurred_at,
            ),
        )
        self._connection.commit()

    def clear(self) -> None:
        self._connection.execute("DELETE FROM managed_entitlements")
        self._connection.commit()
