import base64
import binascii
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Callable, Final, Mapping


_SHA256_DIGESTINFO_PREFIX: Final[bytes] = bytes.fromhex(
    "3031300d060960864801650304020105000420"
)


class TokenValidationError(ValueError):
    """Raised when a bearer token is missing, malformed, or invalid."""


def _decode_base64url(value: str) -> bytes:
    if not value:
        raise TokenValidationError("JWT segment is empty.")
    padding = "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(value + padding)
    except (ValueError, binascii.Error) as exc:
        raise TokenValidationError("JWT segment is not valid base64url.") from exc


def _decode_json_segment(value: str) -> dict[str, object]:
    raw = _decode_base64url(value)
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TokenValidationError("JWT segment is not valid JSON.") from exc
    if not isinstance(decoded, dict):
        raise TokenValidationError("JWT segment must decode to an object.")
    return decoded


def _parse_numeric_timestamp(claim: object) -> int:
    if isinstance(claim, bool):
        raise TokenValidationError("Timestamp claim has invalid type.")
    if isinstance(claim, int):
        return claim
    if isinstance(claim, float) and claim.is_integer():
        return int(claim)
    raise TokenValidationError("Timestamp claim has invalid value.")


def _parse_audience(claim: object) -> list[str]:
    if isinstance(claim, str):
        return [claim]
    if isinstance(claim, list):
        parsed = [item for item in claim if isinstance(item, str)]
        if len(parsed) != len(claim):
            raise TokenValidationError("Audience claim has invalid value.")
        return parsed
    raise TokenValidationError("Audience claim is required.")


def _verify_rs256_signature(
    signing_input: bytes,
    signature: bytes,
    modulus: int,
    exponent: int,
) -> bool:
    modulus_size = (modulus.bit_length() + 7) // 8
    if len(signature) != modulus_size:
        return False

    signature_int = int.from_bytes(signature, "big")
    encoded_message = pow(signature_int, exponent, modulus).to_bytes(
        modulus_size, "big"
    )

    digest = hashlib.sha256(signing_input).digest()
    digest_info = _SHA256_DIGESTINFO_PREFIX + digest
    padding_size = modulus_size - len(digest_info) - 3
    if padding_size < 8:
        return False

    expected = (
        b"\x00\x01"
        + (b"\xff" * padding_size)
        + b"\x00"
        + digest_info
    )
    return hmac.compare_digest(encoded_message, expected)


@dataclass(frozen=True)
class _RsaPublicKey:
    kid: str
    modulus: int
    exponent: int


@dataclass(frozen=True)
class KeycloakTokenValidator:
    issuer: str
    audience: str
    tenant_claim_names: tuple[str, ...]
    _keys_by_kid: Mapping[str, _RsaPublicKey]
    _now_provider: Callable[[], float] = time.time

    @classmethod
    def from_jwks(
        cls,
        *,
        issuer: str,
        audience: str,
        tenant_claim_names: tuple[str, ...],
        jwks_document: Mapping[str, object],
        now_provider: Callable[[], float] = time.time,
    ) -> "KeycloakTokenValidator":
        keys = jwks_document.get("keys")
        if not isinstance(keys, list):
            raise TokenValidationError("JWKS document must contain a keys list.")

        parsed_keys: dict[str, _RsaPublicKey] = {}
        for jwk in keys:
            if not isinstance(jwk, dict):
                continue

            kid = jwk.get("kid")
            kty = jwk.get("kty")
            n = jwk.get("n")
            e = jwk.get("e")
            if (
                not isinstance(kid, str)
                or not kid
                or kty != "RSA"
                or not isinstance(n, str)
                or not isinstance(e, str)
            ):
                continue

            modulus = int.from_bytes(_decode_base64url(n), "big")
            exponent = int.from_bytes(_decode_base64url(e), "big")
            if modulus <= 0 or exponent <= 1 or exponent % 2 == 0:
                continue

            parsed_keys[kid] = _RsaPublicKey(
                kid=kid,
                modulus=modulus,
                exponent=exponent,
            )

        return cls(
            issuer=issuer,
            audience=audience,
            tenant_claim_names=tenant_claim_names,
            _keys_by_kid=parsed_keys,
            _now_provider=now_provider,
        )

    @classmethod
    def from_jwks_json(
        cls,
        *,
        issuer: str,
        audience: str,
        tenant_claim_names: tuple[str, ...],
        jwks_json: str,
        now_provider: Callable[[], float] = time.time,
    ) -> "KeycloakTokenValidator":
        try:
            document = json.loads(jwks_json or '{"keys":[]}')
        except json.JSONDecodeError as exc:
            raise TokenValidationError("JWKS JSON is malformed.") from exc
        if not isinstance(document, dict):
            raise TokenValidationError("JWKS JSON must decode to an object.")
        return cls.from_jwks(
            issuer=issuer,
            audience=audience,
            tenant_claim_names=tenant_claim_names,
            jwks_document=document,
            now_provider=now_provider,
        )

    def validate_authorization_header(self, authorization: str | None) -> dict[str, object]:
        if authorization is None:
            raise TokenValidationError("Authorization header is required.")

        token_type, _, token = authorization.strip().partition(" ")
        if token_type.lower() != "bearer" or not token:
            raise TokenValidationError("Authorization header must use Bearer token.")
        return self.validate_token(token)

    def validate_token(self, token: str) -> dict[str, object]:
        if not self.issuer:
            raise TokenValidationError("Token issuer is not configured.")
        if not self.audience:
            raise TokenValidationError("Token audience is not configured.")

        parts = token.split(".")
        if len(parts) != 3:
            raise TokenValidationError("JWT must have three segments.")

        header_segment, payload_segment, signature_segment = parts
        header = _decode_json_segment(header_segment)
        payload = _decode_json_segment(payload_segment)
        signature = _decode_base64url(signature_segment)

        algorithm = header.get("alg")
        if algorithm != "RS256":
            raise TokenValidationError("Only RS256 tokens are supported.")

        kid = header.get("kid")
        if not isinstance(kid, str) or not kid:
            raise TokenValidationError("JWT kid is required.")

        key = self._keys_by_kid.get(kid)
        if key is None:
            raise TokenValidationError("No matching JWK for token kid.")

        signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
        if not _verify_rs256_signature(
            signing_input,
            signature,
            key.modulus,
            key.exponent,
        ):
            raise TokenValidationError("JWT signature is invalid.")

        self._validate_claims(payload)
        return payload

    def _validate_claims(self, payload: Mapping[str, object]) -> None:
        issuer = payload.get("iss")
        if issuer != self.issuer:
            raise TokenValidationError("JWT issuer is invalid.")

        audiences = _parse_audience(payload.get("aud"))
        if self.audience not in audiences:
            raise TokenValidationError("JWT audience is invalid.")

        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject:
            raise TokenValidationError("JWT subject is required.")

        tenant_id = self._extract_tenant_id(payload)
        if tenant_id is None:
            raise TokenValidationError("JWT tenant claim is required.")

        expiry = _parse_numeric_timestamp(payload.get("exp"))
        now = int(self._now_provider())
        if now >= expiry:
            raise TokenValidationError("JWT is expired.")

    def _extract_tenant_id(self, payload: Mapping[str, object]) -> str | None:
        for claim_name in self.tenant_claim_names:
            value = payload.get(claim_name)
            if isinstance(value, str) and value:
                return value
        return None
