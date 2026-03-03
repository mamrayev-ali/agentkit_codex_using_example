from decider_api.demo_seed import (
    build_demo_seed_manifest,
    collect_seeded_demo_state,
    reset_demo_state_for_connection,
    seed_demo_state_for_connection,
)
from decider_api.infrastructure.storage import apply_initial_schema, create_sqlite_connection


def test_demo_seed_manifest_exposes_canonical_walkthrough_state() -> None:
    manifest = build_demo_seed_manifest()

    assert manifest["seed_version"] == "2026-03-02"
    assert [item["tenant_id"] for item in manifest["tenants"]] == ["acme", "umbrella"]
    assert [item["subject"] for item in manifest["actors"]] == [
        "analyst@acme.decider.local",
        "admin@acme.decider.local",
    ]
    assert [item["dossier_id"] for item in manifest["dossiers"]] == [
        "dos-acme-org-001",
        "dos-acme-person-001",
        "dos-umbrella-org-001",
    ]
    assert [item["request_id"] for item in manifest["search_requests"]] == [
        "req-acme-001",
        "req-acme-002",
        "req-umbrella-001",
    ]
    assert [item["event_id"] for item in manifest["audit_events"]] == [
        "entitlements-updated-1",
        "export-audit-2",
    ]


def test_demo_seed_is_repeatable_for_connection() -> None:
    connection = create_sqlite_connection("sqlite:///:memory:")
    apply_initial_schema(connection)

    reset_demo_state_for_connection(connection)
    seed_demo_state_for_connection(connection)
    first_state = collect_seeded_demo_state(connection)

    reset_demo_state_for_connection(connection)
    seed_demo_state_for_connection(connection)
    second_state = collect_seeded_demo_state(connection)

    assert first_state == second_state
    assert [item["enabled_modules"] for item in second_state["managed_entitlements"]] == [
        ["dashboard", "dossiers"],
        ["dashboard", "dossiers", "watchlist"],
    ]
    assert second_state["tenant_audit_review"]["umbrella"] == []


def test_demo_seed_reset_clears_existing_data_before_reseed() -> None:
    connection = create_sqlite_connection("sqlite:///:memory:")
    apply_initial_schema(connection)

    seed_demo_state_for_connection(connection)
    connection.execute(
        """
        INSERT INTO dossiers (
            tenant_id,
            dossier_id,
            subject_name,
            subject_type,
            created_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        ("acme", "dos-extra-999", "Transient Subject", "person", "2026-03-02T10:00:00Z"),
    )
    connection.commit()

    reset_demo_state_for_connection(connection)
    seed_demo_state_for_connection(connection)
    state = collect_seeded_demo_state(connection)

    assert [item["dossier_id"] for item in state["dossiers"]] == [
        "dos-acme-org-001",
        "dos-acme-person-001",
        "dos-umbrella-org-001",
    ]
    assert [item["event_id"] for item in state["audit_events"]] == [
        "entitlements-updated-1",
        "export-audit-2",
    ]
