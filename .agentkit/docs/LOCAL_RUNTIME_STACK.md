# LOCAL_RUNTIME_STACK

This runbook starts the local Decider walkthrough stack for T13:
- frontend
- api
- postgres
- redis
- keycloak

## 1) Prerequisites
1. Docker Desktop is running.
2. Create runtime env file with local-only credentials:

```bash
cp .env.runtime.example .env.runtime
```

3. Keep `DECIDER_LOCAL_API_PORT=8000` for the default frontend walkthrough.
   The checked-in frontend development environment targets `http://localhost:8000/api/v1`.
   If you override the API host port, update the frontend dev environment config before testing login.

4. Optional if port `8000` is already occupied on host and you are also updating the frontend dev API base URL:

```bash
export DECIDER_LOCAL_API_PORT=8001
```

## 2) Start (one command)

```bash
docker compose -f docker-compose.dev.yml --profile runtime --env-file .env.runtime up -d --build
```

## 3) Health checks

```bash
docker compose -f docker-compose.dev.yml --profile runtime --env-file .env.runtime ps
```

Expected exposed endpoints:
- frontend: `http://localhost:4200`
- api health: `http://localhost:<DECIDER_LOCAL_API_PORT>/api/v1/health` (default `8000`)
- keycloak realm metadata: `http://localhost:8080/realms/decider-local/.well-known/openid-configuration`

## 4) Reset and reseed deterministic demo data

Apply the canonical T19 walkthrough baseline inside the running API container:

```bash
docker compose -f docker-compose.dev.yml --profile runtime --env-file .env.runtime exec api \
  uv run --frozen python -m decider_api.demo_seed reseed
```

Optional commands:

```bash
docker compose -f docker-compose.dev.yml --profile runtime --env-file .env.runtime exec api \
  uv run --frozen python -m decider_api.demo_seed reset
```

```bash
docker compose -f docker-compose.dev.yml --profile runtime --env-file .env.runtime exec api \
  uv run --frozen python -m decider_api.demo_seed summary
```

The walkthrough checklist and expected IDs live in `.agentkit/docs/DEMO_SCENARIOS.md`.

## 5) Get a real Keycloak token (demo user)

```bash
curl -sS -X POST http://localhost:8080/realms/decider-local/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=decider-cli" \
  -d "username=demo-user" \
  -d "password=${DECIDER_KEYCLOAK_DEMO_USER_PASSWORD}"
```

PowerShell:

```powershell
curl.exe -X POST "http://localhost:8080/realms/decider-local/protocol/openid-connect/token" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "grant_type=password" `
  -d "client_id=decider-cli" `
  -d "username=demo-user" `
  -d "password=<value-from-.env.runtime>"
```

Use returned `access_token` against API:

```bash
curl -sS http://localhost:${DECIDER_LOCAL_API_PORT:-8000}/api/v1/auth/context \
  -H "Authorization: Bearer <access_token>"
```

## 6) Stop (one command)

```bash
docker compose -f docker-compose.dev.yml --profile runtime --env-file .env.runtime down -v
```

## 7) Troubleshooting
- If `keycloak-bootstrap` exits with user-not-found, inspect Keycloak logs and realm import path:

```bash
docker compose -f docker-compose.dev.yml --profile runtime --env-file .env.runtime logs keycloak --tail 200
```

- If API returns `401` for valid token, check issuer/audience/JWKS settings in API container:

```bash
docker compose -f docker-compose.dev.yml --profile runtime --env-file .env.runtime logs api --tail 200
```

- If the walkthrough UI or API no longer matches the documented baseline, reseed and print the manifest again:

```bash
docker compose -f docker-compose.dev.yml --profile runtime --env-file .env.runtime exec api \
  uv run --frozen python -m decider_api.demo_seed reseed
docker compose -f docker-compose.dev.yml --profile runtime --env-file .env.runtime exec api \
  uv run --frozen python -m decider_api.demo_seed summary
```
