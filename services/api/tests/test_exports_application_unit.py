from decider_api.application.exports import (
    create_export_result,
    list_export_audit_events,
    record_export_audit_event,
    reset_export_state,
)


def setup_function() -> None:
    reset_export_state()


def teardown_function() -> None:
    reset_export_state()


def test_create_export_result_returns_metadata_only_contract() -> None:
    response = create_export_result(tenant_id="acme", actor_subject="user-1")

    assert response["tenant_id"] == "acme"
    assert response["export_id"].startswith("export-")
    assert response["status"] == "accepted"
    assert "payload" not in response

    audit_metadata = response["audit_metadata"]
    assert audit_metadata["action"] == "export.requested"
    assert audit_metadata["outcome"] == "success"
    assert "reason" not in audit_metadata


def test_record_export_audit_event_tracks_forbidden_attempts() -> None:
    audit_metadata = record_export_audit_event(
        tenant_id="acme",
        actor_subject="user-1",
        outcome="forbidden",
        reason="missing_scope",
    )

    assert audit_metadata["outcome"] == "forbidden"
    assert audit_metadata["reason"] == "missing_scope"

    stored_events = list_export_audit_events()
    assert len(stored_events) == 1
    assert stored_events[0] == audit_metadata


def test_list_export_audit_events_returns_defensive_copies() -> None:
    record_export_audit_event(
        tenant_id="acme",
        actor_subject="user-1",
        outcome="forbidden",
        reason="tenant_mismatch",
    )

    first_read = list_export_audit_events()
    first_read[0]["tenant_id"] = "other"

    second_read = list_export_audit_events()
    assert second_read[0]["tenant_id"] == "acme"
