from decider_api.domain.tenant_guard import is_tenant_access_allowed


def test_tenant_guard_allows_same_tenant() -> None:
    assert is_tenant_access_allowed(
        requested_tenant_id="acme",
        actor_tenant_id="acme",
    )


def test_tenant_guard_blocks_cross_tenant_access() -> None:
    assert not is_tenant_access_allowed(
        requested_tenant_id="acme",
        actor_tenant_id="other-tenant",
    )


def test_tenant_guard_blocks_missing_actor_tenant() -> None:
    assert not is_tenant_access_allowed(
        requested_tenant_id="acme",
        actor_tenant_id=None,
    )
