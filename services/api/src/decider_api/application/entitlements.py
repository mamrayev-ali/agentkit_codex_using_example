from collections.abc import Mapping, Sequence
from datetime import datetime, timezone

from decider_api.application.audit import (
    AUDIT_ACTION_ENTITLEMENTS_UPDATED,
    clear_audit_events_by_action,
)
from decider_api.domain.permissions import (
    default_modules_for_claims,
    normalize_modules,
)
from decider_api.infrastructure.storage import (
    SqliteAuditEventRepository,
    SqliteManagedEntitlementRepository,
    run_with_storage_connection,
)


def _coerce_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []

    parsed: list[str] = []
    for item in value:
        if isinstance(item, str) and item:
            parsed.append(item)
    return parsed


def resolve_modules_for_subject(
    *,
    tenant_id: str | None,
    subject: str,
    scopes: Sequence[str],
    roles: Sequence[str],
) -> list[str]:
    if tenant_id is None:
        return []

    managed_modules = _get_managed_modules(tenant_id=tenant_id, subject=subject)
    if managed_modules is not None:
        return managed_modules

    return default_modules_for_claims(roles=roles, scopes=scopes)


def resolve_modules_from_auth_context(auth_context: Mapping[str, object]) -> list[str]:
    tenant_id = auth_context.get("tenant_id")
    subject = auth_context.get("subject")
    if not isinstance(tenant_id, str) or not isinstance(subject, str):
        return []

    scopes = _coerce_string_list(auth_context.get("scopes"))
    roles = _coerce_string_list(auth_context.get("roles"))
    return resolve_modules_for_subject(
        tenant_id=tenant_id,
        subject=subject,
        scopes=scopes,
        roles=roles,
    )


def get_managed_modules(*, tenant_id: str, subject: str) -> list[str]:
    managed_modules = _get_managed_modules(tenant_id=tenant_id, subject=subject)
    if managed_modules is not None:
        return managed_modules

    return ["dashboard"]


def update_managed_modules(
    *,
    tenant_id: str,
    subject: str,
    enabled_modules: Sequence[str],
    actor_subject: str,
) -> dict[str, object]:
    normalized_modules = normalize_modules(enabled_modules)
    occurred_at = (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )

    def _operation(connection):
        entitlement_repository = SqliteManagedEntitlementRepository(connection)
        audit_repository = SqliteAuditEventRepository(connection)
        try:
            entitlement_repository.upsert_modules(
                tenant_id=tenant_id,
                subject=subject,
                enabled_modules=normalized_modules,
                actor_subject=actor_subject,
                occurred_at=occurred_at,
                commit=False,
            )
            audit_metadata = audit_repository.create_event(
                action=AUDIT_ACTION_ENTITLEMENTS_UPDATED,
                actor_subject=actor_subject,
                target_subject=subject,
                tenant_id=tenant_id,
                outcome="success",
                occurred_at=occurred_at,
                commit=False,
            )
            connection.commit()
            return audit_metadata
        except Exception:
            connection.rollback()
            raise

    audit_metadata = run_with_storage_connection(_operation)

    return {
        "tenant_id": tenant_id,
        "subject": subject,
        "enabled_modules": normalized_modules,
        "audit_metadata": audit_metadata,
    }


def reset_entitlements_state() -> None:
    def _operation(connection):
        repository = SqliteManagedEntitlementRepository(connection)
        repository.clear()

    run_with_storage_connection(_operation)
    clear_audit_events_by_action(action=AUDIT_ACTION_ENTITLEMENTS_UPDATED)


def _get_managed_modules(*, tenant_id: str, subject: str) -> list[str] | None:
    def _operation(connection):
        repository = SqliteManagedEntitlementRepository(connection)
        return repository.get_modules(tenant_id=tenant_id, subject=subject)

    return run_with_storage_connection(_operation)


def _upsert_managed_modules(
    *,
    tenant_id: str,
    subject: str,
    enabled_modules: list[str],
    actor_subject: str,
    occurred_at: str,
) -> None:
    def _operation(connection):
        repository = SqliteManagedEntitlementRepository(connection)
        repository.upsert_modules(
            tenant_id=tenant_id,
            subject=subject,
            enabled_modules=enabled_modules,
            actor_subject=actor_subject,
            occurred_at=occurred_at,
        )

    run_with_storage_connection(_operation)
