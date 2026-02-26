from datetime import datetime, timezone
from itertools import count
from threading import Lock

_EXPORT_AUDIT_EVENTS: list[dict[str, str]] = []
_AUDIT_SEQUENCE = count(1)
_EXPORT_SEQUENCE = count(1)
_STATE_LOCK = Lock()


def _utc_now_isoformat() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def record_export_audit_event(
    *,
    tenant_id: str,
    actor_subject: str,
    outcome: str,
    reason: str | None = None,
) -> dict[str, str]:
    with _STATE_LOCK:
        sequence_value = next(_AUDIT_SEQUENCE)
        event = {
            "event_id": f"export-audit-{sequence_value}",
            "action": "export.requested",
            "actor_subject": actor_subject,
            "tenant_id": tenant_id,
            "outcome": outcome,
            "occurred_at": _utc_now_isoformat(),
        }
        if reason is not None:
            event["reason"] = reason
        _EXPORT_AUDIT_EVENTS.append(dict(event))

    return dict(event)


def create_export_result(*, tenant_id: str, actor_subject: str) -> dict[str, object]:
    with _STATE_LOCK:
        export_sequence_value = next(_EXPORT_SEQUENCE)

    audit_metadata = record_export_audit_event(
        tenant_id=tenant_id,
        actor_subject=actor_subject,
        outcome="success",
    )

    return {
        "tenant_id": tenant_id,
        "export_id": f"export-{export_sequence_value}",
        "status": "accepted",
        "audit_metadata": audit_metadata,
    }


def list_export_audit_events() -> list[dict[str, str]]:
    with _STATE_LOCK:
        return [dict(event) for event in _EXPORT_AUDIT_EVENTS]


def reset_export_state() -> None:
    global _AUDIT_SEQUENCE
    global _EXPORT_SEQUENCE

    with _STATE_LOCK:
        _EXPORT_AUDIT_EVENTS.clear()
        _AUDIT_SEQUENCE = count(1)
        _EXPORT_SEQUENCE = count(1)
