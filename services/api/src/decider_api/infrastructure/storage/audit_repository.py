from sqlite3 import Connection, Row

_EVENT_ID_PREFIX_BY_ACTION = {
    "entitlements.updated": "entitlements-updated",
    "export.requested": "export-audit",
}


def _event_id_for_row(*, action: str, audit_id: int) -> str:
    prefix = _EVENT_ID_PREFIX_BY_ACTION.get(action)
    if prefix is None:
        raise ValueError(f"Unsupported audit action '{action}'.")
    return f"{prefix}-{audit_id}"


def _row_to_audit_event(row: Row) -> dict[str, str]:
    action = str(row["action"])
    audit_id_raw = row["audit_id"]
    if not isinstance(audit_id_raw, int):
        raise ValueError("Invalid audit_id value in audit_events row.")

    event: dict[str, str] = {
        "event_id": _event_id_for_row(action=action, audit_id=audit_id_raw),
        "action": action,
        "actor_subject": str(row["actor_subject"]),
        "tenant_id": str(row["tenant_id"]),
        "outcome": str(row["outcome"]),
        "occurred_at": str(row["occurred_at"]),
    }

    target_subject = row["target_subject"]
    if isinstance(target_subject, str) and target_subject:
        event["target_subject"] = target_subject

    reason = row["reason"]
    if isinstance(reason, str) and reason:
        event["reason"] = reason

    return event


class SqliteAuditEventRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def create_event(
        self,
        *,
        action: str,
        actor_subject: str,
        tenant_id: str,
        outcome: str,
        occurred_at: str,
        target_subject: str | None = None,
        reason: str | None = None,
        commit: bool = True,
    ) -> dict[str, str]:
        cursor = self._connection.execute(
            """
            INSERT INTO audit_events (
                action,
                actor_subject,
                target_subject,
                tenant_id,
                outcome,
                reason,
                occurred_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                action,
                actor_subject,
                target_subject,
                tenant_id,
                outcome,
                reason,
                occurred_at,
            ),
        )
        if commit:
            self._connection.commit()

        audit_id = cursor.lastrowid
        if not isinstance(audit_id, int):
            raise ValueError("Failed to persist audit event.")

        return {
            "event_id": _event_id_for_row(action=action, audit_id=audit_id),
            "action": action,
            "actor_subject": actor_subject,
            "tenant_id": tenant_id,
            "outcome": outcome,
            "occurred_at": occurred_at,
            **({"target_subject": target_subject} if target_subject else {}),
            **({"reason": reason} if reason else {}),
        }

    def list_events_for_tenant(
        self,
        *,
        tenant_id: str,
        action: str | None = None,
    ) -> list[dict[str, str]]:
        if action is None:
            rows = self._connection.execute(
                """
                SELECT
                    audit_id,
                    action,
                    actor_subject,
                    target_subject,
                    tenant_id,
                    outcome,
                    reason,
                    occurred_at
                FROM audit_events
                WHERE tenant_id = ?
                ORDER BY audit_id DESC
                """,
                (tenant_id,),
            ).fetchall()
        else:
            rows = self._connection.execute(
                """
                SELECT
                    audit_id,
                    action,
                    actor_subject,
                    target_subject,
                    tenant_id,
                    outcome,
                    reason,
                    occurred_at
                FROM audit_events
                WHERE tenant_id = ? AND action = ?
                ORDER BY audit_id DESC
                """,
                (tenant_id, action),
            ).fetchall()
        return [_row_to_audit_event(row) for row in rows]

    def list_events_by_action(self, *, action: str) -> list[dict[str, str]]:
        rows = self._connection.execute(
            """
            SELECT
                audit_id,
                action,
                actor_subject,
                target_subject,
                tenant_id,
                outcome,
                reason,
                occurred_at
            FROM audit_events
            WHERE action = ?
            ORDER BY audit_id ASC
            """,
            (action,),
        ).fetchall()
        return [_row_to_audit_event(row) for row in rows]

    def clear_by_action(self, *, action: str, commit: bool = True) -> None:
        self._connection.execute(
            "DELETE FROM audit_events WHERE action = ?",
            (action,),
        )
        if commit:
            self._connection.commit()
