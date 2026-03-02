from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from sqlite3 import Connection

from decider_api.domain.permissions import normalize_modules
from decider_api.infrastructure.ingestion.tasks import reset_ingestion_runtime_state
from decider_api.infrastructure.storage import (
    SqliteAuditEventRepository,
    SqliteManagedEntitlementRepository,
    clear_runtime_storage_cache,
    run_with_storage_connection,
)

DEMO_SEED_VERSION = "2026-03-02"

DEMO_TENANTS: tuple[dict[str, str], ...] = (
    {
        "tenant_id": "acme",
        "display_name": "Acme Holdings",
        "purpose": "Primary local walkthrough tenant.",
    },
    {
        "tenant_id": "umbrella",
        "display_name": "Umbrella Ventures",
        "purpose": "Secondary tenant used to prove tenant isolation.",
    },
)

DEMO_ACTORS: tuple[dict[str, object], ...] = (
    {
        "subject": "demo-user",
        "tenant_id": "acme",
        "roles": ["user"],
        "scopes": ["read:data", "watchlist:view", "export:data"],
        "description": "Primary end-user account from the local Keycloak realm.",
    },
    {
        "subject": "demo-admin",
        "tenant_id": "acme",
        "roles": ["admin"],
        "scopes": ["read:data", "watchlist:view", "export:data", "entitlements:write"],
        "description": "Tenant admin account from the local Keycloak realm.",
    },
)

DEMO_DOSSIERS: tuple[dict[str, str], ...] = (
    {
        "tenant_id": "acme",
        "dossier_id": "dos-acme-org-001",
        "subject_name": "Acme Logistics LLP",
        "subject_type": "organization",
        "created_at": "2026-03-02T09:00:00Z",
    },
    {
        "tenant_id": "acme",
        "dossier_id": "dos-acme-person-001",
        "subject_name": "Aida Sarsen",
        "subject_type": "person",
        "created_at": "2026-03-02T09:05:00Z",
    },
    {
        "tenant_id": "umbrella",
        "dossier_id": "dos-umbrella-org-001",
        "subject_name": "Umbrella Industrial JSC",
        "subject_type": "organization",
        "created_at": "2026-03-02T09:10:00Z",
    },
)

DEMO_SEARCH_REQUESTS: tuple[dict[str, str], ...] = (
    {
        "tenant_id": "acme",
        "request_id": "req-acme-001",
        "dossier_id": "dos-acme-org-001",
        "query_text": "open sanctions check",
        "status": "queued",
        "created_at": "2026-03-02T09:15:00Z",
    },
    {
        "tenant_id": "acme",
        "request_id": "req-acme-002",
        "dossier_id": "dos-acme-person-001",
        "query_text": "court record review",
        "status": "completed",
        "created_at": "2026-03-02T09:20:00Z",
    },
    {
        "tenant_id": "umbrella",
        "request_id": "req-umbrella-001",
        "dossier_id": "dos-umbrella-org-001",
        "query_text": "watchlist screening",
        "status": "failed",
        "created_at": "2026-03-02T09:22:00Z",
    },
)

DEMO_MANAGED_ENTITLEMENTS: tuple[dict[str, object], ...] = (
    {
        "tenant_id": "acme",
        "subject": "demo-user",
        "enabled_modules": ["dashboard", "dossiers"],
        "updated_by_subject": "demo-admin",
        "updated_at": "2026-03-02T09:25:00Z",
    },
    {
        "tenant_id": "acme",
        "subject": "demo-admin",
        "enabled_modules": ["dashboard", "dossiers", "watchlist"],
        "updated_by_subject": "system-seed",
        "updated_at": "2026-03-02T09:26:00Z",
    },
)

DEMO_AUDIT_EVENTS: tuple[dict[str, str], ...] = (
    {
        "action": "entitlements.updated",
        "actor_subject": "demo-admin",
        "target_subject": "demo-user",
        "tenant_id": "acme",
        "outcome": "success",
        "reason": "seed_baseline",
        "occurred_at": "2026-03-02T09:25:00Z",
    },
    {
        "action": "export.requested",
        "actor_subject": "demo-user",
        "tenant_id": "acme",
        "outcome": "success",
        "reason": "seed_baseline",
        "occurred_at": "2026-03-02T09:27:00Z",
    },
)

DEMO_WALKTHROUGHS: tuple[dict[str, object], ...] = (
    {
        "scenario_id": "user-walkthrough",
        "actor_subject": "demo-user",
        "expected_tenant_id": "acme",
        "steps": [
            {
                "step_id": "user-login",
                "surface": "frontend",
                "path": "/dashboard",
                "expected": (
                    "Successful login resolves tenant 'acme' and returns "
                    "module entitlements ['dashboard', 'dossiers']."
                ),
            },
            {
                "step_id": "user-dossiers",
                "surface": "frontend",
                "path": "/dossiers",
                "expected": (
                    "Lists only acme dossiers dos-acme-org-001 and "
                    "dos-acme-person-001; umbrella data remains hidden."
                ),
            },
            {
                "step_id": "user-searches",
                "surface": "frontend",
                "path": "/searches",
                "expected": (
                    "Shows req-acme-001 as queued and req-acme-002 as completed."
                ),
            },
            {
                "step_id": "user-export",
                "surface": "frontend/api",
                "path": "/exports",
                "expected": (
                    "Export request is accepted for tenant acme because the "
                    "seeded account retains the export:data scope from Keycloak."
                ),
            },
        ],
    },
    {
        "scenario_id": "admin-walkthrough",
        "actor_subject": "demo-admin",
        "expected_tenant_id": "acme",
        "steps": [
            {
                "step_id": "admin-login",
                "surface": "frontend",
                "path": "/admin",
                "expected": "Successful login reaches the admin workspace for tenant acme.",
            },
            {
                "step_id": "admin-load-entitlements",
                "surface": "frontend/api",
                "path": "/api/v1/tenants/acme/entitlements/demo-user",
                "expected": (
                    "Loading demo-user returns the seeded entitlement baseline "
                    "['dashboard', 'dossiers']."
                ),
            },
            {
                "step_id": "admin-update-entitlements",
                "surface": "frontend/api",
                "path": "/api/v1/tenants/acme/entitlements/demo-user",
                "expected": (
                    "Saving watchlist for demo-user creates a new "
                    "entitlements.updated audit event."
                ),
            },
            {
                "step_id": "admin-review-audit",
                "surface": "frontend/api",
                "path": "/api/v1/tenants/acme/audit/events",
                "expected": (
                    "Audit review starts with the seeded baseline events "
                    "entitlements-updated-1 and export-audit-2."
                ),
            },
        ],
    },
)


def build_demo_seed_manifest() -> dict[str, object]:
    return {
        "seed_version": DEMO_SEED_VERSION,
        "tenants": [dict(item) for item in DEMO_TENANTS],
        "actors": [dict(item) for item in DEMO_ACTORS],
        "dossiers": [dict(item) for item in DEMO_DOSSIERS],
        "search_requests": [dict(item) for item in DEMO_SEARCH_REQUESTS],
        "managed_entitlements": [_manifest_entitlement(item) for item in DEMO_MANAGED_ENTITLEMENTS],
        "audit_events": [_manifest_audit_event(index, item) for index, item in enumerate(DEMO_AUDIT_EVENTS, start=1)],
        "walkthroughs": [dict(item) for item in DEMO_WALKTHROUGHS],
    }


def reset_demo_state() -> None:
    run_with_storage_connection(reset_demo_state_for_connection)
    clear_runtime_storage_cache()
    reset_ingestion_runtime_state()


def reseed_demo_state() -> dict[str, object]:
    def _operation(connection: Connection) -> dict[str, object]:
        reset_demo_state_for_connection(connection)
        seed_demo_state_for_connection(connection)
        return collect_seeded_demo_state(connection)

    result = run_with_storage_connection(_operation)
    clear_runtime_storage_cache()
    reset_ingestion_runtime_state()
    return result


def reset_demo_state_for_connection(connection: Connection) -> None:
    connection.execute("DELETE FROM search_requests")
    connection.execute("DELETE FROM dossiers")
    connection.execute("DELETE FROM managed_entitlements")
    connection.execute("DELETE FROM audit_events")
    connection.execute("DELETE FROM sqlite_sequence WHERE name = 'audit_events'")
    connection.commit()


def seed_demo_state_for_connection(connection: Connection) -> None:
    _insert_dossiers(connection)
    _insert_search_requests(connection)
    _upsert_managed_entitlements(connection)
    _insert_audit_events(connection)
    connection.commit()


def collect_seeded_demo_state(connection: Connection) -> dict[str, object]:
    entitlement_repository = SqliteManagedEntitlementRepository(connection)
    audit_repository = SqliteAuditEventRepository(connection)

    managed_entitlements = [
        {
            "tenant_id": item["tenant_id"],
            "subject": item["subject"],
            "enabled_modules": entitlement_repository.get_modules(
                tenant_id=str(item["tenant_id"]),
                subject=str(item["subject"]),
            )
            or [],
        }
        for item in DEMO_MANAGED_ENTITLEMENTS
    ]

    audit_events = connection.execute(
        """
        SELECT
            audit_id,
            action,
            actor_subject,
            target_subject,
            tenant_id,
            outcome,
            reason,
            occurred_at
        FROM audit_events
        ORDER BY audit_id ASC
        """
    ).fetchall()

    return {
        "seed_version": DEMO_SEED_VERSION,
        "tenants": [dict(item) for item in DEMO_TENANTS],
        "actors": [dict(item) for item in DEMO_ACTORS],
        "dossiers": [
            dict(row)
            for row in connection.execute(
                """
                SELECT tenant_id, dossier_id, subject_name, subject_type, created_at
                FROM dossiers
                ORDER BY tenant_id ASC, dossier_id ASC
                """
            ).fetchall()
        ],
        "search_requests": [
            dict(row)
            for row in connection.execute(
                """
                SELECT tenant_id, request_id, dossier_id, query_text, status, created_at
                FROM search_requests
                ORDER BY tenant_id ASC, request_id ASC
                """
            ).fetchall()
        ],
        "managed_entitlements": managed_entitlements,
        "audit_events": [
            _manifest_audit_event(
                audit_id=int(row["audit_id"]),
                event={
                    "action": str(row["action"]),
                    "actor_subject": str(row["actor_subject"]),
                    "target_subject": (
                        str(row["target_subject"])
                        if isinstance(row["target_subject"], str) and row["target_subject"]
                        else None
                    ),
                    "tenant_id": str(row["tenant_id"]),
                    "outcome": str(row["outcome"]),
                    "reason": (
                        str(row["reason"])
                        if isinstance(row["reason"], str) and row["reason"]
                        else None
                    ),
                    "occurred_at": str(row["occurred_at"]),
                },
            )
            for row in audit_events
        ],
        "walkthroughs": [dict(item) for item in DEMO_WALKTHROUGHS],
        "tenant_audit_review": {
            "acme": audit_repository.list_events_for_tenant(tenant_id="acme"),
            "umbrella": audit_repository.list_events_for_tenant(tenant_id="umbrella"),
        },
    }


def _insert_dossiers(connection: Connection) -> None:
    for dossier in DEMO_DOSSIERS:
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
            (
                dossier["tenant_id"],
                dossier["dossier_id"],
                dossier["subject_name"],
                dossier["subject_type"],
                dossier["created_at"],
            ),
        )


def _insert_search_requests(connection: Connection) -> None:
    for request in DEMO_SEARCH_REQUESTS:
        connection.execute(
            """
            INSERT INTO search_requests (
                tenant_id,
                request_id,
                dossier_id,
                query_text,
                status,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                request["tenant_id"],
                request["request_id"],
                request["dossier_id"],
                request["query_text"],
                request["status"],
                request["created_at"],
            ),
        )


def _upsert_managed_entitlements(connection: Connection) -> None:
    repository = SqliteManagedEntitlementRepository(connection)
    for entitlement in DEMO_MANAGED_ENTITLEMENTS:
        repository.upsert_modules(
            tenant_id=str(entitlement["tenant_id"]),
            subject=str(entitlement["subject"]),
            enabled_modules=normalize_modules(
                _require_string_sequence(entitlement["enabled_modules"])
            ),
            actor_subject=str(entitlement["updated_by_subject"]),
            occurred_at=str(entitlement["updated_at"]),
            commit=False,
        )


def _insert_audit_events(connection: Connection) -> None:
    repository = SqliteAuditEventRepository(connection)
    for event in DEMO_AUDIT_EVENTS:
        repository.create_event(
            action=event["action"],
            actor_subject=event["actor_subject"],
            tenant_id=event["tenant_id"],
            outcome=event["outcome"],
            occurred_at=event["occurred_at"],
            target_subject=event.get("target_subject"),
            reason=event.get("reason"),
            commit=False,
        )


def _manifest_entitlement(entitlement: dict[str, object]) -> dict[str, object]:
    return {
        "tenant_id": entitlement["tenant_id"],
        "subject": entitlement["subject"],
        "enabled_modules": list(_require_string_sequence(entitlement["enabled_modules"])),
        "updated_by_subject": entitlement["updated_by_subject"],
        "updated_at": entitlement["updated_at"],
    }


def _manifest_audit_event(audit_id: int, event: dict[str, str | None]) -> dict[str, str]:
    action = event["action"]
    if action == "entitlements.updated":
        event_id = f"entitlements-updated-{audit_id}"
    elif action == "export.requested":
        event_id = f"export-audit-{audit_id}"
    else:
        raise ValueError(f"Unsupported audit action '{action}'.")

    manifest = {
        "event_id": event_id,
        "action": action,
        "actor_subject": event["actor_subject"],
        "tenant_id": event["tenant_id"],
        "outcome": event["outcome"],
        "occurred_at": event["occurred_at"],
    }
    target_subject = event.get("target_subject")
    if target_subject:
        manifest["target_subject"] = target_subject
    reason = event.get("reason")
    if reason:
        manifest["reason"] = reason
    return manifest


def _require_string_sequence(value: object) -> Sequence[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError("Expected a sequence of strings.")

    parsed: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise ValueError("Expected a sequence of non-empty strings.")
        parsed.append(item)
    return parsed


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reset and reseed deterministic Decider demo data."
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("reset", "reseed", "summary"),
        default="reseed",
        help="reset current state, reseed deterministic data, or print the canonical manifest",
    )
    args = parser.parse_args(argv)

    if args.command == "reset":
        reset_demo_state()
        print(json.dumps({"status": "reset", "seed_version": DEMO_SEED_VERSION}, indent=2))
        return 0

    if args.command == "summary":
        print(json.dumps(build_demo_seed_manifest(), indent=2))
        return 0

    print(json.dumps(reseed_demo_state(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
