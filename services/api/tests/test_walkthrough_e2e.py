import pytest
from fastapi.testclient import TestClient

from decider_api.api.dependencies.auth import get_token_validator
from decider_api.app import app
from decider_api.demo_seed import build_demo_seed_manifest, reseed_demo_state

pytestmark = [pytest.mark.e2e_api]


class _StaticClaimsValidator:
    tenant_claim_names = ("tenant_id", "tenant", "org_id")

    def __init__(self, claims: dict[str, object]) -> None:
        self._claims = dict(claims)

    def validate_authorization_header(self, authorization: str | None) -> dict[str, object]:
        if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
            raise ValueError("Authorization header must use Bearer token.")
        return dict(self._claims)


def _claims_for_actor(
    *,
    subject: str,
    tenant_id: str,
    scopes: list[str],
    roles: list[str],
) -> dict[str, object]:
    return {
        "sub": subject,
        "tenant_id": tenant_id,
        "scope": " ".join(scopes),
        "roles": roles,
    }


def _set_claims_validator(claims: dict[str, object]) -> None:
    app.dependency_overrides[get_token_validator] = lambda: _StaticClaimsValidator(claims)


def _authorization_headers() -> dict[str, str]:
    return {"Authorization": "Bearer walkthrough-token"}


@pytest.fixture(autouse=True)
def _reseed_runtime_baseline() -> None:
    reseed_demo_state()
    yield
    app.dependency_overrides.clear()


def test_demo_user_walkthrough_matches_seeded_api_baseline() -> None:
    manifest = build_demo_seed_manifest()
    _set_claims_validator(
        _claims_for_actor(
            subject="demo-user",
            tenant_id="acme",
            scopes=["read:data", "watchlist:view", "export:data"],
            roles=["user"],
        )
    )

    client = TestClient(app)

    auth_context_response = client.get("/api/v1/auth/context", headers=_authorization_headers())
    dossiers_response = client.get(
        "/api/v1/tenants/acme/dossiers",
        headers=_authorization_headers(),
    )
    searches_response = client.get(
        "/api/v1/tenants/acme/search-requests",
        headers=_authorization_headers(),
    )
    export_response = client.post(
        "/api/v1/tenants/acme/exports",
        headers=_authorization_headers(),
    )
    cross_tenant_response = client.get(
        "/api/v1/tenants/umbrella/dossiers",
        headers=_authorization_headers(),
    )

    assert auth_context_response.status_code == 200
    assert auth_context_response.json()["tenant_id"] == "acme"
    assert auth_context_response.json()["module_entitlements"] == ["dashboard", "dossiers"]

    assert dossiers_response.status_code == 200
    assert {item["dossier_id"] for item in dossiers_response.json()["dossiers"]} == {
        manifest["dossiers"][0]["dossier_id"],
        manifest["dossiers"][1]["dossier_id"],
    }

    assert searches_response.status_code == 200
    assert {
        item["request_id"]: item["status"] for item in searches_response.json()["search_requests"]
    } == {
        manifest["search_requests"][0]["request_id"]: "queued",
        manifest["search_requests"][1]["request_id"]: "completed",
    }

    assert export_response.status_code == 200
    assert export_response.json()["tenant_id"] == "acme"
    assert export_response.json()["status"] == "accepted"
    assert export_response.json()["audit_metadata"]["outcome"] == "success"

    assert cross_tenant_response.status_code == 403
    assert cross_tenant_response.json() == {"detail": "Forbidden"}


def test_demo_admin_update_changes_demo_user_auth_context_and_audit_trail() -> None:
    admin_claims = _claims_for_actor(
        subject="demo-admin",
        tenant_id="acme",
        scopes=["read:data", "watchlist:view", "export:data", "entitlements:write"],
        roles=["admin"],
    )
    demo_user_claims = _claims_for_actor(
        subject="demo-user",
        tenant_id="acme",
        scopes=["read:data", "watchlist:view", "export:data"],
        roles=["user"],
    )

    _set_claims_validator(admin_claims)
    client = TestClient(app)

    entitlements_before_response = client.get(
        "/api/v1/tenants/acme/entitlements/demo-user",
        headers=_authorization_headers(),
    )
    entitlements_update_response = client.put(
        "/api/v1/tenants/acme/entitlements/demo-user",
        headers=_authorization_headers(),
        json={"enabled_modules": ["dashboard", "dossiers", "watchlist"]},
    )
    audit_events_response = client.get(
        "/api/v1/tenants/acme/audit/events",
        headers=_authorization_headers(),
    )

    assert entitlements_before_response.status_code == 200
    assert entitlements_before_response.json()["enabled_modules"] == ["dashboard", "dossiers"]

    assert entitlements_update_response.status_code == 200
    assert entitlements_update_response.json()["enabled_modules"] == [
        "dashboard",
        "dossiers",
        "watchlist",
    ]
    assert (
        entitlements_update_response.json()["audit_metadata"]["action"]
        == "entitlements.updated"
    )

    assert audit_events_response.status_code == 200
    assert [item["action"] for item in audit_events_response.json()["events"]] == [
        "entitlements.updated",
        "export.requested",
        "entitlements.updated",
    ]

    _set_claims_validator(demo_user_claims)
    auth_context_after_response = client.get(
        "/api/v1/auth/context",
        headers=_authorization_headers(),
    )

    assert auth_context_after_response.status_code == 200
    assert auth_context_after_response.json()["subject"] == "demo-user"
    assert auth_context_after_response.json()["module_entitlements"] == [
        "dashboard",
        "dossiers",
        "watchlist",
    ]
