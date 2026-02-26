from functools import lru_cache

from fastapi import Depends, Header, HTTPException, status

from decider_api.application.auth_context import build_auth_context_response
from decider_api.infrastructure.auth.token_validator import (
    KeycloakTokenValidator,
    TokenValidationError,
)
from decider_api.settings import get_settings


@lru_cache(maxsize=1)
def get_token_validator() -> KeycloakTokenValidator:
    settings = get_settings()
    if settings.keycloak_jwks_url:
        return KeycloakTokenValidator.from_jwks_url(
            issuer=settings.keycloak_issuer,
            audience=settings.keycloak_audience,
            tenant_claim_names=settings.keycloak_tenant_claim_names,
            jwks_url=settings.keycloak_jwks_url,
            timeout_seconds=settings.keycloak_jwks_timeout_seconds,
        )
    return KeycloakTokenValidator.from_jwks_json(
        issuer=settings.keycloak_issuer,
        audience=settings.keycloak_audience,
        tenant_claim_names=settings.keycloak_tenant_claim_names,
        jwks_json=settings.keycloak_jwks_json,
    )


def get_authenticated_auth_context(
    authorization: str | None = Header(default=None),
    validator: KeycloakTokenValidator = Depends(get_token_validator),
) -> dict[str, object]:
    try:
        claims = validator.validate_authorization_header(authorization)
    except TokenValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        ) from exc
    return build_auth_context_response(
        claims=claims,
        tenant_claim_names=validator.tenant_claim_names,
    )
