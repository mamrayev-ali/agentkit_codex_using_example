import os
from dataclasses import dataclass
from functools import lru_cache


def _parse_csv(value: str) -> tuple[str, ...]:
    entries = [item.strip() for item in value.split(",")]
    parsed = [item for item in entries if item]
    return tuple(parsed)


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AppSettings:
    app_name: str = "Decider API"
    public_api_prefix: str = "/api/v1"
    public_api_version: str = "1.0.0"
    database_url: str = "sqlite:///./services/api/decider.db"
    keycloak_issuer: str = ""
    keycloak_audience: str = ""
    keycloak_jwks_json: str = ""
    keycloak_tenant_claim_names: tuple[str, ...] = ("tenant_id", "tenant", "org_id")
    ingestion_task_always_eager: bool = True
    ingestion_task_broker_url: str = "memory://"
    ingestion_task_backend_url: str = "cache+memory://"
    ingestion_http_timeout_seconds: float = 5.0
    ingestion_http_max_retries: int = 2
    ingestion_http_backoff_seconds: float = 0.25
    observability_log_level: str = "INFO"
    observability_correlation_header: str = "X-Correlation-ID"
    observability_enable_request_logging: bool = True
    observability_enable_metrics: bool = True
    observability_enable_exception_reporting: bool = True


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings(
        app_name=os.getenv("DECIDER_APP_NAME", "Decider API"),
        public_api_prefix=os.getenv("DECIDER_PUBLIC_API_PREFIX", "/api/v1"),
        public_api_version=os.getenv("DECIDER_PUBLIC_API_VERSION", "1.0.0"),
        database_url=os.getenv(
            "DECIDER_DATABASE_URL",
            "sqlite:///./services/api/decider.db",
        ),
        keycloak_issuer=os.getenv("DECIDER_KEYCLOAK_ISSUER", ""),
        keycloak_audience=os.getenv("DECIDER_KEYCLOAK_AUDIENCE", ""),
        keycloak_jwks_json=os.getenv("DECIDER_KEYCLOAK_JWKS_JSON", ""),
        keycloak_tenant_claim_names=_parse_csv(
            os.getenv(
                "DECIDER_KEYCLOAK_TENANT_CLAIMS",
                "tenant_id,tenant,org_id",
            )
        ),
        ingestion_task_always_eager=_parse_bool(
            os.getenv("DECIDER_INGESTION_TASK_ALWAYS_EAGER", "true")
        ),
        ingestion_task_broker_url=os.getenv(
            "DECIDER_INGESTION_TASK_BROKER_URL",
            "memory://",
        ),
        ingestion_task_backend_url=os.getenv(
            "DECIDER_INGESTION_TASK_BACKEND_URL",
            "cache+memory://",
        ),
        ingestion_http_timeout_seconds=float(
            os.getenv("DECIDER_INGESTION_HTTP_TIMEOUT_SECONDS", "5.0")
        ),
        ingestion_http_max_retries=int(
            os.getenv("DECIDER_INGESTION_HTTP_MAX_RETRIES", "2")
        ),
        ingestion_http_backoff_seconds=float(
            os.getenv("DECIDER_INGESTION_HTTP_BACKOFF_SECONDS", "0.25")
        ),
        observability_log_level=os.getenv("DECIDER_OBSERVABILITY_LOG_LEVEL", "INFO"),
        observability_correlation_header=os.getenv(
            "DECIDER_OBSERVABILITY_CORRELATION_HEADER",
            "X-Correlation-ID",
        ),
        observability_enable_request_logging=_parse_bool(
            os.getenv("DECIDER_OBSERVABILITY_ENABLE_REQUEST_LOGGING", "true")
        ),
        observability_enable_metrics=_parse_bool(
            os.getenv("DECIDER_OBSERVABILITY_ENABLE_METRICS", "true")
        ),
        observability_enable_exception_reporting=_parse_bool(
            os.getenv("DECIDER_OBSERVABILITY_ENABLE_EXCEPTION_REPORTING", "true")
        ),
    )
