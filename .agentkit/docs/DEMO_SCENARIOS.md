# DEMO_SCENARIOS

This document is the canonical walkthrough checklist for roadmap ticket T19.
It assumes the runtime stack is running and the deterministic demo seed has been applied.

## 1) Reset and reseed
Use the runtime API container so the seed operates on the same SQLite database as the local app:

```bash
docker compose -f docker-compose.dev.yml --profile runtime --env-file .env.runtime exec api \
  uv run --frozen python -m decider_api.demo_seed reseed
```

To clear seeded application data without recreating it:

```bash
docker compose -f docker-compose.dev.yml --profile runtime --env-file .env.runtime exec api \
  uv run --frozen python -m decider_api.demo_seed reset
```

To print the canonical manifest without touching the database:

```bash
docker compose -f docker-compose.dev.yml --profile runtime --env-file .env.runtime exec api \
  uv run --frozen python -m decider_api.demo_seed summary
```

## 2) Seed baseline
The reseed command creates this deterministic baseline:

- Tenants:
  - `acme` for the main walkthrough
  - `umbrella` as isolation-only background data
- Keycloak actors:
  - `demo-user` in tenant `acme`
  - `demo-admin` in tenant `acme`
- Dossiers:
  - `dos-acme-org-001` -> `Acme Logistics LLP`
  - `dos-acme-person-001` -> `Aida Sarsen`
  - `dos-umbrella-org-001` -> `Umbrella Industrial JSC`
- Search requests:
  - `req-acme-001` -> queued
  - `req-acme-002` -> completed
  - `req-umbrella-001` -> failed
- Managed entitlements:
  - `demo-user` -> `dashboard`, `dossiers`
  - `demo-admin` -> `dashboard`, `dossiers`, `watchlist`
- Audit baseline:
  - `entitlements-updated-1`
  - `export-audit-2`

## 3) User walkthrough
Login as `demo-user` and confirm:

1. `/dashboard`
   Expected: tenant resolves to `acme`; auth-context returns `dashboard` and `dossiers`.
2. `/dossiers`
   Expected: only `dos-acme-org-001` and `dos-acme-person-001` are visible.
3. `/searches`
   Expected: `req-acme-001` is queued and `req-acme-002` is completed.
4. `/exports`
   Expected: export request is accepted for `acme`.
5. Isolation spot-check
   Expected: no `umbrella` dossier or search request appears anywhere in the UI/API responses for `demo-user`.

## 4) Admin walkthrough
Login as `demo-admin` and confirm:

1. `/admin`
   Expected: admin workspace opens for tenant `acme`.
2. Load subject `demo-user`
   Expected: current modules are `dashboard` and `dossiers`.
3. Add `watchlist` and save
   Expected: API accepts the update and emits a new `entitlements.updated` audit event.
4. Review audit events
   Expected: the list already contains `entitlements-updated-1` and `export-audit-2`, plus the new admin update event after save.
5. Refresh `demo-user` auth context
   Expected: on the next auth-context refresh, `demo-user` now has `watchlist` in addition to the seeded baseline modules.

## 5) Notes
- All seeded names, IDs, and timestamps are synthetic.
- The seed intentionally keeps a second tenant in storage to make tenant-isolation regressions obvious during manual testing.
- T20 should automate these same steps in end-to-end checks rather than redefining a new walkthrough baseline.
