# Local rules (project-specific) — Decider

These rules customize AgentKit for THIS project.
They must reflect real constraints: tenant isolation, Keycloak OIDC, API versioning, migrations, auditability, and strict verification.

Files:
- `project-context.md` — what this system is, who uses it, what is high-risk, and what must be documented
- `architecture.md` — microservices boundaries, shared libs policy, clean-ish layering
- `security.md` — Keycloak/OIDC, scopes, tenant isolation, headers/CORS, injection/SSRF, secrets, audit logging
- `testing.md` — strict e2e policy: local smoke + CI full UI+API, coverage rules
- `workflow.md` — trunk-based workflow, “no approval → no change” rules, audit logging, DOC-gates

Non-negotiable:
- `.agentkit/docs/PROJECT_MAP.md` must be updated on every ticket (strict).
- No “DOC_SKIP” or similar bypass is allowed.