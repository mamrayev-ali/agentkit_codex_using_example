# PROJECT_MAP

This file is the persistent, human-readable map of the repository.
It explains what exists now, what contracts are enforced, and where new work should be anchored.

## 0) TL;DR
- What this system does:
  - Provides an AgentKit control framework for building the Decider platform with strict auditability, DOC gates, and verification contracts.
- Key user flows:
  - Discovery/intake -> roadmap creation.
  - Ticket execution -> small diffs + ticket log + PROJECT_MAP update + verification.
- Tech stack:
  - Process/tooling: Markdown docs, Bash/PowerShell scripts, Makefile contract.
  - Target product stack (planned): Python/FastAPI backend, Angular frontend, Keycloak, PostgreSQL, MongoDB, Celery.
- Where to start reading the code:
  - `AGENTS.md`
  - `.agentkit/docs/ROADMAP.md`
  - `.agentkit/scripts/verify.sh`
  - `.agentkit/rules/local/project-context.md`

## 1) Repo structure (high level)
- `.agentkit/` - Process framework: docs, rules, templates, and verification scripts.
  - Boundaries:
    - Defines how work is done, not product runtime logic.
    - Enforces DOC gate and verification entrypoints.
- `.agents/skills/` - Codex skills for repeatable workflows.
  - Contains `project-intake` and `ticket-planning` procedural instructions.
- `.codex/` - Codex runtime configuration and MCP server setup.
- `services/` - Product implementation area.
  - Current tracked state: no committed service source yet.
  - Existing local skeleton folder may exist but is not yet part of tracked delivery.
- `logs/agent/` - Local human-readable ticket logs (gitignored).

## 2) Key contracts & boundaries
- Architectural principles:
  - Workflow-first repository with strict documentation and verification gates.
  - Future service code should follow clean layering and explicit boundaries from local rules.
- Public interfaces:
  - No committed public API contract yet; roadmap includes introducing OpenAPI baseline.
- Error handling strategy:
  - Verification scripts fail fast and stop on unmet prerequisites.
  - No placeholder pass paths are allowed.
- Logging/observability conventions:
  - Agent actions must be recorded in `logs/agent/<ticket>.md` with structured tags.
  - Product observability conventions are documented in local rules and planned roadmap tickets.

## 3) Domain map (important concepts)
- Core domain entities (planned):
  - Tenant organization
  - User and permissions/scopes
  - Dossier/object
  - Search request
  - Export action and audit record
- Main business rules:
  - Tenant isolation is mandatory.
  - Backend authorization is authoritative.
  - Sensitive data handling must avoid PII leakage in logs/artifacts.
- Invariants:
  - Any cross-tenant access is a security incident.
  - High-risk areas require PR and extra templates/checks.
  - PROJECT_MAP update is mandatory for every ticket with repo changes.

## 4) Public API surface (if applicable)
- Where the API contract lives:
  - Not established yet (planned in roadmap ticket T4).
- Versioning strategy:
  - Planned baseline: `/api/v1`.
- Critical endpoints / operations (planned):
  - auth context endpoint
  - tenant-scoped dossier operations
  - export operation with scope + tenant guardrails

## 5) Data & migrations (if applicable)
- Database(s):
  - Planned: PostgreSQL primary, MongoDB secondary.
- Migration approach:
  - Planned Alembic linear migration history.
- Rollback approach:
  - Mandatory migration plan + rollback for any schema change.
- Critical tables/collections (planned high level):
  - tenants/users/permissions
  - dossier/search requests
  - export audit metadata

## 6) Frontend / UI surface (if applicable)
- Routing approach:
  - Planned Angular feature routes with permission-aware guards.
- State management approach:
  - Planned use of Angular Signals/services.
- Where styles/tokens live:
  - Planned integration with Figma-backed UI tokens.
- How UI is verified vs design:
  - Planned Playwright e2e coverage for critical entitlement and export flows.

## 7) Testing & verification map
### Local DoD (must pass before asking to push)
- `make verify-local` does:
  - Contract target exists but is currently placeholder-only in `Makefile`.
  - Roadmap T1 will replace placeholders with real checks.
- Coverage target:
  - Local rules set >=80% coverage for critical modules once implemented.
- API e2e smoke definition:
  - Planned minimum: one happy path + one negative 403 across critical flows.

### CI DoD (must pass before ticket is Done)
- `make verify-ci` does:
  - Contract target exists but is currently placeholder-only in `Makefile`.
  - Roadmap T12 covers full CI gate implementation.
- Security scanning policy (high level):
  - Local rules require SAST/DAST/container scan coverage for CI in high-risk pathways.

## 8) High-risk areas
- Auth/permissions/tenant isolation:
  - Why risky: direct security boundary and cross-tenant exposure risk.
  - What to check: token validation, claim mapping, explicit scope checks, 403 negative tests.
  - Where in the code: future API auth middleware/dependencies/services.
- Database migrations:
  - Why risky: data integrity and rollback risk.
  - What to check: migration plan, rollback steps, single-head Alembic state.
  - Where in the code: future backend migration directories.
- Public API contracts:
  - Why risky: client compatibility and versioning stability.
  - What to check: contract versioning, backward compatibility, change notes.
  - Where in the code: future OpenAPI specs and API routers.
- Security headers/CORS:
  - Why risky: browser/session attack surface.
  - What to check: strict allow-lists and production-safe defaults.
  - Where in the code: future API middleware/config.
- Payments/finance integrations:
  - Why risky: legal/financial impact.
  - What to check: explicit authorization, idempotency, audit trails.
  - Where in the code: future finance modules (not present yet).

## 9) File registry (only important files)
- `AGENTS.md` - Top-level operating contract for Codex and safety gates.
  - public surface / key exports:
    - Non-negotiable workflow and approval constraints.
  - invariants / assumptions:
    - Diff visibility, ticket logs, PROJECT_MAP updates, verification order.
  - dependencies:
    - `.agentkit/` framework files.
  - tests:
    - Enforced indirectly by verify scripts and workflow compliance.
- `.agentkit/docs/ROADMAP.md` - Ordered plan of milestones and ticket scopes.
  - public surface / key exports:
    - T1..Tn work breakdown.
  - invariants / assumptions:
    - One ticket per chat scope; risk tags are explicit.
  - dependencies:
    - Project context from local rules.
  - tests:
    - Human review + doc gate coverage.
- `.agentkit/docs/PROJECT_MAP.md` - Persistent repository memory.
  - public surface / key exports:
    - Structure, contracts, risks, and runbook.
  - invariants / assumptions:
    - Must be updated on every ticket with repo changes.
  - dependencies:
    - Verify script DOC gate and ticket logs.
  - tests:
    - Enforced by `.agentkit/scripts/verify.sh`.
- `.agentkit/scripts/verify.sh` - Bash verification entrypoint + DOC gate.
  - public surface / key exports:
    - `local`, `smoke`, and `ci` modes.
  - invariants / assumptions:
    - Any non-PROJECT_MAP file change requires PROJECT_MAP update.
  - dependencies:
    - `git`, `make`, `Makefile` contract targets.
  - tests:
    - Executed directly in ticket verification.
- `.agentkit/scripts/verify.ps1` - Windows-native verification runner.
  - public surface / key exports:
    - `local`, `smoke`, `ci`, `detect` modes.
  - invariants / assumptions:
    - Fails fast on missing toolchain and placeholder artifacts.
  - dependencies:
    - `git`, `python`, `make`, `uv`, `node`, `pnpm`.
  - tests:
    - Executed directly on Windows verification paths.
- `Makefile` - Verification contract target definitions.
  - public surface / key exports:
    - `verify-local`, `verify-smoke`, `verify-ci`.
  - invariants / assumptions:
    - Must run real checks (placeholders are transitional only).
  - dependencies:
    - Project tooling and language-specific commands.
  - tests:
    - Called by verify scripts.

## 10) Runbook (minimal)
- How to run locally:
  - Intake/planning:
    - use skill `project-intake` to maintain `.agentkit/docs/ROADMAP.md`.
    - use skill `ticket-planning` before implementing each roadmap ticket.
  - Verification:
    - Bash: `./.agentkit/scripts/verify.sh local`
    - PowerShell: `pwsh -File .agentkit/scripts/verify.ps1 local`
- Required env vars:
  - None required for current doc/process-only baseline.
  - Future service/env requirements will be added as implementation begins.
- Troubleshooting:
  - If verification fails due missing tools, install required toolchain; do not add bypass scripts.
  - If DOC gate fails, update `.agentkit/docs/PROJECT_MAP.md` in the same ticket.

---

## Map changelog (most recent first)
- 2026-02-23 [project-intake-2026-02-23] Replaced template map with concrete repository memory and aligned it to the new roadmap baseline.
