# ROADMAP

This file is the single source of truth for the Decider implementation roadmap in this repository.
It converts the current AgentKit skeleton into an executable plan with auditable, one-ticket-per-chat work units.

## 0) Project overview (1-2 paragraphs)
Decider is a due-diligence and risk/reliability platform for corporate security, legal, and HR teams. The system assembles dossiers on organizations and persons from approved sources, then provides controlled search, review, and export workflows.

Success means: tenant-safe access control is enforced server-side, high-risk actions are audited, critical user flows are verified in local/CI contracts, and the repository has repeatable delivery mechanics (roadmap, ticket logs, DOC gate, verification gates).

## 1) Constraints & assumptions
- Hard constraints:
  - Tenant isolation is a non-negotiable security invariant.
  - Authn/Authz uses Keycloak OIDC; backend authorization is authoritative.
  - High-risk changes (auth/permissions, migrations, public API contracts, headers, payments) require PR plus required templates.
  - PROJECT_MAP updates are mandatory for every ticket.
  - No placeholder/fake verification; verification must run real toolchains.
- Assumptions:
  - This repository is currently in bootstrap mode (AgentKit core + minimal service skeleton).
  - Frontend and backend implementation will be added incrementally from this roadmap.
  - CI pipeline exists or will be introduced before high-risk merges are allowed.
  - Kazakhstan personal-data handling constraints apply to domain design and logging.

## 2) Architecture sketch (high level)
- Main components/services:
  - API service (FastAPI) for auth-aware domain operations and exports.
  - Frontend app (Angular) for tenant users/admins with entitlement-aware UX.
  - Background workers (Celery) for long-running collection/enrichment jobs.
- Data storage:
  - Primary PostgreSQL for transactional entities and audit metadata.
  - Secondary MongoDB for flexible source payload storage (if retained in architecture).
- Integrations:
  - Keycloak (OIDC + role/scope claims).
  - External source adapters for data collection.
  - Observability stack (Prometheus/OpenTelemetry/Sentry).
- Auth approach:
  - OIDC Authorization Code + PKCE in UI, token validation + scope/tenant checks in API.
- Deployment environment (if known):
  - Containerized services with CI-driven verification gates.

## 3) Milestones
- M1: Engineering foundation and repository adaptation
- M2: Secure multi-tenant core flows
- M3: Dossier and export workflows
- M4: Reliability, CI hardening, and release readiness
- M5: Local end-to-end product walkthrough readiness (user/admin)

## 4) Ticket plan (ordered)
Each ticket is intended to be done in one agent chat (plan -> implement -> verify -> done).

### T1 - Implement real verification contract
**Scope**
- Replace placeholder `Makefile` verify targets with real local checks for current repo contents.
- Ensure `.agentkit/scripts/verify.sh` and `.agentkit/scripts/verify.ps1` can run end-to-end without semantic bypass.

**Acceptance criteria**
- `./.agentkit/scripts/verify.sh local` runs real commands and returns pass/fail accurately.
- `make verify-local`, `make verify-smoke`, and `make verify-ci` are implemented with non-placeholder behavior.
- PROJECT_MAP updated with verification map details.

**Risk**
- medium

**Notes**
- Keep implementation minimal but real; no fake-pass scripts.

### T2 - Establish backend service scaffold
**Scope**
- Add tracked Python backend skeleton (entrypoint, settings, health endpoint, package structure).
- Align with clean layering guidance for API/app/domain/infra boundaries.

**Acceptance criteria**
- Service starts locally with a health endpoint.
- Basic unit tests run in local verification.
- Repository map documents backend file ownership.

**Risk**
- medium

**Notes**
- No auth changes yet in this ticket.

### T3 - Establish frontend shell scaffold
**Scope**
- Add tracked Angular app shell with route skeleton and environment configuration.
- Add minimal lint/test hooks into verify targets.

**Acceptance criteria**
- Frontend builds and runs.
- Unit test/lint commands are wired into `verify-local`.
- PROJECT_MAP includes frontend structure and verification hooks.

**Risk**
- medium

**Notes**
- Keep UI surface minimal; no feature-complete flows yet.

### T4 - Define initial public API contract
**Scope**
- Add first OpenAPI contract for health, auth context, and tenant-aware base resources.
- Define versioning baseline (`/api/v1`).

**Acceptance criteria**
- OpenAPI contract is checked into repo and referenced by API tests.
- Breaking-change policy documented in PROJECT_MAP.
- Contract lint/validation included in verification path.

**Risk**
- high

**Notes**
- PR required (public API contract area).

### T5 - Implement Keycloak token validation and claims mapping
**Scope**
- Add Keycloak integration for token validation and normalized auth context extraction.
- Add tests for issuer/audience/expiry handling and claim mapping.

**Acceptance criteria**
- Requests with invalid or expired tokens are rejected.
- Auth context includes tenant and scopes in a consistent structure.
- Security note added to ticket log and PROJECT_MAP.

**Risk**
- high

**Notes**
- PR + threat model required (auth area).

### T6 - Enforce tenant isolation guardrails
**Scope**
- Implement server-side tenant resolution and cross-tenant blocking in API boundary.
- Add negative tests proving forbidden cross-tenant access.

**Acceptance criteria**
- Cross-tenant access attempts return 403.
- Positive same-tenant requests continue to function.
- Coverage for tenant guard modules reaches policy target.

**Risk**
- high

**Notes**
- PR + threat model required (auth/tenant area).

### T7 - Implement permissions and module entitlements
**Scope**
- Add RBAC/module-permission checks and admin APIs to manage entitlements per tenant/user.
- Align frontend visibility logic with backend permission responses.

**Acceptance criteria**
- Permission checks enforced server-side.
- Admin changes to entitlements affect module access behavior.
- Audit metadata exists for permission change actions.

**Risk**
- high

**Notes**
- PR + threat model required (permissions/public behavior).

### T8 - Build dossier core domain and storage
**Scope**
- Implement core domain entities and repositories for dossiers/objects and search requests.
- Add migration set for initial schema.

**Acceptance criteria**
- Core entities can be created/read with tenant scoping.
- Alembic migration plan + rollback documented and tested.
- Integration tests cover repository behavior.

**Risk**
- high

**Notes**
- PR + migration plan required (migrations area).

### T9 - Implement export workflow with scope gating and audit
**Scope**
- Add export endpoint/process guarded by `export:data` scope and tenant checks.
- Record audit events for export attempts/results without leaking payload data.

**Acceptance criteria**
- No scope -> 403; wrong tenant -> 403; valid scope + tenant -> success.
- Audit record is created for each export action.
- API e2e smoke includes at least one positive and one negative export case.

**Risk**
- high

**Notes**
- PR + threat model required (permissions/public API/security-sensitive action).

### T10 - Add background ingestion pipeline foundation
**Scope**
- Add Celery worker skeleton and first source-adapter abstraction with retries/timeouts.
- Add SSRF-safe URL handling policy for any remote fetch flow.

**Acceptance criteria**
- Background job can be queued and processed in local dev.
- External client configuration enforces timeout/retry policy.
- Security checks and tests exist for URL validation behavior.

**Risk**
- medium

**Notes**
- Escalate to high if new external fetch endpoints are introduced.

### T11 - Add observability and operational guardrails
**Scope**
- Add structured logging, correlation ID propagation, metrics endpoint, and exception reporting hooks.
- Define runbook for common local/CI failures.

**Acceptance criteria**
- Correlation ID appears in request lifecycle logs.
- `/metrics` exposes baseline service metrics.
- PROJECT_MAP runbook section is actionable for local troubleshooting.

**Risk**
- medium

**Notes**
- Keep logs free of tokens/PII.

### T12 - Harden CI verification and release gate
**Scope**
- Implement CI job coverage for `verify-ci`, API e2e, UI e2e, and required security scans.
- Define release-ready checklist and done criteria for production branch.

**Acceptance criteria**
- CI runs `make verify-ci` as contract entrypoint.
- High-risk tickets cannot be closed without green CI.
- Documentation clearly states CI gate expectations and artifact links.

**Risk**
- high

**Notes**
- PR required if CI/CD configuration is changed.

### T13 - Stand up local runtime stack for walkthrough
**Scope**
- Add a local compose profile for API + frontend + Postgres + Redis + Keycloak.
- Add bootstrap configuration for local realm, clients, and demo tenants.
- Provide one-command startup/shutdown runbook entries.

**Acceptance criteria**
- `docker compose ... up` brings all required services to healthy state.
- API can validate real Keycloak-issued tokens in local stack.
- Startup prerequisites and troubleshooting are documented.

**Risk**
- high

**Notes**
- PR required (Docker/runtime infrastructure area).

### T14 - Integrate frontend OIDC login/logout with role-aware guards
**Scope**
- Implement OIDC Authorization Code + PKCE in frontend.
- Add login/logout/session handling and route guarding by auth state.
- Fetch backend auth-context and drive module visibility from real claims.

**Acceptance criteria**
- User and admin can log in locally via Keycloak and reach authorized routes.
- Unauthenticated access is redirected to login.
- Session expiration and re-login behavior are covered in tests.

**Risk**
- high

**Notes**
- PR + threat model required (auth area).

### T15 - Persist entitlements and audit trail in database
**Scope**
- Replace in-memory entitlement/audit state with persistent storage.
- Add migration set and rollback for entitlement and audit tables.
- Keep response contract compatible with existing API shape.

**Acceptance criteria**
- Entitlement updates survive API restarts.
- Audit records are queryable for admin review.
- Migration up/down paths are tested and documented.

**Risk**
- high

**Notes**
- PR + migration plan + threat model required (migrations + permissions area).

### T16 - Implement user dossier/search workflows in public API
**Scope**
- Add tenant-scoped endpoints for dossier list/create/detail.
- Add tenant-scoped endpoints for search-request create/list/detail/status.
- Wire ingestion trigger path into user search workflow.

**Acceptance criteria**
- Authenticated tenant user can complete dossier and search lifecycle via API.
- Cross-tenant and missing-entitlement requests are blocked with 403.
- OpenAPI v1 and API e2e coverage are updated.

**Risk**
- high

**Notes**
- PR required (public API contract area).

### T17 - Build frontend user flows for dossier/search/export
**Scope**
- Replace shell pages with working views: dashboard, dossiers, search, export.
- Add data fetching, loading/error states, and empty-state UX.
- Keep frontend module visibility aligned with backend entitlements.

**Acceptance criteria**
- User can execute happy-path flows from UI without manual API calls.
- Forbidden operations are shown with explicit UX feedback.
- UI unit/integration tests cover critical user paths.

**Risk**
- medium

**Notes**
- Keep UI surface scoped to MVP workflows.

### T18 - Build frontend admin flows for entitlement management
**Scope**
- Add admin UI to view/update subject entitlements within tenant.
- Add admin UI to inspect export/permission audit events.
- Reflect permission changes in UI state on next auth-context refresh.

**Acceptance criteria**
- Admin can grant/revoke modules for a target subject.
- Updated rights are enforced server-side and reflected in user UX.
- Admin operations create auditable records visible in UI/API.

**Risk**
- high

**Notes**
- PR + threat model required (permissions/auth area).

### T19 - Add deterministic demo seed and scenario harness
**Scope**
- Provide deterministic seed data for tenants, users, dossiers, and requests.
- Add scripts/runbook to reset environment and reseed scenarios.
- Define canonical walkthrough scenarios for user and admin roles.

**Acceptance criteria**
- Fresh local setup can be prepared for demo/testing in <= 20 minutes.
- Seed/reset process is repeatable and documented.
- Scenario checklist maps each walkthrough step to expected system behavior.

**Risk**
- medium

**Notes**
- Seed data must be synthetic and policy-safe (no real PII/secrets).

### T20 - Enforce end-to-end acceptance gate for user/admin walkthrough
**Scope**
- Add Playwright e2e suites for full user and admin journeys.
- Add API e2e scenarios aligned with UI paths and role transitions.
- Gate release readiness on walkthrough suite pass.

**Acceptance criteria**
- CI runs and passes user/admin journey suites as required checks.
- Manual runbook steps match automated assertions.
- Release checklist references walkthrough evidence artifacts.

**Risk**
- high

**Notes**
- PR required if CI gate configuration changes.

## 5) Backlog / parking lot
- Data retention and archival strategy for sensitive source material.
- Fine-grained audit review UI for compliance teams.
- Performance/load model for large export datasets.
- Tokenized design system and Figma-to-code sync workflow.
- Tenant self-service onboarding automation.
