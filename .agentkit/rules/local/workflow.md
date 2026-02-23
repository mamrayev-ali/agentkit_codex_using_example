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