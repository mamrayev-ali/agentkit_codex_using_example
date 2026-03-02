import pytest
from fastapi.testclient import TestClient

import decider_api.application.search_requests as search_request_application
from decider_api.api.dependencies.auth import (
    get_authenticated_auth_context,
    get_token_validator,
)
from decider_api.app import app
from decider_api.application.entitlements import reset_entitlements_state
from decider_api.application.exports import (
    list_export_audit_events,
    reset_export_state,
)
from decider_api.infrastructure.storage import run_with_storage_connection
from test_auth_context_authn import _VALID_TOKEN, _build_validator

pytestmark = [pytest.mark.e2e_api]


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    reset_entitlements_state()
    reset_export_state()
    _reset_dossier_search_state()
    yield
    _reset_dossier_search_state()
    reset_entitlements_state()
    reset_export_state()


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


def _dashboard_only_auth_context() -> dict[str, object]:
    return {
        "authenticated": True,
        "subject": "dashboard-user-1",
        "tenant_id": "acme",
        "scopes": [],
        "roles": [],
    }


def _export_user_auth_context() -> dict[str, object]:
    return {
        "authenticated": True,
        "subject": "export-user-1",
        "tenant_id": "acme",
        "scopes": ["read:data", "watchlist:view", "export:data"],
        "roles": ["user"],
    }


def _reset_dossier_search_state() -> None:
    def _operation(connection) -> None:
        connection.execute("DELETE FROM search_requests")
        connection.execute("DELETE FROM dossiers")
        connection.commit()

    run_with_storage_connection(_operation)


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


def test_dossier_and_search_request_user_workflow() -> None:
    app.dependency_overrides[get_authenticated_auth_context] = _user_auth_context

    def _fake_enqueue_ingestion_job(**kwargs):
        assert kwargs["tenant_id"] == "acme"
        assert kwargs["requested_by"] == "user-123"
        return {
            "task_id": "task-1",
            "queue_status": "queued",
        }

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        search_request_application,
        "enqueue_ingestion_job",
        _fake_enqueue_ingestion_job,
    )
    try:
        client = TestClient(app)
        dossier_response = client.post(
            "/api/v1/tenants/acme/dossiers",
            json={"subject_name": "Acme LLP", "subject_type": "organization"},
        )
        assert dossier_response.status_code == 201
        dossier_body = dossier_response.json()
        dossier_id = dossier_body["dossier_id"]

        dossier_list_response = client.get("/api/v1/tenants/acme/dossiers")
        assert dossier_list_response.status_code == 200
        assert dossier_list_response.json()["dossiers"][0]["dossier_id"] == dossier_id

        dossier_detail_response = client.get(f"/api/v1/tenants/acme/dossiers/{dossier_id}")
        assert dossier_detail_response.status_code == 200
        assert dossier_detail_response.json()["subject_name"] == "Acme LLP"

        search_response = client.post(
            "/api/v1/tenants/acme/search-requests",
            json={
                "dossier_id": dossier_id,
                "query_text": "open sanctions check",
                "source_key": "gov-registry",
                "remote_url": "https://example.com/api/company",
            },
        )
        assert search_response.status_code == 201
        search_body = search_response.json()
        request_id = search_body["search_request"]["request_id"]
        assert search_body["search_request"]["status"] == "queued"
        assert search_body["enqueue_metadata"] == {
            "task_id": "task-1",
            "queue_status": "queued",
            "result_status": None,
        }

        search_list_response = client.get("/api/v1/tenants/acme/search-requests")
        assert search_list_response.status_code == 200
        assert search_list_response.json()["search_requests"][0]["request_id"] == request_id

        search_detail_response = client.get(
            f"/api/v1/tenants/acme/search-requests/{request_id}"
        )
        assert search_detail_response.status_code == 200
        assert search_detail_response.json()["dossier_id"] == dossier_id

        search_status_response = client.get(
            f"/api/v1/tenants/acme/search-requests/{request_id}/status"
        )
        assert search_status_response.status_code == 200
        assert search_status_response.json() == {
            "tenant_id": "acme",
            "request_id": request_id,
            "status": "queued",
        }
    finally:
        app.dependency_overrides.clear()
        monkeypatch.undo()


def test_dossier_endpoints_reject_missing_dossier_module_entitlement() -> None:
    app.dependency_overrides[get_authenticated_auth_context] = _dashboard_only_auth_context
    try:
        client = TestClient(app)
        response = client.get("/api/v1/tenants/acme/dossiers")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}


def test_search_request_endpoint_blocks_cross_tenant_access() -> None:
    app.dependency_overrides[get_authenticated_auth_context] = _user_auth_context
    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/tenants/other-tenant/search-requests",
            json={
                "dossier_id": "dos-001",
                "query_text": "query",
                "source_key": "gov-registry",
                "remote_url": "https://example.com/api/company",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}


def test_search_request_creation_returns_404_for_missing_dossier() -> None:
    app.dependency_overrides[get_authenticated_auth_context] = _user_auth_context

    def _fake_enqueue_ingestion_job(**kwargs):
        return {"task_id": "task-1", "queue_status": "queued"}

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        search_request_application,
        "enqueue_ingestion_job",
        _fake_enqueue_ingestion_job,
    )
    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/tenants/acme/search-requests",
            json={
                "dossier_id": "missing-dossier",
                "query_text": "query",
                "source_key": "gov-registry",
                "remote_url": "https://example.com/api/company",
            },
        )
    finally:
        app.dependency_overrides.clear()
        monkeypatch.undo()

    assert response.status_code == 404
    assert response.json() == {"detail": "Dossier not found."}


def test_search_request_creation_returns_422_for_invalid_remote_url() -> None:
    app.dependency_overrides[get_authenticated_auth_context] = _user_auth_context
    try:
        client = TestClient(app)
        dossier_response = client.post(
            "/api/v1/tenants/acme/dossiers",
            json={"subject_name": "Acme LLP", "subject_type": "organization"},
        )
        dossier_id = dossier_response.json()["dossier_id"]
        response = client.post(
            "/api/v1/tenants/acme/search-requests",
            json={
                "dossier_id": dossier_id,
                "query_text": "query",
                "source_key": "gov-registry",
                "remote_url": "http://127.0.0.1/private",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert "blocked IP range" in response.json()["detail"]


def test_search_request_status_returns_404_when_request_is_missing() -> None:
    app.dependency_overrides[get_authenticated_auth_context] = _user_auth_context
    try:
        client = TestClient(app)
        response = client.get("/api/v1/tenants/acme/search-requests/missing/status")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Not found."}


@pytest.mark.smoke
def test_export_endpoint_rejects_missing_scope_and_audits_attempt() -> None:
    app.dependency_overrides[get_authenticated_auth_context] = _user_auth_context
    try:
        client = TestClient(app)
        response = client.post("/api/v1/tenants/acme/exports")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}

    audit_events = list_export_audit_events()
    assert len(audit_events) == 1
    assert audit_events[0]["tenant_id"] == "acme"
    assert audit_events[0]["actor_subject"] == "user-123"
    assert audit_events[0]["outcome"] == "forbidden"
    assert audit_events[0]["reason"] == "missing_scope"


def test_export_endpoint_rejects_cross_tenant_and_audits_attempt() -> None:
    app.dependency_overrides[get_authenticated_auth_context] = _export_user_auth_context
    try:
        client = TestClient(app)
        response = client.post("/api/v1/tenants/other-tenant/exports")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}

    audit_events = list_export_audit_events()
    assert len(audit_events) == 1
    assert audit_events[0]["tenant_id"] == "other-tenant"
    assert audit_events[0]["actor_subject"] == "export-user-1"
    assert audit_events[0]["outcome"] == "forbidden"
    assert audit_events[0]["reason"] == "tenant_mismatch"


@pytest.mark.smoke
def test_export_endpoint_accepts_scope_and_tenant_and_audits_success() -> None:
    app.dependency_overrides[get_authenticated_auth_context] = _export_user_auth_context
    try:
        client = TestClient(app)
        response = client.post("/api/v1/tenants/acme/exports")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == "acme"
    assert body["export_id"].startswith("export-")
    assert body["status"] == "accepted"
    assert body["audit_metadata"]["action"] == "export.requested"
    assert body["audit_metadata"]["actor_subject"] == "export-user-1"
    assert body["audit_metadata"]["outcome"] == "success"

    audit_events = list_export_audit_events()
    assert len(audit_events) == 1
    assert audit_events[0]["outcome"] == "success"


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


def test_admin_can_query_tenant_audit_events() -> None:
    app.dependency_overrides[get_authenticated_auth_context] = _admin_auth_context
    client = TestClient(app)
    entitlement_response = client.put(
        "/api/v1/tenants/acme/entitlements/user-123",
        json={"enabled_modules": ["dashboard", "watchlist"]},
    )
    assert entitlement_response.status_code == 200

    app.dependency_overrides[get_authenticated_auth_context] = _export_user_auth_context
    export_response = client.post("/api/v1/tenants/acme/exports")
    assert export_response.status_code == 200

    app.dependency_overrides[get_authenticated_auth_context] = _admin_auth_context
    audit_response = client.get("/api/v1/tenants/acme/audit/events")
    app.dependency_overrides.clear()

    assert audit_response.status_code == 200
    body = audit_response.json()
    assert body["tenant_id"] == "acme"
    assert len(body["events"]) == 2
    assert {item["action"] for item in body["events"]} == {
        "entitlements.updated",
        "export.requested",
    }


def test_non_admin_cannot_query_tenant_audit_events() -> None:
    app.dependency_overrides[get_authenticated_auth_context] = _user_auth_context
    try:
        client = TestClient(app)
        response = client.get("/api/v1/tenants/acme/audit/events")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}
