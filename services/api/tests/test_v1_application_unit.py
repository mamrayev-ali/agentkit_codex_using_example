from decider_api.application.auth_context import build_auth_context_response
from decider_api.application.tenant_resources import list_tenant_base_resources


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
    }


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
