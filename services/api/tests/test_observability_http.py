import logging
import re

from fastapi.testclient import TestClient

from decider_api.app import app


def test_health_propagates_incoming_correlation_id() -> None:
    client = TestClient(app)

    response = client.get(
        "/api/v1/health",
        headers={"X-Correlation-ID": "trace-abc-123"},
    )

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == "trace-abc-123"


def test_health_generates_correlation_id_when_missing() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    correlation_id = response.headers.get("X-Correlation-ID")
    assert correlation_id is not None
    assert re.fullmatch(r"[A-Za-z0-9._-]{1,128}", correlation_id) is not None


def test_metrics_endpoint_exposes_http_metrics() -> None:
    client = TestClient(app)

    health_response = client.get("/api/v1/health")
    assert health_response.status_code == 200

    response = client.get("/metrics")

    assert response.status_code == 200
    body = response.text
    assert "decider_http_requests_total" in body
    assert 'method="GET"' in body
    assert 'route="/api/v1/health"' in body
    assert 'status_code="200"' in body


def test_request_lifecycle_log_contains_correlation_id(caplog) -> None:
    caplog.set_level(logging.INFO, logger="decider_api.access")
    client = TestClient(app)

    response = client.get(
        "/api/v1/health",
        headers={"X-Correlation-ID": "trace-log-42"},
    )

    assert response.status_code == 200

    matching_records = [
        record
        for record in caplog.records
        if getattr(record, "event", None) == "http.request.completed"
        and getattr(record, "http_route", None) == "/api/v1/health"
    ]
    assert matching_records
    assert getattr(matching_records[-1], "correlation_id", None) == "trace-log-42"
