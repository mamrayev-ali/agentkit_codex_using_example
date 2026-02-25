# Decider API (T4 baseline)

Backend scaffold with versioned public API contract baseline for ticket T4.

## Run

```powershell
uv run --directory services/api uvicorn decider_api.app:app --host 0.0.0.0 --port 8000
```

## Public API (v1)

- `GET /api/v1/health`
- `GET /api/v1/auth/context`
- `GET /api/v1/tenants/{tenant_id}/resources`

OpenAPI source of truth:

- `services/api/openapi/openapi.v1.json`

## Test

```powershell
uv run --directory services/api pytest -q -m smoke
uv run --directory services/api pytest -q
```
