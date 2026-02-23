# Architecture (local) — Decider

## Macro-architecture
- Microservices architecture.
- Services must not duplicate code: shared logic must be extracted into shared packages/libraries.
- Avoid copy/paste across services. Prefer a single shared implementation with explicit ownership.

## Service boundaries (guidelines)
Each service should have:
- clear API surface (OpenAPI)
- explicit dependencies
- isolated data access responsibilities
- strict tenant isolation enforcement at the boundary (auth middleware / dependencies)

## Clean-ish layering (backend)
Preferred structure inside each service:
- API layer: FastAPI routers, request/response schemas
- Application layer: use-cases/services (business orchestration)
- Domain layer: core rules/entities/policies (no infra dependencies)
- Infrastructure: DB, message brokers, external sources, clients

Dependency direction: infra -> app -> domain (never the other way around).

## Data model
- Primary relational DB: PostgreSQL (migrated from MSSQL in rewrite)
- Secondary store: MongoDB
- Migrations:
  - Alembic (linear history preferred, single head)
  - migration plan + rollback required for all schema changes

## Async / integrations
- Celery used for background processing and long-running tasks.
- External HTTP clients must have:
  - timeouts
  - retries with backoff (tenacity)
  - circuit-breaking strategy if needed (project-defined)
- SSRF-safe URL handling if any “fetch remote URL” exists.

## Frontend structure (Angular)
- Feature-oriented structure preferred.
- UI components thin; business logic in services/facades.
- Permissions/entitlements affect:
  - route guards
  - module visibility
  - action availability
…but backend remains authoritative.

## Observability
- Every request should be traceable:
  - correlation_id (request id) propagated
  - OpenTelemetry traces where possible
  - Sentry for exceptions
- Prometheus metrics exposed at `/metrics` (service-specific)

## Forbidden (without explicit approval / separate ticket)
- “big refactor” that changes multiple services/modules at once
- cross-service coupling via shared DB tables without explicit architecture decision
- modifying CI/CD, Docker, k8s manifests without dedicated approval/ticket