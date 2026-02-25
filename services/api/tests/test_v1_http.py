from fastapi.testclient import TestClient

from decider_api.api.dependencies.auth import get_token_validator
from decider_api.app import app
from test_auth_context_authn import _VALID_TOKEN, _build_validator


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
