import pytest
from fastapi.testclient import TestClient

from decider_api.app import app


@pytest.mark.smoke
def test_health_endpoint_returns_exact_contract() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
