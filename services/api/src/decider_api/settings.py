import os
from dataclasses import dataclass
from functools import lru_cache


def _parse_csv(value: str) -> tuple[str, ...]:
    entries = [item.strip() for item in value.split(",")]
    parsed = [item for item in entries if item]
    return tuple(parsed)


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
    )
