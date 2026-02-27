from datetime import datetime, timezone

from decider_api.infrastructure.storage import (
    SqliteAuditEventRepository,
    run_with_storage_connection,
)

AUDIT_ACTION_ENTITLEMENTS_UPDATED = "entitlements.updated"
AUDIT_ACTION_EXPORT_REQUESTED = "export.requested"


def _utc_now_isoformat() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def record_audit_event(
    *,
    action: str,
    tenant_id: str,
    actor_subject: str,
    outcome: str,
    target_subject: str | None = None,
    reason: str | None = None,
) -> dict[str, str]:
    occurred_at = _utc_now_isoformat()

    def _operation(connection):
        repository = SqliteAuditEventRepository(connection)
        return repository.create_event(
            action=action,
            actor_subject=actor_subject,
            tenant_id=tenant_id,
            outcome=outcome,
            occurred_at=occurred_at,
            target_subject=target_subject,
            reason=reason,
        )

    return run_with_storage_connection(_operation)


def list_audit_events_for_tenant(*, tenant_id: str) -> list[dict[str, str]]:
    def _operation(connection):
        repository = SqliteAuditEventRepository(connection)
        return repository.list_events_for_tenant(tenant_id=tenant_id)

    return run_with_storage_connection(_operation)


def list_audit_events_by_action(*, action: str) -> list[dict[str, str]]:
    def _operation(connection):
        repository = SqliteAuditEventRepository(connection)
        return repository.list_events_by_action(action=action)

    return run_with_storage_connection(_operation)


def clear_audit_events_by_action(*, action: str) -> None:
    def _operation(connection):
        repository = SqliteAuditEventRepository(connection)
        repository.clear_by_action(action=action)

    run_with_storage_connection(_operation)
