from fastapi.testclient import TestClient

from decider_api.app import app


def test_v1_tenant_resources_endpoint_is_tenant_scoped() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/tenants/acme/resources")

    assert response.status_code == 200
    assert response.json() == {
        "tenant_id": "acme",
        "resources": [],
    }
