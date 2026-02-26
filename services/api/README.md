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

## Auth runtime settings (Keycloak)

The API supports two JWKS configuration modes:

- Static JWKS JSON:
  - `DECIDER_KEYCLOAK_JWKS_JSON`
- JWKS URL (recommended for local runtime stack):
  - `DECIDER_KEYCLOAK_JWKS_URL`
  - `DECIDER_KEYCLOAK_JWKS_TIMEOUT_SECONDS` (default: `5.0`)

Shared auth settings:

- `DECIDER_KEYCLOAK_ISSUER`
- `DECIDER_KEYCLOAK_AUDIENCE`
- `DECIDER_KEYCLOAK_TENANT_CLAIMS`

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

## Observability guardrails (T11)

T11 adds observability modules under
`services/api/src/decider_api/infrastructure/observability/`:

- correlation-id normalization and request context (`correlation.py`)
- structured JSON logging formatter/filter (`logging.py`)
- in-memory Prometheus-text metrics registry (`metrics.py`)
- exception reporting hook abstraction (`exceptions.py`)

### Behavior

- API propagates correlation id via `X-Correlation-ID` request/response header by default.
- Request lifecycle logs include safe metadata only:
  - `correlation_id`, `http_method`, `http_route`, `status_code`, `duration_ms`
- Metrics endpoint is available at `GET /metrics` and intentionally excluded from OpenAPI v1 schema.

### Observability environment variables

- `DECIDER_OBSERVABILITY_LOG_LEVEL` (default: `INFO`)
- `DECIDER_OBSERVABILITY_CORRELATION_HEADER` (default: `X-Correlation-ID`)
- `DECIDER_OBSERVABILITY_ENABLE_REQUEST_LOGGING` (default: `true`)
- `DECIDER_OBSERVABILITY_ENABLE_METRICS` (default: `true`)
- `DECIDER_OBSERVABILITY_ENABLE_EXCEPTION_REPORTING` (default: `true`)
