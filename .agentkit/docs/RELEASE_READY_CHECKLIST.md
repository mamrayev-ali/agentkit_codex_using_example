# RELEASE_READY_CHECKLIST

This checklist defines the production-branch release gate for Decider.

## 1) CI contract (mandatory)
- `verify-ci-contract` job is green.
- `api-e2e` job is green.
- `ui-e2e` job is green.
- `ui-runtime-walkthrough` job is green.
- `security-semgrep` job is green.
- `security-trivy-fs` job is green.
- `security-codeql` job is green.
- `release-gate` job is green.

## 2) High-risk ticket closure rule (mandatory)
- Tickets touching high-risk areas must not be marked Done until all jobs listed above are green.
- PR reviewers must block merge if any required gate is red, cancelled, or missing.

## 3) Evidence requirements (mandatory)
- CI run URL is captured in ticket summary.
- Artifact links are attached when applicable:
  - Playwright report artifact from `ui-e2e`
  - Runtime walkthrough Playwright report artifact from `ui-runtime-walkthrough`
  - Walkthrough report/logs showing `demo-user` and `demo-admin` seeded journeys passed
  - SARIF findings from Trivy and CodeQL security tabs
- Walkthrough evidence must map back to `.agentkit/docs/DEMO_SCENARIOS.md`:
  - user journey covers dashboard, dossiers, searches, and export acceptance
  - admin journey covers entitlement update, audit review, and post-refresh user access change

## 4) Branch protection recommendation
- Configure production branch protection to require successful status checks:
  - `verify-ci-contract`
  - `api-e2e`
  - `ui-e2e`
  - `ui-runtime-walkthrough`
  - `security-semgrep`
  - `security-trivy-fs`
  - `security-codeql`
  - `release-gate`

## 5) Manual pre-release confirmation
- Confirm no unresolved high/critical vulnerabilities in security scan outputs.
- Confirm release notes reference ticket IDs and risk notes.
- Confirm rollback owner and communication channel are assigned before deploy.
- Confirm the seeded walkthrough baseline was reseeded before collecting final user/admin evidence.
