# Testing (local) — Decider

Policy highlights:
- Coverage target applies to critical modules (>= 80%).
- Every ticket must satisfy: local smoke + CI full e2e (UI+API).
- No bypass. PROJECT_MAP update is mandatory for every ticket.

## Critical modules (coverage applies)
Treat these as “critical modules” for coverage >= 80%:
- tenant resolution / org scoping
- authn/authz (Keycloak integration, scopes, permissions)
- export flows + audit trails
- admin permission management
- any payment/finance integration modules
- any code that enforces security headers / CORS policies

## Test layers
### Backend
- Unit tests (pytest): domain and policy rules, pure logic
- Integration tests: DB repositories, Keycloak claim mapping (mocked), service wiring
- API e2e:
  - Smoke (local): small HTTP suite for critical path
  - Full (CI): broader API suite including negative checks

### Frontend
- Unit tests (Vitest): components/services, permission-driven rendering
- UI e2e (Playwright, CI): critical user flows + key negative cases

## Mandatory e2e flows (minimum acceptance suite)
Your CI full e2e must cover at least these flows:
1) SSO login (Keycloak) → tenant selection/autodetect → module visibility matches entitlements
2) Admin enables a module for a tenant → user sees new module and gains access
3) Export is gated by `export:data` scope and tenant isolation:
   - without scope: 403
   - wrong org_id: 403
   - with scope + correct org: 200 + audit record created

Local smoke must cover “fast subset” of the above (at least one happy path + at least one negative 403).

## Contract with tooling
- Local required:
  - format/lint/type
  - unit + integration
  - coverage check for critical modules
  - API e2e smoke (HTTP)
- CI required:
  - full UI e2e (Playwright)
  - full API e2e
  - SAST/DAST/container scans
  - migrations applied in ephemeral env when schema changes

## Anti-flake rules
- no sleeps; use deterministic waits
- isolated test data per tenant
- tests must not rely on real external services (mock/stub)