# Workflow (local) — Decider

## Branching
- trunk-based development, short-lived branches
- default: developer creates branch
- PR/MR is optional for low-risk, but mandatory for high-risk.

## High-risk definition (strict)
High-risk if ticket touches:
- auth/permissions/scopes
- migrations
- public API contracts (OpenAPI), versioning/breaking changes
- security headers / CORS / cookies
- payments/finance

High-risk requires:
- PR/MR mandatory
- threat-model mandatory
- migration plan + rollback mandatory if schema changes
- cannot merge without green CI (incl. full e2e + security jobs)

## Forbidden without explicit approval (hard stops)
- touch files outside the repo
- download new dependencies / use network access without explaining why and getting approval
- DB migrations without migration plan + rollback
- CI/CD, Docker, k8s changes without a dedicated ticket + approval
- auth/permissions changes without threat-model note in agent log
- generating or writing secrets/keys into files
- large refactors without a separate ticket

## Auditability requirements
- Agent must always show diffs (and summarize changes) before declaring “done”.
- Agent log must be readable and sequential with tags:
  - [PLAN], [ACT], [DIFF], [TEST], [DOC], [SECURITY], [MCP:*]

## Documentation gate
- `.agentkit/docs/PROJECT_MAP.md` MUST be updated on every ticket.
- No bypass flags (DOC_SKIP forbidden).
- verify must fail if PROJECT_MAP wasn’t updated.

## Verification integrity (no-bypass)

If tools are missing locally (uv/pnpm/make/bash), the agent must NOT:
- change Makefile/verify scripts to bypass checks
- add placeholder tasks that always pass
- create alternative runners that mask failures

Required action:
- stop and provide exact install steps (Windows/Linux)
- or create a dedicated tooling ticket to add OS-native wrappers (e.g., verify.ps1) without changing semantics.

## Development environment policy (container-first)

Default mode: **container-first**.
The agent must run all tooling (format/lint/type/tests/e2e/deps install) **inside Docker containers**.

Host machine is treated as “clean”:
- Allowed on host: git, docker, docker compose, basic file edits.
- Not allowed on host: installing project toolchains (uv/pnpm/python deps/node_modules), except with explicit approval.

If a command requires dependencies, the agent must:
1) ensure containers are running
2) execute the command inside the dev container (see Runbook commands below)
3) record [ACT]/[TEST] logs with the exact docker command used.

## Dependency download policy

Pre-approved inside containers:
- `uv sync` / `uv pip install` **only from lockfile / pinned versions**
- `pnpm install` **only with pnpm-lock.yaml**
- pulling Docker images from approved registries (default: Docker Hub) for dev services

NOT allowed without explicit approval:
- adding new dependencies (changes to pyproject.toml / package.json / lockfiles)
- installing tools globally on host
- downloading binaries/scripts via curl/irm from random URLs

## Host safety
- Never write outside repository root without approval.
- Use Docker volumes for databases/caches.
- Never store secrets in repo files. Use `.env.local` (gitignored) or Docker secrets.

## Runbook (how to run commands)

Start dev environment:
- `docker compose -f docker-compose.dev.yml up -d`

Run a command inside dev container:
- `docker compose -f docker-compose.dev.yml run --rm dev <command>`

Examples:
- `docker compose -f docker-compose.dev.yml run --rm dev make verify-local`
- `docker compose -f docker-compose.dev.yml run --rm dev make verify-smoke`

Stop:
- `docker compose -f docker-compose.dev.yml down -v`