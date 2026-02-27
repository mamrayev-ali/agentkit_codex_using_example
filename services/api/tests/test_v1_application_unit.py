from decider_api.application.auth_context import build_auth_context_response
from decider_api.application.entitlements import (
    reset_entitlements_state,
    update_managed_modules,
)
from decider_api.application.tenant_resources import list_tenant_base_resources
from decider_api.infrastructure.storage import clear_runtime_storage_cache


def setup_function() -> None:
    reset_entitlements_state()


def teardown_function() -> None:
    reset_entitlements_state()


def test_auth_context_response_maps_claims_consistently() -> None:
    claims = {
        "sub": "user-123",
        "tenant_id": "acme",
        "scope": "read:data export:data",
        "scp": ["read:data", "watchlist:view"],
        "roles": ["user"],
        "realm_access": {"roles": ["analyst", "user"]},
        "resource_access": {
            "decider-api": {"roles": ["operator"]},
            "frontend": {"roles": ["viewer", "operator"]},
        },
    }

    response = build_auth_context_response(
        claims=claims,
        tenant_claim_names=("tenant_id", "tenant"),
    )

    assert response == {
        "authenticated": True,
        "subject": "user-123",
        "tenant_id": "acme",
        "scopes": ["read:data", "export:data", "watchlist:view"],
        "roles": ["user", "analyst", "operator", "viewer"],
        "module_entitlements": ["dashboard", "dossiers", "watchlist"],
    }


def test_auth_context_response_reflects_managed_entitlements() -> None:
    update_managed_modules(
        tenant_id="acme",
        subject="user-123",
        enabled_modules=["dashboard", "watchlist"],
        actor_subject="admin-1",
    )
    claims = {
        "sub": "user-123",
        "tenant_id": "acme",
        "scope": "read:data watchlist:view",
        "roles": ["user"],
    }

    response = build_auth_context_response(
        claims=claims,
        tenant_claim_names=("tenant_id",),
    )

    assert response["module_entitlements"] == ["dashboard", "watchlist"]


def test_auth_context_response_returns_fresh_lists() -> None:
    claims = {
        "sub": "user-123",
        "tenant_id": "acme",
        "scope": "read:data",
        "realm_access": {"roles": ["analyst"]},
    }

    first = build_auth_context_response(
        claims=claims,
        tenant_claim_names=("tenant_id",),
    )
    first["scopes"].append("export:data")
    first["roles"].append("admin")
    first["module_entitlements"].append("watchlist")

    second = build_auth_context_response(
        claims=claims,
        tenant_claim_names=("tenant_id",),
    )

    assert second == {
        "authenticated": True,
        "subject": "user-123",
        "tenant_id": "acme",
        "scopes": ["read:data"],
        "roles": ["analyst"],
        "module_entitlements": ["dashboard", "dossiers", "watchlist"],
    }


def test_tenant_resources_response_is_immutable_between_calls() -> None:
    first = list_tenant_base_resources("acme")
    assert isinstance(first["resources"], list)
    first["resources"].append({"resource_id": "r1", "name": "X"})

    second = list_tenant_base_resources("acme")

    assert second == {
        "tenant_id": "acme",
        "resources": [],
    }


def test_managed_entitlements_persist_across_runtime_cache_reset() -> None:
    update_managed_modules(
        tenant_id="acme",
        subject="user-123",
        enabled_modules=["dashboard"],
        actor_subject="admin-1",
    )
    clear_runtime_storage_cache()

    claims = {
        "sub": "user-123",
        "tenant_id": "acme",
        "scope": "read:data watchlist:view",
        "roles": ["user"],
    }
    response = build_auth_context_response(
        claims=claims,
        tenant_claim_names=("tenant_id",),
    )

    assert response["module_entitlements"] == ["dashboard"]
