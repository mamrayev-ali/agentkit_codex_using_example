import json
import urllib.error
from typing import Final

import pytest
from fastapi.testclient import TestClient

from decider_api.api.dependencies.auth import get_token_validator
from decider_api.app import app
from decider_api.infrastructure.auth.token_validator import (
    KeycloakTokenValidator,
    TokenValidationError,
)


_FIXED_NOW: Final[int] = 1_736_500_000
_ISSUER: Final[str] = "https://keycloak.example/realms/decider"
_AUDIENCE: Final[str] = "decider-api"
_KID: Final[str] = "test-key-1"
_N_B64: Final[str] = (
    "XmRJgMLcaLh8YecUy_CVbJVkuZoD1CMBDGlCj4AqAsWSrE12UKjX301CO7jrq5CT8VSmkoX-9"
    "evMiVQxF1Iuv18sncsYIKNyxv8VqBhzA1dyKJDNmusjYgoOOSaHYfBX63TqqSZpkHGux9locz"
    "6OKHB4zf-thQkTRMG1y-qHOVE"
)

_VALID_TOKEN: Final[str] = (
    "eyJhbGciOiJSUzI1NiIsImtpZCI6InRlc3Qta2V5LTEiLCJ0eXAiOiJKV1QifQ."
    "eyJhdWQiOiJkZWNpZGVyLWFwaSIsImV4cCI6MTczNjUwMzYwMCwiaXNzIjoiaHR0cHM6Ly9rZXlj"
    "bG9hay5leGFtcGxlL3JlYWxtcy9kZWNpZGVyIiwicmVhbG1fYWNjZXNzIjp7InJvbGVzIjpbImFu"
    "YWx5c3QiXX0sInJlc291cmNlX2FjY2VzcyI6eyJkZWNpZGVyLWFwaSI6eyJyb2xlcyI6WyJvcGVy"
    "YXRvciJdfX0sInJvbGVzIjpbInVzZXIiXSwic2NvcGUiOiJyZWFkOmRhdGEgZXhwb3J0OmRhdGEi"
    "LCJzY3AiOlsid2F0Y2hsaXN0OnZpZXciXSwic3ViIjoidXNlci0xMjMiLCJ0ZW5hbnRfaWQiOiJh"
    "Y21lIn0."
    "QFgw_DtGHnCyRntALksw4f5D_UsHILO5yf4eF9vDyDA1yOLv_FInVSwyzEHhV73ZBVZcZz_I5nuv"
    "-NU6kXlX8rJ_-0vu4dQD9XqRe2GBI5g6fgxJhlzlKRCsi1HWkyIkMxzlCLbgnQOkDMaIOitY7S4i"
    "i47T5YwSQbCzbBQNNHo"
)
_BAD_ISSUER_TOKEN: Final[str] = (
    "eyJhbGciOiJSUzI1NiIsImtpZCI6InRlc3Qta2V5LTEiLCJ0eXAiOiJKV1QifQ."
    "eyJhdWQiOiJkZWNpZGVyLWFwaSIsImV4cCI6MTczNjUwMzYwMCwiaXNzIjoiaHR0cHM6Ly9iYWQu"
    "ZXhhbXBsZS9yZWFsbXMvZGVjaWRlciIsInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJhbmFseXN0"
    "Il19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiZGVjaWRlci1hcGkiOnsicm9sZXMiOlsib3BlcmF0b3Ii"
    "XX19LCJyb2xlcyI6WyJ1c2VyIl0sInNjb3BlIjoicmVhZDpkYXRhIGV4cG9ydDpkYXRhIiwic2Nw"
    "IjpbIndhdGNobGlzdDp2aWV3Il0sInN1YiI6InVzZXItMTIzIiwidGVuYW50X2lkIjoiYWNtZSJ9."
    "FztlE0rXhJA84CozUxLVXqCReXEzL7fT5RIEhmTLUTwPWomNdka1GJCLcONPobVA6_B_n9LLLU0V"
    "sS52lmEI49KBxSVvYKr3uT51KJzLWCgvUjLSHi01gTx05WB-JId5y0uarse7tJMRFhsUrkilwawW"
    "KtorcpEbMWSQw-iHwUA"
)
_BAD_AUDIENCE_TOKEN: Final[str] = (
    "eyJhbGciOiJSUzI1NiIsImtpZCI6InRlc3Qta2V5LTEiLCJ0eXAiOiJKV1QifQ."
    "eyJhdWQiOiJ3cm9uZy1hdWRpZW5jZSIsImV4cCI6MTczNjUwMzYwMCwiaXNzIjoiaHR0cHM6Ly9r"
    "ZXljbG9hay5leGFtcGxlL3JlYWxtcy9kZWNpZGVyIiwicmVhbG1fYWNjZXNzIjp7InJvbGVzIjpb"
    "ImFuYWx5c3QiXX0sInJlc291cmNlX2FjY2VzcyI6eyJkZWNpZGVyLWFwaSI6eyJyb2xlcyI6WyJv"
    "cGVyYXRvciJdfX0sInJvbGVzIjpbInVzZXIiXSwic2NvcGUiOiJyZWFkOmRhdGEgZXhwb3J0OmRh"
    "dGEiLCJzY3AiOlsid2F0Y2hsaXN0OnZpZXciXSwic3ViIjoidXNlci0xMjMiLCJ0ZW5hbnRfaWQi"
    "OiJhY21lIn0."
    "U911P_1FYOZVVcpFtkPjPjsw13E_8qLWjeWdqzFrGTvyoLR5BymBQ8Px_lxy-bFvL6x6Hfgc17LB"
    "KPQvC_G_OypORnWW6g9NmbSPecjKHV4wO6c9iQhJh8-QjJkUCovcyHxG3D1iYgtsSSwVOm0UYddH"
    "O0QBJZfH5pm1Zgm1Mlk"
)
_EXPIRED_TOKEN: Final[str] = (
    "eyJhbGciOiJSUzI1NiIsImtpZCI6InRlc3Qta2V5LTEiLCJ0eXAiOiJKV1QifQ."
    "eyJhdWQiOiJkZWNpZGVyLWFwaSIsImV4cCI6MTczNjQ5OTk5OSwiaXNzIjoiaHR0cHM6Ly9rZXlj"
    "bG9hay5leGFtcGxlL3JlYWxtcy9kZWNpZGVyIiwicmVhbG1fYWNjZXNzIjp7InJvbGVzIjpbImFu"
    "YWx5c3QiXX0sInJlc291cmNlX2FjY2VzcyI6eyJkZWNpZGVyLWFwaSI6eyJyb2xlcyI6WyJvcGVy"
    "YXRvciJdfX0sInJvbGVzIjpbInVzZXIiXSwic2NvcGUiOiJyZWFkOmRhdGEgZXhwb3J0OmRhdGEi"
    "LCJzY3AiOlsid2F0Y2hsaXN0OnZpZXciXSwic3ViIjoidXNlci0xMjMiLCJ0ZW5hbnRfaWQiOiJh"
    "Y21lIn0."
    "Oej6f4LbYa2JUvkdxZWOy_a1jdJ-gPHv0fuH6ZDlkcuv4-0RuII1uthICJmM2rCqeh77L24-4cv3"
    "hrOmInCQEzabz0ChOydE-Kdk0NO4ivBzvnZ2megERVIA5gYPrEWAmyaPPBU-iOt_vpOgL1h2nFOl"
    "5VIu-rWIiXT6ptrZdhc"
)
_MISSING_TENANT_TOKEN: Final[str] = (
    "eyJhbGciOiJSUzI1NiIsImtpZCI6InRlc3Qta2V5LTEiLCJ0eXAiOiJKV1QifQ."
    "eyJhdWQiOiJkZWNpZGVyLWFwaSIsImV4cCI6MTczNjUwMzYwMCwiaXNzIjoiaHR0cHM6Ly9rZXlj"
    "bG9hay5leGFtcGxlL3JlYWxtcy9kZWNpZGVyIiwicmVhbG1fYWNjZXNzIjp7InJvbGVzIjpbImFu"
    "YWx5c3QiXX0sInJlc291cmNlX2FjY2VzcyI6eyJkZWNpZGVyLWFwaSI6eyJyb2xlcyI6WyJvcGVy"
    "YXRvciJdfX0sInJvbGVzIjpbInVzZXIiXSwic2NvcGUiOiJyZWFkOmRhdGEgZXhwb3J0OmRhdGEi"
    "LCJzY3AiOlsid2F0Y2hsaXN0OnZpZXciXSwic3ViIjoidXNlci0xMjMiLCJ0ZW5hbnRfaWQiOm51"
    "bGx9."
    "NDihBkui3UCzV5Ku7dHF7TpIv2fStVZE5tAW08ZlOkOyp7Avw0pbw1P7CGtnNb0g7_0Sz8niSrVF"
    "5mtSC1I9YezR3h2qLXq_9LKEgPcLrPHySVRP-VDAoneA70i4vBrM9jA6Z2XmVvts2nCOuRvZ2nPF"
    "rzo41pTdFd2PF4CKrCU"
)


def _build_validator(now: int = _FIXED_NOW) -> KeycloakTokenValidator:
    return KeycloakTokenValidator.from_jwks(
        issuer=_ISSUER,
        audience=_AUDIENCE,
        tenant_claim_names=("tenant_id", "tenant", "org_id"),
        jwks_document={
            "keys": [
                {
                    "kty": "RSA",
                    "kid": _KID,
                    "alg": "RS256",
                    "use": "sig",
                    "n": _N_B64,
                    "e": "AQAB",
                }
            ]
        },
        now_provider=lambda: float(now),
    )


def test_token_validator_can_load_jwks_from_url(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeResponse:
        def __enter__(self) -> "_FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def getcode(self) -> int:
            return 200

        def read(self) -> bytes:
            return json.dumps(
                {
                    "keys": [
                        {
                            "kty": "RSA",
                            "kid": _KID,
                            "alg": "RS256",
                            "use": "sig",
                            "n": _N_B64,
                            "e": "AQAB",
                        }
                    ]
                }
            ).encode("utf-8")

    def _fake_urlopen(url: str, timeout: float) -> _FakeResponse:
        assert url == "https://keycloak.example/realms/decider/protocol/openid-connect/certs"
        assert timeout == 2.5
        return _FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)
    validator = KeycloakTokenValidator.from_jwks_url(
        issuer=_ISSUER,
        audience=_AUDIENCE,
        tenant_claim_names=("tenant_id", "tenant", "org_id"),
        jwks_url="https://keycloak.example/realms/decider/protocol/openid-connect/certs",
        timeout_seconds=2.5,
        now_provider=lambda: float(_FIXED_NOW),
    )

    claims = validator.validate_token(_VALID_TOKEN)
    assert claims["sub"] == "user-123"


def test_token_validator_rejects_unreachable_jwks_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_urlopen(url: str, timeout: float) -> None:
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)
    with pytest.raises(TokenValidationError, match="fetch JWKS"):
        KeycloakTokenValidator.from_jwks_url(
            issuer=_ISSUER,
            audience=_AUDIENCE,
            tenant_claim_names=("tenant_id", "tenant", "org_id"),
            jwks_url="https://keycloak.example/realms/decider/protocol/openid-connect/certs",
        )


def test_token_validator_rejects_invalid_issuer() -> None:
    validator = _build_validator()
    with pytest.raises(TokenValidationError, match="issuer"):
        validator.validate_token(_BAD_ISSUER_TOKEN)


def test_token_validator_rejects_invalid_audience() -> None:
    validator = _build_validator()
    with pytest.raises(TokenValidationError, match="audience"):
        validator.validate_token(_BAD_AUDIENCE_TOKEN)


def test_token_validator_rejects_expired_token() -> None:
    validator = _build_validator()
    with pytest.raises(TokenValidationError, match="expired"):
        validator.validate_token(_EXPIRED_TOKEN)


def test_token_validator_rejects_missing_tenant_claim() -> None:
    validator = _build_validator()
    with pytest.raises(TokenValidationError, match="tenant claim"):
        validator.validate_token(_MISSING_TENANT_TOKEN)


def test_token_validator_rejects_invalid_signature() -> None:
    validator = _build_validator()
    header, payload, signature = _VALID_TOKEN.split(".")
    replacement = "A" if signature[-1] != "A" else "B"
    tampered_signature = f"{signature[:-1]}{replacement}"
    tampered_token = f"{header}.{payload}.{tampered_signature}"

    with pytest.raises(TokenValidationError, match="signature"):
        validator.validate_token(tampered_token)


def test_auth_context_endpoint_rejects_missing_token() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/auth/context")
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or expired token."}


def test_auth_context_endpoint_rejects_expired_token() -> None:
    validator = _build_validator()
    app.dependency_overrides[get_token_validator] = lambda: validator
    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/auth/context",
            headers={"Authorization": f"Bearer {_EXPIRED_TOKEN}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or expired token."}


def test_auth_context_endpoint_rejects_missing_tenant_claim() -> None:
    validator = _build_validator()
    app.dependency_overrides[get_token_validator] = lambda: validator
    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/auth/context",
            headers={"Authorization": f"Bearer {_MISSING_TENANT_TOKEN}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or expired token."}


def test_auth_context_endpoint_returns_mapped_claims() -> None:
    validator = _build_validator()
    app.dependency_overrides[get_token_validator] = lambda: validator
    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/auth/context",
            headers={"Authorization": f"Bearer {_VALID_TOKEN}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "authenticated": True,
        "subject": "user-123",
        "tenant_id": "acme",
        "scopes": ["read:data", "export:data", "watchlist:view"],
        "roles": ["user", "analyst", "operator"],
        "module_entitlements": ["dashboard", "dossiers", "watchlist"],
    }
