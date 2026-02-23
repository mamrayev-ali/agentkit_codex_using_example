# Security (local) — Decider

Decider processes sensitive data. Default stance: strict isolation, least privilege, secure-by-default.

## Core invariants (non-negotiable)
1) Tenant isolation:
   - requests must not access data from another tenant
   - enforce server-side every time (never rely on frontend)
2) Explicit permission/scope:
   - critical actions require explicit scopes/permissions (e.g., export)
3) Auditability:
   - high-risk actions produce audit records with correlation_id (no PII payload)

## Keycloak / OIDC rules
- Flow: Authorization Code + PKCE (plus corporate SSO via Keycloak)
- Backend must:
  - validate token signature/issuer/audience
  - verify token is not expired
  - map roles/scopes consistently
  - enforce tenant scope: token tenant claim must match requested org/tenant

## AuthZ model
- RBAC (admin/user) + module-level permissions within tenant.
- Any permission change is high-risk:
  - PR required
  - threat model required
  - changes must be logged in agent log under [SECURITY]

## Scopes (example: export:data)
For endpoints like `/api/v1/org/{org_id}/export`:
- require scope `export:data`
- enforce `tenant_id == org_id` (or equivalent tenant claim mapping)
- users without scope must get 403 (even if UI hides the button)

## Web security
### CORS
- Allow-list origins per environment (dev/stage/prod).
- Never ship permissive CORS to prod.

### Security headers
- CSP enabled (project uses CSP)
- plus: HSTS, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
- Any change to headers is high-risk.

### Cookies / sessions
If cookies are used:
- HttpOnly + Secure + SameSite=Lax/Strict

## Injection & input validation (explicit checklist)
- SQL injection:
  - parameterized queries only
  - avoid string formatting SQL
- NoSQL injection:
  - validate filters; allow-list fields/operators
- command injection:
  - never pass user input to shell
- template injection / XSS:
  - avoid unsafe HTML injection; never bypass sanitization without approval
- SSRF:
  - any “fetch URL” must allow-list domains/IP ranges and block internal networks

## Data leakage / logs
- Never log tokens, secrets, passwords, raw exported datasets, or PII.
- Logs may include:
  - correlation_id
  - org_id/tenant_id
  - user_id (internal id)
  - action + status + durations
- For exports: log metadata only (row_count/status), never content.

## Supply chain / dependencies
- lockfiles are required
- adding new deps needs explicit approval (explain why)
- in CI: CodeQL/Semgrep + container scanning are required

## High-risk rule (strict)
If ticket touches any of:
- auth/permissions/scopes
- migrations
- public API contracts
- security headers
- payments/finance
Then:
- PR/MR mandatory
- threat model mandatory
- migration plan mandatory if schema changes
- cannot merge without green CI (including full e2e + security jobs)