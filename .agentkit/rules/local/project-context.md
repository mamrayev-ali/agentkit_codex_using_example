# Project context — Decider (local)

## What this system is
Decider is a due-diligence / risk & reliability platform.
It automates search, storage, and accounting of data about organizations and persons (“dossiers/objects”) from multiple sources
(including public internet and government/open sources) to support corporate security, HR, and legal teams.

Data about individuals is formed from open and government sources in compliance with Kazakhstan personal-data requirements.
Treat the entire domain as sensitive: avoid leaking PII/credentials via logs, errors, screenshots, or artifacts.

## Who uses it
Two classes of users:
- Admin (our company): creator/operators/support; can manage tenants and permissions.
- Non-admin (client users): employees of client organizations.

## Tenant model (hard rule)
- Each client is a tenant organization.
- Each user belongs to exactly one tenant organization (tenant-scoped).
- Permissions are assigned per user or per tenant, including module-level entitlements.
- Tenant isolation is a primary security invariant:
  - any cross-tenant access is a security incident.

## Auth model (hard rule)
- Keycloak OIDC (Authorization Code + PKCE) + possible corporate SSO.
- Backend must enforce:
  - token validation
  - tenant isolation checks
  - scope/permission checks
- Frontend may hide UI actions, but backend is the source of truth.

## Stack snapshot (for orientation)
Backend:
- Python 3.13, FastAPI + Uvicorn, Pydantic v2
- SQLAlchemy + Alembic, PostgreSQL (asyncpg/psycopg), plus MongoDB
- Celery + Redis/RabbitMQ
- httpx (async/HTTP2) + tenacity
- Observability: Prometheus /metrics, OpenTelemetry, Sentry
- Keycloak integration (python-keycloak / fastapi-keycloak)

Frontend:
- Angular 21, TS >=5.9 <6
- Signals
- ESLint + Prettier
- Vitest for unit tests
- Playwright for UI e2e
- Custom UI kit defined in Figma (tokens planned to move to code)

## High-risk areas (require PR + templates)
High-risk if a ticket touches any of:
- auth/permissions/scopes, tenant isolation logic
- DB migrations (Alembic) or data model changes
- public API contracts (OpenAPI), versioning / breaking changes
- security headers / CORS / cookies
- payments/finance integrations

High-risk requires:
- PR/MR is mandatory
- threat model is mandatory
- migration plan + rollback is mandatory (if schema changes)
- cannot merge without green CI

## Documentation discipline (strict)
- `.agentkit/docs/PROJECT_MAP.md` is the primary “repo memory”.
- Update PROJECT_MAP on EVERY ticket (no bypass).
- When a ticket changes any of:
  - auth/permissions/scopes
  - API contracts/versioning
  - tenant resolution/claims mapping
  - migrations/data model
  - verification commands
  - service boundaries / module ownership
…then PROJECT_MAP must be updated with:
  - what changed
  - why
  - where to look now

## What the agent must log
For every ticket:
- [PLAN] ticket plan + DoD
- [ACT] key actions/commands
- [DIFF] summary of changes + show diff
- [TEST] what was run locally; what must run in CI
- [SECURITY] if any high-risk area touched (plus links to templates)
- [DOC] PROJECT_MAP updated (always)
- [MCP:*] MCP usage when relevant (Figma/Notion/Docs/Playwright)