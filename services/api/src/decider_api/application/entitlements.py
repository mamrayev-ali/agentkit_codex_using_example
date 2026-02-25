from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from itertools import count
from threading import Lock

from decider_api.domain.permissions import (
    default_modules_for_claims,
    normalize_modules,
)

_MANAGED_ENTITLEMENTS: dict[tuple[str, str], tuple[str, ...]] = {}
_AUDIT_SEQUENCE = count(1)
_STATE_LOCK = Lock()


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

    lookup_key = (tenant_id, subject)
    managed_modules = _MANAGED_ENTITLEMENTS.get(lookup_key)
    if managed_modules is not None:
        return list(managed_modules)

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
    managed_modules = _MANAGED_ENTITLEMENTS.get((tenant_id, subject))
    if managed_modules is not None:
        return list(managed_modules)

    return ["dashboard"]


def update_managed_modules(
    *,
    tenant_id: str,
    subject: str,
    enabled_modules: Sequence[str],
    actor_subject: str,
) -> dict[str, object]:
    normalized_modules = normalize_modules(enabled_modules)

    with _STATE_LOCK:
        _MANAGED_ENTITLEMENTS[(tenant_id, subject)] = tuple(normalized_modules)
        sequence_value = next(_AUDIT_SEQUENCE)

    occurred_at = (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )

    return {
        "tenant_id": tenant_id,
        "subject": subject,
        "enabled_modules": normalized_modules,
        "audit_metadata": {
            "event_id": f"entitlements-updated-{sequence_value}",
            "action": "entitlements.updated",
            "actor_subject": actor_subject,
            "target_subject": subject,
            "tenant_id": tenant_id,
            "occurred_at": occurred_at,
        },
    }


def reset_entitlements_state() -> None:
    global _AUDIT_SEQUENCE

    with _STATE_LOCK:
        _MANAGED_ENTITLEMENTS.clear()
        _AUDIT_SEQUENCE = count(1)
