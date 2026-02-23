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

## 5) Backlog / parking lot
- Data retention and archival strategy for sensitive source material.
- Fine-grained audit review UI for compliance teams.
- Performance/load model for large export datasets.
- Tokenized design system and Figma-to-code sync workflow.
- Tenant self-service onboarding automation.
