import pytest
from fastapi.testclient import TestClient

from decider_api.api.dependencies.auth import (
    get_authenticated_auth_context,
    get_token_validator,
)
from decider_api.app import app
from decider_api.application.entitlements import reset_entitlements_state
from test_auth_context_authn import _VALID_TOKEN, _build_validator


@pytest.fixture(autouse=True)
def _reset_entitlements() -> None:
    reset_entitlements_state()
    yield
    reset_entitlements_state()


def _admin_auth_context() -> dict[str, object]:
    return {
        "authenticated": True,
        "subject": "admin-1",
        "tenant_id": "acme",
        "scopes": ["entitlements:write", "read:data", "watchlist:view"],
        "roles": ["admin"],
    }


def _user_auth_context() -> dict[str, object]:
    return {
        "authenticated": True,
        "subject": "user-123",
        "tenant_id": "acme",
        "scopes": ["read:data", "watchlist:view"],
        "roles": ["user"],
    }


def test_v1_tenant_resources_endpoint_allows_same_tenant() -> None:
    validator = _build_validator()
    app.dependency_overrides[get_token_validator] = lambda: validator
    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/tenants/acme/resources",
            headers={"Authorization": f"Bearer {_VALID_TOKEN}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "tenant_id": "acme",
        "resources": [],
    }


def test_v1_tenant_resources_endpoint_rejects_missing_token() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/tenants/acme/resources")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or expired token."}


def test_v1_tenant_resources_endpoint_blocks_cross_tenant_access() -> None:
    validator = _build_validator()
    app.dependency_overrides[get_token_validator] = lambda: validator
    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/tenants/other-tenant/resources",
            headers={"Authorization": f"Bearer {_VALID_TOKEN}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}


def test_admin_can_update_entitlements_and_change_access() -> None:
    app.dependency_overrides[get_authenticated_auth_context] = _admin_auth_context
    client = TestClient(app)
    update_response = client.put(
        "/api/v1/tenants/acme/entitlements/user-123",
        json={"enabled_modules": ["dashboard", "watchlist"]},
    )

    assert update_response.status_code == 200
    body = update_response.json()
    assert body["tenant_id"] == "acme"
    assert body["subject"] == "user-123"
    assert body["enabled_modules"] == ["dashboard", "watchlist"]
    assert body["audit_metadata"]["action"] == "entitlements.updated"
    assert body["audit_metadata"]["actor_subject"] == "admin-1"

    app.dependency_overrides[get_authenticated_auth_context] = _user_auth_context
    access_response = client.get("/api/v1/tenants/acme/resources")

    app.dependency_overrides.clear()

    assert access_response.status_code == 403
    assert access_response.json() == {"detail": "Forbidden"}


def test_non_admin_cannot_update_entitlements() -> None:
    app.dependency_overrides[get_authenticated_auth_context] = _user_auth_context
    try:
        client = TestClient(app)
        response = client.put(
            "/api/v1/tenants/acme/entitlements/user-123",
            json={"enabled_modules": ["dashboard"]},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}


def test_admin_cannot_manage_other_tenant_entitlements() -> None:
    app.dependency_overrides[get_authenticated_auth_context] = _admin_auth_context
    try:
        client = TestClient(app)
        response = client.put(
            "/api/v1/tenants/other-tenant/entitlements/user-123",
            json={"enabled_modules": ["dashboard"]},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}


def test_update_entitlements_rejects_unknown_modules() -> None:
    app.dependency_overrides[get_authenticated_auth_context] = _admin_auth_context
    try:
        client = TestClient(app)
        response = client.put(
            "/api/v1/tenants/acme/entitlements/user-123",
            json={"enabled_modules": ["dashboard", "unknown-module"]},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert "Unsupported module" in response.json()["detail"]
