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
  - Current tracked state:
    - `services/api/` contains the minimal FastAPI scaffold from T2.
    - Layered package boundary is present: `api`, `application`, `domain`, `infrastructure`.
    - Public bootstrap endpoint exists: `GET /health` (contract-only response).
- `logs/agent/` - Local human-readable ticket logs (gitignored).

## 2) Key contracts & boundaries
- Architectural principles:
  - Workflow-first repository with strict documentation and verification gates.
  - Future service code should follow clean layering and explicit boundaries from local rules.
- Public interfaces:
  - Minimal public runtime endpoint exists at `GET /health` for liveness scaffold.
  - OpenAPI contract baseline and broader API versioning remain planned for T4.
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
  - Runtime-only contract for `GET /health` exists in code (`services/api/src/decider_api/api/routes/health.py`).
  - Formal OpenAPI source of truth is still planned for T4.
- Versioning strategy:
  - Planned baseline: `/api/v1`.
- Critical endpoints / operations (planned):
  - health endpoint (`/health`) with exact response `{ "status": "ok" }`
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
  - Runs real profile-aware checks via `.agentkit/scripts/verification_contract.py`.
  - Always runs `DOC-gate + placeholder-ban + detect + scaffold contract checks`.
  - In `scaffold-only` profile, does not require `uv`/`pnpm`.
  - In `backend-present` profile, adds backend toolchain checks (configured in `Makefile`):
    - smoke: `uv run --directory services/api pytest -q -m smoke`
    - local: `uv run --directory services/api pytest -q`
    - ci: `uv run --directory services/api pytest -q --maxfail=1 --disable-warnings`
  - In `frontend-present` profile, adds frontend toolchain checks (configured in `Makefile`).
- Coverage target:
  - Local rules set >=80% coverage for critical modules once implemented.
- API e2e smoke definition:
  - Current implemented minimum (T2): in-process HTTP smoke for `GET /health` with status `200` and exact JSON `{ "status": "ok" }`.
  - Broader happy-path + negative-403 policy remains for later security-sensitive endpoints.
- Windows evidence policy (source of truth for local verification on this repo):
  - Required: `pwsh -File .agentkit/scripts/verify.ps1 smoke`
  - Required: `pwsh -File .agentkit/scripts/verify.ps1 local`
  - Optional on Windows: `./.agentkit/scripts/verify.sh local` (if Git Bash is available)

### CI DoD (must pass before ticket is Done)
- `make verify-ci` does:
  - Runs real profile-aware CI checks via `Makefile` contract.
  - Includes shared preflight (`DOC-gate + placeholder-ban + detect`) and profile-specific checks.
- Linux CI contract entrypoints:
  - `./.agentkit/scripts/verify.sh local`
  - `make verify-ci`
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
    - `detect`, `local`, `smoke`, and `ci` modes.
  - invariants / assumptions:
    - Any non-PROJECT_MAP file change requires PROJECT_MAP update.
  - dependencies:
    - `git`, `make`, `Makefile` contract targets.
  - tests:
    - Executed directly in Linux/CI verification paths.
- `.agentkit/scripts/verify.ps1` - Windows-native verification runner.
  - public surface / key exports:
    - `local`, `smoke`, `ci`, `detect` modes.
  - invariants / assumptions:
    - Fails fast on missing base toolchain and placeholder artifacts.
    - Requires `uv` only when backend markers are present.
    - Requires `node`/`pnpm` only when frontend markers are present.
  - dependencies:
    - Always: `git`, `python`, `make`.
    - Conditional by profile: `uv` (backend), `node` + `pnpm` (frontend).
  - tests:
    - Executed directly on Windows verification paths.
- `.agentkit/scripts/verification_contract.py` - Shared verification preflight contract.
  - public surface / key exports:
    - `detect`, `doc-gate`, `placeholder-ban`, `scaffold-contract`, `verify --mode`.
  - invariants / assumptions:
    - Any verification mode runs DOC discipline and placeholder-ban checks.
    - Scaffold-only verification must remain independent of backend/frontend package managers.
  - dependencies:
    - `python`, `git`.
  - tests:
    - Called from `Makefile` verify targets.
- `Makefile` - Verification contract target definitions.
  - public surface / key exports:
    - `detect`, `verify-local`, `verify-smoke`, `verify-ci`.
  - invariants / assumptions:
    - Must run real checks (no placeholder behavior).
    - Must support profile matrix: scaffold-only / backend-present / frontend-present / backend+frontend.
  - dependencies:
    - `.agentkit/scripts/verification_contract.py`.
    - Project tooling and language-specific commands by profile.
  - tests:
    - Called by verify scripts.
- `services/api/pyproject.toml` - Backend project marker + dependency/test configuration.
  - public surface / key exports:
    - Declares backend profile marker and Python test configuration.
  - invariants / assumptions:
    - Enables `backend-present` verification profile.
  - dependencies:
    - FastAPI runtime and pytest/httpx test stack.
  - tests:
    - Consumed by `uv run --directory services/api pytest ...` commands.
- `services/api/uv.lock` - Locked backend dependency graph for reproducible installs.
  - public surface / key exports:
    - Pins resolved Python packages for `services/api`.
  - invariants / assumptions:
    - Must stay in sync with `services/api/pyproject.toml`.
  - dependencies:
    - Generated/updated by `uv sync --directory services/api`.
  - tests:
    - Indirectly validated by `verify-smoke` and `verify-local` in backend profile.
- `services/api/src/decider_api/app.py` - FastAPI entrypoint and app factory.
  - public surface / key exports:
    - `create_app()` and module-level `app` ASGI object.
  - invariants / assumptions:
    - Registers only `/health` in T2 scope.
  - dependencies:
    - `decider_api.settings`, `decider_api.api.routes.health`.
  - tests:
    - Covered by `services/api/tests/test_health_http.py`.
- `services/api/src/decider_api/application/health.py` - Health contract provider.
  - public surface / key exports:
    - `get_health_response()` returns exact payload contract.
  - invariants / assumptions:
    - Response must remain `{ "status": "ok" }`.
  - dependencies:
    - none (pure function).
  - tests:
    - Covered by `services/api/tests/test_health_unit.py`.
- `services/api/src/decider_api/api/routes/health.py` - Health route handler.
  - public surface / key exports:
    - `GET /health` endpoint.
  - invariants / assumptions:
    - Must not call DB or external services.
    - Must return `200` with exact JSON payload contract.
  - dependencies:
    - `decider_api.application.health`.
  - tests:
    - Covered by HTTP smoke test.

## 10) Runbook (minimal)
- How to run locally:
  - Intake/planning:
    - use skill `project-intake` to maintain `.agentkit/docs/ROADMAP.md`.
    - use skill `ticket-planning` before implementing each roadmap ticket.
  - Verification:
    - Bash: `./.agentkit/scripts/verify.sh local`
    - Bash detect: `./.agentkit/scripts/verify.sh detect`
    - PowerShell: `pwsh -File .agentkit/scripts/verify.ps1 local`
    - PowerShell smoke: `pwsh -File .agentkit/scripts/verify.ps1 smoke`
    - PowerShell detect: `pwsh -File .agentkit/scripts/verify.ps1 detect`
- Required env vars:
  - None required for the current minimal `/health` scaffold.
  - Future service/env requirements will be added in later tickets.
- Troubleshooting:
  - If verification fails due missing tools, install required toolchain for the active profile; do not add bypass scripts.
  - If DOC gate fails, update `.agentkit/docs/PROJECT_MAP.md` in the same ticket.
  - For backend-present profile:
    - ensure `uv` is installed and available on PATH
    - run `uv run --directory services/api pytest -q`
  - Start API manually:
    - `uv run --directory services/api uvicorn decider_api.app:app --host 0.0.0.0 --port 8000`
    - `GET /health` must return `{ "status": "ok" }`

---

## Map changelog (most recent first)
- 2026-02-23 [T2] Added minimal backend scaffold under `services/api` with FastAPI app factory, `/health` endpoint contract, and unit + HTTP smoke tests; updated verification map for backend-present profile.
- 2026-02-23 [T1] Replaced placeholder verify targets with a profile-aware verification contract (`Makefile`, `verify.sh`, `verify.ps1`, `verification_contract.py`) and documented Windows-first local evidence policy.
- 2026-02-23 [project-intake-2026-02-23] Replaced template map with concrete repository memory and aligned it to the new roadmap baseline.
