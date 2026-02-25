def is_tenant_access_allowed(
    *,
    requested_tenant_id: str,
    actor_tenant_id: str | None,
) -> bool:
    normalized_requested_tenant = requested_tenant_id.strip()
    normalized_actor_tenant = (actor_tenant_id or "").strip()
    if not normalized_requested_tenant or not normalized_actor_tenant:
        return False
    return normalized_requested_tenant == normalized_actor_tenant
