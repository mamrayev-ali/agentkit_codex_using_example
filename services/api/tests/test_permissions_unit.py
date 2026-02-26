import pytest

from decider_api.application.entitlements import (
    resolve_modules_for_subject,
    reset_entitlements_state,
    update_managed_modules,
)
from decider_api.domain.permissions import (
    default_modules_for_claims,
    has_scope,
    is_admin_actor,
    normalize_modules,
)


def setup_function() -> None:
    reset_entitlements_state()


def teardown_function() -> None:
    reset_entitlements_state()


def test_default_modules_for_claims_uses_roles_and_scopes() -> None:
    modules = default_modules_for_claims(
        roles=["user", "viewer"],
        scopes=["watchlist:view"],
    )

    assert modules == ["dashboard", "dossiers", "watchlist"]


def test_is_admin_actor_accepts_role_or_scope() -> None:
    assert is_admin_actor(roles=["admin"], scopes=[])
    assert is_admin_actor(roles=[], scopes=["entitlements:write"])
    assert not is_admin_actor(roles=["user"], scopes=["read:data"])


def test_normalize_modules_rejects_unknown_modules() -> None:
    with pytest.raises(ValueError, match="Unsupported module"):
        normalize_modules(["dashboard", "unknown"])


def test_resolve_modules_for_subject_prefers_managed_state() -> None:
    update_managed_modules(
        tenant_id="acme",
        subject="user-123",
        enabled_modules=["dashboard", "watchlist"],
        actor_subject="admin-1",
    )

    modules = resolve_modules_for_subject(
        tenant_id="acme",
        subject="user-123",
        roles=["user"],
        scopes=["read:data"],
    )

    assert modules == ["dashboard", "watchlist"]


def test_has_scope_is_case_insensitive_and_trim_aware() -> None:
    assert has_scope(required_scope="export:data", scopes=["read:data", " Export:Data "])
    assert not has_scope(required_scope="export:data", scopes=["read:data"])
