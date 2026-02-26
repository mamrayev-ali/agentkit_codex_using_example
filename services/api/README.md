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

## Ingestion foundation (T10)

T10 adds a background-ingestion foundation under
`services/api/src/decider_api/infrastructure/ingestion/`:

- URL validation policy with SSRF guards (`domain/url_policy.py`)
- source-adapter abstraction (`domain/source_adapter.py`)
- retry-aware HTTP client (`infrastructure/ingestion/http_client.py`)
- Celery queue skeleton with eager local processing fallback
  (`infrastructure/ingestion/celery_app.py`)
- ingestion task orchestration (`infrastructure/ingestion/tasks.py`)

### Environment variables

- `DECIDER_INGESTION_TASK_ALWAYS_EAGER` (default: `true`)
- `DECIDER_INGESTION_TASK_BROKER_URL` (default: `memory://`)
- `DECIDER_INGESTION_TASK_BACKEND_URL` (default: `cache+memory://`)
- `DECIDER_INGESTION_HTTP_TIMEOUT_SECONDS` (default: `5.0`)
- `DECIDER_INGESTION_HTTP_MAX_RETRIES` (default: `2`)
- `DECIDER_INGESTION_HTTP_BACKOFF_SECONDS` (default: `0.25`)

### Run Celery worker (non-eager mode)

Set `DECIDER_INGESTION_TASK_ALWAYS_EAGER=false` and start worker:

```powershell
uv run --directory services/api celery -A decider_api.infrastructure.ingestion.worker:celery_app worker --loglevel=INFO
```

In this mode, ingestion jobs are queued with Celery `.delay(...)` instead of being
executed synchronously in-process.
