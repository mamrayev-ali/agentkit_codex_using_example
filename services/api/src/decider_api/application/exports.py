from decider_api.application.audit import (
    AUDIT_ACTION_EXPORT_REQUESTED,
    clear_audit_events_by_action,
    list_audit_events_by_action,
    record_audit_event,
)


def record_export_audit_event(
    *,
    tenant_id: str,
    actor_subject: str,
    outcome: str,
    reason: str | None = None,
) -> dict[str, str]:
    return record_audit_event(
        action=AUDIT_ACTION_EXPORT_REQUESTED,
        tenant_id=tenant_id,
        actor_subject=actor_subject,
        outcome=outcome,
        reason=reason,
    )


def create_export_result(*, tenant_id: str, actor_subject: str) -> dict[str, object]:
    audit_metadata = record_export_audit_event(
        tenant_id=tenant_id,
        actor_subject=actor_subject,
        outcome="success",
    )
    export_sequence_value = audit_metadata["event_id"].removeprefix("export-audit-")

    return {
        "tenant_id": tenant_id,
        "export_id": f"export-{export_sequence_value}",
        "status": "accepted",
        "audit_metadata": audit_metadata,
    }


def list_export_audit_events() -> list[dict[str, str]]:
    return list_audit_events_by_action(action=AUDIT_ACTION_EXPORT_REQUESTED)


def reset_export_state() -> None:
    clear_audit_events_by_action(action=AUDIT_ACTION_EXPORT_REQUESTED)
